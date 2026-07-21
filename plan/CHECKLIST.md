# Research checklist — <project name>

The selected provider's root conductor-orchestrator keeps dependent stages ordered. Independent
read-only stages may run in parallel. Every completed row requires an evidence pointer.

| Stage | Acceptance item | Owner | Status | Evidence |
|---|---|---|---|---|
| scope | `plan/PRD.md` agreed with the user | root | pending | `plan/PRD.md` |
| literature | primary-source evidence map complete | brainstorm | pending | `report/discussion.md` |
| hypothesis | falsifiable HYP cleared by critic | brainstorm / critic | pending | `report/discussion.md` |
| data | DATASET provenance and leakage audit passed | data | pending | `report/discussion.md` |
| build | accepted model and experiment code implemented | developer | pending | `model/`, `functionals/`, `utils/`, `experiments/` |
| verify | implementation and split checks passed | qa | pending | `report/discussion.md` |
| run | reproducible EXP record complete | experiment-tracker | pending | `report/result.md`, `experiments/runs/` |
| analyze | claims cleared for uncertainty and validity | critic | pending | `analysis/`, `report/discussion.md` |
| write | claims, references, and artifacts reviewed | writer / critic / qa | pending | `report/result.md` |
