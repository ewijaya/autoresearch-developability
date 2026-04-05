"""Fixed evaluation harness: ranking metrics.

THIS FILE IS FROZEN. Do not modify during the autoresearch loop.

Computes ranking quality metrics for a given policy output.
Accepts a ranked list of candidate indices and the scored DataFrame.

Usage:
    python -m src.evaluate [--strategy weighted_sum] [--split val]
"""

import argparse
import csv
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.rank import rank_candidates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
RESULTS_FILE = Path("results.tsv")


# --- Metric functions ---


def topk_enrichment(
    ranked_indices: list,
    reference_scores: pd.Series,
    k: int = 20,
) -> float:
    """Fraction of true top-k candidates captured in the policy's top-k.

    'True top-k' is defined by a composite reference score:
    high activity, low toxicity, high stability, low dev_penalty.

    Args:
        ranked_indices: ordered list of DataFrame indices (best first).
        reference_scores: Series with a composite reference score (higher=better).
        k: number of top candidates to consider.

    Returns:
        Enrichment ratio in [0, 1].
    """
    if k > len(ranked_indices):
        k = len(ranked_indices)
    if k == 0:
        return 0.0

    # True top-k by reference
    true_topk = set(reference_scores.nlargest(k).index)

    # Policy's top-k
    policy_topk = set(ranked_indices[:k])

    overlap = len(true_topk & policy_topk)
    return overlap / k


def ndcg(
    ranked_indices: list,
    reference_scores: pd.Series,
    k: int = 20,
) -> float:
    """Normalized Discounted Cumulative Gain.

    Measures how well the ranking policy orders candidates according
    to the reference scores, with a logarithmic position discount.
    """
    if k > len(ranked_indices):
        k = len(ranked_indices)
    if k == 0:
        return 0.0

    # Relevance scores for the policy's ranking
    rel = np.array([reference_scores.get(idx, 0.0) for idx in ranked_indices[:k]])

    # DCG
    discounts = np.log2(np.arange(2, k + 2))  # log2(2), log2(3), ...
    dcg = np.sum(rel / discounts)

    # Ideal DCG (sorted by true relevance)
    ideal_rel = np.sort(reference_scores.values)[::-1][:k]
    idcg = np.sum(ideal_rel / discounts)

    if idcg < 1e-10:
        return 0.0
    return dcg / idcg


def hypervolume_2d(
    df: pd.DataFrame,
    ranked_indices: list,
    k: int = 20,
    obj_x: str = "activity",
    obj_y_inv: str = "toxicity",
    ref_point: tuple = (0.0, 0.0),
) -> float:
    """Dominated hypervolume in 2D (activity vs safety) for top-k.

    Both objectives are maximized: activity and safety (1 - toxicity).
    The reference point is the worst corner (0, 0).
    Hypervolume = area dominated by the Pareto front of top-k above ref_point.
    """
    if k > len(ranked_indices):
        k = len(ranked_indices)
    if k == 0:
        return 0.0

    topk_idx = ranked_indices[:k]
    points = np.array([
        (df.loc[i, obj_x], 1.0 - df.loc[i, obj_y_inv])
        for i in topk_idx
        if i in df.index
    ])

    if len(points) == 0:
        return 0.0

    # Filter to points dominating the reference
    points = points[(points[:, 0] > ref_point[0]) & (points[:, 1] > ref_point[1])]
    if len(points) == 0:
        return 0.0

    # Sort by x descending for sweep line
    points = points[points[:, 0].argsort()[::-1]]

    # Sweep from right to left, tracking the Pareto front
    hv = 0.0
    prev_y = ref_point[1]
    for x, y in points:
        if y > prev_y:
            hv += (x - ref_point[0]) * (y - prev_y)
            prev_y = y

    return hv


def _norm(s):
    """Min-max normalize a Series to [0, 1]."""
    r = s.max() - s.min()
    if r < 1e-10:
        return s * 0.0 + 0.5
    return (s - s.min()) / r


