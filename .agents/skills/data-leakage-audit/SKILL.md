---
name: data-leakage-audit
description: Audit AI/ML datasets, splits, preprocessing, feature engineering, training, and evaluation code for train/test contamination and target leakage. Use for every split release, cross-validation design, suspicious result, data QA, and critic integrity review.
---

# Data leakage audit

Treat a split as untrusted until every applicable check has recorded evidence:

1. Split by the true independence unit (subject, patient, user, document, session, site, or time).
2. Prove group-key intersections across splits are empty.
3. Hash canonical content and inspect exact and near duplicates across splits.
4. Enforce temporal causality: every feature is available before the target time.
5. Reject target-derived fields, post-outcome proxies, and label-dependent selection.
6. Fit scalers, imputers, vocabularies, feature selection, target encoding, augmentation, and resampling
   on training data only, inside each cross-validation fold.
7. Use validation for tuning and touch the test set only for the final locked evaluation.
8. Assess foundation-model pretraining and public-benchmark contamination; record uncertainty.

Inspect code paths rather than trusting documentation. Trace split creation through preprocessing,
training, checkpoint selection, and evaluation. Verify hashes/counts with an executable check and record
the command/output source.

A released DATASET entry states provenance, license, hash/version, population, exclusion criteria,
split method and unit, counts, preprocessing fit boundaries, duplicate checks, contamination limits,
and `**Leakage audit:** passed | blocked`. Use `passed` only when all applicable checks have evidence.

When leakage is found, stop downstream runs, identify every affected EXP, file BUG/VAL entries, and
require corrected re-runs. Never silently fix the split while retaining invalid numbers. Also verify
sensitive data, raw records, credentials, and outputs are excluded from version control and logs.
