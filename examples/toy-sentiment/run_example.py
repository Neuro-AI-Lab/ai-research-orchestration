#!/usr/bin/env python3
"""Train + evaluate the toy-sentiment example in one go (stdlib only, CPU-only).

This is the single entry point for the onboarding example: it fits the
bag-of-words Naive Bayes classifier on `data/train.jsonl` ONLY, then
evaluates the fitted model on `data/test.jsonl` and prints a metrics summary.

Deliberately NOT named run.sh/evaluate.sh and does not live under models/, so
it is unaffected by the template's experiment_gate PreToolUse hook (which
only gates real experiment launches, not this teaching fixture).

No randomness is used anywhere in this pipeline (Naive Bayes fitting and
prediction are both deterministic given the input order-independent counts),
so `--seed` is accepted for CLI/config-capture consistency with the
project's reproducibility conventions but is not read by any code path.

Usage:
    python3 run_example.py
    python3 run_example.py --train data/train.jsonl --test data/test.jsonl --alpha 1.0
"""
import argparse
import json
import platform
import sys
from pathlib import Path

from classifier import NaiveBayesClassifier, load_jsonl
from eval_example import evaluate, format_metrics


def _display_path(path: Path, base: Path) -> str:
    """Render `path` relative to `base` (the script dir) for location-independent
    printing; falls back to the path as given (not resolved to an absolute cwd
    path) if it lies outside `base`, e.g. a user-supplied --train/--test override."""
    try:
        return str(path.resolve().relative_to(base))
    except ValueError:
        return str(path)


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default=str(here / "data" / "train.jsonl"),
                         help="Path to training JSON-lines file (fit only, never eval).")
    parser.add_argument("--test", default=str(here / "data" / "test.jsonl"),
                         help="Path to test JSON-lines file (evaluation only).")
    parser.add_argument("--alpha", type=float, default=1.0,
                         help="Laplace smoothing parameter for the Naive Bayes model.")
    parser.add_argument("--seed", type=int, default=42,
                         help="Recorded for config/reproducibility capture; unused "
                              "(Naive Bayes fit/predict here is fully deterministic).")
    args = parser.parse_args()

    train_path = Path(args.train)
    test_path = Path(args.test)
    if not train_path.exists() or train_path.stat().st_size == 0:
        print(f"WARNING: training file missing or empty: {train_path}. Skipping run.",
              file=sys.stderr)
        return 1
    if not test_path.exists() or test_path.stat().st_size == 0:
        print(f"WARNING: test file missing or empty: {test_path}. Skipping run.",
              file=sys.stderr)
        return 1

    train_rows = load_jsonl(train_path)
    test_rows = load_jsonl(test_path)
    if not train_rows or not test_rows:
        print("WARNING: training or test set parsed to zero rows. Skipping run.",
              file=sys.stderr)
        return 1

    train_display = _display_path(train_path, here)
    test_display = _display_path(test_path, here)

    config = {
        "train_path": train_display,
        "test_path": test_display,
        "alpha": args.alpha,
        "seed": args.seed,
        "model": "bag-of-words multinomial Naive Bayes (stdlib only)",
        "python": platform.python_version(),
        "device": "cpu",
    }
    print("=== config ===")
    print(json.dumps(config, indent=2))

    print(f"\n=== training ===")
    print(f"fitting on {len(train_rows)} rows from {train_display} (train split only)")
    clf = NaiveBayesClassifier(alpha=args.alpha).fit(
        [r["text"] for r in train_rows], [r["label"] for r in train_rows]
    )
    print(f"vocabulary size: {len(clf.vocab)}  classes: {clf.classes}")

    print(f"\n=== evaluation ===")
    print(f"evaluating on {len(test_rows)} rows from {test_display} (test split only)")
    metrics = evaluate(clf, test_rows)
    labels = sorted(metrics["per_class"])
    print()
    print(format_metrics(metrics, labels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
