# CLAUDE.md — Multi-agent AI research template

Reusable research project template with a team of specialist AI subagents. Designed for reproducible AI/ML experiments with built-in quality gates, adversarial review, and traceable decision-making. Read this file first on every session.

## How this project works

The main Claude session is the **orchestrator** — it plans, routes work to specialist subagents,
enforces the quality gates, and reports to the user. Use direct topology by default: the main
session orchestrates specialists itself and does not add a dedicated orchestrator hop merely
because a task is non-trivial (each hop costs a full lead-model context and a user-clarification
round trip). The main session still does not write code, run experiments, or generate research
artifacts directly — every artifact comes from a specialist dispatch.

### The agent team

| Tier | Agent | Model | Effort | Owns (this repo) |
|---|---|---|---|---|
| 1 — Coordination | `orchestrator` | `fable` | `xhigh` | Dedicated-orchestrator option (isolation); same charter the main session runs directly |
| 1 — Coordination | `orchestrator-opus` | `opus` | `xhigh` | Fallback twin of `orchestrator` (Fable 5 backport prompt) |
| 2 — Research | `brainstorm` | `sonnet` | `high` | Hypotheses, literature (Zotero + MCP), method design |
| 2 — Research | `data` | `sonnet` | `medium` | `data/`, `analysis/` |
| 2 — Research | `critic` | `sonnet` | `max` | Adversarial review of validity |
| 3 — Build | `developer` | `sonnet` | `medium` | `model/`, `experiments/`, `functionals/`, `utils/`, `run.sh`, `evaluate.sh`, `tests/` |
| 3 — Verify | `qa` | `sonnet` | `high` | `tests/`, bug isolation, gates code before experiments |
| 4 — Ops | `experiment-tracker` | `sonnet` | `low` | `experiments/runs/` (per-run dirs) |
| 4 — Ops | `filemanager` | `sonnet` | `low` | Repo structure, git, env, `setup.sh`, dependency files |
| 4 — Ops | `writer` | `sonnet` | `medium` | `docs/`, human-facing prose, README |

Each agent's full spec is in `.claude/agents/<name>.md`. Read the relevant one before invoking.

The Model/Effort columns show the default `quality` fleet (authoritative source:
`.claude/fleets/quality.json`, which must match the frontmatter pins — drift is test-enforced).
Cheaper fleets are selectable per session: `./orchestrate claude --preset balanced|fast`, with
per-role overrides `--role ROLE=PRESET|MODEL@EFFORT`. The launcher enforces research-gate floors
(critic/qa at least sonnet@high, data at least sonnet@medium, lead model fable or opus) so no
preset weakens verification — see `.claude/fleets/README.md`.

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

