"""Codex-driven autoresearch loop orchestrator.

Outer loop that spawns one-shot Codex sessions to iteratively improve
the ranking policy in rank.py. Each Codex session makes exactly one
policy change, evaluates it, and records the result.

Based on phase2_runner.py from autoresearch-mol.

Usage:
    # Run 50 experiments with full architecture search
    python -m src.run_agent_loop --experiments 50

    # Run with HP-only constraint (for ablation)
    python -m src.run_agent_loop --experiments 50 --program program_hponly.md

    # Resume a previous run
    python -m src.run_agent_loop --experiments 50 --run-name prompt5

    # Dry run (print prompts without launching Codex)
    python -m src.run_agent_loop --experiments 5 --dry-run
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [loop] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
RESULTS_BASE = PROJECT_ROOT / "results" / "loops"

# Files to copy into workspace
WORKSPACE_FILES = [
    "rank.py",
    "rank_learnable.py",
    "evaluate.py",
    "prepare.py",
    "features.py",
    "endpoint_activity.py",
    "endpoint_toxicity.py",
    "endpoint_stability.py",
    "endpoint_dev.py",
    "analysis.py",
    "session_tools.py",
    "__init__.py",
]

# Codex configuration
AGENT_STEP_TIMEOUT = 20 * 60  # 20 minutes per Codex session
AGENT_STEP_MAX_RETRIES = 3     # max consecutive steps without progress
AUTO_WAIT_MAX_SECONDS = 3600   # max time to auto-wait for rate limits (1h)
RATE_LIMIT_BUFFER = 90         # seconds buffer after rate limit reset


# ---------------------------------------------------------------------------
# Workspace management
# ---------------------------------------------------------------------------


def create_workspace(run_dir: Path) -> Path:
    """Create an isolated workspace for the Codex agent.

    Copies source files to run_dir/workspace/src/.
    Symlinks data/ from project root.

    Returns the workspace src/ path.
    """
    workspace_root = run_dir / "workspace"
    workspace_src = workspace_root / "src"

    workspace_root.mkdir(parents=True, exist_ok=True)
    if workspace_src.exists():
        # Workspace exists — just ensure rank.py is current
        return workspace_src

    workspace_src.mkdir(parents=True, exist_ok=True)

    for filename in WORKSPACE_FILES:
        src_file = SRC_DIR / filename
        if src_file.exists():
            shutil.copy2(src_file, workspace_src / filename)

    # Copy program.md to workspace root
    for prog in ["program.md", "program_hponly.md"]:
        prog_src = PROJECT_ROOT / prog
        if prog_src.exists():
            shutil.copy2(prog_src, workspace_root / prog)

    # Symlink data/ directory (shared, not copied)
    data_link = workspace_root / "data"
    if not data_link.exists():
        data_src = PROJECT_ROOT / "data"
        if data_src.exists():
            data_link.symlink_to(data_src)

    # Symlink pyproject.toml for imports
    toml_link = workspace_root / "pyproject.toml"
    if not toml_link.exists():
        toml_src = PROJECT_ROOT / "pyproject.toml"
        if toml_src.exists():
            shutil.copy2(toml_src, toml_link)

    logger.info(f"Workspace created: {workspace_src}")
    return workspace_src


def sync_rank_py(workspace_src: Path, run_dir: Path):
    """Sync rank.py from workspace back to the project and vice versa.

    After a keep, the workspace rank.py is the new best.
    After a discard, session_tools.py already reverted it.
    Either way, copy the current workspace rank.py back to the project.
    """
    ws_rank = workspace_src / "rank.py"
    proj_rank = SRC_DIR / "rank.py"
    if ws_rank.exists():
        shutil.copy2(ws_rank, proj_rank)


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def build_agent_prompt(
    run_dir: Path,
    program_name: str,
    experiments: int,
    existing_rows: int,
) -> str:
    """Build the prompt for one Codex session.

    Tells the agent exactly what to do: read program.md, make one change
    to rank.py, evaluate it, record the result.
    """
    next_experiment = existing_rows + 1

    if existing_rows >= experiments:
        return (
            f"You are resuming a completed autoresearch-developability session.\n\n"
            f"The run already has {existing_rows} recorded experiments, "
            f"which meets the target of {experiments}.\n"
            f"Do not make any further edits. "
            f"Run `python session_tools.py status` and stop.\n"
        )

    prompt = f"""You are executing experiment {next_experiment} of up to {experiments} for the autoresearch-developability ranking policy loop.

Read `{program_name}` and follow it. This Codex session is responsible for exactly one additional experiment row.

