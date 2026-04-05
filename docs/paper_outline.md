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

### 4.3 Multi-objective vs single-objective
- **Table 2:** Multi-objective ranking quality vs single-endpoint ranking
- **Figure 3:** Pareto front visualization (activity vs toxicity, colored
  by ranking position under different policies)

### 4.4 Ablations
- Remove each endpoint → measure ranking quality drop
- Weight sensitivity analysis
- Bootstrap robustness across random splits

### 4.5 Qualitative examples
- **Table 3:** Example peptides whose rank changed significantly between
  baseline and agent-improved policy, with endpoint scores
- Interpretation: why the ranking change makes biological sense

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

| # | Type | Content | Section |
|---|---|---|---|
| 1 | Bar chart | Baseline comparison on primary metrics | 4.1 |
| 2 | Scatter + line | Loop trajectory (iteration vs metric) | 4.2 |
| 3 | Scatter (Pareto) | Activity vs toxicity, colored by rank | 4.3 |
| 4 | Heatmap | Endpoint weight sensitivity | 4.4 |
| 5 | Table-as-figure | Example peptides with changed rankings | 4.5 |

## Table plan

| # | Content | Section |
|---|---|---|
| 1 | All baselines on all metrics | 4.1 |
| 2 | Multi-objective vs single-objective | 4.3 |
| 3 | Ablation: endpoint removal | 4.4 |
| 4 | Dataset statistics | 3.2 |

---

## Strongest abstract claim (draft)

> We adapt the autoresearch paradigm — autonomous iterative code improvement
> against a fixed evaluation harness — from language modeling to peptide drug
> discovery. Our system iteratively refines a multi-objective ranking policy
> that triages peptide candidates across activity, toxicity, stability, and
> manufacturability constraints. On a public benchmark built from DBAASP,
> ToxinPred, and HLP datasets, the agent-improved policy achieves [X]%
> higher top-k enrichment and [Y]% greater hypervolume than the best static
> baseline, demonstrating that constrained autonomous loops can improve
> realistic drug candidate selection.

## What we explicitly do NOT claim

- This is not a drug discovery system
- This does not replace wet-lab validation
- The public benchmark is not equivalent to proprietary data
- We do not claim the ranking policy generalizes to non-AMP peptides
- We do not claim AGI-for-drugs
