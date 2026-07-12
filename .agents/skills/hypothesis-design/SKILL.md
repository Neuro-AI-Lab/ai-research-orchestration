---
name: hypothesis-design
description: Design falsifiable AI research hypotheses with explicit predictions, falsifiers, baselines, metrics, meaningful effect sizes, feasibility, and contamination risks. Use for research questions, method design, study planning, and pre-implementation hypothesis pressure-testing.
---

# Hypothesis design

Turn each idea into a claim that evidence can refute before implementation begins.

```markdown
**Claim:** named method on named data changes a named metric in a stated direction.
**Prediction:** expected observation, quantified when defensible.
**Falsifier:** exact observation that would refute the claim.

| Requirement | Details |
|---|---|
| Data and split unit | source, population, train/validation/test unit |
| Baselines | canonical implementation/model IDs and matched budget |
| Metrics | definitions, primary metric, failure/safety metrics |
| Meaningful effect | practical threshold, not only significance |
| Resources | compute, time, licenses, access assumptions |
| Contamination | benchmark/pretraining/duplicate overlap risk |
```

Before writing HYP, verify that it is falsifiable, specific, feasible, grounded in fetched primary
sources, novel relative to current Codex state, and testable with a fair comparison. Attribute paper
claims to their sources; mark abstract-only evidence and unknown contamination explicitly. Never invent
a citation or substitute a weaker baseline silently.

Design the test with the claim: name conditions, controlled variables, sample unit, seeds, uncertainty
plan, and which outcomes mean supported, refuted, or inconclusive. If no experiment can distinguish
those outcomes, refine the hypothesis instead of proceeding.
