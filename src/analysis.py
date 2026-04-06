"""Paper-evidence engine: bootstrap CIs, ablations, figures, qualitative examples.

Usage:
    # Run all analyses and generate figures
    python -m src.analysis

    # Bootstrap confidence intervals only
    python -m src.analysis --bootstrap

    # Ablation study only
    python -m src.analysis --ablation

    # Multi-split robustness
    python -m src.analysis --multi-split

    # Generate all figures
    python -m src.analysis --figures

    # Qualitative examples table
    python -m src.analysis --examples
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluate import (
    ORACLE_FUNCTIONS,
    compute_reference_scores,
    evaluate_ranking,
    topk_enrichment,
    ndcg,
    hypervolume_2d,
)
from src.rank import rank_candidates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"
ABLATION_DIR = RESULTS_DIR / "ablations"

ALL_STRATEGIES = [
    "activity_only",
    "toxicity_exclusion",
    "weighted_sum",
    "agent_improved",
    "rule_only",
    "random",
    "random_weight_search",
    "nsga2_crowding",
]

# Strategies that require trained models and won't work on synthetic data
LEARNABLE_STRATEGIES = ["mlp_learned", "lambdamart"]


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------


def bootstrap_evaluate(
    df: pd.DataFrame,
    strategy: str,
    k: int = 20,
    n_bootstrap: int = 1000,
    seed: int = 42,
    confidence: float = 0.95,
    **kwargs,
) -> dict:
    """Run bootstrap resampling to get confidence intervals for all metrics.

    Resamples candidates with replacement, re-ranks, re-evaluates.

    Args:
        df: scored DataFrame with endpoint columns.
        strategy: ranking strategy name.
        k: top-k for metrics.
        n_bootstrap: number of bootstrap iterations.
        seed: random seed.
        confidence: confidence level (e.g. 0.95 for 95% CI).
        **kwargs: passed to rank_candidates.

    Returns:
        dict with keys like 'topk_enrichment_mean', 'topk_enrichment_ci_lo',
        'topk_enrichment_ci_hi', etc.
    """
    rng = np.random.RandomState(seed)
    alpha = 1 - confidence

    metric_samples = {
        "topk_enrichment": [],
        "ndcg": [],
        "hypervolume": [],
        "topk_feasible_frac": [],
    }

    n = len(df)
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample_idx = rng.choice(n, size=n, replace=True)
        df_boot = df.iloc[sample_idx].reset_index(drop=True)

        ranked = rank_candidates(df_boot, strategy=strategy, **kwargs)
        metrics = evaluate_ranking(df_boot, ranked, k=k)

        for key in metric_samples:
            metric_samples[key].append(metrics[key])

    results = {}
    for key, samples in metric_samples.items():
        arr = np.array(samples)
        results[f"{key}_mean"] = float(np.mean(arr))
        results[f"{key}_std"] = float(np.std(arr))
        results[f"{key}_ci_lo"] = float(np.percentile(arr, 100 * alpha / 2))
        results[f"{key}_ci_hi"] = float(np.percentile(arr, 100 * (1 - alpha / 2)))
        results[f"{key}_median"] = float(np.median(arr))

    results["n_bootstrap"] = n_bootstrap
    results["confidence"] = confidence
    results["strategy"] = strategy
    return results


def run_bootstrap_all(
    split: str = "val",
    k: int = 20,
    n_bootstrap: int = 1000,
    strategies: list | None = None,
) -> pd.DataFrame:
    """Run bootstrap CIs for all strategies on a given split.

    Returns a DataFrame with one row per strategy and columns for
    each metric's mean, std, and CI bounds.
    """
    csv_path = PROCESSED_DIR / f"{split}.csv"
    df = pd.read_csv(csv_path)
    logger.info(f"Bootstrap: {split} split, {len(df)} candidates, "
                f"n_bootstrap={n_bootstrap}")

    if strategies is None:
        strategies = ALL_STRATEGIES

    all_results = []
    for strat in strategies:
        logger.info(f"  Bootstrapping {strat}...")
        try:
            res = bootstrap_evaluate(df, strat, k=k, n_bootstrap=n_bootstrap)
            all_results.append(res)
        except Exception as e:
            logger.error(f"  Bootstrap failed for {strat}: {e}")

    results_df = pd.DataFrame(all_results)

    # Save
    ABLATION_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ABLATION_DIR / f"bootstrap_{split}_k{k}.csv"
    results_df.to_csv(out_path, index=False)
    logger.info(f"Saved bootstrap results to {out_path}")

    # Print summary table
    logger.info("\nBootstrap summary (95% CI):")
    header = (f"{'Strategy':<25} {'TopK Enrich':>12} {'CI':>20} "
              f"{'NDCG':>8} {'CI':>20}")
    logger.info(header)
    logger.info("-" * len(header))
    for _, row in results_df.iterrows():
        logger.info(
            f"{row['strategy']:<25} "
            f"{row['topk_enrichment_mean']:>12.4f} "
            f"[{row['topk_enrichment_ci_lo']:.4f}, {row['topk_enrichment_ci_hi']:.4f}] "
            f"{row['ndcg_mean']:>8.4f} "
            f"[{row['ndcg_ci_lo']:.4f}, {row['ndcg_ci_hi']:.4f}]"
        )

    return results_df


# ---------------------------------------------------------------------------
# Multi-split robustness
# ---------------------------------------------------------------------------


def multi_split_evaluate(
    n_splits: int = 10,
    k: int = 20,
    strategies: list | None = None,
    seed_base: int = 100,
) -> pd.DataFrame:
    """Evaluate all strategies across multiple random train/val/test splits.

    Re-splits the full pool with different seeds and evaluates on each
    val split. Reports mean +/- std across splits.

    Returns DataFrame with one row per (strategy, seed).
    """
    pool_path = PROCESSED_DIR / "full_pool.csv"
    if not pool_path.exists():
        raise FileNotFoundError(
            f"Full pool not found: {pool_path}. Run prepare.py first."
        )
    pool = pd.read_csv(pool_path)
    n = len(pool)
    logger.info(f"Multi-split: {n} candidates, {n_splits} splits")

    if strategies is None:
        strategies = ALL_STRATEGIES

    train_ratio, val_ratio = 0.70, 0.15

    all_rows = []
    for split_i in range(n_splits):
        seed = seed_base + split_i
        rng = np.random.RandomState(seed)
        idx = rng.permutation(n)

        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        val_df = pool.iloc[idx[n_train:n_train + n_val]].reset_index(drop=True)

        for strat in strategies:
            try:
                ranked = rank_candidates(val_df, strategy=strat)
                metrics = evaluate_ranking(val_df, ranked, k=k)
                row = {
                    "split_seed": seed,
                    "strategy": strat,
                    **metrics,
                }
                all_rows.append(row)
            except Exception as e:
                logger.error(f"  Split {split_i}, {strat} failed: {e}")

    results_df = pd.DataFrame(all_rows)

    # Summary: mean +/- std per strategy
    summary = results_df.groupby("strategy").agg(
        topk_mean=("topk_enrichment", "mean"),
        topk_std=("topk_enrichment", "std"),
        ndcg_mean=("ndcg", "mean"),
        ndcg_std=("ndcg", "std"),
        hv_mean=("hypervolume", "mean"),
        hv_std=("hypervolume", "std"),
        feasible_mean=("topk_feasible_frac", "mean"),
        feasible_std=("topk_feasible_frac", "std"),
    ).reset_index()

    ABLATION_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(ABLATION_DIR / f"multi_split_raw.csv", index=False)
    summary.to_csv(ABLATION_DIR / f"multi_split_summary.csv", index=False)
    logger.info(f"Saved multi-split results to {ABLATION_DIR}")

    logger.info("\nMulti-split summary:")
    for _, row in summary.iterrows():
        logger.info(
            f"  {row['strategy']:<25} "
            f"TopK={row['topk_mean']:.4f}+/-{row['topk_std']:.4f}  "
            f"NDCG={row['ndcg_mean']:.4f}+/-{row['ndcg_std']:.4f}"
        )

    return results_df


# ---------------------------------------------------------------------------
# Endpoint ablation study
# ---------------------------------------------------------------------------


def ablation_study(
    split: str = "val",
    k: int = 20,
    strategies: list | None = None,
) -> pd.DataFrame:
    """Drop each endpoint one at a time, measure ranking quality degradation.

    For each endpoint, replaces its values with the column mean (neutral),
    then re-ranks and evaluates. This shows which endpoints contribute
    most to ranking quality.

    Returns DataFrame with columns: strategy, ablated_endpoint, and all metrics.
    """
    csv_path = PROCESSED_DIR / f"{split}.csv"
    df = pd.read_csv(csv_path)
    logger.info(f"Ablation study: {split} split, {len(df)} candidates")

    if strategies is None:
        strategies = ["weighted_sum", "agent_improved", "rule_only"]

    endpoints = ["activity", "toxicity", "stability", "dev_penalty"]

    all_rows = []

    for strat in strategies:
        # Full model (no ablation)
        ranked_full = rank_candidates(df, strategy=strat)
        metrics_full = evaluate_ranking(df, ranked_full, k=k)
        row_full = {
            "strategy": strat,
            "ablated_endpoint": "none",
            **metrics_full,
        }
        all_rows.append(row_full)

        # Ablate each endpoint
        for endpoint in endpoints:
            df_abl = df.copy()
            df_abl[endpoint] = df_abl[endpoint].mean()

            ranked_abl = rank_candidates(df_abl, strategy=strat)
            metrics_abl = evaluate_ranking(df_abl, ranked_abl, k=k)

            delta_topk = metrics_abl["topk_enrichment"] - metrics_full["topk_enrichment"]
            delta_ndcg = metrics_abl["ndcg"] - metrics_full["ndcg"]

            row = {
                "strategy": strat,
                "ablated_endpoint": endpoint,
                "delta_topk": delta_topk,
                "delta_ndcg": delta_ndcg,
                **metrics_abl,
            }
            all_rows.append(row)

    results_df = pd.DataFrame(all_rows)

    ABLATION_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ABLATION_DIR / f"endpoint_ablation_{split}.csv"
    results_df.to_csv(out_path, index=False)
    logger.info(f"Saved ablation results to {out_path}")

    # Print summary
    logger.info("\nEndpoint ablation summary:")
    for strat in strategies:
        logger.info(f"\n  Strategy: {strat}")
        strat_df = results_df[results_df["strategy"] == strat]
        full_row = strat_df[strat_df["ablated_endpoint"] == "none"].iloc[0]
        logger.info(f"    Full model: TopK={full_row['topk_enrichment']:.4f}, "
                    f"NDCG={full_row['ndcg']:.4f}")
        for _, row in strat_df[strat_df["ablated_endpoint"] != "none"].iterrows():
            logger.info(
                f"    Drop {row['ablated_endpoint']:<15} "
                f"TopK={row['topk_enrichment']:.4f} "
                f"(delta={row['delta_topk']:+.4f})  "
                f"NDCG={row['ndcg']:.4f} "
                f"(delta={row['delta_ndcg']:+.4f})"
            )

    return results_df


# ---------------------------------------------------------------------------
# Qualitative examples
# ---------------------------------------------------------------------------


def qualitative_examples(
    split: str = "val",
    k: int = 20,
    n_examples: int = 10,
) -> pd.DataFrame:
    """Find peptides whose rank changed most between baseline and agent_improved.

    Reports the top-N biggest movers (up and down) with all endpoint scores,
    giving reviewers concrete evidence of what the policy change does.

    Returns DataFrame of example peptides with their scores and rank changes.
    """
    csv_path = PROCESSED_DIR / f"{split}.csv"
    df = pd.read_csv(csv_path)

    ranked_baseline = rank_candidates(df, strategy="weighted_sum")
    ranked_agent = rank_candidates(df, strategy="agent_improved")

    # Build rank lookup: index -> rank position (0-based)
    rank_baseline = {idx: pos for pos, idx in enumerate(ranked_baseline)}
    rank_agent = {idx: pos for pos, idx in enumerate(ranked_agent)}

    examples = []
    for idx in df.index:
        rb = rank_baseline.get(idx, len(df))
        ra = rank_agent.get(idx, len(df))
        rank_change = rb - ra  # positive = moved up (improved)

        examples.append({
            "df_index": idx,
            "sequence": df.loc[idx, "sequence"][:30] + ("..." if len(df.loc[idx, "sequence"]) > 30 else ""),
            "seq_length": len(df.loc[idx, "sequence"]),
            "activity": df.loc[idx, "activity"],
            "toxicity": df.loc[idx, "toxicity"],
            "stability": df.loc[idx, "stability"],
            "dev_penalty": df.loc[idx, "dev_penalty"],
            "rank_baseline": rb + 1,  # 1-indexed for humans
            "rank_agent": ra + 1,
            "rank_change": rank_change,
            "in_topk_baseline": rb < k,
            "in_topk_agent": ra < k,
        })

    ex_df = pd.DataFrame(examples)

    # Top movers up (entered top-k or moved up a lot)
    movers_up = ex_df.nlargest(n_examples // 2, "rank_change")
    # Top movers down (dropped from top-k or moved down)
    movers_down = ex_df.nsmallest(n_examples // 2, "rank_change")

    result = pd.concat([movers_up, movers_down]).sort_values(
        "rank_change", ascending=False
    )

    ABLATION_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ABLATION_DIR / f"qualitative_examples_{split}.csv"
    result.to_csv(out_path, index=False)
    logger.info(f"Saved {len(result)} qualitative examples to {out_path}")

    logger.info("\nQualitative examples (biggest rank changes):")
    logger.info(f"{'Sequence':<33} {'Act':>5} {'Tox':>5} {'Stab':>5} "
                f"{'Dev':>5} {'Rank BL':>8} {'Rank AG':>8} {'Change':>8}")
    logger.info("-" * 100)
    for _, row in result.iterrows():
        logger.info(
            f"{row['sequence']:<33} "
            f"{row['activity']:>5.3f} {row['toxicity']:>5.3f} "
            f"{row['stability']:>5.3f} {row['dev_penalty']:>5.1f} "
            f"{row['rank_baseline']:>8d} {row['rank_agent']:>8d} "
            f"{row['rank_change']:>+8d}"
        )

    return result


# ---------------------------------------------------------------------------
# Figure generation
# ---------------------------------------------------------------------------


def _ensure_matplotlib():
    """Import matplotlib with non-interactive backend."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_theme(style="whitegrid", font_scale=1.1)
    return plt, sns


