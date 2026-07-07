---
name: data-leakage-audit
description: >-
  Audit datasets, splits, preprocessing pipelines, and model/evaluation code for
  data leakage and train/test contamination in AI and modeling research. Use this
  skill whenever the work involves defining train/val/test splits, preprocessing or
  feature engineering, building an evaluation, or whenever a result looks
  suspiciously good. Trigger it even when the user only says things like "split this
  data", "is my evaluation fair", "why is my accuracy so high", "set up
  cross-validation", "preprocess these features", or "check my pipeline" — leakage is
  the single most common cause of invalid ML results and is easy to miss, so prefer
  running this audit over assuming the setup is clean.
---

# Data leakage audit

Leakage is when information that would not be available at prediction time, or
information from the evaluation set, influences training or model selection. It
produces inflated, irreproducible results that collapse on truly held-out data. It
is the most common silent failure in modeling research. Treat any split or pipeline
as guilty until the checklist below clears it.

## When to apply this

Apply the relevant checklist before declaring a split "done", before trusting an
evaluation, and immediately whenever a metric looks too good (near-perfect scores,
or train-like examples scoring far higher than novel ones). These are leakage
symptoms, not cause for celebration.

## The split-integrity checklist

Run every item. Record the result. If any item cannot be checked off, the split is
not releasable — fix it or flag it explicitly rather than proceeding.

1. **Group-level splits.** If records share a group key (subject ID, patient,
   session, document, user), the same group must never appear in two splits.
   Splitting by row when rows are grouped leaks group identity. Verify by intersecting
   the group keys of each split — the intersection must be empty.
2. **No record overlap.** No exact or near-duplicate record appears in more than one
   split. Verify by hashing canonical record content (not just an index) and checking
   for collisions across splits. Near-duplicates (augmentations, reposts, minor edits)
   count.
3. **Temporal integrity.** If the task is predictive over time, every feature used as
   input must be observable strictly before the prediction target's timestamp. No
   future information — including future-derived aggregates — may enter a feature.
4. **No target leakage in features.** No feature is a proxy for, derived from, or
   computed using the label. Common culprits: an ID assigned after the outcome, a
   field populated only for positive cases, post-outcome timestamps.
5. **Statistics fit on train only.** Every normalizer, scaler, vocabulary, imputation
   value, target encoder, or feature-selection step is fit on the training split and
   then *applied* to val/test. Fitting on the full dataset before splitting leaks
   test distribution into training. This is the most common pipeline bug.
6. **Pretraining contamination.** For models pretrained on large corpora (LLMs,
   foundation models), check whether the evaluation set overlaps with known
   pretraining data. If the benchmark is public and old, assume overlap until shown
   otherwise; document it even when you cannot fully rule it out.

Record the outcome in the dataset's documentation, e.g.:

```markdown
### Leakage checklist
- [x] Group-level splits: split by `patient_id`; train∩test groups = 0
- [x] No record overlap: SHA256 of content, 0 collisions across splits
- [x] Temporal integrity: features use events < target timestamp (verified in pipeline)
- [x] No target leakage: reviewed all 14 features; none derived from label
- [x] Statistics from train only: scaler/vocab fit on train fold inside CV loop
- [ ] Pretraining contamination: benchmark is public (2019); overlap UNVERIFIED — flagged
```

## Code-level audit

Leakage hides in code even when the split design is correct. Grep is a starting
point, not a verdict — review every hit, since many matches are legitimate.

```bash
# Ground truth / labels referenced inside model or training code (should live in evaluation/)
grep -rn "gold\|ground_truth\|\blabel\b\|\by_true\b" path/to/model_code/

# Evaluation metrics computed inside model code (selection on the metric = leakage)
grep -rn "accuracy\|f1\|\bauc\b\|\bscore\b\|evaluate" path/to/model_code/

# Test or val split touched during training or model selection
grep -rn "test\b\|\bval\b\|holdout" path/to/model_code/
```

What to look for in the hits:
- A scaler/encoder/vocabulary `.fit()` called on data that includes val or test.
- Model selection, early stopping, or hyperparameter choice keyed on the **test**
  set (validation is fine for selection; test must be touched once, at the end).
- The evaluation comparing predictions to ground truth — never ground truth to
  itself, and never feeding the label in as a feature.
- Feature code that reads a column derived from the outcome.

## Cross-validation specifics

The same discipline applies *inside each fold*: preprocessing must be fit on the
fold's training portion only, refit per fold. Pre-splitting feature selection, SMOTE
or other resampling applied before the split, and global normalization are the
classic CV leakage bugs. Grouped or time-series data needs grouped/blocked CV, not
plain k-fold.

## When you find leakage mid-project

Stop. Identify every downstream result that used the leaky split or code path —
those results are now invalid and must be marked and re-run, not quietly kept.
Document which experiments are affected. Fixing the split silently and keeping old
numbers is itself a research-integrity failure.

## Data protection (adjacent concern)

While auditing pipelines, also confirm raw and sensitive data is gitignored, no
records with sensitive fields are printed or logged in full, and no credentials sit
in tracked files. Leakage of data *out of the repo* is a different failure than
train/test leakage, but the audit is a natural moment to catch both.
