# AI Research Orchestration

**English** | [한국어](README.ko.md)

A source distribution for running AI/ML research through explicit specialist roles, evidence
contracts, and review gates. It covers literature review, hypothesis design, data integrity,
implementation, independent QA, experiments, analysis, references, and paper review.

This repository contains two independent provider implementations. Select exactly one for a research
checkout; they do not collaborate or share research state. The launcher refuses cross-provider use
after initialization, so comparisons require separate clones or worktrees.

## Choose a provider

| Provider | Coordination | User guide |
|---|---|---|
| Codex | the root session is intended to coordinate direct specialists | [Codex guide](docs/orchestration/CODEX.md) |
| Claude Code | provider-owned lead-agent routing and specialists | [Claude guide](docs/orchestration/CLAUDE.md) |

Maintainer and release procedures are in the [maintainer guide](docs/orchestration/MAINTAINERS.md).
Korean guides are available beside each English document.

## Quick start

Use a dedicated checkout and initialize its default provider:

For Codex
```bash
git clone <this-repo> my-research
cd my-research
./orchestrate init codex       # or: ./orchestrate init claude
./orchestrate doctor codex     # use the same provider
./orchestrate codex --preset quality
```
For CLAUDE, you can type `./orchestrate claude --preset quality` analogous to codex

Cheaper presets are selectable per session — `./orchestrate claude|codex --preset balanced|fast`

`init` creates provider-private local state, completes any missing workspace seeds, and binds the
checkout to that provider. It will refuse the other provider in the same checkout.

`doctor` validates files, configuration, CLI capabilities, and local MCP handshakes. It is not proof
that a native specialist received the selected role, BRIEF, or RESULT contract. Before substantive
research, run the provider guide's one-specialist smoke test and inspect the returned runtime identity
and evidence.

## Project layout

| Area | Paths | Purpose |
|---|---|---|
| research development | `plan/`, `report/`, `data/` | PRD/checklist, user-agent research records, datasets and preprocessing assets |
| develop and release | `model/`, `experiments/`, `analysis/`, `functionals/`, `utils/` | model source, experiment code/configs, analysis, reusable functions and utilities |
| generated runs | `experiments/runs/` | ignored logs, checkpoints, metrics, and run status |

`plan/`, `report/`, and `data/` are intentionally not blanket-ignored. Commit only material that the
project's privacy, licensing, and size policy permits.

## The agent team

Ten roles: a lead session (or a spawnable dedicated orchestrator) plus eight research/build/ops
specialists, each with an owned area, a pinned default model, and a pinned reasoning effort. The
table below is the `quality` fleet, the system default.

| Tier | Agent | Model | Effort | Owns |
|---|---|---|---|---|
| 1 — coordination | orchestrator | Fable 5 (or Opus 4.8 + backport prompt) | xhigh | lead routing, gates, synthesis |
| 1 — coordination | orchestrator-opus | Opus 4.8 | xhigh | fallback twin of orchestrator |
| 2 — research | brainstorm | Sonnet 5 | high | hypotheses, literature, method design |
| 2 — research | data | Sonnet 5 | medium | `data/`, `analysis/` |
| 2 — research | critic | Sonnet 5 | max | adversarial review of validity |
| 3 — build | developer | Sonnet 5 | medium | `model/`, `experiments/`, `functionals/`, `utils/`, entry points |
| 3 — verify | qa | Sonnet 5 | high | `tests/`, bug isolation, pre-experiment code gate |
| 4 — ops | experiment-tracker | Sonnet 5 | low | `experiments/runs/` per-run records |
| 4 — ops | filemanager | Sonnet 5 | low | repo structure, git, env, dependency files |
| 4 — ops | writer | Sonnet 5 | medium | `docs/`, human-facing prose, README |

Cheaper presets are selectable per session — `./orchestrate claude --preset balanced|fast` (Codex
analogue: `.codex/fleets/`) — with per-role overrides. Research-gate floors keep verification honest
regardless of preset: `critic`/`qa` never drop below `sonnet@high`, `data` never below
`sonnet@medium`, and the lead role stays on Fable 5 or Opus 4.8. See the
[Claude fleets guide](.claude/fleets/README.md) and [CLAUDE.md](CLAUDE.md) for the full table. The
same role set exists on the Codex plane (`.codex/prompts/roles/`, `.agents/skills/`).

## Quality gates and the research record

Three mandatory gates run before any experiment launches:

1. **Critic** reviews the plan (a `REV` entry records `Gate: passed`; no blocking `REV` open).
2. **QA** verifies the code commit (a `QA` entry records a passed verdict; no critical `BUG` open).
3. **Data** documents the split and runs the leakage checklist (a `DATASET` entry records a passed
   leakage audit).

