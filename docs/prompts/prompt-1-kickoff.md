# Prompt 1: Kickoff

Use this to start the project correctly. This prompt is for **orientation, repo scaffolding, and disciplined setup**. It is **not** for full implementation.

```text
you are working in the repo:
https://github.com/ewijaya/autoresearch-developability

start by reading:
1. docs/PRD.md
2. https://github.com/karpathy/autoresearch
3. https://github.com/ewijaya/autoresearch-mol

your job in this session is to kick off the repo seriously and create the foundation for execution.

core instructions:
- follow docs/PRD.md as the source of truth
- explicitly use karpathy/autoresearch as the conceptual template
- explicitly use autoresearch-mol as the style and execution reference
- keep the repo small, sharp, and legible
- optimize for a publishable public-data proof of concept
- optimize for obvious future portability to StemRIM internal peptide data
- do not overengineer
- do not build a giant multi-agent platform
- do not attempt full PRD execution in this session

important operating rules:
- the fixed harness comes first
- keep one main editable file in the loop
- prefer a constrained autoresearch loop around ranking policy, not unrestricted repo mutation
- every major choice must answer: does this help prove that autoresearch improves peptide developability triage on public data?

mission for this session:
1. read and summarize the PRD in your own words
2. inspect karpathy/autoresearch and extract the exact structural elements we should preserve
3. inspect autoresearch-mol and extract the exact domain-adaptation lessons we should reuse
4. propose the minimal v1 repo scaffold
5. create or improve these files:
   - README.md
   - program.md
   - docs/dataset_notes.md
   - docs/paper_outline.md
   - src/__init__.py if useful
6. define the initial public dataset bundle for:
   - activity
   - toxicity
   - stability
   - developability proxies
7. define the initial baseline ranking policies
8. list all unresolved decisions and risks

hard constraints:
- do not implement the full harness yet unless it is trivial
- do not start running large experiments
- do not add unnecessary dependencies
- do not invent proprietary data assumptions

deliverables:
- concise PRD summary
- architecture summary comparing autoresearch vs autoresearch-mol vs this repo
- proposed repo scaffold
- initial dataset plan
- baseline plan
- created files
- exact next 5 steps

quality bar:
- think like a serious computational drug discovery researcher
- think like a practical engineer
- think like someone trying to impress a biotech boss with public-data work
- clarity over hype
- decisions over options
- no hand-wavy slop

start now.
```