def _oracle_pareto_rank(df: pd.DataFrame) -> pd.Series:
    """Oracle A: Pareto dominance rank.

    A candidate dominates another if it is at least as good on all
    endpoints and strictly better on at least one. The rank is the
    number of candidates that dominate it (lower = better), inverted
    to a score (higher = better).

    This oracle has NO parametric formula to reverse-engineer.
    """
    n = len(df)
    act = _norm(df["activity"]).values
    safety = (1.0 - _norm(df["toxicity"])).values
    stab = _norm(df["stability"]).values
    devq = (1.0 - _norm(df["dev_penalty"])).values

    # Count how many candidates dominate each one (vectorized)
    objectives = np.column_stack([act, safety, stab, devq])  # (n, 4)
    dom_count = np.zeros(n, dtype=int)
    for i in range(n):
        # j dominates i if all(obj[j] >= obj[i]) and any(obj[j] > obj[i])
        geq = objectives >= objectives[i]        # (n, 4) bool
        gt = objectives > objectives[i]           # (n, 4) bool
        dominates = geq.all(axis=1) & gt.any(axis=1)  # (n,) bool
        dominates[i] = False
        dom_count[i] = dominates.sum()

    # Score = max_dom - dom_count (so less dominated = higher score)
    max_dom = dom_count.max() if dom_count.max() > 0 else 1
    scores = (max_dom - dom_count).astype(float)
    return pd.Series(scores, index=df.index)


def _oracle_rank_product(df: pd.DataFrame) -> pd.Series:
    """Oracle B: Rank product.

    Rank each candidate independently on each endpoint, then take the
    geometric mean of ranks. Lower geometric mean = better candidate.
    Inverted to a score (higher = better).

    This has no weight vector to discover — it treats all endpoints
    as independently important via their rank order.
    """
    act_rank = _norm(df["activity"]).rank(ascending=False)
    tox_rank = _norm(df["toxicity"]).rank(ascending=True)   # lower tox = better
    stab_rank = _norm(df["stability"]).rank(ascending=False)
    dev_rank = _norm(df["dev_penalty"]).rank(ascending=True)  # lower penalty = better

    # Geometric mean of ranks (lower = better)
    geo_mean_rank = (act_rank * tox_rank * stab_rank * dev_rank) ** 0.25

    # Invert: higher score = better candidate
    score = geo_mean_rank.max() - geo_mean_rank
    return score


def _oracle_threshold_gate(df: pd.DataFrame) -> pd.Series:
    """Oracle C: Threshold-gated activity.

    Candidates must pass hard filters on toxicity and developability,
    then are ranked by activity * stability. Candidates failing any
    gate get a steep penalty but are not fully zeroed out (to keep
    NDCG well-behaved).

    This oracle tests whether the policy respects hard constraints
    while optimizing the remaining objectives.
    """
    act = _norm(df["activity"])
    tox = _norm(df["toxicity"])
    stab = _norm(df["stability"])
    dev = _norm(df["dev_penalty"])

    # Gate factors: sharp sigmoid-like penalty near thresholds
    # Toxicity gate at 0.5 (normalized), dev gate at 0.5 (normalized)
    tox_gate = 1.0 / (1.0 + np.exp(10 * (tox - 0.5)))
    dev_gate = 1.0 / (1.0 + np.exp(10 * (dev - 0.5)))

    score = act * (0.3 + 0.7 * stab) * tox_gate * dev_gate
    return score


# Oracle ensemble: the primary metric is the mean enrichment across all three
ORACLE_FUNCTIONS = {
    "pareto_rank": _oracle_pareto_rank,
    "rank_product": _oracle_rank_product,
    "threshold_gate": _oracle_threshold_gate,
}


def compute_reference_scores(df: pd.DataFrame) -> dict:
    """Compute reference scores from all oracle functions.

    Returns dict of {oracle_name: pd.Series of scores}.
    """
    return {name: fn(df) for name, fn in ORACLE_FUNCTIONS.items()}


