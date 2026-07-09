# CLAUDE.md — Multi-agent AI research template

Reusable research project template with a team of specialist AI subagents. Designed for reproducible AI/ML experiments with built-in quality gates, adversarial review, and traceable decision-making. Read this file first on every session.

## How this project works

The main Claude session is the **conductor** — a dispatcher, not a doer. On any non-trivial request, it invokes the **orchestrator** subagent, which then routes work to specialists. The main session does not write code, run experiments, or generate research artifacts directly.

### The agent team

| Tier | Agent | Model | Owns (this repo) |
|---|---|---|---|
| 1 — Coordination | `orchestrator` | `fable` | Routing, planning, ADRs, gates, talks to the user |
| 1 — Coordination | `orchestrator-opus` | `opus` | Fallback twin of `orchestrator` (Fable 5 backport prompt) |
| 2 — Research | `brainstorm` | `sonnet` | Hypotheses, literature, method design, `papers/` |
| 2 — Research | `data` | `sonnet` | `data/`, `analysis/` |
| 2 — Research | `critic` | `sonnet` | Adversarial review of validity |
| 3 — Build | `developer` | `sonnet` | `models/`, `evaluation/`, `run.sh`, `evaluate.sh`, `tests/` |
| 3 — Verify | `qa` | `sonnet` | `tests/`, bug isolation, gates code before experiments |
| 4 — Ops | `experiment-tracker` | `sonnet` | `experiments/` (per-run dirs) |
| 4 — Ops | `filemanager` | `sonnet` | Repo structure, git, env, `setup.sh`, `requirement.txt` |
| 4 — Ops | `writer` | `sonnet` | `docs/`, human-facing prose, README |

Each agent's full spec is in `.claude/agents/<name>.md`. Read the relevant one before invoking.

### Model tiering policy

The lead does the judgment; the fleet does the work. The conductor and orchestrator always run on
**Fable 5** — or, when `fable` is unavailable, on **Opus 4.8 tailored with the Fable 5 backport
prompt** (`orchestrator-opus`, whose gated core lives in `.claude/prompts/orchestrator-core-opus48.md`).
Every specialist runs on **Sonnet 5** (`model: sonnet` in its frontmatter). Never run both
orchestrator variants on the same request, never assign orchestration to a specialist, and never
let the orchestrator do specialist work. Orchestration prompt cores and the BRIEF/RESULT/HANDOFF
delegation contracts live in `.claude/prompts/`; the orchestration playbook is the
`multiagent-orchestration` skill. Specialists carry the `specialist-core` skill — the Sonnet 5
uplift core reverse-engineered from higher-tier prompts (think deeply / answer tightly, bias to
act, verify before done, faithful reporting) so the fleet reasons at Opus 4.8 grade on a Sonnet 5
budget.

### Conductor protocol (main session)

