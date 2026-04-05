"""Session tools: experiment lifecycle for the autoresearch loop.

This is the Codex agent's interface for running experiments.
It handles: init, run, status, revert.

Designed to be called by the Codex agent as CLI commands:

    python session_tools.py init
    python session_tools.py status
    python session_tools.py run --description "increased activity weight to 0.50"
    python session_tools.py show-rank

Environment variables (set by run_agent_loop.py):
    DEVELOPABILITY_RUN_DIR      — path to the run directory
    DEVELOPABILITY_RESULTS_TSV  — path to results.tsv
    DEVELOPABILITY_SRC_DIR      — path to the workspace src/ directory

Based on the session_tools.py pattern from autoresearch-mol.
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [session_tools] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --- Paths (configurable via env vars) ---

SRC_DIR = Path(os.environ.get("DEVELOPABILITY_SRC_DIR", Path(__file__).parent))
RUN_DIR = Path(os.environ.get(
    "DEVELOPABILITY_RUN_DIR",
    Path(__file__).resolve().parent.parent / "results" / "loops" / "default",
))
RESULTS_TSV = Path(os.environ.get(
    "DEVELOPABILITY_RESULTS_TSV",
    RUN_DIR / "results.tsv",
))

RANK_PATH = SRC_DIR / "rank.py"
RANK_LEARNABLE_PATH = SRC_DIR / "rank_learnable.py"
PYTHON_BIN = sys.executable

# Sub-directories inside RUN_DIR
LOGS_DIR = RUN_DIR / "logs"
DIFFS_DIR = RUN_DIR / "diffs"
VERSIONS_DIR = RUN_DIR / "rank_versions"
STATE_DIR = RUN_DIR / ".state"

# Evaluation timeout (seconds): evaluation is fast, generous limit
EVAL_TIMEOUT = 120

# --- Session state ---

STATE_FILE = STATE_DIR / "session_state.json"


@dataclass
class SessionState:
    best_topk_enrichment: float | None = None
    best_ndcg: float | None = None
    best_snapshot: str | None = None
    best_learnable_snapshot: str | None = None
    best_experiment: int = 0
    total_experiments: int = 0

    def save(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls) -> "SessionState":
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                data = json.load(f)
            return cls(**data)
        return cls()


# --- Layout init ---


RESULTS_HEADER = (
    "commit\tstrategy\tsummary_metric\ttopk_enrichment\tndcg\t"
    "hypervolume\ttopk_feasible_frac\tn_candidates\tk\tstatus\tdescription\n"
)


def ensure_layout():
    """Create run directory layout and initialize results.tsv."""
    for d in [RUN_DIR, LOGS_DIR, DIFFS_DIR, VERSIONS_DIR, STATE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    if not RESULTS_TSV.exists():
        with open(RESULTS_TSV, "w") as f:
            f.write(RESULTS_HEADER)
        logger.info(f"Created {RESULTS_TSV}")

    logger.info(f"Layout ready: {RUN_DIR}")


# --- Experiment execution ---


def _get_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def _count_results_rows() -> int:
    """Count non-header rows in results.tsv."""
    if not RESULTS_TSV.exists():
        return 0
    with open(RESULTS_TSV) as f:
        lines = [l for l in f if l.strip() and not l.startswith("commit")]
    return len(lines)


def _experiment_id(n: int) -> str:
    """Format experiment number as exp001, exp002, etc."""
    return f"exp{n:03d}"


def run_experiment(description: str, strategy: str = "agent_improved",
                   split: str = "val", k: int = 20):
    """Run one experiment: evaluate the current rank.py, log result.

    Steps:
    1. Load session state
    2. Snapshot current rank.py
    3. Run evaluation
    4. Parse metrics
    5. Determine keep/discard
    6. Log to results.tsv
    7. Revert if discard/crash
    """
    state = SessionState.load()
    state.total_experiments += 1
    exp_id = _experiment_id(state.total_experiments)

    logger.info(f"--- Experiment {exp_id}: {description} ---")

    # Snapshot candidate rank.py and rank_learnable.py
    snapshot_path = VERSIONS_DIR / f"{exp_id}_candidate.py"
    shutil.copy2(RANK_PATH, snapshot_path)
    snapshot_learnable = VERSIONS_DIR / f"{exp_id}_candidate_learnable.py"
    if RANK_LEARNABLE_PATH.exists():
        shutil.copy2(RANK_LEARNABLE_PATH, snapshot_learnable)
    logger.info(f"Snapshot saved: {snapshot_path}")

    # Compute diff against best snapshot
    if state.best_snapshot and Path(state.best_snapshot).exists():
        diff_path = DIFFS_DIR / f"{exp_id}.diff"
        try:
            result = subprocess.run(
                ["diff", "-u", str(state.best_snapshot), str(RANK_PATH)],
                capture_output=True, text=True, timeout=10,
            )
            with open(diff_path, "w") as f:
                f.write(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Run evaluation
    log_path = LOGS_DIR / f"{exp_id}.log"
    try:
        result = subprocess.run(
            [PYTHON_BIN, "-m", "src.evaluate",
             "--strategy", strategy, "--split", split, "--k", str(k)],
            cwd=SRC_DIR.parent,
            capture_output=True, text=True,
            timeout=EVAL_TIMEOUT,
        )
        with open(log_path, "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr)
    except subprocess.TimeoutExpired:
        with open(log_path, "w") as f:
            f.write(f"TIMEOUT after {EVAL_TIMEOUT}s\n")
        _record_result(state, exp_id, None, "crash", description, strategy)
        _restore_best(state)
        state.save()
        logger.error(f"{exp_id}: TIMEOUT")
        return

    if result.returncode != 0:
        _record_result(state, exp_id, None, "crash", description, strategy)
        _restore_best(state)
        state.save()
        logger.error(f"{exp_id}: evaluation failed (exit {result.returncode})")
        return

    # Parse metrics from log
    metrics = _parse_eval_log(result.stdout + (result.stderr or ""))
    if metrics is None:
        _record_result(state, exp_id, None, "crash",
                       description + " [parse_failed]", strategy)
        _restore_best(state)
        state.save()
        logger.error(f"{exp_id}: could not parse metrics from log")
        return

    # Determine keep/discard
    topk = metrics["topk_enrichment"]
    ndcg_val = metrics["ndcg"]

    if state.best_topk_enrichment is None or topk > state.best_topk_enrichment:
        status = "keep"
    elif (topk == state.best_topk_enrichment and
          ndcg_val > (state.best_ndcg or 0)):
        status = "keep"
    else:
        status = "discard"

    # Record
    _record_result(state, exp_id, metrics, status, description, strategy)

    if status == "keep":
        state.best_topk_enrichment = topk
        state.best_ndcg = ndcg_val
        keep_path = VERSIONS_DIR / f"{exp_id}_keep.py"
        shutil.copy2(RANK_PATH, keep_path)
        if RANK_LEARNABLE_PATH.exists():
            keep_learnable = VERSIONS_DIR / f"{exp_id}_keep_learnable.py"
            shutil.copy2(RANK_LEARNABLE_PATH, keep_learnable)
            state.best_learnable_snapshot = str(keep_learnable)
        state.best_snapshot = str(keep_path)
        state.best_experiment = state.total_experiments
        logger.info(f"{exp_id}: KEEP (topk={topk:.4f}, ndcg={ndcg_val:.4f})")
    else:
        discard_path = VERSIONS_DIR / f"{exp_id}_discard.py"
        shutil.copy2(RANK_PATH, discard_path)
        if RANK_LEARNABLE_PATH.exists():
            shutil.copy2(RANK_LEARNABLE_PATH,
                         VERSIONS_DIR / f"{exp_id}_discard_learnable.py")
        _restore_best(state)
        logger.info(f"{exp_id}: DISCARD (topk={topk:.4f} vs "
                    f"best={state.best_topk_enrichment:.4f})")

    state.save()


def _parse_eval_log(log_text: str) -> dict | None:
    """Parse evaluation metrics from the evaluate.py log output.

    Looks for the RESULTS SUMMARY table or individual metric lines.
    """
    metrics = {}

    # Try to find metric values from the summary line
    # Format: strategy   topk_enrich   ndcg   hv   feasible
    patterns = {
        "topk_enrichment": r"(\d+\.\d{4})\s+(\d+\.\d{4})\s+(\d+\.\d{4})\s+(\d+\.\d{4})",
    }

    # Look for "Result logged:" lines which are more reliable
    result_match = re.search(
        r"topk_enrichment=(\d+\.\d+).*ndcg=(\d+\.\d+)",
        log_text,
    )
    if result_match:
        metrics["topk_enrichment"] = float(result_match.group(1))
        metrics["ndcg"] = float(result_match.group(2))

    # Also try to extract hypervolume and feasible fraction from summary
    summary_match = re.search(
        r"\s+(\d+\.\d{4})\s+(\d+\.\d{4})\s+(\d+\.\d{4})\s+(\d+\.\d{4})\s*$",
        log_text, re.MULTILINE,
    )
    if summary_match:
        if "topk_enrichment" not in metrics:
            metrics["topk_enrichment"] = float(summary_match.group(1))
            metrics["ndcg"] = float(summary_match.group(2))
        metrics["hypervolume"] = float(summary_match.group(3))
        metrics["topk_feasible_frac"] = float(summary_match.group(4))

    if "topk_enrichment" not in metrics:
        return None

    # Fill defaults for missing metrics
    metrics.setdefault("hypervolume", 0.0)
    metrics.setdefault("topk_feasible_frac", 0.0)
    metrics.setdefault("n_candidates", 0)
    metrics.setdefault("k", 20)

    # Try to get n_candidates from "Loaded val split: N candidates"
    loaded_match = re.search(r"Loaded \w+ split: (\d+) candidates", log_text)
    if loaded_match:
        metrics["n_candidates"] = int(loaded_match.group(1))

    return metrics


def _record_result(state, exp_id, metrics, status, description, strategy):
    """Append one row to the run's results.tsv."""
    commit = _get_commit()

    if metrics is None:
        row = (f"{commit}\t{strategy}\t0.0000\t0.0000\t0.0000\t"
               f"0.0000\t0.0000\t0\t20\t{status}\t{description}\n")
    else:
        row = (
            f"{commit}\t{strategy}\t"
            f"{metrics['topk_enrichment']:.4f}\t"
            f"{metrics['topk_enrichment']:.4f}\t"
            f"{metrics['ndcg']:.4f}\t"
            f"{metrics['hypervolume']:.4f}\t"
            f"{metrics.get('topk_feasible_frac', 0):.4f}\t"
            f"{metrics.get('n_candidates', 0)}\t"
            f"{metrics.get('k', 20)}\t"
            f"{status}\t{description}\n"
        )

    with open(RESULTS_TSV, "a") as f:
        f.write(row)

    logger.info(f"Recorded {exp_id} [{status}] to {RESULTS_TSV}")


