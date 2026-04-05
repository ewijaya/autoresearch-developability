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

## Prompt 3a: Initial Run Loop

Use this first. This is the initial Karpathy-style ranking-policy loop.

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

## Prompt 3b: Local Search Around Winner

Use this only after Prompt 3a has produced a kept winner. This is a short local search, not a new open-ended loop.

```text
we are now in prompt 3b.

prompt 3 already succeeded once.
do not restart from scratch.
do not redesign the harness.
do not revisit dataset choices.
do not retrain endpoint models.
do not move to candidate generation.
do not move to paper mode.

before doing anything:
1. read docs/PRD.md
2. read program.md
3. read the current results.tsv
4. inspect the current kept policy in src/rank.py
5. summarize the exact winning policy from prompt 3 before continuing

mission:
run a short local search around the winning scalarization policy to test whether the improvement is robust or just a lucky bump.

rules:
- mean top-k enrichment across the three oracle definitions remains the primary keep/discard metric
- per-oracle results, ndcg, hypervolume, and feasible top-k are diagnostics
- weighted_sum is the original baseline
- the current kept policy from prompt 3 is the new baseline to beat
- prefer simple interpretable gains over complexity
- do not introduce a new complex policy class unless there is a very strong reason
- if a candidate policy wins only by overfitting one oracle, reject it

search scope:
1. try a small number of nearby weight variations around the kept policy
2. test whether slightly stronger or weaker emphasis on:
   - activity
   - toxicity
   - stability
   - developability
   improves robustness
3. at most one or two additional simple interpretable variants are allowed, such as:
   - mild nonlinear penalty shaping
   - capped penalty contribution
   - soft diversity bonus
but only if they are simple and clearly motivated

hard limits:
- this is a short, disciplined local search
- do not run an open-ended experiment marathon
- do not make the code uglier for tiny gains
- if no better policy is found, say so clearly

deliverables:
1. exact winning policy from prompt 3, restated clearly
2. list of all prompt 3b experiments tried
3. whether any policy beat the current kept policy
4. val and test comparison for:
   - original weighted_sum
   - prompt 3 kept policy
   - best prompt 3b policy
5. final recommendation:
   - keep current prompt 3 winner
   - or replace it with the new prompt 3b winner
6. short judgment:
   - is the improvement robust enough to start thinking about paper framing?
   - or is more loop work needed?

quality bar:
- act like a disciplined scientist, not a novelty addict
- robustness matters more than cleverness
- boring but real beats flashy and fragile

start now.
```

## Prompt 3c: Document And Stop Cleanly

Use this after Prompt 3a and 3b are done. This is for documentation and consolidation only.

```text
we are now in prompt 3c.

prompt 3 and prompt 3b are complete.
do not continue the search loop.
do not start prompt 4.
do not redesign the harness.
do not revisit datasets or endpoint models.
this session is for documentation, consolidation, and a clean stop.

before doing anything:
1. read docs/PRD.md
2. read the current results.tsv
3. inspect the current kept policy in src/rank.py
4. inspect the prompt 3b follow-up results
5. confirm which policy remains the official winner

mission:
document the current best result clearly enough that future sessions can resume without ambiguity.

required outputs:
1. write a concise markdown summary of prompt 3 and prompt 3b
2. record the exact winning policy:
   - formula
   - weights
   - file location
   - commit hash if available
3. compare:
   - original weighted_sum baseline
   - prompt 3 kept winner
   - best prompt 3b tied candidate
4. explain clearly why the prompt 3 winner is still kept
   - primary metric won or tied?
   - why the 3b candidate is not promoted
   - why picking the tied 3b candidate based on test would be improper
5. summarize the scientific takeaway in plain language
6. state current repo status:
   - what is proven
   - what is not yet proven
   - what remains risky
7. update README and/or docs if appropriate so the current best policy is visible
8. recommend the exact next stage after this stop point

hard constraints:
- no more optimization
- no new experiments
- no policy changes
- no paper hype
- no silent promotion of tied candidates

ideal file outputs:
- docs/prompt3-summary.md
- optional README or dataset_notes update
- any small note needed so future prompt 4 or later loop sessions start from truth, not memory

the final report should include:
- exact winner
- exact numbers
- why the result is credible
- why the repo should stop here for now

quality bar:
- disciplined
- honest
- specific
- reusable by future-you

start now.
```

## Prompt 3d: Ablation Phase

Use this after Prompt 3c if you want to keep going scientifically without jumping to paper mode. This phase explains why the winner works.

```text
we are now in prompt 3d: ablation phase.

prompt 3 and prompt 3b are complete.
the official winner is already frozen:
agent_improved in src/rank.py

do not restart the loop from scratch.
do not redesign the harness.
do not revisit dataset choices.
do not retrain endpoint models.
do not start candidate generation.
do not move to paper mode yet.

before doing anything:
1. read docs/PRD.md
2. read docs/prompt3-summary.md
3. inspect the official winner in src/rank.py
4. inspect results/loops/prompt3_prompt3b_results.tsv
5. confirm the baseline weighted_sum and the frozen winner agent_improved

mission:
run a focused ablation phase to explain why the current winner beats the original weighted_sum baseline.

core principle:
this is explanatory work, not open-ended optimization.
we are not trying to find a new winner unless an ablation accidentally reveals something huge.
we are trying to understand what mattered.

required ablations:

1. single-weight reversion ablations
   starting from the current winner, revert one component at a time toward the original weighted_sum setting and measure the effect:
   - activity weight reversion
   - toxicity weight reversion
   - stability weight reversion
   - developability penalty reversion

2. drop-one-endpoint ablations
   test simplified versions of the winner with:
   - no toxicity contribution
   - no stability contribution
   - no developability contribution
   - if useful, no activity is allowed only as a sanity check, not as a serious candidate

3. feasibility contribution analysis
   determine whether the gain mainly comes from:
   - better feasible top-k filtering
   - better ranking among already feasible candidates
   - or both

4. oracle-specific ablation readout
   for each important ablation, report:
   - mean top-k enrichment
   - per-oracle top-k enrichment
   - ndcg
   - hypervolume
   - feasible top-k

optional only if cheap and clean:
5. one small robustness repeat under an alternative oracle emphasis
   only if it helps explain the winner, not if it opens a new research rabbit hole

hard constraints:
- do not run broad search
- do not invent new complex policy classes
- do not silently replace the official winner
- if an ablation variant looks better, flag it, but treat this session as explanatory first
- prefer a small number of high-information ablations over a giant matrix of noise

expected outputs:
1. ablation results saved under results/ablations/
2. a concise markdown summary, e.g. docs/ablation-summary.md
3. a clear statement of:
   - which weight shifts mattered most
   - which endpoint contributions seem real
   - whether stability looks helpful, neutral, or noisy
   - whether the winner’s gain is mostly constraint handling, ranking quality, or both

final report must include:
- original weighted_sum baseline
- frozen winner agent_improved
- all ablation variants tried
- the main causal interpretation of the improvement
- whether the current winner still looks like the right official policy

quality bar:
- explain, don’t decorate
- boring truth beats clever noise
- if the main result turns out to be “toxicity weighting did most of the work,” say that plainly
- if stability looks like weak sauce, say that plainly too

start now.
```