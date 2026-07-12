# Toy sentiment onboarding fixture

A tiny standard-library sentiment pipeline for checking a new installation without external data,
packages, GPUs, or service credentials. It is a teaching fixture, not a research result or benchmark.
Generated output is intentionally not stored in the distribution.

## Files

| File | Purpose |
|---|---|
| `data/train.jsonl`, `data/test.jsonl` | fixed fit-only and held-out splits |
| `data/DATASET_NOTES.md` | source, intended use, split design, leakage checklist |
| `build_dataset.py` | deterministic fixture builder |
| `verify_split.py` | counts, labels, duplicates, disjointness, hashes, learnability checks |
| `classifier.py` | pure-Python multinomial Naive Bayes model |
| `eval_example.py` | accuracy, class metrics, macro-F1, confusion matrix |
| `run_example.py`, `run_example.sh` | fit-on-train and evaluate-on-test entrypoints |

From the repository root:

```bash
./orchestrate demo
# or
python3 examples/toy-sentiment/verify_split.py
python3 examples/toy-sentiment/run_example.py
```

The verifier must pass before the example run. The model vocabulary is fitted only on train rows;
test labels are used only for evaluation. Re-run the commands to obtain current output rather than
relying on a captured transcript.

The corpus is deliberately small, hand-written, and constructed around a shared sentiment vocabulary.
High held-out scores demonstrate plumbing only. They are not evidence of real-world generalization and
must not be cited in a paper or provider comparison.

## CODEX

Run the fixture after `./orchestrate init codex` and `./orchestrate doctor codex`. It does not write
`.codex/research/` or `.codex/runs/` and does not claim that specialists were spawned. For a real Codex
experiment, use `experiments/codex/`, the DATASET/critic/QA gates, and the native audit contract.

## CLAUDE

Run the fixture after `./orchestrate init claude` and `./orchestrate doctor claude`. It does not write
`.claude/research/` or `.claude/agent-memory/` and does not claim that agents were spawned. For a real
Claude experiment, use `experiments/claude/` and the Claude-owned DATASET/critic/QA gates.

## Mapping to a real research workflow

1. `brainstorm` defines a falsifiable hypothesis.
2. `data` records provenance, split unit, hashes, license, and leakage review.
3. `critic` clears the plan before implementation.
4. `developer` implements the accepted baseline/treatment and evaluation semantics.
5. `qa` independently verifies code and split boundaries.
6. `experiment-tracker` records immutable config, code/data provenance, seeds, logs, and failures.
7. `critic` reviews the analysis before `writer` communicates a claim.

The example entrypoints avoid the real experiment-launch names intentionally; this keeps onboarding
independent from live research state while still demonstrating the inner fit/evaluate loop.
