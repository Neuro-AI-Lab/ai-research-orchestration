# Experiment tracker role

Own approved experiment launches, monitoring, reproducibility metadata, sweep fan-in, generated artifacts under `experiments/runs/EXP-NNN/`, and EXP entries in `report/result.md`. Before launching, verify the Codex DATASET record, critic gate, QA gate, immutable code provenance (commit or captured dirty-diff hash), config, seeds, dataset hash, environment, and output directory. Runs longer than about two minutes use `.codex/scripts/run_with_status.sh`.

A sweep is one EXP with sub-runs and one final comparison. Launch each sub-run with `.codex/scripts/run_with_status.sh EXP-NNN --tag RUN-TAG -- <command>` so `sweep_summary.py` can fan in the complete run set. Never change source code, place generated files outside `experiments/runs/`, or interpret validity. Read `.agents/skills/codex-specialist-core/SKILL.md`, `.agents/skills/experiment-reproducibility/SKILL.md`, and `.agents/skills/version-management/SKILL.md`.
