# autoresearch-developability

**An AI agent that learns to pick the best peptide drug candidates by balancing activity, toxicity, stability, and manufacturability at the same time.**

<p align="center">
  <a href="https://doi.org/10.64898/2026.04.19.719536"><img src="https://img.shields.io/badge/bioRxiv-10.64898%2F2026.04.19.719536-b31b1b.svg" alt="bioRxiv preprint"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/recall%4020-65%25-brightgreen.svg" alt="Recall@20: 65%">
  <img src="https://img.shields.io/badge/agent%20loop-100%20experiments-8A2BE2.svg" alt="Agent loop: 100 experiments">
</p>

<p align="center">
  <img src="results/figures/fig2_loop_trajectory.png" alt="Autoresearch loop trajectory: 100 experiments, 12 kept improvements" width="700">
</p>
<p align="center"><em>The AI agent ran 100 autonomous experiments and kept 12 improvements, progressing from simple weight tuning to consensus voting to learned reranking.</em></p>

> 📄 **Preprint posted on bioRxiv (2026-04-23):** Wijaya, E. *Agent-Guided Ranking Policy Improvement for Peptide Drug Candidate Prioritization.* [doi.org/10.64898/2026.04.19.719536](https://doi.org/10.64898/2026.04.19.719536)

## For biopharma teams

If your peptide program already has in-house activity, toxicity, stability, and manufacturability scores, this repository is a drop-in triage layer you can run on top:

- **Replace your hand-tuned scoring spreadsheet** with a ranking policy that is tuned automatically against your own assay data, not set by intuition.
- **Focus expensive synthesis and wet-lab validation** on the 20 candidates the policy judges most likely to pass — the point of triage is to do less work, better.
- **Keep your data proprietary.** The agent runs locally on your infrastructure; the public-data pipeline is only an example you swap out.

The academic claim (below) is supported on a public antimicrobial benchmark. The practical claim is that the pipeline is designed to port to proprietary programs with modest engineering effort — see **Pilot it on your data**.

## The problem

Peptide drug discovery optimizes multiple properties simultaneously: a candidate must be potent against its target, non-toxic, metabolically stable, and manufacturable. Most computational tools optimize one property at a time, leaving the balancing act to human judgment. A peptide with excellent activity but poor toxicity is not a lead; it is an expensive distraction.

This project automates that balancing act. An AI agent iteratively improves a ranking policy that considers all four properties at once, surfacing the candidates most likely to survive downstream validation.

## Results at a glance

On a public benchmark of 3,554 antimicrobial peptides from DBAASP, the AI-improved policy captures **65% of the best candidates** in its top-20 shortlist, compared to:

- **44%** for the standard multi-objective optimization method (NSGA-II, Non-dominated Sorting Genetic Algorithm)
- **61%** for the best result from 1,000 random weight combinations
- **61%** for equal-weight scoring (the naive baseline)

The improvement holds across 10 independent data splits (p < 0.001 by sign test), with the AI-improved policy showing the most consistent performance (lowest variance).

Standard multi-objective methods like NSGA-II are designed to spread candidates across the full trade-off frontier. But when the goal is to pick the top 20 candidates for expensive lab validation, concentrated selection outperforms diverse exploration.

**Is the AI doing real work?** The policy beats best-of-1,000 random weight search on the same scoring inputs (65% vs 61%), which is the closest honest comparison to "a prompt-wrapped random search". The agent discovered structural innovations — consensus voting across multiple ranking criteria, reciprocal rank fusion, and learned reranking — that no random weight sampling can reach.

## What it is not

To set expectations correctly:

- **Not a drug-discovery system.** This ranks candidates your program already has. It does not generate new peptides.
- **Not a replacement for wet-lab validation.** The output is a shortlist to synthesize and assay, not a decision to skip validation.
- **Not a clinical claim.** Results are on a public antimicrobial peptide benchmark. Generalization to non-AMP programs (cyclic peptides, GLP-1 analogs, oncology) is untested.
- **Not a generative model.** It consumes peptide scores; it does not propose new sequences.
- **Not autonomous in production.** The agent runs offline against a fixed candidate pool. It does not observe live assay feedback or take live actions.

## Pilot it on your data

The framework is designed as a drop-in system for proprietary peptide programs. Three things change; everything else stays fixed:

1. **Swap the candidate pool.** Replace the DBAASP download in `src/prepare.py` with a loader that pulls your internal peptide library (from a database, S3 bucket, or a local file). The loader must emit a table with one row per peptide and columns for each endpoint score.

2. **Replace the endpoint models.** The public version uses DBAASP MIC for activity, ToxinPred3 for toxicity, HLP for stability, and rule-based manufacturability. Swap these with your own activity assays, toxicity screens, ADMET models, or any scoring function — the loop treats each as a black-box scorer.

3. **Run the loop.** The agent reads the current ranking policy, proposes one change, evaluates it on your data's held-out split, and keeps the change only if it improves. The evaluation harness, ranking-policy search loop, and agent interface require no modification.

Realistic integration effort is measured in engineer-days, not engineer-months, for a team that already has its endpoint scores in tabular form. The longest path is usually wiring the data loader and agreeing on which three oracle definitions best represent your program's triage criteria. Once that is set, running the loop is a single command.

The evaluation harness is frozen by design: the agent is given read-only access to data and metrics, so it can only improve by writing better ranking code, not by reshaping the test.

## How it works

The system has three parts:

1. **A scored candidate pool.** 3,554 antimicrobial peptides from the public [DBAASP](https://dbaasp.org) database in the shipped example, each scored on four endpoints: antimicrobial activity (measured), predicted toxicity, predicted stability, and a rule-based manufacturability penalty.

2. **A fixed evaluation harness.** Three independent definitions of "what makes a good candidate" (oracles) prevent the AI from gaming any single scoring formula. The primary metric measures how many of the truly best candidates appear in the AI's top-20 shortlist.

3. **An autonomous improvement loop.** A Codex agent (GPT-5.4) reads the current ranking policy, makes one change, evaluates it, and keeps the change only if it improves. Over 100 iterations, the agent discovered structural innovations that a human operator did not pre-specify: consensus voting across multiple ranking criteria, reciprocal rank fusion, and learned reranking models.

## What the AI agent can change

The agent modifies only the ranking policy (`src/rank.py` and `src/rank_learnable.py`). Everything else is frozen:

- **Data pipeline and endpoint models** are fixed to prevent data leakage
- **Evaluation metrics and oracle definitions** are fixed to prevent gaming
- **Each iteration** produces exactly one change, evaluated and logged automatically

## Quickstart

The repository ships with a public-data demo so you can reproduce the benchmark before porting it.

```bash
# 1. Prepare public demo data (downloads DBAASP, ToxinPred3, HLP; ~10 min first run)
python -m src.prepare

# 2. Evaluate all baseline ranking policies
python -m src.evaluate

# 3. Evaluate a single strategy
python -m src.evaluate --strategy agent_improved --split val --k 20

# 4. Run tests
python -m pytest tests/ -v
```

To pilot on your own data: see **Pilot it on your data** above, then edit `src/prepare.py` to point at your sources and rerun step 2.

## Manuscript and references

A companion preprint reports the full methodology, baselines, ablations, and limitations:

- **Wijaya, E.** (2026). *Agent-Guided Ranking Policy Improvement for Peptide Drug Candidate Prioritization.* bioRxiv. [doi.org/10.64898/2026.04.19.719536](https://doi.org/10.64898/2026.04.19.719536) · [v1 on bioRxiv](https://www.biorxiv.org/cgi/content/short/2026.04.19.719536v1) · local copy: `manuscript/main.pdf`.

Prior art and data sources:

- Karpathy, A. [autoresearch](https://github.com/karpathy/autoresearch) — the iterative agent-edits-code-against-a-fixed-harness loop this repo adapts.
- Wijaya, E. [autoresearch-mol](https://github.com/ewijaya/autoresearch-mol) — companion project applying the same loop to molecular transformer architecture search.
- [DBAASP](https://dbaasp.org) — antimicrobial peptide database (activity).
- [ToxinPred3](https://webs.iiitd.edu.in/raghava/toxinpred3/) — peptide toxicity prediction.
- [HLP](https://webs.iiitd.edu.in/raghava/hlp/) — peptide half-life prediction.

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
├── manuscript/                # bioRxiv preprint
├── docs/                      # Design documents and prompt history
└── tests/
```

</details>

## License

MIT
