# Orphan and Missing Citation Audit

**Scope:** `manuscript/references.bib` cross-checked against every `\cite` / `\citep` / `\citet` command in `manuscript/main.tex` and `manuscript/sections/*.tex`.

**Date:** 2026-04-20

## Summary counts

| Metric | Count |
|---|---|
| Total bib entries in `references.bib` | 26 |
| Total unique citekeys cited in `.tex` sources | 26 |
| Total `\cite*` invocations across all .tex files | 31 |
| Orphan bib entries (never cited) | 0 |
| Undefined citations (cited but missing from bib) | 0 |

**Result: bib and cites are in one-to-one correspondence. No blockers, no cleanup needed.**

### Cite invocation distribution per file

| File | `\cite*` count |
|---|---|
| `sections/related_work.tex` | 10 |
| `sections/methodology.tex` | 9 |
| `sections/introduction.tex` | 7 |
| `sections/discussion.tex` | 3 |
| `sections/results.tex` | 2 |
| `main.tex` | 0 |
| `sections/abstract.tex` | 0 |
| `sections/conclusion.tex` | 0 |
| `sections/ethics.tex` | 0 |
| `sections/reproducibility.tex` | 0 |
| `sections/supplementary.tex` | 0 |

## Severity-sorted issues

**Blockers (undefined citations):** none.

**Minor (orphans):** none.

## Orphan table

| citekey | title | keep-or-drop |
|---|---|---|
| _(none)_ | — | — |

## Undefined citations table

| citekey | section | line |
|---|---|---|
| _(none)_ | — | — |

## Appendix: full citekey coverage

All 26 bib entries are cited at least once. Coverage below lists each key, its bib type/year, and every section where it appears.

| citekey | sections citing it |
|---|---|
| bergstra2012random | methodology |
| brown2019guacamol | related_work |
| burges2010ranknet | related_work, results |
| chen2023evoprompting | related_work |
| cormack2009rrf | results, discussion |
| deb2002nsga2 | methodology, introduction, related_work, discussion |
| emmerich2018tutorial | related_work |
| huang2024mlagentbench | related_work |
| jarvelin2002ndcg | methodology |
| jin2020multiobjective | related_work |
| karpathy2026autoresearch | methodology, introduction, related_work |
| ke2017lightgbm | introduction, results |
| lin2023esm2 | methodology, related_work |
| liu2009learningtorank | related_work |
| lu2024aiscientist | related_work |
| mooney2012peptidemoo | related_work |
| pirtskhalava2021dbaasp | methodology, introduction |
| rathore2024toxinpred3 | methodology, introduction, related_work |
| romeraparedes2024funsearch | related_work |
| sharma2014hlp | methodology, introduction, related_work |
| veltri2018ampscanner | introduction, related_work |
| wijaya2026autonomousagentdiscoversmolecular | methodology, introduction, related_work, discussion |
| xie2021mars | related_work |
| yan2022review | introduction |
| zhang2007moead | related_work |
| zitzler2003hypervolume | methodology |

## Method

1. Parsed bib keys by matching `^@<type>{<key>,` at the start of each entry in `references.bib` (26 entries).
2. Extracted every `\cite`, `\citep`, `\citet` (including optional `*`, optional `[...]` args, and comma-separated multi-key forms) from `main.tex` and `sections/*.tex`.
3. Split multi-key cite arguments on commas and deduplicated.
4. Computed `cited \ bib` (undefined) and `bib \ cited` (orphans).

No edits were made to anything in `manuscript/`; this audit is read-only.
