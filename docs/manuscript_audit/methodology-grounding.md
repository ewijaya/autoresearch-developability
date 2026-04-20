# Methodology Grounding & Technical-Claim Audit

**Scope:** `manuscript/sections/methodology.tex`, `results.tex`, `related_work.tex`; cross-checked against `abstract.tex`, `introduction.tex`, `discussion.tex`, `conclusion.tex`, `references.bib`.
**Mode:** Read-only. No manuscript files were modified.
**Auditor:** methodology-grounding (task #4).

---

## 1. Summary Table

| # | Claim | Section(s) | Citekey | Verdict | Evidence |
|---|-------|------------|---------|---------|----------|
| 1 | DBAASP "v4" with 3,554 *E. coli* peptides | methodology.tex L31, L40 | `pirtskhalava2021dbaasp` | **BLOCKER** (version mismatch) | Cited paper is "DBAASP **v3**" (Nucleic Acids Res. 49(D1), 2021). Intro and abstract say "DBAASP" (no version). No `pirtskhalava*2023*` / v4 citation exists in references.bib. |
| 2 | NSGA-II is "designed" to "spread solutions across the Pareto front" / "Pareto spread" | results.tex L45, discussion.tex L17, intro.tex L10 | `deb2002nsga2` | **PASS** (minor nuance) | Deb 2002 explicitly states dual goals of NSGA-II: (a) convergence to the Pareto-optimal set, (b) maintenance of diversity (via crowding distance). "Pareto spread" is a legitimate short-hand for (b); the phrasing is accurate. |
| 3 | NSGA-II uses "non-dominated sorting with crowding distance tie-break" | methodology.tex L126 | `deb2002nsga2` | **PASS** | Exactly matches Deb 2002 mechanism. |
| 4 | Reciprocal rank fusion across multiple scoring functions | results.tex L84, discussion.tex L7 | `cormack2009rrf` | **PASS** | Cormack, Clarke, Buettcher SIGIR 2009. Formula `sum 1/(k+rank_i)`; combining multiple ranked lists. Usage here (fuse threshold-gated, rank product, Pareto) is an appropriate application. |
| 5 | NDCG = "normalized discounted cumulative gain" | methodology.tex L85 | `jarvelin2002ndcg` | **PASS** | Järvelin & Kekäläinen, ACM TOIS 20(4), 2002 — original DCG/NDCG formulation (called "cumulated gain"); NDCG as a standard derivative is universally attributed to this work. |
| 6 | Hypervolume = "dominated area in the (activity, 1−toxicity) plane" | methodology.tex L86 | `zitzler2003hypervolume` | **PASS** | Zitzler et al. 2003 "Performance assessment of multiobjective optimizers" — standard hypervolume reference; "dominated area/volume bounded by reference point" is the canonical definition. |
| 7 | LambdaMART gradient-boosted learning-to-rank | intro.tex L21, results.tex L90 | `ke2017lightgbm`, `burges2010ranknet` | **MINOR** (attribution) | `burges2010ranknet` is "From RankNet to LambdaRank to LambdaMART: An Overview" (MSR-TR-2010-82) — correctly describes LambdaMART. `ke2017lightgbm` is the LightGBM library (which implements LambdaMART via `objective='lambdarank'`) — appropriate as the tooling citation. OK, but the intro cites only `ke2017lightgbm` for the LambdaMART concept (line 21), which is technically the library not the algorithm. |
| 8 | ESM-2 "8M-parameter model" | methodology.tex L45 | `lin2023esm2` | **PASS** | Official ESM-2 checkpoint list includes `esm2_t6_8M_UR50D` (6 layers, 320-d). Paper is Lin et al., *Science* 379(6637):1123–1130, 2023 — correct. |
| 9 | "DBAASP v3" dataset content | methodology.tex (see #1); also intro L17 | `pirtskhalava2021dbaasp` | **PASS** (content) | DBAASP v3 indeed contains MIC data for AMPs incl. *E. coli* ATCC 25922. The *version label* is wrong (see #1), but the data use is legitimate. |
| 10 | ToxinPred3 toxicity training labels | methodology.tex L45, related_work.tex L11 | `rathore2024toxinpred3` | **PASS** | Rathore et al., *Comput. Biol. Med.* 179:108926, 2024 — improved peptide toxicity predictor. AUC 0.920 on local RF classifier is internally consistent (original ToxinPred3 reports AUROC up to 0.95–0.98 with its best hybrid method; 0.920 for a small RF reproduction is plausible). |
| 11 | HLP = "peptide half-life data" (stability endpoint) | methodology.tex L50, intro.tex L17, related_work.tex L11 | `sharma2014hlp` | **PASS — but flag to team-lead** | `sharma2014hlp` bib entry is correctly "Designing of peptides with desired half-life in intestine-like environment" (BMC Bioinformatics 15:282, 2014). The task brief refers to HLP as "hemolytic peptide predictor" — that is **incorrect**. The manuscript's characterization (intestinal half-life → stability proxy) matches the cited source. |
| 12 | GuacaMol = benchmark suite for molecular design | related_work.tex L5 | `brown2019guacamol` | **PASS** | Brown, Fiscato, Segler, Vaucher, *JCIM* 59(3):1096–1108, 2019. "Benchmark suite" is accurate. |
| 13 | Baseline numbers consistency (0.650 / 0.444 / 0.611 / 0.609 / 0.037) | abstract, intro, results, discussion, conclusion | — | **PASS** (see §4) | All five numbers are internally consistent across sections; full cross-check in §4 below. |

---

## 2. Detailed Findings (sorted by severity)

### BLOCKER — B1. DBAASP version mismatch (v3 vs v4)

**Location:** `methodology.tex` line 31 (Table caption column "Source") and line 40 (prose).

**Claim:** "DBAASP v4" is cited with `\citep{pirtskhalava2021dbaasp}`.

**Evidence:**
- `references.bib` L108–118: `pirtskhalava2021dbaasp` → "DBAASP **v3**: database of antimicrobial/cytotoxic activity and structure of peptides ...", *Nucleic Acids Research* 49(D1):D288–D297, 2021 (DOI `10.1093/nar/gkaa991`).
- External verification (PubMed PMID 33151284; NAR 49(D1) 2021): the paper is explicitly titled and labelled **DBAASP v3**.
- The only subsequent DBAASP publication announcing a "v4" is a later (2024) update; no such bib entry is present in `references.bib`.
- `introduction.tex` L17 writes simply "DBAASP" (no version), and `abstract.tex` L4 also writes "DBAASP" (no version). Only `methodology.tex` introduces "v4".

**Impact:** Readers/reviewers who follow the citation will find v3, creating a credibility hit. Two fixes are available:
1. (Preferred) Change "DBAASP v4" → "DBAASP v3" in `methodology.tex` L31, L40 to match the cited reference.
2. (If v4 is truly the source) Add a v4 bib entry and cite it; verify the 3,554 *E. coli* ATCC 25922 candidate count is what v4 returns.

**Verdict:** BLOCKER — the manuscript as written cites the wrong version label; trivial to fix either direction but must be consistent with what was actually used to build the benchmark.

---

### MAJOR — none identified.

---

### MINOR

#### M1. LambdaMART attribution in Introduction cites library, not algorithm

**Location:** `introduction.tex` L21: "... learned MLP and LambdaMART \citep{ke2017lightgbm} ensembles."

**Issue:** LambdaMART is the algorithm (Burges 2010 / Wu et al. 2010). LightGBM (Ke et al. 2017, NeurIPS) is one implementation among several. The results section L90 does cite both (`ke2017lightgbm,burges2010ranknet`), so the fix is a one-citation addition in the intro for consistency with §6.

**Recommendation:** Change `\citep{ke2017lightgbm}` → `\citep{ke2017lightgbm,burges2010ranknet}` on intro line 21 (or `\citep{burges2010ranknet}` alone, with LightGBM mentioned once in methodology as the implementation).

**Severity:** MINOR (attribution hygiene; does not mischaracterize what LambdaMART is).

#### M2. HLP dataset size in Table 1 vs cited source

**Location:** `methodology.tex` Table 1 (L33): "Stability / HLP / 1,353 train".

**Check:** Sharma et al. 2014 HLP used HL10 (10-mer) and HL16 (16-mer) datasets in the paper; the web server aggregates additional peptides. 1,353 is within the plausible range of the combined HLP-derived training set but was not verifiable directly from the source abstract. Recommend the authors confirm 1,353 traces to an explicit HLP subset. Non-blocking for correctness of the *claim* (a predictor trained on HLP data) but worth a double-check.

**Severity:** MINOR (traceability; no evidence of error, but I could not fully verify the count from the primary source alone).

#### M3. ToxinPred3 reported AUC divergence from original paper

**Location:** `methodology.tex` L46: "Held-out AUC is 0.920" for the local RF classifier on ToxinPred3 labels.

**Check:** Original ToxinPred3 paper reports AUROC up to ≈0.95 (extra-tree features) and ≈0.98 (hybrid method). The manuscript's RF-with-physchem-plus-ESM-2-8M achieves 0.920, which is plausible but below the original's best. No mischaracterization — the manuscript is not claiming to reproduce ToxinPred3's headline number, only reporting the locally-trained RF's AUC. OK as written; no change recommended unless reviewers confuse the two numbers.

**Severity:** MINOR (clarity, not accuracy).

---

### NIT

#### N1. "DBAASP" without version in abstract/intro, "v4" in methodology

Even after fixing B1, the authors should decide on a single convention (`DBAASP v3` everywhere, or `DBAASP` with the version named only once at first mention). Current inconsistency is stylistic.

#### N2. Task-brief terminology: HLP as "hemolytic peptide predictor"

The team-lead's task brief referred to HLP as "hemolytic peptide predictor" (HLPpred-Fuse is a hemolytic predictor — different tool). The manuscript correctly treats `sharma2014hlp` as an intestinal-half-life predictor / stability proxy. No manuscript change needed; flagging for the team-lead so downstream audits do not propagate the misnomer.

---

## 3. Source-by-Source Verification (verbatim primary-source grounding)

| Citekey | What the primary source actually is | Manuscript's characterization | Grounded? |
|---------|--------------------------------------|-------------------------------|-----------|
| `deb2002nsga2` | Deb, Pratap, Agarwal, Meyarivan, *IEEE TEvC* 6(2):182–197, 2002. Elitist multi-objective GA with fast non-dominated sorting + crowding distance. Stated goals: convergence *and* diversity. | "non-dominated sorting with crowding distance tie-break" (methodology); "design goal of spreading solutions across the Pareto front" (results); "designed to maintain a diverse set of non-dominated solutions" (discussion). | ✅ Accurate. |
| `cormack2009rrf` | Cormack, Clarke, Buettcher, SIGIR 2009. Combine ranked lists via Σ 1/(k+rank_i). | "reciprocal rank fusion across multiple scoring functions" (results); "reciprocal rank fusion, combining multiple scoring functions into a consensus" (discussion). | ✅ Accurate. |
| `jarvelin2002ndcg` | Järvelin & Kekäläinen, *ACM TOIS* 20(4):422–446, 2002. Introduces DCG; NDCG is its normalized form. | "NDCG: normalized discounted cumulative gain at k=20." | ✅ Accurate (standard practice to cite this paper for NDCG). |
| `zitzler2003hypervolume` | Zitzler, Thiele, Laumanns, Fonseca, Fonseca, *IEEE TEvC* 7(2):117–132, 2003. Performance assessment of MOO; hypervolume is Pareto-compliant, measures volume dominated relative to reference point. | "Hypervolume: dominated area in the (activity, 1−toxicity) plane for the policy's top-k selections." | ✅ Accurate. |
| `burges2010ranknet` | Burges, MSR-TR-2010-82. Describes RankNet → LambdaRank → LambdaMART evolution. LambdaMART = boosted-tree version of LambdaRank. | "LambdaMART" (results). | ✅ Accurate. |
| `ke2017lightgbm` | Ke et al., NeurIPS 2017. LightGBM library with LambdaMART objective via `lambdarank`. | Used jointly with `burges2010ranknet` in results; alone in intro. | ⚠️ See M1 — tooling citation, not algorithmic. |
| `lin2023esm2` | Lin et al., *Science* 379(6637):1123–1130, 2023. ESM-2 protein LM, variants from 8M to 15B parameters. | "ESM-2 embeddings from the 8M-parameter model." | ✅ Accurate (`esm2_t6_8M_UR50D` exists). |
| `pirtskhalava2021dbaasp` | Pirtskhalava et al., *NAR* 49(D1):D288–D297, 2021. **DBAASP v3**. | "DBAASP v4" (methodology). | ❌ Version mismatch — see B1. |
| `rathore2024toxinpred3` | Rathore et al., *Comput. Biol. Med.* 179:108926, 2024. ToxinPred 3.0 peptide toxicity. | Training labels for local RF toxicity classifier. | ✅ Accurate. |
| `sharma2014hlp` | Sharma et al., *BMC Bioinformatics* 15:282, 2014. HLP — peptide half-life in intestine-like environment. | Training data for local RF stability regressor. | ✅ Accurate. (Not hemolytic — see N2.) |
| `brown2019guacamol` | Brown, Fiscato, Segler, Vaucher, *JCIM* 59(3):1096–1108, 2019. Benchmark for de novo molecular design. | "benchmark suites such as GuacaMol" (related work). | ✅ Accurate. |

---

## 4. Baseline-Number Consistency Check

Task brief expects the following triage figures to be consistently reported:

| Strategy | Expected (brief) | Rounded-from value (table) |
|----------|------------------|----------------------------|
| NSGA-II | 44 % | 0.444 |
| Random-weight search (best) | 61 % | 0.611 |
| Weighted sum (equal-weight) | 61 % | 0.609 |
| Random | 4 % | 0.037 |
| Agent-improved | 65 % | 0.650 |

### 4.1 Appearance of each number across sections

| Value | Abstract | Intro | Methodology | Results | Discussion | Conclusion |
|-------|:--------:|:-----:|:-----------:|:-------:|:----------:|:----------:|
| 0.650 (agent) | ✅ L5 | ✅ L22, L33 | — | ✅ Table 1, L40, L44, L49, L53, L55, L167 | ✅ L12 | ✅ L5 |
| 0.444 (NSGA-II) | ✅ L5 | ✅ L22 | — | ✅ Table 1, L44, L172 (implicit) | ✅ L17 | ✅ L5 |
| 0.611 (random wt.) | ✅ L5 | ✅ L22 | — | ✅ Table 1, L49 | ✅ L12 | ✅ L5 |
| 0.609 (equal-weight) | ✅ L6 ("0.609") | — | — | ✅ Table 1, L53 | — | — |
| 0.037 (random) | — | — | — | ✅ Table 1 only | — | — |
| 0.585 ± 0.050 (equal-weight, 10-split mean) | ✅ L6 | ✅ L33 | — | ✅ L55, L163, L167 | ✅ L36 (via CI reference) | ✅ L5 |
| 0.650 ± 0.034 (agent, 10-split mean) | ✅ L6 | ✅ L33 | — | ✅ L55, L163, L167 | — | ✅ L5 |

### 4.2 Verdict

**All five baseline numbers are reported consistently wherever they appear.** No value shifts across sections.

- 0.650 / 0.444 / 0.611 / 0.609 / 0.037 are each reported with the same decimal precision everywhere they occur.
- The single-split value (weighted sum = 0.609) and the 10-split mean (weighted sum = 0.585 ± 0.050) are *different measurements of the same strategy* — both are clearly labelled in context (single validation split vs 10 random splits). No ambiguity.
- Bootstrap 95 % CIs are also consistent: `[0.533, 0.767]` (agent), `[0.483, 0.733]` (weighted sum), `[0.267, 0.617]` (NSGA-II) are repeated in abstract, results (L44, L53, L172), discussion (L35), with the same numeric intervals.
- Table 1 in `results.tex` (L17–L30) is the single source of truth for the 8-strategy bar; every downstream prose number traces back to this table without drift.

**Minor note (nit, not a consistency issue):** `results.tex` L67 reports a *different* metric — "harmonic mean of top-k enrichment and NDCG progresses from 0.802 to 0.828" — on the loop's internal split ($n = 533$). This metric is distinct from top-k enrichment and is not a baseline number, so it doesn't fall under the consistency check; but readers should not confuse it with the 0.650 headline number. The prose makes the distinction clear (L65–67).

---

## 5. Recommended Edits (in severity order)

1. **BLOCKER** — Reconcile "DBAASP v4" (methodology.tex L31, L40) with the cited v3 reference, or add a v4 bib entry and cite it. Confirm which version actually supplied the 3,554 *E. coli* ATCC 25922 peptides.
2. **MINOR** — Add `burges2010ranknet` to the LambdaMART citation in `introduction.tex` L21 for consistency with `results.tex` L90.
3. **MINOR** — Verify the 1,353 HLP training count traces to a specific HLP subset (HL10 / HL16 / combined).
4. **NIT** — Pick a single DBAASP-version convention throughout.

No other technical characterizations were found to misrepresent their cited source.

---

## 6. Files Reviewed (absolute paths)

- `/home/ubuntu/storage1/autoresearch-developability/manuscript/sections/methodology.tex`
- `/home/ubuntu/storage1/autoresearch-developability/manuscript/sections/results.tex`
- `/home/ubuntu/storage1/autoresearch-developability/manuscript/sections/related_work.tex`
- `/home/ubuntu/storage1/autoresearch-developability/manuscript/sections/abstract.tex` (for consistency check)
- `/home/ubuntu/storage1/autoresearch-developability/manuscript/sections/introduction.tex` (for consistency check)
- `/home/ubuntu/storage1/autoresearch-developability/manuscript/sections/discussion.tex` (for consistency check)
- `/home/ubuntu/storage1/autoresearch-developability/manuscript/sections/conclusion.tex` (for consistency check)
- `/home/ubuntu/storage1/autoresearch-developability/manuscript/references.bib` (L40–L280)

## 7. External Sources Consulted

- Deb et al. 2002 NSGA-II — IEEE TEvC 6(2):182–197 (web searches + Deb NSGA-II PDF mirrors)
- Cormack, Clarke, Buettcher 2009 RRF — SIGIR 2009 (original PDF via cormack.uwaterloo.ca)
- Järvelin & Kekäläinen 2002 NDCG — ACM TOIS 20(4):422–446 (verified via Taylor & Francis and Wikipedia cross-check)
- Zitzler et al. 2003 hypervolume — IEEE TEvC 7(2):117–132
- Burges 2010 RankNet→LambdaRank→LambdaMART — MSR-TR-2010-82
- Lin et al. 2023 ESM-2 — Science 379(6637):1123–1130; ESM GitHub checkpoint list (facebookresearch/esm) for the 8M-parameter model variant
- Pirtskhalava et al. 2021 — *Nucleic Acids Research* 49(D1):D288–D297 — DBAASP **v3** (PMID 33151284)
- Rathore et al. 2024 ToxinPred 3.0 — *Comput. Biol. Med.* 179:108926
- Sharma et al. 2014 HLP — *BMC Bioinformatics* 15:282 (intestinal half-life, not hemolytic)
- Brown et al. 2019 GuacaMol — *JCIM* 59(3):1096–1108
