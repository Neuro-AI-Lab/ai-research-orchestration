# AI Research Orchestration

**English** | [한국어](README.ko.md)

A source distribution for running AI/ML research through explicit specialist roles, evidence
contracts, and review gates. It covers literature review, hypothesis design, data integrity,
implementation, independent QA, experiments, analysis, references, and paper review.

This repository contains two independent provider implementations. Select one as the default for a
research checkout; they do not collaborate or share research state. For the strongest isolation, use
separate clones or worktrees when comparing providers.

## Choose a provider

| Provider | Coordination | User guide |
|---|---|---|
| Codex | the root session is intended to coordinate direct specialists | [Codex guide](docs/orchestration/CODEX.md) |
| Claude Code | provider-owned lead-agent routing and specialists | [Claude guide](docs/orchestration/CLAUDE.md) |

Maintainer and release procedures are in the [maintainer guide](docs/orchestration/MAINTAINERS.md).
Korean guides are available beside each English document.

## Quick start

Use a dedicated checkout and initialize its default provider:

```bash
git clone <this-repo> my-research
cd my-research
./orchestrate init codex       # or: ./orchestrate init claude
./orchestrate doctor codex     # use the same provider
./orchestrate codex --preset quality --dry-run
./orchestrate codex --preset quality
```

`init` creates ignored provider-owned local state and saves a default. An explicit launch of the
other provider is allowed with a warning because data, evaluation, and entry-point paths remain
shared; do not run both providers concurrently on the same files.

`doctor` validates files, configuration, CLI capabilities, and local MCP handshakes. It is not proof
that a native specialist received the selected role, BRIEF, or RESULT contract. Before substantive
research, run the provider guide's one-specialist smoke test and inspect the returned runtime identity
and evidence.

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
research state, run ledgers, datasets, generated run/analysis outputs, or paper checkouts.

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
