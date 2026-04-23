"""Annotated trajectory figure highlighting the agent's structural discoveries.

Reads results/loops/prompt5/results.tsv and produces a narrative-annotated
version of the loop trajectory: four callouts mark the iterations where the
agent moved beyond weight-tuning.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results" / "loops" / "prompt5" / "results.tsv"
OUT = ROOT / "results" / "figures" / "fig_trajectory_annotated.png"

CALLOUTS = [
    (2, "Weight tuning", "#4a7ab8", (14, 24)),
    (26, "Reciprocal rank fusion", "#c84a4a", (-6, -38)),
    (32, "Consensus voting", "#c84a4a", (14, 28)),
    (38, "Learned reranking", "#c84a4a", (18, 58)),
]


def main() -> None:
    df = pd.read_csv(DATA, sep="\t")
    df["iteration"] = range(1, len(df) + 1)
    df["topk_enrichment"] = df["topk_enrichment"].astype(float)
    df["ndcg"] = df["ndcg"].astype(float)
    df["composite"] = (
        2 * df["topk_enrichment"] * df["ndcg"]
        / (df["topk_enrichment"] + df["ndcg"])
    )

    keeps = df[df["status"] == "keep"].copy()
    discards = df[df["status"] == "discard"]

    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=200)

    ax.scatter(
        discards["iteration"],
        discards["composite"],
        c="#d5d8dc",
        s=18,
        alpha=0.4,
        edgecolors="none",
        zorder=1,
        label="Discarded (88)",
    )

    step_x, step_y = [keeps["iteration"].iloc[0]], [keeps["composite"].iloc[0]]
    for i in range(1, len(keeps)):
        step_x.append(keeps["iteration"].iloc[i])
        step_y.append(step_y[-1])
        step_x.append(keeps["iteration"].iloc[i])
        step_y.append(keeps["composite"].iloc[i])
    step_x.append(len(df))
    step_y.append(step_y[-1])
    ax.plot(step_x, step_y, color="#2a9d57", linewidth=2.4, alpha=0.85, zorder=2)

    callout_iters = {row[0] for row in CALLOUTS}
    regular_keeps = keeps[~keeps["iteration"].isin(callout_iters)]
    ax.scatter(
        regular_keeps["iteration"],
        regular_keeps["composite"],
        c="#2a9d57",
        s=60,
        edgecolors="white",
        linewidth=1.0,
        zorder=3,
        label="Kept improvements (12 total)",
    )

    for it, label, color, offset in CALLOUTS:
        row = keeps[keeps["iteration"] == it].iloc[0]
        ax.scatter(
            [row["iteration"]],
            [row["composite"]],
            c=color,
            s=180,
            edgecolors="white",
            linewidth=1.8,
            zorder=5,
        )
        ha = "left" if offset[0] >= 0 else "right"
        va = "bottom" if offset[1] >= 0 else "top"
        ax.annotate(
            label,
            xy=(row["iteration"], row["composite"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=12,
            fontweight="bold",
            color=color,
            ha=ha,
            va=va,
            zorder=6,
            arrowprops=dict(
                arrowstyle="-",
                color=color,
                lw=1.2,
                alpha=0.7,
                shrinkA=4,
                shrinkB=4,
            ),
        )

    y_min = keeps["composite"].min()
    y_max = keeps["composite"].max()
    y_pad = (y_max - y_min) * 1.3
    ax.set_ylim(y_min - y_pad * 0.25, y_max + y_pad)

    ax.set_xlabel("Experiment number (out of 100)", fontsize=12)
    ax.set_ylabel("Ranking quality (higher is better)", fontsize=12)
    ax.set_title(
        "What the AI agent discovered, in order",
        fontsize=14,
        pad=14,
    )
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