def figure1_baseline_comparison(split: str = "val", k: int = 20):
    """Figure 1: Bar chart comparing all strategies on primary metrics.

    Grouped bar chart with strategies on x-axis and metric values on y-axis.
    If bootstrap results exist, adds error bars.
    """
    plt, sns = _ensure_matplotlib()

    csv_path = PROCESSED_DIR / f"{split}.csv"
    df = pd.read_csv(csv_path)

    strategies = ALL_STRATEGIES
    labels = {
        "activity_only": "Activity\nOnly",
        "toxicity_exclusion": "Toxicity\nExclusion",
        "weighted_sum": "Weighted\nSum",
        "agent_improved": "Agent\nImproved",
        "rule_only": "Rule\nOnly",
        "random": "Random",
        "random_weight_search": "Random\nWeight Search",
        "nsga2_crowding": "NSGA-II\nCrowding",
    }
    metrics_to_plot = ["topk_enrichment", "ndcg", "topk_feasible_frac"]
    metric_labels = {
        "topk_enrichment": "Top-k Enrichment",
        "ndcg": "NDCG",
        "topk_feasible_frac": "Feasible Fraction",
    }

    # Evaluate all strategies
    data = []
    for strat in strategies:
        ranked = rank_candidates(df, strategy=strat)
        metrics = evaluate_ranking(df, ranked, k=k)
        for m in metrics_to_plot:
            data.append({
                "Strategy": labels.get(strat, strat),
                "Metric": metric_labels[m],
                "Value": metrics[m],
            })

    plot_df = pd.DataFrame(data)

    # Try to load bootstrap CIs for error bars
    bootstrap_path = ABLATION_DIR / f"bootstrap_{split}_k{k}.csv"
    ci_data = None
    if bootstrap_path.exists():
        ci_data = pd.read_csv(bootstrap_path)

    fig, ax = plt.subplots(figsize=(12, 6))
    bar_plot = sns.barplot(
        data=plot_df, x="Strategy", y="Value", hue="Metric",
        ax=ax, palette="Set2",
    )

    # Add error bars from bootstrap if available
    if ci_data is not None:
        _add_bootstrap_errorbars(ax, bar_plot, ci_data, strategies, labels,
                                 metrics_to_plot, metric_labels)

    ax.set_ylabel("Score")
    ax.set_title(f"Strategy Comparison ({split} split, k={k})")
    ax.set_ylim(0, 1.1)
    ax.legend(title="Metric", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig1_baseline_comparison.pdf"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved Figure 1 to {out_path}")


