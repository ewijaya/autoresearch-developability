"""Headline comparison figure for non-technical audiences.

Reads results/ablations/multi_split_raw.csv and produces a simplified boxplot
showing agent_improved vs. the main baselines across 10 random splits.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results" / "ablations" / "multi_split_raw.csv"
OUT = ROOT / "results" / "figures" / "fig_headline_recall_at_20.png"

STRATEGIES = [
    ("agent_improved", "Agent-designed\nranking"),
    ("random_weight_search", "Best-of-1000\nrandom search"),
    ("nsga2_crowding", "NSGA-II\n(industry standard)"),
    ("random", "Random\nselection"),
]
HIGHLIGHT = "agent_improved"

HIGHLIGHT_COLOR = "#c84a4a"
MUTED_COLOR = "#9aa5b1"
FLOOR_COLOR = "#d0d5dc"


def main() -> None:
    df = pd.read_csv(DATA)
    data = [df.loc[df.strategy == key, "topk_enrichment"].values for key, _ in STRATEGIES]
    labels = [label for _, label in STRATEGIES]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    box = ax.boxplot(
        data,
        labels=labels,
        patch_artist=True,
        widths=0.55,
        medianprops=dict(color="black", linewidth=2),
        whiskerprops=dict(color="#444", linewidth=1.2),
        capprops=dict(color="#444", linewidth=1.2),
        flierprops=dict(marker="o", markersize=4, markerfacecolor="#444", markeredgecolor="none"),
    )
    for patch, (key, _) in zip(box["boxes"], STRATEGIES):
        if key == HIGHLIGHT:
            patch.set_facecolor(HIGHLIGHT_COLOR)
            patch.set_alpha(0.9)
        elif key == "random":
            patch.set_facecolor(FLOOR_COLOR)
            patch.set_alpha(0.9)
        else:
            patch.set_facecolor(MUTED_COLOR)
            patch.set_alpha(0.75)

    for i, (key, _) in enumerate(STRATEGIES):
        values = df.loc[df.strategy == key, "topk_enrichment"].values
        ax.scatter(
            [i + 1] * len(values),
            values,
            color="black",
            alpha=0.35,
            s=14,
            zorder=3,
        )
        median = pd.Series(values).median()
        ax.annotate(
            f"{median*100:.0f}%",
            xy=(i + 1, median),
            xytext=(18, 0),
            textcoords="offset points",
            va="center",
            ha="left",
            fontsize=12,
            fontweight="bold",
        )

    ax.set_ylim(0, 0.8)
    ax.set_ylabel("Fraction of best candidates in top-20 shortlist", fontsize=12)
    ax.set_title(
        "AI-designed ranking vs. standard methods (10 random data splits)",
        fontsize=13,
        pad=14,
    )
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{int(y*100)}%"))
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=11)

    plt.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
