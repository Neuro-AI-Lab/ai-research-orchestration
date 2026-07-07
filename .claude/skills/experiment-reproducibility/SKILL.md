---
name: experiment-reproducibility
description: >-
  Run and record AI/modeling experiments reproducibly — capturing every variable that
  affects a result (commit, config, seed, environment, hardware) and logging raw
  numbers with their source. Use this skill whenever the user is about to run training,
  fine-tuning, generation, or evaluation, when they ask "how should I track this
  experiment", "make this reproducible", "log these results", or "set up my run", and
  whenever results need recording. Trigger it before a run rather than after — the
  metadata that makes a result reproducible is mostly impossible to recover once the
  run is over, so prefer setting up capture up front.
---

# Experiment reproducibility

A result you cannot reproduce is not a result. The discipline here is to capture
every variable that could change the outcome *before* the run, record raw numbers
with their source during the run, and never fill a gap with a remembered or guessed
value. Interpretation of whether a number supports a hypothesis is a separate
job — this skill is about producing trustworthy raw evidence.

## Pre-run checklist — block on any failed item

- [ ] The target hypothesis exists and is current (not deprecated).
- [ ] Any validity review of the plan is non-blocking — known blocking issues are
      resolved or explicitly overridden with stated reasoning.
- [ ] The code has passed its tests/QA at the commit being run.
- [ ] The dataset and splits are defined and have cleared a leakage audit.
- [ ] **The config is saved as a file before the run starts** — not passed as
      ad-hoc CLI flags that vanish afterward.
- [ ] Model weights and dependencies are available and pinned.
- [ ] Hardware resources are sufficient (won't OOM partway and corrupt the record).

If any item fails, do not run. Fix it first.

## Metadata to capture for every run

Capture these into a per-run directory (e.g. `experiments/<run-id>/`) so the run can
be reconstructed exactly:

| Field         | Why it matters                                    |
|:--------------|:--------------------------------------------------|
| Git commit    | The exact code. Get it with `git rev-parse HEAD`. |
| Full config   | Every hyperparameter, saved as a file.            |
| CLI args      | The exact invocation.                             |
| Seed(s)       | Reproducibility *and* a basis for variance.       |
| Model name/ID | The exact weights.                                |
| Dataset ID    | Which split definition was used.                  |
| Environment   | Python version, key dependency versions, CUDA.    |
| Hardware      | GPU/CPU, RAM — affects both feasibility and timing.|
| Wall-clock    | For cost and comparison.                           |

A run logged without its commit hash and config is not reproducible no matter how
good the numbers look.

## Recording results

Write one record per experiment — including failed and inconclusive runs, which are
evidence too. Every number must come from a logged run and cite its log file; never
summarize results from memory.

```markdown
## [run-id] short title | YYYY-MM-DD
**Hypothesis:** <id, claim in one line>
**Status:** complete | failed | inconclusive
**Dataset:** <id>   **Config:** `experiments/<run-id>/config.yaml`

### Setup
| Parameter | Value |
|:----------|:------|
| Task / Method / Model | ... |
| Hardware / Wall-clock | ... |

### Results
| Metric | Value |   <- every value traceable to a log file
|:-------|:------|

### Notes
- caveats, artifact locations, anything surprising
```

For a failed run, record the failure mode and error class rather than leaving it
blank or inventing a plausible number. "Crashed" is a valid, honest entry.

## Reproducibility hygiene

- **Seed everything** that has a random component, and record the seed.
- **Run multiple seeds** when the conclusion depends on the size of an effect — a
  single seed cannot tell you whether a gap is signal or noise.
- **Snapshot the environment** (`pip freeze`) per run, and never delete the snapshot
  for a run whose results have been published or reported.
- **Save the config as a file before the run**, so the record is the actual config,
  not a reconstruction.

## When a result looks surprising

Suspiciously high scores, or identical scores across configurations that should
differ, are signals — not findings. Do not just record them. Flag the run as
suspicious and trigger a leakage audit and a validity review before the number is
trusted or reported.
