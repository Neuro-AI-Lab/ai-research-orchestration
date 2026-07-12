---
name: experiment-analysis
description: Analyze AI/ML experiment results with design-aware statistics, effect sizes, uncertainty, paired comparisons, multiple-comparison control, sensitivity checks, practical significance, and calibrated claims. Use after raw EXP results and for critic result gates.
---

# Experiment analysis

Start from the locked HYP, analysis plan, EXP manifests, raw metrics, and failed-run record. Verify that
the analysis unit matches the split/randomization unit and that paired observations remain paired.

1. Account for all planned and attempted runs; explain missing or excluded runs.
2. Report per-run values and distributions before aggregate summaries.
3. Use estimands and tests appropriate to the design, scale, dependencies, and sample size.
4. Report effect sizes and uncertainty intervals, not p-values alone.
5. Correct or explicitly scope multiple comparisons and post-hoc exploration.
6. Compare against matched baselines and the predeclared meaningful-effect threshold.
7. Run sensitivity checks for seeds, outliers, split choices, tuning budget, and metric variants.
8. Separate confirmatory analysis from exploratory observations.

Do not infer independence from repeated rows, treat test examples as independent when grouped, or call
a non-significant result equivalence without an equivalence design. Avoid choosing a test merely because
it gives a favorable answer. Record assumptions and diagnostics.

Return observation, quantitative uncertainty, practical interpretation, threats to validity, and which
claim strengths are supported. If raw artifacts or design metadata are missing, block the result gate
instead of reconstructing them from prose.