def evaluate_ranking(
    df: pd.DataFrame,
    ranked_indices: list,
    k: int = 20,
) -> dict:
    """Compute all ranking metrics.

    Primary metric (topk_enrichment) is the MEAN enrichment across all
    oracle definitions. This prevents gaming any single formula.

    Returns dict with metric names and values.
    """
    ref_scores_dict = compute_reference_scores(df)

    # Per-oracle enrichment and NDCG
    enrichments = {}
    ndcgs = {}
    for name, ref in ref_scores_dict.items():
        enrichments[name] = topk_enrichment(ranked_indices, ref, k=k)
        ndcgs[name] = ndcg(ranked_indices, ref, k=k)

    # Primary metric: mean enrichment across oracles
    mean_enrich = np.mean(list(enrichments.values()))
    mean_ndcg = np.mean(list(ndcgs.values()))

    metrics = {
        "topk_enrichment": mean_enrich,
        "ndcg": mean_ndcg,
        "hypervolume": hypervolume_2d(df, ranked_indices, k=k),
        "n_candidates": len(ranked_indices),
        "k": k,
    }

    # Per-oracle breakdown (for diagnostics)
    for name in enrichments:
        metrics[f"enrich_{name}"] = enrichments[name]
        metrics[f"ndcg_{name}"] = ndcgs[name]

    # Fraction of top-k satisfying all hard constraints
    topk_idx = ranked_indices[:k]
    if topk_idx:
        topk_df = df.loc[[i for i in topk_idx if i in df.index]]
        feasible = topk_df[
            (topk_df["toxicity"] < 0.5) & (topk_df["dev_penalty"] <= 3)
        ]
        metrics["topk_feasible_frac"] = len(feasible) / len(topk_df) if len(topk_df) > 0 else 0
    else:
        metrics["topk_feasible_frac"] = 0.0

    return metrics


def append_result(
    metrics: dict,
    strategy: str,
    status: str = "baseline",
    description: str = "",
    commit: str = "",
):
    """Append one row to results.tsv."""
    if not commit:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5,
            )
            commit = result.stdout.strip() if result.returncode == 0 else "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            commit = "unknown"

    row = {
        "commit": commit,
        "strategy": strategy,
        "summary_metric": f"{metrics['topk_enrichment']:.4f}",
        "topk_enrichment": f"{metrics['topk_enrichment']:.4f}",
        "ndcg": f"{metrics['ndcg']:.4f}",
        "hypervolume": f"{metrics['hypervolume']:.4f}",
        "topk_feasible_frac": f"{metrics.get('topk_feasible_frac', 0):.4f}",
        "n_candidates": metrics["n_candidates"],
        "k": metrics["k"],
        "status": status,
        "description": description,
    }

    file_exists = RESULTS_FILE.exists()
    with open(RESULTS_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys(), delimiter="\t")
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    logger.info(f"Result logged: strategy={strategy}, "
                f"topk_enrichment={metrics['topk_enrichment']:.4f}, "
                f"ndcg={metrics['ndcg']:.4f}")


def run_evaluation(split: str = "val", strategy: str = "weighted_sum",
                   k: int = 20, **kwargs) -> dict:
    """Run a complete evaluation for one strategy on one split.

    Args:
        split: 'train', 'val', or 'test'.
        strategy: ranking strategy name (see rank.py).
        k: top-k for enrichment metrics.
        **kwargs: passed to rank_candidates.

    Returns:
        dict of metrics.
    """
    csv_path = PROCESSED_DIR / f"{split}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Processed data not found: {csv_path}. Run prepare.py first."
        )

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {split} split: {len(df)} candidates")

    # Run ranking
    ranked = rank_candidates(df, strategy=strategy, **kwargs)

    # Evaluate
    metrics = evaluate_ranking(df, ranked, k=k)

    return metrics


