# Dataset card: toy-sentiment

Synthetic teaching fixture only. It carries no research claim and is not suitable for model
comparison or publication.

## Source and license

- Hand-written generic English review-style sentences; no scraped content, people, or personal data.
- Distributed under the repository license.
- JSON Lines schema: `{"text": string, "label": "positive"|"negative"}`.
- Builder: `../build_dataset.py`; verifier: `../verify_split.py`.

## Cohort and split

The fixture contains 60 independent sentences, balanced across two labels. A fixed seed stratifies
each class into 42 train rows and 18 held-out test rows. No subject, session, or document grouping key
exists; the sentence is the record-level split unit.

The train and test files are regenerated deterministically. The model vocabulary and class statistics
are fitted later from train rows only.

## Learnability design

Every sentence contains two words from a small class-specific sentiment vocabulary. Each vocabulary
word appears across multiple independently written sentences and topics, making a small bag-of-words
pipeline reliably learnable. Shared words across splits are intentional feature vocabulary, not shared
records.

Positive and negative sentences are written independently rather than as near-identical templates with
a swapped label word. This reduces trivial cross-label pair matching while keeping the example easy to
understand.

## Leakage checklist

- [x] split unit is explicit;
- [x] source lists contain no exact duplicate record;
- [x] normalized train and test records are disjoint;
- [x] label values are restricted to the documented domain;
- [x] label text is not concatenated into model input;
- [x] vocabulary and probabilities are fitted on train only;
- [x] test labels are used only for metric calculation;
- [x] fixed-vocabulary learnability is checked without moving test records into train;
- [x] temporal and pretraining contamination are not applicable to the intended stdlib model demo.

Recompute the evidence instead of relying on stored output:

```bash
python3 examples/toy-sentiment/verify_split.py
python3 examples/toy-sentiment/run_example.py
```

The verifier prints current counts, duplicate/overlap checks, label balance, content hashes, and
vocabulary coverage. The run prints current metrics. Neither transcript is a distribution artifact.

## Limitations

- Small, single-author, English-only vocabulary.
- No neutral, mixed, negated, sarcastic, or informal examples.
- Review-style topics only; no claim of domain generalization.
- Strong lexical cues make this a plumbing check, not a realistic sentiment benchmark.

## Intended use

Use only to verify the onboarding path: deterministic split → fit on train → evaluate on held-out test
→ report current metrics. Do not cite its score as evidence of model capability.
