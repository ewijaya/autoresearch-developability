# Manuscript Audit Report
_Date: 2026-04-20 · Auditors: 6-Opus team_

## Summary

The manuscript is **nearly submission-ready from a mechanical standpoint** (clean LaTeX build, no undefined refs, no broken citations, all figures referenced) **but carries five blocking issues that must be resolved before posting to bioRxiv**: (1) an "activity/toxicity/stability/manufacturability" vs. "activity/toxicity/stability/developability" terminological split that touches the abstract, introduction, and methodology; (2) a "manufacturability" label that is not a biopharma synonym for "developability" and conflicts with the table, the code repository name, and the rule-based endpoint itself; (3) an overloaded use of "oracle" (harness ground-truth) vs. "heuristic score" (policy feature) that blurs the evaluation/policy boundary; (4) the term "LambdaMART oracle score" in the supplement that misleadingly implies a harness oracle; and (5) an inconsistent description of the loop's "Phase 3" boundary (experiments 32–94 in body text vs. 32–100 in figure caption) combined with an undocumented "manual pre-Codex" Phase 3 referenced only in the supplement. The should-fix list (20 items) is dominated by narrative polish, one orphan bib entry, abstract-level numeric ambiguity ("61%" is shared by two baselines), and figure-caption completeness. No numeric claim is wrong; no citation is broken; no reference or label is undefined. Recommended path: address the five blocking items, sweep the 20 should-fix items, and submit.

## Build Status

- **pdflatex result:** PASS (all three runs, exit 0; 15 pages, 340 kB).
- **bibtex result:** PASS (27 entries parsed, 0 warnings in `main.blg`).
- **Undefined refs:** 0
- **Undefined citations:** 0
- **Multiply-defined labels:** 0
- **Overfull/underfull boxes:** 5 total (1 overfull hbox at methodology `tab:datasets` line 27–37, 18.1 pt too wide; 1 underfull vbox during output; 3 underfull hboxes — two in `reproducibility.tex` around the GitHub URL, one in `supplementary.tex:33–34` in the keeps-table description cell).
- **Other notable warnings:** 1 `LaTeX Warning: 'h' float specifier changed to 'ht'` (supplementary `[h]` floats).
- **Missing files:** none. All six figure PDFs resolve. `manuscript/tables/` directory is empty (all tables are inline `.tex`); noted by crossref-checker but not load-bearing.

## (a) Blocking issues

1. **[TERMINOLOGY]** `sections/abstract.tex:6`, `sections/introduction.tex:7,25,40`, `sections/methodology.tex:9` — "manufacturability" is used as the name of the fourth endpoint in abstract/intro/problem-formulation, but the data table, all body prose in methodology/results/discussion, and the repository itself call it "developability" (and the underlying quantity is a rule-based developability penalty, not manufacturability). In biopharma these are **not synonyms**. Blocks: introduces an endpoint the reader cannot find in the tables/code. Fix: pick "developability" everywhere. _Jointly flagged by narrative-reviewer and terminology-reviewer._

2. **[TERMINOLOGY]** `sections/methodology.tex:§5.3`, `sections/results.tex:84,87,88`, `sections/supplementary.tex:100` — The three formulas (threshold-gate, rank-product, Pareto) are variously called **oracle** (harness role), **scoring functions**, **heuristic**, and **ranking criteria**. The same three names describe two structurally different roles: ground-truth evaluation harness AND policy features (consensus voting stage). Blocks: readers cannot tell which "oracle" the agent sees vs. is evaluated against. Fix: reserve **oracle** for harness ground truth, **heuristic score** for policy-internal features.

3. **[TERMINOLOGY]** `sections/supplementary.tex:38` — "LambdaMART oracle score" reads as an additional harness oracle but actually denotes a classifier trained to imitate the oracle. Blocks: compounds #2 above. Fix: rename to "LambdaMART oracle-aligned score" (consistent with `results.tex:90` and `discussion.tex:8`).

4. **[CLAIM]** / **[CROSSREF]** `sections/results.tex:72` (figure caption, "32–100") vs. `sections/results.tex:86` (body, "32–94") — The Phase 3 boundary is inconsistent between the figure 2 caption and the body subsection header. Table `tab:keeps` confirms the last kept experiment is #94. Blocks: a reader who reads the caption and then Table 2 in the supplement will see an unresolved three-off. Fix: change caption to "32–94". _Confirmed by narrative-reviewer, claim-auditor, crossref-checker._

