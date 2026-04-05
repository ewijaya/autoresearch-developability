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


def compute_reference_score(df: pd.DataFrame) -> pd.Series:
    """Compute a composite reference score for ground-truth ranking.

    This is the 'oracle' ranking that policies are compared against.

    Design: the reference uses a DIFFERENT formula from any baseline
    strategy to avoid circularity. It is a multiplicative combination
    that rewards high activity while penalizing constraint violations.

    Formula: activity * feasibility_bonus
    - feasibility_bonus = 1.0 if all constraints satisfied, else decayed
    - This ensures the reference prefers active + feasible candidates
      but does NOT use any specific weight vector that a baseline copies.

    Higher = better candidate.
    """
    def _norm(s):
        r = s.max() - s.min()
        if r < 1e-10:
            return s * 0.0 + 0.5
        return (s - s.min()) / r

    act = _norm(df["activity"])

    # Feasibility: multiplicative penalty for constraint violations
    # Each constraint contributes a factor in (0, 1]
    tox_factor = 1.0 - 0.5 * _norm(df["toxicity"])       # less toxic → higher
    stab_factor = 0.5 + 0.5 * _norm(df["stability"])     # more stable → higher
    dev_factor = 1.0 - 0.3 * _norm(df["dev_penalty"])    # lower penalty → higher

    ref = act * tox_factor * stab_factor * dev_factor
    return ref


def evaluate_ranking(
    df: pd.DataFrame,
    ranked_indices: list,
    k: int = 20,
) -> dict:
    """Compute all ranking metrics.

    Returns dict with metric names and values.
    """
    ref_scores = compute_reference_score(df)

    metrics = {
        "topk_enrichment": topk_enrichment(ranked_indices, ref_scores, k=k),
        "ndcg": ndcg(ranked_indices, ref_scores, k=k),
        "hypervolume": hypervolume_2d(df, ranked_indices, k=k),
        "n_candidates": len(ranked_indices),
        "k": k,
    }

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


def main():
    """Run evaluation for all baseline strategies."""
    parser = argparse.ArgumentParser(description="Evaluate ranking policies")
    parser.add_argument("--split", default="val", choices=["train", "val", "test"])
    parser.add_argument("--strategy", default=None,
                        help="Single strategy to evaluate (default: all baselines)")
    parser.add_argument("--k", type=int, default=20, help="Top-k for metrics")
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

    return results


if __name__ == "__main__":
    main()