Model choice is one axis; reasoning depth is a second, independent one. Each agent's frontmatter
also pins an explicit `effort:` level — `low | medium | high | xhigh | max`, per the official
subagent frontmatter documentation (https://code.claude.com/docs/en/subagents.md, "Supported
frontmatter fields") — which overrides the session's inherited effort for that agent alone; the
table above lists each agent's pinned level. The tiering principle: reasoning depth scales with
what the charter demands and the cost of a missed error at that station, discounted by how often
the agent is invoked and by how much of its discipline is already carried by a mandatory skill
checklist. Available effort levels depend on the underlying model and are not exhaustively
documented per model, so a pinned level is a request the harness may adapt, not a guarantee.

### Orchestration protocol (main session)

The main session runs the orchestrator charter directly — single hop. Classify each request
(trivial lookup → answer from the docs; anything else → plan, dispatch specialists with full
BRIEFs, enforce gates, synthesize), applying the `multiagent-orchestration` skill and the
orchestrator core discipline: on Fable 5 read `.claude/prompts/orchestrator-core-fable5.md`; **when
the main session runs on Opus 4.8** (Fable 5 unavailable), read
`.claude/prompts/orchestrator-core-opus48.md` and run its Gate 0–8 sequence on every request. Read
`.claude/agent-memory/orchestrator/MEMORY.md` at session start; append durable routing lessons.

Spawn the dedicated `orchestrator` subagent (or `orchestrator-opus` on Opus 4.8 — never both on one
request) only when isolation is worth a full extra lead-model context: the user explicitly asks for
it, or the main-session context is too long or polluted to orchestrate reliably. In that case pass
the user's request with its critical phrasing verbatim and relay the output faithfully.

### Skills

Reusable research disciplines in `.claude/skills/<name>/SKILL.md`. Skills listed in an agent's frontmatter (`skills:` field) arrive preloaded in the agent's context at spawn — no Read needed — and apply as mandatory checklists and procedures.

| Skill | Purpose | Agent(s) |
|---|---|---|
| `version-management` | Four-document lifecycle: report/result.md/discussion.md/error.md (current version) + report/version.md (archive). Archive before reset. User prompt is highest priority. | All agents except `developer` |
| `multiagent-orchestration` | Orchestrator-worker playbook: fleet sizing, BRIEF/RESULT/HANDOFF contracts, parallel-reads/serial-writes, failure ladders | `orchestrator`, `orchestrator-opus` |
| `specialist-core` | Sonnet 5 uplift core: deliberate thinking, bias to act, verify-before-done, faithful condensed reporting, trust boundary | All 8 specialists |
| `hypothesis-design` | Falsifiable hypothesis formulation with quality checklist | `brainstorm` |
| `research-validity-review` | Adversarial review of experiments, results, and claims | `critic` |
| `data-leakage-audit` | Split integrity checklist + code-level leakage audit | `data`, `qa`, `critic` |
| `experiment-reproducibility` | Pre-run checklist, metadata capture, reproducibility hygiene | `experiment-tracker`, `developer` |
| `grounded-research-writing` | Grounded prose with traceable claims and honest hedging | `writer` |

**Skill loading rule:** Skills in an agent's `skills:` frontmatter arrive preloaded — do not re-read them; that is a wasted tool call. Apply each preloaded skill's procedures as mandatory discipline. The skill text is authoritative when it differs from the agent spec's abbreviated version.

### Session continuity (two layers)

Continuity across sessions is automatic and two-layered:

- **Human monitoring layer (markdown):** the four Claude research docs. STATE / REPORT / BUG / VAL / EXP
  entries are the readable record; the orchestrator appends a `STATE-YYYY-MM-DD` entry when
  research state changes in a session.
- **Agent collaboration layer (structured):** `.claude/state/handoff.json` — dense machine-readable
  hand-off ({summary, open_items, next_actions, in_flight_runs, doc_pointers}) plus
  `.claude/agent-memory/<role>/` for role-level lessons.

Enforcement: a `SessionStart` hook (`session_brief.py`) injects the hand-off, open gates, the last
STATE entry, and running/orphaned experiment runs into every new session's context; a `Stop` hook
(`session_close_gate.py`) blocks the first stop attempt if Claude research docs changed after handoff.json
was last updated, with instructions to update the hand-off (and STATE entry via orchestrator).
Keep handoff.json dense — the next session reads it cold.

### Routing rules (memorize these)

1. **User <> orchestrator (= main session) only.** No subagent talks to the user. When a dedicated orchestrator subagent is used, the main session relays its output verbatim or summarized.
2. **No specialist-to-specialist calls.** All cross-agent coordination goes through the orchestrator (the main session, or the dedicated subagent when spawned).
3. **Mandatory gates** before any experiment runs:
   - `critic` has reviewed the plan (a REV records `**Gate:** passed`; no blocking REV open).
   - `qa` has verified the code commit (a QA entry records `**Gate:** passed`; no critical BUG open).
   - `data` has documented the split (a DATASET entry records `**Leakage audit:** passed`).
   These gates are also enforced mechanically: a `PreToolUse` hook
   (`.claude/hooks/experiment_gate.py`) blocks experiment launch commands
   (`run.sh`, `evaluate.sh`, `python model/*.py`) while any gate is unmet.
4. **Mandatory critic review** before any result is reported to the user.

## The four documents

The project uses a **version-gated document system**. Three working docs (`report/result.md`, `report/discussion.md`, `report/error.md`) contain only the **current version's** content. One archive doc (`report/version.md`) accumulates the full project history.

| File | Scope | Purpose | Entry types |
|---|---|---|---|
| `report/result.md` | **Current version only** | Experiment results and narrative summaries | `EXP-NNN`, `REPORT-YYYY-MM-DD` |
| `report/discussion.md` | **Current version only** | Hypotheses, reviews, QA attestations, decisions, plans, state | `HYP-NNN`, `RES-NNN`, `DATASET-NNN`, `REV-NNN`, `QA-NNN`, `ADR-NNN`, `PLAN-YYYY-WW`, `STATE-YYYY-MM-DD`, `REPORT-YYYY-WW` |
| `report/error.md` | **Current version only** | Bugs and validity issues | `BUG-NNN` (qa), `VAL-NNN` (critic) |
| `report/version.md` | **Cumulative archive** | Version history, archived summaries, dependency snapshots | `VER-NNN`, `CLEAN-YYYY-MM-DD` |

### Version lifecycle

```
[Working phase]                    [Version transition]                [New version]
report/result.md     ─── current work ──► archived into VER-NNN ──────────► cleared (fresh)
report/discussion.md ─── current work ──► archived into VER-NNN ──────────► cleared (fresh)
report/error.md      ─── current work ──► critical/open items in VER-NNN ─► cleared (fresh)
report/version.md    ─── cumulative   ──► receives VER-NNN entry ─────────► keeps growing
```

**Version transitions** are triggered by:
- Major experiment completion (e.g., EXP-004 null result → EXP-005 trial-level pivot)
- Methodology change (e.g., preprocessing pipeline overhaul)
- Milestone or phase boundary (e.g., "preprocessing done, moving to modeling")
- User request ("start a new version")

The `orchestrator` initiates version transitions. The `filemanager` writes the `VER-NNN` entry. The `writer` produces the condensed summary.

### Version transition protocol

When a version transition is triggered:

1. `writer` produces a **condensed version summary** covering report/result.md, report/discussion.md, and report/error.md. This summary includes:
   - Key results with headline numbers (from EXP/REPORT entries)
   - Open issues and their severity (from REV/BUG entries)
   - Decisions made (from ADR entries)
   - Hypotheses and their status (from HYP entries)
   - Dataset state (from DATASET entries)
2. `filemanager` writes a `VER-NNN` entry to `report/version.md` containing the summary, environment snapshot, and linked entry IDs.
3. `report/result.md`, `report/discussion.md`, and `report/error.md` are **reset** to their template headers with empty summary tables. Any **open** items (unresolved BUGs, open REVs, active HYPs, active DATASETs) are carried forward into the new version's docs with a `Carried from VER-NNN` annotation.
4. Entry ID counters continue incrementing globally (never reset). EXP-005 in VER-002 is followed by EXP-006 in VER-003.

### What agents read at session start

Every agent must read, in this priority order:

1. **User prompt** -- the user's current request is the highest priority. Always.
2. **CLAUDE.md** -- project rules and structure.
3. **report/discussion.md** -- summary tables always (open reviews, active hypotheses, decisions at a glance); full entries only for the doc IDs the BRIEF names or the write will touch. Do not read the whole file per dispatch.
4. **Their own agent spec** (`.claude/agents/<name>.md`) -- their rules and assigned skills.
5. **Assigned skills** -- already preloaded in context via the `skills:` frontmatter; do not re-read the files. Apply as mandatory checklists.
6. **report/version.md summary tables** -- for historical context when needed (not full entries unless investigating).

Subagents receive CLAUDE.md automatically in their injected context — items 1, 2,
4, and 5 arrive without tool calls; only report/discussion.md (and report/version.md when needed) costs a Read.

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

Maintainer process lives in `docs/orchestration/MAINTAINERS.md` (kept out of this file so it is not
injected into every agent context). The one rule every session must know: **personal research and
development history never reach the distribution `main`.** Live state is gitignored structurally
(`report/`, `.claude/agent-memory/`, `.claude/state/handoff.json`); the distribution
ships only the clean seeds in `.claude/templates/`. When the user has explicitly authorized release
or PR work, run the pre-distribution checklist in `docs/orchestration/MAINTAINERS.md`.

### Git authority boundary

Without an explicit user request for the corresponding action, do not stage or unstage; create,
rename, delete, or switch branches; create, amend, squash, or rewrite commits; fetch, pull, push, or
force-push; open, edit, close, or approve pull requests; merge, rebase, cherry-pick, stash, reset,
restore, tag, or publish a release. Do not run another Git command that mutates the index, working
tree, refs, history, or a remote. Implementation, testing, review, documentation, and release
preparation authorize ordinary working-tree edits only. One Git permission never implies another.

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

All four Claude research docs (`report/result.md`, `report/error.md`, `report/discussion.md`, `report/version.md`) are formatted as **readable reports**, not raw logs. Every agent that writes to a Claude research doc must follow these rules:

1. **Summary tables at the top.** Each Claude research doc has one or more summary tables (grouped by entry type) providing an at-a-glance overview. When you append a new entry, you must also add a row to the corresponding summary table.

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
├── CLAUDE.md                 # this file (injected into every agent context)
├── plan/                     # development-only: PRD.md, CHECKLIST.md (orchestrator <-> user)
├── report/                   # development-only: report/discussion.md (hypotheses, reviews, decisions),
│                             #   report/error.md (issue log), report/result.md, report/version.md —
│                             #   the written collaboration space between the user and the agent team
├── data/                     # development-only: datasets, splits, preprocessing (data agent; gitignored)
├── model/                    # develop-and-release: model source code (developer)
├── experiments/              # develop-and-release: experiment + evaluation code (developer);
│                             #   runs/ = per-run records (experiment-tracker; gitignored)
├── analysis/                 # develop-and-release: result-analysis code and notebooks (data)
├── functionals/              # develop-and-release: research functions kept to official-release conventions (developer)
├── utils/                    # develop-and-release: utilities kept to official-release conventions (developer)
├── docs/                     # long-form deliverables and template docs (writer)
├── run.sh / evaluate.sh      # pipeline entry points (developer; experiment-gated)
├── setup.sh / requirements*.txt  # environment (filemanager)
├── .claude/                  # agents, skills, prompts, hooks, fleets, templates, state, memory
└── .mcp.json                 # MCP servers: literature (arXiv/OpenAlex/PubMed/S2) + zotero
```

The workspace splits into **development-only** dirs (`plan/`, `report/`, `data/` —
planning, written discussion, private data, and reading material do not ship with a research-code
release) and **develop-and-release** dirs (`model/`, `experiments/`, `analysis/`, `functionals/`,
`utils/`, `tests/`, `docs/` — publishable code, verification, and deliverables). `functionals/` and
`utils/` follow official AI-research release conventions: typed, documented, importable, and free of
experiment-local state.

### Directory ownership map (write authority)

| Path | Write authority | Lifecycle | Notes |
|---|---|---|---|
| `plan/` | `orchestrator` | development-only | PRD and checklist, agreed with the user |
| `report/*.md` | per the research-state table above | development-only | the user <-> agent-team discussion space; entry-typed, append-only |
| `data/` | `data` | development-only | raw + processed data; gitignored |
| `model/` | `developer` | develop-and-release | model architecture, training, inference source |
| `experiments/` | `developer` (code), `experiment-tracker` (`runs/` only) | develop-and-release | evaluation drivers + experiment code; per-run records under `runs/` |
| `analysis/` | `data` | develop-and-release | EDA and result-analysis notebooks/code |
| `functionals/` | `developer` | develop-and-release | official-convention research functions |
| `utils/` | `developer` | develop-and-release | official-convention utilities |
| `tests/` | `developer` (new), `qa` (regression) | develop-and-release | reusable verification and research regression tests |
| `docs/` | `writer` | develop-and-release | long-form deliverables |
| `run.sh`, `evaluate.sh` | `developer` | develop-and-release | experiment-gated entry points |
| `setup.sh`, `requirements*.txt`, `.gitignore` | `filemanager` | develop-and-release | env and repo hygiene |

## How to invoke

On any new request from the user, the main Claude session should:

1. Read this file at session start (injected automatically; do not re-read).
2. Decide if the request is trivial (lookup, no gates) or non-trivial.
3. For non-trivial requests: orchestrate directly — plan per the orchestrator core, dispatch the
   right specialists via the `Agent` tool with full BRIEFs, enforce gates, synthesize. Spawn the
   dedicated `orchestrator` subagent (or `orchestrator-opus` on Opus 4.8; never both on one
   request) only under the isolation conditions in "Orchestration protocol", passing the user's
   request as-is.
4. For trivial follow-ups (e.g., "what does HYP-005 say?"): may read the doc directly and answer.
5. The main session may write `report/discussion.md` orchestration entries (PLAN / ADR / STATE) as the
   orchestrator; everything else — the other Claude research docs, `model/`, `experiments/`, `functionals/`, `utils/`, `data/`,
   `tests/`, `experiments/runs/`, `docs/` — goes through the owning specialist.

## Communication conventions

- Runtime research documents and code comments are in English; public distribution guides may have a
  paired `.ko.md` translation.
- Sentence case for headings. No title case, no ALL CAPS.
- Honest hedging in summaries. Claims of "supports" require a non-blocking REV from critic.
- No emojis in documents or commits. Commit messages reference at least one doc ID.
- The user's spoken language is acceptable for conversation; docs and code stay English.

## PR and issue conventions

The full grammar (branch `type/N-kebab-scope`, PR title `type: lowercase summary (#N)`, closing
keywords in bodies only, the mandatory tabled description skeleton) lives in
`docs/orchestration/MAINTAINERS.md`.
Read it before any branch, PR, or issue work; every non-trivial PR references at least one issue
or doc ID.

## When to break the rules

Rules are skippable, but skipping must be explicit. To bypass a mandatory gate (e.g., proceed without critic review on a time-sensitive run), the orchestrator must write an `ADR-NNN` in `report/discussion.md` with:

- Which rule is being skipped.
- Why.
- What the rollback plan is if the skip turns out to have been wrong.

A skipped gate without an ADR is a process bug. If you find one, file it to `report/error.md` as a `VAL-NNN`.

After writing the bypass ADR, prefix the launch command with `GATE_OVERRIDE=ADR-NNN` — the
mechanical gate hook verifies that the cited ADR exists and contains Context, Decision,
Consequences, and Rollback fields before letting the run through. A nonexistent or incomplete ADR
is rejected.

## Bootstrapping

On the first orchestrator invocation for a new project:

1. Verify the four Claude research docs exist; create empty stubs if any are missing.
2. Create `tests/`, `experiments/runs/`, `docs/` if they do not exist.
3. `filemanager` performs a one-time audit: confirm data directories are gitignored, write `VER-001` capturing the current commit hash and environment.
4. `data` performs a one-time audit of existing data pipelines: produce `DATASET-001` for each dataset in use, running the leakage checklist against whatever splits exist.
5. `critic` reviews the bootstrap audit and files any `VAL-` issues found.

No experiments run until bootstrap completes.
