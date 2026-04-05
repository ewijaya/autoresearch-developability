# Prompt 3 Summary

This document records the final state after **Prompt 3** and **Prompt 3b**.
It is the handoff note for any future session. It is intentionally narrow:
the fixed harness, datasets, and endpoint models are assumed unchanged.

## Official Winner

The official winner remains **`agent_improved`** in
[`src/rank.py`](../src/rank.py).

- **Policy class:** same simple weighted linear scalarization as `weighted_sum`
- **Formula:**

```text
score =
  0.45 * norm(activity)
  - 0.40 * norm(toxicity)
  + 0.25 * norm(stability)
  - 0.15 * norm(dev_penalty)
```

- **Weights:**
  - activity: `0.45`
  - toxicity: `0.40`
  - stability: `0.25`
  - dev_penalty: `0.15`
- **File location:** [`src/rank.py`](../src/rank.py), strategy `agent_improved`
- **Winner first kept at commit:** `2ec8089` (see `results.tsv`)
- **Current HEAD still using same winner:** `a56cc3d`

This policy is implemented by calling `_rank_weighted_sum(...)` with the
weights above. No new policy class was introduced.

## Prompt 3 Result

Prompt 3 established a real improvement over the original `weighted_sum`
baseline on the locked primary metric: **mean top-k enrichment across the
three oracle definitions**.

### Val split, k=20

| Policy | TopK Enrichment | NDCG | Hypervolume | Feasible | Pareto | Rank Product | Threshold Gate |
|---|---:|---:|---:|---:|---:|---:|---:|
| `weighted_sum` | 0.5167 | 0.8938 | 0.5674 | 0.55 | 0.20 | 0.90 | 0.45 |
| `agent_improved` | 0.5500 | 0.9365 | 0.5640 | 0.80 | 0.30 | 0.65 | 0.70 |

Interpretation:
- The Prompt 3 winner improved the **primary metric** from `0.5167` to `0.5500`.
- The gain did **not** come from overfitting one oracle.
- The policy traded away some `rank_product` enrichment, but improved both
  `pareto_rank` and `threshold_gate`, lifting the mean and increasing
  feasible top-k from `0.55` to `0.80`.

## Prompt 3b Local Search

Prompt 3b was a short, disciplined robustness check around the Prompt 3
winner. It did **not** continue open-ended search.

### Experiments tried

One-at-a-time weight perturbations around the Prompt 3 winner:

- `p3b_more_activity`
- `p3b_less_activity`
- `p3b_more_toxicity`
- `p3b_less_toxicity`
- `p3b_more_stability`
- `p3b_less_stability`
- `p3b_more_dev`
- `p3b_less_dev`

Two simple shaped-penalty variants:

- `p3b_capped_dev`
- `p3b_tox_power_1p5`

See [`results.tsv`](../results.tsv) for exact rows.

### Prompt 3b outcome

- No Prompt 3b candidate **beat** `agent_improved` on the locked primary
  `val` metric.
- Several candidates **tied** at `0.5500`.
- The strongest tied candidate by secondary diagnostics was
  `p3b_tox_power_1p5`, but it was **not promoted**.

## Why The Prompt 3 Winner Stays Official

### Primary metric rule

The project rule is explicit: promotion requires a win on the **primary**
keep/discard metric, which is mean top-k enrichment across the oracle
ensemble on `val`.

### Best tied Prompt 3b candidate

The best Prompt 3b tied candidate was:

```text
score =
  0.45 * norm(activity)
  - 0.40 * norm(toxicity)^1.5
  + 0.25 * norm(stability)
  - 0.15 * norm(dev_penalty)
```

This candidate:

- tied the Prompt 3 winner on `val` top-k enrichment: `0.5500`
- had somewhat better secondary diagnostics
- did **not** exceed the primary metric

### Why it is not promoted

It is not promoted because:

1. A **tie** on the primary metric is not a clean win.
2. It is **more complex** than the current official winner.
3. Choosing it because of better `test` performance would be improper.

### Why promoting on test would be improper

The `test` split is for confirmation, not model selection. If a candidate
ties on `val` and is then promoted because it looks better on `test`, that
turns the held-out test set into a selection tool. That would weaken the
credibility of later claims.

## Required Comparison

### Val split, k=20

| Policy | TopK Enrichment | NDCG | Hypervolume | Feasible |
|---|---:|---:|---:|---:|
| Original `weighted_sum` | 0.5167 | 0.8938 | 0.5674 | 0.55 |
| Prompt 3 winner `agent_improved` | 0.5500 | 0.9365 | 0.5640 | 0.80 |
| Best Prompt 3b tied candidate `p3b_tox_power_1p5` | 0.5500 | 0.9402 | 0.5640 | 0.75 |

### Test split, k=20

| Policy | TopK Enrichment | NDCG | Hypervolume | Feasible |
|---|---:|---:|---:|---:|
| Original `weighted_sum` | 0.6000 | 0.9571 | 0.4965 | 0.90 |
| Prompt 3 winner `agent_improved` | 0.6333 | 0.9614 | 0.5533 | 0.85 |
| Best Prompt 3b tied candidate `p3b_tox_power_1p5` | 0.6500 | 0.9714 | 0.5533 | 0.85 |

Important: the Prompt 3b candidate looks slightly better on `test`, but it
was only a **tie** on `val`. That is not enough to justify promotion.

## Scientific Takeaway

In plain language:

- A simple reweighting of the original scalarization produced a real gain.
- The gain appears **robust locally**, not just a lucky single point.
- More elaborate policies in Prompt 3 mostly failed by over-favoring one
  oracle family.
- The current best result supports the narrow claim that the loop can
  improve multi-objective peptide ranking under a fixed public harness.

## Current Repo Status

### What is proven

- The fixed harness runs end-to-end.
- The repository contains at least one kept policy that beats the original
  `weighted_sum` baseline on the locked `val` metric.
- That same kept policy also performs better than `weighted_sum` on the
  current `test` split.
- A short local robustness check did not reveal a clearly superior nearby
  replacement.

### What is not yet proven

- That the current policy is the globally best simple scalarization.
- That the result is stable across alternative split seeds or cluster-aware
  splitting.
- That the benchmark transfer claim extends beyond this public AMP setup.
- That the loop is done exploring useful policy space.

### What remains risky

- The split is still the documented random fallback, not mmseqs2 clustering.
- Stability is still a weak learned endpoint.
- Oracle definitions remain synthetic benchmark constructs, not biological
  truth.
- The policy gain is meaningful but still modest in absolute size.

## Stop Point

The repo should stop here for now.

- **Official winner:** `agent_improved`
- **No promotion from Prompt 3b**
- **No further loop search in this session**

## Exact Next Stage

The next stage after this stop point should be:

1. preserve `agent_improved` as the official ranking policy
2. begin the next explicitly scoped phase with a fresh prompt
3. treat Prompt 4 or later evaluation/reporting work as starting from the
   facts in this document, not from memory

If another loop session happens before Prompt 4, it should start from the
official winner recorded here and require a new explicit hypothesis, not a
generic continuation of local search.
