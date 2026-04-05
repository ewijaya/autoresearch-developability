# Dataset Notes

## Design principle

Choose the **smallest coherent bundle** of public datasets that lets us
demonstrate multi-objective peptide ranking. Biological perfection is not
the goal; a stable, reproducible benchmark for the framework is.

---

## Endpoint 1: Activity (antimicrobial peptides)

### Primary source: DBAASP v4

- **URL:** https://dbaasp.org
- **What:** Database of antimicrobial peptides with MIC values against
  multiple organisms
- **Why this one:** largest curated public AMP dataset with quantitative
  activity values (not just binary labels), well-cited, downloadable
- **Target column:** MIC (μg/mL) against a reference organism
  (e.g., *E. coli* ATCC 25922 or *S. aureus* ATCC 25923)
- **Preprocessing:** log-transform MIC, filter to peptides with
  length 5-50 residues, remove duplicates by canonical sequence
- **Fallback:** APD3 (smaller, binary labels only) or DRAMP

### Alternative: SATPDB / starPepDB

- Broader activity types but noisier; prefer DBAASP for v1

### Decision: use DBAASP with one reference organism for v1

Pick a single organism with the most data points to maximize statistical
power. Document the organism choice explicitly.

---

## Endpoint 2: Toxicity

### Primary source: ToxinPred3 dataset

- **URL:** https://webs.iiitd.edu.in/raghava/toxinpred3/
- **What:** Binary toxicity labels for peptides (toxic / non-toxic)
- **Why this one:** well-curated, used in multiple published benchmarks,
  downloadable training set
- **Preprocessing:** binary label, align sequences to canonical form

### Secondary source: DBAASP hemolysis subset

- **What:** hemolytic activity (HC50) values for a subset of AMPs
- **Why useful:** hemolysis is a direct developability-relevant toxicity
  proxy — a hemolytic peptide is not a drug candidate
- **Preprocessing:** log-transform HC50, threshold for binary toxic/safe

### Decision: use ToxinPred3 as primary toxicity endpoint

Hemolysis data from DBAASP can augment if peptide overlap is sufficient.
Check overlap during data preparation; document coverage.

---

## Endpoint 3: Stability

### Primary source: HLP (Half-Life Prediction) dataset

- **What:** Peptide half-life in different biological environments
  (serum, kidney, intestine, plasma)
- **URL:** https://webs.iiitd.edu.in/raghava/hlp/
- **Why this one:** directly relevant stability proxy, public,
  quantitative values
- **Preprocessing:** log-transform half-life, focus on one environment
  (plasma or serum) for v1

### Alternative: PeptideCutter / protease cleavage data

- **What:** known protease cleavage sites
- **Use:** as a rule-based stability penalty (more cleavage sites → less
  stable), not as a standalone endpoint
- **Why alternative:** cleavage data is rule-based, not empirical
  half-life, but useful as a developability proxy

### Decision: use HLP plasma half-life as primary stability endpoint

Supplement with rule-based protease susceptibility count as a feature
in the developability endpoint.

---

## Endpoint 4: Developability / Manufacturability Proxies

No single public dataset captures "developability." Instead, compute
rule-based proxy scores from sequence properties:

### Features to compute:

| Feature | Rationale | Scoring |
|---|---|---|
| Sequence length | Very short or very long peptides are harder to develop | Penalty outside 8-40 residues |
| Aggregation-prone motifs | Hydrophobic stretches cause aggregation | Count of 3+ consecutive hydrophobic residues |
| Difficult synthesis motifs | Consecutive prolines, D-amino acid positions | Penalty for known difficult motifs |
| Net charge extremes | Extreme charge reduces solubility | Penalty for |charge| > 5 |
| Hydrophobicity extremes | Very hydrophobic peptides are insoluble | Penalty for mean hydrophobicity > threshold |
| Cysteine count | Disulfide complexity | Penalty for > 2 cysteines in short peptides |
| Unusual residues | Selenocysteine, non-standard amino acids | Binary flag |

### Scoring approach

Compute a composite developability penalty (sum of weighted rule
violations). Higher penalty = worse developability.

These rules are explicit, documented, and deterministic. No ML model
is needed for this endpoint in v1. This is acceptable and honest for
a proof-of-concept.

### Decision: rule-based developability scoring for v1

This is the right trade-off. It keeps the harness simple and
reproducible. A learned developability model can replace it later
if warranted.

---

## Dataset integration plan

### The bundle

For each peptide in the evaluation set, we need scores for all four
endpoints. There are two approaches:

**Approach A: Overlapping peptides only**
- Intersect datasets by canonical sequence
- Pro: every peptide has real labels for all endpoints
- Con: small intersection (likely < 500 peptides)
- Risk: too small for meaningful ranking evaluation

**Approach B: Separate endpoint models, unified candidate set**
- Train/obtain a predictor for each endpoint on its native dataset
- Apply all predictors to a shared candidate pool (e.g., all DBAASP peptides)
- Pro: large candidate set, all peptides get scores for all endpoints
- Con: predicted scores, not ground truth, for some endpoints
- This is what the PRD recommends

### Decision: Approach B for v1

Use DBAASP peptides as the candidate pool. Train or use published
models/rules for toxicity, stability, and developability scoring.
Activity comes from DBAASP ground truth. This gives us a large enough
ranking problem to be meaningful.

---

## Split strategy

- **Train:** 70% — used for fitting any endpoint models
- **Val:** 15% — used for ranking policy development (the autoresearch loop
  evaluates on this)
- **Test:** 15% — held out, used only for final paper results

### Leakage controls

- Split by **peptide sequence** (not by data row)
- Remove near-duplicates: peptides with > 90% sequence identity should
  be in the same split (cluster-based splitting via cd-hit or mmseqs2)
- Document the clustering threshold and method

---

## Data size estimates

| Source | Expected peptides | Expected usable after filtering |
|---|---|---|
| DBAASP v4 (full) | ~20,000+ | ~5,000-10,000 (with MIC for reference organism) |
| ToxinPred3 train | ~10,000 | ~8,000 |
| HLP | ~1,000-2,000 | ~800-1,500 |
| Developability | Computed for all | All candidates |

The candidate pool for ranking will be the DBAASP subset with valid
activity labels. Other endpoints are predicted or computed for all
candidates.

---

## Known risks

1. **HLP dataset is small** — stability predictions will have high
   uncertainty. Document this. Consider using stability as a soft
   signal, not a hard filter.
2. **Endpoint model quality varies** — toxicity and stability models
   trained on different peptide populations than the AMP candidate
   pool. Cross-domain prediction quality is uncertain.
3. **No true multi-objective ground truth** — there is no public dataset
   where peptides are labeled for all four endpoints. We construct a
   synthetic benchmark. The paper must be honest about this.
4. **Activity is indication-specific** — AMP activity may not transfer
   to other peptide modalities. Frame the benchmark as a proof-of-concept
   for the framework, not a universal peptide ranker.
