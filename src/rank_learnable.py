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


def _norm(s: pd.Series) -> pd.Series:
    """Min-max normalize a Series to [0, 1]."""
    r = s.max() - s.min()
    if r < 1e-10:
        return s * 0.0 + 0.5
    return (s - s.min()) / r


def _make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build engineered endpoint features for learned ranking models."""
    act = _norm(df["activity"])
    tox = _norm(df["toxicity"])
    stab = _norm(df["stability"])
    dev = _norm(df["dev_penalty"])

    safe = 1.0 - tox
    devq = 1.0 - dev
    tox_gate = 1.0 / (1.0 + np.exp(10.0 * (tox - 0.5)))
    dev_gate = 1.0 / (1.0 + np.exp(10.0 * (dev - 0.5)))
    gate_score = act * (0.3 + 0.7 * stab) * tox_gate * dev_gate

    return pd.DataFrame(
        {
            "activity": df["activity"],
            "toxicity": df["toxicity"],
            "stability": df["stability"],
            "dev_penalty": df["dev_penalty"],
            "act_n": act,
            "tox_n": tox,
            "stab_n": stab,
            "dev_n": dev,
            "safe_n": safe,
            "devq_n": devq,
            "act_safe": act * safe,
            "act_stab": act * stab,
            "act_devq": act * devq,
            "safe_stab": safe * stab,
            "safe_devq": safe * devq,
            "stab_devq": stab * devq,
            "act_safe_stab": act * safe * stab,
            "act_safe_devq": act * safe * devq,
            "gate_score": gate_score,
            "tox_gate": tox_gate,
            "dev_gate": dev_gate,
            "bottleneck": np.minimum.reduce(
                [act.values, safe.values, stab.values, devq.values]
            ),
            "geom4": np.power(
                np.clip(act * safe * stab * devq, 1e-12, None),
                0.25,
            ),
            "harm4": 4.0 / np.clip(
                1.0 / np.clip(act, 1e-6, None)
                + 1.0 / np.clip(safe, 1e-6, None)
                + 1.0 / np.clip(stab, 1e-6, None)
                + 1.0 / np.clip(devq, 1e-6, None),
                1e-6,
                None,
            ),
        },
        index=df.index,
    )


def _normalize_oracle_targets(oracle_scores: dict) -> np.ndarray:
    """Normalize each oracle target independently to [0, 1]."""
    normalized = []
    for scores in oracle_scores.values():
        arr = scores.values.astype(float)
        r = arr.max() - arr.min()
        if r < 1e-10:
            normalized.append(np.zeros_like(arr))
        else:
            normalized.append((arr - arr.min()) / r)
    return np.vstack(normalized)


def _make_composite_target(oracle_scores: dict) -> np.ndarray:
    """Create a conservative composite target from normalized oracle scores.

    The target rewards candidates that are good across all oracle views,
    not just excellent on one of them.
    """
    normalized = _normalize_oracle_targets(oracle_scores)
    return 0.65 * normalized.min(axis=0) + 0.35 * normalized.mean(axis=0)


def _fuse_rank_scores(*scores: pd.Series, c: float = 10.0) -> pd.Series:
    """Combine score orderings by reciprocal-rank fusion."""
    fused = pd.Series(0.0, index=scores[0].index, dtype=float)
    for score in scores:
        ranks = score.rank(ascending=False, method="average")
        fused = fused + 1.0 / (c + ranks)
    return fused


# ---------------------------------------------------------------------------
# MLP ranking policy
# ---------------------------------------------------------------------------


def train_mlp_ranker(
    hidden_dim: int = 96,
    n_layers: int = 3,
    lr: float = 8e-4,
    epochs: int = 400,
    dropout: float = 0.05,
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
    feature_df = _make_features(train_df)
    X = feature_df.values.astype(np.float32)
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
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.SmoothL1Loss(beta=0.05)

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
        "feature_columns": feature_df.columns.tolist(),
        "framework": "torch",
    }


def score_mlp(df: pd.DataFrame, model_data: object = None, **kwargs) -> pd.Series:
    """Score candidates with the trained MLP."""
    if model_data is None:
        model_data = train_mlp_ranker(**kwargs)
    if model_data is None:
        raise RuntimeError("MLP ranker not available (torch not installed)")

    import torch

    model = model_data["model"]
    X = _make_features(df).values.astype(np.float32)
    X_norm = (X - model_data["X_mean"]) / model_data["X_std"]

    with torch.no_grad():
        scores = model(torch.from_numpy(X_norm).float()).squeeze().numpy()

    return pd.Series(scores, index=df.index)


def rank_mlp(df: pd.DataFrame, model_data: object = None, **kwargs) -> list:
    """Rank candidates using the trained MLP."""
    scores = score_mlp(df, model_data=model_data, **kwargs)
    return scores.sort_values(ascending=False).index.tolist()


# ---------------------------------------------------------------------------
# LambdaMART ranking policy
# ---------------------------------------------------------------------------


def train_lambdamart_ranker(
    n_estimators: int = 250,
    max_depth: int = 5,
    learning_rate: float = 0.03,
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


def score_lambdamart(
    df: pd.DataFrame,
    model_data: object = None,
    **kwargs,
) -> pd.Series:
    """Score candidates with the trained LambdaMART model."""
    if model_data is None:
        model_data = train_lambdamart_ranker(**kwargs)
    if model_data is None:
        raise RuntimeError("LambdaMART ranker not available "
                           "(lightgbm not installed)")

    model = model_data["model"]
    X = _make_features(df)
    scores = model.predict(X)

    return pd.Series(scores, index=df.index)


def score_learned_ensemble(df: pd.DataFrame) -> pd.Series:
    """Fuse MLP and LambdaMART rankings over engineered endpoint features."""
    mlp_scores = None
    lambdamart_scores = None

    try:
        mlp_scores = score_mlp(df)
    except Exception:
        mlp_scores = None

    try:
        lambdamart_scores = score_lambdamart(df)
    except Exception:
        lambdamart_scores = None

    if mlp_scores is None and lambdamart_scores is None:
        raise RuntimeError("No learnable ranker is available")
    if mlp_scores is None:
        return lambdamart_scores
    if lambdamart_scores is None:
        return mlp_scores
    return _fuse_rank_scores(mlp_scores, lambdamart_scores)


def rank_lambdamart(df: pd.DataFrame, model_data: object = None, **kwargs) -> list:
    """Rank candidates using the trained LambdaMART model."""
    scores = score_lambdamart(df, model_data=model_data, **kwargs)
    return scores.sort_values(ascending=False).index.tolist()
