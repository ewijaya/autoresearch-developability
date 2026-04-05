# Paper Outline

**Working title:** Autoresearch for multi-objective peptide developability:
iterative ranking-policy improvement on public benchmarks

**Target venue:** Workshop paper or short paper at a computational biology
or ML4Drug Discovery venue (e.g., NeurIPS ML4Molecules, ICML CompBio,
or Bioinformatics application note)

**Core claim:** An autoresearch-style loop — where an AI agent iteratively
edits a ranking policy against a fixed evaluation harness — can improve
multi-objective peptide candidate triage over static baselines using
entirely public data.

---

## 1. Introduction

- Peptide drug discovery requires simultaneous optimization across
  activity, toxicity, stability, and manufacturability
- Most AI-peptide work optimizes one endpoint at a time
- Karpathy's autoresearch showed autonomous iterative improvement
  works for language modeling via a constrained loop
- We adapt this paradigm: replace neural architecture search with
  ranking-policy search for multi-objective peptide selection
- Contribution: first application of autoresearch-style loops to
  multi-objective drug candidate ranking

## 2. Related work

- Multi-objective optimization in drug discovery (MOO, Pareto methods)
- Peptide property prediction (AMP, toxicity, stability models)
- Autonomous ML research (autoresearch, ML-agent-bench)
- Scalarization vs Pareto vs lexicographic ranking

## 3. Methods

### 3.1 Problem formulation
- Given: peptide candidate pool with estimated scores for K endpoints
- Goal: rank candidates to maximize discovery utility under all constraints
- Formal: ranking policy π maps score vectors to candidate orderings

### 3.2 Public benchmark bundle
- Activity: DBAASP antimicrobial MIC data
- Toxicity: ToxinPred3 binary labels + DBAASP hemolysis
- Stability: HLP half-life predictions
- Developability: rule-based proxy scores
- Integration: Approach B (separate endpoint models, unified candidate pool)

### 3.3 Fixed evaluation harness
- Data loading, split creation, leakage control (cluster-based)
- Endpoint scoring pipeline
- Ranking metrics: top-k enrichment, NDCG, hypervolume

### 3.4 Editable surface: ranking policy (rank.py)
- Scalarization, Pareto, lexicographic, uncertainty-aware strategies
- Agent makes one policy change per iteration
- Keep/discard decision based on summary metric

### 3.5 Baselines
- Activity-only ranking
- Toxicity-exclusion + activity ranking
- Equal-weight linear combination
- Random ranking among acceptable candidates
- Handcrafted rule-only ranking
- Agent-improved policy (the autoresearch loop output)

## 4. Results

### 4.1 Baseline comparison
- Table: all baselines on primary metrics (top-k enrichment, NDCG, hypervolume)
- **Figure 1:** Bar chart comparing baselines

### 4.2 Loop improvement trajectory
- **Figure 2:** Iteration number vs summary metric (scatter: keep/discard,
  line: running best)
- Analysis: what kinds of policy changes helped vs failed
- Phase 3: 20 iterations with linear scalarization (4-weight search)
- Phase 4: 50+ iterations with learnable policies (MLP, LambdaMART)
- Show that richer policy classes find structure beyond linear weights

### 4.3 Multi-objective vs single-objective
- **Table 2:** Multi-objective ranking quality vs single-endpoint ranking
- **Figure 3:** Pareto front visualization (activity vs safety, colored
  by ranking position under different policies)
- Three panels: activity-only, weighted-sum baseline, agent-improved
- Visual evidence that multi-objective ranking covers more of the front

### 4.4 Ablations
- **Figure 4:** Endpoint ablation heatmap
  - Remove each endpoint (set to constant mean) → measure degradation
  - Strategies: weighted_sum, agent_improved, rule_only
  - Shows which endpoints contribute most to each strategy
- **Figure 5:** Weight sensitivity analysis (Prompt 3b perturbations)
  - All single-weight perturbations around the optimum
  - Shows the current solution is a local optimum

