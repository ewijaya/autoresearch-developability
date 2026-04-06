# Manuscript PRD: autoresearch-developability

**Working title:** Autonomous Multi-Objective Peptide Ranking via Iterative
Policy Search on Public Benchmarks

**Target venue:** NeurIPS 2026 Workshop on ML for Molecules (4-page + appendix),
or Bioinformatics Application Note (4-page)

**Companion paper:** Wijaya, 2026. "What an Autonomous Agent Discovers About
Molecular Transformer Design: Does It Transfer?" arXiv:2603.28015
https://arxiv.org/abs/2603.28015

**Companion repo:** `autoresearch-mol` (architecture search for molecular
transformers — same autoresearch framework, different domain)

**Status:** All experiments complete. All figures generated. Ready to write.

---

## 1. Core Claim

An autonomous Codex-driven loop — where an LLM agent iteratively edits a
ranking policy against a fixed evaluation harness — can improve multi-objective
peptide candidate triage over static baselines and standard multi-objective
optimization methods, using entirely public data.

**Specifically:**
- Agent-improved policy achieves 0.717 top-k enrichment vs 0.650 for the
  equal-weight baseline, 0.617 for best-of-1000 random weight search, and
  0.567 for NSGA-II (a standard multi-objective optimization method).
- 12 kept improvements out of 100 experiments, progressing from simple
  weight tuning to oracle consensus voting to learned MLP+LambdaMART
  ensembles — structural innovation, not just hyperparameter search.
- The framework is designed for obvious portability to proprietary peptide data.

---

## 2. What We Explicitly Do NOT Claim

- This is not a drug discovery system
- This does not replace wet-lab validation
- The public benchmark is not equivalent to proprietary data
- We do not claim the ranking policy generalizes to non-AMP peptides
- The bootstrap CIs overlap at 95% for agent_improved vs weighted_sum
  (practical improvement, not statistically significant at that threshold)
- The stability model is weak (R^2 = 0.547) and this is acknowledged

---

## 3. Manuscript Structure

Follow the `autoresearch-mol` manuscript layout exactly. Each section is a
separate `.tex` file under `manuscript/sections/`. The `main.tex` file
`\input{}`s them in order.

### 3.1 Directory Layout

```
manuscript/
  main.tex                    # Master file, inputs all sections
  neurips_2026.sty            # Style file (copy from autoresearch-mol)
  references.bib              # Bibliography
  sections/
    abstract.tex
    introduction.tex
    related_work.tex
    methodology.tex
    results.tex
    discussion.tex
    conclusion.tex
    ethics.tex
    reproducibility.tex
    supplementary.tex
  figures/                    # Symlink or copy from results/figures/
    fig1_baseline_comparison.pdf
    fig2_loop_trajectory.pdf
    fig3_pareto_front.pdf
    fig4_ablation_heatmap.pdf
    fig5_weight_sensitivity.pdf
    fig6_multi_split_boxplot.pdf
  tables/                     # LaTeX table fragments (optional)
```

### 3.2 `main.tex`

```latex
\documentclass{article}
\usepackage[preprint]{neurips_2026}
\usepackage{booktabs, graphicx, amsmath, amssymb}
\usepackage{hyperref, xcolor, multirow, subcaption, enumitem}

\title{Autonomous Multi-Objective Peptide Ranking via
       Iterative Policy Search on Public Benchmarks}

\author{
  Edward Wijaya \\
  StemRIM, Inc. \\
  \texttt{wijaya@stemrim.com}
}

\begin{document}
\maketitle
\input{sections/abstract}
\input{sections/introduction}
\input{sections/related_work}
\input{sections/methodology}
\input{sections/results}
\input{sections/discussion}
\input{sections/conclusion}
\bibliographystyle{plainnat}
\bibliography{references}
\appendix
\input{sections/ethics}
\input{sections/reproducibility}
\input{sections/supplementary}
\end{document}
```

---

## 4. Section-by-Section Writing Guide

### 4.1 `abstract.tex` (~150 words)

**Structure:** Problem → Gap → Method → Result → Implication

**Key sentences to hit:**
- Peptide drug discovery requires simultaneous optimization across activity,
  toxicity, stability, and manufacturability
- Most AI-peptide work optimizes one endpoint at a time
- We adapt Karpathy's autoresearch paradigm: a Codex agent iteratively edits
  a ranking policy against a fixed evaluation harness
