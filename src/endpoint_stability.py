"""Stability endpoint: trained on HLP half-life data.

Trains a RandomForest regressor on HLP peptide half-life data
using AAindex physicochemical features.

Convention: higher stability score = better (longer half-life).
Score is log10(half-life in seconds), then normalized to [0, 1].
"""

import logging
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from src.features import sequences_to_feature_matrix

logger = logging.getLogger(__name__)

MODEL_PATH = Path("data/processed/stability_model.pkl")


def load_hlp_data(data_dir: Path) -> tuple:
    """Load HLP half-life data from downloaded files.

    Expected files in data_dir:
        10mer-peptides.txt  (TSV: sequence, half-life in seconds)
        16mer-peptides.txt  (TSV: sequence, half-life in seconds)

    Returns:
        (sequences, half_lives_log10)
    """
    sequences = []
    half_lives = []

    for fname in ["10mer-peptides.txt", "16mer-peptides.txt"]:
        fpath = data_dir / fname
        if not fpath.exists():
            logger.warning(f"HLP file not found: {fpath}")
            continue
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    seq = parts[0].strip().upper()
                    try:
                        hl = float(parts[1].strip())
                        if hl > 0 and all(c.isalpha() for c in seq):
                            sequences.append(seq)
                            half_lives.append(hl)
                    except ValueError:
                        continue

    logger.info(f"Loaded HLP: {len(sequences)} sequences, "
                f"half-life range: {min(half_lives):.1f}-{max(half_lives):.1f} sec")

    # Log-transform
    log_hl = [np.log10(hl) for hl in half_lives]
    return sequences, log_hl


def train_stability_model(data_dir: Path, save: bool = True) -> RandomForestRegressor:
    """Train stability regressor on HLP data.

    Uses 80/20 split for held-out evaluation.
    Final model is trained on all data after reporting held-out metrics.

    Returns the trained model (fitted on full data).
    """
    from sklearn.model_selection import ShuffleSplit
    from sklearn.metrics import mean_absolute_error

    sequences, log_hl = load_hlp_data(data_dir)

    X, feat_names, valid_mask = sequences_to_feature_matrix(sequences)
    y = np.array(log_hl)

    valid_idx = [i for i, v in enumerate(valid_mask) if v]
    X = X[valid_idx]
    y = y[valid_idx]
    logger.info(f"Stability data: {len(valid_idx)} valid sequences, "
                f"{len(feat_names)} features")

    # --- Held-out evaluation (80/20 split) ---
    splitter = ShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    eval_model = RandomForestRegressor(
        n_estimators=200, max_depth=10, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    eval_model.fit(X_train, y_train)

    # Held-out metrics (the real ones)
    heldout_r2 = eval_model.score(X_test, y_test)
    heldout_mae = mean_absolute_error(y_test, eval_model.predict(X_test))
    logger.info(f"Stability held-out R²: {heldout_r2:.3f}, MAE: {heldout_mae:.3f}")

    # Diagnostic: train metrics (for comparison only)
    train_r2 = eval_model.score(X_train, y_train)
    logger.info(f"Stability train R²: {train_r2:.3f} (diagnostic only)")

    # --- Final model: train on all data ---
    model = RandomForestRegressor(
        n_estimators=200, max_depth=10, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    model.fit(X, y)

    if save:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({
                "model": model,
                "feature_names": feat_names,
                "heldout_metrics": {
                    "r2": heldout_r2,
                    "mae": heldout_mae,
                    "n_train": len(train_idx),
                    "n_test": len(test_idx),
                },
            }, f)
        logger.info(f"Saved stability model to {MODEL_PATH}")

    return model


def predict_stability(sequences: list, model=None) -> list:
    """Predict log10(half-life) for a list of sequences.

    Returns list of floats. Higher = more stable.
    """
    if model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Stability model not found at {MODEL_PATH}. Run prepare.py first."
            )
        with open(MODEL_PATH, "rb") as f:
            data = pickle.load(f)
        model = data["model"]

    X, _, valid_mask = sequences_to_feature_matrix(sequences)
    preds = model.predict(X)

    # Invalid sequences get minimum stability
    min_pred = preds[list(map(bool, valid_mask))].min() if any(valid_mask) else 0.0
    for i, v in enumerate(valid_mask):
        if not v:
            preds[i] = min_pred

    return preds.tolist()


def normalize_stability(scores: list) -> list:
    """Min-max normalize stability scores to [0, 1]."""
    arr = np.array(scores, dtype=float)
    smin, smax = arr.min(), arr.max()
    if smax - smin < 1e-10:
        return [0.5] * len(scores)
    return ((arr - smin) / (smax - smin)).tolist()