def _add_bootstrap_errorbars(ax, bar_plot, ci_data, strategies, labels,
                              metrics_to_plot, metric_labels):
    """Overlay bootstrap CI error bars on a grouped bar chart."""
    n_metrics = len(metrics_to_plot)
    n_strats = len(strategies)
    bars = bar_plot.patches

    # bars are ordered: all bars of metric 0, then metric 1, etc.
    for m_idx, metric in enumerate(metrics_to_plot):
        for s_idx, strat in enumerate(strategies):
            ci_row = ci_data[ci_data["strategy"] == strat]
            if ci_row.empty:
                continue
            ci_row = ci_row.iloc[0]

            bar_idx = m_idx * n_strats + s_idx
            if bar_idx >= len(bars):
                continue

            bar = bars[bar_idx]
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            lo = ci_row.get(f"{metric}_ci_lo", y)
            hi = ci_row.get(f"{metric}_ci_hi", y)

            ax.errorbar(x, y, yerr=[[y - lo], [hi - y]],
                        fmt="none", color="black", capsize=3, linewidth=1)


def figure2_loop_trajectory():
    """Figure 2: Iteration number vs summary metric (loop trajectory).

    Scatter plot with keep/discard coloring and a running-best line.
    Prefers the Codex loop results (results/loops/*/results.tsv) over
    the root results.tsv. Falls back to root if no loop data exists.
    """
    plt, sns = _ensure_matplotlib()

    # Find loop results — prefer the most recent loop with the most rows
    loop_dir = RESULTS_DIR / "loops"
    loop_files = sorted(loop_dir.glob("*/results.tsv")) if loop_dir.exists() else []

    results_path = None
    best_rows = 0
    for lf in loop_files:
        try:
            n = sum(1 for line in open(lf) if line.strip() and not line.startswith("commit"))
            if n > best_rows:
                best_rows = n
                results_path = lf
        except OSError:
            continue

    # Fall back to root results.tsv
    if results_path is None or best_rows == 0:
        results_path = Path("results.tsv")

    if not results_path.exists():
        logger.warning("No results.tsv found, skipping Figure 2")
        return

    logger.info(f"Figure 2: using {results_path} ({best_rows} experiments)")

    results = pd.read_csv(results_path, sep="\t")
    results["iteration"] = range(1, len(results) + 1)
    results["topk_enrichment"] = results["topk_enrichment"].astype(float)
    results["ndcg"] = results["ndcg"].astype(float)

    # Combined score: topk is primary, ndcg breaks ties.
    # This mirrors the keep/discard logic in session_tools.py exactly:
    #   keep if topk > best_topk, OR (topk == best_topk AND ndcg > best_ndcg)
    # Weight of 0.1 makes NDCG sub-steps visible between TopK plateaus:
    # TopK steps are ~0.017 apart; NDCG diffs ~0.01 * 0.1 = 0.001 per sub-step,
    # giving ~6 visible sub-steps per TopK plateau without overlapping the next.
    results["combined_score"] = (results["topk_enrichment"]
                                 + results["ndcg"] * 0.1)

    # Running best as step function (like autoresearch-mol style)
    running_best = results["combined_score"].cummax()

    keeps = results[results["status"] == "keep"]
    n_keep = len(keeps)
    n_discard = (results["status"] == "discard").sum()
    n_total = len(results)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Step plot for running best — the main visual
    ax.step(results["iteration"], running_best, where="post",
            color="#2c3e50", linewidth=2.5, label="Running best", zorder=2)

    # Faded grey dots for discards (behind step line)
    mask_discard = results["status"] == "discard"
    if mask_discard.any():
        ax.scatter(
            results.loc[mask_discard, "iteration"],
            results.loc[mask_discard, "combined_score"],
            c="#d5d8dc", s=20, zorder=1, edgecolors="#c0c5c9",
            linewidth=0.3, alpha=0.4, label="Discard",
        )

    # Green diamonds for keeps (on top)
    mask_keep = results["status"] == "keep"
    if mask_keep.any():
        ax.scatter(
            results.loc[mask_keep, "iteration"],
            results.loc[mask_keep, "combined_score"],
            c="#2ecc71", s=80, zorder=3, edgecolors="#1a9c4a",
            linewidth=1.0, alpha=0.95, marker="D", label="Keep",
        )

    # Annotate first and last keep
    if len(keeps) > 1:
        first_keep = keeps.iloc[0]
        last_keep = keeps.iloc[-1]
        ax.annotate(
            f"TopK={first_keep['topk_enrichment']:.3f}",
            xy=(first_keep["iteration"], first_keep["combined_score"]),
            xytext=(-15, -20), textcoords="offset points",
            fontsize=9, color="#555",
            arrowprops=dict(arrowstyle="->", color="#999", lw=1),
        )
        ax.annotate(
            f"Best: TopK={last_keep['topk_enrichment']:.3f}, "
            f"NDCG={last_keep['ndcg']:.3f}",
            xy=(last_keep["iteration"], last_keep["combined_score"]),
            xytext=(10, 15), textcoords="offset points",
            fontsize=10, fontweight="bold", color="#2c3e50",
            arrowprops=dict(arrowstyle="->", color="#2c3e50", lw=1.5),
        )

    # Tight y-axis: zoom to the staircase range
    best_val = running_best.iloc[-1]
    first_val = running_best.iloc[0]
    y_range = best_val - first_val
    y_pad = max(y_range * 1.0, 0.01)
    ax.set_ylim(first_val - y_pad, best_val + y_pad * 0.5)

    ax.set_xlabel("Experiment", fontsize=11)
    ax.set_ylabel("Summary Score (TopK + NDCG tiebreak)", fontsize=11)
    ax.set_title(f"Autoresearch Loop: {n_total} Experiments "
                 f"({n_keep} keep, {n_discard} discard)", fontsize=12)
    ax.legend(loc="lower right", fontsize=10)
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig2_loop_trajectory.pdf"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved Figure 2 to {out_path}")


