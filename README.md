# AI Research Orchestration System

**English** | [한국어](README.ko.md)

A provider-selectable template for running AI/ML research as a staged, reviewable workflow. Instead of
asking one agent to handle everything, it separates literature review, hypothesis design, data checks,
implementation, independent verification, experiments, analysis, reference management, and paper
review into explicit roles and gates.

The template organizes work and makes its provenance visible. It does not guarantee that a scientific
claim is true, and it does not make Codex and Claude collaborate. Choose one backend for each checkout.

## What you get

| Research need | What this repository provides |
|---|---|
| Plan a study | literature, hypothesis, feasibility, and critic stages |
| Protect evaluation validity | dataset provenance, leakage checks, critic and QA gates |
| Build and run reproducibly | separated implementation/execution roles, configs, seeds, logs, and status tools |
| Analyze without hiding uncertainty | effect-size, uncertainty, failed-run, sensitivity, and limitation checks |
| Manage papers | Zotero-backed references, Overleaf Git workflow, scientific and artifact review |
| Verify orchestration | returned runtime identities and RESULT evidence; Codex also provides a native local audit ledger |

## Choose one backend

| | CODEX | CLAUDE |
|---|---|---|
| Coordination | the root Codex session directly coordinates specialists | Claude uses its own lead-agent routing |
| Runtime evidence | native agent IDs, BRIEF/RESULT verdicts, and a local hash-chained audit | returned agent/thread IDs and RESULT evidence |
| Control files | `AGENTS.md`, `.codex/`, `.agents/skills/` | `CLAUDE.md`, `.mcp.json`, `.claude/` |
| Best selection rule | choose when your deployment runs Codex | choose when your deployment runs Claude Code |

Both backends ship `quality`, `balanced`, and `fast` fleets and the same baseline research stages.
Their runtime rules, state, memory, integrations, and evidence stores remain independent. If you want
to compare them, create two clones or worktrees rather than switching one active checkout.

## Quick start

The following creates a Codex checkout, verifies it, and opens the research session:

```bash
git clone <this-repo> my-research-codex
cd my-research-codex
./orchestrate init codex
./orchestrate doctor codex
./orchestrate codex --preset quality
```

A healthy setup ends the doctor report with `0 failure(s), 0 warning(s)`. For Claude, use a different
checkout and replace `codex` with `claude`. Start with `quality` unless speed or cost is more important
than maximum reasoning effort.

Once the provider session opens, describe the research question, constraints, evidence standard, and
desired stopping point. Copy-ready requests for literature review, ideation, implementation, QA,
analysis, Zotero, and Overleaf are in the [AI research prompt book](docs/AI_RESEARCH_PROMPTS.md).

## Documentation map

| When you need to... | Read |
|---|---|
| install and launch the first checkout | [Setup](SETUP.md) |
| copy a research workflow request | [AI research prompt book](docs/AI_RESEARCH_PROMPTS.md) |
| check exactly what is implemented | [Feature reference](docs/FEATURES.md) |
| check OS, CLI, and tool requirements | [Compatibility](docs/COMPATIBILITY.md) |
| configure credentials or permission modes safely | [Security policy](SECURITY.md) |
| prepare a distribution release | [Release guide](docs/RELEASING.md) |

## Isolation by design

`./orchestrate init <backend>` records the selected backend in ignored local configuration and creates
only that backend's live state. The two systems are alternatives, not collaborators.

| Boundary | CODEX checkout | CLAUDE checkout |
|---|---|---|
| Entry policy | `AGENTS.md` | `CLAUDE.md` |
| Control plane | `.codex/`, `.agents/skills/` | `CLAUDE.md`, `.mcp.json`, `.claude/` |
| Live research | `.codex/research/` | `.claude/research/` |
| Memory and handoff | `.codex/memory/`, `.codex/state/` | `.claude/agent-memory/`, `.claude/state/` |
| Generated artifacts | `experiments/codex/`, `analysis/codex/` | `experiments/claude/`, `analysis/claude/` |

The permission default is `safe`. `--permissions bypass --allow-unsafe-bypass` removes local
approval/sandbox boundaries, so use it only inside a researcher-controlled external container or VM.
It never disables critic, QA, leakage, or other research gates.

## CODEX

The root Codex session is both conductor and orchestrator. It interprets the user's intent, selects a
minimal team, registers each BRIEF, dispatches native specialists directly, evaluates RESULTs, enforces
gates, resolves conflicts, and produces the final synthesis. There is no conductor or orchestrator
subagent and specialists cannot delegate.

```text
user <-> root Codex conductor-orchestrator
                  |-- brainstorm          literature, ideas, hypotheses
                  |-- data                provenance, splits, leakage
                  |-- critic              validity and statistical gates
                  |-- developer           implementation
                  |-- qa                  independent verification
                  |-- experiment-tracker  reproducible execution
                  |-- filemanager         repository and version hygiene
                  `-- writer              grounded reports and papers
