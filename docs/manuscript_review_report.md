# Manuscript Review Report

**Date:** 2026-04-06
**Manuscript:** Agent-Guided Ranking Policy Improvement for Peptide Drug Candidate Prioritization
**Reviewers:** bib-checker, number-auditor, coherence-reviewer, scope-checker (4 parallel subagents)

---

## Executive Summary

| Dimension | Status | Critical | Major | Minor |
|---|---|---|---|---|
| Bibliography accuracy | **FAIL** | 4 | 3 | 3 |
| Numerical accuracy | **PASS** | 0 | 0 | 4 |
| Cross-reference integrity | **PASS** | 0 | 0 | 1 |
| Number consistency across sections | **FAIL** | 0 | 1 | 0 |
| Claim-evidence alignment | **FAIL** | 1 | 0 | 0 |
| Scope & overclaiming | **PASS** | 0 | 1 | 5 |
| Limitation coverage | **PASS** | 0 | 0 | 0 |
| **Total** | | **5** | **5** | **13** |

---

## Issue Table (sorted by severity)

### Critical

| # | Category | File:Line | Issue | Suggested Fix | Found by |
|---|----------|-----------|-------|---------------|----------|
| 1 | Bib | `references.bib` (lee2023peptidevae) | **Fabricated reference.** arXiv:2302.12880 resolves to a graph theory paper by Foisy et al., not a peptide VAE paper. The paper "Multi-objective antimicrobial peptide design via variational autoencoders" by Lee & Pellegrini could not be found in any search. | Remove this entry and the `\cite{lee2023peptidevae}` in `introduction.tex:6`. Replace with a real multi-objective peptide design citation if one exists, or remove the claim. | bib-checker |
| 2 | Bib | `references.bib` (gupta2024toxinpred3) | **Wrong authors, journal, volume, pages.** Actual ToxinPred 3.0 is by Rathore, Choudhury, Arora, Tijare & Raghava in *Computers in Biology and Medicine* 179:108926, not by Gupta, Sharma, Jain & Raghava in *Briefings in Bioinformatics* 25(1):bbad493. | Replace entire entry with correct metadata. | bib-checker |
| 3 | Bib | `references.bib` (sharma2014hlp) | **Wrong title, journal, volume, pages, first name.** Actual paper is "Designing of peptides with desired half-life in intestine-like environment" by Sharma, **Arun** et al. in *BMC Bioinformatics* 15:282, not "Prediction of peptide half-life..." in *Scientific Reports* 4:4981. | Replace entire entry with correct metadata. | bib-checker |
| 4 | Bib | `references.bib` (huang2024mlagentbench) | **Wrong venue.** Published at ICML 2024 (PMLR v235, pp. 20271-20309), not NeurIPS vol 36. | Change booktitle to "International Conference on Machine Learning", volume to 235, add pages. | bib-checker |
| 5 | Claim | `abstract.tex:5`, `introduction.tex:22`, `results.tex:44,172`, `conclusion.tex:5` | **"Non-overlapping CIs" claim for agent vs NSGA-II is incorrect.** Agent CI [0.533, 0.767] and NSGA-II CI [0.267, 0.617] DO overlap in the range [0.533, 0.617] since the agent lower bound (0.533) < NSGA-II upper bound (0.617). Appears 5 times. | Replace "non-overlapping CIs" with "substantially separated CIs" or "a gap of 0.206 in point estimates." Alternatively, report a formal bootstrap test of the difference. | coherence-reviewer |

### Major

| # | Category | File:Line | Issue | Suggested Fix | Found by |
|---|----------|-----------|-------|---------------|----------|
| 6 | Bib | `references.bib` (yan2022review) | **Wrong authors, volume, issue, pages.** Actual: Yan, Cai, Zhang, Wang, Wong & Siu in Antibiotics 11(10):1451, not Yan, Bhadra, Li et al. in Antibiotics 12(1):46. | Replace with correct metadata. | bib-checker |
| 7 | Bib | `references.bib` (veltri2018ampscanner) | **Wrong third author.** Should be Amarda **Shehu**, not Amarda **Bhatt**. | Fix author field. | bib-checker |
| 8 | Bib | `references.bib` (xie2021mars) | **Venue upgrade missing.** Listed as arXiv preprint but published at ICLR 2021. | Update to ICLR 2021 proceedings. | bib-checker |
| 9 | Consistency | `abstract.tex:4`, `methodology.tex:112`, `discussion.tex:5` | **"12 kept improvements" is misleading.** results.tex:66 correctly says "12 are kept (11 improvements plus the initial baseline)". Other sections call them "12 improvements", overcounting the baseline. | Change to "12 kept policies (11 improvements over the baseline)" or "11 improvements" throughout. | coherence-reviewer |
| 10 | Scope | `results.tex:174` | **"reliably outperforms all baselines" overclaims.** CIs overlap with weighted sum on single splits. The companion paper never makes unqualified blanket superiority claims. | Rewrite to: "the agent-improved policy outperforms all baselines on point estimates, with non-overlapping CIs against NSGA-II but overlapping CIs against weighted sum on individual splits." | scope-checker |

### Minor

