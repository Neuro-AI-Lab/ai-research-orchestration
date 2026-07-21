# Research checklist — <project name>

Local development checklist owned by the root Codex conductor-orchestrator. Keep only one dependent
stage in progress; independent read-only stages may run in parallel. Every completed row needs an
evidence pointer.

| Stage | Acceptance item | Owner | Status | Evidence |
|---|---|---|---|---|
| scope | `plan/PRD.md` agreed with the user | root | pending | `plan/PRD.md` |
| literature | primary-source evidence map complete | brainstorm | pending | `report/discussion.md` |
| hypothesis | falsifiable HYP cleared by critic | brainstorm / critic | pending | `report/discussion.md` |
| data | DATASET provenance and leakage audit passed | data | pending | `report/discussion.md` |
| build | implementation satisfies accepted plan | developer | pending | `model/`, `functionals/`, `utils/`, `experiments/` |
| verify | implementation and split checks passed | qa | pending | `report/discussion.md` |
| run | reproducible EXP record complete | experiment-tracker | pending | `report/result.md`, `experiments/runs/` |
| analyze | claims cleared for uncertainty and validity | critic | pending | `analysis/`, `report/discussion.md` |
| write | claims, references, and artifacts reviewed | writer / critic / qa | pending | `report/result.md` |