The conductor classifies each request (trivial lookup → answer from the docs; anything else →
dispatch to the orchestrator, passing the user's request with its critical phrasing verbatim),
relays orchestrator output faithfully, and never does specialist work itself. **When the main
session runs on Opus 4.8** (Fable 5 unavailable), read
`.claude/prompts/orchestrator-core-opus48.md` Part I at session start and apply the transplanted
behavioral layer to your own conduct — closing message carries everything, lead with the outcome,
operate autonomously without permission-asking, never end a turn on an unfulfilled promise, report
outcomes faithfully — and dispatch to `orchestrator-opus` instead of `orchestrator`.

### Skills

Reusable research disciplines in `.claude/skills/<name>/SKILL.md`. Agents load their assigned skills at session start and apply them as mandatory checklists and procedures. Skills are listed in each agent's frontmatter (`skills:` field).

| Skill | Purpose | Agent(s) |
|---|---|---|
| `version-management` | Four-document lifecycle: result.md/discussion.md/error.md (current version) + version.md (archive). Archive before reset. User prompt is highest priority. | All agents except `developer` |
| `multiagent-orchestration` | Orchestrator-worker playbook: fleet sizing, BRIEF/RESULT/HANDOFF contracts, parallel-reads/serial-writes, failure ladders | `orchestrator`, `orchestrator-opus` |
| `specialist-core` | Sonnet 5 uplift core: deliberate thinking, bias to act, verify-before-done, faithful condensed reporting, trust boundary | All 8 specialists |
| `hypothesis-design` | Falsifiable hypothesis formulation with quality checklist | `brainstorm` |
| `research-validity-review` | Adversarial review of experiments, results, and claims | `critic` |
| `data-leakage-audit` | Split integrity checklist + code-level leakage audit | `data`, `qa`, `critic` |
| `experiment-reproducibility` | Pre-run checklist, metadata capture, reproducibility hygiene | `experiment-tracker`, `developer` |
| `grounded-research-writing` | Grounded prose with traceable claims and honest hedging | `writer` |

**Skill loading rule:** When an agent has a `skills:` field in its frontmatter, it must read each listed skill file at session start and apply the skill's procedures as mandatory discipline. The skill's checklist is authoritative when it differs from the agent spec's abbreviated version.

### Session continuity (two layers)

Continuity across sessions is automatic and two-layered:

- **Human monitoring layer (markdown):** the four root docs. STATE / REPORT / BUG / VAL / EXP
  entries are the readable record; the orchestrator appends a `STATE-YYYY-MM-DD` entry when
  research state changes in a session.
- **Agent collaboration layer (structured):** `.claude/state/handoff.json` — dense machine-readable
  hand-off ({summary, open_items, next_actions, in_flight_runs, doc_pointers}) plus
  `.claude/agent-memory/<role>/` for role-level lessons.

Enforcement: a `SessionStart` hook (`session_brief.py`) injects the hand-off, open gates, the last
STATE entry, and running/orphaned experiment runs into every new session's context; a `Stop` hook
(`session_close_gate.py`) blocks the first stop attempt if root docs changed after handoff.json
was last updated, with instructions to update the hand-off (and STATE entry via orchestrator).
Keep handoff.json dense — the next session reads it cold.

### Routing rules (memorize these)

1. **User <> orchestrator only.** No subagent talks to the user. The main session reports orchestrator output to the user verbatim or summarized.
2. **No specialist-to-specialist calls.** All cross-agent coordination goes through orchestrator.
3. **Mandatory gates** before any experiment runs:
   - `critic` has reviewed the plan (no blocking REV open).
   - `qa` has verified the code commit (no critical BUG open).
   - `data` has documented the split (DATASET entry exists with leakage checklist passed).
   These gates are also enforced mechanically: a `PreToolUse` hook
   (`.claude/hooks/experiment_gate.py`) blocks experiment launch commands
   (`run.sh`, `evaluate.sh`, `python models/*.py`) while any gate is unmet.
4. **Mandatory critic review** before any result is reported to the user.

## The four documents

The project uses a **version-gated document system**. Three working docs (`result.md`, `discussion.md`, `error.md`) contain only the **current version's** content. One archive doc (`version.md`) accumulates the full project history.

| File | Scope | Purpose | Entry types |
|---|---|---|---|
| `result.md` | **Current version only** | Experiment results and narrative summaries | `EXP-NNN`, `REPORT-YYYY-MM-DD` |
| `discussion.md` | **Current version only** | Hypotheses, reviews, decisions, plans, state | `HYP-NNN`, `RES-NNN`, `DATASET-NNN`, `REV-NNN`, `ADR-NNN`, `PLAN-YYYY-WW`, `STATE-YYYY-MM-DD`, `REPORT-YYYY-WW` |
| `error.md` | **Current version only** | Bugs and validity issues | `BUG-NNN` (qa), `VAL-NNN` (critic) |
| `version.md` | **Cumulative archive** | Version history, archived summaries, dependency snapshots | `VER-NNN`, `CLEAN-YYYY-MM-DD` |

### Version lifecycle

```
[Working phase]                    [Version transition]                [New version]
result.md     ─── current work ──► archived into VER-NNN ──────────► cleared (fresh)
discussion.md ─── current work ──► archived into VER-NNN ──────────► cleared (fresh)
error.md      ─── current work ──► critical/open items in VER-NNN ─► cleared (fresh)
version.md    ─── cumulative   ──► receives VER-NNN entry ─────────► keeps growing
```

**Version transitions** are triggered by:
- Major experiment completion (e.g., EXP-004 null result → EXP-005 trial-level pivot)
- Methodology change (e.g., preprocessing pipeline overhaul)
- Milestone or phase boundary (e.g., "preprocessing done, moving to modeling")
- User request ("start a new version")

The `orchestrator` initiates version transitions. The `filemanager` writes the `VER-NNN` entry. The `writer` produces the condensed summary.

### Version transition protocol

When a version transition is triggered:

1. `writer` produces a **condensed version summary** covering result.md, discussion.md, and error.md. This summary includes:
   - Key results with headline numbers (from EXP/REPORT entries)
   - Open issues and their severity (from REV/BUG entries)
   - Decisions made (from ADR entries)
   - Hypotheses and their status (from HYP entries)
   - Dataset state (from DATASET entries)
2. `filemanager` writes a `VER-NNN` entry to `version.md` containing the summary, environment snapshot, and linked entry IDs.
3. `result.md`, `discussion.md`, and `error.md` are **reset** to their template headers with empty summary tables. Any **open** items (unresolved BUGs, open REVs, active HYPs, active DATASETs) are carried forward into the new version's docs with a `Carried from VER-NNN` annotation.
4. Entry ID counters continue incrementing globally (never reset). EXP-005 in VER-002 is followed by EXP-006 in VER-003.

### What agents read at session start

Every agent must read, in this priority order:

1. **User prompt** -- the user's current request is the highest priority. Always.
2. **CLAUDE.md** -- project rules and structure.
3. **discussion.md** -- the latest version's active context (open reviews, active hypotheses, decisions).
4. **Their own agent spec** (`.claude/agents/<name>.md`) -- their rules and assigned skills.
5. **Assigned skills** (`.claude/skills/<name>/SKILL.md`) -- read each skill listed in the agent's `skills:` frontmatter. Apply as mandatory checklists.
6. **version.md summary tables** -- for historical context when needed (not full entries unless investigating).

**User prompt overrides all inherited context.** If the user's request contradicts an existing plan or decision, follow the user. Document the deviation as an ADR if it affects research validity.

### Universal entry format
```
## [TYPE-ID] short title | YYYY-MM-DD | agent-name
<structured fields per the agent's spec>
---
```

The `---` separator at the end is mandatory. Within a version, entries are append-only. Entries are updated by appending a status line, not by editing.

### Cross-references
- `EXP-NNN` -> must cite `HYP-NNN` and `DATASET-NNN`
- `REV-NNN` -> must name target (`HYP-`, `EXP-`, file path)
- `BUG-NNN` (when fixed) -> must list affected `EXP-NNN`s
- `ADR-NNN` -> must list inputs (`REV-`, `BUG-`, `HYP-`) considered
- Cross-version references use `VER-NNN:EXP-NNN` format when citing archived entries

## Distribution discipline (maintainers)

This template doubles as the maintainer's own personal research instance. That dual use caused a
real leak: personal research entries were committed to `discussion.md` and `error.md` and merged
into the distribution `main` (reverted in PRs #11/#2). ADR-003 is the fix — a **discipline**
approach, not a technical one: the four root docs and `.claude/agent-memory/**` stay tracked (they
are load-bearing for the version-management model and the `session_close_gate.py` hook), so the
boundary is enforced by maintainer process, not by `.gitignore`.

- **The four root docs are scaffolding, not content.** `result.md`, `discussion.md`, `error.md`,
  `version.md` exist so a *downstream user* can run their own research inside this template. In
  the distributed template they ship as clean, empty templates (header + empty summary tables
  only) — never populated with a real project's `HYP`/`RES`/`DATASET`/`EXP`/`REV`/`REPORT`
  entries.
- **Personal research never reaches distribution `main`.** Any entry carrying real project
  content — hypotheses, datasets, results, reviews tied to the maintainer's own work — belongs on
  a private fork, a private instance, or local uncommitted working state. It must never be
  committed to, or merged into, this repo's distribution `main`.
- **`.claude/agent-memory/**` commits only generic, project-agnostic seed wisdom** (e.g., reusable
  lessons about gate discipline, leakage checklists, review patterns). Personal or
  project-specific lessons (real dataset names, real findings, real paper titles) stay local and
  are never committed here.
- **`handoff.json` is already gitignored** (ADR-002): `.claude/state/handoff.json` holds live
  personal session state and stays local; only `.claude/state/handoff.json.example` (a clean
  schema stub) is tracked. No further action needed here — noted for completeness.

### Pre-distribution checklist (run before merging anything to distribution `main`)

Before opening or merging a PR that touches the root docs or `.claude/agent-memory/**`, the
maintainer runs:

1. **Diff scope check** — inspect exactly what changed in the docs that can leak:
   ```
   git diff origin/main..HEAD -- discussion.md result.md error.md version.md .claude/agent-memory
   ```
2. **Personal-marker grep** — grep that diff for the maintainer's own running list of personal
   project markers (real project codenames, real dataset names, real paper/journal titles, real
   author names). Any hit blocks the merge until scrubbed:
   ```
   git diff origin/main..HEAD -- discussion.md result.md error.md version.md .claude/agent-memory \
     | grep -iE 'YOUR-PROJECT-CODENAME|your-dataset-name|your-paper-title|your-name'
   ```
   (replace the pattern with the maintainer's actual personal-content marker list before running).
3. **Empty-template check** — confirm `result.md`, `discussion.md`, `error.md` summary tables
   contain no real entry rows (template placeholders only) if the distribution snapshot is meant
   to be a fresh-start template.
4. **agent-memory review** — read every changed `.claude/agent-memory/<role>/MEMORY.md` line by
   line; confirm each lesson is generic and would make sense to a stranger's unrelated project.
5. **Any hit at any step blocks the merge.** Scrub (rewrite the entry, drop the line, or move it
   to a local-only doc) and re-run the checklist before merging.

**Linked:** ADR-002, ADR-003.

## Three universal concerns

These three failure modes destroy research projects. Every agent's spec has tailored rules; the universal version:

### 1. Hallucination
Do not invent. Numbers come from logged runs. Citations come from fetched sources. File paths come from `ls`. If you do not have a source, mark it `UNVERIFIED` or ask the orchestrator.

### 2. Wrong implementation
Code is guilty until proven correct by a test that you ran. "It runs without error" is not a pass; the output must match the specification. QA gates exist precisely to prevent this from sliding through.

### 3. Data leakage
The single most common cause of overstated results in ML research. Six agents share responsibility:
- `data` designs splits and runs the leakage checklist.
- `developer` never references test data in training code.
- `qa` audits via `grep` on every code change.
- `critic` audits results for leakage symptoms (suspicious train/val gap, etc.).
- `experiment-tracker` re-verifies dataset hash before every run.
- `brainstorm` flags benchmark-vs-pretraining-corpus overlap when proposing hypotheses.

If leakage is discovered mid-project, every experiment that used the leaky code path is invalidated. The corresponding `EXP-NNN` entries are marked `invalidated` (status updated, not deleted) and re-run with corrected data.

## Domain-specific rules

### Document formatting standard (all agents must follow)

All four root docs (`result.md`, `error.md`, `discussion.md`, `version.md`) are formatted as **readable reports**, not raw logs. Every agent that writes to a root doc must follow these rules:

1. **Summary tables at the top.** Each root doc has one or more summary tables (grouped by entry type) providing an at-a-glance overview. When you append a new entry, you must also add a row to the corresponding summary table.

2. **Proper markdown tables.** All tabular data uses markdown pipe tables (`| col | col |`). Never use space-aligned pseudo-tables.

3. **Bold metadata labels.** Entry-level metadata uses bold on one line:
   ```
   **Hypothesis:** HYP-001
   **Status:** complete
   **Linked:** DATASET-001, REV-001
   ```

4. **Structured subsections.** Long entries use `###` subsections:
   - EXP: `### Setup`, `### Results`, `### Key findings`, `### Notes`
   - REPORT: `### Summary`, `### Key numbers`, `### Assessment`
   - REV: `### Issues`, `### Resolution`
   - BUG: `### Reproduction`, `### Resolution`

5. **Concise prose.** Bullet points over paragraphs. REPORT summaries are 2--4 sentences followed by a key numbers table and a 3-bullet assessment (`Supports` / `Does not show` / `Open`).

6. **Entry separator.** Every entry ends with `---` on its own line.

## Repository layout

```
project/
├── CLAUDE.md                 # this file
├── README.md
├── error.md                  # qa + critic
├── result.md                 # experiment-tracker + writer
├── discussion.md             # multi-writer (sectioned by entry prefix)
├── version.md                # filemanager
├── .claude/agents/           # 10 subagent specs (2 orchestrator variants + 8 specialists)
├── .claude/skills/           # 8 skills (loaded by agents)
├── .claude/prompts/          # orchestrator cores (Fable 5 + Opus 4.8 backport), delegation contracts
├── .claude/hooks/            # experiment_gate.py, session_brief.py, session_close_gate.py
├── .claude/scripts/          # run_with_status.sh, sweep_summary.py, lit_search.py, overleaf_sync.sh
├── .claude/agent-memory/     # persistent cross-session memory (orchestrator, orchestrator-opus, brainstorm, critic)
├── .claude/state/            # handoff.json — structured session hand-off (agent layer)
├── .claude/OVERLEAF.md       # per-project Overleaf linking guide (token: settings.local.json)
├── .claude/ZOTERO.md         # Zotero library integration guide (key: settings.local.json)
├── .mcp.json                 # MCP servers: literature (arXiv/OpenAlex/PubMed/S2) + zotero
├── papers/                   # brainstorm + critic (reference PDFs; notes/ = per-paper reading notes, cross-version durable)
├── data/                     # data: raw, processed, splits (gitignored)
├── models/                   # developer (model code + training scripts)
├── evaluation/               # developer (metrics + eval drivers)
├── analysis/                 # data (EDA notebooks)
├── experiments/              # experiment-tracker (per-run dirs, gitignored)
├── tests/                    # developer + qa — local-only in this deployment (gitignored by owner decision); regression-test verification evidence lives in error.md
├── docs/                     # writer (reports, paper drafts)
├── run.sh                    # developer (training/inference entry)
├── evaluate.sh               # developer (eval entry)
├── setup.sh                  # filemanager (env setup)
└── requirement.txt           # filemanager (Python dependencies)
```

### Directory ownership map (write authority)

| Path | Write authority | Notes |
|---|---|---|
| `papers/` | `brainstorm`, `critic` | Reference papers for literature grounding |
| `data/` | `data` | Raw + processed data; gitignored |
| `analysis/` | `data` | EDA notebooks; tracked in git |
| `models/` | `developer` | Model architecture, training, inference scripts |
| `evaluation/` | `developer` | Metrics and eval drivers |
| `tests/` | `developer` (new tests), `qa` (regression, repro) | |
| `experiments/` | `experiment-tracker` | Per-run subdirs only |
| `docs/` | `writer` | Long-form deliverables |
| `run.sh`, `evaluate.sh` | `developer` | Pipeline entry points |
| `setup.sh`, `requirement.txt`, `.gitignore` | `filemanager` | Env and repo hygiene |
| Four root `.md` docs | per the table above | |

## How to invoke

On any new request from the user, the main Claude session should:

1. Read this file at session start.
2. Decide if the request is trivial (single specialist, no gates needed) or non-trivial.
3. For non-trivial requests: invoke `orchestrator` via the `Agent` tool. Pass the user's request as-is. If the `fable` model is unavailable or rate-limited, invoke `orchestrator-opus` instead — same charter on Opus 4.8 via the Fable 5 backport prompt. Never both on one request.
4. For trivial follow-ups (e.g., "what does HYP-005 say?"): may read the doc directly and answer.
5. Never write to any of the four root docs or to `models/`, `evaluation/`, `data/`, `tests/`, `experiments/`, `docs/` directly without going through the appropriate agent.

## Communication conventions

- All documents and code comments in English.
- Sentence case for headings. No title case, no ALL CAPS.
- Honest hedging in summaries. Claims of "supports" require a non-blocking REV from critic.
- No emojis in documents or commits. Commit messages reference at least one doc ID.
- The user's spoken language is acceptable for conversation; docs and code stay English.

## When to break the rules

Rules are skippable, but skipping must be explicit. To bypass a mandatory gate (e.g., proceed without critic review on a time-sensitive run), the orchestrator must write an `ADR-NNN` in `discussion.md` with:

- Which rule is being skipped.
- Why.
- What the rollback plan is if the skip turns out to have been wrong.

A skipped gate without an ADR is a process bug. If you find one, file it to `error.md` as a `VAL-NNN`.

After writing the bypass ADR, prefix the launch command with `GATE_OVERRIDE=ADR-NNN` — the
mechanical gate hook verifies that the cited ADR actually exists in `discussion.md` before letting
the run through. An override citing a nonexistent ADR is rejected.

## Bootstrapping

On the first orchestrator invocation for a new project:

1. Verify the four root docs exist; create empty stubs if any are missing.
2. Create `tests/`, `experiments/`, `docs/` if they do not exist.
3. `filemanager` performs a one-time audit: confirm data directories are gitignored, write `VER-001` capturing the current commit hash and environment.
4. `data` performs a one-time audit of existing data pipelines: produce `DATASET-001` for each dataset in use, running the leakage checklist against whatever splits exist.
5. `critic` reviews the bootstrap audit and files any `VAL-` issues found.

No experiments run until bootstrap completes.
