---
name: experiment-reproducibility
description: Plan, implement, launch, record, and audit reproducible AI/ML experiments with immutable configs, code/data provenance, deterministic seeds, environment capture, resumable runs, and traceable metrics. Use for developer and experiment-tracker work.
---

# Experiment reproducibility

Before a run, require a current HYP, passed critic plan review, passed QA attestation for the exact code,
and passed DATASET leakage audit. Save the full config before launch and verify resources, weights,
licenses, and output paths.

Capture generated run evidence under `experiments/runs/EXP-NNN/` while keeping reusable entrypoints
and configs directly under `experiments/`:

- actual git commit and dirty diff status, or an immutable captured diff hash when no commit exists;
- immutable config and exact command;
- all seeds and determinism settings;
- model/weights identifier and checksum when available;
- dataset ID, version, split hash, and preprocessing version;
- Python/package/CUDA environment and hardware;
- start/end timestamps, wall time, logs, checkpoints, metrics, and failure status.

Make stochastic behavior seedable. Keep train/validation/test boundaries explicit. Support checkpoints
and resumption for long jobs without overwriting prior evidence. A sweep has one EXP owner, a fixed
manifest, process-level sub-runs launched with distinct `--tag` values, and one fan-in summary;
disclose every attempted configuration.

Record failed and inconclusive runs. Every reported number must be parsed from a retained artifact and
name its source. Run multiple seeds when an effect claim depends on variance. Treat suspiciously high
or identical scores as triggers for leakage and validity review, not findings.
