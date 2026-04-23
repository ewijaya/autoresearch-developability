# Lay summaries

Non-technical summaries of the preprint *Agent-Guided Ranking Policy Improvement for Peptide Drug Candidate Prioritization* (bioRxiv, 2026), written for stakeholders who do not work in computational methods: executives, program leads, partners, and scientists outside the ML field.

Each summary below addresses one aspect of the work and can stand alone.

---

## 1. What the work is

A peptide drug program lives or dies on one question: which handful of candidates do you send to the lab?

Picking wrong costs months. Good candidates have to balance four properties at once: they need to work, be safe, stay stable, and be manufacturable. Most tools handle one at a time.

We gave an AI agent one assignment: improve the ranking recipe one change at a time, and only keep changes that pick better candidates on held-out data. It ran 100 experiments and kept 12.

The loop is Andrej Karpathy's autoresearch idea (2026): let an agent edit code against a fixed scoring system. We pointed it at peptide triage.

The result: 65% of the best candidates in the top-20 shortlist, versus 44% for the industry-standard approach. On a public benchmark of 3,554 antimicrobial peptides.

The pipeline plugs into a company's own candidate library. The paper uses public data; the code is built for proprietary programs.

---

## 2. The result, and why it surprised us

Going in, the goal was modest: build a ranking recipe that beats a hand-tuned scoring spreadsheet. Most programs use some version of that spreadsheet today.

What we didn't expect was that the AI-designed recipe would also beat the field's textbook answer.

For multi-objective problems like peptide triage, NSGA-II is the standard method taught in every optimization course. It has been the default for twenty years. On our benchmark, it correctly surfaces 44% of the best candidates in the top-20 shortlist.

The AI-designed recipe gets 65%.

This is not NSGA-II being bad. It is NSGA-II being designed for the wrong goal. The method tries to spread candidates across the whole trade-off frontier, because many problems reward diversity. But triage is not about diversity. It is about picking the 20 candidates a program will actually spend lab money on. Concentrated selection beats diverse exploration when the budget is fixed.

The lesson for anyone running a benchmark: check whether the optimizer's goal matches the decision that will actually be made with its output.

---

## 3. What the agent built on its own

The part of the project worth pausing on is what the agent did that nobody asked for.

The setup was narrow. The agent could edit a peptide ranking recipe. It could keep a change only if the change scored better on held-out data. We expected weight-tuning: adjust this coefficient, boost that feature, average a few scores differently.

That is what the first twenty experiments looked like. Then the behavior changed.

- It began voting across multiple ranking criteria instead of averaging them.
- It blended rank lists from different scoring methods using reciprocal rank fusion, a technique from search-engine research. That technique was not in the template.
- By the end of the run, it was training small machine-learning models to re-rank its own shortlist.

Of the 100 experiments the loop ran, 12 were kept. Three of those 12 were structural changes, not parameter tweaks. The agent had moved past the problem we posed and started solving the meta-problem: what kind of recipe works here at all.

This is the practical argument for Karpathy's autoresearch framing. The loop is simple. The outcomes are not, because the space of changes is as large as the space of code the agent can write.

---

## 4. What the work is and is not

Limitations matter, in plain English, before anyone asks.

**This is not a drug-discovery system.** It ranks candidates a program already has. It does not invent new peptides.

**This is not a replacement for the lab.** The output is a shortlist to synthesize and assay. It is triage, not decision.

**The benchmark is antimicrobial peptides.** Transfer to cyclic peptides, GLP-1 analogs, or oncology programs is untested. Peptide chemistry is not one field.

**The AI agent runs offline.** It does not see live assay results. It does not take actions. It proposes ranking recipes against a fixed scoring harness, and a human approves each kept change.

**The improvements are not guaranteed to transfer.** The 65% figure is on a public dataset. A proprietary library with different score distributions may behave differently, which is exactly why the pipeline was built to plug into internal data and re-learn on it.

None of this makes the result less real. It does mean the right question is not whether AI replaces medicinal chemists. The right question is whether AI can make the next 20 candidates a program sends to the lab more likely to work. That is a narrower claim and the one the paper tests.

---

## 5. For programs that want to pilot

The practical end.

For a peptide program with in-house scores for activity, toxicity, stability, and manufacturability, the pipeline described in the paper is designed to plug into internal data with a swapped data loader. Nothing about the agent, the evaluation harness, or the ranking-recipe search needs to change. Only the input table does.

What integration looks like in practice:

- One engineer, one to two weeks, to wire internal scoring into the expected input format.
- A single command to launch the agent loop against the program's data.
- A shortlist of top-20 candidates, with the policy that produced it, written to disk.

The agent runs locally. Peptide sequences never leave the program's environment. The public-data pipeline in the repository is the worked example that gets swapped out.

The author is interested in a small number of pilots with teams already running peptide triage today.

---

## References

- Preprint: https://www.biorxiv.org/content/10.64898/2026.04.19.719536
- Code: https://github.com/ewijaya/autoresearch-developability
- Prior art: Karpathy, A. *autoresearch* (2026), https://github.com/karpathy/autoresearch
