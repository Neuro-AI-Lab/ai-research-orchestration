#!/usr/bin/env python3
"""Bag-of-words multinomial Naive Bayes sentiment classifier (stdlib only).

Deliberately CPU-only and dependency-free (no numpy/sklearn/torch) so this
example runs anywhere a plain python3 interpreter is available. This is a
teaching fixture for the template's onboarding workflow, not a research-grade
model.

Leakage discipline: `NaiveBayesClassifier.fit` must only ever be called with
training rows. All vocabulary, class priors, and word-likelihood statistics
are derived exclusively from the rows passed to `fit`; nothing in this module
reads or references `data/test.jsonl`.

Usage (library):
    from classifier import NaiveBayesClassifier, load_jsonl, tokenize

    train_rows = load_jsonl("data/train.jsonl")
    clf = NaiveBayesClassifier(alpha=1.0)
    clf.fit([r["text"] for r in train_rows], [r["label"] for r in train_rows])
    predicted_label = clf.predict("This was a fantastic experience.")
"""
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence

_TOKEN_RE = re.compile(r"[a-z']+")


def tokenize(text: str) -> List[str]:
    """Lowercase and split text into alphabetic word tokens (stdlib regex only)."""
    return _TOKEN_RE.findall(text.lower())


def load_jsonl(path) -> List[dict]:
    """Load a JSON-lines file of {"text": str, "label": str} rows."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class NaiveBayesClassifier:
    """Multinomial Naive Bayes over bag-of-words counts, with Laplace smoothing.

    All statistics (class priors, vocabulary, word-likelihoods) are fit from
    the texts/labels passed to `fit` only. Words seen only at prediction time
    (out-of-vocabulary) are ignored when scoring, since no train-time count
    exists for them under Laplace smoothing without leaking test-time stats
    into the vocabulary.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.classes: List[str] = []
        self.vocab: set = set()
        self.log_prior: Dict[str, float] = {}
        self.log_likelihood: Dict[str, Dict[str, float]] = {}
        self._fitted = False

    def fit(self, texts: Sequence[str], labels: Sequence[str]) -> "NaiveBayesClassifier":
        """Fit class priors and word likelihoods from training texts/labels only."""
        if len(texts) != len(labels):
            raise ValueError("texts and labels must be the same length")
        if not texts:
            raise ValueError("cannot fit on an empty training set")

        label_counts = Counter(labels)
        self.classes = sorted(label_counts)
        n_docs = len(labels)

        word_counts_per_class: Dict[str, Counter] = {c: Counter() for c in self.classes}
        total_words_per_class: Dict[str, int] = {c: 0 for c in self.classes}

        for text, label in zip(texts, labels):
            tokens = tokenize(text)
            word_counts_per_class[label].update(tokens)
            total_words_per_class[label] += len(tokens)
            self.vocab.update(tokens)

        vocab_size = len(self.vocab)
        self.log_prior = {
            c: math.log(label_counts[c] / n_docs) for c in self.classes
        }
        self.log_likelihood = {}
        self._unseen_log_likelihood: Dict[str, float] = {}
        for c in self.classes:
            denom = total_words_per_class[c] + self.alpha * vocab_size
            # NOTE: previously used defaultdict(lambda: math.log(self.alpha / denom)),
            # which is a late-binding closure bug -- all per-class factories captured
            # the same free variable `denom`, so by score-time every class's
            # "unseen word" fallback silently used the LAST class's denominator
            # instead of its own. Fixed by storing the per-class fallback value
            # explicitly (self._unseen_log_likelihood[c]) instead of relying on a
            # closure over a loop variable.
            self._unseen_log_likelihood[c] = math.log(self.alpha / denom)
            likelihoods: Dict[str, float] = {}
            for word, count in word_counts_per_class[c].items():
                likelihoods[word] = math.log((count + self.alpha) / denom)
            self.log_likelihood[c] = likelihoods

        self._fitted = True
        return self

    def score(self, text: str) -> Dict[str, float]:
        """Return log-posterior (unnormalized) score per class for a single text."""
        if not self._fitted:
            raise RuntimeError("classifier must be fit before scoring")
        tokens = tokenize(text)
        scores = {}
        for c in self.classes:
            s = self.log_prior[c]
            likelihoods = self.log_likelihood[c]
            fallback = self._unseen_log_likelihood[c]
            for tok in tokens:
                if tok in self.vocab:
                    s += likelihoods.get(tok, fallback)
            scores[c] = s
        return scores

    def predict(self, text: str) -> str:
        """Predict the most likely class label for a single text."""
        scores = self.score(text)
        return max(scores, key=scores.get)

    def predict_batch(self, texts: Sequence[str]) -> List[str]:
        """Predict labels for a batch of texts."""
        return [self.predict(t) for t in texts]


if __name__ == "__main__":
    # Minimal self-check on synthetic in-memory data (no file I/O), so this
    # module can be smoke-tested standalone: `python3 classifier.py`.
    demo_texts = [
        "great awesome wonderful", "terrible awful bad",
        "amazing fantastic love it", "hate disgusting horrible",
    ]
    demo_labels = ["positive", "negative", "positive", "negative"]
    clf = NaiveBayesClassifier().fit(demo_texts, demo_labels)
    pred = clf.predict("this was fantastic and wonderful")
    print(f"self-check prediction for a clearly positive sentence: {pred}")
    assert pred == "positive", "self-check failed: expected positive"
    print("classifier.py self-check OK")