These are mechanically enforced, not just procedural: a `PreToolUse` hook
(`.claude/hooks/experiment_gate.py`, Codex analogue `.codex/hooks/experiment_gate.py`) blocks
`run.sh`/`evaluate.sh`/`python model/*.py` launches while any gate is unmet. A documented bypass
requires an `ADR` entry naming the skipped rule, reason, and rollback plan, then prefixing the
launch command with `GATE_OVERRIDE=ADR-NNN`; the hook checks the ADR exists and carries the required
fields before allowing the run through.

Research state lives in a **version-gated four-document record** under `report/`: `result.md`,
`discussion.md`, and `issue.md` hold only the current version's typed, append-only entries
(`HYP`/`EXP`/`REV`/`QA`/`BUG`/`ADR`/... with cross-references between them); `version.md` is the
cumulative archive that absorbs each version's content at a milestone boundary. Session continuity is
two-layered: a `SessionStart` hook injects a machine-readable hand-off
(`.claude/state/handoff.json`), open gates, and running/orphaned experiments into every new session;
a `Stop` hook blocks session close if the research docs changed without a matching hand-off update.

## Research features

Integrations and disciplines the system provides out of the box:

| Capability | What you get | Where |
|---|---|---|
| Literature search MCP | arXiv, OpenAlex, PubMed, and Semantic Scholar search + link fetch, no credentials required | `lit_search`/`lit_fetch` tools; server `.claude/scripts/literature_mcp.py` (Codex: `.codex/scripts/literature_mcp.py`); registered in `.mcp.json` |
| Zotero MCP | Search, full-text, collections, add-item, and BibTeX export straight into a paper's `.bib` — writer never hand-writes citations Zotero can generate | `.claude/scripts/zotero_mcp.py`; requires a Zotero account key or the local desktop API (see provider guide) |
| Overleaf integration | Git-based sync (`clone`/`pull`/`push`/`status`); writer-owned paper workflow; compilation stays on Overleaf's servers, no local LaTeX toolchain; push guard refuses staged data/secret paths and oversized files | `.claude/scripts/overleaf_sync.sh`; requires an Overleaf git token (premium feature or self-hosted) |
| Reproducibility discipline | Per-run records under `experiments/runs/`, pre-run metadata capture (commit, config, seed, environment), dataset-hash re-verification before every run | `experiment-reproducibility` skill; `experiment-tracker`, `developer` |
| Leakage defense | Split-integrity checklist shared across six roles; a leaky experiment is invalidated and re-run, never silently deleted | `data-leakage-audit` skill |
| Adversarial review | A dedicated critic role, on a `max`-effort budget, gates plans before experiments and results before reporting | `research-validity-review` skill |
| New-project adaptation | `./orchestrate init` diffs the checkout against a machine-readable project map and prints a concrete adaptation checklist | `.orchestration/project_map.json`; human guide `docs/orchestration/PROJECT_MAP.md` |

## Research workflow

```text
literature -> hypothesis -> critic -> data/leakage -> implementation -> QA
           -> experiment -> analysis/critic -> writing -> artifact/reference review
```

Delegated work counts only when the runtime returns an agent/thread identity and an evidence-bearing
RESULT. Search snippets are leads, not citation evidence. Experiments require explicit data, critic,
and QA clearance, and paper claims must trace to reviewed sources or experiment artifacts.

## Permissions and external services

`safe` is the default. `bypass` removes local approval and sandbox boundaries and is suitable only
inside a researcher-controlled external container or VM. A permission flag is not evidence that a
scientific gate ran; verify the gate and runtime report separately.

Implementation, testing, review, documentation, and release preparation authorize working-tree edits
only. Agents must not stage, branch, commit, pull, push, create or modify a PR, merge, or perform any
other mutating Git action unless the user explicitly requests that exact action.

Literature search can run without private credentials. Zotero and Overleaf require the account and
network configuration described in the selected provider guide. Never commit local settings, tokens,
provider-private handoffs/memory/run ledgers, generated run outputs, or paper checkouts. Review data
licenses, privacy, file size, and generated analysis artifacts before committing them.

## Documentation footprint

All detailed distribution documentation is consolidated under `docs/orchestration/` so a consumer
project can exclude it as one unit:

```gitignore
/docs/orchestration/
```

Git ignores only untracked files. If a project was cloned from this source repository, removing
already tracked documentation requires an explicit repository change; adding the ignore rule alone
does not untrack it. Runtime policies such as `AGENTS.md`, `CLAUDE.md`, `.codex/`, and `.claude/` are
not distribution documentation and must not be removed from a provider that uses them.

## Scope

The system structures work and makes missing evidence visible; it does not guarantee that a research
claim is true. Local audit records are tamper-evident metadata, not remotely signed attestations.

## License

[MIT](LICENSE)