def figure3_pareto_front(split: str = "val", k: int = 20):
    """Figure 3: Activity vs safety Pareto front, colored by ranking strategy.

    Scatter of all candidates in (activity, 1-toxicity) space.
    Top-k candidates under different policies are highlighted.
    """
    plt, sns = _ensure_matplotlib()

    csv_path = PROCESSED_DIR / f"{split}.csv"
    df = pd.read_csv(csv_path)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    strategies_to_show = ["activity_only", "weighted_sum", "agent_improved"]
    titles = ["Activity Only", "Weighted Sum (baseline)", "Agent Improved"]
    colors = ["#e74c3c", "#3498db", "#2ecc71"]

    safety = 1.0 - df["toxicity"]

    for ax, strat, title, color in zip(axes, strategies_to_show, titles, colors):
        ranked = rank_candidates(df, strategy=strat)
        topk_set = set(ranked[:k])

        in_topk = df.index.isin(topk_set)
        not_topk = ~in_topk

        ax.scatter(df.loc[not_topk, "activity"], safety[not_topk],
                   c="#bdc3c7", s=8, alpha=0.3, label="Other candidates")
        ax.scatter(df.loc[in_topk, "activity"], safety[in_topk],
                   c=color, s=40, alpha=0.8, edgecolors="white",
                   linewidth=0.5, label=f"Top-{k}")

        ax.set_xlabel("Activity")
        ax.set_title(title)
        ax.legend(loc="lower right", fontsize=9)

    axes[0].set_ylabel("Safety (1 - Toxicity)")
    fig.suptitle(f"Pareto Front: Activity vs Safety ({split} split)", y=1.02)
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig3_pareto_front.pdf"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved Figure 3 to {out_path}")


