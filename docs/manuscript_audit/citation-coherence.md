# Citation Coherence Audit

**Auditor:** citation-coherence (team manuscript-audit)
**Scope:** every `\cite{}`, `\citep{}`, `\citet{}` in `manuscript/sections/*.tex`
**Date:** 2026-04-20
**Sources verified:** references.bib + live WebFetch/WebSearch for primary sources
**Read-only audit.** No manuscript files were modified.

---

## Summary counts per verdict

| Verdict | Count |
|---|---|
| Supported (cite appropriate for claim) | 22 |
| Minor (loose fit, tangential, or imperfect framing) | 5 |
| Major (miscited — right paper, wrong finding / misrepresents source) | 1 |
| Missing citation where one is load-bearing | 3 |
| Blocker (fabricated or non-existent cite) | 0 |

Total `\cite*` invocations audited: **28** (some keys appear more than once).

---

## Summary table

| Section | Line | Claim (short) | Citekey | Verdict | Rationale |
|---|---|---|---|---|---|
| introduction | 4 | "must survive a portfolio of constraints... activity, toxicity, stability, manufacturability" | `yan2022review` | minor | Yan 2022 is an AMP-specific ML review; it supports activity/toxicity framing but does not explicitly enumerate the 4-endpoint triage portfolio claimed here. |
| introduction | 6 | "Most computational approaches to peptide discovery optimize a single endpoint at a time" | `veltri2018ampscanner` | minor | Veltri is ONE single-endpoint AMP classifier — it exemplifies the pattern but cannot by itself support a claim about "most" approaches. |
| introduction | 9 | NSGA-II finds Pareto-optimal solutions | `deb2002nsga2` | supported | Canonical NSGA-II cite. |
| introduction | 13 | Autoresearch: tight loop of read / edit / eval / keep-or-revert | `karpathy2026autoresearch` | supported | Matches `karpathy/autoresearch` README and `program.md` loop description (verified on GitHub). |
| introduction | 14 | Companion paper: 3,106 experiments across SMILES/protein/NLP; domain-dependent value | `wijaya2026autonomousagentdiscoversmolecular` | supported | arXiv 2603.28015 exists (verified); abstract matches (SMILES ≈ HP-tuning beats NAS, NL 81 % gain, proteins intermediate). |
| introduction | 17 | DBAASP = activity source | `pirtskhalava2021dbaasp` | supported | Correct DBAASP v3/v4 paper. |
| introduction | 17 | ToxinPred3 = toxicity source | `rathore2024toxinpred3` | supported | Correct. |
| introduction | 17 | HLP = stability source | `sharma2014hlp` | supported | HLP is the peptide half-life dataset from Sharma 2014. |
| introduction | 21 | "LambdaMART ensembles" | `ke2017lightgbm` | minor | LightGBM is the implementation; LambdaMART's origin is Burges 2010. Intro cites only LightGBM; results.tex:90 does co-cite both. Inconsistent attribution. |
| methodology | 40 | DBAASP v4 as activity source, *E. coli* ATCC 25922 | `pirtskhalava2021dbaasp` | supported | Correct. |
| methodology | 45 | ToxinPred3 binary toxicity labels | `rathore2024toxinpred3` | supported | Correct. |
| methodology | 45 | ESM-2 embeddings, 8M-parameter model | `lin2023esm2` | supported | Correct (Lin 2023 Science). |
| methodology | 50 | HLP peptide half-life training data | `sharma2014hlp` | supported | Correct. |
| methodology | 85 | NDCG definition | `jarvelin2002ndcg` | supported | Canonical NDCG cite. |
| methodology | 86 | Hypervolume indicator | `zitzler2003hypervolume` | supported | Canonical hypervolume cite. |
| methodology | 95 | Autoresearch framework adapted | `karpathy2026autoresearch` | supported | Same as intro L13. |
| methodology | 96 | Companion paper applied autoresearch to transformer NAS | `wijaya2026autonomousagentdiscoversmolecular` | supported | Verified. |
| methodology | 125 | "best-of-1,000 Dirichlet-sampled weight vectors" | `bergstra2012random` | minor | Bergstra–Bengio justify random search for hyperparameter optimization, not Dirichlet-sampled scalarization weights for MOO specifically. Fit is philosophical, not exact. |
| methodology | 126 | NSGA-II with non-dominated sorting + crowding distance | `deb2002nsga2` | supported | Correct. |
| related_work | 5 | Evolutionary-algorithm MOO for molecules | `deb2002nsga2,zhang2007moead` | supported | NSGA-II and MOEA/D are the canonical evolutionary MOO cites. |
| related_work | 5 | Generative models for multi-objective molecular design | `jin2020multiobjective,xie2021mars` | supported | Jin 2020 ICML and MARS ICLR 2021 — correct. |
| related_work | 5 | GuacaMol benchmark suite | `brown2019guacamol` | supported | Correct. |
| related_work | 8 | "Scalarization, Pareto, lexicographic methods... in broader optimization literature" | `emmerich2018tutorial` | supported | Emmerich tutorial covers these exact paradigms. |
| related_work | 11 | AMP activity prediction exemplar | `veltri2018ampscanner` | supported | Veltri is a standard AMP-activity-prediction reference. |
| related_work | 11 | Toxicity prediction tool | `rathore2024toxinpred3` | supported | Correct. |
| related_work | 11 | Stability estimation tool | `sharma2014hlp` | supported | Correct. |
| related_work | 12 | ESM-2 = protein language model | `lin2023esm2` | supported | Correct. |
| related_work | 13 | "few address the joint ranking problem across multiple developability criteria" | `mooney2012peptidemoo` | **major** | **Miscite.** PeptideRanker (Mooney 2012) predicts a single generic-bioactivity probability across peptide classes; it does NOT perform joint multi-endpoint (activity + toxicity + stability + developability) ranking. The manuscript positions it as an example of joint developability ranking — this overreaches what the source shows. |
| related_work | 14 | Learning-to-rank foundations | `liu2009learningtorank,burges2010ranknet` | supported | Correct LTR foundational references. |
| related_work | 17 | Autoresearch iteratively improves an LM training script | `karpathy2026autoresearch` | supported | Correct. |
| related_work | 18 | EvoPrompting for code-level NAS | `chen2023evoprompting` | supported | Correct (NeurIPS 2023). |
| related_work | 18 | FunSearch for mathematical discovery | `romeraparedes2024funsearch` | supported | Correct (Nature 2024; cap set, online bin-packing). The manuscript's summary "mathematical discovery" is tight but fine — FunSearch is explicitly framed as program-search for math. |
| related_work | 18 | AI Scientist for open-ended scientific investigation | `lu2024aiscientist` | supported | Correct. |
| related_work | 19 | MLAgentBench benchmark for language-agent ML experimentation | `huang2024mlagentbench` | supported | Correct (ICML 2024, PMLR). |
| related_work | 20 | Companion paper, 3,106 experiments, domain-dependent findings | `wijaya2026autonomousagentdiscoversmolecular` | supported | Verified. |
| results | 84 | "reciprocal rank fusion" | `cormack2009rrf` | supported | Canonical RRF cite. |
| results | 90 | LambdaMART reranker | `ke2017lightgbm,burges2010ranknet` | supported | Correct joint citation (implementation + method). |
| discussion | 7 | Reciprocal rank fusion in mid-loop experiments | `cormack2009rrf` | supported | Same as above. |
| discussion | 14 | "agent outperformed random NAS on SMILES architecture search" (parallels companion paper) | `wijaya2026autonomousagentdiscoversmolecular` | minor | The companion paper's headline finding is the *opposite*: on SMILES, hyperparameter tuning beat full architecture search (p = 0.001). The "agent vs. random NAS" comparison is secondary; current wording could mislead readers who do not open the companion paper. Verify framing. |
| discussion | 17 | NSGA-II = highest hypervolume, lowest top-k enrichment among MOO strategies | `deb2002nsga2` | supported | Deb 2002 is the NSGA-II source; the claim is empirical (about this paper's results) not about the source. OK. |

---

## Detailed findings — sorted by severity

### BLOCKER

None.

### MAJOR

#### M1. `mooney2012peptidemoo` misrepresented (related_work.tex:13)

**Claim context (lines 12–13):**

> Protein language models such as ESM-2 [lin2023esm2] provide general-purpose sequence embeddings that improve downstream predictors. However, most tools predict a single endpoint; few address the joint ranking problem across multiple developability criteria [mooney2012peptidemoo].

**Why this is a miscite.** Mooney et al. 2012 introduces PeptideRanker, a *single-output* binary classifier that predicts whether a peptide is "bioactive" in a generalized sense (trained across AMP, hormone, and other bioactive classes). It does not integrate activity with toxicity, stability, or manufacturability, and it does not perform multi-objective ranking. In context the citation is used to exemplify "few [works that] address the joint ranking problem" — PeptideRanker is not such a work; it is a generic bioactivity predictor.

**Recommendation.** Either (a) remove the citation from this sentence and leave the gap statement uncited (the absence itself is the claim), or (b) reframe the cite as "generalized single-score peptide bioactivity prediction [mooney2012peptidemoo]" — but then it no longer supports the sentence's "joint ranking problem" framing. Option (a) is cleaner.

Severity rationale: this is the only citation anchoring the gap-in-the-literature claim for related work's "peptide property prediction" paragraph, and it load-bears on the paper's novelty argument.

### MINOR

#### m1. `yan2022review` supports only part of the portfolio claim (introduction.tex:4)

**Claim:** "Peptide drug candidates must survive a portfolio of constraints before entering preclinical development: high activity against the biological target, low toxicity, adequate metabolic stability, and acceptable manufacturability."

Yan 2022 is "Recent progress in the discovery and design of antimicrobial peptides using traditional ML and deep learning" (Antibiotics) — it centers on activity prediction and to a lesser degree toxicity; it is not a review of the full preclinical developability portfolio (activity + tox + stability + manufacturability). Consider an additional/alternative reference that explicitly covers developability triage (e.g., Lau & Dunn 2018 "Therapeutic peptides: Historical perspectives, current development trends, and future directions", Bioorg Med Chem) or similar peptide-therapeutics review.

**How to apply.** Low risk — the claim is uncontroversial — but the single citation does not fully substantiate the multi-criterion framing.

#### m2. `veltri2018ampscanner` as evidence for "most" single-endpoint tools (introduction.tex:6)

**Claim:** "Most computational approaches to peptide discovery optimize a single endpoint at a time [veltri2018ampscanner]."

One paper cannot establish a "most" claim; it only exemplifies. The adjacent related_work paragraph handles this better by citing multiple single-endpoint tools. Consider either softening the claim ("typical approaches such as [veltri2018ampscanner, rathore2024toxinpred3, sharma2014hlp]") or citing a review (e.g., `yan2022review`) that actually surveys the field.

#### m3. `ke2017lightgbm` as LambdaMART attribution (introduction.tex:21)

**Claim:** "learned MLP and LambdaMART [ke2017lightgbm] ensembles."

LightGBM is the implementation; LambdaMART is Burges 2010. results.tex:90 cites both (`ke2017lightgbm,burges2010ranknet`). The intro should match. Not load-bearing, but inconsistent attribution looks careless.

#### m4. `bergstra2012random` for Dirichlet-sampled MOO weights (methodology.tex:125)

**Claim:** "best-of-1,000 Dirichlet-sampled weight vectors evaluated with the weighted-sum scalarization [bergstra2012random]. This controls for blind exploration of the same policy class the agent starts from."

Bergstra & Bengio 2012 argues empirically and theoretically that random search beats grid search for *hyperparameter optimization of ML models*. It does not address MOO scalarization, Dirichlet weight sampling, or ranking-policy search. The philosophical connection (random as a strong baseline) is real, but the cite does not specifically justify the Dirichlet-simplex sampling choice. Consider adding a weight-sampling reference (e.g., Das & Dennis 1997 on normal-boundary intersection, or Deb 2001 on weight generation schemes for MOO), or clarifying that the cite justifies "random search as a baseline paradigm" only.

#### m5. `wijaya2026autonomousagentdiscoversmolecular` framing in discussion (discussion.tex:14)

**Claim:** "This parallels findings from our companion paper [wijaya2026autonomousagentdiscoversmolecular], where the full agent outperformed random NAS on SMILES architecture search."

Verification against the companion paper's abstract: for SMILES, the companion paper's headline finding is that **simple hyperparameter tuning outperformed full architecture search (p = 0.001)**. The "agent vs. random NAS on SMILES" comparison is not its primary result and selecting only that comparison to assert a parallel is potentially misleading. A reader who opens the companion paper will find its main message pointing in a *different* direction (HP-tuning > NAS on SMILES). The present paper's parallel-claim ("directed agent search > random search") is true of that companion paper at a fine grain, but the framing risks citation misplacement — right paper, narrow finding used out of context.

**Recommendation.** Either rephrase ("where a sub-analysis showed the agent outperformed random NAS on SMILES") or choose a different anchor (e.g., the companion paper's NL-domain result, where the agent-driven search delivered 81 % improvement).

### MISSING CITATIONS (load-bearing claims without support)

#### MC1. Intro L7 — mechanistic toxicity/activity correlation claim

> "Because endpoints often conflict (highly active peptides tend toward membrane-disrupting mechanisms that correlate with toxicity), single-endpoint optimization produces candidates that fail downstream."

This is a load-bearing biological claim that motivates the entire multi-objective framing. It is uncited. Standard references for AMP activity–hemolysis trade-off include:
- Chen et al. 2005 "Rational design of α-helical antimicrobial peptides with enhanced activities and specificity/therapeutic index" (J. Biol. Chem.)
- Matsuzaki 2009 "Control of cell selectivity of antimicrobial peptides" (BBA Biomembranes)
- Yin et al. 2012 "Roles of hydrophobicity and charge distribution of cationic antimicrobial peptides in peptide–membrane interactions and antibacterial activity" (J. Biol. Chem.)

Severity: borderline major — the claim frames the whole paper and should be grounded.

#### MC2. Intro L10–11 + Discussion L17 — "classical MOO methods optimize for Pareto spread rather than top-k concentration"

> "classical MOO methods optimize for Pareto spread (diversity across the frontier) rather than top-k concentration (the best 20 candidates for wet-lab validation)."

This characterization is a core argument against NSGA-II. A supporting reference from MOO literature discussing the spread-vs-concentration distinction would strengthen the claim. `emmerich2018tutorial` could be reused here. Currently no support.

#### MC3. Methodology L54 — developability rule thresholds

> "seven sequence-level rules: length outside 8--40 residues, consecutive hydrophobic stretches, consecutive prolines, high net charge, high mean hydrophobicity, and excess cysteines."

These are load-bearing design choices that directly affect every benchmark result. No citation to AMP developability rules (e.g., Lipinski-like peptide rules, Fjell et al. 2012 "Designing antimicrobial peptides: form follows function" Nat Rev Drug Discov, or the MAPS developability framework). If these are authors' custom thresholds, that should be stated explicitly. If they derive from literature, cite.

Severity: minor in text but the absence is surprising given the rules directly weight into the benchmark — supplementary or methodology should justify each threshold with either a literature cite or an explicit "we chose" declaration.

### NITS

None worth separate callout — stylistic consistency issues (e.g., LambdaMART attribution) are folded into the minors above.

---

## Cross-section citation consistency

- `karpathy2026autoresearch` is cited identically in intro L13, methods L95, related L17. Consistent.
- `wijaya2026autonomousagentdiscoversmolecular` appears in intro L14, methods L96, related L20, discussion L14. All describe "3,106 experiments" and "SMILES/protein/NLP domains" — consistent. Framing in discussion L14 is the only concern (see m5).
- `deb2002nsga2` used consistently across intro, methods, related work, discussion.
- NSGA-II's "hypervolume as design goal" is asserted in discussion L17 without citation to the hypervolume-spread literature; `zitzler2003hypervolume` already in bib and could be added for rigor.

---

## Verification log (external lookups performed)

| Citekey | Source consulted | Result |
|---|---|---|
| `wijaya2026autonomousagentdiscoversmolecular` | WebFetch arxiv.org/abs/2603.28015 | Exists, title and content match bib |
| `karpathy2026autoresearch` | WebSearch + github.com/karpathy/autoresearch | Exists, loop description matches intro/methods |
| `romeraparedes2024funsearch` | WebSearch Nature 625:468 | Verified |
| `chen2023evoprompting` | WebSearch NeurIPS 2023 | Verified |
| `xie2021mars` | WebSearch ICLR 2021 | Verified |
| `lin2023esm2` | WebSearch Science 2023 | Verified |
| `veltri2018ampscanner` | WebSearch Bioinformatics 2018 | Verified |
| `mooney2012peptidemoo` | WebSearch PLOS One 2012 | Verified (and identified miscite) |
| `bergstra2012random` | WebSearch JMLR 2012 | Verified; scope mismatch documented |

Remaining bib keys (`pirtskhalava2021dbaasp`, `rathore2024toxinpred3`, `sharma2014hlp`, `ke2017lightgbm`, `burges2010ranknet`, `lu2024aiscientist`, `huang2024mlagentbench`, `jin2020multiobjective`, `brown2019guacamol`, `emmerich2018tutorial`, `cormack2009rrf`, `jarvelin2002ndcg`, `zitzler2003hypervolume`, `liu2009learningtorank`, `zhang2007moead`, `yan2022review`) were checked only against their bib entries, which are internally well-formed and match standard reference patterns. Task #1 covers exhaustive bib verification.

---

## Recommended highest-priority actions

1. **Fix `mooney2012peptidemoo` miscite** (related_work.tex:13) — M1 above. Either drop or reframe.
2. **Ground the "activity ↔ toxicity correlate via membrane mechanism" claim** (introduction.tex:7) — MC1. This is the paper's motivational hinge.
3. **Reconsider `veltri2018ampscanner` as sole support for "most approaches are single-endpoint"** (introduction.tex:6) — m2.
4. **Unify LambdaMART attribution** — m3. Add `burges2010ranknet` to intro L21.
5. **Verify the discussion L14 framing of the companion paper's SMILES result** — m5.
