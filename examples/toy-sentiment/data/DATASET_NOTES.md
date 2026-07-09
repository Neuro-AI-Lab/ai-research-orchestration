# Dataset notes: toy-sentiment (example fixture)

This is **example documentation for a teaching fixture**, not a real project's
root `discussion.md` DATASET entry. It exists to demonstrate the template's
data-agent workflow (split design, leakage checklist, hashing discipline) end
to end on a trivial, self-contained dataset. It is not linked to any real
`HYP-NNN` and carries no research claims.

**Revision note (this version):** this replaces an earlier revision that was
too templated -- several test sentences were near-duplicates of an
opposite-label train sentence differing by one adjective, and that adjective
was out-of-vocabulary in the tiny train set, so the downstream bag-of-words
classifier scored 0.167 (below chance). This revision rebuilds the corpus
around a small, fixed, shared sentiment vocabulary reused across many varied
sentences (the "learnability" design below), which is a deliberate,
documented, non-leaky design choice — see "Known leakage risks."

**Source:** hand-written by the data agent for this template, 2026-07-09.
Generic film/tech/food/travel/retail review-style sentences. No real people,
no personal data, no scraped content, no external license.
**Format:** JSON Lines, one record per line, stdlib-parseable
(`{"text": str, "label": "positive"|"negative"}`).
**Build script:** `build_dataset.py` (deterministic, stdlib `random`, `re`,
`json`; fixed seed).
**Verify script:** `verify_split.py` (stdlib `hashlib`, `json`, `re`,
`collections`; reproduces every number below, including the learnability
check).

### Cohort

- All 60 records are independent, single-sentence, hand-written texts — no
  natural grouping key (no subject/session/document ID), so there is nothing
  to leak at a "group" level beyond the sentence itself.
- 30 positive-sentiment sentences, 30 negative-sentiment sentences, each
  covering a mix of domains (film/music, tech product, restaurant/cafe,
  hotel/travel, retail/apparel, book/museum, app, customer service) so the
  classifier cannot key on domain instead of sentiment.
- No inclusion/exclusion filtering was needed; every hand-written sentence
  was used.

### Learnability design (the point of this revision)

Every sentence is built around **two** words drawn from a small, fixed,
class-specific sentiment vocabulary:

| Positive vocab | Negative vocab |
|:--|:--|
| great, love, excellent, wonderful, amazing, best, enjoyed, happy, fantastic, recommend | terrible, hate, awful, worst, boring, disappointing, poor, broken, waste, avoid |

Each word is used in a "shift" combinatorial layout (word `i` paired with
words at circular distances 1, 2, and 3 in the 10-word list) so it occurs in
exactly **6 of the 30 sentences** in its class. This was tuned empirically:
an earlier draft of this revision used **one** vocab word per sentence
(occurring 3x per word), which passed every leakage and learnability check
but only reached **0.667** test accuracy with the bag-of-words classifier,
because with just 1-3 occurrences per word the aggregate signal from
sentiment words was not reliably stronger than incidental noise from
stopwords and topic nouns in this tiny corpus. Doubling the words-per-sentence
(and thus per-word train evidence) to a 6x design raised held-out accuracy to
**1.0** (18/18) — see "Verification output" below.

Positive and negative sentences were written **independently**, not as
opposite-label templates differing by one swapped word (that pattern was the
root cause of the original bug: an OOV adjective for one class made the
opposite-class train evidence dominate). A post-hoc Jaccard-similarity check
across every positive/negative sentence pair (token overlap, run during this
build) found a maximum similarity of **0.32** — no near-duplicate
opposite-label pairs exist in this corpus.

### Size and splits

| Split | N | positive | negative |
|:--|--:|--:|--:|
| Total | 60 | 30 | 30 |
| Train | 42 | 21 | 21 |
| Test  | 18 | 9 | 9 |

Split fraction: 70% train / 30% test, applied **per class** (stratified) so
class balance is exact in both splits.