- On a public benchmark of 3,554 antimicrobial peptides from DBAASP,
  100 autonomous experiments improved top-k enrichment from 0.683 to 0.717
  (H-mean of TopK and NDCG from 0.802 to 0.828)
- The agent-improved policy outperforms NSGA-II (0.717 vs 0.567) and
  best-of-1000 random weight search (0.717 vs 0.617)
- We release the full pipeline as a reusable framework

**Tone:** Factual, no hype. "Proof-of-concept" and "public benchmark" appear early.

### 4.2 `introduction.tex` (~1.5 pages)

**Paragraph plan:**

1. **The multi-objective problem.** Peptide candidates must survive a portfolio
   of constraints: activity, toxicity, stability, manufacturability. A peptide
   with high activity but poor toxicity is not a lead — it is an expensive
   distraction. Most AI-peptide work optimizes one endpoint at a time.

2. **The autoresearch paradigm.** Karpathy's autoresearch showed that an LLM
   agent can iteratively improve a system through a tight loop around a fixed
   evaluation harness and a single editable file. Our companion paper
   \cite{wijaya2026autonomousagentdiscoversmolecular} demonstrated this for
   molecular transformer architecture search across SMILES, protein, and NLP
   domains (3,106 experiments). Here we adapt the same paradigm to
   multi-objective ranking policy search for peptide candidate triage.

3. **What we do.** We build a public benchmark from DBAASP (antimicrobial MIC),
   ToxinPred3 (toxicity), HLP (stability), and rule-based developability
   proxies. A Codex agent (gpt-5.4) runs 100 experiments, iteratively editing
   a ranking policy. The evaluation harness uses a 3-oracle ensemble to
   prevent reverse-engineering.

4. **What we find.** The agent progresses from simple weight tuning to
   two-stage reranking to oracle consensus voting to learned MLP+LambdaMART
   ensembles. The final policy outperforms all baselines including NSGA-II.

5. **Contributions:**
   - First application of autoresearch-style loops to multi-objective peptide ranking
   - A public multi-objective peptide benchmark with 3-oracle evaluation
   - Empirical comparison of autonomous policy search vs standard MOO methods
   - Open-source framework portable to proprietary peptide data

**Citations needed:**
- Karpathy autoresearch
- autoresearch-mol (our companion paper)
- DBAASP database
- ToxinPred3
- HLP
- NSGA-II (Deb et al., 2002)
- Multi-objective drug discovery surveys
- PeptideRanker, AMP prediction tools

### 4.3 `related_work.tex` (~0.75 pages)

**Three subsections:**

1. **Multi-objective optimization in drug discovery.**
   NSGA-II, MOEA/D, Pareto methods for molecular optimization.
   Scalarization vs Pareto vs lexicographic ranking.
   Most work focuses on small molecules, not peptides.

2. **Peptide property prediction.**
   Antimicrobial peptide prediction (AMP), toxicity (ToxinPred),
   stability (HLP), developability proxies.
   Most tools predict single endpoints; few address multi-objective ranking.

3. **Autonomous ML research.**
   Karpathy's autoresearch, ML-Agent-Bench, AI Scientist.
   Our companion paper \cite{wijaya2026autonomousagentdiscoversmolecular}
   applied this to molecular transformer design across 3 domains with
   3,106 experiments — this paper extends it from architecture search
   (single metric: val\_bpb) to ranking policy search (multi-objective).
   The one-editable-file + fixed-harness discipline.

### 4.4 `methodology.tex` (~1.5 pages)

**Subsections:**

1. **Problem formulation (Section 3.1).**
   Given a candidate pool with estimated scores for K endpoints, rank
   candidates to maximize discovery utility under all constraints.
   Formally: ranking policy pi maps score vectors to candidate orderings.

2. **Public benchmark bundle (Section 3.2).**
   - Activity: DBAASP antimicrobial MIC for E. coli ATCC 25922 (3,554 peptides)
   - Toxicity: RF classifier on ToxinPred3 data (held-out AUC 0.920)
   - Stability: RF regressor on HLP data (held-out R^2 0.547 — weak, acknowledged)
   - Developability: deterministic rule-based penalty (7 rules)
   - ESM-2 embeddings (8M model) augment toxicity/stability features
   - **Table: Dataset statistics** (source data from manifest.json)