5. **[NARRATIVE]** / **[CLAIM]** `sections/supplementary.tex:7,14` vs. `sections/results.tex:72,76,78,82,86` — "Phase 3" in the main text refers to Codex experiments 32–94, but `supplementary.tex` ("manual loop phase (Phase 3, prior to the Codex loop)") refers to a **different, undocumented "manual Phase 3"** preceding the Codex loop. Blocks: reviewers will conclude the pipeline has a hidden human-tuned stage that is not described in methodology. Fix: either rename the supplement's "manual Phase 3" or add a methodology subsection describing the manual pre-Codex loop.

## (b) Should-fix issues

6. **[CITATION]** `references.bib:247` — `mooney2012peptideranker` is defined but never cited. Fix: cite it in the peptide-ranking paragraph of `related_work.tex:11–14` (natural fit) or remove.

7. **[CLAIM]** `sections/abstract.tex:6` — "61% for equal-weight scalarization" is ambiguous because weighted-sum (0.609) and random weight search (0.611) **both round to 61%** (`results.tex:26,27`). Fix: say "61% for equal-weight scalarization (and best-of-1,000 random weight search)" or round to 3 sig figs.

8. **[CLAIM]** `sections/introduction.tex:26` — "12 modifications passed the keep/discard gate" is off by one. Methodology (`methodology.tex:112`) and discussion (`discussion.tex:5`) correctly state 11 improvements over the baseline (the +1 baseline never passes a gate because it is the starting point). Fix: "11 modifications passed the keep/discard gate".

9. **[CLAIM]** / **[TERMINOLOGY]** `sections/methodology.tex:34,54` — the caption and prose declare **7 penalties** but the enumeration lists only 6 (length, hydrophobic stretches, consecutive prolines, high net charge, high mean hydrophobicity, excess cysteines). Fix: either restore the seventh rule or change "7 penalties" to "6 penalties". _Flagged by claim-auditor._

10. **[CLAIM]** `sections/results.tex:65` — loop split is n=533 but methodology (`methodology.tex:59`) reports train/val/test as 2,452/539/563, with no mention of n=533. Fix: one sentence in §4.2 or §5.2 explaining that the loop trajectory uses an earlier data split (before the final evaluation split was fixed at n=539).

11. **[CLAIM]** / **[NARRATIVE]** `sections/conclusion.tex:5` — presents "0.650 ± 0.034 vs 0.585 ± 0.050" without the CI-overlap caveat that `results.tex:54,170` and `discussion.tex:34` explicitly flag. Fix: one clause acknowledging single-split CIs overlap.

12. **[TERMINOLOGY]** `sections/reproducibility.tex:5`, `sections/introduction.tex:21` — "ranking strategies" and "ranking code" drift from the canonical term "ranking policy". Fix: use "ranking polic(y|ies)".

13. **[TERMINOLOGY]** `sections/results.tex:88`, `sections/supplementary.tex:100`, `sections/related_work.tex:13` — "criteria" is used once meaning heuristic-score and once meaning endpoints. Fix: "heuristic score" and "endpoints" respectively.

14. **[TERMINOLOGY]** `sections/results.tex:46` — "top 20 candidates" → "top-20 candidates" (hyphenation consistent with every other "top-20" in the paper).

15. **[CROSSREF]** `sections/results.tex:69–74` (fig2 caption) — never names the y-axis metric. Body text uses harmonic mean of top-k enrichment and NDCG. Fix: add "y-axis: harmonic mean of top-k enrichment and NDCG".

16. **[CROSSREF]** `sections/results.tex:99–104` (fig3 caption) — uses "left/right" but names only 2 of 3 strategies and never labels which panel corresponds to PR/RP/TG oracle. Fix: spell out all three strategies and oracle per panel.

17. **[CROSSREF]** `sections/results.tex:144–149` (fig4 caption) — omits color-scale direction (sign of ΔTopK) and min/max. Fix: "red = worse, blue = better; range [−0.200, +0.183]".

18. **[CROSSREF]** `sections/results.tex:160–165` (fig6 caption) — never says "boxplot" and does not enumerate the strategies shown (the figure filename implies all 8). Fix: "boxplot of top-k enrichment across 8 strategies × 10 random splits".