### Schema

| Field | Type | Description |
|:--|:--|:--|
| `text` | string | A single English sentence expressing sentiment. |
| `label` | string | One of `"positive"` / `"negative"`. |

### Split policy

- Stratified split by label: within each class, sentences are shuffled with
  `random.Random(42)` and the first 70% (rounded, `round(30*0.7)=21`) go to
  train, the remainder to test.
- After per-class assignment, `train` and `test` lists are each shuffled
  again with the same seeded RNG so classes are interleaved in file order
  rather than block-ordered (order carries no information for a
  bag-of-words model but keeps the file from looking artificially sorted).
- **Seed:** 42, hard-coded in `build_dataset.py`. Re-running the script
  reproduces byte-identical output (verified: hashes below are stable across
  two runs during this build).
- No stats (vocabulary, scaler, etc.) are fit in this data-layer step; that
  is the downstream developer's responsibility to fit on train only
  (`classifier.py` already does this correctly).

### Known leakage risks

(Per `.claude/skills/data-leakage-audit/SKILL.md`, run via `verify_split.py`)

- [x] **Group-level splits:** N/A — no shared group key exists across
      records (each row is an independently authored sentence, not a
      repeated subject/session). Verified no record appears more than once
      in the source lists (`build_dataset.py` asserts
      `len(POSITIVE) == len(set(POSITIVE))` and same for `NEGATIVE`, plus
      `POSITIVE` and `NEGATIVE` are disjoint sets).
- [x] **No record overlap:** exact + normalized (lowercased,
      whitespace-collapsed, trailing-punctuation-stripped) SENTENCE text
      compared across train/test. Intersection size = 0 (see verification
      output below). A separate cross-label Jaccard-similarity scan (see
      "Learnability design" above) also confirms no near-duplicate
      opposite-label sentence pairs (max similarity 0.32), which is the
      near-duplicate-record risk called out by the leakage skill.
      **Important distinction:** individual sentiment *words* (e.g.
      "great", "terrible") intentionally repeat across train and test and
      across many sentences — this is shared vocabulary, not leaked
      records. The skill's "no record overlap" check is about whole
      records/near-duplicate records, not shared words; a bag-of-words
      classifier cannot learn anything from train unless the vocabulary it
      needs at test time was also observed at train time, so word reuse
      across splits is a required design property here, not a defect.
- [x] **Temporal integrity:** N/A — task is static text classification, no
      timestamps or event ordering involved.
- [x] **No target leakage in features:** the only feature is raw sentence
      text; `label` is a separate field never concatenated into `text`, and
      no sentence contains the literal word "positive"/"negative" as a
      leak-through token (spot-checked against the file above).
- [x] **Statistics from train only:** N/A at this data-layer stage — no
      normalizer/vocabulary is fit here; downstream `classifier.py` fits its
      bag-of-words vocabulary on `train.jsonl` only (verified by reading
      `classifier.py`: `fit()` is only ever called with train rows in
      `run_example.py`, and OOV test-time words are ignored rather than
      added to the vocabulary).
- [x] **Pretraining contamination:** not applicable in the traditional
      sense (this is a hand-written toy fixture, not a public benchmark),
      but noted for completeness: since the sentences are generic and
      simple, semantically similar phrasing may exist in any LLM's
      pretraining data. This has no bearing on the stdlib bag-of-words
      classifier (the intended downstream use), which is not pretrained.

**Result: all applicable checklist items pass. 0 unresolved items.**

### Content hashes (SHA256)

| File | SHA256 |
|:--|:--|
| `train.jsonl` | `153caf41b39aeafac2a6144d9422f4e93eb45b0a9edeb23ff72c1e29f15336c4` |
| `test.jsonl` | `288416627354ed85f09a1cd41989803d706885495b2649541e4bedea63c2e8ce` |

### Verification output (evidence, `python3 verify_split.py`)

