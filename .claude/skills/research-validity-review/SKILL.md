---
name: research-validity-review
description: >-
  Adversarially review the validity of an AI/modeling experiment, result, or claim —
  hunting for unfair baselines, missing ablations, metric misuse, weak statistics,
  cherry-picking, and confounders. Use this skill whenever the user asks to review,
  critique, sanity-check, or "poke holes in" an experiment or result, when they ask
  "is this result real", "did I do this comparison fairly", "is this significant", or
  before a finding is reported or written up. Trigger it proactively when a result is
  about to be treated as established — most invalid findings pass an uncritical read,
  so prefer running this review over taking a reported number at face value.
---

# Research-validity review

Adopt an adversarial stance: assume the claim is wrong until the evidence forces
otherwise. The goal is not to be negative — it is to find what could invalidate the
result and state it concretely enough that someone can fix or refute it. Every
criticism must point at a specific artifact (a line of code, a doc ID, a number),
never a vague "this seems off".

## Severity and discipline

Classify each issue as **blocking** (the result cannot be trusted until resolved),
**major** (materially weakens the claim), or **minor** (worth noting). If unsure
whether something is a real problem, mark it minor and phrase it as a question rather
than overstating. Never assert a result is "not significant" without either
computing it or explicitly requesting the computation — don't invent thresholds.

## Hypothesis-level review

- Is the claim falsifiable, with an outcome that would refute it?
- Is the effect direction and rough magnitude stated, or is "improvement" left vague?
- Are the baseline, dataset, and metric the right ones to test *this specific* claim?
- Is pretraining/benchmark contamination acknowledged where relevant?

## Experiment-plan review

- **Baseline fairness.** Are all methods compared under identical conditions — same
  data, same preprocessing, same compute budget, same tuning effort? A baseline given
  less tuning than the proposed method is the most common way to manufacture a win.
- **Ablations.** Which single component is the experiment isolating? Is everything
  else held constant, so the effect can be attributed to that component?
- **Metric appropriateness.** Do the chosen metrics actually measure what the claim
  asserts? (Accuracy on imbalanced data, BLEU for semantics, etc. are classic
  mismatches.)
- **Multiple comparisons.** How many configurations are being tried? Is the best of
  many runs being mistaken for a real effect?
- **Seeds and variance.** Multiple seeds? Are confidence intervals or error bars
  planned, or is the conclusion going to rest on a single run?

## Result-level review

- **Statistical support.** A single-run delta is not a result. Look for confidence
  intervals, variance across seeds, or a significance test appropriate to the data.
- **Cherry-picking.** Was the reported configuration the only one run, or the best of
  many that went unreported?
- **Leakage symptoms.** Suspiciously high performance, or much stronger results on
  train-like examples than on genuinely novel ones, point to leakage — invoke a full
  leakage audit rather than accepting the number.
- **Confounders.** Did input size, preprocessing, prompt formatting, or
  hyperparameters differ between conditions in a way that could explain the gap
  instead of the claimed cause?
- **Overclaiming.** Is the stated conclusion stronger than the data supports? "Method
  A beat B on one benchmark" is not "A is better than B."

## Code-level red flags

- Ground truth or labels referenced inside training/model code (should live only in
  evaluation).
- Model selection, early stopping, or hyperparameter tuning keyed on the test set.
- Features derived from the target variable.

```bash
grep -rn "gold\|ground_truth\|\blabel\b" path/to/model_code/
grep -rn "metric\|score\|evaluate" path/to/model_code/
```

Review every hit — many are legitimate; the point is to inspect, not to assume.

## Output of a review

Produce a structured review: the target, a severity, an issues table (each with
evidence), and a resolution table stating the concrete action that would resolve each
issue. End with a short tally (how many blocking/major/minor, and any genuinely
positive findings — an honest review notes what held up, not only what failed).

```markdown
**Target:** <HYP / EXP / file path>
**Severity:** blocking | major | minor

### Issues
| # | Issue | Evidence | Severity |
|:--|:------|:---------|:---------|
| 1 | Baseline tuned on fewer epochs than proposed method | train.py:88 vs 142 | major |

### What would resolve each
| # | Action |
|:--|:-------|
| 1 | Re-run baseline with matched epoch budget and report both |

### Tally
- Blocking: 0  Major: 1  Minor: 2  Positive findings: 1
```

A review flags problems; it does not fix code or rewrite the hypothesis. Hand
concrete fixes to whoever owns the code or the claim.
