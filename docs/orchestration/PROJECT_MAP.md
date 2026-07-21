# Project path map — keep, delete, or rewrite in a real research project

One-page guide for turning a clone of this template into your own AI-research project. Both
control planes (Codex and Claude) use the same map; the machine-readable source consumed by
`./orchestrate init` is `.orchestration/project_map.json` — init prints this adaptation
checklist automatically for either backend.

## 1. Research workspace — keep (this is your project)

| Path | Purpose | Lifecycle |
|---|---|---|
| `plan/` | `PRD.md`, `CHECKLIST.md` — agreed with the user, kept by the orchestrator | development-only |
| `report/` | `discussion.md`, `issue.md`, `result.md`, `version.md` — the written discussion space between you and the agent team | development-only |
| `data/` | datasets, splits, preprocessing | development-only |
| `model/` | model source code | develop-and-release |
| `experiments/` | experiment + evaluation code; per-run records in `runs/` | develop-and-release |
| `analysis/` | result-analysis code, notebooks, reading notes | develop-and-release |
| `functionals/` | research functions kept to official-release conventions | develop-and-release |
| `utils/` | utilities kept to official-release conventions | develop-and-release |

## 2. Orchestration core — keep (required for the agent system)

| Path | Role |
|---|---|
| `CLAUDE.md`, `.claude/` | Claude control plane: policy, agents, skills, prompts, hooks, fleets, templates |
| `AGENTS.md`, `.codex/`, `.agents/` | Codex control plane |
| `orchestrate`, `.orchestration/` | launcher, init/doctor, isolation and release checks, project map source |
| `.mcp.json` | literature/Zotero MCP servers |
| `run.sh`, `evaluate.sh`, `setup.sh`, `.gitignore` | gated entry points and hygiene |

## 3. Template-distribution only — safe to delete in a real project

| Path | Why it exists | In your project |
|---|---|---|
| `docs/` | template usage guides (including this file) | delete after reading, or keep as reference |
| `tests/` | validates the template's own orchestration system | delete unless you plan to modify and re-verify the system |
| `.github/` | the template's distribution CI | replace with your project's CI |

## 4. Keep the file, rewrite the content for your project

| File | What to do |
|---|---|
| `README.md` / `README.ko.md` | truncate; write your project's README |
| `LICENSE` | set your license and copyright holder |
| `requirements.txt` | single dependency file — replace with your project's dependencies (drop the pytest lines if you delete `tests/`) |
| `plan/PRD.md`, `plan/CHECKLIST.md` | fill in with the orchestrator on your first session |

## How the agent system helps

`./orchestrate init <backend>` compares the tree against this map and prints the concrete
recommendations (template-only paths still present; adapt-files still carrying template
content). In a session, ask the orchestrator to "apply the PROJECT_MAP adaptation" — it
confirms deletions and rewrites with you before touching anything, and git operations always
require your explicit request.
