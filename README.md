# autoresearch-developability

Multi-objective peptide candidate ranking via an autoresearch-style
iterative loop on public data.

## What this is

An autonomous loop iteratively improves a **ranking policy** that triages
peptide drug candidates across four competing objectives:

| Endpoint | Source | Type | On candidate pool |
|---|---|---|---|
| Activity | DBAASP antimicrobial MIC | Quantitative (log MIC) | **Ground truth** |
| Toxicity | ToxinPred3 RF model | Binary classification | Predicted (held-out AUC 0.920) |
| Stability | HLP RF model | Quantitative (log t½) | Predicted (held-out R² 0.547) |
| Developability | Rule-based sequence analysis | Composite penalty | Computed (deterministic) |

The loop follows Karpathy's [autoresearch](https://github.com/karpathy/autoresearch)
discipline: a **fixed evaluation harness** and a **single editable file**
(`src/rank.py`). The agent makes one policy change per iteration, evaluates,
and keeps or discards.

This repo also builds on domain-adaptation lessons from
[autoresearch-mol](https://github.com/ewijaya/autoresearch-mol).

## Why this matters

Most AI-peptide work optimizes one endpoint at a time. That is
scientifically incomplete. A peptide with high activity but poor toxicity
or bad stability is not a lead — it is an expensive distraction.

This repo asks: **can an autoresearch-style loop improve multi-objective
peptide triage on public data?**

The public benchmark is the proof-of-concept. The framework is designed
for obvious portability to proprietary peptide data.

## Quickstart

```bash
# 1. Prepare data (downloads DBAASP, ToxinPred3, HLP; ~10 min first run)
python -m src.prepare

# 2. Evaluate all baseline ranking policies
python -m src.evaluate

# 3. Evaluate a single strategy
python -m src.evaluate --strategy weighted_sum --split val --k 20

# 4. Run tests
python -m pytest tests/ -v
```

### Current benchmark numbers (val split, k=20, mean across 3 oracles)

| Strategy | TopK Enrichment | NDCG | Hypervolume | Feasible |
|---|---|---|---|---|
| activity_only | 0.083 | 0.62 | 0.29 | 0.00 |
| toxicity_exclusion | 0.300 | 0.79 | 0.53 | 1.00 |
| weighted_sum | 0.517 | 0.89 | 0.57 | 0.55 |
| **agent_improved** | **0.550** | **0.94** | **0.56** | **0.80** |
| rule_only | 0.367 | 0.83 | 0.51 | 0.50 |
| random | 0.017 | 0.52 | 0.43 | 0.15 |

**Candidate pool:** 3,554 antimicrobial peptides from DBAASP (E. coli ATCC 25922).
**TopK enrichment is the mean across three oracle definitions** (Pareto rank,
rank product, threshold-gated). See "Benchmark honesty" below.

### Current official best policy

The official winner after Prompt 3 and Prompt 3b is `agent_improved` in
`src/rank.py`, using the same weighted-sum policy class as `weighted_sum`
with tuned weights:

```text
score =
  0.45 * norm(activity)
  - 0.40 * norm(toxicity)
  + 0.25 * norm(stability)
  - 0.15 * norm(dev_penalty)
```

Prompt 3b produced nearby **ties** but no clean primary-metric win, so the
official policy was **not** changed. See `docs/prompt3-summary.md`.

## Repository structure

```
autoresearch-developability/
├── program.md                 # Agent operating manual
├── pyproject.toml             # Dependencies
├── results.tsv                # Top-level loop log snapshot / compatibility copy
├── src/
│   ├── prepare.py             # Fixed: data loading, splits, leakage control
│   ├── rank.py                # EDITABLE: ranking policy (agent modifies this)
│   ├── evaluate.py            # Fixed: ranking metrics
│   ├── features.py            # Fixed: AAindex physicochemical features
│   ├── endpoint_activity.py   # Fixed: activity scoring (DBAASP MIC)
│   ├── endpoint_toxicity.py   # Fixed: toxicity scoring (ToxinPred3 RF)
│   ├── endpoint_stability.py  # Fixed: stability scoring (HLP RF)
│   └── endpoint_dev.py        # Fixed: developability proxies (rule-based)
├── data/
│   ├── raw/                   # Downloaded public datasets
│   ├── processed/             # Harmonized benchmark files
│   └── manifests/             # Dataset metadata and download records
├── results/
│   ├── baseline/              # Baseline evaluation outputs
│   ├── loops/                 # Archived loop-session logs
│   │   └── prompt3_prompt3b_results.tsv
│   ├── ablations/             # Reserved for ablation outputs
│   └── figures/               # Reserved for figures
├── docs/
│   ├── PRD.md                 # Product requirements document
│   ├── dataset_notes.md       # Dataset selection rationale
│   ├── paper_outline.md       # Paper structure and claim plan
│   └── prompt3-summary.md     # Prompt 3 / 3b checkpoint and official winner
└── tests/
```

## The loop

```
1. Establish baseline (current rank.py)
2. Make one coherent policy change
3. Run evaluation harness
4. Log result in `results/loops/<session>.tsv` (optionally mirror to `results.tsv`)
5. Keep if metrics improve, discard if they regress
6. Repeat
```

See `program.md` for the full agent operating rules.

### Loop log location

Future loop-session logs should be written under `results/loops/` using a
session-specific filename such as `results/loops/prompt4_results.tsv`.
The root `results.tsv` is kept as a top-level snapshot / compatibility file;
`docs/prompt3-summary.md` is the narrative checkpoint for the current official
winner.

## Baselines

| # | Policy | Description |
|---|---|---|
| 1 | activity-only | Rank by predicted activity alone |
| 2 | toxicity-exclusion | Exclude toxic, rank rest by activity |
| 3 | weighted-sum | Equal-weight linear combination |
| 4 | random | Random ranking among candidates |
| 5 | rule-only | Handcrafted heuristic filters |
| 6 | agent-improved | Output of the autoresearch loop |

## Metrics

- **Top-k enrichment (primary):** mean fraction of oracle-top-k candidates
  captured in the policy's top-k, **averaged across three independent oracle
  definitions**. No single oracle can be reverse-engineered to win.
- **NDCG:** normalized discounted cumulative gain, also averaged across oracles
- **Hypervolume:** dominated area in (activity, 1−toxicity) space for top-k
- **Feasible fraction:** share of top-k satisfying all hard constraints

### Oracle ensemble

The benchmark uses three structurally different oracles to define "what
is a good candidate." Top-k enrichment and NDCG are reported as the
mean across all three. This prevents an agent from gaming one formula.

| Oracle | Definition | Resists linear approx? |
|---|---|---|
| **Pareto rank** | Count of dominating candidates across all 4 endpoints | Yes (combinatorial, no weights) |
| **Rank product** | Geometric mean of per-endpoint ranks | Partially (nonlinear) |
| **Threshold gate** | Activity×stability with sigmoid gates on toxicity and dev_penalty | Yes (sharp nonlinearities) |

No single strategy wins all three oracles. `weighted_sum` leads on
`rank_product` and `threshold_gate` but ties on `pareto_rank`.

## Benchmark honesty

This is a **synthetic multi-objective benchmark**. The claim is about the
framework, not about solving peptide drug discovery.

- Only **activity** has experimental ground truth on the candidate pool
  (DBAASP MIC values for E. coli ATCC 25922)
- **Toxicity** is predicted by an RF model trained on ToxinPred3 data
  (held-out AUC 0.920; 8.9% of candidates overlap with ToxinPred3 training)
- **Stability** is predicted by an RF model trained on 375 HLP peptides
  (held-out R² 0.547 — weak; cross-domain generalization is uncertain)
- **Developability** is a deterministic rule-based score, not empirical
- The **oracle definitions** are design choices, not biological truth.
  We mitigate this by using three structurally diverse oracles and
  reporting the mean.
- Splitting is random (mmseqs2 cluster-aware splitting is supported but
  not yet installed)

## Status

**Phase 1: Scaffold** — complete.
**Phase 2: Fixed harness** — complete. All endpoint models trained,
baseline policies evaluated, end-to-end pipeline works.
**Phase 3: Initial loop and local robustness check** — complete.
`agent_improved` is the current official winner over the original
`weighted_sum` baseline.

**Next recommended stage:** stop optimization here, preserve the current
winner, and begin the next explicitly scoped evaluation or reporting phase
from `docs/prompt3-summary.md`.

## References

- Karpathy, A. [autoresearch](https://github.com/karpathy/autoresearch)
- Wijaya, E. [autoresearch-mol](https://github.com/ewijaya/autoresearch-mol)
- [DBAASP](https://dbaasp.org) — antimicrobial peptide database
- [ToxinPred3](https://webs.iiitd.edu.in/raghava/toxinpred3/) — peptide toxicity
- [HLP](https://webs.iiitd.edu.in/raghava/hlp/) — peptide half-life prediction

## License

MIT