def figure4_ablation_heatmap(split: str = "val"):
    """Figure 4: Endpoint ablation heatmap.

    Heatmap showing delta in top-k enrichment when each endpoint is dropped,
    for each ranking strategy.
    """
    plt, sns = _ensure_matplotlib()

    abl_path = ABLATION_DIR / f"endpoint_ablation_{split}.csv"
    if not abl_path.exists():
        logger.warning(f"Ablation results not found at {abl_path}, "
                       "running ablation first...")
        ablation_study(split=split)

    abl_df = pd.read_csv(abl_path)
    abl_df = abl_df[abl_df["ablated_endpoint"] != "none"]

    if "delta_topk" not in abl_df.columns:
        logger.warning("delta_topk not in ablation results, skipping Figure 4")
        return

    # Pivot for heatmap: strategies as rows, endpoints as columns
    pivot = abl_df.pivot_table(
        index="strategy", columns="ablated_endpoint",
        values="delta_topk", aggfunc="first",
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(
        pivot, annot=True, fmt=".3f", cmap="RdYlGn_r", center=0,
        ax=ax, linewidths=1, linecolor="white",
        cbar_kws={"label": "Delta Top-k Enrichment"},
    )
    ax.set_xlabel("Ablated Endpoint")
    ax.set_ylabel("Strategy")
    ax.set_title(f"Endpoint Ablation Impact ({split} split)")
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig4_ablation_heatmap.pdf"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved Figure 4 to {out_path}")