def _restore_best(state: SessionState):
    """Restore rank.py and rank_learnable.py to the best-known versions."""
    if state.best_snapshot is None:
        logger.info("No best snapshot to restore (first experiment)")
        return
    best_path = Path(state.best_snapshot)
    if best_path.exists():
        shutil.copy2(best_path, RANK_PATH)
        logger.info(f"Restored rank.py from {best_path.name}")
    else:
        logger.warning(f"Best snapshot not found: {best_path}")

    # Also restore rank_learnable.py if we have a snapshot
    best_learnable = getattr(state, "best_learnable_snapshot", None)
    if best_learnable:
        best_learnable_path = Path(best_learnable)
        if best_learnable_path.exists():
            shutil.copy2(best_learnable_path, RANK_LEARNABLE_PATH)
            logger.info(f"Restored rank_learnable.py from {best_learnable_path.name}")


# --- Status ---


def show_status():
    """Print current session status."""
    state = SessionState.load()
    n_rows = _count_results_rows()

    print(f"Run directory: {RUN_DIR}")
    print(f"Results file:  {RESULTS_TSV}")
    print(f"Rank.py:       {RANK_PATH}")
    print(f"Experiments:   {n_rows}")
    print(f"Best TopK:     {state.best_topk_enrichment}")
    print(f"Best NDCG:     {state.best_ndcg}")
    print(f"Best experiment: {state.best_experiment}")
    print(f"Best snapshot: {state.best_snapshot}")

    if RESULTS_TSV.exists():
        print(f"\nLast 5 results:")
        with open(RESULTS_TSV) as f:
            lines = f.readlines()
        if len(lines) > 1:
            print(lines[0].rstrip())  # header
            for line in lines[-5:]:
                print(line.rstrip())