3. **Fixed evaluation harness (Section 3.3).**
   - 3-oracle ensemble: Pareto rank, rank product, threshold-gated
   - Primary metric: mean top-k enrichment across 3 oracles (k=20)
   - Secondary: NDCG (also oracle-averaged)
   - Diagnostic: hypervolume, feasible fraction
   - Why 3 oracles: prevents the agent from gaming any single formula

4. **Autoresearch loop (Section 3.4).**
   - Architecture: run_agent_loop.py spawns one-shot Codex sessions
   - Each session: read program.md + rank.py + results.tsv → edit rank.py
     → evaluate → keep/discard → next session
   - Codex model: gpt-5.4 with xhigh reasoning effort
   - Workspace isolation: each session gets a copy of src/
   - session_tools.py handles evaluation, logging, revert-on-regression
   - Budget: 100 experiments
   - **Figure: Architecture diagram** (optional — describe the loop visually)

5. **Baselines (Section 3.5).**
   - activity-only, toxicity-exclusion, weighted-sum (equal weights),
     random, rule-only: internal baselines
   - random-weight-search (best of 1000 Dirichlet samples): proves
     the loop beats blind search over the same policy class
   - NSGA-II with crowding distance: standard external MOO baseline
   - agent-improved: the loop's output

### 4.5 `results.tex` (~1.5 pages)

**Subsections:**

1. **Strategy comparison (Section 4.1).**
   - **Table 1:** All 8 strategies on all metrics with bootstrap 95% CIs
   - **Figure 1:** `fig1_baseline_comparison.pdf` — grouped bar chart
   - Key finding: agent_improved (0.650 TopK, CI [0.533, 0.767]) beats
     all baselines on point estimates. CIs overlap with weighted_sum
     but not with NSGA-II or random.
   - Data source: `results/ablations/bootstrap_val_k20.csv`

2. **Loop trajectory (Section 4.2).**
   - **Figure 2:** `fig2_loop_trajectory.pdf` — Karpathy-style staircase
   - 100 experiments, 12 keeps, H-mean from 0.802 to 0.828
   - Trajectory: weight tuning → two-stage reranking → oracle consensus
     → learned ensemble (3 structural phases)
   - **Table 2:** The 12 kept experiments with descriptions
   - Data source: `results/loops/prompt5/results.tsv`

3. **Multi-objective vs single-objective (Section 4.3).**
   - **Figure 3:** `fig3_pareto_front.pdf` — activity vs safety, 3 panels
   - activity_only clusters in high-activity/low-safety corner
   - agent_improved covers more of the Pareto front

4. **Endpoint ablation (Section 4.4).**
   - **Figure 4:** `fig4_ablation_heatmap.pdf` — delta when each endpoint
     is set to constant mean
   - Key finding: all 4 endpoints contribute to ranking quality
   - Dropping stability hurts rule_only most (-0.200)
   - agent_improved is more robust to ablation than rule_only
   - Data source: `results/ablations/endpoint_ablation_val.csv`

5. **Cross-split robustness (Section 4.5).**
   - **Figure 6:** `fig6_multi_split_boxplot.pdf` — box plot across 10 splits
   - agent_improved: 0.650 +/- 0.034 vs weighted_sum: 0.585 +/- 0.050
   - Improvement is consistent across splits (non-overlapping IQRs)
   - Data source: `results/ablations/multi_split_summary.csv`

6. **Statistical significance (Section 4.6).**
   - Bootstrap CIs at 95%: agent_improved [0.533, 0.767] vs
     weighted_sum [0.483, 0.733] — overlapping
   - Multi-split means: 0.650 vs 0.585 with smaller std — more convincing
   - Honest statement: practical improvement, marginal statistical significance
   - The small k=20 window makes CIs inherently wide

### 4.6 `discussion.tex` (~0.75 pages)

**Paragraph plan:**

1. **What the loop found.** Structural progression from linear weights to
   consensus voting to learned ensembles. The agent independently discovered
   oracle-consensus voting — a form of ensemble agreement selection.

2. **Agent search vs random search.** The loop outperforms best-of-1000
   random weight search (0.717 vs 0.617), proving directed policy search
   adds value over blind exploration.