def run_overlap_audit(split: str = "val", k: int = 20):
    """Report metrics with and without ToxinPred3-overlapping candidates.

    This is a benchmark integrity check. If metrics change significantly
    when overlap candidates are removed, the toxicity endpoint may be
    giving those candidates an unfair advantage.
    """
    csv_path = PROCESSED_DIR / f"{split}.csv"
    df = pd.read_csv(csv_path)

    if "tox_train_overlap" not in df.columns:
        logger.warning("No tox_train_overlap column — skipping overlap audit. "
                       "Re-run prepare.py to add it.")
        return None

    n_overlap = df["tox_train_overlap"].sum()
    logger.info(f"\n{'='*60}")
    logger.info(f"OVERLAP AUDIT ({split} split)")
    logger.info(f"{'='*60}")
    logger.info(f"Candidates with ToxinPred3 training overlap: "
                f"{n_overlap}/{len(df)} ({100*n_overlap/len(df):.1f}%)")

    if n_overlap == 0:
        logger.info("No overlap — audit not needed.")
        return None

    # Evaluate on full set vs overlap-excluded set
    df_clean = df[~df["tox_train_overlap"]].reset_index(drop=True)
    logger.info(f"After removing overlaps: {len(df_clean)} candidates")

    strategies = ["activity_only", "toxicity_exclusion", "weighted_sum",
                  "random", "rule_only"]

    header = f"{'Strategy':<25} {'Full TopK':>10} {'Clean TopK':>11} {'Delta':>7}"
    logger.info(header)
    logger.info("-" * len(header))

    audit_results = {}
    for strat in strategies:
        ranked_full = rank_candidates(df, strategy=strat)
        ranked_clean = rank_candidates(df_clean, strategy=strat)
        m_full = evaluate_ranking(df, ranked_full, k=k)
        m_clean = evaluate_ranking(df_clean, ranked_clean, k=k)
        delta = m_clean["topk_enrichment"] - m_full["topk_enrichment"]
        logger.info(f"{strat:<25} {m_full['topk_enrichment']:>10.4f} "
                    f"{m_clean['topk_enrichment']:>11.4f} {delta:>+7.4f}")
        audit_results[strat] = {
            "full": m_full, "clean": m_clean, "delta": delta
        }

    return audit_results


def main():
    """Run evaluation for all baseline strategies."""
    parser = argparse.ArgumentParser(description="Evaluate ranking policies")
    parser.add_argument("--split", default="val", choices=["train", "val", "test"])
    parser.add_argument("--strategy", default=None,
                        help="Single strategy to evaluate (default: all baselines)")
    parser.add_argument("--k", type=int, default=20, help="Top-k for metrics")
    parser.add_argument("--audit-overlap", action="store_true",
                        help="Run ToxinPred3 overlap audit")
    args = parser.parse_args()

    strategies = (
        [args.strategy] if args.strategy
        else ["activity_only", "toxicity_exclusion", "weighted_sum",
              "random", "rule_only"]
    )

    logger.info("=" * 60)
    logger.info(f"Evaluating on {args.split} split, k={args.k}")
    logger.info("=" * 60)

    results = {}
    for strat in strategies:
        logger.info(f"\n--- Strategy: {strat} ---")
        try:
            metrics = run_evaluation(
                split=args.split, strategy=strat, k=args.k
            )
            results[strat] = metrics
            append_result(
                metrics, strategy=strat, status="baseline",
                description=f"Baseline {strat} on {args.split}",
            )
        except Exception as e:
            logger.error(f"Strategy {strat} failed: {e}")
            results[strat] = {"error": str(e)}

    # Summary table
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 60)
    header = f"{'Strategy':<25} {'TopK Enrich':>12} {'NDCG':>8} {'HV':>8} {'Feasible':>10}"
    logger.info(header)
    logger.info("-" * len(header))
    for strat, m in results.items():
        if "error" in m:
            logger.info(f"{strat:<25} ERROR: {m['error']}")
        else:
            logger.info(
                f"{strat:<25} {m['topk_enrichment']:>12.4f} {m['ndcg']:>8.4f} "
                f"{m['hypervolume']:>8.4f} {m.get('topk_feasible_frac',0):>10.4f}"
            )

    # Overlap audit
    if args.audit_overlap:
        run_overlap_audit(split=args.split, k=args.k)

    return results


if __name__ == "__main__":
    main()