19. **[CROSSREF]** `sections/results.tex:158` vs. `sections/supplementary.tex:7` — fig6 is referenced in main body but fig5 is supplementary-only; figure order is non-monotonic (fig6 appears before fig5 in reading order). Fix: renumber so the supplementary figure becomes fig6 (or vice versa).

20. **[NARRATIVE]** `sections/abstract.tex:2–5` ≈ `sections/introduction.tex:4–17` — abstract and introduction repeat the triage/spreadsheet/weighted-sum motivation nearly verbatim, and "We asked whether..." appears in both (`abstract.tex:5`, `introduction.tex:19`). Fix: compress abstract motivation to 1 sentence; intro keeps the full version.

21. **[NARRATIVE]** `sections/abstract.tex:7`, `sections/introduction.tex:32`, `sections/ethics.tex:7` — "we are not making a clinical claim" appears three times within 3 pages. Fix: keep it in the abstract and the ethics statement only.

22. **[NARRATIVE]** `sections/introduction.tex:22`, `sections/related_work.tex:20`, `sections/methodology.tex:96`, `sections/discussion.tex:14` — the companion paper (`wijaya2026autonomousagentdiscoversmolecular`) is re-introduced 4 times with the same "3,106 experiments across SMILES/protein/NLP" framing. Fix: full description once in related_work; discussion can cite with just `\citep{}`.

23. **[NARRATIVE]** `sections/results.tex:174` → `sections/discussion.tex:4` — Results ends with a summary sentence and Discussion opens cold with "What the loop discovered." Fix: Discussion should open with a one-sentence transition.

24. **[NARRATIVE]** `sections/introduction.tex:40`, `sections/methodology.tex:90` — "three mathematically distinct oracles" is promised but never cashed out in Results as a claim about oracle-structure diversity. Fix: one sentence in §4.5 or Table `tab:per_oracle` discussion.

25. **[CITATION]** `sections/introduction.tex:7` — `yan2022review` is load-bearing (it anchors the "multi-endpoint failure is a lead killer" motivation) but is never resurfaced in related_work or discussion. Fix: cite once more in `related_work.tex` peptide-property-prediction paragraph.

## (c) Nits

26. **[NARRATIVE]** `sections/abstract.tex:8` — "swap the candidate pool with **your** internal peptide library" is a voice shift from third-person scientific prose to direct-address marketing. Fix: "swap the candidate pool with an internal peptide library".

27. **[NARRATIVE]** `sections/introduction.tex:45–46` — "The agent earned its keep beyond prompt-wrapped random search." is colloquial for a contribution bullet. Fix: reword to match the tone of bullets 1–3.

28. **[NARRATIVE]** `sections/introduction.tex:27` — "but the practical point for a biotech reader is" is a mid-sentence aside. Fix: trim.

29. **[NARRATIVE]** `sections/related_work.tex:22–23` — "This paper extends the autoresearch paradigm along two axes:" is a flat handoff into methodology. Optional polish.

30. **[NARRATIVE]** `sections/conclusion.tex:1–9` — no forward-looking sentence (no "next step" or "future work"). Fix: one closing clause.

31. **[CLAIM]** `sections/results.tex:26–27` — weighted-sum CI [0.483, 0.733] and random-weight-search CI [0.483, 0.734] are nearly identical. Fix: add a one-line footnote flagging the equivalence.

