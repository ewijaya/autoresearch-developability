# Manuscript Audit — Synthesis & Fix List

**Manuscript:** NeurIPS 2026 submission, agent-guided ranking policy improvement for peptide drug candidate prioritization
**Date:** 2026-04-20
**Scope:** `manuscript/main.tex`, `manuscript/sections/*.tex`, `manuscript/references.bib`
**Mode:** Read-only audit. No manuscript files were modified.

## Headline

The manuscript is in strong shape bibliographically. **Zero fabricated references, zero undefined citations, zero orphan bib entries, baseline numbers consistent across all sections.** The companion arXiv paper (2603.28015) resolves and matches its bib entry. However, there are **two must-fix items** before submission (one blocker, one miscite) and one medium-severity pre-submission item (double-blind compliance) that becomes a blocker only if the venue requires anonymization.

- Entries audited: 25 bib / 31 cite invocations / 26 unique keys
- Blockers: **1** (DBAASP version label)
- Major: **1** (PeptideRanker miscite)
- Medium (pre-submission): **1** (double-blind self-citation)
- Minor + missing-citation flags: **8**
- Nits: **2**

Full per-teammate reports:
- [bib-verifier.md](bib-verifier.md) — every @entry fact-checked against live sources
- [citation-coherence.md](citation-coherence.md) — every `\cite*` claim judged against source
- [orphan-and-missing.md](orphan-and-missing.md) — bib ↔ body cross-check
- [methodology-grounding.md](methodology-grounding.md) — technical-claim grounding + baseline-number consistency
- [companion-paper-check.md](companion-paper-check.md) — arXiv 2603.28015 verification + double-blind flag

---

## Top ~15 items to fix before submission

### A. Fabricated or wrong-metadata references (must fix)

**A1. [BLOCKER] DBAASP version label is wrong.**
`methodology.tex` L31 (Table 1) and L40 (prose) say "DBAASP v4". The cited key `pirtskhalava2021dbaasp` is the **v3** paper (NAR 49(D1), 2021). Intro L17 and abstract say just "DBAASP" (no version). No v4 bib entry exists. Fix: change "v4" → "v3" in methodology, OR add a v4 bib entry and verify the 3,554 *E. coli* ATCC 25922 count comes from v4. Source: methodology-grounding §B1.

*No fabricated references. No wrong-year/wrong-venue entries. The companion arXiv 2603.28015 is real.*

### B. Miscited claims (must fix)

**B1. [MAJOR] PeptideRanker miscited as joint multi-endpoint ranker.**
`related_work.tex` L13: "few address the joint ranking problem across multiple developability criteria \citep{mooney2012peptidemoo}". Mooney 2012 (PeptideRanker) is a *single-output* generic bioactivity classifier; it does not do joint activity+toxicity+stability+manufacturability ranking. This is the only citation anchoring the gap-in-literature claim and load-bears on novelty. Fix: drop the cite (the absence is itself the claim) or reframe to "generalized single-score peptide bioactivity prediction" (which breaks the sentence). Source: citation-coherence §M1.

**B2. [MINOR-MAJOR] Companion paper framing in discussion may cherry-pick a sub-analysis.**
`discussion.tex` L14: "the full agent outperformed random NAS on SMILES architecture search." The companion paper's *headline* SMILES finding is the opposite — hyperparameter tuning beats architecture search (p = 0.001). The agent-vs-random-NAS comparison is a narrower internal contrast that is not explicitly in the public abstract. Verify against the paper body; if only true for protein/NLP, narrow the claim (e.g., the NL-domain 81% improvement is a safer anchor). Source: citation-coherence §m5 + companion-paper-check §2.

### C. Missing citations on load-bearing claims (should fix)

**C1. [MAJOR-borderline] Activity ↔ toxicity membrane-mechanism claim is uncited.**
`introduction.tex` L7: "Because endpoints often conflict (highly active peptides tend toward membrane-disrupting mechanisms that correlate with toxicity)..." This biological claim frames the entire multi-objective motivation and has no citation. Standard anchors: Chen et al. 2005 (JBC), Matsuzaki 2009 (BBA Biomembranes), Yin et al. 2012 (JBC). Source: citation-coherence §MC1.

**C2. "Classical MOO optimizes for Pareto spread, not top-k concentration" is uncited in the spots that argue against NSGA-II.**
Intro L10–11 + discussion L17. `emmerich2018tutorial` is already in the bib and would support this; add it. Source: citation-coherence §MC2.

**C3. [MINOR] Developability rule thresholds in methodology L54 are uncited.**
The "seven sequence-level rules" (length, hydrophobic/proline runs, net charge, hydrophobicity, cysteines) directly weight every benchmark outcome. Either cite the source (e.g., Fjell et al. 2012 NRDD) or state explicitly "we chose these thresholds because...". Source: citation-coherence §MC3.

**C4. [MINOR] Single-endpoint "most approaches" claim in intro L6 rests on one cite.**
`veltri2018ampscanner` alone cannot substantiate a "most computational approaches optimize a single endpoint" claim. Either broaden (co-cite `rathore2024toxinpred3`, `sharma2014hlp`) or cite the review (`yan2022review`). Source: citation-coherence §m2.

**C5. [MINOR] Portfolio-of-constraints claim in intro L4 undersupported.**
`yan2022review` is an AMP-activity-centric review; it does not explicitly enumerate the activity + toxicity + stability + manufacturability quad. Consider an additional peptide-developability reference (e.g., Lau & Dunn 2018 BMC). Source: citation-coherence §m1.

