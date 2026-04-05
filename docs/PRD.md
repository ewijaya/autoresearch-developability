# Product Requirements Document: autoresearch-developability

**Project:** Multi-objective autoresearch for peptide developability
**Repository:** https://github.com/ewijaya/autoresearch-developability
**Reference repos:**
- Karpathy autoresearch: https://github.com/karpathy/autoresearch
- Existing molecular fork: https://github.com/ewijaya/autoresearch-mol
**Status:** Kick-start PRD for new agent session
**Intent:** Public-data proof of concept that demonstrates obvious internal value to StemRIM

---

## 1. Executive Summary

`autoresearch-developability` is a public-data proof-of-concept repo that adapts the core loop from **Karpathy’s `autoresearch`** to a peptide discovery setting where the objective is **not a single metric**, but a **multi-objective developability decision**.

The core idea is simple:

1. Start from the operating pattern in `https://github.com/karpathy/autoresearch`
2. Reuse the practical lessons already learned in `https://github.com/ewijaya/autoresearch-mol`
3. Replace single-objective next-token optimization with a **multi-objective peptide evaluator**
4. Show, on entirely public datasets, that an autonomous loop can improve peptide candidate ranking under real discovery constraints:
   - activity
   - toxicity
   - stability
   - developability / manufacturability proxies

This repo should be designed so that, once validated publicly, the same framework can be swapped onto StemRIM internal peptide data with minimal architectural change.

**The public paper is the wedge. The internal platform is the real goal.**

---

## 2. Why This Repo Exists

### 2.1 Problem

Most AI-for-peptides work optimizes one endpoint at a time:
- activity only
- toxicity only
- stability only

That is scientifically incomplete and operationally naive.

In real peptide discovery, a candidate is only valuable if it survives a **portfolio of constraints**. A peptide with high activity but poor toxicity or bad stability is not a lead. It is an expensive distraction.

### 2.2 Opportunity

Karpathy’s `autoresearch` showed that an agent can iteratively improve a system through a tight loop around a fixed evaluation harness and one editable surface.

Your `autoresearch-mol` repo already proved you understand how to port that idea into a scientific domain:
- domain-adapted `prepare.py`
- fixed metric discipline
- track structure
- calibration logic
- baseline comparisons
- PRD-driven execution

`autoresearch-developability` should be the next step:
**not architecture search for token prediction, but autonomous multi-objective optimization for peptide candidate selection.**

### 2.3 Target Outcome

A repo and paper that make StemRIM immediately think:

> “If this works on public peptide datasets, plugging in our TRIM data would be genuinely valuable.”

---

## 3. The Reference Pattern to Follow

The agent must explicitly study and reuse the operating logic of:

### 3.1 Karpathy autoresearch
**Source:** https://github.com/karpathy/autoresearch

The agent should understand these principles from the source repo:
- `prepare.py` is fixed and defines the evaluation harness
- `train.py` is the only editable file in the core loop
- `program.md` is the human-authored operating instruction layer
- fixed-time experiments allow comparable iterative progress
- keep/discard discipline matters more than fancy orchestration

### 3.2 autoresearch-mol
**Source:** https://github.com/ewijaya/autoresearch-mol

The agent should extract these lessons from your repo:
- how to translate a general autoresearch repo into a domain-specific scientific repo
- how to write a serious PRD before building
- how to set up tracks, baselines, calibration studies, and analysis
- how to make the paper and the repo reinforce each other
- how to keep scope disciplined

This repo is **not** a blind copy of either one.
It is a new fork in spirit, borrowing:
- Karpathy’s loop discipline
- your `autoresearch-mol` seriousness and execution style

---

## 4. Primary Research Question

> Can an autoresearch-style loop improve peptide candidate ranking under multiple developability constraints using entirely public data?

Subquestions:
1. Does a multi-objective evaluator outperform single-endpoint ranking?
2. Which objective trade-offs dominate early peptide triage?
3. Can an agent improve candidate ranking policy iteratively under a fixed public benchmark?
4. Does the resulting system look credible enough that a biotech company would want to port it to proprietary data?

---

## 5. Success Criteria

### 5.1 Hard Success Criteria

1. A fully reproducible public-data pipeline exists
2. Multi-objective scoring works end-to-end on at least one peptide benchmark bundle
3. The repo produces ranked candidate lists, not just model scores
4. At least one agent-edit loop demonstrably improves ranking quality over baseline
5. A paper-grade figure set can be generated from the results
6. The repository is clean enough that a new agent session can continue autonomously from the PRD

### 5.2 Soft Success Criteria

1. Clear Pareto-front visualization of trade-offs
2. Strong ablation against single-objective baselines
3. Candidate proposal module added after evaluator is stable
4. Active learning simulation added as a second-stage paper direction
5. The system looks obviously portable to StemRIM internal data

---

## 6. What This Repo Is and Is Not

### In Scope
- Public peptide datasets only
- Multi-objective ranking / developability evaluation
- Autoresearch-style iterative loop
- Benchmarking against simpler baselines
- Reproducible repo and paper-quality outputs
- Candidate selection and triage

