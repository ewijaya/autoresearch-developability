# Prompt 2: Implement Harness

Use this only **after Prompt 1 is done and reviewed**. This prompt is for building the **fixed evaluation harness** and making one complete end-to-end dry run possible.

## Recommended AWS Instance

**Best choice:** CPU first, GPU optional only if a real bottleneck appears

- **Recommended default:** `c7i.large` or `c7a.large`
- **If preprocessing or small model fitting starts dragging:** temporary `g5.xlarge` on spot
- **GPU needed?** Usually no for the first harness pass

### Why
The main risk in this phase is not compute starvation. It is building a bad harness. Correctness matters more than speed. Stay on CPU unless a concrete training bottleneck appears.

```text
you are continuing work in:
https://github.com/ewijaya/autoresearch-developability

before doing anything else:
1. read docs/PRD.md again
2. read the outputs from the kickoff session
3. confirm the agreed repo scaffold and dataset plan

this session is not for broad planning. this session is for implementation.

your mission:
build the first fixed harness so the repo can run end to end on a small public benchmark.

scope for this session:
1. implement the fixed harness files:
   - src/prepare.py
   - src/evaluate.py
   - src/endpoint_activity.py
   - src/endpoint_toxicity.py
   - src/endpoint_stability.py
   - src/endpoint_dev.py
2. make the public dataset ingestion real
3. define strict train/val/test split logic with leakage protection
4. implement the initial baseline ranking policies
5. make one end-to-end dry run possible
6. create a machine-readable results/logging format
7. add minimal tests or smoke checks

requirements:
- keep the harness fixed and legible
- keep the design simple enough that a future agent can trust it
- prefer one coherent public benchmark bundle over too many half-broken datasets
- if activity data is messy, choose the cleanest practical public subset and document the compromise clearly
- document every assumption in docs/dataset_notes.md

hard constraints:
- do not build a giant framework
- do not add multi-agent orchestration
- do not start the autoresearch loop yet
- do not make rank.py the center of this session unless needed for dry run
- do not optimize for speed before correctness

expected output by end of session:
- one reproducible command or script that runs the harness end to end
- baseline outputs for at least one toy or real benchmark split
- clear logging format
- updated README with how to run the harness
- updated docs with remaining risks and gaps

report back with:
- files created or changed
- exact command to run the harness
- what works
- what is still weak or placeholder
- whether the repo is ready for Prompt 3

start now and bias toward getting one complete dry run working.
```