| # | Category | File:Line | Issue | Suggested Fix | Found by |
|---|----------|-----------|-------|---------------|----------|
| 11 | Numbers | `supplementary.tex` (tab:keeps) | **4 H-mean values rounded up by +0.001.** Experiments 2, 26, 38, 41 show 0.815/0.817/0.827/0.828 but correct values are 0.814/0.816/0.826/0.827. Systematic upward rounding. | Correct H-mean column values. | number-auditor |
| 12 | Bib | `references.bib` (vaswani2017attention) | **Ghost entry.** "Attention is all you need" exists in bib but is never cited in any .tex file. | Remove entry or add a citation where relevant. | bib-checker, coherence-reviewer |
| 13 | Bib | `references.bib` (burges2010ranknet) | **Garbled venue.** Listed as `booktitle={Learning}` but is actually Microsoft Research Tech Report MSR-TR-2010-82. Known bibliographic anomaly. | Change to `@techreport` with `institution={Microsoft Research}`, number `MSR-TR-2010-82`. | bib-checker |
| 14 | Bib | `references.bib` (pirtskhalava2024dbaasp) | **Unverifiable.** No DBAASP v4 NAR 2024 publication found. Latest verifiable is v3 (2021). May be genuine forthcoming paper. | Manually verify -- check DBAASP website or contact authors. | bib-checker |
| 15 | Scope | `introduction.tex:26` | **"First application" is an unverifiable priority claim.** | Consider "An application of..." or verify no prior work exists. | scope-checker |
| 16 | Scope | `related_work.tex:22` | **"peptide drug discovery" framing.** PRD says "this is not a drug discovery system" -- prefer "peptide candidate triage". | Replace with "peptide candidate triage." | scope-checker |
| 17 | Scope | `results.tex:174` | **"statistically significant margins"** inferred from non-overlapping bootstrap CIs without formal test. Companion paper uses p-values. | Add formal test or soften to "non-overlapping CIs." | scope-checker |
| 18 | Scope | `discussion.tex:12` | **"confirming" implies prior certainty.** Companion paper tone uses "indicating" or "suggesting." | Replace "confirming" with "indicating." | scope-checker |
| 19 | Scope | General | **No effect sizes (Cohen's d) reported.** Companion paper includes them for key comparisons. | Consider adding for agent vs NSGA-II and agent vs weighted sum. | scope-checker |
| 20 | Figure | `results.tex:97,102` | **Fig 3 caption says "three strategies" but text says "each strategy."** Minor ambiguity. | Align text to "three representative strategies." | coherence-reviewer |
| 21 | Scope | `results.tex:174` | **"statistically significant"** language used without formal hypothesis test. Bootstrap CI non-overlap != formal significance test with controlled Type I error. | Rephrase or add formal test. | scope-checker (duplicate of #17, merged) |

---

## Detailed Results by Reviewer

### bib-checker
- **28 entries examined**, 6 with metadata errors, 1 fabricated, 1 ghost
- Companion paper citation (arXiv:2603.28015) verified: all claims match
- Most serious: `lee2023peptidevae` appears fabricated, `gupta2024toxinpred3` and `sharma2014hlp` have completely wrong metadata

### number-auditor
- **All 6 tasks pass** (N1-N6)
- 170+ individual values checked across Tables 1, 3, S1-S4
- Only finding: 4 H-mean rounding errors of +0.001 in supplementary Table S1
- Inline claims (0.650 +/- 0.034 etc.) verified consistent across all 4 sections where they appear

### coherence-reviewer
- **Cross-references: PASS** (all 18 \ref/\label pairs resolve, zero undefined refs)
- **Number consistency: FAIL** ("12 improvements" inconsistency)
- **Claim-evidence: FAIL** (false "non-overlapping CIs" claim)
- **Figure-text: PASS** (1 minor ambiguity)

### scope-checker
- **All 7 required limitations: PASS** (covered in discussion.tex lines 24-53)
- **No hype language found** (no "breakthrough", "revolutionary", "state-of-the-art")
- **1 major overclaiming issue** ("reliably outperforms all baselines")
- **Tone generally matches companion paper** with minor gaps (no p-values, no effect sizes)

---

## Recommended Fix Priority

**Do immediately (before any submission):**
1. Fix or remove `lee2023peptidevae` (fabricated reference)
2. Fix `gupta2024toxinpred3` metadata (wrong everything)
3. Fix `sharma2014hlp` metadata (wrong everything)
4. Fix `huang2024mlagentbench` venue (NeurIPS -> ICML)
5. Fix "non-overlapping CIs" claim (5 locations) -- either recompute or rephrase
6. Fix "12 improvements" -> "11 improvements + baseline" (3 locations)
7. Fix `yan2022review` metadata
8. Fix `veltri2018ampscanner` author (Bhatt -> Shehu)

**Do before camera-ready:**
9. Update `xie2021mars` to ICLR 2021
10. Fix 4 H-mean rounding values in supplementary
11. Soften "reliably outperforms all baselines"
12. Remove ghost `vaswani2017attention` or add citation
13. Fix `burges2010ranknet` to tech report format
14. Verify `pirtskhalava2024dbaasp` manually