### Out of Scope for v1
- Proprietary StemRIM data
- Wet lab integration
- Full multi-agent swarms
- Patent/FTO engine
- Complex docking or structural pipelines as a core dependency
- Full molecule foundation model pretraining

v1 should be **small, sharp, and publishable**.

---

## 7. Core Product Concept

`autoresearch-developability` should revolve around a **fixed multi-objective harness** and one **editable ranking policy**.

### 7.1 Fixed Harness
This is the equivalent of Karpathy’s `prepare.py` discipline.

The harness should:
- load public peptide datasets
- harmonize them into a shared representation
- define train/val/test splits with leakage controls
- compute all endpoint models or endpoint scores
- compute aggregate ranking metrics
- expose a single summary score for keep/discard decisions

### 7.2 Editable Surface
The editable surface should be tightly constrained.

Recommended starting editable file:
- `rank.py` or `policy.py`

This file should be the agent’s playground for:
- scalarization strategy
- Pareto ranking strategy
- objective weights
- uncertainty-aware ranking
- diversity bonus
- hard filters vs soft penalties

Do **not** let the early agent freely rewrite the whole repo.
That was the right lesson from Karpathy and from `autoresearch-mol`.

---

## 8. Proposed Repo Structure

```text
autoresearch-developability/
├── README.md
├── program.md
├── pyproject.toml
├── src/
│   ├── prepare.py              # fixed harness, data prep, eval definitions
│   ├── rank.py                 # primary editable file for agent
│   ├── endpoint_activity.py    # fixed or semi-fixed
│   ├── endpoint_toxicity.py    # fixed or semi-fixed
│   ├── endpoint_stability.py   # fixed or semi-fixed
│   ├── endpoint_dev.py         # manufacturability/developability proxies
│   ├── evaluate.py             # ranking metrics, Pareto utilities
│   ├── run_agent_loop.py       # orchestration helper
│   └── analysis.py             # paper figures and summaries
├── data/
│   ├── raw/
│   ├── processed/
│   └── manifests/
├── results/
│   ├── baseline/
│   ├── loops/
│   ├── ablations/
│   └── figures/
├── docs/
│   ├── PRD.md
│   ├── paper_outline.md
│   └── dataset_notes.md
└── tests/
```

---

## 9. Public Datasets to Use

The first version should select from the following public sources, prioritizing usability over maximal breadth.

### 9.1 Toxicity
Use one or more of:
- ToxinPred datasets
- DBAASP toxicity / hemolysis subsets
- CellPPD toxicity-related subsets

### 9.2 Stability
Use one or more of:
- peptide half-life datasets (HLP-style)
- protease cleavage / substrate datasets
- public serum stability datasets curated from literature

### 9.3 Activity
Activity is the trickiest because “activity” is indication-dependent.
For v1, do not overcomplicate this.
Pick a coherent public peptide activity target family, for example:
- antimicrobial activity
- cell-penetrating peptide activity
- anti-inflammatory peptide labels if quality permits

The key is not biological perfection. The key is a stable benchmark for demonstrating the **multi-objective framework**.

### 9.4 Developability / Manufacturability Proxies
If direct datasets are sparse, encode public rule-based features:
- sequence length penalties
- aggregation-prone motifs
- difficult synthesis motifs
- unusual residue composition penalties
- extreme hydrophobicity or charge pattern penalties

This is acceptable for v1 as long as the rules are explicit and documented.

---

## 10. Ranking Formulation

The heart of the repo is the ranking problem.

For each peptide candidate, generate endpoint estimates such as:
- activity score
- toxicity risk
- stability score
- developability penalty

Then build a ranking layer that supports multiple strategies:

1. **Weighted scalarization**
2. **Pareto frontier ranking**
3. **Lexicographic filtering**
4. **Uncertainty-aware ranking**
5. **Diversity-aware reranking**

The first public paper should compare these policies rather than pretending there is one obvious correct answer.

---

## 11. Baselines

The repo needs strong baselines or the whole thing becomes hand-wavy.

### Required baselines
1. **Single-objective activity ranking**
2. **Single-objective toxicity exclusion only**
3. **Simple weighted sum baseline**
4. **Random ranking among acceptable candidates**
5. **Handcrafted rule-only ranking**
6. **Agent-improved ranking policy**

Optional:
7. Hyperparameter-only policy tuning baseline
8. Random search over policy weights

The point is to prove that the autoresearch loop adds value over trivial decision policies.

---

## 12. Metrics

This repo must optimize **decision quality**, not vanity benchmark scores.

Recommended metrics:

### Candidate ranking metrics
- top-k enrichment
- NDCG
- pairwise ranking accuracy
- Kendall tau / Spearman correlation when reference ranks are available

### Multi-objective quality metrics
- Pareto front coverage
- dominated hypervolume
- composite utility score

### Practical metrics
- fraction of top-k candidates that satisfy all hard constraints
- diversity among top-k candidates
- robustness of ranking across bootstrap samples

