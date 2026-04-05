"""Ranking policy for multi-objective peptide candidate selection.

This is the PRIMARY EDITABLE FILE in the autoresearch loop.
The agent modifies this file to improve ranking quality.
All other src/ files are treated as frozen.

Each ranking function takes a DataFrame with endpoint scores and returns
a ranked ordering (list of indices from best to worst candidate).
"""

import numpy as np


def rank_candidates(df, strategy="weighted_sum", **kwargs):
    """Rank peptide candidates by the specified strategy.

    Args:
        df: DataFrame with columns: activity, toxicity, stability, dev_penalty.
            Higher activity = better. Lower toxicity = better.
            Higher stability = better. Lower dev_penalty = better.
        strategy: one of the implemented ranking strategies.
        **kwargs: strategy-specific parameters.

    Returns:
        List of DataFrame indices ordered from best to worst candidate.
    """
    rankers = {
        "activity_only": _rank_activity_only,
        "toxicity_exclusion": _rank_toxicity_exclusion,
        "weighted_sum": _rank_weighted_sum,
        "random": _rank_random,
        "rule_only": _rank_rule_only,
        "agent_improved": _rank_agent_improved,
        "mlp_learned": _rank_mlp_learned,
        "lambdamart": _rank_lambdamart,
    }
    if strategy not in rankers:
        raise ValueError(f"Unknown strategy: {strategy}. Options: {list(rankers)}")
    return rankers[strategy](df, **kwargs)


# --- Baseline policies (frozen after initial implementation) ---


def _rank_activity_only(df, **kwargs):
    """Rank by predicted activity alone (higher = better)."""
    return df["activity"].sort_values(ascending=False).index.tolist()


def _rank_toxicity_exclusion(df, toxic_threshold=0.5, **kwargs):
    """Exclude toxic candidates, rank remainder by activity."""
    safe = df[df["toxicity"] < toxic_threshold]
    if len(safe) == 0:
        return df["activity"].sort_values(ascending=False).index.tolist()
    return safe["activity"].sort_values(ascending=False).index.tolist()


def _rank_weighted_sum(df, weights=None, **kwargs):
    """Rank by weighted linear combination of normalized scores.

    Default weights: equal across all endpoints.
    Signs: activity (+), toxicity (-), stability (+), dev_penalty (-).
    """
    if weights is None:
        weights = {"activity": 0.25, "toxicity": 0.25,
                   "stability": 0.25, "dev_penalty": 0.25}

    # Normalize each column to [0, 1]
    def _norm(s):
        r = s.max() - s.min()
        if r == 0:
            return s * 0.0
        return (s - s.min()) / r

    score = (
        weights["activity"] * _norm(df["activity"])
        - weights["toxicity"] * _norm(df["toxicity"])
        + weights["stability"] * _norm(df["stability"])
        - weights["dev_penalty"] * _norm(df["dev_penalty"])
    )
    return score.sort_values(ascending=False).index.tolist()


def _rank_random(df, seed=42, **kwargs):
    """Random ranking among all candidates."""
    rng = np.random.RandomState(seed)
    idx = df.index.tolist()
    rng.shuffle(idx)
    return idx


def _rank_rule_only(df, **kwargs):
    """Handcrafted rule-based ranking.

    Rules:
    1. Exclude if dev_penalty > 3 (hard filter)
    2. Exclude if toxicity > 0.7 (hard filter)
    3. Among remaining, sort by: stability desc, then activity desc
    """
    pool = df[(df["dev_penalty"] <= 3) & (df["toxicity"] <= 0.7)]
    if len(pool) == 0:
        pool = df  # fallback: no candidates pass, rank all
    return pool.sort_values(
        ["stability", "activity"], ascending=[False, False]
    ).index.tolist()


def _rank_agent_improved(df, **kwargs):
    """Tuned linear policy discovered in the loop.

    Keeps the same interpretable scalarization as ``weighted_sum`` but
    shifts emphasis toward activity and toxicity, treating stability as
    secondary and developability as a lighter penalty.
    """
    return _rank_weighted_sum(
        df,
        weights={
            "activity": 0.45,
            "toxicity": 0.40,
            "stability": 0.25,
            "dev_penalty": 0.15,
        },
        **kwargs,
    )


# --- Learnable policies (require optional dependencies) ---


def _rank_mlp_learned(df, **kwargs):
    """MLP-based learned ranking policy.

    Trains a small neural network on oracle scores from the training split,
    then applies it to rank the given DataFrame. Requires PyTorch.
    """
    from src.rank_learnable import rank_mlp
    return rank_mlp(df, **kwargs)


def _rank_lambdamart(df, **kwargs):
    """LightGBM-based learning-to-rank policy.

    Trains a gradient-boosted tree model on oracle scores from the
    training split, then applies it to rank the given DataFrame.
    Requires LightGBM.
    """
    from src.rank_learnable import rank_lambdamart
    return rank_lambdamart(df, **kwargs)
