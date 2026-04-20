# Companion Paper Citation Audit

**Task:** #5 — Audit `wijaya2026autonomousagentdiscoversmolecular` (arXiv:2603.28015)
**Auditor:** companion-paper-check
**Date:** 2026-04-20

## 1. arXiv ID Verification

| Field | Value |
|---|---|
| arXiv ID | 2603.28015 |
| ID format sanity | Valid. YYMM.NNNNN = March 2026; today is 2026-04-20, so the ID is in the past. |
| URL | https://arxiv.org/abs/2603.28015 |
| Resolves? | Yes — page returns paper metadata, not 404. |
| Title (fetched) | "What an Autonomous Agent Discovers About Molecular Transformer Design: Does It Transfer?" |
| Title (bib) | "What an Autonomous Agent Discovers About Molecular Transformer Design: Does It Transfer?" |
| Author (fetched) | Edward Wijaya |
| Author (bib) | Edward Wijaya |
| Submission date | 2026-03-30 |
| Primary class (bib) | cs.AI |

**Status:** arXiv ID, title, and authorship all check out. The bib entry at `manuscript/references.bib:3` is consistent with the live arXiv record.

**Abstract summary (from arXiv):** Autonomous architecture search across SMILES, protein, and English text sequences, >3,100 experiments. Findings: for SMILES, hyperparameter tuning outperforms architecture search; for natural language, architectural modifications drive most gains. Despite distinct per-domain architectures, "every innovation transfers across all three domains with <1% degradation," suggesting differences stem from search methodology, not domain-specific requirements.

## 2. Citation Sites — Claim vs. Companion Paper

| File | Line | Surrounding claim (paraphrased) | Verdict |
|---|---|---|---|
| `manuscript/sections/introduction.tex` | 14 | "applied this paradigm to molecular transformer architecture search across SMILES, protein, and NLP domains, running 3,106 experiments and finding that the value of architecture search is domain-dependent." | **Supported.** Matches abstract (three domains, >3,100 runs, domain-dependent value of NAS). |
| `manuscript/sections/related_work.tex` | 20 | Same phrasing as introduction: cross-domain NAS, 3,106 experiments, "value of architecture search is domain-dependent." | **Supported.** |
| `manuscript/sections/methodology.tex` | 96 | "previously applied this paradigm to molecular transformer architecture search across SMILES, protein, and NLP domains (3,106 experiments)." | **Supported.** Descriptive only, no overreach. |
| `manuscript/sections/discussion.tex` | 14 | "full agent outperformed random NAS on SMILES architecture search." | **Partially supported / needs verification.** The public abstract explicitly says that for SMILES, *simple hyperparameter tuning outperforms architecture search* — i.e., architecture search does not help much on SMILES. The claim that the "full agent outperformed random NAS on SMILES" is a narrower, internal comparison (agent vs. random NAS, both within the NAS setting) that is plausible but *not explicitly visible in the abstract*. Recommend the lead verify this against the companion paper's SMILES results section; if the agent-vs-random-NAS comparison is in the paper, the citation stands; if not, soften to protein/NLP where the agent's advantage is clearer. |

**Overall:** No hallucinated claims. Three of four cites are clean; the discussion cite is the only one to double-check against the companion paper's body (not just abstract).

## 3. Double-Blind Flag (NeurIPS 2026)

**ACTION ITEM FOR LEAD — flagged, not fixed (read-only scope).**

- Companion paper author (arXiv + bib): **Edward Wijaya**.
- Current manuscript `main.tex` author block (lines 13–16): `Edward Wijaya`, `wijaya@stemrim.com`. Line 10 has `% \author{Anonymous}` commented out — preprint mode is active.
- The citations to the companion paper use first-person possessive: "Our companion paper" (introduction.tex:14, methodology.tex:96, related_work.tex:20, discussion.tex:14).

**Double-blind risk:** For NeurIPS 2026 submission, the author block must be anonymized *and* the "Our companion paper" phrasing must be rewritten to third-person (e.g., "Prior work by \citet{wijaya2026...}" or "A concurrent arXiv preprint \citep{wijaya2026...}"). Leaving "Our companion paper" in a double-blind submission is a direct de-anonymization vector because the cited arXiv is single-authored by Edward Wijaya.

The bib entry itself (named author) is acceptable — reviewers can see bib entries. The problem is only the self-attribution ("our") in prose plus the uncommented author block.

**Do not change anything now** — the manuscript appears to be in preprint mode. But before NeurIPS submission: (a) switch author to `\author{Anonymous}`, and (b) rewrite the four "Our companion paper" phrases.

## 4. Severity-Sorted Findings

1. **[MEDIUM — pre-submission blocker]** Double-blind hazard: four "Our companion paper" self-references plus named author block. Fine for preprint; must be fixed before NeurIPS 2026 double-blind submission. Sites: introduction.tex:14, methodology.tex:96, related_work.tex:20, discussion.tex:14; author block at main.tex:13–16.
2. **[LOW — factual check]** `discussion.tex:14` claims "full agent outperformed random NAS on SMILES architecture search." Not explicitly visible in the public abstract (which emphasizes that on SMILES, hyperparameter tuning beats NAS overall). Likely supported by the paper body, but the lead should confirm before final submission; if only true for protein/NLP, narrow the claim.
3. **[NONE]** arXiv ID, title, authorship, year, and three of four citation claims are accurate. No fabrication detected.