### Optional uncertainty metrics
- calibration error
- prediction interval width

---

## 13. The Karpathy Loop Adapted Here

This repo must explicitly say in the PRD and `program.md`:

> This project is inspired by and structurally derived from Karpathy’s `autoresearch` repo: https://github.com/karpathy/autoresearch

But adapted as follows:

### Original autoresearch
- fixed data/eval harness
- editable `train.py`
- optimize one scalar metric (`val_bpb`)

### autoresearch-developability
- fixed public peptide evaluation harness
- editable `rank.py` / `policy.py`
- optimize ranking quality under multiple competing constraints

This is the conceptual translation.

---

## 14. program.md Requirements

The repo must include a `program.md` that tells a future coding agent exactly how to work.

It should explicitly instruct the agent to:

1. Read `https://github.com/karpathy/autoresearch` first for the original pattern
2. Read the local PRD before making changes
3. Treat `prepare.py` as fixed unless the human explicitly allows otherwise
4. Modify only the designated editable file in the main loop
5. Make one coherent ranking-policy change at a time
6. Run the evaluation suite
7. Log the result in `results.tsv`
8. Keep only if the summary ranking objective improves
9. Revert if it regresses or breaks interpretability
10. Prefer simple policies that generalize over baroque logic

---

## 15. Required Logging

The repo must maintain a machine-readable experiment ledger.

Recommended schema:

```tsv
commit\tsummary_metric\ttopk_enrichment\thypervolume\tstatus\tdescription
```

Status values:
- keep
- discard
- crash
- ambiguous

Descriptions should say exactly what changed in the ranking policy.

---

## 16. Paper Strategy

### Best first paper framing
**Working title:**
"Autoresearch for peptide developability: multi-objective candidate ranking under public-data constraints"

### Better subtitle logic
- public proof-of-concept
- multi-objective peptide selection
- autoresearch-style iterative improvement

### Strong paper claim
Do **not** claim AGI drug discovery nonsense.
Claim something narrower and stronger:

> An autoresearch-style loop can iteratively improve peptide candidate triage under realistic multi-objective constraints using entirely public data.

That is publishable and believable.

---

## 17. 90-Day Build Plan

### Phase 1: scaffold the repo
- create the repo and initial file layout
- port the discipline of `autoresearch` and `autoresearch-mol`
- write `prepare.py`, `rank.py`, `program.md`, `README.md`
- define the public dataset bundle
- define baseline ranking policies

### Phase 2: get one benchmark working
- choose one coherent activity dataset family
- join with toxicity and stability layers
- implement the fixed evaluator
- verify splits, leakage control, and metrics

### Phase 3: run the first loop
- baseline policy
- 20 to 50 iterative policy experiments
- keep/discard logging
- generate first figures

### Phase 4: strengthen for paper
- ablations
- uncertainty / robustness
- diversity-aware reranking
- paper outline and figures

### Phase 5: prepare next-stage expansion
- candidate proposal module
- active learning simulation
- note how StemRIM internal data would plug in

---

## 18. What the New Agent Should Do First

A new agent session starting on this repo should do the following in order:

1. Read this PRD fully
2. Clone or inspect `https://github.com/karpathy/autoresearch`
3. Clone or inspect `https://github.com/ewijaya/autoresearch-mol`
4. Draft the repo skeleton
5. Draft `program.md`
6. Draft `README.md`
7. Implement `prepare.py` with fixed public-data harness
8. Implement a simple initial `rank.py`
9. Create baseline policies
10. Run one full dry-run end-to-end

---

## 19. Explicit Instructions to the Agent

When continuing this repo, the agent should follow these instructions exactly:

- Use `https://github.com/karpathy/autoresearch` as the explicit conceptual source for the loop design
- Use `https://github.com/ewijaya/autoresearch-mol` as the explicit source for domain adaptation style, PRD discipline, and execution tone
- Keep the repo small and legible
- Optimize for publishable science and StemRIM relevance, not maximal complexity
- Build the fixed harness first
- Keep one main editable file in the core loop
- Prefer ranking-policy improvement over broad uncontrolled code mutation
- Every major addition must help answer the core question: does autoresearch improve peptide developability triage on public data?

---

## 20. Definition of Done for v1

v1 is done when all of the following are true:

1. Repo exists and is private on GitHub
2. PRD, README, and `program.md` exist
3. Public datasets are wired into a fixed evaluation harness
4. At least one baseline ranking policy runs end-to-end
5. At least one autoresearch-style improvement loop is demonstrated
6. Figures exist showing improvement over baseline
7. A new coding agent can start from the repo with minimal human intervention

---

## 21. Final Strategic Note

The mission of this repo is not merely to build a nice GitHub project.

The mission is to create a public, credible, publishable demonstration that:

- multi-objective peptide triage can be improved autonomously
- the Karpathy loop is scientifically useful outside language modeling
- StemRIM would gain real leverage by porting the same framework onto internal peptide data

That is the bar.