```
=== Counts ===
train: 42 rows, by label: {'negative': 21, 'positive': 21}
test:  18 rows, by label: {'positive': 9, 'negative': 9}
total: 60

=== Label domain check ===
distinct labels present: ['negative', 'positive']
OK: only {'positive', 'negative'} present

=== Within-split exact-duplicate check ===
train duplicate normalized texts: 0
test duplicate normalized texts: 0
OK: no within-split duplicates

=== Cross-split overlap / disjointness check ===
train unique normalized texts: 42
test unique normalized texts: 18
intersection (train ∩ test): 0
OK: train and test are disjoint (0 overlap)

=== Class balance check ===
train pos/neg: 21/21
test pos/neg:  9/9
OK: both splits are exactly 50/50 positive/negative

=== Content hashes (SHA256) ===
train.jsonl: 153caf41b39aeafac2a6144d9422f4e93eb45b0a9edeb23ff72c1e29f15336c4
test.jsonl:  288416627354ed85f09a1cd41989803d706885495b2649541e4bedea63c2e8ce

=== Learnability check (no test-only discriminative OOV) ===
For each fixed sentiment vocab word, every test sentence of a class
that contains the word must have a train sentence of the SAME class
that also contains it (so the word is in-vocabulary and correctly
signed for the bag-of-words model).
positive vocab train occurrence counts: great=4, love=4, excellent=6, wonderful=3, amazing=3, best=5, enjoyed=5, happy=4, fantastic=3, recommend=5
negative vocab train occurrence counts: terrible=3, hate=5, awful=4, worst=5, boring=5, disappointing=2, poor=5, broken=5, waste=3, avoid=5
OK: every test-set sentiment vocab word is present in the train vocabulary for its class (0 out-of-vocabulary discriminative words)

=== Summary ===
ALL CHECKS PASSED
```

### Downstream model sanity check (evidence, `python3 eval_example.py`, read-only run of existing developer-owned code -- data agent does not own or modify this script)

```
n=18  correct=18  accuracy=1.0000  macro_f1=1.0000

class      precision    recall        f1  support
negative      1.0000    1.0000    1.0000        9
positive      1.0000    1.0000    1.0000        9

confusion (rows=true, cols=pred): negative positive
  negative   9 0
  positive   0 9
```

This exceeds the target of >=0.80 test accuracy. A perfect score on a small,
intentionally learnable toy corpus is expected — it demonstrates the
pipeline works end to end, not a claim about real-world sentiment
classification performance (see "Intended use").

### Known biases

- Vocabulary is small, fixed, and hand-written by a single author; every
  sentence is deliberately anchored to 2 of 20 total sentiment words. This
  is intentional for a teaching fixture demonstrating a working pipeline —
  it is not representative of real-world sentiment-analysis difficulty
  (real review text has far more lexical diversity, negation, sarcasm, and
  mixed sentiment).
- Domain mix is review-style only (film/music, tech, food/cafe, hotel/
  travel, retail/apparel, book/museum, app, customer service); no other
  genres (e.g., social media slang, sarcasm) are represented, so a
  classifier trained here will not generalize to informal or sarcastic
  text.
- English only, no negation ("not good"), no ambiguous/neutral sentiment
  examples, no sarcasm — this is intentional for a teaching fixture, not
  appropriate for a real sentiment-analysis benchmark.
- Some topic nouns (e.g. "tour", "customer support/service") appear in both
  classes, which is desirable (prevents the model from keying on domain
  instead of sentiment) but does add minor stopword/topic-noun noise; this
  is why per-word repetition (6x) was needed to keep the sentiment signal
  dominant in such a small corpus.

### Intended use

Teaching fixture for the `examples/toy-sentiment/` onboarding example only.
Not a research dataset; do not cite as evidence of model capability. The
target for this fixture is a believable, visibly-working pipeline
(test accuracy >= 0.80 on a stdlib bag-of-words Naive Bayes baseline), not a
benchmark of sentiment-classification difficulty.
