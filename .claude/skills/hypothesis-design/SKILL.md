---
name: hypothesis-design
description: >-
  Formulate rigorous, falsifiable research hypotheses for AI and modeling work, and
  pressure-test ideas before any code is written. Use this skill whenever the user is
  proposing a research idea, planning what to investigate, designing a study, or
  asking "would this experiment show X", "what should I test", "is this a good
  research question", or "help me frame this hypothesis". Trigger it early — a vague
  or unfalsifiable hypothesis wastes the entire experiment that follows it, so prefer
  applying this discipline over accepting a loosely-stated idea at face value.
---

# Hypothesis design

A hypothesis that cannot be refuted by any observation is not a research
hypothesis — it is a hope. The job here is to turn an idea into a single,
falsifiable claim with an explicit prediction, named conditions, and a stated
observation that would prove it wrong. Doing this *before* implementation prevents
running experiments that cannot answer anything.

## The form of a good hypothesis

Write each hypothesis as three sentences plus a conditions table:

```markdown
**Claim:** <one falsifiable sentence: a named method, on a named dataset,
            measured by a named metric, produces a stated effect in a stated direction>
**Prediction:** <what should be observed if the claim is true, quantified where possible>
**Falsifier:** <the specific observation that would refute the claim>

| Requirement       | Details                                          |
|:------------------|:-------------------------------------------------|
| Data              | dataset, splits, sample size                     |
| Baselines         | named methods/models, with citations or model IDs|
| Metrics           | named, with definitions                          |
| Effect direction  | which way, and roughly how much would matter     |
| Contamination risk| pretraining/benchmark overlap assessment         |
```

Vague verbs like "improves", "is better", or "works well" are red flags — better
than what, measured how, by how much to matter?

## Quality checklist — apply before committing to a hypothesis

- [ ] **Falsifiable.** There exists a concrete outcome that would refute it.
- [ ] **Specific.** Names a model/method, a dataset, a metric, and an effect direction.
- [ ] **Effect size considered.** States roughly what magnitude would count as
      meaningful, so a tiny-but-significant blip is not oversold.
- [ ] **Novel within the project.** Not a duplicate of an idea already on the table.
- [ ] **Feasible.** Data and compute are within reach; if not, that is flagged now.
- [ ] **Grounded.** At least one piece of prior work motivates it.
- [ ] **Contamination assessed.** Benchmark/pretraining overlap is noted where it applies.

If a box fails, refine the hypothesis before proceeding — do not write it down as-is.

## Grounding in prior work

A hypothesis should be motivated by, and check itself against, existing literature.
When citing prior work to support an idea:

- **Never invent citations.** Every claimed author, number, or result needs a
  verifiable source. If you cannot verify it, mark it `UNVERIFIED` and do not lean on
  it as a foundation.
- **Distinguish "the paper claims X" from "X is true."** Attribute, don't assert.
- **Quote sparingly** (a short phrase, not abstracts or blocks) and paraphrase the rest.
- **Flag the basis** — if you have only read an abstract or a search snippet, say so
  rather than implying you read the full method.
- When literature is sparse or contradictory, say so plainly instead of papering
  over the uncertainty with confident prose.

## Naming baselines precisely

When the hypothesis names a baseline, name the *canonical* implementation or model
identifier (e.g. a specific HuggingFace model ID, a paper's released code), so
whoever implements it does not silently substitute a different or weaker version. An
unfair or mismatched baseline invalidates the comparison before it starts.

## Designing the test alongside the claim

A hypothesis is only complete when you can state the experiment that would test it:
which conditions are compared, what is held constant, and what result maps to
"supported" versus "refuted". If you cannot describe that experiment, the claim is
still too vague — return to the form above and sharpen it.
