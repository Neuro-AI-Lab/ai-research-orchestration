# examples/toy-sentiment — onboarding fixture

A tiny, self-contained, dependency-free sentiment classification pipeline that walks a new
user through one full loop of this template's research workflow — hypothesis, dataset with a
leakage checklist, model/eval code, and a result — without needing any external data, GPU,
or third-party packages. It is a **teaching fixture**, not a research project: read
`### About the perfect score` below before drawing any conclusion from its numbers.

## What this demonstrates

- A falsifiable hypothesis stated up front, before any code ran.
- A documented, hashed, leakage-checked train/test split (the `data` agent's job in a real
  project).
- Model and evaluation code that fits statistics on the train split only, and that keeps a
  visible, auditable record of that discipline in its own docstrings.
- A single reproducible run producing a metrics report, with real numbers captured from an
  actual execution (`sample_output.txt`), not invented ones.
- How the toy maps onto the template's mandatory gates (critic / qa / data) and the
  four-document system, even though the fixture itself is intentionally exempt from the
  mechanical experiment gate (see "Why the naming matters" below).

## File map

| File | Role |
|:--|:--|
| `data/train.jsonl` | 42 labeled sentences (21 positive, 21 negative) — fit-only split. |
| `data/test.jsonl` | 18 labeled sentences (9 positive, 9 negative) — held-out evaluation split. |
| `data/DATASET_NOTES.md` | The dataset card: source, split policy, seed, content hashes, and the full leakage checklist (this is the toy stand-in for a real `DATASET-NNN` `discussion.md` entry). |
| `build_dataset.py` | Deterministic split builder (`random.Random(42)`, stratified per class, 70/30). Re-running it reproduces the split byte-for-byte. |
| `verify_split.py` | Stdlib-only integrity/leakage verifier: counts, duplicate check, cross-split disjointness, label domain check, content hashes, and a "learnability" check (every test-time sentiment word is present in the train vocabulary for its class). |
| `classifier.py` | The model: a bag-of-words multinomial Naive Bayes classifier, pure Python stdlib (no numpy/sklearn/torch). `fit()` is only ever called on train rows; out-of-vocabulary test-time words are ignored rather than folded into the vocabulary. |
| `eval_example.py` | Metrics: accuracy, per-class precision/recall/F1, macro-F1, confusion matrix — computed from ground-truth test labels used for comparison only, never for fitting. |
| `run_example.py` | The single entry point: loads train+test, fits on train, evaluates on test, prints a config block and the metrics report. |
| `run_example.sh` | Thin shell wrapper around `run_example.py`. |
| `sample_output.txt` | The real, captured stdout of an actual `run_example.py` run — the exact numbers referenced below. |

## How to run it

From the repository root:

```bash
python3 examples/toy-sentiment/run_example.py
```

or from inside the fixture directory:

```bash
cd examples/toy-sentiment && ./run_example.sh
```

### Expected output

The run trains on the 42-row train split, fits a vocabulary of 242 tokens, evaluates on the
18-row held-out test split, and reports (see `sample_output.txt` for the full captured
transcript of a real run):

```
n=18  correct=18  accuracy=1.0000  macro_f1=1.0000

class      precision    recall        f1  support
negative      1.0000    1.0000    1.0000        9
positive      1.0000    1.0000    1.0000        9
```

### About the perfect score

Accuracy 1.0000 / macro-F1 1.0000 on 18 test rows is **expected for this fixture and is not
a benchmark result**. The corpus is deliberately tiny (60 hand-written sentences total) and
built around a small, fixed, shared sentiment vocabulary so the pipeline is visibly and
reliably learnable end to end (see `data/DATASET_NOTES.md`, "Learnability design" and
"Intended use"). Do not cite this number as evidence of real-world sentiment-classification
capability — it demonstrates that the plumbing (split → fit-on-train → evaluate-on-test →
report) works correctly, nothing more. The illustrative `REV-EX-001` entry below spells out
this caveat in the template's own review format.

### Why the naming matters

`run_example.py` / `run_example.sh` are deliberately **not** named `run.sh` / `evaluate.sh`,
and this code does **not** live under `models/`. The template's `PreToolUse` gate hook
(`.claude/hooks/experiment_gate.py`) blocks those specific launch patterns until critic/qa/data
gates are satisfied — appropriate for real experiments, but this fixture is a teaching example
with no hypothesis riding on its outcome, so it is intentionally outside that hook's scope.

## How this maps to the template's real workflow

This fixture compresses the full research cycle described in `CLAUDE.md` into one runnable
example. The correspondence:

1. **Hypothesis** — a real project starts with `brainstorm` writing a falsifiable `HYP-NNN`
   entry to `discussion.md`. This fixture's stand-in is the illustrative `HYP-EX-001` entry
   below.
2. **Dataset + leakage checklist** — a real project has `data` design the split and write a
   `DATASET-NNN` entry with the leakage checklist from the `data-leakage-audit` skill. Here,
   `data/DATASET_NOTES.md` plays that role directly, and `verify_split.py` is the runnable
   evidence behind it (disjoint splits, class balance, content hashes, learnability check —
   all reproducible by re-running the script). The illustrative `DATASET-EX-001` entry below
   shows what the corresponding `discussion.md` entry would look like.
3. **Model and eval code** — a real project's `developer` owns `models/` and `evaluation/`.
   Here `classifier.py` and `eval_example.py` play those roles, with the same discipline
   (fit only on train, never reference test labels for fitting).
4. **Gates** — before any real experiment launches, `critic` must have reviewed the plan (no
   blocking `REV` open), `qa` must have verified the code (no critical `BUG` open), and `data`
   must have a passing leakage checklist. In a real project these three gates are also
   enforced mechanically by `experiment_gate.py` for `run.sh` / `evaluate.sh` / `models/*.py`
   launches. This fixture illustrates the shape of that review with `REV-EX-001` below, but
   (per "Why the naming matters") is not itself subject to the mechanical hook.
5. **Experiment run** — a real project's `experiment-tracker` owns `experiments/<run-id>/` and
   writes an `EXP-NNN` entry to `result.md` with setup, results, and artifacts. The
   illustrative `EXP-EX-001` entry below mirrors that structure, citing the real numbers from
   `sample_output.txt`.
6. **Report** — a real project's `writer` synthesizes `EXP` entries into a `REPORT-YYYY-MM-DD`
   narrative in `result.md`, after `critic` review, before anything is reported to the user.
   This README's "Expected output" section plays that role for the fixture.
7. **Handoff, gates, and version management** — a real project wraps all of the above in the
   session-continuity layer (`.claude/state/handoff.json`, `SessionStart`/`Stop` hooks) and the
   four-document version lifecycle (`version-management` skill: archive into `version.md`
   before resetting `result.md` / `discussion.md` / `error.md` at a milestone). This toy fixture
   is a single, self-contained loop and does not exercise that machinery — it exists to make
   the *inner* loop (hypothesis → data → model → gate → result) concrete before a new user
   reads about the outer loop.

See `EXAMPLE_ENTRIES.md` in this directory for the illustrative `HYP` / `DATASET` / `EXP` /
`REV` entries in the template's exact entry format.