def figure5_weight_sensitivity():
    """Figure 5: Weight sensitivity analysis from Prompt 3b results.

    Bar chart showing how perturbing each weight affects top-k enrichment.
    Uses results.tsv data from the p3b_ experiments.
    """
    plt, sns = _ensure_matplotlib()

    results_path = Path("results.tsv")
    if not results_path.exists():
        logger.warning("results.tsv not found, skipping Figure 5")
        return

    results = pd.read_csv(results_path, sep="\t")

    # Filter to p3b experiments
    p3b = results[results["strategy"].str.startswith("p3b_")].copy()
    if len(p3b) == 0:
        logger.warning("No p3b_ experiments in results.tsv, skipping Figure 5")
        return

    # Get agent_improved baseline for reference
    agent_row = results[results["strategy"] == "agent_improved"]
    if len(agent_row) == 0:
        logger.warning("No agent_improved in results.tsv, skipping Figure 5")
        return
    baseline_topk = float(agent_row.iloc[0]["topk_enrichment"])

    p3b["topk_enrichment"] = p3b["topk_enrichment"].astype(float)
    p3b["delta"] = p3b["topk_enrichment"] - baseline_topk

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#2ecc71" if d >= 0 else "#e74c3c" for d in p3b["delta"]]
    bars = ax.bar(range(len(p3b)), p3b["delta"], color=colors, edgecolor="white")

    ax.set_xticks(range(len(p3b)))
    ax.set_xticklabels(
        [s.replace("p3b_", "") for s in p3b["strategy"]],
        rotation=45, ha="right",
    )
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="--")
    ax.set_ylabel("Delta Top-k Enrichment vs Agent Improved")
    ax.set_title("Weight Sensitivity Analysis (Prompt 3b)")
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig5_weight_sensitivity.pdf"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved Figure 5 to {out_path}")


