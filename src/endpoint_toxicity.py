"""Toxicity endpoint: trained on ToxinPred3 data.

Trains a RandomForest classifier on ToxinPred3 positive/negative
peptide sequences using AAindex physicochemical features.

Convention: toxicity score in [0, 1]. Higher = more likely toxic.
"""

import logging
import os
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

from src.features import sequences_to_feature_matrix

logger = logging.getLogger(__name__)

MODEL_PATH = Path("data/processed/toxicity_model.pkl")


def load_toxinpred_data(data_dir: Path) -> tuple:
    """Load ToxinPred3 training data from downloaded files.

    Expected files in data_dir:
        train_pos.csv  (one sequence per line, toxic)
        train_neg.csv  (one sequence per line, non-toxic)

    Returns:
        (sequences, labels) where labels: 1=toxic, 0=non-toxic
    """
    pos_file = data_dir / "train_pos.csv"
    neg_file = data_dir / "train_neg.csv"

    sequences = []
    labels = []

    for fpath, label in [(pos_file, 1), (neg_file, 0)]:
        if not fpath.exists():
            raise FileNotFoundError(f"ToxinPred3 data not found: {fpath}")
        with open(fpath) as f:
            for line in f:
                seq = line.strip().upper()
                if seq and all(c.isalpha() for c in seq):
                    sequences.append(seq)
                    labels.append(label)

    logger.info(f"Loaded ToxinPred3: {len(sequences)} sequences "
                f"({sum(labels)} toxic, {len(labels)-sum(labels)} non-toxic)")
    return sequences, labels


def train_toxicity_model(data_dir: Path, save: bool = True) -> RandomForestClassifier:
    """Train toxicity classifier on ToxinPred3 data.

    Returns the trained model.
    """
    sequences, labels = load_toxinpred_data(data_dir)

    X, feat_names, valid_mask = sequences_to_feature_matrix(sequences)
    y = np.array(labels)

    # Filter invalid sequences
    valid_idx = [i for i, v in enumerate(valid_mask) if v]
    X = X[valid_idx]
    y = y[valid_idx]
    logger.info(f"Training toxicity model on {len(valid_idx)} valid sequences, "
                f"{len(feat_names)} features")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    # Quick self-check (not a proper evaluation — just sanity)
    train_auc = roc_auc_score(y, model.predict_proba(X)[:, 1])
    logger.info(f"Toxicity model train AUC: {train_auc:.3f}")

    if save:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"model": model, "feature_names": feat_names}, f)
        logger.info(f"Saved toxicity model to {MODEL_PATH}")

    return model


def predict_toxicity(sequences: list, model=None) -> list:
    """Predict toxicity probability for a list of sequences.

    Returns list of floats in [0, 1]. Higher = more likely toxic.
    """
    if model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Toxicity model not found at {MODEL_PATH}. Run prepare.py first."
            )
        with open(MODEL_PATH, "rb") as f:
            data = pickle.load(f)
        model = data["model"]

    X, _, valid_mask = sequences_to_feature_matrix(sequences)
    probs = model.predict_proba(X)[:, 1]

    # Invalid sequences get maximum toxicity (precautionary)
    for i, v in enumerate(valid_mask):
        if not v:
            probs[i] = 1.0

    return probs.tolist()
