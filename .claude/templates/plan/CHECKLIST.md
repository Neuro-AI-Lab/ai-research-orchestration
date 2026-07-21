# Research checklist — <project name>

Development-only working checklist (never part of the released research code). The orchestrator
keeps one stage `in_progress` at a time; completed items keep their evidence pointer.

| Stage | Item | Owner (agent) | Status | Evidence |
|---|---|---|---|---|
| plan | PRD agreed with the user | orchestrator | pending | plan/PRD.md |
| hypothesis | HYP entries reviewed (REV gate passed) | brainstorm / critic | pending | report/discussion.md |
| data | DATASET entry with leakage audit passed | data | pending | report/discussion.md |
| build | model + experiment code QA-gated | developer / qa | pending | report/discussion.md |
| run | EXP entries with reproducibility metadata | experiment-tracker | pending | report/result.md |
| report | REPORT written from recorded results only | writer / critic | pending | report/result.md |
