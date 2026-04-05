"""Tests for the paper-evidence analysis engine.

Run with: python -m pytest tests/test_analysis.py -v
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """Small test DataFrame with known properties."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame({
        "activity": np.random.uniform(0, 1, n),
        "toxicity": np.random.uniform(0, 1, n),
        "stability": np.random.uniform(0, 1, n),
        "dev_penalty": np.random.uniform(0, 3, n),
    })


# --- Bootstrap CIs ---


def test_bootstrap_returns_correct_keys(sample_df):
    from src.analysis import bootstrap_evaluate

    result = bootstrap_evaluate(
        sample_df, strategy="weighted_sum", k=10, n_bootstrap=50,
    )
    assert "topk_enrichment_mean" in result
    assert "topk_enrichment_ci_lo" in result
    assert "topk_enrichment_ci_hi" in result
    assert "ndcg_mean" in result
    assert "ndcg_ci_lo" in result
    assert "ndcg_ci_hi" in result
    assert result["n_bootstrap"] == 50
    assert result["strategy"] == "weighted_sum"


def test_bootstrap_ci_ordering(sample_df):
    from src.analysis import bootstrap_evaluate

    result = bootstrap_evaluate(
        sample_df, strategy="weighted_sum", k=10, n_bootstrap=100,
    )
    assert result["topk_enrichment_ci_lo"] <= result["topk_enrichment_mean"]
    assert result["topk_enrichment_mean"] <= result["topk_enrichment_ci_hi"]
    assert result["ndcg_ci_lo"] <= result["ndcg_mean"]
    assert result["ndcg_mean"] <= result["ndcg_ci_hi"]


def test_bootstrap_different_strategies(sample_df):
    from src.analysis import bootstrap_evaluate

    r1 = bootstrap_evaluate(sample_df, strategy="random", k=10, n_bootstrap=50)
    r2 = bootstrap_evaluate(sample_df, strategy="weighted_sum", k=10, n_bootstrap=50)

    # Both should produce valid results
    assert 0.0 <= r1["topk_enrichment_mean"] <= 1.0
    assert 0.0 <= r2["topk_enrichment_mean"] <= 1.0


# --- Ablation ---


def test_ablation_study(sample_df, tmp_path):
    """Test ablation on synthetic data (no file I/O)."""
    from src.evaluate import evaluate_ranking
    from src.rank import rank_candidates

    endpoints = ["activity", "toxicity", "stability", "dev_penalty"]

    # Full model
    ranked_full = rank_candidates(sample_df, strategy="weighted_sum")
    metrics_full = evaluate_ranking(sample_df, ranked_full, k=10)

    # Ablate each endpoint
    for endpoint in endpoints:
        df_abl = sample_df.copy()
        df_abl[endpoint] = df_abl[endpoint].mean()

        ranked_abl = rank_candidates(df_abl, strategy="weighted_sum")
        metrics_abl = evaluate_ranking(df_abl, ranked_abl, k=10)

        # Ablated metrics should be valid
        assert 0.0 <= metrics_abl["topk_enrichment"] <= 1.0
        assert 0.0 <= metrics_abl["ndcg"] <= 1.0


def test_ablation_activity_matters(sample_df):
    """Dropping activity should change the ranking for activity_only strategy."""
    from src.rank import rank_candidates

    ranked_full = rank_candidates(sample_df, strategy="activity_only")

    df_abl = sample_df.copy()
    df_abl["activity"] = df_abl["activity"].mean()
    ranked_abl = rank_candidates(df_abl, strategy="activity_only")

    # With constant activity, all candidates score the same -> different order
    assert ranked_full != ranked_abl


# --- Qualitative examples ---


def test_qualitative_rank_changes(sample_df):
    """Verify rank change computation is correct."""
    from src.rank import rank_candidates

    ranked_bl = rank_candidates(sample_df, strategy="weighted_sum")
    ranked_ag = rank_candidates(sample_df, strategy="agent_improved")

    rank_bl = {idx: pos for pos, idx in enumerate(ranked_bl)}
    rank_ag = {idx: pos for pos, idx in enumerate(ranked_ag)}

    # At least some candidates should have changed rank
    changes = [rank_bl[idx] - rank_ag[idx] for idx in sample_df.index]
    assert any(c != 0 for c in changes)


# --- Learnable rankers ---


