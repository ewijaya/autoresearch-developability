#!/bin/bash
# auto_commit.sh — Auto-stage, commit, and push every hour via cron
# Skips if there are no changes to commit.

set -euo pipefail

REPO_DIR="/home/ubuntu/storage1/autoresearch-developability"
cd "$REPO_DIR"

# Check if there are any changes (tracked modifications or untracked results)
if git diff --quiet HEAD && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard -- results/ data/manifests/)" ]; then
    echo "$(date): No changes to commit" >> "$REPO_DIR/scripts/auto_commit.log"
    exit 0
fi

# Stage results and data manifests (not source code — that should be manual)
git add results/loops/*/results.tsv \
    results/loops/*/summary.json \
    results/ablations/ \
    results/figures/ \
    data/manifests/ \
    2>/dev/null || true

# Also stage any modified source files (from the Codex loop syncing rank.py back)
git add src/rank.py src/rank_learnable.py 2>/dev/null || true

# Check if staging produced anything
if git diff --cached --quiet; then
    echo "$(date): Nothing staged after add" >> "$REPO_DIR/scripts/auto_commit.log"
    exit 0
fi

# Count loop experiments for the commit message
LOOP_ROWS=$(tail -n +2 results/loops/prompt5/results.tsv 2>/dev/null | wc -l || echo 0)

git commit -m "chore: auto-commit loop progress (${LOOP_ROWS} experiments)"

git push origin HEAD 2>/dev/null || true

echo "$(date): Committed and pushed (${LOOP_ROWS} loop experiments)" >> "$REPO_DIR/scripts/auto_commit.log"
