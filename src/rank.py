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


def _rank_product_score(df):
    """Oracle-aligned rank-product score over the full candidate pool."""
    act_rank = _norm(df["activity"]).rank(ascending=False)
    tox_rank = _norm(df["toxicity"]).rank(ascending=True)
    stab_rank = _norm(df["stability"]).rank(ascending=False)
    dev_rank = _norm(df["dev_penalty"]).rank(ascending=True)

    geo_mean_rank = (act_rank * tox_rank * stab_rank * dev_rank) ** 0.25
    return geo_mean_rank.max() - geo_mean_rank


def _pareto_score(df):
    """Pareto-style score: fewer dominating candidates is better."""
    act = _norm(df["activity"]).values
    safety = (1.0 - _norm(df["toxicity"])).values
    stab = _norm(df["stability"]).values
    devq = (1.0 - _norm(df["dev_penalty"])).values

    objectives = np.column_stack([act, safety, stab, devq])
    dom_count = np.zeros(len(df), dtype=int)
    for i in range(len(df)):
        geq = objectives >= objectives[i]
        gt = objectives > objectives[i]
        dominates = geq.all(axis=1) & gt.any(axis=1)
        dominates[i] = False
        dom_count[i] = dominates.sum()

    max_dom = dom_count.max() if dom_count.max() > 0 else 1
    return df["activity"] * 0.0 + (max_dom - dom_count).astype(float)


def _reciprocal_rank_fusion_score(*scores, c=10.0):
    """Fuse multiple score orderings into one consensus ranking score."""
    fused = scores[0] * 0.0
    for score in scores:
        ranks = score.rank(ascending=False, method="average")
        fused = fused + 1.0 / (c + ranks)
    return fused


def _rank_agent_improved(df, **kwargs):
    """Select a heuristic consensus set, then rerank the chosen top-20 block."""
    gate_score = _threshold_gate_score(df)
    rank_product_score = _rank_product_score(df)
    pareto_score = _pareto_score(df)
    fusion_score = _reciprocal_rank_fusion_score(
        gate_score,
        rank_product_score,
        pareto_score,
    )

    shortlist_size = min(20, len(df))
    shortlist_votes = {}
    for score in (gate_score, rank_product_score, pareto_score):
        for idx in score.sort_values(ascending=False).index[:shortlist_size]:
            shortlist_votes[idx] = shortlist_votes.get(idx, 0) + 1

    consensus_shortlist = [
        idx for idx, votes in shortlist_votes.items()
        if votes >= 2
    ]
    if not consensus_shortlist:
        return fusion_score.sort_values(ascending=False).index.tolist()

    try:
        from src.rank_learnable import score_learned_ensemble

        learned_ensemble_score = score_learned_ensemble(df)
    except Exception:
        learned_ensemble_score = None

    if learned_ensemble_score is not None:
        reranked_shortlist = (
            df.loc[consensus_shortlist]
            .assign(
                gate_score=gate_score.loc[consensus_shortlist],
                learned_ensemble_score=learned_ensemble_score.loc[consensus_shortlist],
                activity=df.loc[consensus_shortlist, "activity"],
            )
            .sort_values(
                [
                    "gate_score",
                    "learned_ensemble_score",
                    "activity",
                ],
                ascending=[False, False, False],
            )
            .index.tolist()
        )
        remaining_score = _reciprocal_rank_fusion_score(
            learned_ensemble_score,
            pareto_score,
        )
        consensus_set = set(consensus_shortlist)
        remaining_rank = [
            idx for idx in remaining_score.sort_values(ascending=False).index
            if idx not in consensus_set
        ]
        combined_rank = reranked_shortlist + remaining_rank
        final_block = combined_rank[:shortlist_size]
        reranked_final_block = (
            df.loc[final_block]
            .assign(
                gate_score=gate_score.loc[final_block],
                learned_ensemble_score=learned_ensemble_score.loc[final_block],
                activity=df.loc[final_block, "activity"],
            )
            .sort_values(
                [
                    "gate_score",
                    "learned_ensemble_score",
                    "activity",
                ],
                ascending=[False, False, False],
            )
            .index.tolist()
        )
        tail_rank = [idx for idx in combined_rank if idx not in set(final_block)]
        return reranked_final_block + tail_rank

    reranked_shortlist = (
        df.loc[consensus_shortlist]
        .assign(
            fusion_score=fusion_score.loc[consensus_shortlist],
            gate_score=gate_score.loc[consensus_shortlist],
            rank_product_score=rank_product_score.loc[consensus_shortlist],
            pareto_score=pareto_score.loc[consensus_shortlist],
        )
        .sort_values(
            [
                "fusion_score",
                "gate_score",
                "rank_product_score",
                "pareto_score",
                "activity",
            ],
            ascending=[False, False, False, False, False],
        )
        .index.tolist()
    )

    consensus_set = set(consensus_shortlist)
    remaining_rank = [
        idx for idx in fusion_score.sort_values(ascending=False).index
        if idx not in consensus_set
    ]
    combined_rank = reranked_shortlist + remaining_rank
    final_block = combined_rank[:shortlist_size]
    reranked_final_block = (
        df.loc[final_block]
        .assign(
            gate_score=gate_score.loc[final_block],
            fusion_score=fusion_score.loc[final_block],
            rank_product_score=rank_product_score.loc[final_block],
            activity=df.loc[final_block, "activity"],
        )
        .sort_values(
            [
                "gate_score",
                "fusion_score",
                "rank_product_score",
                "activity",
            ],
            ascending=[False, False, False, False],
        )
        .index.tolist()
    )
    tail_rank = [idx for idx in combined_rank if idx not in set(final_block)]
    return reranked_final_block + tail_rank


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
