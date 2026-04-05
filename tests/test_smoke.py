"""Smoke tests for the autoresearch-developability harness.

Run with: python -m pytest tests/ -v
"""

import numpy as np
import pandas as pd
import pytest

from src.features import compute_features, is_valid_sequence, sequences_to_feature_matrix
from src.endpoint_dev import score_developability
from src.endpoint_activity import mic_to_activity_score, normalize_activity
from src.rank import rank_candidates
from src.evaluate import compute_reference_score, topk_enrichment, ndcg


# --- Feature extraction ---


def test_valid_sequence():
    assert is_valid_sequence("ACDEFGHIKLMNPQRSTVWY")
    assert not is_valid_sequence("ACDEFX")
    assert not is_valid_sequence("")


def test_compute_features():
    feats = compute_features("KLLKWLLKWLK")
    assert feats["length"] == 11
    assert feats["charge_net"] > 0  # K residues
    assert feats["frac_hydrophobic"] > 0
    assert "frac_A" in feats


def test_feature_matrix():
    seqs = ["KLLK", "ACDE", "FWYW"]
    X, names, valid = sequences_to_feature_matrix(seqs)
    assert X.shape[0] == 3
    assert len(names) > 10
    assert all(valid)


# --- Endpoint scoring ---


def test_developability_good_peptide():
    # Short, simple, balanced peptide
    score = score_developability("KLLKWLLKWLK")
    assert score >= 0
    assert score < 5  # should not be heavily penalized


def test_developability_bad_peptide():
    # Very long, extreme hydrophobic
    score = score_developability("AAAIIILLLFFFFFF" * 3)
    assert score > 2  # should be penalized


def test_activity_scoring():
    mics = [1.0, 10.0, 100.0, 0.1]
    scores = mic_to_activity_score(mics)
    # Lower MIC → higher score
    assert scores[3] > scores[0] > scores[1] > scores[2]


def test_normalize_activity():
    scores = [0.0, 5.0, 10.0]
    normed = normalize_activity(scores)
    assert normed[0] == 0.0
    assert normed[2] == 1.0


# --- Ranking ---


@pytest.fixture
def sample_df():
    """Small test DataFrame with known properties."""
    return pd.DataFrame({
        "activity": [0.9, 0.5, 0.3, 0.7, 0.1],
        "toxicity": [0.1, 0.8, 0.2, 0.3, 0.9],
        "stability": [0.7, 0.3, 0.8, 0.5, 0.2],
        "dev_penalty": [0.5, 1.0, 0.0, 0.5, 2.0],
    })


def test_rank_activity_only(sample_df):
    ranked = rank_candidates(sample_df, strategy="activity_only")
    assert ranked[0] == 0  # highest activity


def test_rank_weighted_sum(sample_df):
    ranked = rank_candidates(sample_df, strategy="weighted_sum")
    assert len(ranked) == len(sample_df)


def test_rank_random(sample_df):
    ranked = rank_candidates(sample_df, strategy="random")
    assert len(ranked) == len(sample_df)
    assert set(ranked) == set(sample_df.index)


def test_rank_toxicity_exclusion(sample_df):
    ranked = rank_candidates(sample_df, strategy="toxicity_exclusion")
    # Toxic candidates (idx 1, 4) should not appear first
    assert 1 not in ranked[:2]


def test_rank_rule_only(sample_df):
    ranked = rank_candidates(sample_df, strategy="rule_only")
    assert len(ranked) > 0


# --- Evaluation metrics ---


def test_topk_enrichment_perfect(sample_df):
    ref = compute_reference_score(sample_df)
    ideal = ref.sort_values(ascending=False).index.tolist()
    enrich = topk_enrichment(ideal, ref, k=3)
    assert enrich == 1.0


def test_ndcg_perfect(sample_df):
    ref = compute_reference_score(sample_df)
    ideal = ref.sort_values(ascending=False).index.tolist()
    score = ndcg(ideal, ref, k=3)
    assert abs(score - 1.0) < 1e-6


def test_ndcg_random_worse(sample_df):
    ref = compute_reference_score(sample_df)
    ideal = ref.sort_values(ascending=False).index.tolist()
    reversed_order = ideal[::-1]
    score_ideal = ndcg(ideal, ref, k=3)
    score_bad = ndcg(reversed_order, ref, k=3)
    assert score_ideal > score_bad


# --- Integration test (requires processed data) ---


def test_processed_data_exists():
    """Check that prepare.py has been run and data exists."""
    from pathlib import Path
    for split in ["train", "val", "test"]:
        p = Path(f"data/processed/{split}.csv")
        if not p.exists():
            pytest.skip("Processed data not found. Run: python -m src.prepare")
        df = pd.read_csv(p)
        assert "sequence" in df.columns
        assert "activity" in df.columns
        assert "toxicity" in df.columns
        assert "stability" in df.columns
        assert "dev_penalty" in df.columns
        assert len(df) > 10
