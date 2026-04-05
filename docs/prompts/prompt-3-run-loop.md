# Prompt 3: Run Loop

Use this only **after the fixed harness is working**. This prompt is for starting the actual **Karpathy-style iterative loop** with a tightly constrained editable surface.

## Recommended AWS Instance

**Best choice:** single modest GPU

- **Recommended:** `g5.xlarge`
- **Buy mode:** prefer **spot** whenever practical
- **CPU companion box (optional):** `c7i.large`
- **GPU needed?** Yes, if the loop involves repeated neural evaluations or embedding-heavy scoring

### Why
This is the first stage where speed starts to matter. The whole point of the Karpathy loop is rapid iteration. A single `g5.xlarge` is the cheapest sane GPU choice for that. Do not scale up before the loop proves value.

## Disk Hygiene Policy

This is the stage where disk gets abused if no rules exist.

- Save only **final or best** artifacts unless a checkpoint is explicitly needed
- Do **not** store one full dataset copy per run
- Keep experiment logs compact and machine-readable
- Avoid dumping large intermediate tensors or embeddings unless they are part of the actual result
- Use one explicit directory for caches and one for results
- Periodically check disk usage before launching more runs
- If space starts getting tight, prune temporary outputs before continuing

### Practical rule
The loop is supposed to optimize ranking policy, not create a graveyard of redundant artifacts. Keep the repo lean enough that many iterations remain cheap and manageable.

```text
you are continuing work in:
https://github.com/ewijaya/autoresearch-developability

before doing anything else:
1. read docs/PRD.md
2. read program.md
3. verify the fixed harness still works
4. confirm which file is the editable surface for the loop

this session is about running the loop, not redesigning the repo.

core rule:
- treat the fixed harness as frozen
- the main editable file is rank.py or policy.py
- do not casually mutate the rest of the repository

mission:
start the first autoresearch-style policy-improvement loop for peptide developability ranking.

loop structure:
1. establish baseline performance using the current ranking policy
2. make one coherent change to the ranking policy
3. run the evaluation harness
4. record metrics in results.tsv or equivalent
5. decide keep / discard / ambiguous
6. continue iterating

things you are allowed to explore in the editable file:
- weighted scalarization
- Pareto ranking strategy
- hard filters vs soft penalties
- uncertainty-aware ranking
- diversity bonus
- top-k decision logic
- tie-break logic

things you are not allowed to change unless clearly justified and explicitly logged:
- dataset definitions
- train/val/test splits
- endpoint labels
- fixed evaluation metrics
- repo architecture

requirements:
- log every experiment clearly
- keep diffs understandable
- prefer simple policies with interpretable gains
- if gains are tiny and complexity rises a lot, reject the change
- do not fake progress with overfit heuristics

minimum target for this session:
- run at least several clean loop iterations
- identify at least one keep-worthy improvement or conclude honestly that none improved
- produce a short summary of what kinds of policy changes helped or failed

report back with:
- baseline metrics
- experiment log summary
- best current policy
- top 3 most useful lessons from the loop
- whether the repo is ready for broader experiments or candidate generation

start now.
```