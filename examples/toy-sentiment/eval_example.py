#!/usr/bin/env python3
"""Evaluation step for the toy-sentiment example (stdlib only).

Computes accuracy, per-class precision/recall/F1, macro-F1, and a confusion
matrix for a fitted `NaiveBayesClassifier` against a labeled JSON-lines file.
Ground truth (`data/test.jsonl` labels) is used here for comparison ONLY,
never for fitting anything — that discipline lives in `classifier.py`
(`fit` is called on train rows exclusively, in `run_example.py`).

Usage (standalone, given an already-fit classifier is impractical from the
CLI, so this script is normally used as a library from run_example.py; a
`__main__` block below still trains+evaluates for convenience/debugging):
    python3 eval_example.py [--train data/train.jsonl] [--test data/test.jsonl]
"""
import argparse
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence

from classifier import NaiveBayesClassifier, load_jsonl


def compute_metrics(y_true: Sequence[str], y_pred: Sequence[str], labels: Sequence[str]) -> Dict:
    """Compute accuracy, per-class precision/recall/F1, macro-F1, and a confusion matrix."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be the same length")
    n = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / n if n else 0.0

    confusion = {t: Counter() for t in labels}  # confusion[true][pred] = count
    for t, p in zip(y_true, y_pred):
        confusion[t][p] += 1

    per_class = {}
    f1_sum = 0.0
    for c in labels:
        tp = confusion[c][c]
        fp = sum(confusion[other][c] for other in labels if other != c)
        fn = sum(confusion[c][other] for other in labels if other != c)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        per_class[c] = {
            "precision": precision, "recall": recall, "f1": f1,
            "support": sum(confusion[c].values()),
        }
        f1_sum += f1
    macro_f1 = f1_sum / len(labels) if labels else 0.0

    return {
        "n": n,
        "correct": correct,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion": {t: dict(confusion[t]) for t in labels},
    }


def format_metrics(metrics: Dict, labels: Sequence[str]) -> str:
    """Render a metrics dict as a human-readable summary string."""
    lines = []
    lines.append(f"n={metrics['n']}  correct={metrics['correct']}  "
                  f"accuracy={metrics['accuracy']:.4f}  macro_f1={metrics['macro_f1']:.4f}")
    lines.append("")
    lines.append(f"{'class':<10} {'precision':>9} {'recall':>9} {'f1':>9} {'support':>8}")
    for c in labels:
        pc = metrics["per_class"][c]
        lines.append(f"{c:<10} {pc['precision']:>9.4f} {pc['recall']:>9.4f} "
                      f"{pc['f1']:>9.4f} {pc['support']:>8d}")
    lines.append("")
    header = "confusion (rows=true, cols=pred): " + " ".join(labels)
    lines.append(header)
    for t in labels:
        row = " ".join(str(metrics["confusion"][t].get(p, 0)) for p in labels)
        lines.append(f"  {t:<10} {row}")
    return "\n".join(lines)


def evaluate(clf: NaiveBayesClassifier, test_rows: List[dict]) -> Dict:
    """Predict on test_rows with a fitted classifier and compute metrics vs. ground truth."""
    y_true = [r["label"] for r in test_rows]
    y_pred = clf.predict_batch([r["text"] for r in test_rows])
    labels = sorted(set(y_true) | set(y_pred))
    return compute_metrics(y_true, y_pred, labels)


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default=str(here / "data" / "train.jsonl"),
                         help="Path to training JSON-lines file (fit only, never eval).")
    parser.add_argument("--test", default=str(here / "data" / "test.jsonl"),
                         help="Path to test JSON-lines file (evaluation only).")
    parser.add_argument("--alpha", type=float, default=1.0,
                         help="Laplace smoothing parameter for the Naive Bayes model.")
    args = parser.parse_args()

    train_rows = load_jsonl(args.train)
    test_rows = load_jsonl(args.test)
    clf = NaiveBayesClassifier(alpha=args.alpha).fit(
        [r["text"] for r in train_rows], [r["label"] for r in train_rows]
    )
    metrics = evaluate(clf, test_rows)
    labels = sorted(metrics["per_class"])
    print(format_metrics(metrics, labels))


if __name__ == "__main__":
    main()