3. **Agent search vs NSGA-II.** NSGA-II optimizes for Pareto spread, not
   top-k concentration. This makes it the wrong tool for candidate triage
   where you want the best 20, not a diverse frontier.

4. **Limitations.**
   - Synthetic benchmark: only activity is ground truth; toxicity and
     stability are predicted
   - Stability model is weak (R^2 0.547)
   - Bootstrap CIs overlap for the closest comparison
   - Random splitting (mmseqs2 cluster splitting not yet applied)
   - 8.9% ToxinPred3 training overlap (flagged, not fully controlled)
   - Oracle definitions are design choices, not biological truth
   - Single candidate pool, single organism (E. coli)

5. **Portability.** The framework is designed for drop-in replacement of
   endpoint models and candidate pools. The ranking policy search is
   agnostic to the underlying data source.

### 4.7 `conclusion.tex` (~0.25 pages)

- Autoresearch-style loops are applicable beyond language modeling
- Multi-objective framing is more realistic than single-endpoint ranking
- Public-data proof-of-concept; proprietary data is the next step
- Released as open-source framework

### 4.8 `ethics.tex` (~0.25 pages)

- No human subjects or animal experiments
- All data is public
- No dual-use concerns (ranking tool, not generative)
- Codex agent used with full API access; no adversarial use

### 4.9 `reproducibility.tex` (~0.25 pages)

- Code at: github.com/ewijaya/autoresearch-developability
- All data downloaded from public sources (DBAASP, ToxinPred3, HLP)
- Random seed: 42 for all splits and models
- Codex model: gpt-5.4 with xhigh reasoning effort
- Hardware: g5.xlarge (GPU for ESM-2 embeddings), c7i.large (CPU for loop)
- `run_all.sh --with-loop` reproduces the full pipeline

### 4.10 `supplementary.tex`

