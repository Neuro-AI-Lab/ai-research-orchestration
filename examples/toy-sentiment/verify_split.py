#!/usr/bin/env python3
"""Leakage / integrity verification for the toy-sentiment split (stdlib only).

Checks, printed as evidence:
  1. Per-split and per-class counts (class balance).
  2. No exact-duplicate text within a split.
  3. No exact-duplicate or case/whitespace-normalized near-duplicate text
     across train and test (record overlap check).
  4. Train/test sets are disjoint by normalized text (group-level: here the
     "group" is the sentence itself, since each row is its own record with
     no shared subject/session key).
  5. Label values are restricted to {positive, negative} (no leakage of
     other fields, no stray labels).
  6. SHA256 content hash of each split file, for the dataset card.
  7. LEARNABILITY check: every fixed-vocabulary sentiment word that appears
     in a test sentence of a given class also appears in at least one train
     sentence of that same class. Shared vocabulary is intentional; records
     remain disjoint (see DATASET_NOTES.md).

Usage:
    python3 verify_split.py
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

POSITIVE_VOCAB = [
    "great", "love", "excellent", "wonderful", "amazing",
    "best", "enjoyed", "happy", "fantastic", "recommend",
]
NEGATIVE_VOCAB = [
    "terrible", "hate", "awful", "worst", "boring",
    "disappointing", "poor", "broken", "waste", "avoid",
]
VOCAB_BY_LABEL = {"positive": POSITIVE_VOCAB, "negative": NEGATIVE_VOCAB}

_TOKEN_RE = re.compile(r"[a-z']+")


def tokenize(text):
    return set(_TOKEN_RE.findall(text.lower()))


def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize(text):
    # lowercase + collapse whitespace + strip trailing punctuation, to catch
    # trivial near-duplicates (case/spacing variants), not just exact matches
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[.!?,]+$", "", t)
    return t


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    train_path = DATA_DIR / "train.jsonl"
    test_path = DATA_DIR / "test.jsonl"

    train = load_jsonl(train_path)
    test = load_jsonl(test_path)

    print("=== Counts ===")
    print(f"train: {len(train)} rows, by label: {dict(Counter(r['label'] for r in train))}")
    print(f"test:  {len(test)} rows, by label: {dict(Counter(r['label'] for r in test))}")
    print(f"total: {len(train) + len(test)}")

    print("\n=== Label domain check ===")
    labels = set(r["label"] for r in train) | set(r["label"] for r in test)
    print(f"distinct labels present: {sorted(labels)}")
    assert labels == {"positive", "negative"}, f"unexpected label values: {labels}"
    print("OK: only {'positive', 'negative'} present")

    print("\n=== Within-split exact-duplicate check ===")
    train_norm = [normalize(r["text"]) for r in train]
    test_norm = [normalize(r["text"]) for r in test]
    train_dupes = [t for t, c in Counter(train_norm).items() if c > 1]
    test_dupes = [t for t, c in Counter(test_norm).items() if c > 1]
    print(f"train duplicate normalized texts: {len(train_dupes)}")
    print(f"test duplicate normalized texts: {len(test_dupes)}")
    assert not train_dupes, f"duplicates within train: {train_dupes}"
    assert not test_dupes, f"duplicates within test: {test_dupes}"
    print("OK: no within-split duplicates")

    print("\n=== Cross-split overlap / disjointness check ===")
    train_set = set(train_norm)
    test_set = set(test_norm)
    overlap = train_set & test_set
    print(f"train unique normalized texts: {len(train_set)}")
    print(f"test unique normalized texts: {len(test_set)}")
    print(f"intersection (train ∩ test): {len(overlap)}")
    assert not overlap, f"leakage: overlapping records across train/test: {overlap}"
    print("OK: train and test are disjoint (0 overlap)")

    print("\n=== Class balance check ===")
    train_counts = Counter(r["label"] for r in train)
    test_counts = Counter(r["label"] for r in test)
    print(f"train pos/neg: {train_counts['positive']}/{train_counts['negative']}")
    print(f"test pos/neg:  {test_counts['positive']}/{test_counts['negative']}")
    assert train_counts["positive"] == train_counts["negative"], "train not balanced"
    assert test_counts["positive"] == test_counts["negative"], "test not balanced"
    print("OK: both splits are exactly 50/50 positive/negative")

    print("\n=== Content hashes (SHA256) ===")
    train_hash = sha256_file(train_path)
    test_hash = sha256_file(test_path)
    print(f"train.jsonl: {train_hash}")
    print(f"test.jsonl:  {test_hash}")

    print("\n=== Learnability check (no test-only discriminative OOV) ===")
    print("For each fixed sentiment vocab word, every test sentence of a class")
    print("that contains the word must have a train sentence of the SAME class")
    print("that also contains it (so the word is in-vocabulary and correctly")
    print("signed for the bag-of-words model).")
    train_word_sets = {label: set() for label in VOCAB_BY_LABEL}
    for r in train:
        train_word_sets[r["label"]] |= tokenize(r["text"])

    oov_failures = []
    per_word_train_count = {label: {w: 0 for w in vocab} for label, vocab in VOCAB_BY_LABEL.items()}
    for r in train:
        toks = tokenize(r["text"])
        for w in VOCAB_BY_LABEL[r["label"]]:
            if w in toks:
                per_word_train_count[r["label"]][w] += 1

    for r in test:
        toks = tokenize(r["text"])
        label = r["label"]
        for w in VOCAB_BY_LABEL[label]:
            if w in toks and w not in train_word_sets[label]:
                oov_failures.append((r["text"], label, w))

    for label, vocab in VOCAB_BY_LABEL.items():
        counts_str = ", ".join(f"{w}={per_word_train_count[label][w]}" for w in vocab)
        print(f"{label} vocab train occurrence counts: {counts_str}")

    if oov_failures:
        for text, label, w in oov_failures:
            print(f"FAIL: test sentence ({label}) uses {w!r} which never appears "
                  f"in any train sentence of class {label!r}: {text!r}")
    assert not oov_failures, f"{len(oov_failures)} learnability failures (see above)"
    print("OK: every test-set sentiment vocab word is present in the train "
          "vocabulary for its class (0 out-of-vocabulary discriminative words)")

    print("\n=== Summary ===")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
