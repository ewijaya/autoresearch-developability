# Prompt 4: Paper Mode

Use this only **after the harness works and the loop has produced real results**. This prompt is for turning the repo output into a **publishable paper-grade package**.

## Recommended AWS Instance

**Best choice:** mostly CPU, with burst GPU only for missing ablations

- **Recommended default:** `c7i.large` or `c7a.large`
- **If additional ablation runs are needed:** temporary `g5.xlarge` on spot
- **GPU needed?** Not for writing/analysis itself. Only for final missing experiments.

### Why
Paper mode is mostly analysis, figures, writing, and honesty. That should happen on cheap CPU infrastructure. Only spin up a GPU if a critical experiment is still missing.

```text
you are continuing work in:
https://github.com/ewijaya/autoresearch-developability

before starting:
1. read docs/PRD.md
2. read docs/paper_outline.md
3. review the full results produced so far
4. verify what claims are truly supported vs merely hoped for

this session is about paper mode.
that means:
- strengthen evidence
- run necessary ablations
- produce figures
- tighten claims
- write clearly

mission:
turn the current state of the repo into a paper-grade public proof of concept for autoresearch-style peptide developability triage.

required work:
1. identify the strongest supported paper claim
2. identify which weak claims should be cut
3. run the minimum necessary ablations and robustness checks
4. generate paper-quality figures and tables
5. update docs/paper_outline.md into a near-paper draft structure
6. write a concise results summary suitable for abstract/introduction reuse
7. document limitations honestly

preferred evidence types:
- baseline vs loop improvement
- multi-objective vs single-objective comparison
- robustness across splits or bootstrap samples
- uncertainty-aware analysis if available
- interpretable examples of changed rankings and why they matter

hard constraints:
- do not oversell
- do not claim drug discovery breakthroughs from public toy data
- do not bury limitations
- do not pretend the public benchmark is the same as StemRIM internal data
- do not let the paper become a generic LLM hype piece

what the paper should make obvious:
- the framework is real
- the public benchmark is a proof of concept
- the next logical step is internal proprietary peptide data
- the multi-objective framing is more realistic than one-endpoint peptide modeling

deliverables for this session:
- recommended title options
- strongest abstract claim
- figure list
- table list
- limitations list
- required final experiments
- updated paper outline or draft sections

report back with brutal honesty.
if the results are not paper-worthy yet, say so and specify exactly what is missing.
```