- **Figure 5:** `fig5_weight_sensitivity.pdf` — Prompt 3b weight perturbations
  (moves to appendix since it's from the pre-Codex manual loop)
- **Table S1:** Full 12-keep trajectory with descriptions and metrics
- **Table S2:** Per-oracle breakdown (pareto_rank, rank_product, threshold_gate)
  for all strategies
- **Table S3:** Qualitative examples — peptides with biggest rank changes
  between weighted_sum and agent_improved, with endpoint scores
  (data source: `results/ablations/qualitative_examples_val.csv`)
- **Table S4:** ToxinPred3 overlap audit results

---

## 5. Figures

| # | File | Section | Caption summary |
|---|---|---|---|
| 1 | `fig1_baseline_comparison.pdf` | 4.1 | Strategy comparison: 8 strategies on TopK, NDCG, feasible fraction with bootstrap error bars |
| 2 | `fig2_loop_trajectory.pdf` | 4.2 | Autoresearch progress: 100 experiments, 12 keeps, H-mean staircase with annotations |
| 3 | `fig3_pareto_front.pdf` | 4.3 | Pareto front: activity vs safety, top-20 highlighted under 3 strategies |
| 4 | `fig4_ablation_heatmap.pdf` | 4.4 | Endpoint ablation: delta top-k enrichment when each endpoint is neutralized |
| 5 | `fig5_weight_sensitivity.pdf` | Supp | Weight sensitivity from manual loop (Prompt 3b perturbations) |
| 6 | `fig6_multi_split_boxplot.pdf` | 4.5 | Cross-split robustness: top-k enrichment distribution across 10 random splits |

All figures exist in `results/figures/` as PDF and PNG. Copy or symlink to `manuscript/figures/`.

---

## 6. Tables

| # | Section | Content | Data source |
|---|---|---|---|
| 1 | 4.1 | All strategies, all metrics, bootstrap 95% CIs | `bootstrap_val_k20.csv` |
| 2 | 4.2 | 12 kept experiments: TopK, NDCG, H-mean, short description | `results/loops/prompt5/results.tsv` |
| 3 | 3.2 | Dataset statistics: sources, sizes, held-out performance | `data/manifests/manifest.json` |
| 4 | 4.4 | Endpoint ablation: delta TopK per strategy per endpoint | `endpoint_ablation_val.csv` |
| S1 | Supp | Full 12-keep trajectory with full descriptions | loop results.tsv |
| S2 | Supp | Per-oracle breakdown for all strategies | evaluate.py output |
| S3 | Supp | Qualitative examples: biggest rank movers | `qualitative_examples_val.csv` |
| S4 | Supp | ToxinPred3 overlap audit | evaluate.py --audit-overlap |

---

## 7. References (key citations)

**Companion paper (cite prominently in intro and methodology):**
```bibtex
@misc{wijaya2026autonomousagentdiscoversmolecular,
      title={What an Autonomous Agent Discovers About Molecular Transformer
             Design: Does It Transfer?},
      author={Edward Wijaya},
      year={2026},
      eprint={2603.28015},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2603.28015},
}
```

**Other key citations:**
```
- Karpathy, A. autoresearch. GitHub, 2025.
- Deb, K. et al. A fast and elitist multiobjective genetic algorithm: NSGA-II. IEEE TEC, 2002.
- Pirtskhalava, M. et al. DBAASP v4. NAR, 2024.
- Gupta, S. et al. ToxinPred3. Briefings in Bioinformatics, 2024.
- Sharma, A. et al. HLP: half-life prediction of peptides. Scientific Reports, 2014.
- Lin, Z. et al. ESM-2: Language models of protein sequences at the scale of evolution. Science, 2023.
- Ke, G. et al. LightGBM. NeurIPS, 2017.
- Lu, C. et al. The AI Scientist. ICML, 2024.
- Huang, Q. et al. ML-Agent-Bench. NeurIPS, 2023.
```

**Framing note:** This paper is the second in a two-paper series. The
companion paper (Wijaya, 2026; arXiv:2603.28015) applied the autoresearch
paradigm to molecular transformer architecture search. This paper applies
it to multi-objective peptide ranking — a different domain, a different
editable surface (ranking policy vs neural architecture), and a different
evaluation structure (multi-objective vs single-metric).

---

## 8. Writing Constraints

- **Page limit:** 4 pages main + unlimited appendix (workshop format)
- **No hype:** do not claim drug discovery breakthroughs from public toy data
- **Honest limitations:** CIs overlap, stability model weak, synthetic benchmark
- **Do not bury limitations:** they go in discussion, not footnotes
- **Do not pretend the public benchmark is the same as proprietary data**
- **The paper should make a biotech reader think:** "If this works on public
  data, plugging in our data would be genuinely valuable."
- **Tone:** Match autoresearch-mol — empirical, systematic, honest about
  what works and what doesn't

---

## 9. Writing Order

Recommended order for an agent writing session:

1. `abstract.tex` — forces clarity on the core claim
2. `methodology.tex` — establish what was done (most mechanical section)
3. `results.tex` — present the evidence
4. `introduction.tex` — motivate the work now that results are clear
5. `discussion.tex` — interpret and acknowledge limitations
6. `related_work.tex` — position the work (can be written in parallel)
7. `conclusion.tex` — wrap up
8. `supplementary.tex` — dump extra tables and figures
9. `ethics.tex` + `reproducibility.tex` — boilerplate
10. `references.bib` — compile all citations

---

## 10. Pre-Writing Checklist

Before starting `main.tex`, verify these files exist:

- [ ] `results/figures/fig1_baseline_comparison.pdf`
- [ ] `results/figures/fig2_loop_trajectory.pdf`
- [ ] `results/figures/fig3_pareto_front.pdf`
- [ ] `results/figures/fig4_ablation_heatmap.pdf`
- [ ] `results/figures/fig5_weight_sensitivity.pdf`
- [ ] `results/figures/fig6_multi_split_boxplot.pdf`
- [ ] `results/ablations/bootstrap_val_k20.csv`
- [ ] `results/ablations/endpoint_ablation_val.csv`
- [ ] `results/ablations/multi_split_summary.csv`
- [ ] `results/ablations/qualitative_examples_val.csv`
- [ ] `results/loops/prompt5/results.tsv` (100 experiments)
- [ ] `data/manifests/manifest.json`

---

## 11. Post-Writing Checklist

- [ ] All numbers in the paper match the CSV/TSV sources
- [ ] Bootstrap CIs are reported for every comparison claim
- [ ] Limitations section covers all known weaknesses
- [ ] No claim exceeds what the evidence supports
- [ ] Figures are vector PDF (not rasterized PNG) in the final build
- [ ] `pdflatex main && bibtex main && pdflatex main && pdflatex main` compiles cleanly
- [ ] Page count is within venue limit
- [ ] Anonymous version ready (comment out author block)
