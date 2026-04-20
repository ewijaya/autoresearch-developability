# What this paper is about, plainly

_Purpose of this file: re-read in 6 months to remember what ground we are standing
on. If you (or a future reviewer, boss, or collaborator) start inflating the claims
beyond what appears here, trust this file over the inflation. The audit in
`AUDIT_REPORT.md` plus this plain-English version are the truth anchors for the
manuscript in `main.pdf`._

## The problem

You are running a peptide drug program. You have 3,554 candidate peptides.
For each one you have four numbers: how well it kills the bacteria (activity),
how toxic it is (toxicity), how long it survives in the body (stability), and
how easy it is to manufacture (developability). You can only afford to synthesize
and wet-lab-test about 20 of them. Which 20?

## How people do it today

They open a spreadsheet. They pick weights — "activity is 40% important,
toxicity 30%, stability 15%, manufacturing 15%" — multiply everything out,
sort, take the top 20. The weights come from gut feel. Nobody ever checks
if the weights are any good.

## The fancy academic alternative does not help

Researchers have built tools (NSGA-II) that spit out a "Pareto front" — a
spread of 200 different compromise peptides along the trade-off curve. That
is useless for triage. You do not want 200 compromises. You want the best 20.

## What this paper does

An AI agent edits the ranking code in a loop against a frozen grader:

- The data and the grading system are frozen. The AI cannot touch them.
- The AI is allowed to edit one file: the ranking code.
- It makes one change. Gets graded. If the grade goes up, keep the change.
  If it goes down, throw it away. Try again.
- Repeat 100 times.

That is the whole idea. It is basically evolution for code, with the AI as
the mutation engine and a fixed grader as the environment.

## What the AI figured out

Over 100 tries, 11 changes survived. Early on it just fiddled with the
weights (same thing a human would do). Then it got creative: it started
combining multiple scoring formulas, voting across them, and eventually
trained tiny machine-learning models to learn the right ordering. Nobody
told it to do any of this — it found the structure itself.

## The scorecard

Task: "Of the 20 peptides the policy picks, how many are actually among
the truly best?" (See next section for what "truly best" means — this is
the single most important caveat in the whole paper.)

| Method | Hit rate |
|---|---|
| Random picking | 4% |
| Pick by activity alone | 11% |
| The fancy academic method (NSGA-II) | 44% |
| The spreadsheet approach (equal weights) | 61% |
| Best of 1,000 random weight combinations | 61% |
| **The AI's policy** | **65%** |

## Is 65% vs 61% decisive? Honestly, no — but it is real

On a single data split, the AI beats the spreadsheet by 4 percentage points.
The error bars overlap. It is not statistically significant on that one split.

The stronger evidence comes from repeating the whole evaluation on 10 different
random data shuffles:

- Agent wins on **8 out of 10** shuffles.
- Loses on 2, but the losses are tiny (Δ ≤ 0.033).
- The 8 wins are much larger (mean Δ = +0.088).
- Wilcoxon signed-rank test: **p = 0.004** (one-sided).

_Earlier drafts of the paper claimed "Agent wins 10/10, sign-test p = 2⁻¹⁰ ≈ 0.001."
That claim was not supported by the raw data. The correct numbers are above.
See commits `0d46aa9` and `fix: correct cross-split significance claim`._

The bigger win is against NSGA-II: 65% vs 44%. That gap is huge and clean.
Takeaway: "spread across a frontier" is the wrong tool for "pick the top 20."

## The catch: we know the "answer" beforehand — but the "answer" is synthetic

The AI is graded against a formula, not against real wet-lab outcomes.

For each of the 3,554 peptides there are four scores (activity measured,
the other three predicted by other models/rules). The paper defines three
formulas called "oracles" that take those four scores and compute an
overall-quality score. Then:

1. Apply oracle formula → sort all 3,554 → call the top 20 the "truly best."
2. Let the policy sort the same 3,554 → take its top 20.
3. Count overlap.

That is the entire grading mechanism. The "ground truth" is what a formula
says is good. The AI is optimizing against a mathematical definition of
good, not against biological reality.

**Why do it this way?** Running 3,554 peptides through wet lab would cost
millions of dollars. So a formula is substituted and called ground truth.
This is a known compromise in computational drug discovery.

**The paper's defense.** If the AI optimized against the same formula that
grades it, it could reverse-engineer the formula. To prevent this, the paper
uses three different oracle formulas with different math (Pareto dominance
count, geometric mean of ranks, sigmoid-gated threshold) and averages the
grades. The idea: a policy can't simultaneously reverse-engineer all three,
so if it scores well on all three it is probably doing something real.

**The remaining weakness.** All three oracles are computed from the *same*
four input scores. If those scores have errors — and they do: the toxicity
model has AUC 0.92, not 1.0; the stability model (R² = 0.547) explains only
about half the variance — the oracles inherit those errors. The AI is
optimizing against a slightly wrong target. This is exactly what the paper's
"Synthetic benchmark" limitation in the Discussion says.

## What the paper does NOT claim

- **Does NOT claim** the AI finds real drugs. It ranks candidates that a
  formula says are good.
- **Does NOT claim** any of this has been validated in a wet lab.
- **Does NOT claim** this works for anything other than antimicrobial
  peptides against one bacterium. Cancer drugs, cyclic peptides,
  GLP-1 analogs — untested.
- **Does NOT claim** the AI generates new peptides. It sorts existing ones.
- **Does NOT claim** the AI is autonomous in production. It ran offline
  against a fixed candidate pool, not against live assay feedback.
- **Does NOT claim** p < 0.001. The actual test is Wilcoxon p = 0.004.

## Why anyone should care

A biotech company could swap the public DBAASP data for their own internal
peptide library, and their own in-house toxicity/stability assays, and run
the same loop. The output is a ranking policy tuned to *their* data —
replacing the gut-feel spreadsheet with something tuned by an agent, in
engineer-days of work.

## The meta-point

The whole project is a proof-of-concept that the "let an AI edit code in a
loop against a fixed grader" pattern — invented by Karpathy for neural
architecture search — works on a different kind of problem (peptide ranking).
The AI does not do biology; it does code evolution, constrained by a grader
that knows a formula-based version of biology.

## If anyone tries to inflate this — lines we do not cross

The following would cross the honesty line. If a co-author, reviewer,
investor, or press release starts saying any of these, push back:

- "The AI discovers drug candidates." No — it ranks ones we already have.
- "Statistically significant at p < 0.001." No — it is p = 0.004.
- "Agent wins on every split." No — it wins on 8 of 10.
- "Validated." No — this is a computational benchmark, not a wet-lab result.
- "Generalizes to other peptide classes." No — only AMPs against one
  organism were tested.
- "Replaces wet-lab validation." No — it reorders the queue for wet lab.
- "The benchmark measures real biology." No — it measures a formula on
  top of imperfect predicted scores.

Every one of those inflations is easier to make than to catch. Re-read
this file before agreeing to a quote, an abstract edit, or a deck slide
that touches any of these.
