"""Learnable ranking policies for the autoresearch loop.

These provide a richer search space than the 4-weight linear scalarization
in rank.py. The agent can iterate on architecture, hyperparameters, and
training strategy.

Policies here are trained on oracle scores from the TRAINING split,
then applied to rank the val/test split. This avoids leakage.

Two policy classes:
1. MLP: small 2-layer neural network trained on oracle scores
2. LambdaMART: LightGBM-based learning-to-rank
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
MODEL_DIR = Path("data/processed")


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


def _load_train_with_oracle_labels(k: int = 20) -> tuple:
    """Load training split and compute oracle reference scores.

    Returns (train_df, oracle_scores_dict) where oracle_scores_dict
    maps oracle name -> Series of scores.
    """
    from src.evaluate import compute_reference_scores

    train_path = PROCESSED_DIR / "train.csv"
    if not train_path.exists():
        raise FileNotFoundError(
            f"Training data not found: {train_path}. Run prepare.py first."
        )
    train_df = pd.read_csv(train_path)
    oracle_scores = compute_reference_scores(train_df)
    return train_df, oracle_scores


def _make_features(df: pd.DataFrame) -> np.ndarray:
    """Extract the 4 endpoint scores as feature matrix for ranking models."""
    return df[["activity", "toxicity", "stability", "dev_penalty"]].values


def _make_composite_target(oracle_scores: dict) -> np.ndarray:
    """Create a single composite target by averaging oracle scores.

    Each oracle is min-max normalized before averaging so they
    contribute equally regardless of scale.
    """
    normalized = []
    for name, scores in oracle_scores.items():
        arr = scores.values
        r = arr.max() - arr.min()
        if r < 1e-10:
            normalized.append(np.zeros_like(arr))
        else:
            normalized.append((arr - arr.min()) / r)
    return np.mean(normalized, axis=0)


# ---------------------------------------------------------------------------
# MLP ranking policy
# ---------------------------------------------------------------------------


def train_mlp_ranker(
    hidden_dim: int = 32,
    n_layers: int = 2,
    lr: float = 1e-3,
    epochs: int = 200,
    dropout: float = 0.1,
    seed: int = 42,
) -> object:
    """Train a small MLP to predict composite oracle scores from endpoints.

    The MLP learns a nonlinear mapping from (activity, toxicity, stability,
    dev_penalty) -> composite_score. This gives the loop a richer function
    class to search over than linear weights.

    Returns the trained model (or None if torch is not available).
    """
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        logger.warning("PyTorch not available. MLP ranker disabled. "
                       "Install with: pip install torch")
        return None

    torch.manual_seed(seed)
    np.random.seed(seed)

    train_df, oracle_scores = _load_train_with_oracle_labels()
    X = _make_features(train_df).astype(np.float32)
    y = _make_composite_target(oracle_scores).astype(np.float32)

    # Standardize features
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0) + 1e-8
    X_norm = (X - X_mean) / X_std

    # Build MLP
    layers = []
    in_dim = X.shape[1]
    for i in range(n_layers):
        out_dim = hidden_dim if i < n_layers - 1 else 1
        layers.append(nn.Linear(in_dim, out_dim))
        if i < n_layers - 1:
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
        in_dim = hidden_dim

    model = nn.Sequential(*layers)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    X_t = torch.from_numpy(X_norm)
    y_t = torch.from_numpy(y).unsqueeze(1)

    # Train
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = model(X_t)
        loss = loss_fn(pred, y_t)
        loss.backward()
        optimizer.step()

    model.eval()
    logger.info(f"MLP ranker trained: {n_layers} layers, hidden={hidden_dim}, "
                f"final loss={loss.item():.6f}")

    return {
        "model": model,
        "X_mean": X_mean,
        "X_std": X_std,
        "framework": "torch",
    }


def rank_mlp(df: pd.DataFrame, model_data: object = None, **kwargs) -> list:
    """Rank candidates using the trained MLP.

    If model_data is None, trains a new model (uses training split).
    """
    if model_data is None:
        model_data = train_mlp_ranker(**kwargs)
    if model_data is None:
        raise RuntimeError("MLP ranker not available (torch not installed)")

    import torch

    model = model_data["model"]
    X = _make_features(df).astype(np.float32)
    X_norm = (X - model_data["X_mean"]) / model_data["X_std"]

    with torch.no_grad():
        scores = model(torch.from_numpy(X_norm)).squeeze().numpy()

    # Higher score = better candidate
    ranked_idx = np.argsort(-scores)
    return df.index[ranked_idx].tolist()


# ---------------------------------------------------------------------------
# LambdaMART ranking policy
# ---------------------------------------------------------------------------


def train_lambdamart_ranker(
    n_estimators: int = 100,
    max_depth: int = 4,
    learning_rate: float = 0.1,
    seed: int = 42,
) -> object:
    """Train a LightGBM LambdaMART model for learning-to-rank.

    Uses pointwise regression on composite oracle scores as a simpler
    alternative to true pairwise/listwise LTR (which requires group
    structure we don't have).

    Returns the trained model (or None if lightgbm is not available).
    """
    try:
        import lightgbm as lgb
    except ImportError:
        logger.warning("LightGBM not available. LambdaMART ranker disabled. "
                       "Install with: pip install lightgbm")
        return None

    train_df, oracle_scores = _load_train_with_oracle_labels()
    X = _make_features(train_df)
    y = _make_composite_target(oracle_scores)

    model = lgb.LGBMRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=seed,
        verbose=-1,
    )
    model.fit(X, y)

    logger.info(f"LambdaMART ranker trained: {n_estimators} trees, "
                f"max_depth={max_depth}")

    return {"model": model, "framework": "lightgbm"}


def rank_lambdamart(df: pd.DataFrame, model_data: object = None, **kwargs) -> list:
    """Rank candidates using the trained LambdaMART model.

    If model_data is None, trains a new model (uses training split).
    """
    if model_data is None:
        model_data = train_lambdamart_ranker(**kwargs)
    if model_data is None:
        raise RuntimeError("LambdaMART ranker not available "
                           "(lightgbm not installed)")

    model = model_data["model"]
    X = _make_features(df)
    scores = model.predict(X)

    ranked_idx = np.argsort(-scores)
    return df.index[ranked_idx].tolist()
