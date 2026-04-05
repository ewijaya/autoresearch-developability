#!/bin/bash
# run_all.sh — Full paper-evidence pipeline in one go
# Designed for g5.xlarge GPU instance
#
# Usage:
#   # Everything except agent loop (data, tests, analysis, figures)
#   nohup bash run_all.sh > results/run_all.log 2>&1 &
#
#   # Everything INCLUDING 50-experiment Codex agent loop
#   nohup bash run_all.sh --with-loop > results/run_all.log 2>&1 &
#
#   # Agent loop only (after run_all.sh has completed once)
#   nohup bash run_all.sh --loop-only > results/run_all.log 2>&1 &
#
# Expected time:
#   Without loop: ~30-60 min
#   With loop: ~4-8 hours (depends on Codex rate limits)
set -euo pipefail

WITH_LOOP=false
LOOP_ONLY=false
RUN_NAME="prompt5"
EXPERIMENTS=100

for arg in "$@"; do
    case "$arg" in
        --with-loop)  WITH_LOOP=true ;;
        --loop-only)  LOOP_ONLY=true ;;
        --run-name=*) RUN_NAME="${arg#*=}" ;;
        --experiments=*) EXPERIMENTS="${arg#*=}" ;;
    esac
done

echo "============================================================"
echo "autoresearch-developability: full pipeline"
echo "Started: $(date)"
echo "  with-loop=$WITH_LOOP  loop-only=$LOOP_ONLY"
echo "  run-name=$RUN_NAME  experiments=$EXPERIMENTS"
echo "============================================================"

cd "$(dirname "$0")"

if [ "$LOOP_ONLY" = false ]; then

    # --- Step 0: Install optional dependencies ---
    echo ""
    echo "--- Step 0: Installing dependencies ---"
    pip install torch fair-esm lightgbm matplotlib seaborn 2>&1 | tail -5
    echo "Dependencies installed."

    # --- Step 1: Re-prepare with ESM-2 embeddings (GPU) ---
    echo ""
    echo "============================================================"
    echo "--- Step 1: Re-prepare data with ESM-2 embeddings ---"
    echo "Started: $(date)"
    echo "============================================================"
    python -m src.prepare --skip-download
    echo "Step 1 DONE: $(date)"

    # --- Step 2: Run tests to verify pipeline integrity ---
    echo ""
    echo "============================================================"
    echo "--- Step 2: Running tests ---"
    echo "Started: $(date)"
    echo "============================================================"
    python -m pytest tests/ -v --tb=short || echo "WARNING: some tests failed (non-fatal, continuing)"
    echo "Step 2 DONE: $(date)"

    # --- Step 3: Full paper-evidence pipeline ---
    echo ""
    echo "============================================================"
    echo "--- Step 3: Full analysis pipeline ---"
    echo "  (bootstrap, multi-split, ablation, examples, figures)"
    echo "Started: $(date)"
    echo "============================================================"
    python -m src.analysis
    echo "Step 3 DONE: $(date)"

    # --- Step 4: Re-evaluate all strategies with updated data ---
    echo ""
    echo "============================================================"
    echo "--- Step 4: Re-evaluate all strategies ---"
    echo "Started: $(date)"
    echo "============================================================"
    python -m src.evaluate --split val --k 20
    echo "Step 4 DONE: $(date)"

fi  # end LOOP_ONLY check

# --- Step 5: Codex agent loop (optional) ---
if [ "$WITH_LOOP" = true ] || [ "$LOOP_ONLY" = true ]; then
    echo ""
    echo "============================================================"
    echo "--- Step 5: Codex agent loop ---"
    echo "  Run: $RUN_NAME, Target: $EXPERIMENTS experiments"
    echo "Started: $(date)"
    echo "============================================================"

    # Check codex is installed
    if ! command -v codex &> /dev/null; then
        echo "ERROR: Codex CLI not found."
        echo "Install with: npm install -g @openai/codex"
        echo "Skipping agent loop."
    else
        python -m src.run_agent_loop \
            --run-name "$RUN_NAME" \
            --experiments "$EXPERIMENTS"
        echo "Step 5 DONE: $(date)"

        # Re-run analysis with new loop results
        echo ""
        echo "--- Step 5b: Re-generating figures with loop data ---"
        python -m src.analysis --figures
        echo "Step 5b DONE: $(date)"
    fi
fi

echo ""
echo "============================================================"
echo "ALL DONE: $(date)"
echo "============================================================"
echo ""
echo "Outputs:"
echo "  Figures:    results/figures/"
echo "  Ablations:  results/ablations/"
echo "  Results:    results.tsv"
echo "  Loop logs:  results/loops/$RUN_NAME/"
echo ""
ls -la results/figures/ 2>/dev/null || echo "  (no figures yet)"
ls -la results/ablations/ 2>/dev/null || echo "  (no ablations yet)"
ls -la results/loops/$RUN_NAME/results.tsv 2>/dev/null || echo "  (no loop results yet)"
