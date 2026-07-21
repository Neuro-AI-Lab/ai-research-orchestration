# Project path map — keep, remove, or rewrite

[한국어](PROJECT_MAP.ko.md) | [Project overview](../../README.md)

This is the authoritative human inventory for turning the dual-provider distribution into one real
AI-research project. `.orchestration/project_map.json` is the machine-readable source used by
`./orchestrate init` and `./orchestrate adapt`. A release check verifies that every tracked path is
covered by the map.

## 1. Adaptation decision

Choose exactly one provider per checkout. Keep its control plane and remove the unselected one only
after initialization. Keep the research workspace. Review and usually remove template-maintainer
assets. Rewrite project-owned files instead of carrying the template's identity into the research
repository.

```bash
./orchestrate init codex            # or: claude
./orchestrate adapt codex           # advisory text; changes nothing
./orchestrate adapt codex --json    # machine-readable advisory report
```

The advisor never deletes, truncates, or rewrites. Ask the selected root orchestrator to apply an
approved subset. Deletions, license choice, and Git operations require explicit user direction.

## 2. Research workspace — keep

| Tracked path | Purpose | First-project action |
|---|---|---|
| `plan/PRD.md`, `plan/CHECKLIST.md` | user-approved scope and evidence-linked workflow | replace `<project name>` and fill with the root orchestrator |
| `report/{discussion,issue,result,version}.md` | live four-document research record | keep the clean seeds; append only typed project entries |
| `data/.gitkeep` | datasets, manifests, splits, dataset-specific preprocessing | remove `.gitkeep` when real content exists; apply license/privacy/size policy |
| `model/.gitkeep` | model source | replace with project code |
| `experiments/.gitkeep` | experiment code and configs; generated runs go under ignored `runs/` | replace with project code |
| `analysis/.gitkeep` | EDA and result-analysis code/artifacts | replace with project content |
| `functionals/.gitkeep`, `utils/.gitkeep` | reusable research functions and generic helpers | replace with project code |
| `run.sh`, `evaluate.sh` | gated project training/evaluation entrypoints | replace the fail-closed placeholders |

`plan/`, `report/`, and `data/` are intentionally not ignored. Only commit data and research records
allowed by the project's privacy, licensing, size, and collaboration policy.

## 3. Selected-provider orchestration core — keep one

| Selection | Keep | Remove after init |
|---|---|---|
| Codex | `AGENTS.md`, `.codex/**`, `.agents/**` | `CLAUDE.md`, `.claude/**`, `.mcp.json` |
| Claude | `CLAUDE.md`, `.claude/**`, `.mcp.json` | `AGENTS.md`, `.codex/**`, `.agents/**` |

Codex inventory: `.codex/{ORCHESTRATION.md,config.toml}`, the BRIEF/RESULT contract, three eight-role
fleets, eight role prompts, five hooks, seven integration/audit scripts, settings/handoff examples,
plan/report/memory templates, and all reusable `.agents/skills/**` procedures.

Claude inventory: ten `.claude/agents/*.md` definitions, three fleet manifests plus their README,
four hooks, five prompts, seven scripts, provider settings/state examples, eight skills, and
plan/report/memory templates. `.mcp.json` is the Claude MCP registration.

Never combine the two providers' roles, instructions, state, memory, hooks, or run ledgers. Use a
separate clone/worktree for comparison.

## 4. Shared orchestration runtime — keep while agents are used

| Path | Role |
|---|---|
| `orchestrate` | provider-bound init, adapt, doctor, launch, audit, and run-list entrypoint |
| `.orchestration/launcher.py` | preset/permission resolution, provider lock, adaptation advisor, process lifecycle |
| `.orchestration/isolation.py` | selected-provider isolation check used by doctor |
| `.orchestration/config.local.json.example` | schema seed for ignored local launcher preferences |
| `.orchestration/project_map.json` | this inventory's machine source; optional after adaptation is complete |

## 5. Template-distribution only — review, then remove

| Tracked path | Why it ships | Real-project action |
|---|---|---|
| `docs/orchestration/{CODEX,CLAUDE,MAINTAINERS,PROJECT_MAP}{,.ko}.md` | distribution/user/maintainer documentation | read first; then remove `docs/` or keep as reference |
| `tests/{__init__.py,orchestration/**}` | tests this dual-provider template | remove unless maintaining or modifying the orchestration system |
| `.github/workflows/validate.yml` | template distribution CI | replace with project CI |
| `.orchestration/release_check.py`, `.orchestration/validate_system.py` | dual-provider release validation | remove with template tests, or keep when modifying the control plane |
| `setup.sh` | convenience wrapper for first initialization | optional after `./orchestrate init` |

Removing the unselected provider makes the dual-provider `release-check` inapplicable; the selected
provider's `doctor` remains the runtime check.

## 6. Keep the file, rewrite or truncate its content

| File | Required decision |
|---|---|
| `README.md`, `README.ko.md` | replace the template overview with the project's README; delete an unused language copy |
| `LICENSE` | choose the project's license and copyright holder; never infer this choice |
| `requirements.txt` | keep this single dependency file and replace template-test dependencies with project dependencies |
| `.gitignore` | review data, checkpoint, generated-run, paper, local-state, and secret rules |
| `plan/PRD.md`, `plan/CHECKLIST.md` | populate from user-approved scope and acceptance criteria |
| `run.sh`, `evaluate.sh` | implement reproducible project entrypoints while preserving research gates |

There is intentionally no `requirements-dev.txt`; validation and project dependencies share one
`requirements.txt` until the real project rewrites it.

## 7. Complete tracked inventory and coverage rule

The following patterns partition all paths returned by `git ls-files` (adapt files may also belong to
their functional category):

| Category | Complete path pattern |
|---|---|
| research workspace | `plan/**`, `report/**`, `data/**`, `model/**`, `experiments/**`, `analysis/**`, `functionals/**`, `utils/**`, `run.sh`, `evaluate.sh` |
| Codex core | `AGENTS.md`, `.codex/**`, `.agents/**` |
| Claude core | `CLAUDE.md`, `.claude/**`, `.mcp.json` |
| shared runtime/adaptation | `orchestrate`, `.orchestration/{launcher,isolation,project_map}.py` where applicable, `.orchestration/config.local.json.example` |
| distribution validation | `tests/**`, `.github/**`, `docs/**`, `.orchestration/{release_check,validate_system}.py`, `setup.sh` |
| project-owned rewrite | `README.md`, `README.ko.md`, `LICENSE`, `requirements.txt`, `.gitignore` |

The literal shared paths are `.orchestration/launcher.py`, `.orchestration/isolation.py`, and
`.orchestration/project_map.json` (the compact brace notation above groups unlike extensions only for
readability). Release validation fails if a tracked file is uncategorized, if workspace paths are
ignored, if both language guides drift structurally, or if a second requirements file reappears.

## 8. Safe adaptation workflow

1. Run `./orchestrate adapt <selected-provider> --json` and review every proposed path.
2. Decide the provider removal, template-doc/test/CI removal, license, README languages, dependencies,
   and data/privacy policy with the user.
3. Ask the selected root orchestrator to apply only that approved subset.
4. Run `./orchestrate doctor <selected-provider>` plus project tests.
5. Perform branch, commit, push, or PR operations only when the user explicitly requests each class.