**C6. [MINOR] Bergstra & Bengio 2012 used to justify Dirichlet-simplex MOO weight sampling.**
`methodology.tex` L125. Bergstra–Bengio argues random search > grid search for *hyperparameter* optimization; it does not justify Dirichlet weight sampling for MOO scalarization. Either soften (cite for "random search as a strong baseline paradigm") or add a weight-sampling reference (Das & Dennis 1997, or Deb 2001). Source: citation-coherence §m4.

**C7. [MINOR] LambdaMART attribution inconsistent.**
Intro L21 cites `ke2017lightgbm` alone (library, not algorithm); results L90 correctly co-cites `burges2010ranknet`. Add `burges2010ranknet` to intro L21. Source: citation-coherence §m3 + methodology-grounding §M1.

### D. Orphan bib entries (consider removing)

**D1. None.** All 26 bib entries are cited at least once. No pruning needed. Source: orphan-and-missing.

### E. Stylistic / nit (optional)

**E1. [NIT] `jin2020multiobjective` entry-type mismatch.**
Declared as `@article` with `journal=...ICML...`. Sibling ICML/NeurIPS entries use `@inproceedings` + `booktitle`. Compiles fine; style-consistency only. Source: bib-verifier.

**E2. [NIT] `mooney2012peptidemoo` idiosyncratic citekey.**
`peptidemoo` looks like a truncation artifact; rename to `mooney2012peptideranker` if desired. Source: bib-verifier.

**E3. [NIT] Missing DOIs on ~12 entries.**
NSGA-II, FunSearch, MOEA/D, Emmerich 2018, GuacaMol, ESM-2, NDCG, RRF, Liu LTR, Veltri, LightGBM, hypervolume all have verifiable DOIs not included. Cosmetic polish. Source: bib-verifier.

**E4. [NIT] HLP dataset size (1,353 training) in Table 1 could not be traced to a specific HLP subset.**
Sharma 2014 used HL10/HL16 datasets; 1,353 is plausible but worth an internal confirmation. Source: methodology-grounding §M2.

**E5. [NIT] DBAASP version convention — pick one and use everywhere.**
Even after fixing A1, decide on "DBAASP v3 throughout" or "DBAASP (first mention: v3)". Currently inconsistent. Source: methodology-grounding §N1.

---

## F. Pre-submission double-blind item (separate track)

**F1. [MEDIUM — becomes BLOCKER at submission if NeurIPS 2026 enforces double-blind]**

- Current state: `main.tex` L13–16 has the named author block active (Edward Wijaya, wijaya@stemrim.com). L10 has `% \author{Anonymous}` commented out — preprint mode.
- The four citation sites to `wijaya2026autonomousagentdiscoversmolecular` all use first-person possessive ("Our companion paper"): introduction.tex:14, related_work.tex:20, methodology.tex:96, discussion.tex:14.
- The companion paper (arXiv 2603.28015) is single-authored by Edward Wijaya. "Our companion paper" + a single-authored cited work is a direct de-anonymization vector.
- Fix before NeurIPS submission: (a) switch to `\author{Anonymous}`, and (b) rewrite the four "Our companion paper" phrases to third-person (e.g., "Prior work by \citet{wijaya2026...}" or "A concurrent arXiv preprint \citep{wijaya2026...}").
- Do NOT change anything now — the manuscript is in preprint mode. This is a checklist item for the submission switchover.

Source: companion-paper-check §3.

---

## Verified clean (positive findings — no action needed)

- All 25 bib entries correspond to real, retrievable sources with correct titles/authors/venues/years. (bib-verifier)
- Companion arXiv 2603.28015 resolves: title, author, submission date, primary class all match bib. (companion-paper-check)
- Baseline numbers (0.650 agent, 0.444 NSGA-II, 0.611 random-weight best, 0.609 equal-weight, 0.037 random) reported consistently across abstract, intro, results, discussion, conclusion. Bootstrap CIs also consistent. No numerical drift. (methodology-grounding §4)
- NSGA-II's "spread the frontier" attribution to `deb2002nsga2` is accurate — Deb 2002 explicitly states diversity preservation via crowding distance as a design goal. (methodology-grounding §2, row 2)
- All 10 domain-specific technical characterizations (NSGA-II mechanism, RRF, NDCG, hypervolume, LambdaMART, ESM-2 8M, DBAASP content, ToxinPred3, HLP-as-stability, GuacaMol) are accurately grounded in their cited sources. (methodology-grounding §3)
- ESM-2 "8M-parameter model" matches official `esm2_t6_8M_UR50D` checkpoint. (methodology-grounding)
- HLP is correctly characterized as an intestinal half-life / stability proxy (the task-brief description of HLP as "hemolytic peptide predictor" was a misnomer — the manuscript has it right). (methodology-grounding §N2)
- 26 bib entries ↔ 26 unique cited keys, one-to-one. No orphans, no undefined cites. LaTeX build will not fail on undefined references. (orphan-and-missing)

---

## Recommended fix ordering

1. **A1** (DBAASP v3/v4) — 30 seconds, trivially verifiable.
2. **B1** (drop or reframe PeptideRanker miscite) — 2 minutes.
3. **C1** (ground activity↔toxicity claim) — 5 minutes; pick one of the three suggested references.
4. **B2** (verify discussion L14 companion-paper framing) — requires opening the companion paper body; 10 minutes.
5. **C2, C7** (reuse `emmerich2018tutorial` and add `burges2010ranknet` to intro) — 2 minutes.
6. **C3–C6** — judgment calls, bundle in one revision pass.
7. **E1–E5** — optional polish.
8. **F1** — checklist item at submission time, do NOT touch now.

Audit complete. Awaiting lead review before any fixes are applied.
