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
ESM_EMBEDDINGS_PATH = Path("data/processed/esm_embeddings.npy")


def _load_esm_embeddings_for_training(sequences: list) -> np.ndarray | None:
    """Load ESM-2 embeddings for ToxinPred3 training sequences.

    Since the training sequences differ from the candidate pool,
    we need to generate embeddings on-the-fly for training data.
    Returns None if ESM is not available.
    """
    try:
        import torch
        import esm
    except ImportError:
        return None

    logger.info("Generating ESM-2 embeddings for toxicity training data...")
    from src.prepare import generate_esm_embeddings
    import tempfile

    tmp_path = Path(tempfile.mkdtemp()) / "tox_esm_embeddings.npy"

    embeddings = generate_esm_embeddings(sequences, tmp_path)
    if tmp_path.exists():
        tmp_path.unlink()
        tmp_path.parent.rmdir()
    return embeddings


def _load_esm_embeddings_for_candidates() -> np.ndarray | None:
    """Load pre-computed ESM-2 embeddings for the candidate pool."""
    if ESM_EMBEDDINGS_PATH.exists():
        return np.load(ESM_EMBEDDINGS_PATH)
    return None


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


def train_toxicity_model(data_dir: Path, save: bool = True,
                         use_esm: bool = True) -> RandomForestClassifier:
    """Train toxicity classifier on ToxinPred3 data.

    Uses 80/20 stratified split for held-out evaluation.
    Final model is trained on all data after reporting held-out metrics.

    If ESM-2 embeddings are available and use_esm=True, concatenates
    them with AAindex features for richer representation.

    Returns the trained model (fitted on full data).
    """
    from sklearn.model_selection import StratifiedShuffleSplit
    from sklearn.metrics import accuracy_score, f1_score

    sequences, labels = load_toxinpred_data(data_dir)

    X, feat_names, valid_mask = sequences_to_feature_matrix(sequences)
    y = np.array(labels)

    # Filter invalid sequences
    valid_idx = [i for i, v in enumerate(valid_mask) if v]
    X = X[valid_idx]
    y = y[valid_idx]

    # Optionally augment with ESM-2 embeddings
    esm_used = False
    if use_esm:
        valid_seqs = [sequences[i] for i in valid_idx]
        esm_emb = _load_esm_embeddings_for_training(valid_seqs)
        if esm_emb is not None and len(esm_emb) == len(X):
            X = np.hstack([X, esm_emb])
            esm_used = True
            logger.info(f"Toxicity: augmented with ESM-2 embeddings, "
                        f"total features={X.shape[1]}")

    logger.info(f"Toxicity data: {len(valid_idx)} valid sequences, "
                f"{X.shape[1]} features (ESM={'yes' if esm_used else 'no'})")

    # --- Held-out evaluation (80/20 stratified split) ---
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    eval_model = RandomForestClassifier(
        n_estimators=200, max_depth=15, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    eval_model.fit(X_train, y_train)

    # Held-out metrics (the real ones)
    test_probs = eval_model.predict_proba(X_test)[:, 1]
    test_preds = eval_model.predict(X_test)
    heldout_auc = roc_auc_score(y_test, test_probs)
    heldout_acc = accuracy_score(y_test, test_preds)
    heldout_f1 = f1_score(y_test, test_preds)
    logger.info(f"Toxicity held-out AUC: {heldout_auc:.3f}, "
                f"acc: {heldout_acc:.3f}, F1: {heldout_f1:.3f}")

    # Diagnostic: train metrics (for comparison only)
    train_auc = roc_auc_score(y_train, eval_model.predict_proba(X_train)[:, 1])
    logger.info(f"Toxicity train AUC: {train_auc:.3f} (diagnostic only)")

    # --- Final model: train on all data ---
    model = RandomForestClassifier(
        n_estimators=200, max_depth=15, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    model.fit(X, y)

    if save:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({
                "model": model,
                "feature_names": feat_names,
                "esm_used": esm_used,
                "heldout_metrics": {
                    "auc": heldout_auc,
                    "accuracy": heldout_acc,
                    "f1": heldout_f1,
                    "n_train": len(train_idx),
                    "n_test": len(test_idx),
                },
            }, f)
        logger.info(f"Saved toxicity model to {MODEL_PATH}")

    # Attach esm_used flag to model so predict_toxicity can check it
    model._esm_used = esm_used
    return model


def predict_toxicity(sequences: list, model=None) -> list:
    """Predict toxicity probability for a list of sequences.

    Returns list of floats in [0, 1]. Higher = more likely toxic.
    If the model was trained with ESM features, attempts to load
    pre-computed candidate pool embeddings.
    """
    esm_used = False
    if model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Toxicity model not found at {MODEL_PATH}. Run prepare.py first."
            )
        with open(MODEL_PATH, "rb") as f:
            data = pickle.load(f)
        model = data["model"]
        esm_used = data.get("esm_used", False)
    else:
        esm_used = getattr(model, "_esm_used", False)

    X, _, valid_mask = sequences_to_feature_matrix(sequences)

    # Augment with ESM embeddings if the model expects them
    if esm_used:
        esm_emb = _load_esm_embeddings_for_candidates()
        if esm_emb is not None and len(esm_emb) == len(X):
            X = np.hstack([X, esm_emb])
        else:
            logger.warning("Model was trained with ESM features but embeddings "
                           "not available for prediction. Falling back to "
                           "AAindex-only features — predictions may be poor.")
            # Pad with zeros to match expected feature count
            n_esm = model.n_features_in_ - X.shape[1]
            if n_esm > 0:
                X = np.hstack([X, np.zeros((len(X), n_esm))])

    probs = model.predict_proba(X)[:, 1]

    # Invalid sequences get maximum toxicity (precautionary)
    for i, v in enumerate(valid_mask):
        if not v:
            probs[i] = 1.0

    return probs.tolist()