```

The topology is deliberately single-hop: at most four specialists run concurrently, only independent
work is parallelized, and the root checkpoints before eight total dispatches. This avoids a redundant
coordination layer while preserving specialist context isolation.

Launch or inspect the resolved fleet:

```bash
./orchestrate codex --preset quality
./orchestrate codex --preset balanced --role brainstorm=fast
./orchestrate codex --role critic=gpt-5.6-sol@max
./orchestrate codex --dry-run
```

### MCP integrations

Codex loads project MCP servers from `.codex/config.toml`:

- `literature`: `lit_search` and `lit_fetch` for arXiv, OpenAlex, PubMed, and Semantic Scholar;
- `zotero`: library search, item/full-text retrieval, BibTeX, collections, and optional save-back.

```bash
./orchestrate codex --preset quality  # review and trust the project on first launch
# after trust, start a new session and verify from the project directory:
codex mcp list                        # both rows should be enabled
```

Project-scoped MCP is loaded only for a trusted repository. A fresh checkout may not list these
servers until the first trust step. MCP tools are loaded at session start; restart through the
launcher after trusting the project or changing
`.codex/config.toml` or `.codex/settings.local.json`; an already-running session does not acquire the
new tools. Zotero credentials remain optional, but Zotero calls need either its API settings or
`ZOTERO_LOCAL=1`. Overleaf uses the explicit Git synchronization script rather than MCP.

### Proving that project orchestration was used

Codex's native harness performs the actual spawn. This repository supplies the role specs, skills,
BRIEF delivery, hooks, gates, and audit ledger. A session launched through `./orchestrate codex`
receives a run ID; native lifecycle hooks record the root session, runtime-issued agent IDs, delivered
BRIEF hashes, RESULT verdicts, and research-gate decisions in a hash-chained local ledger.

```bash
./orchestrate runs list
./orchestrate audit latest
./orchestrate audit latest --json
```

Expected report shape:

```text
Run: ORCH-YYYYMMDD-001
Backend: codex
Fleet: quality
Topology: root-conductor-direct
Status: completed
Event chain: verified
Conductor-orchestrator: verified
Specialists:
  brainstorm  agent-123  BRIEF delivered  RESULT valid
  critic      agent-456  BRIEF delivered  RESULT valid
Research gates: 1 allowed, 0 blocked
Unverified claims: 0
```

A direct `codex` launch can still read project guidance, but it has no launcher run ID and cannot be
reported as a verified project-orchestrated run. The ignored `.codex/runs/` ledger stores bounded
metadata and hashes, not prompt/RESULT bodies, datasets, tokens, or transcript paths.

Copy-ready request:

```text
Use the Codex quality fleet to orchestrate this research. The root Codex session must act as the sole
conductor-orchestrator and directly spawn brainstorm -> critic -> data -> developer -> qa in dependency
order. Register the exact BRIEF before each spawn. Report every native agent ID, RESULT evidence,
artifacts, verification commands, and unresolved gate. Finish with `./orchestrate audit latest`; do not
claim that an unverified or failed dispatch succeeded.
```

Codex details: [.codex/README.md](.codex/README.md),
[.codex/ORCHESTRATION.md](.codex/ORCHESTRATION.md). Optional integration secrets belong only in the
ignored `.codex/settings.local.json`. Codex-owned literature, Zotero, long-run, sweep, and Overleaf
tools live under `.codex/scripts/`.

## CLAUDE

Claude has an independent control plane with its own lead agents, specialist definitions, skills,
hooks, fleets, prompts, research state, memory, and integrations. It never reads Codex roles, skills,
state, or audit records.

```bash
git clone <this-repo> my-research-claude
cd my-research-claude
./orchestrate init claude
./orchestrate doctor claude
./orchestrate claude --preset quality
./orchestrate claude --preset fast --role critic=quality
```

Claude-owned tools and secrets use `.claude/scripts/` and the ignored
`.claude/settings.local.json`. Its runtime contracts report returned agent/thread identities and
RESULT evidence. The Codex native ledger is not shared and must not be cited as proof for a Claude
run. See [.claude/README.md](.claude/README.md).

## AI research workflow

| Stage | Owner | Required output before the next dependent stage |
|---|---|---|
| Literature | `brainstorm` | primary-source evidence map, stable IDs, caveats |
| Hypothesis | `brainstorm` | prediction, falsifier, baseline, metric, effect threshold |
| Plan review | `critic` | explicit passed/blocked REV and resolution criteria |
| Data | `data` | provenance, license, split unit, hashes, leakage audit |
| Implementation | `developer` | accepted scope, immutable config, focused tests |
| Independent QA | `qa` | inspected diff, executed checks, passed/blocked QA |
| Experiment | `experiment-tracker` | code/data/config provenance, seeds, logs, failures |
| Analysis | `critic` | effect size, uncertainty, sensitivity, limitations |
| Paper | `writer` | claim-evidence map and verified references |
| Final review | `critic`, then `qa` | scientific and artifact/citation clearance |

Every delegated task uses BRIEF → RESULT; dependent work receives a HANDOFF built only from actual
RESULTs. Before an experiment, the selected provider's own state must contain a passed DATASET leakage
audit, critic gate, and QA gate, with no open critical issue. An override requires a complete ADR and
`GATE_OVERRIDE=ADR-NNN` on every launch segment.

Literature results and abstracts are leads, not verified evidence. Search Zotero first when building
on a lab library, verify primary-source metadata/full text, preserve contradictions, and never invent
citations. Pull Overleaf before editing; require critic and QA review before an explicitly authorized
push.

## Project layout

Most researchers work in `data/`, `models/`, `evaluation/`, `experiments/`, `analysis/`, and
`papers/`. The provider directories are the orchestration control planes; do not copy roles, state,
or settings between them. Live state directories are created locally by initialization and remain
ignored.

```text
AGENTS.md, .codex/, .agents/skills/   CODEX control plane
CLAUDE.md, .claude/                   CLAUDE control plane
.orchestration/                       selector, diagnostics, audit adapter, release checks
data/, models/, evaluation/           project source owned by the checkout's selected backend
experiments/<backend>/                run artifacts and status
analysis/<backend>/                   generated analyses
papers/notes/<backend>/               reading notes
docs/                                 distribution guides and paper checkouts
tests/orchestration/                  current behavior and isolation tests
```

## License

[MIT](LICENSE)
