# PRD: Agent-Team Manuscript Review

**Purpose:** Use Claude Code agent teams to fact-check `manuscript/references.bib`
and verify coherence across the full `manuscript/` directory.

**How to run:** Open Claude Code in the project root with agent teams enabled,
then paste the launch prompt from Section 5.

---

## 1. Prerequisites

Enable agent teams in your settings:

```json
// ~/.claude/settings.json  OR  .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Ensure the manuscript compiles before starting:

```bash
cd manuscript && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
```

---

## 2. Team Structure

Four teammates, each with a clearly scoped role. The lead synthesizes
findings into a final review report.

| Teammate | Role | Primary files | Tools needed |
|---|---|---|---|
| **bib-checker** | Verify every bib entry against real publications | `manuscript/references.bib` | WebSearch, WebFetch, Read, Grep |
| **number-auditor** | Cross-check every number in .tex files against source CSVs/TSVs | `manuscript/sections/*.tex`, `results/ablations/*.csv`, `results/loops/prompt5/results.tsv`, `data/manifests/manifest.json` | Read, Grep, Bash (python3 for arithmetic) |
| **coherence-reviewer** | Check logical flow, cross-references, claim-evidence alignment | All `manuscript/sections/*.tex` | Read, Grep |
| **scope-checker** | Verify all claims stay within stated limitations; no overclaiming | All `manuscript/sections/*.tex`, `docs/manuscript_PRD.md` | Read, Grep, WebFetch |

---

## 3. Task Definitions

### 3.1 bib-checker tasks

**Task B1: Verify bibliographic metadata for every entry in references.bib**

For each of the 28 entries in `manuscript/references.bib`:

1. Search the web (Google Scholar, Semantic Scholar, publisher site) for the
   paper by title.
2. Confirm these fields match the real publication:
   - `title` — exact wording (watch for subtitle omissions)
   - `author` — first author correct, author list not truncated incorrectly
   - `year` — matches actual publication year
   - `journal` / `booktitle` — correct venue name
   - `volume`, `number`, `pages` — match the real publication record
   - `doi` or `url` — valid and resolves (for arXiv/GitHub entries)
3. Flag entries where the bib key name misleads (e.g., `huang2024mlagentbench`
   — was it 2023 or 2024?).
4. Check for ghost entries: bib entries that exist but are never `\cite{}`d
   in any .tex file.
5. Check for missing entries: `\cite{}` keys in .tex files that have no
   matching bib entry.

**Output format:** A markdown table:

```
| Bib key | Field | Expected | Found | Status |
|---------|-------|----------|-------|--------|
```

Status: OK, MISMATCH, UNVERIFIED, GHOST (unused), MISSING (cited but absent).

---

**Task B2: Verify the companion paper citation is accurate**

The companion paper `wijaya2026autonomousagentdiscoversmolecular` (arXiv:2603.28015)
is cited prominently throughout the manuscript. Verify:

1. The arXiv ID 2603.28015 resolves to the correct paper.
2. The title, author, and year match.
3. Every claim attributed to the companion paper in the .tex files
   (e.g., "3,106 experiments", "domain-dependent value of architecture
   search") is consistent with the companion paper's abstract.

---

### 3.2 number-auditor tasks

**Task N1: Verify Table 1 (strategy comparison) against bootstrap CSV**

Source file: `results/ablations/bootstrap_val_k20.csv`

For every cell in Table 1 (`\label{tab:strategies}` in `results.tex`):

1. Read the CSV. Extract mean, CI lo, CI hi for each strategy × metric.
2. Compare to the LaTeX table values. Round to 3 decimal places.
3. Flag any mismatch > 0.001.

---

**Task N2: Verify Table 3 (ablation) against endpoint_ablation_val.csv**

Source file: `results/ablations/endpoint_ablation_val.csv`

For every ΔTopK and ΔNDCG value in `\label{tab:ablation}`:

1. Read the CSV. Compute delta from the `delta_topk` and `delta_ndcg` columns.
2. Compare to the LaTeX table values (3 decimal places).
3. Flag any mismatch.

---

**Task N3: Verify cross-split table against multi_split_summary.csv**

Source file: `results/ablations/multi_split_summary.csv`

Verify:
1. All mean and std values in `\label{tab:multi_split}` (supplementary)
   match the CSV.
2. The inline claims "0.650 ± 0.034 vs 0.585 ± 0.050" (appearing in
   abstract, introduction, results, conclusion) match the CSV.

---

**Task N4: Verify loop trajectory numbers against results.tsv**

Source file: `results/loops/prompt5/results.tsv`

1. Confirm exactly 12 rows have `status == keep` (including baseline).
2. Confirm the 12 experiment numbers in `\label{tab:keeps}` (supplementary)
   match the row positions in the TSV.
3. Verify TopK and NDCG values for each keep match the TSV.
4. Recompute H-mean = 2×TopK×NDCG/(TopK+NDCG) for each row and verify.
5. Confirm total experiment count = 100 (excluding header).
6. Confirm keep rate = 11/100 = 11% (baseline is keep #1, 11 improvements).

---

**Task N5: Verify dataset statistics against manifest.json**

Source file: `data/manifests/manifest.json`

1. Confirm: total_candidates = 3554.
2. Confirm mean/std for activity, toxicity, stability, dev_penalty in
   `methodology.tex` match the manifest (to 3 decimal places).
3. Confirm split sizes (2452/539/563) match actual file line counts:
   - `wc -l data/processed/train.csv` minus 1 (header)
   - `wc -l data/processed/val.csv` minus 1
   - `wc -l data/processed/test.csv` minus 1

---

**Task N6: Verify qualitative examples against qualitative_examples_val.csv**

Source file: `results/ablations/qualitative_examples_val.csv`

For every row in `\label{tab:qualitative}` (supplementary):

1. Match by sequence prefix and verify activity, toxicity, stability,
   dev_penalty, and ΔRank values.
2. Flag any mismatch.

---

### 3.3 coherence-reviewer tasks

**Task C1: Cross-reference integrity**

1. Compile the manuscript and check for any "??" undefined references.
2. Verify every `\ref{}` and `\label{}` pair resolves correctly.
3. Verify every `\cite{}` key exists in `references.bib`.
4. Verify every bib entry is cited at least once (no ghost entries).

---

**Task C2: Number consistency across sections**

The same numbers appear in multiple sections (abstract, introduction,
results, conclusion). Verify these key numbers are identical everywhere
they appear:

- Agent improved TopK enrichment: 0.650
- Agent improved NDCG: 0.982
- Agent improved bootstrap CI: [0.533, 0.767]
- Weighted sum TopK: 0.609
- Weighted sum bootstrap CI: [0.483, 0.733]
- NSGA-II TopK: 0.444
- NSGA-II CI: [0.267, 0.617]
- Random weight search TopK: 0.611
- Cross-split agent: 0.650 ± 0.034
- Cross-split weighted: 0.585 ± 0.050
- Candidate pool size: 3,554
- Experiment count: 100
- Keep count: 12
- Companion paper experiments: 3,106

List every occurrence with file:line and value. Flag any inconsistency.

---

**Task C3: Claim-evidence alignment**

For every empirical claim in the manuscript, verify it is supported by
a table, figure, or explicit data reference:

1. "outperforming NSGA-II (0.444; non-overlapping CIs)" →
   Table 1 CIs [0.533,0.767] vs [0.267,0.617] — confirm non-overlap.
2. "consistent across 10 independent data splits" →
   Figure 6 / Table S2.
3. "12 kept improvements" → Table S1.
4. "agent independently discovered oracle consensus voting" →
   Check loop trajectory descriptions for experiment 32.
5. "keep rate of 11%" → 11 improvements out of 100 (not 12/100,
   since experiment 1 is the baseline).
6. All numbers marked "bootstrap 95% CI" use 1,000 resamples →
   check n_bootstrap column in CSV.

---

**Task C4: Figure-caption-text coherence**

For each of the 6 figures:

1. Read the figure caption.
2. Read all text that references the figure.
3. Verify the caption and text describe the same content.
4. Check that figure file exists at `manuscript/figures/fig{N}_*.pdf`.

---

### 3.4 scope-checker tasks

**Task S1: Verify claims stay within stated limitations**

Read `docs/manuscript_PRD.md` Section 2 ("What We Explicitly Do NOT Claim")
and Section 8 ("Writing Constraints"). Then read the full manuscript and flag
any sentence that:

1. Claims drug discovery breakthroughs.
2. Implies the public benchmark equals proprietary data.
3. Claims the ranking policy generalizes beyond AMPs.
4. Claims statistical significance for agent vs weighted sum on a single split.
5. Uses hype language ("revolutionary", "breakthrough", "state-of-the-art").

---

**Task S2: Verify honest limitation coverage**

The PRD lists these required limitations. Verify each is covered in the
Discussion section:

1. CIs overlap for agent vs weighted sum — ☐
2. Stability model is weak (R² = 0.547) — ☐
3. Only activity is ground truth — ☐
4. Random splitting (not cluster-aware) — ☐
5. 8.9% ToxinPred3 training overlap — ☐
6. Oracle definitions are design choices — ☐
7. Single candidate pool / organism — ☐

---

**Task S3: Verify tone matches companion paper**

Read the companion paper at https://arxiv.org/abs/2603.28015 (or its HTML
at https://arxiv.org/html/2603.28015v1). Compare writing style:

1. Are claims hedged appropriately (CIs, p-values, "proof-of-concept")?
2. Are limitations stated directly in the discussion, not buried in footnotes?
3. Is the abstract factual and free of superlatives?
4. Are comparisons stated with exact numbers and CIs?

Flag any sentences that deviate from the companion paper's tone.

---

## 4. Lead Responsibilities

After all teammates finish, the lead should:

1. **Collect** all findings from the four teammates.
2. **Deduplicate** issues found by multiple reviewers.
3. **Prioritize** by severity:
   - **Critical**: wrong numbers, missing citations, overclaiming
   - **Major**: inconsistent numbers across sections, metadata errors
   - **Minor**: style mismatches, unused bib entries
4. **Produce** a final review report as `docs/manuscript_review_report.md`
   with an actionable issue table:

```markdown
| # | Severity | Category | File:Line | Issue | Suggested fix |
|---|----------|----------|-----------|-------|---------------|
```

5. **Optionally** apply fixes if instructed (the lead should ask before
   editing manuscript files).

---

## 5. Launch Prompt

Copy-paste this into Claude Code to start the review:

```
Create an agent team with 4 teammates to review our NeurIPS manuscript
for factual accuracy and coherence. The manuscript is in manuscript/
and source data is in results/ablations/*.csv, results/loops/prompt5/results.tsv,
and data/manifests/manifest.json.

Spawn these teammates:

1. "bib-checker" — Verify every entry in manuscript/references.bib against
   real publication metadata (title, authors, year, venue, volume, pages).
   Search the web for each paper. Also check for ghost entries (in bib but
   never cited) and missing entries (cited but not in bib). Start with tasks
   B1 and B2 from docs/manuscript_review_PRD.md.

2. "number-auditor" — Cross-check every number in the manuscript .tex files
   against the source CSV/TSV/JSON data files. Use python3 for arithmetic
   verification. Start with tasks N1 through N6 from docs/manuscript_review_PRD.md.

3. "coherence-reviewer" — Check cross-reference integrity, number consistency
   across sections, claim-evidence alignment, and figure-caption-text
   coherence. Start with tasks C1 through C4 from docs/manuscript_review_PRD.md.

4. "scope-checker" — Verify all claims stay within stated limitations,
   check limitation coverage in the discussion, and compare tone against
   the companion paper (arXiv:2603.28015). Start with tasks S1 through S3
   from docs/manuscript_review_PRD.md.

Use Sonnet for all teammates to save tokens.

After all teammates finish, synthesize their findings into a single review
report at docs/manuscript_review_report.md with an actionable issue table
sorted by severity (critical > major > minor). Do NOT edit the manuscript
files — just report issues.

Detailed task specs are in docs/manuscript_review_PRD.md.
```

---

## 6. Expected Output

A single file `docs/manuscript_review_report.md` containing:

1. **Summary**: pass/fail for each review dimension.
2. **Issue table**: every finding with severity, file:line, and suggested fix.
3. **Teammate logs**: which teammate found what (for traceability).
4. **Recommendations**: prioritized list of fixes to apply.

---

## 7. Estimated Cost

- 4 teammates × ~50K tokens each ≈ 200K input tokens
- Lead synthesis ≈ 30K tokens
- Total ≈ 250K–350K tokens (roughly $2–4 at Sonnet pricing)
- Duration ≈ 10–15 minutes with parallel execution

---

## 8. Alternative: Sequential Single-Session Approach

If agent teams are unavailable or too expensive, the same tasks can be run
sequentially in a single Claude Code session using subagents:

```
Read docs/manuscript_review_PRD.md. Execute all tasks (B1-B2, N1-N6, C1-C4,
S1-S3) using subagents in parallel where possible. Produce the same review
report at docs/manuscript_review_report.md.
```

This uses fewer tokens but takes longer and loses inter-agent communication
(e.g., bib-checker can't alert coherence-reviewer about a missing citation
in real time).
