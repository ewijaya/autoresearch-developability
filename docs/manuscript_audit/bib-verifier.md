---
name: bib-verifier findings
description: Fact-check results for every @entry in manuscript/references.bib (manuscript-audit team, task #1)
type: audit-report
---

# Bibliography Verification Report

**Auditor:** bib-verifier
**Source file:** `/home/ubuntu/storage1/autoresearch-developability/manuscript/references.bib`
**Entries audited:** 25
**Date:** 2026-04-20

## Summary Counts

- **Verified (no changes needed):** 22
- **Minor issues (nits, optional polish):** 3
- **Major issues:** 0
- **Blockers / fabricated entries:** 0

Every bibliographic entry corresponds to a real, publicly retrievable source. The companion arXiv paper `2603.28015` resolves to the stated title/author. The Karpathy `autoresearch` GitHub repository exists at the given URL. No entry is fabricated. Two entries have minor field-type/ordering nits and one has a journal-vs-booktitle nit; none block publication.

## Summary Table

| citekey | status | evidence | correction-if-any |
|---|---|---|---|
| wijaya2026autonomousagentdiscoversmolecular | verified | arxiv.org/abs/2603.28015 resolves; title and author match (Edward Wijaya, cs.AI, 2026-03) | none (the citekey is unusually long but functional) |
| chen2023evoprompting | verified | NeurIPS 2023 poster; arXiv 2302.14838; authors Angelica Chen, David Dohan, David So | none |
| romeraparedes2024funsearch | verified | Nature vol 625, pp 468-475, 2024; DOI 10.1038/s41586-023-06924-6 | optional: add `doi={10.1038/s41586-023-06924-6}` |
| karpathy2026autoresearch | verified | github.com/karpathy/autoresearch exists; README frames project in "March 2026" — year field consistent | none |
| deb2002nsga2 | verified | IEEE TEVC vol 6, no 2, pp 182-197, 2002; DOI 10.1109/4235.996017 | optional: add DOI |
| zhang2007moead | verified | IEEE TEVC vol 11, no 6, pp 712-731, 2007; DOI 10.1109/TEVC.2007.892759 | optional: add DOI |
| emmerich2018tutorial | verified | Natural Computing vol 17, no 3, pp 585-609, 2018; DOI 10.1007/s11047-018-9685-y | optional: add DOI |
| jin2020multiobjective | verified with nit | ICML 2020 (PMLR vol 119), pp 4849-4859; authors Jin, Barzilay, Jaakkola | **nit**: entry uses `@article` with `journal={Proceedings of the International Conference on Machine Learning}`; conventional form is `@inproceedings` + `booktitle={Proceedings of the 37th International Conference on Machine Learning}` + `volume={119}`. Current form still compiles and resolves. |
| xie2021mars | verified | ICLR 2021 spotlight; arXiv 2103.10432; authors and title match exactly | none |
| brown2019guacamol | verified | JCIM vol 59, no 3, pp 1096-1108, 2019; DOI 10.1021/acs.jcim.8b00839 | optional: add DOI |
| pirtskhalava2021dbaasp | verified | NAR vol 49, D1, pp D288-D297, 2021; DOI 10.1093/nar/gkaa991 (already present) | none |
| rathore2024toxinpred3 | verified | CBM vol 179, 108926, 2024; DOI 10.1016/j.compbiomed.2024.108926 (already present) | none |
| sharma2014hlp | verified | BMC Bioinformatics vol 15, 282, 2014; DOI 10.1186/1471-2105-15-282 (already present) | none |
| lin2023esm2 | verified | Science vol 379, no 6637, pp 1123-1130, 2023; DOI 10.1126/science.ade2574 | optional: add DOI |
| ke2017lightgbm | verified | NeurIPS 2017 (vol 30); pages 3146-3154 in the proceedings | optional: add `pages={3146--3154}` |
| burges2010ranknet | verified | MSR-TR-2010-82, Microsoft Research, 2010 | none |
| lu2024aiscientist | verified | arXiv 2408.06292, 2024; authors Lu, Lu, Lange, Foerster, Clune, Ha | none |
| huang2024mlagentbench | verified | ICML 2024, PMLR vol 235, pp 20271-20309; authors Huang, Vora, Liang, Leskovec | none |
| veltri2018ampscanner | verified | Bioinformatics vol 34, no 16, pp 2740-2747, 2018; DOI 10.1093/bioinformatics/bty179 | optional: add DOI |
| yan2022review | verified | Antibiotics vol 11, no 10, 1451, 2022; DOI 10.3390/antibiotics11101451 (already present) | none |
| mooney2012peptidemoo | verified with nit | PLoS One vol 7, no 10, e45012, 2012; DOI 10.1371/journal.pone.0045012; authors Mooney, Haslam, Pollastri, Shields | **nit**: citekey `peptidemoo` is a weird truncation of "peptide...MOO"-ish; does not affect compilation. Optional: add DOI. |
| liu2009learningtorank | verified | Foundations and Trends in IR vol 3, no 3, pp 225-331, 2009; DOI 10.1561/1500000016 | optional: add DOI |
| cormack2009rrf | verified | SIGIR 2009, pp 758-759; DOI 10.1145/1571941.1572114 | optional: add DOI |
| jarvelin2002ndcg | verified | ACM TOIS vol 20, no 4, pp 422-446, 2002; DOI 10.1145/582415.582418 | optional: add DOI |
| zitzler2003hypervolume | verified | IEEE TEVC vol 7, no 2, pp 117-132, 2003; DOI 10.1109/TEVC.2003.810758 | optional: add DOI |
| bergstra2012random | verified | JMLR vol 13, pp 281-305, 2012 | none |

## Detailed Findings (sorted by severity)

### Blockers
None.

### Major
None.

### Minor / Nits

1. **`jin2020multiobjective` — entry type mismatch.** Declared as `@article` with `journal={Proceedings of the International Conference on Machine Learning}`. ICML PMLR proceedings are conventionally cited as `@inproceedings` with `booktitle={Proceedings of the 37th International Conference on Machine Learning}`, `series={PMLR}`, `volume={119}`, `pages={4849--4859}`. Current form is unambiguous and will compile; this is a style-consistency nit, since the sibling ICML/NeurIPS entries in this bib (`chen2023evoprompting`, `xie2021mars`, `ke2017lightgbm`, `huang2024mlagentbench`) use `@inproceedings`.

2. **`mooney2012peptidemoo` — idiosyncratic citekey.** The key fragment `peptidemoo` looks like a truncation artifact ("peptide multi-objective?"). Not a bibliographic error; rename only if the author wants cleaner keys (e.g. `mooney2012peptideranker`).

3. **Missing DOIs on ~12 entries.** Several entries (FunSearch, NSGA-II, MOEA/D, Emmerich 2018 tutorial, GuacaMol, ESM-2, NDCG, hypervolume, RRF, Liu LTR, Veltri AMP Scanner, LightGBM) have verifiable DOIs that are not included. This is cosmetic — journals and reviewers typically expect DOIs on non-arXiv citations. Optional polish.

### Special-attention entry (companion paper)

`wijaya2026autonomousagentdiscoversmolecular` with arXiv **2603.28015** resolves successfully:

- **Title (from arXiv):** "What an Autonomous Agent Discovers About Molecular Transformer Design: Does It Transfer?"
- **Author:** Edward Wijaya
- **Primary class:** cs.AI
- **Month encoding:** arXiv ID prefix `2603` = March 2026, consistent with the `year={2026}` field.

All fields (title, author, eprint, primaryClass, url) match the live arXiv record. No fabrication. The citekey is unusually long but is internally consistent and compiles cleanly.

## Verification method

For each entry I queried one or more of: WebSearch (title + authors + venue), WebFetch against publisher or arXiv landing pages, and cross-checked volume/issue/page metadata against at least two independent result sources (publisher site + Semantic Scholar / PubMed / dblp / DOI.org). The companion arXiv paper was fetched directly from `arxiv.org/abs/2603.28015`. The Karpathy `autoresearch` GitHub repo was fetched to confirm existence and consistency with the `year={2026}` field.
