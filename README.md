# autoresearch-developability

Multi-objective peptide candidate ranking via an autoresearch-style
iterative loop on public data.

## What this is

An autonomous loop iteratively improves a **ranking policy** that triages
peptide drug candidates across four competing objectives:

| Endpoint | Source | Type |
|---|---|---|
| Activity | DBAASP antimicrobial MIC | Quantitative (log MIC) |
| Toxicity | ToxinPred3 | Binary classification |
| Stability | HLP half-life | Quantitative (log t½) |
| Developability | Rule-based sequence analysis | Composite penalty |

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

## Repository structure

```
autoresearch-developability/
├── program.md                 # Agent operating manual
├── pyproject.toml             # Dependencies
├── src/
│   ├── prepare.py             # Fixed: data loading, splits, leakage control
│   ├── rank.py                # EDITABLE: ranking policy (agent modifies this)
│   ├── evaluate.py            # Fixed: ranking metrics
│   ├── endpoint_activity.py   # Fixed: activity scoring
│   ├── endpoint_toxicity.py   # Fixed: toxicity scoring
│   ├── endpoint_stability.py  # Fixed: stability scoring
│   └── endpoint_dev.py        # Fixed: developability proxies
├── data/
│   ├── raw/                   # Downloaded public datasets
│   ├── processed/             # Harmonized benchmark files
│   └── manifests/             # Dataset metadata and download records
├── results/
│   ├── baseline/              # Baseline policy outputs
│   ├── loops/                 # Autoresearch loop experiment logs
│   ├── ablations/             # Ablation study outputs
│   └── figures/               # Paper-quality visualizations
├── docs/
│   ├── PRD.md                 # Product requirements document
│   ├── dataset_notes.md       # Dataset selection rationale
│   └── paper_outline.md       # Paper structure and claim plan
└── tests/
```

## The loop

```
1. Establish baseline (current rank.py)
2. Make one coherent policy change
3. Run evaluation harness
4. Log result in results.tsv
5. Keep if metrics improve, discard if they regress
6. Repeat
```

See `program.md` for the full agent operating rules.

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

- **Top-k enrichment:** fraction of true top candidates captured in top-k
- **NDCG:** normalized discounted cumulative gain
- **Hypervolume:** dominated volume in multi-objective space
- Bootstrap robustness, diversity, constraint satisfaction

## Status

**Phase 1: Scaffold** — complete. Repo structure, program.md, dataset
plan, paper outline, and baseline ranking policies are defined.

**Next:** Phase 2 — implement the fixed harness (`prepare.py`, `evaluate.py`,
endpoint modules) and run one end-to-end dry run.

## References

- Karpathy, A. [autoresearch](https://github.com/karpathy/autoresearch)
- Wijaya, E. [autoresearch-mol](https://github.com/ewijaya/autoresearch-mol)
- [DBAASP](https://dbaasp.org) — antimicrobial peptide database
- [ToxinPred3](https://webs.iiitd.edu.in/raghava/toxinpred3/) — peptide toxicity
- [HLP](https://webs.iiitd.edu.in/raghava/hlp/) — peptide half-life prediction

## License

MIT