Operational requirements:
- Work only inside this workspace's `src/` directory.
- Do not edit any file except `rank.py` (and optionally `rank_learnable.py` for learnable policies).
- Use `session_tools.py` for all experiment execution and logging.
- Start with `python session_tools.py init`.
- Run `python session_tools.py status` before deciding the next step.
- The run state lives in `{run_dir}/results.tsv`, `{run_dir}/logs/`, and `{run_dir}/rank_versions/`.
- Existing completed experiments: {existing_rows}.
- Your goal is to leave the run with exactly one additional row in `{run_dir}/results.tsv`.
- If the run has zero completed experiments, the next row must be the untouched baseline: `python session_tools.py run --description "baseline agent_improved"`.
- Otherwise, inspect the current `rank.py` (run `python session_tools.py show-rank`) and recent results (run `python session_tools.py status`), make one coherent change to the ranking policy, then record it with `python session_tools.py run --description "..."`.
- The description must say exactly what you changed in the ranking policy.
- Stop after that single additional row is recorded.
- If a run crashes, log it through `session_tools.py` and continue.
- Keep the search behavior aligned with `{program_name}`.
- `session_tools.py run` is the source of truth. Treat it as a blocking command and wait for it to finish.
- Do not read full evaluation logs unless a run crashes. For successful runs, use `python session_tools.py status` and the results.tsv. If you need a crash log, read only the tail of the newest file in `{run_dir}/logs/`.
- Do not spend time on long post-hoc analysis. Make one reasonable next-step decision and execute it.
- Avoid commands that print huge files.
- When the new row is present, run `python session_tools.py status` and stop immediately.

What you may change in rank.py:
- Scalarization strategy and objective weights
- Pareto ranking logic
- Lexicographic filtering thresholds
- Hard constraint filters vs soft penalty functions
- Nonlinear transformations of endpoint scores
- Interaction terms between endpoints
- Diversity bonus or redundancy penalty
- Top-k selection and tie-break logic
- Parameters of learnable policies (MLP architecture, LambdaMART hyperparameters)

What you may NOT change:
- evaluate.py, prepare.py, or any endpoint_*.py file
- The evaluation metrics or oracle definitions
- Data files or splits
"""
    return prompt


# ---------------------------------------------------------------------------
# Results tracking
# ---------------------------------------------------------------------------


def results_row_count(run_dir: Path) -> int:
    """Count completed experiment rows in the run's results.tsv."""
    tsv = run_dir / "results.tsv"
    if not tsv.exists():
        return 0
    with open(tsv) as f:
        lines = [l for l in f if l.strip() and not l.startswith("commit")]
    return len(lines)


# ---------------------------------------------------------------------------
# Rate limit detection
# ---------------------------------------------------------------------------


def detect_rate_limit(log_text: str, returncode: int) -> dict | None:
    """Detect Codex rate limits from session output.

    Returns dict with 'scope' and 'retry_after_seconds', or None.
    """
    if not log_text:
        return None

    text_lower = log_text.lower()

    # Weekly limit
    if re.search(r"weekly limit:.*0% left", text_lower):
        return {"scope": "weekly", "retry_after_seconds": 604800}

    # 5-hour limit
    if re.search(r"5h limit:.*0% left", text_lower):
        return {"scope": "5h", "retry_after_seconds": 18000}

    # Generic rate limit phrases (only if non-zero exit)
    if returncode != 0:
        rate_phrases = [
            "rate limit", "usage limit", "limit reached",
            "too many requests", "credits exhausted",
            "credits depleted", "buy additional credits",
        ]
        for phrase in rate_phrases:
            if phrase in text_lower:
                return {"scope": "unknown", "retry_after_seconds": 3600}

    return None


def sleep_for_rate_limit(seconds: int):
    """Sleep in chunks, logging progress."""
    end_time = time.time() + seconds
    while time.time() < end_time:
        remaining = int(end_time - time.time())
        logger.info(f"Rate limit: waiting {remaining}s...")
        time.sleep(min(300, remaining))  # 5-minute chunks


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------


