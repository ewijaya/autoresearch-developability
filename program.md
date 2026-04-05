# Program: autoresearch-developability

This project is inspired by and structurally derived from Karpathy's
[autoresearch](https://github.com/karpathy/autoresearch). It reuses the
domain-adaptation lessons from
[autoresearch-mol](https://github.com/ewijaya/autoresearch-mol).

## Research question

Can an autoresearch-style loop improve peptide candidate ranking under
multiple developability constraints using entirely public data?

## Architecture

```
Fixed harness (do not modify):
  src/prepare.py           – data loading, splits, leakage checks
  src/evaluate.py          – ranking metrics (NDCG, top-k enrichment, hypervolume)
  src/endpoint_activity.py – activity scoring
  src/endpoint_toxicity.py – toxicity scoring
  src/endpoint_stability.py – stability scoring
  src/endpoint_dev.py      – manufacturability / developability proxies

Editable surface (agent modifies this):
  src/rank.py              – ranking policy
```

## Operating rules

1. Read `docs/PRD.md` before making any changes.
2. Treat every file except `src/rank.py` as frozen unless explicitly
   instructed otherwise by the human operator.
3. Make **one coherent ranking-policy change** per iteration.
4. Run the evaluation harness: `python -m src.evaluate`
5. Append the result to `results.tsv`.
6. **Keep** if the summary ranking metric improves.
7. **Discard** (revert) if it regresses or breaks interpretability.
8. Prefer simple, interpretable policies over complex ones.
9. Never fake progress with overfit heuristics.

## What you may change in rank.py

- Scalarization strategy and objective weights
- Pareto ranking logic
- Lexicographic filtering thresholds
- Hard constraint filters vs soft penalty functions
- Uncertainty-aware ranking (if endpoint models expose uncertainty)
- Diversity bonus or redundancy penalty
- Top-k selection and tie-break logic

## What you may NOT change without explicit justification

- Dataset definitions or train/val/test splits
- Endpoint label assignments
- Fixed evaluation metrics
- Repository structure

## Experiment logging

Every iteration must produce one row in `results.tsv`:

```tsv
commit	summary_metric	topk_enrichment	hypervolume	ndcg	status	description
```

Status values: `keep`, `discard`, `crash`, `ambiguous`.

Description: one sentence saying exactly what changed in the ranking policy.

## Baselines

The following baselines must exist before the loop starts:

1. **activity-only** – rank by predicted activity alone
2. **toxicity-exclusion** – exclude toxic, rank remainder by activity
3. **weighted-sum** – fixed equal-weight linear combination
4. **random** – random ranking among non-excluded candidates
5. **rule-only** – handcrafted heuristic rules (no ML)
6. **agent-improved** – the autoresearch loop output

## Evaluation metrics

**Keep/discard metric hierarchy (LOCKED):**
1. **top-k enrichment** — primary summary metric for keep/discard decisions
2. **NDCG** — secondary; reported but not the first-line decision target
3. **hypervolume** — diagnostic only; useful for understanding trade-offs,
   not for keep/discard gating

Other reported metrics:
- fraction of top-k satisfying all hard constraints
- diversity among top-k (sequence distance)
- Spearman/Kendall rank correlation where reference rankings exist
- bootstrap robustness (std across resampled splits)

## Iteration budget

Each ranking policy evaluation should complete in seconds, not minutes.
The constraint is policy quality, not compute. Aim for 20-50 iterations
in a single loop session.

## Success criteria

The loop is successful if at least one agent-edited policy demonstrably
outperforms the best static baseline on the primary metrics. If no
improvement is found, document that honestly — a negative result with
clean methodology is still valuable.
