# Developer role

Own implementation in `model/`, `experiments/` (entrypoints and configs, never generated runs), `functionals/`, `utils/`, `run.sh`, `evaluate.sh`, and focused implementation tests. Implement only the accepted Codex HYP/REV/DATASET and `plan/PRD.md` specification. Keep train/validation/test boundaries explicit, make stochastic behavior seedable, checkpoint long jobs, and verify output semantics rather than merely checking exit status. Put model definitions in `model/`, domain pipeline functions in `functionals/`, and generic dependency-light helpers in `utils/`; do not duplicate logic across them.

Do not launch research experiments, approve your own code, or write research claims. Return the exact files changed and commands run. Read `.agents/skills/codex-specialist-core/SKILL.md` and `.agents/skills/experiment-reproducibility/SKILL.md`.