def run_agent_session(
    run_dir: Path,
    workspace_src: Path,
    program_name: str,
    experiments: int,
) -> bool:
    """Run one Codex session (one experiment).

    Returns True if a new row was recorded, False otherwise.
    """
    existing_rows = results_row_count(run_dir)
    if existing_rows >= experiments:
        logger.info(f"Run complete: {existing_rows}/{experiments} experiments")
        return False

    # Build prompt
    prompt_text = build_agent_prompt(
        run_dir, program_name, experiments, existing_rows,
    )
    prompt_path = run_dir / "prompt.txt"
    with open(prompt_path, "w") as f:
        f.write(prompt_text)

    # Build environment for session_tools.py
    env = os.environ.copy()
    env["DEVELOPABILITY_RUN_DIR"] = str(run_dir)
    env["DEVELOPABILITY_RESULTS_TSV"] = str(run_dir / "results.tsv")
    env["DEVELOPABILITY_SRC_DIR"] = str(workspace_src)

    # Build Codex command
    command = [
        "codex",
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C", str(workspace_src),
        "--add-dir", str(run_dir),
        "-o", str(run_dir / "last_message.txt"),
        "-",
    ]

    session_log = run_dir / "agent_session.log"
    logger.info(f"Launching Codex session for experiment {existing_rows + 1}...")

    try:
        with open(prompt_path) as prompt_handle, \
             open(session_log, "a") as output_handle:
            output_handle.write(f"\n{'='*60}\n")
            output_handle.write(f"Experiment {existing_rows + 1} started at "
                                f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            output_handle.write(f"{'='*60}\n\n")

            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                env=env,
                stdin=prompt_handle,
                stdout=output_handle,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                timeout=AGENT_STEP_TIMEOUT,
            )
    except subprocess.TimeoutExpired:
        logger.warning(f"Codex session timed out after {AGENT_STEP_TIMEOUT}s")
        with open(session_log, "a") as f:
            f.write(f"\n[TIMEOUT after {AGENT_STEP_TIMEOUT}s]\n")
        return False
    except FileNotFoundError:
        logger.error("Codex CLI not found. Install with: "
                     "npm install -g @openai/codex")
        raise

    # Check for rate limits
    log_text = ""
    if session_log.exists():
        log_text = session_log.read_text()[-5000:]  # last 5KB

    rate_limit = detect_rate_limit(log_text, result.returncode)
    if rate_limit:
        logger.warning(f"Rate limit detected: {rate_limit['scope']}")
        if rate_limit["retry_after_seconds"] <= AUTO_WAIT_MAX_SECONDS:
            wait = rate_limit["retry_after_seconds"] + RATE_LIMIT_BUFFER
            sleep_for_rate_limit(wait)
        else:
            logger.error(f"Rate limit too long ({rate_limit['scope']}). "
                         "Stopping. Resume manually later.")
            return False

    # Check if a new row was recorded
    updated_rows = results_row_count(run_dir)
    if updated_rows > existing_rows:
        logger.info(f"Experiment recorded: row {updated_rows}/{experiments}")
        # Sync rank.py back to project
        sync_rank_py(workspace_src, run_dir)
        return True
    else:
        logger.warning("Codex session completed but no new row in results.tsv")
        return False


def run_loop(
    run_name: str = "default",
    program_name: str = "program.md",
    experiments: int = 50,
    dry_run: bool = False,
):
    """Run the full agent loop: spawn Codex sessions until target reached.

    Args:
        run_name: name for this run (used as directory name).
        program_name: which program.md to use.
        experiments: target number of experiments.
        dry_run: if True, print prompts without launching Codex.
    """
    run_dir = RESULTS_BASE / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # Create isolated workspace
    workspace_src = create_workspace(run_dir)

    logger.info("=" * 60)
    logger.info(f"Autoresearch loop: {run_name}")
    logger.info(f"  Program: {program_name}")
    logger.info(f"  Target: {experiments} experiments")
    logger.info(f"  Run dir: {run_dir}")
    logger.info(f"  Workspace: {workspace_src}")
    logger.info("=" * 60)

    if dry_run:
        prompt = build_agent_prompt(run_dir, program_name, experiments, 0)
        print("--- DRY RUN: Prompt for experiment 1 ---")
        print(prompt)
        print("--- END DRY RUN ---")
        return

    retries_without_progress = 0

    while True:
        existing = results_row_count(run_dir)
        if existing >= experiments:
            logger.info(f"Target reached: {existing}/{experiments} experiments")
            break

        success = run_agent_session(
            run_dir, workspace_src, program_name, experiments,
        )

        if success:
            retries_without_progress = 0
        else:
            retries_without_progress += 1
            if retries_without_progress >= AGENT_STEP_MAX_RETRIES:
                logger.error(
                    f"Agent stalled: {retries_without_progress} consecutive "
                    f"steps without progress. Stopping."
                )
                break
            logger.warning(
                f"No progress ({retries_without_progress}/"
                f"{AGENT_STEP_MAX_RETRIES} retries)"
            )

    # Finalize
    logger.info("=" * 60)
    logger.info("Loop complete. Generating summary...")

    env = os.environ.copy()
    env["DEVELOPABILITY_RUN_DIR"] = str(run_dir)
    env["DEVELOPABILITY_RESULTS_TSV"] = str(run_dir / "results.tsv")
    env["DEVELOPABILITY_SRC_DIR"] = str(workspace_src)

    subprocess.run(
        [sys.executable, str(workspace_src / "session_tools.py"), "summary"],
        env=env, cwd=workspace_src.parent,
    )

    # Copy final best rank.py back to project
    sync_rank_py(workspace_src, run_dir)

    final_rows = results_row_count(run_dir)
    logger.info(f"Final: {final_rows}/{experiments} experiments completed")
    logger.info(f"Results: {run_dir / 'results.tsv'}")
    logger.info(f"Summary: {run_dir / 'summary.json'}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Codex-driven autoresearch loop for ranking policy search",
    )
    parser.add_argument("--run-name", default="default",
                        help="Name for this run (directory name)")
    parser.add_argument("--program", default="program.md",
                        help="Program file for the agent (default: program.md)")
    parser.add_argument("--experiments", type=int, default=100,
                        help="Target number of experiments (default: 100)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt without launching Codex")
    args = parser.parse_args()

    run_loop(
        run_name=args.run_name,
        program_name=args.program,
        experiments=args.experiments,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
