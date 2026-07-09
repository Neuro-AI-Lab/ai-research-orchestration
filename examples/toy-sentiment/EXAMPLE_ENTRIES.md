# examples/toy-sentiment — illustrative doc entries

> ## ILLUSTRATIVE TEACHING EXAMPLE — NOT REAL RESEARCH
>
> Everything below is a **fictional, illustrative example** showing what `HYP` / `DATASET` /
> `EXP` / `REV` entries look like in this template's exact entry format, written for the
> `examples/toy-sentiment/` onboarding fixture only.
>
> - These are **not** entries from any real research project.
> - They use placeholder IDs (`HYP-EX-001`, etc.) that are **outside** the real project's
>   global `HYP-NNN` / `DATASET-NNN` / `EXP-NNN` / `REV-NNN` counters, specifically so they can
>   never collide with, or be mistaken for, a real entry.
> - **Do not copy these into the real `discussion.md`, `result.md`, or `error.md`.** Those
>   documents record this project's actual research; this file records a worked example for
>   people learning the system.
>
> The numbers cited below (accuracy 1.0000, macro-F1 1.0000, vocabulary size 242, split sizes,
> content hashes) are real — they are taken directly from an actual run of this fixture
> (`sample_output.txt`) and from `data/DATASET_NOTES.md`. Only the framing as formal `HYP` /
> `DATASET` / `EXP` / `REV` doc entries is illustrative; the toy classifier itself really was
> run and really did produce these numbers.

---

## [HYP-EX-001] toy sentiment corpus is learnable by a bag-of-words classifier | 2026-07-09 | brainstorm (illustrative)
Claim: A bag-of-words multinomial Naive Bayes classifier, fit only on a stratified train split
of a small hand-written sentiment corpus, can distinguish positive from negative review-style
sentences on a held-out test split at accuracy meaningfully above chance.
Prediction: test accuracy >= 0.80 on the held-out split (the target stated in
`data/DATASET_NOTES.md`, "Intended use").
Falsifier: test accuracy at or below chance level (~0.50) on the held-out split would refute
the claim that the corpus/model combination is learnable.
Required data: DATASET-EX-001 (toy-sentiment corpus, stratified split).
Required baselines: none — this is a pipeline-demonstration fixture, not a comparative
benchmark; no other model is evaluated against it.
Required metrics: accuracy, macro-F1, confusion matrix.
Linked papers: none (toy fixture; no literature grounding claimed or required).
---

## [DATASET-EX-001] toy-sentiment corpus | 2026-07-09 | data (illustrative)
Source: hand-written by the data agent for this template fixture, 2026-07-09. Generic
film/tech/food/travel/retail review-style sentences. No real people, no personal data, no
scraped content, no external license.
Cohort: 60 independent, single-sentence, hand-written texts (no natural grouping key); 30
positive-sentiment and 30 negative-sentiment, spanning 8 review domains (film/music, tech
product, restaurant/cafe, hotel/travel, retail/apparel, book/museum, app, customer service) so
the classifier cannot key on domain instead of sentiment.
Size: total=60, train=42, val=0, test=18 (per-class: train 21/21, test 9/9).
Split policy: stratified by label — within each class, sentences shuffled with
`random.Random(42)` and the first 70% (`round(30*0.7)=21`) assigned to train, remainder to
test; train/test lists re-shuffled with the same seed to interleave classes in file order.
Seed 42, hard-coded in `build_dataset.py`; re-running the script reproduces byte-identical
output.
Known leakage risks: checklist run via `verify_split.py`, all applicable items pass, 0
unresolved — group-level splits N/A (no shared group key, disjoint-set assertions in
`build_dataset.py`); no record overlap (0 intersection of normalized text between train and
test; cross-label Jaccard max similarity 0.32, no near-duplicate opposite-label pairs);
temporal integrity N/A (static text classification); no target leakage in features (label
never concatenated into text); statistics fit on train only (`classifier.py` fits its
vocabulary on `train.jsonl` rows exclusively, verified by reading the code); pretraining
contamination N/A/noted (hand-written toy fixture, not a public benchmark).
Hash: `train.jsonl` = `153caf41b39aeafac2a6144d9422f4e93eb45b0a9edeb23ff72c1e29f15336c4`;
`test.jsonl` = `288416627354ed85f09a1cd41989803d706885495b2649541e4bedea63c2e8ce` (both from
`data/DATASET_NOTES.md`).
Linked: HYP-EX-001.
---

## [EXP-EX-001] toy-sentiment bag-of-words Naive Bayes run | 2026-07-09 | experiment-tracker (illustrative)
**Hypothesis:** HYP-EX-001
**Status:** complete

### Setup
- Task: binary sentiment classification (positive/negative).
- Method: bag-of-words multinomial Naive Bayes with Laplace smoothing (`alpha=1.0`),
  stdlib-only regex tokenizer (`classifier.py`).
- Model: `NaiveBayesClassifier`; vocabulary fit on the train split only; vocabulary size 242
  tokens; classes `['negative', 'positive']`.
- Dataset: DATASET-EX-001.
- Hardware: CPU only (`device: cpu` in the run's own config block); no GPU, no third-party
  numerical libraries (no numpy/sklearn/torch).
- Wall-clock: not separately timed — the pipeline is a sub-second, pure-Python, 60-row-corpus
  run.

### Results
| Metric | Value |
|:--|:--|
| n (test rows) | 18 |
| correct | 18 |
| accuracy | 1.0000 |
| macro-F1 | 1.0000 |
| negative precision/recall/F1 | 1.0000 / 1.0000 / 1.0000 (support 9) |
| positive precision/recall/F1 | 1.0000 / 1.0000 / 1.0000 (support 9) |

Confusion matrix (rows=true, cols=pred): negative [9, 0]; positive [0, 9].

### Key findings
- Meets and exceeds the `>= 0.80` prediction in HYP-EX-001 on this held-out split.
- All numbers above are copied unmodified from a real captured run
  (`sample_output.txt`), reproduced by `python3 run_example.py`.

### Notes
Artifacts: `examples/toy-sentiment/sample_output.txt` (captured stdout of the run).
Linked: HYP-EX-001, DATASET-EX-001, REV-EX-001.
---

## [REV-EX-001] toy-sentiment result has no generalization claim | 2026-07-09 | critic (illustrative)
**Target:** EXP-EX-001
**Severity:** minor (non-blocking for the fixture's own teaching purpose; would block any
attempt to cite this result as evidence of real-world model capability)

### Issues
1. The 18-row test set is drawn from a 60-sentence corpus deliberately built around a small,
   fixed, ~20-word sentiment vocabulary (`data/DATASET_NOTES.md`, "Learnability design").
   Perfect accuracy reflects near-total separability by construction, not classifier
   generalization ability.
2. The corpus contains no negation ("not good"), no sarcasm, no mixed or neutral sentiment,
   and no lexical diversity beyond the fixed vocabulary — `data/DATASET_NOTES.md`'s own "Known
   biases" section states the split will not generalize to informal or sarcastic text.
3. n=18 is far too small to support any statistical claim of robustness; the run is a single
   deterministic execution (Naive Bayes fit/predict here has no randomness), not a
   multi-seed or multi-replicate result.

### Resolution
Status: open (informational). Accepted as expected and by design for a teaching fixture whose
stated purpose (`data/DATASET_NOTES.md`, "Intended use") is a visibly-working pipeline, not a
sentiment-classification benchmark. This entry exists to show, in template format, the kind of
caveat a real `critic` review would raise before a result like this could be reported to a
user as evidence of anything beyond "the pipeline runs correctly end to end."
---