def show_rank():
    """Print the current rank.py content."""
    if RANK_PATH.exists():
        print(RANK_PATH.read_text())
    else:
        print(f"rank.py not found at {RANK_PATH}")


# --- Summary ---


def finalize_summary():
    """Write summary.json with aggregate stats."""
    state = SessionState.load()
    n_rows = _count_results_rows()

    # Count statuses
    statuses = {"keep": 0, "discard": 0, "crash": 0}
    if RESULTS_TSV.exists():
        with open(RESULTS_TSV) as f:
            for line in f:
                for s in statuses:
                    if f"\t{s}\t" in line:
                        statuses[s] += 1

    summary = {
        "total_experiments": n_rows,
        "keep": statuses["keep"],
        "discard": statuses["discard"],
        "crash": statuses["crash"],
        "best_topk_enrichment": state.best_topk_enrichment,
        "best_ndcg": state.best_ndcg,
        "best_experiment": state.best_experiment,
    }

    summary_path = RUN_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {summary_path}")
    print(json.dumps(summary, indent=2))


# --- CLI ---


def main():
    parser = argparse.ArgumentParser(description="Session tools for autoresearch loop")
    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init", help="Initialize run directory layout")

    # status
    subparsers.add_parser("status", help="Show current session status")

    # run
    run_parser = subparsers.add_parser("run", help="Run one experiment")
    run_parser.add_argument("--description", required=True,
                            help="One-line description of what changed")
    run_parser.add_argument("--strategy", default="agent_improved",
                            help="Strategy to evaluate (default: agent_improved)")
    run_parser.add_argument("--split", default="val",
                            help="Data split to evaluate on")
    run_parser.add_argument("--k", type=int, default=20,
                            help="Top-k for metrics")

    # show-rank
    subparsers.add_parser("show-rank", help="Print current rank.py")

    # summary
    subparsers.add_parser("summary", help="Finalize and print summary.json")

    args = parser.parse_args()

    if args.command == "init":
        ensure_layout()
    elif args.command == "status":
        show_status()
    elif args.command == "run":
        ensure_layout()
        run_experiment(
            description=args.description,
            strategy=args.strategy,
            split=args.split,
            k=args.k,
        )
    elif args.command == "show-rank":
        show_rank()
    elif args.command == "summary":
        finalize_summary()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