### 4.5 Qualitative examples
- **Table 3:** Top 10 peptides with biggest rank changes between
  weighted_sum baseline and agent_improved, with full endpoint scores
- Highlight: peptides promoted (entered top-k) and demoted (left top-k)
- Interpretation: why the ranking change makes biological sense
  (e.g., promoted peptide has moderate activity but much lower toxicity)

### 4.6 Statistical significance
- **Table 4:** Bootstrap 95% CIs for all strategies on all metrics
  (1000 resamples on val split)
- **Figure 6:** Box plot of top-k enrichment across 10 random splits
- Report: which pairwise strategy differences are significant
- If agent_improved CI overlaps weighted_sum, state this honestly
  and discuss the practical vs statistical significance

## 5. Discussion

- What the loop found: which policy strategies dominate
- Limitations: synthetic benchmark, predicted endpoints, AMP-specific
- Transferability: how this framework maps to proprietary data
- When multi-objective ranking matters most (early triage vs late-stage)

## 6. Conclusion

- Autoresearch-style loops are applicable beyond language modeling
- Multi-objective framing is more realistic than single-endpoint ranking
- Public-data proof-of-concept; internal data is the next step

---

## Figure plan

| # | Type | File | Content | Section |
|---|---|---|---|---|
| 1 | Bar chart | `fig1_baseline_comparison.pdf` | All strategies on primary metrics with bootstrap error bars | 4.1 |
| 2 | Scatter + line | `fig2_loop_trajectory.pdf` | Iteration vs top-k enrichment, keep/discard colored, running best | 4.2 |
| 3 | Scatter (3-panel) | `fig3_pareto_front.pdf` | Activity vs safety, top-k highlighted under 3 strategies | 4.3 |
| 4 | Heatmap | `fig4_ablation_heatmap.pdf` | Endpoint ablation impact (delta top-k) per strategy | 4.4 |
| 5 | Bar chart | `fig5_weight_sensitivity.pdf` | Prompt 3b weight perturbation deltas | 4.4 |
| 6 | Box plot | `fig6_multi_split_boxplot.pdf` | Top-k enrichment distribution across 10 random splits | 4.6 |

All figures generated by: `python -m src.analysis --figures`

## Table plan

| # | Content | Section | Source |
|---|---|---|---|
| 1 | All strategies on all metrics | 4.1 | `evaluate.py` output |
| 2 | Multi-objective vs single-objective | 4.3 | ablation of endpoints |
| 3 | Endpoint ablation: delta per endpoint | 4.4 | `endpoint_ablation_val.csv` |
| 4 | Bootstrap 95% CIs for all strategies | 4.6 | `bootstrap_val_k20.csv` |
| 5 | Qualitative rank-change examples | 4.5 | `qualitative_examples_val.csv` |
| 6 | Dataset statistics | 3.2 | `manifest.json` |

---

## Strongest abstract claim (draft)

> We adapt the autoresearch paradigm — autonomous iterative code improvement
> against a fixed evaluation harness — from language modeling to peptide drug
> discovery. Our system iteratively refines a multi-objective ranking policy
> that triages peptide candidates across activity, toxicity, stability, and
> manufacturability constraints. On a public benchmark of 3,554 antimicrobial
> peptides built from DBAASP, ToxinPred3, and HLP datasets, the
> agent-improved policy achieves [X]+/-[Y] top-k enrichment (95% CI) vs
> [A]+/-[B] for the best static baseline, evaluated against a 3-oracle
> ensemble that resists reverse-engineering. Endpoint ablation confirms that
> all four objectives contribute to ranking quality. We release the full
> pipeline as a reusable framework for multi-objective peptide triage.

(Fill [X/Y/A/B] with actual bootstrap CI numbers after running analysis.)

## What we explicitly do NOT claim

- This is not a drug discovery system
- This does not replace wet-lab validation
- The public benchmark is not equivalent to proprietary data
- We do not claim the ranking policy generalizes to non-AMP peptides
- We do not claim AGI-for-drugs