def test_mlp_ranker_import():
    """Test that rank_learnable imports without error."""
    from src.rank_learnable import _make_features, _make_composite_target
    # These should be importable without torch/lightgbm


def test_make_features(sample_df):
    from src.rank_learnable import _make_features
    X = _make_features(sample_df)
    assert X.shape == (len(sample_df), 4)
    assert X.dtype in [np.float64, np.float32]


def test_make_composite_target(sample_df):
    from src.evaluate import compute_reference_scores
    from src.rank_learnable import _make_composite_target

    oracle_scores = compute_reference_scores(sample_df)
    y = _make_composite_target(oracle_scores)
    assert len(y) == len(sample_df)
    assert y.min() >= 0.0
    assert y.max() <= 1.0


def test_mlp_ranker_on_sample(sample_df):
    """Test MLP ranker if torch is available, skip otherwise."""
    try:
        import torch
    except ImportError:
        pytest.skip("PyTorch not installed")

    from src.rank_learnable import train_mlp_ranker, rank_mlp
    from src.evaluate import compute_reference_scores

    # We need to mock the training data loading since we don't have
    # data/processed/train.csv in the test environment.
    # Instead, test the ranking function directly with a pre-built model.
    import torch.nn as nn
    model = nn.Sequential(
        nn.Linear(4, 16), nn.ReLU(),
        nn.Linear(16, 1),
    )
    model.eval()

    model_data = {
        "model": model,
        "X_mean": np.zeros(4),
        "X_std": np.ones(4),
        "framework": "torch",
    }

    ranked = rank_mlp(sample_df, model_data=model_data)
    assert len(ranked) == len(sample_df)
    assert set(ranked) == set(sample_df.index)


def test_lambdamart_ranker_on_sample(sample_df):
    """Test LambdaMART ranker if lightgbm is available, skip otherwise."""
    try:
        import lightgbm as lgb
    except ImportError:
        pytest.skip("LightGBM not installed")

    from src.rank_learnable import rank_lambdamart
    from src.evaluate import compute_reference_scores
    from src.rank_learnable import _make_features, _make_composite_target

    # Train a small model directly on the sample data
    oracle_scores = compute_reference_scores(sample_df)
    X = _make_features(sample_df)
    y = _make_composite_target(oracle_scores)

    model = lgb.LGBMRegressor(n_estimators=10, max_depth=2, verbose=-1)
    model.fit(X, y)

    model_data = {"model": model, "framework": "lightgbm"}
    ranked = rank_lambdamart(sample_df, model_data=model_data)
    assert len(ranked) == len(sample_df)
    assert set(ranked) == set(sample_df.index)


# --- Strategy registration ---


def test_all_strategies_registered():
    """All strategies in rank.py should be callable."""
    from src.rank import rank_candidates

    # These should work on any DataFrame
    basic_strategies = [
        "activity_only", "toxicity_exclusion", "weighted_sum",
        "random", "rule_only", "agent_improved",
    ]
    df = pd.DataFrame({
        "activity": [0.9, 0.5, 0.3],
        "toxicity": [0.1, 0.8, 0.2],
        "stability": [0.7, 0.3, 0.8],
        "dev_penalty": [0.5, 1.0, 0.0],
    })

    for strat in basic_strategies:
        ranked = rank_candidates(df, strategy=strat)
        assert len(ranked) > 0, f"Strategy {strat} returned empty ranking"


def test_learnable_strategies_registered():
    """Learnable strategies should be in the rankers dict (even if deps missing)."""
    from src.rank import rank_candidates
    # Just verify they raise the right error, not KeyError
    df = pd.DataFrame({
        "activity": [0.9], "toxicity": [0.1],
        "stability": [0.7], "dev_penalty": [0.5],
    })
    try:
        rank_candidates(df, strategy="mlp_learned")
    except (RuntimeError, ImportError, FileNotFoundError):
        pass  # Expected if torch or training data not available
    except ValueError as e:
        if "Unknown strategy" in str(e):
            pytest.fail("mlp_learned not registered in rank.py")

    try:
        rank_candidates(df, strategy="lambdamart")
    except (RuntimeError, ImportError, FileNotFoundError):
        pass
    except ValueError as e:
        if "Unknown strategy" in str(e):
            pytest.fail("lambdamart not registered in rank.py")
