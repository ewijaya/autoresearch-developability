# Program: autoresearch-developability

This project is inspired by and structurally derived from Karpathy's
[autoresearch](https://github.com/karpathy/autoresearch). It reuses the
domain-adaptation lessons from
[autoresearch-mol](https://github.com/ewijaya/autoresearch-mol).

## Research question

Can an autoresearch-style loop improve peptide candidate ranking under
multiple developability constraints using entirely public data?

## Architecture

```
Fixed harness (do not modify):
  src/prepare.py           – data loading, splits, leakage checks
  src/evaluate.py          – ranking metrics (NDCG, top-k enrichment, hypervolume)
  src/endpoint_activity.py – activity scoring
  src/endpoint_toxicity.py – toxicity scoring
  src/endpoint_stability.py – stability scoring
  src/endpoint_dev.py      – manufacturability / developability proxies
  src/analysis.py          – paper-evidence pipeline (bootstrap, ablations, figures)

Editable surface (agent modifies this):
  src/rank.py              – ranking policy (primary)
  src/rank_learnable.py    – learnable ranking policies (MLP, LambdaMART)

Loop infrastructure:
  src/session_tools.py     – experiment lifecycle (init, run, status, revert)
  src/run_agent_loop.py    – Codex-driven orchestrator (outer loop)
```

## Operating rules

1. Read `docs/PRD.md` before making any changes.
2. Treat every file except `src/rank.py` and `src/rank_learnable.py`
   as frozen unless explicitly instructed otherwise by the human operator.
3. Make **one coherent ranking-policy change** per iteration.
4. Run the evaluation harness via session_tools:
   `python session_tools.py run --description "what I changed"`
5. session_tools.py automatically records the result and handles
   keep/discard/revert.
6. **Keep** if the summary ranking metric improves.
7. **Discard** (revert) if it regresses or breaks interpretability.
8. Prefer simple, interpretable policies over complex ones.
9. Never fake progress with overfit heuristics.

## Automated loop (Codex agent)

The loop is driven by `src/run_agent_loop.py`, which spawns one-shot
Codex sessions. Each session makes exactly one policy change.

### How it works

```
run_agent_loop.py (outer Python loop)
  └─ for each experiment:
       1. Build prompt with current state
       2. codex exec -C workspace/src/ --add-dir run_dir/ -
       3. Codex agent reads program.md + rank.py + results.tsv
       4. Codex agent edits rank.py
       5. Codex agent runs: python session_tools.py run --description "..."
       6. session_tools.py evaluates, records result, reverts if discard
       7. Codex session exits
       8. Outer loop checks new row in results.tsv, repeats
```

### Running the loop

```bash
# 50 experiments with full policy search
python -m src.run_agent_loop --experiments 50 --run-name prompt5

# Preview the prompt without launching Codex
python -m src.run_agent_loop --experiments 5 --dry-run

# Resume a previous run (automatically skips completed experiments)
python -m src.run_agent_loop --experiments 50 --run-name prompt5
```

### For the Codex agent

When you are spawned by run_agent_loop.py:

1. Run `python session_tools.py init` first.
2. Run `python session_tools.py status` to see current state.
3. Run `python session_tools.py show-rank` to see current rank.py.
4. Edit `rank.py` with one coherent change.
5. Run `python session_tools.py run --description "what you changed"`.
6. Run `python session_tools.py status` to confirm the new row.
7. **Stop immediately.** Do not make a second change.

## What you may change in rank.py

- Scalarization strategy and objective weights
- Pareto ranking logic
- Lexicographic filtering thresholds
- Hard constraint filters vs soft penalty functions
- Uncertainty-aware ranking (if endpoint models expose uncertainty)
- Diversity bonus or redundancy penalty
- Top-k selection and tie-break logic

## What you may NOT change without explicit justification

- Dataset definitions or train/val/test splits
- Endpoint label assignments
- Fixed evaluation metrics
- Repository structure

## Experiment logging

Every iteration must produce one row in `results.tsv`:

```tsv
commit	summary_metric	topk_enrichment	hypervolume	ndcg	status	description
```

Status values: `keep`, `discard`, `crash`, `ambiguous`.

Description: one sentence saying exactly what changed in the ranking policy.

## Baselines

The following baselines must exist before the loop starts:

1. **activity-only** – rank by predicted activity alone
2. **toxicity-exclusion** – exclude toxic, rank remainder by activity
3. **weighted-sum** – fixed equal-weight linear combination
4. **random** – random ranking among non-excluded candidates
5. **rule-only** – handcrafted heuristic rules (no ML)
6. **agent-improved** – the autoresearch loop output

## Evaluation metrics

**Keep/discard metric hierarchy (LOCKED):**
1. **top-k enrichment** — primary summary metric for keep/discard decisions.
   This is the **mean enrichment across three oracle definitions** (Pareto
   rank, rank product, threshold-gated). No single oracle can be gamed.
2. **NDCG** — secondary; also averaged across oracles
3. **hypervolume** — diagnostic only; useful for understanding trade-offs,
   not for keep/discard gating

The per-oracle enrichment breakdown is logged in results.tsv for
diagnostics. Focus on the mean.

Other reported metrics:
- fraction of top-k satisfying all hard constraints
- diversity among top-k (sequence distance)
- per-oracle enrichment breakdown

## Iteration budget

Each ranking policy evaluation should complete in seconds, not minutes.
The constraint is policy quality, not compute. Aim for 20-50 iterations
in a single loop session.

## Success criteria

The loop is successful if at least one agent-edited policy demonstrably
outperforms the best static baseline on the primary metrics. If no
improvement is found, document that honestly — a negative result with
clean methodology is still valuable.

---

## Phase 4: Paper-strengthening loop

Phase 4 extends the autoresearch loop with richer policies, statistical
rigor, and publication-quality evidence. The fixed harness remains
frozen. The editable surface expands from `rank.py` alone to include
`rank_learnable.py` (learnable ranking policies).

### 4.1 Expanded editable surface

In addition to the linear scalarization in `rank.py`, the agent may
now iterate on:

- **`src/rank_learnable.py`** — MLP and LambdaMART ranking policies
  trained on oracle scores from the training split. The agent can
  modify architecture, hyperparameters, and training strategy.

Policies in `rank_learnable.py` are trained on **training data only**.
They are evaluated on val/test as usual. Leakage control is critical.

### 4.2 Bootstrap CI requirement

Every keep/discard decision in Phase 4 **must** include bootstrap
confidence intervals (95%, 1000 resamples). A policy that improves
the point estimate but whose CI overlaps the current best is logged
as `ambiguous`, not `keep`.

Run: `python -m src.analysis --bootstrap`

### 4.3 Required evidence for paper

Before the paper can be written, the following must exist in
`results/ablations/`:

1. **Bootstrap CIs** for all strategies (`bootstrap_val_k20.csv`)
2. **Multi-split robustness** across 10 random seeds (`multi_split_*.csv`)
3. **Endpoint ablation** for agent_improved and weighted_sum
   (`endpoint_ablation_val.csv`)
4. **Qualitative examples** of rank-changed peptides
   (`qualitative_examples_val.csv`)

Run all at once: `python -m src.analysis`

### 4.4 Figures

All figures are generated by `python -m src.analysis --figures`
and saved to `results/figures/`:

| # | File | Content |
|---|---|---|
| 1 | `fig1_baseline_comparison.pdf` | Grouped bar chart, all strategies |
| 2 | `fig2_loop_trajectory.pdf` | Iteration vs metric with keep/discard |
| 3 | `fig3_pareto_front.pdf` | Activity vs safety, top-k highlighted |
| 4 | `fig4_ablation_heatmap.pdf` | Endpoint importance heatmap |
| 5 | `fig5_weight_sensitivity.pdf` | Prompt 3b weight perturbations |
| 6 | `fig6_multi_split_boxplot.pdf` | Cross-split robustness |

### 4.5 ESM-2 embeddings (optional, GPU)

If `torch` and `fair-esm` are installed, `prepare.py` will generate
ESM-2 embeddings for the candidate pool. These are automatically used
by the toxicity and stability models if available:

```bash
pip install torch fair-esm
python -m src.prepare --skip-download   # re-runs with ESM features
```

### 4.6 Expanded iteration budget

Phase 4 targets 50-100 iterations with the learnable policies.
The linear scalarization is a solved baseline — Phase 4 asks whether
a nonlinear policy can find structure the linear one misses.

### 4.7 Cluster-aware splitting

If `mmseqs2` is installed, `prepare.py` will automatically use
cluster-aware splitting at 90% sequence identity. This is strongly
recommended before paper submission:

```bash
# Ubuntu/Debian
sudo apt-get install mmseqs2
# or conda
conda install -c bioconda mmseqs2

python -m src.prepare --skip-download   # re-splits with clustering
```