def figure6_multi_split_boxplot():
    """Figure 6 (bonus): Box plot of top-k enrichment across multiple splits.

    Shows distribution of each strategy's performance across random splits.
    Requires multi-split results to exist.
    """
    plt, sns = _ensure_matplotlib()

    raw_path = ABLATION_DIR / "multi_split_raw.csv"
    if not raw_path.exists():
        logger.warning("Multi-split results not found, skipping Figure 6")
        return

    raw_df = pd.read_csv(raw_path)

    fig, ax = plt.subplots(figsize=(10, 5))
    order = ALL_STRATEGIES
    sns.boxplot(
        data=raw_df, x="strategy", y="topk_enrichment",
        order=order, ax=ax, palette="Set2",
    )
    sns.stripplot(
        data=raw_df, x="strategy", y="topk_enrichment",
        order=order, ax=ax, color="black", size=4, alpha=0.5,
    )

    ax.set_xlabel("Strategy")
    ax.set_ylabel("Top-k Enrichment")
    ax.set_title("Strategy Robustness Across Random Splits")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig6_multi_split_boxplot.pdf"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved Figure 6 to {out_path}")


# ---------------------------------------------------------------------------
# Run all analyses
# ---------------------------------------------------------------------------


def run_all(split: str = "val", k: int = 20, n_bootstrap: int = 1000):
    """Run the complete paper-evidence pipeline."""
    logger.info("=" * 60)
    logger.info("Running full paper-evidence pipeline")
    logger.info("=" * 60)

    logger.info("\n--- Step 1: Bootstrap CIs ---")
    run_bootstrap_all(split=split, k=k, n_bootstrap=n_bootstrap)

    logger.info("\n--- Step 2: Multi-split robustness ---")
    multi_split_evaluate(n_splits=10, k=k)

    logger.info("\n--- Step 3: Endpoint ablation ---")
    ablation_study(split=split, k=k)

    logger.info("\n--- Step 4: Qualitative examples ---")
    qualitative_examples(split=split, k=k)

    logger.info("\n--- Step 5: Generating figures ---")
    figure1_baseline_comparison(split=split, k=k)
    figure2_loop_trajectory()
    figure3_pareto_front(split=split, k=k)
    figure4_ablation_heatmap(split=split)
    figure5_weight_sensitivity()
    figure6_multi_split_boxplot()

    logger.info("\n" + "=" * 60)
    logger.info("Paper-evidence pipeline COMPLETE")
    logger.info(f"Figures saved to: {FIGURES_DIR}")
    logger.info(f"Ablation data saved to: {ABLATION_DIR}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Paper-evidence analysis pipeline")
    parser.add_argument("--split", default="val", choices=["train", "val", "test"])
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--bootstrap", action="store_true",
                        help="Run bootstrap CIs only")
    parser.add_argument("--multi-split", action="store_true",
                        help="Run multi-split robustness only")
    parser.add_argument("--ablation", action="store_true",
                        help="Run endpoint ablation only")
    parser.add_argument("--examples", action="store_true",
                        help="Generate qualitative examples only")
    parser.add_argument("--figures", action="store_true",
                        help="Generate figures only")
    args = parser.parse_args()

    # If no specific flag, run everything
    run_specific = any([
        args.bootstrap, args.multi_split, args.ablation,
        args.examples, args.figures,
    ])

    if not run_specific:
        run_all(split=args.split, k=args.k, n_bootstrap=args.n_bootstrap)
        return

    if args.bootstrap:
        run_bootstrap_all(split=args.split, k=args.k,
                          n_bootstrap=args.n_bootstrap)

    if args.multi_split:
        multi_split_evaluate(n_splits=10, k=args.k)

    if args.ablation:
        ablation_study(split=args.split, k=args.k)

    if args.examples:
        qualitative_examples(split=args.split, k=args.k)

    if args.figures:
        figure1_baseline_comparison(split=args.split, k=args.k)
        figure2_loop_trajectory()
        figure3_pareto_front(split=args.split, k=args.k)
        figure4_ablation_heatmap(split=args.split)
        figure5_weight_sensitivity()
        figure6_multi_split_boxplot()


if __name__ == "__main__":
    main()
