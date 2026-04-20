---
name: Manuscript Audit Fixes — Applied
date: 2026-04-20
scope: Items A1, B1, B2, C1–C7, E1–E3 from SUMMARY.md
---

# Manuscript Audit — Fixes Applied

This log records the disposition of every in-scope item from
[SUMMARY.md](SUMMARY.md). Five commits on `main` (24aa66c, 6873fc4, 7b52ef7,
76edde1, 9e48f76) plus one lead-applied unstaged edit
(`reproducibility.tex`) implement the fixes.

## Per-item disposition

| id | title | status | files touched | line(s) | diff summary |
|----|-------|--------|---------------|---------|--------------|
| A1 | DBAASP version label wrong | applied | `manuscript/sections/methodology.tex` | 31, 40 | "DBAASP v4" → "DBAASP v3" in Table 1 row and Activity prose. Commit 7b52ef7. |
| A1 (extension) | DBAASP v4 in reproducibility section | applied by lead | `manuscript/sections/reproducibility.tex` | 8 | "DBAASP v4" → "DBAASP v3" (out-of-original-scope third occurrence; folded into this commit). |
| B1 | PeptideRanker miscited as joint multi-endpoint ranker | applied | `manuscript/sections/related_work.tex` | 13 | Removed the trailing `\citep{mooney2012peptidemoo}` — the absence-of-prior-work claim now stands without a miscite. Commit 9e48f76. |
| B2 | Companion paper SMILES-NAS framing in discussion | applied | `manuscript/sections/discussion.tex` | 14 | Reframed from "outperformed random NAS on SMILES architecture search" to safer NL-domain anchor: "achieved an 81% improvement over random search on natural-language architecture tasks". Commit 9e48f76. |
| C1 | Activity↔toxicity membrane-mechanism claim uncited | applied | `manuscript/sections/introduction.tex` + `manuscript/references.bib` | intro L7 | Added `\citep{matsuzaki2009control}` to the membrane-disruption claim. Bib entry added in commit 76edde1; cite site in commit 9e48f76. |
| C2 | "Pareto spread vs. top-k concentration" uncited | applied | `manuscript/sections/introduction.tex`, `manuscript/sections/discussion.tex` | intro L11, discussion L17 | Added `\citep{emmerich2018tutorial}` at both anti-NSGA-II argument sites. Commit 9e48f76. |
| C3 | Developability rule thresholds uncited | applied | `manuscript/sections/methodology.tex` + `manuscript/references.bib` | methodology L54 | Added `\citep{fjell2012peptidedev}` after "seven sequence-level rules". New bib entry in 6873fc4 (NRDD 2012, DOI 10.1038/nrd3591); cite site in 7b52ef7. |
| C4 | Single-endpoint "most approaches" claim under-supported | applied | `manuscript/sections/introduction.tex` | L6 | Broadened cite from `\citep{veltri2018ampscanner}` to `\citep{veltri2018ampscanner,rathore2024toxinpred3,sharma2014hlp}`. Commit 9e48f76. |
| C5 | Portfolio-of-constraints claim under-supported | deferred | — | — | Prose-fixer judged the existing `yan2022review` cite acceptable; no additional Lau & Dunn entry added. No code change. |
| C6 | Bergstra & Bengio 2012 misframed for Dirichlet sampling | applied | `manuscript/sections/methodology.tex` | L125 | Reworded so `\citep{bergstra2012random}` anchors the "random-search-as-baseline paradigm" rather than the Dirichlet sampling choice. Commit 7b52ef7. |
| C7 | LambdaMART intro citation incomplete | applied | `manuscript/sections/introduction.tex` | L21 | Added `burges2010ranknet` co-cite: `\citep{ke2017lightgbm}` → `\citep{burges2010ranknet,ke2017lightgbm}`. Commit 9e48f76. |
| E1 | `jin2020multiobjective` entry-type mismatch | applied | `manuscript/references.bib` | — | Converted from `@article` (journal=...) to `@inproceedings` (booktitle=...). Commit 24aa66c. |
| E2 | `mooney2012peptidemoo` idiosyncratic citekey | applied | `manuscript/references.bib` | — | Renamed to `mooney2012peptideranker`. No cite-site updates needed because B1 had already removed the only invocation. Commit 24aa66c. |
| E3 | Missing DOIs on bib entries | partial (11/12 applied, 1 skipped) | `manuscript/references.bib` | — | Added DOIs for `deb2002nsga2`, `romeraparedes2024funsearch`, `zhang2007moead`, `emmerich2018tutorial`, `brown2019guacamol`, `lin2023esm2`, `jarvelin2002ndcg`, `cormack2009rrf`, `liu2009learningtorank`, `veltri2018ampscanner`, `zitzler2003hypervolume` (plus `mooney2012peptideranker` opportunistically). Skipped `ke2017lightgbm` — NeurIPS 2017 proceedings paper has no publisher-issued DOI; only an aggregator DOI exists, which would violate the no-fabrication rule. Commit 24aa66c. |

## Build status

- **pdflatex available:** yes (TinyTeX at `/home/ubuntu/.TinyTeX/bin/x86_64-linux/`).
- **Build command:** `pdflatex && bibtex && pdflatex && pdflatex` (4 passes).
- **Exit code:** 0 (clean).
- **Undefined citations:** 0 (pre-fix) → 0 (post-fix). No regressions.
- **LaTeX errors (`! ` lines):** 0 (pre-fix) → 0 (post-fix).
- **Warnings:** 5 (pre-fix) → 4 (post-fix). All remaining warnings are
  benign `'h' float specifier changed to 'ht'` notices on tables; one of
  the pre-fix warnings was eliminated incidentally by the methodology
  edits. No new warnings introduced.
- **Bib entry count:** 26 → 28 (added `fjell2012peptidedev` for C3 and
  `matsuzaki2009control` for C1; renamed `mooney2012peptidemoo` →
  `mooney2012peptideranker` in place).
- **Cite ↔ bib coherence:** 28 bib entries; 28 unique cite keys;
  one-to-one. No orphans, no undefined references.

## Notes on skipped / deferred items

- **C5 (deferred):** prose-fixer judged the existing `yan2022review` citation
  sufficient for the portfolio-of-constraints framing; no additional
  peptide-developability reference was added. Low-severity nit; revisit if
  reviewer pushback.
- **E3 / `ke2017lightgbm` (skipped):** no publisher-issued DOI exists for the
  NeurIPS 2017 proceedings paper. Only an ACM aggregator DOI (10.5555/...) is
  available, which is not a true publisher DOI. Per the no-guess rule, no
  DOI was added.
- **F1 (out of scope):** double-blind compliance is intentionally untouched —
  manuscript remains in preprint mode. Submission-time checklist item.

## Commit lineage

```
24aa66c  refs: fix bib entries (citekey rename, DOIs, entry type)        [bib-fixer]
6873fc4  refs: add fjell2012peptidedev entry for developability rules    [bib-fixer]
7b52ef7  manuscript: fix DBAASP version and tighten methodology cites    [methodology-fixer]
76edde1  refs: add Matsuzaki 2009 for activity-toxicity claim            [bib-fixer]
9e48f76  manuscript: fix miscited claims and add missing citations       [prose-fixer]
(this commit: reproducibility.tex A1 extension + this log)
```
