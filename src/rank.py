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


def _norm(s):
    """Min-max normalize a Series to [0, 1]."""
    r = s.max() - s.min()
    if r == 0:
        return s * 0.0
    return (s - s.min()) / r


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


def _threshold_gate_score(df):
    """Nonlinear score that emphasizes safe, stable activity."""
    act = _norm(df["activity"])
    tox = _norm(df["toxicity"])
    stab = _norm(df["stability"])
    dev = _norm(df["dev_penalty"])

    tox_gate = 1.0 / (1.0 + np.exp(10.0 * (tox - 0.5)))
    dev_gate = 1.0 / (1.0 + np.exp(10.0 * (dev - 0.5)))
    return act * (0.3 + 0.7 * stab) * tox_gate * dev_gate


def _rank_agent_improved(df, **kwargs):
    """Two-stage policy: linear shortlist, nonlinear rerank inside top-20."""
    base_rank = _rank_weighted_sum(
        df,
        weights={
            "activity": 0.50,
            "toxicity": 0.50,
            "stability": 0.30,
            "dev_penalty": 0.15,
        },
        **kwargs,
    )

    shortlist_size = min(20, len(base_rank))
    if shortlist_size == 0:
        return base_rank

    gate_score = _threshold_gate_score(df)
    shortlist = base_rank[:shortlist_size]
    reranked_shortlist = gate_score.loc[shortlist].sort_values(
        ascending=False
    ).index.tolist()
    return reranked_shortlist + base_rank[shortlist_size:]


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