32. **[CLAIM]** `sections/results.tex:78` — "Phase 1" is described as 10 experiments but Table `tab:keeps` shows only **1 kept** experiment beyond the baseline in that range (experiment #2). Fix: note "1 improvement in 10 experiments".

33. **[CLAIM]** `sections/abstract.tex` — omits the cross-split p≈0.001 and cross-split mean. Optional: strengthen.

34. **[CITATION]** `sections/introduction.tex:9` — `matsuzaki2009control` is introduction-only. Acceptable but noted.

35. **[CITATION]** `sections/methodology.tex:54` — `fjell2012peptidedev` could be resurfaced in `discussion.tex:24–28` where developability is flagged as a limitation. Optional.

36. **[TERMINOLOGY]** `sections/supplementary.tex:32` — table row uses the code identifier `agent_improved`; prose elsewhere uses "agent improved". Fix: "agent improved" (with space).

37. **[TERMINOLOGY]** `sections/methodology.tex:9` — `K` (number of endpoints) is introduced but never used downstream. Optional: drop.

38. **[TERMINOLOGY]** `sections/supplementary.tex:55` — "$n = 10$" overloads $n$ (candidates vs. splits). Optional: drop the math formatting.

39. **[BUILD]** `sections/methodology.tex:27–37` (tab:datasets) — one overfull hbox, 18 pt too wide. Trimmable by shortening the "Notes" column. Cosmetic.

40. **[BUILD]** `sections/reproducibility.tex:4–6` — two underfull hboxes around the GitHub URL. Cosmetic (stretched URL line).

## Preferred-term glossary

_From terminology-reviewer (task #4)._

| Term | Preferred usage |
|---|---|
| agent | the Codex/GPT-5.4 session that edits `rank.py` |
| ranking policy π | the mathematical object the agent edits (never "ranking strategy", "ranking code") |
| reranker | a learned model (MLP, LambdaMART) used within the policy as a secondary stage |
| endpoint | a per-candidate predicted property (activity, toxicity, stability, **developability**) — never "manufacturability" |
| metric | a number computed by the harness over a ranked list (top-k enrichment, NDCG, hypervolume, feasible fraction) |
| oracle | **harness role only** — one of the three ground-truth definitions (Pareto rank, rank product, threshold gate) |
| heuristic score | **policy-feature role only** — the same three formulas when used as features inside the policy (consensus voting, RRF) |
| candidate / peptide | interchangeable; prefer "candidate" in policy/metric contexts, "peptide" in biology contexts |
| top-20 shortlist | the k=20 output of the policy (hyphenated; never "top 20") |
| N | size of the pool (=3,554) |
| K | number of endpoints (=4) — currently unused in body text |
| k | top-k cutoff (=20) |
| p | p-value |

## Per-figure reference count

_From crossref-checker (task #5) plus independent verification._

| Figure | Label | Referenced in | Count | Notes |
|---|---|---|---|---|
| fig1 `fig1_baseline_comparison.pdf` | `fig:baseline_comparison` | `results.tex:9` | 1 | Caption complete. |
| fig2 `fig2_loop_trajectory.pdf` | `fig:loop_trajectory` | `results.tex:65` | 1 | **Y-axis metric unnamed in caption.** |
| fig3 `fig3_pareto_front.pdf` | `fig:pareto_front` | `results.tex:97` | 1 | **Only 2 of 3 strategies named; panels not mapped to oracles.** |
| fig4 `fig4_ablation_heatmap.pdf` | `fig:ablation_heatmap` | `results.tex:112` | 1 | **Color-scale direction/range not given.** |
| fig5 `fig5_weight_sensitivity.pdf` | `fig:weight_sensitivity` | `supplementary.tex:7` | 1 | Supplementary only; figure-order non-monotonic vs fig6. |
| fig6 `fig6_multi_split_boxplot.pdf` | `fig:multi_split` | `results.tex:158` | 1 | **"boxplot" word absent; strategies not enumerated.** |

All tables referenced: `tab:datasets` (1), `tab:strategies` (1), `tab:ablation` (1), `tab:keeps` (2), `tab:multi_split` (1), `tab:per_oracle` (1), `tab:qualitative` (1). 19 orphan `\label{sec:*}` anchors exist (harmless hyperref targets).

## Orphan bib entries

_From citation-auditor (task #3) plus independent verification._

| Key | File:line | Status |
|---|---|---|
| `mooney2012peptideranker` | `references.bib:247` | **Orphan** — defined, never cited. Natural home: `related_work.tex:11–14` peptide-property-prediction paragraph. |

All other 27 bib entries are cited at least once. 31 `\cite*{}` call sites resolve, 27 unique keys, 0 broken keys.

---

## Coordination note

All five teammate tasks (#1 narrative-reviewer, #2 claim-auditor, #3 citation-auditor, #4 terminology-reviewer, #5 crossref-checker) completed and were relayed to this task by the orchestrator because their environments lacked TaskUpdate/SendMessage schemas. Their findings are folded into the lists above. The submission-lead independently re-verified: the clean LaTeX build, the bib orphan, the figure reference count, the Phase-3 caption/body discrepancy, and the manufacturability/developability split.
