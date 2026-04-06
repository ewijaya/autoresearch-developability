# autoresearch-developability

**An AI agent that learns to pick the best peptide drug candidates by balancing activity, toxicity, stability, and manufacturability at the same time.**

<p align="center">
  <img src="results/figures/fig2_loop_trajectory.png" alt="Autoresearch loop trajectory: 100 experiments, 12 kept improvements" width="700">
</p>
<p align="center"><em>The AI agent ran 100 autonomous experiments and kept 12 improvements, progressing from simple weight tuning to consensus voting to learned reranking.</em></p>

## The problem

Peptide drug discovery optimizes multiple properties simultaneously: a candidate must be potent against its target, non-toxic, metabolically stable, and manufacturable. Most computational tools optimize one property at a time, leaving the balancing act to human judgment. A peptide with excellent activity but poor toxicity is not a lead; it is an expensive distraction.

This project automates that balancing act. An AI agent iteratively improves a ranking policy that considers all four properties at once, surfacing the candidates most likely to survive downstream validation.

## How it works

The system has three parts:

1. **A scored candidate pool.** 3,554 antimicrobial peptides from the public [DBAASP](https://dbaasp.org) database, each scored on four endpoints: antimicrobial activity (measured), predicted toxicity, predicted stability, and a rule-based manufacturability penalty.

2. **A fixed evaluation harness.** Three independent definitions of "what makes a good candidate" (oracles) prevent the AI from gaming any single scoring formula. The primary metric measures how many of the truly best candidates appear in the AI's top-20 shortlist.

3. **An autonomous improvement loop.** A Codex agent (GPT-5.4) reads the current ranking policy, makes one change, evaluates it, and keeps the change only if it improves. Over 100 iterations, the agent discovered structural innovations that a human operator did not pre-specify: consensus voting across multiple ranking criteria, reciprocal rank fusion, and learned reranking models.

## Results at a glance

The AI-improved policy captures **65% of the best candidates** in its top-20 shortlist, compared to:

- **44%** for NSGA-II, the standard multi-objective optimization method
- **61%** for the best result from 1,000 random weight combinations
- **61%** for equal-weight scoring (the naive baseline)
- **4%** for random selection

The improvement holds across 10 independent data splits (p < 0.001 by sign test), with the AI-improved policy showing the most consistent performance (lowest variance).

NSGA-II achieves the best spread across the Pareto front, which is what it is designed for. But when the goal is to pick the top 20 candidates for expensive lab validation, concentrated selection outperforms diverse exploration.

## Use it with your data

The framework is designed as a drop-in system for proprietary peptide programs. To adapt it:

- **Swap the candidate pool** with your internal peptide library
- **Replace the endpoint models** with your own activity assays, toxicity screens, ADMET models, or any scoring functions
- **Run the loop** and let the agent discover the best way to combine your endpoints

The loop infrastructure, evaluation harness, and agent interface require no modification. Only the data pipeline (`src/prepare.py`) needs updating to point at your data sources.

## Quickstart

```bash
# 1. Prepare data (downloads DBAASP, ToxinPred3, HLP; ~10 min first run)
python -m src.prepare

# 2. Evaluate all baseline ranking policies
python -m src.evaluate

# 3. Evaluate a single strategy
python -m src.evaluate --strategy agent_improved --split val --k 20

# 4. Run tests
python -m pytest tests/ -v
```

## What the AI agent can change

The agent modifies only the ranking policy (`src/rank.py` and `src/rank_learnable.py`). Everything else is frozen:

- **Data pipeline and endpoint models** are fixed to prevent data leakage
- **Evaluation metrics and oracle definitions** are fixed to prevent gaming
- **Each iteration** produces exactly one change, evaluated and logged automatically

<details>
<summary><strong>Repository structure</strong></summary>

```
autoresearch-developability/
├── program.md                 # Agent operating manual
├── pyproject.toml             # Dependencies
├── src/
│   ├── prepare.py             # Fixed: data loading, splits, leakage control
│   ├── rank.py                # EDITABLE: ranking policy (agent modifies this)
│   ├── rank_learnable.py      # EDITABLE: learned ranking models (MLP, LambdaMART)
│   ├── evaluate.py            # Fixed: ranking metrics and oracle definitions
│   ├── features.py            # Fixed: physicochemical features
│   ├── endpoint_activity.py   # Fixed: activity scoring (DBAASP MIC)
│   ├── endpoint_toxicity.py   # Fixed: toxicity scoring (ToxinPred3)
│   ├── endpoint_stability.py  # Fixed: stability scoring (HLP)
│   ├── endpoint_dev.py        # Fixed: developability proxies (rule-based)
│   ├── analysis.py            # Paper-evidence pipeline (bootstrap, ablations, figures)
│   ├── run_agent_loop.py      # Outer loop orchestrator (spawns Codex sessions)
│   └── session_tools.py       # Experiment lifecycle (init, run, status, revert)
├── data/
│   ├── raw/                   # Downloaded public datasets
│   └── processed/             # Scored and split candidate pool
├── results/
│   ├── loops/                 # Experiment logs from all loop runs
│   ├── ablations/             # Endpoint ablation and robustness analyses
│   └── figures/               # Generated figures
├── manuscript/                # NeurIPS 2026 submission
├── docs/                      # Design documents and prompt history
└── tests/
```

</details>

## References

- Karpathy, A. [autoresearch](https://github.com/karpathy/autoresearch)
- Wijaya, E. [autoresearch-mol](https://github.com/ewijaya/autoresearch-mol)
- [DBAASP](https://dbaasp.org) -- antimicrobial peptide database
- [ToxinPred3](https://webs.iiitd.edu.in/raghava/toxinpred3/) -- peptide toxicity prediction
- [HLP](https://webs.iiitd.edu.in/raghava/hlp/) -- peptide half-life prediction

## License

MIT
