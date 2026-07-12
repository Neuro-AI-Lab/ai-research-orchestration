---
name: research-validity-review
description: Adversarially review AI research hypotheses, plans, experiments, results, and claims for confounding, unfair baselines, leakage, metric misuse, weak statistics, cherry-picking, missing ablations, and overclaiming. Use for every critic gate and before reporting findings.
---

# Research-validity review

Assume the claim may be wrong until direct evidence survives review. Point every criticism to an entry,
artifact, line, log, or number. Classify issues as `blocking`, `major`, or `minor`; do not assert a
statistical failure without computing it or requesting the missing analysis.

Review:

- falsifiability, meaningful effect, feasibility, and contamination;
- matched data, preprocessing, compute, tuning effort, and baseline implementation;
- ablations that isolate the claimed component;
- metric alignment with the research question and class/population structure;
- selection on validation rather than test and disclosure of all tried configurations;
- seeds, paired structure, uncertainty, effect size, multiple comparisons, and failed runs;
- leakage symptoms, duplicates, target proxies, and pretraining overlap;
- alternative explanations and whether prose exceeds the actual evidence.

Write a REV containing the target, evidence inspected, issue table, resolution criteria, severity,
`**Gate:** passed | blocked`, and status. `passed` requires affirmative evidence, not merely no issue
noticed. File result-invalidating problems as VAL entries. Do not repair the work you review.

Before the root reports a result, verify its EXP data, analysis, provenance, caveats, and exact claim.
State what held up as well as what failed. A blocking issue remains blocking until new evidence resolves
it or a complete ADR explicitly records the deviation and rollback.
