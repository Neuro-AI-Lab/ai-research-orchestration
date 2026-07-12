# Setup

**English** | [한국어](SETUP.ko.md)

This guide takes a fresh clone to its first diagnosed research session. The setup has three actions:
initialize one provider, run its diagnostics, and launch a fleet. No optional literature or paper
integration is required for the built-in demo.

## Before you begin

Use exactly one provider per checkout. If you want to compare Codex and Claude, create two clones or
worktrees so live research, memory, experiments, and paper drafts cannot mix.

| Requirement | Why it is needed | Quick check |
|---|---|---|
| Python 3.8+ | launcher, hooks, MCP servers, and validation | `python3 --version` |
| Git | repository and Overleaf workflows | `git --version` |
| POSIX shell | launch and research utility scripts | `bash --version` |
| Codex or Claude Code CLI | selected agent runtime | `codex --version` or `claude --version` |

Linux is the primary target. On Windows, use WSL2 or a Linux container/VM. Internet access is needed
only for provider login and optional literature, Zotero, or Overleaf operations.

## What the setup commands do

| Command | Result |
|---|---|
| `./orchestrate init <backend>` | creates ignored local state from clean templates and locks the checkout to that backend |
| `./orchestrate doctor <backend>` | checks required files, CLI capabilities, fleet/topology settings, local configuration, and isolation |
| `./orchestrate <backend> --preset quality` | starts the selected provider with this repository's research control plane |

Do not continue past diagnostics if doctor reports a failure. A ready checkout ends with
`0 failure(s), 0 warning(s)`. The examples below use `quality`, the default for research-critical
reasoning and review; lower-cost presets remain optional.

## CODEX

### Initialize and verify

```bash
git clone <this-repo> my-research-codex
cd my-research-codex
codex --version
./orchestrate init codex
./orchestrate doctor codex
./orchestrate demo                     # optional dependency-free onboarding run
./orchestrate codex --preset quality
```

Initialization is non-destructive and creates only Codex-owned ignored live files from clean
templates. It also locks this checkout to `codex`. The root Codex session is automatically loaded as
the sole conductor-orchestrator; do not create or configure an `orchestrator` subagent.

Fleet tips:

- Use `quality` for hypothesis selection, critic/QA gates, result analysis, and paper review.
- Use `balanced` for routine implementation or bounded exploratory work.
- Use `fast` for broad first-pass discovery and mechanical tasks.
- Override a specialist, not the root coordination role: `--role brainstorm=fast` or
  `--role critic=gpt-5.6-sol@max`.
- Keep no more than four specialists active and checkpoint before eight total dispatches.

Inspect the command without launching:

```bash
./orchestrate codex --preset quality --dry-run
```

On the first safe launch, inspect and trust the project hooks in the Codex UI. Skipped hook trust
leaves the audit unverified. For an externally isolated environment only:

```bash
./orchestrate codex --preset quality \
  --permissions bypass --allow-unsafe-bypass
```

Bypass removes local approvals and sandboxing; it does not bypass critic, QA, data-leakage, RESULT,
or session gates.

### Optional integrations

Edit only the ignored `.codex/settings.local.json` created by initialization. Do not place secrets in
tracked files. Supported values include `LIT_CONTACT_EMAIL`, `S2_API_KEY`, `ZOTERO_API_KEY`,
`ZOTERO_USER_ID` or `ZOTERO_GROUP_ID`, `ZOTERO_LOCAL`, and `OVERLEAF_GIT_TOKEN`.

```bash
codex mcp list  # run after the first project-trust step
python3 .codex/scripts/lit_search.py openalex "your topic" --limit 3
python3 .codex/scripts/zotero_mcp.py collections
python3 .codex/scripts/zotero_mcp.py search "your topic" --limit 10
.codex/scripts/overleaf_sync.sh clone <project-id> docs/paper-codex-my-paper
```

After project trust, the `literature` and `zotero` rows must be `enabled`. Before trust, doctor reports
activation as pending while still validating the project config and both server handshakes. For these
local STDIO servers, an
`Auth: Unsupported` display means Codex-managed OAuth is not applicable; Zotero credentials are
supplied through the ignored local environment instead. The CLI commands above exercise the same
implementation directly. Start a new Codex session after changing MCP configuration or credentials.

See `.codex/docs/integrations/ZOTERO.md` and `.codex/docs/integrations/OVERLEAF.md`. Search results
are leads; require stable identifiers and primary-source inspection before citing them. Pull Overleaf
before editing and push only with explicit user authorization.

### Start and audit a research run

```text
Use the Codex quality fleet. Act as the sole root conductor-orchestrator and directly spawn the
minimum specialists needed for <research question>. Register every exact BRIEF before spawn. Do not
implement before critic clearance and do not experiment before DATASET leakage and QA gates pass.
Report native agent IDs, RESULT evidence, artifacts, verification commands, and unresolved gates.
Finish by running `./orchestrate audit latest`.
```

After leaving the Codex session:

```bash
./orchestrate runs list
./orchestrate audit latest
./orchestrate audit latest --json
```

A verified run needs a native root session, delivered BRIEF and valid RESULT for every started
specialist, an intact event chain, and a completed root session. Direct `codex` launches have no
project run ID and cannot produce this verdict.

For long jobs:

```bash
.codex/scripts/run_with_status.sh EXP-001 -- \
  ./run.sh --config experiments/codex/EXP-001/config.yaml
```

## CLAUDE

### Initialize and verify

```bash
git clone <this-repo> my-research-claude
cd my-research-claude
claude --version
./orchestrate init claude
./orchestrate doctor claude
./orchestrate demo
./orchestrate claude --preset quality
```

Initialization creates only Claude-owned ignored live files and locks the checkout to `claude`.
Claude retains its own lead-agent topology and specialist definitions. Use its own fleet rows only:

```bash
./orchestrate claude --preset fast --role critic=quality
./orchestrate claude --dry-run
```

Edit only `.claude/settings.local.json`. Claude integration commands use `.claude/scripts/`:

```bash
python3 .claude/scripts/lit_search.py openalex "your topic" --limit 3
python3 .claude/scripts/zotero_mcp.py search "your topic" --limit 10
.claude/scripts/overleaf_sync.sh clone <project-id> docs/paper-claude-my-paper
```

See `.claude/ZOTERO.md` and `.claude/OVERLEAF.md`. Claude must report returned agent/thread IDs and
RESULT evidence, but it does not read or write the Codex native audit ledger.

For long jobs:

```bash
.claude/scripts/run_with_status.sh EXP-001 -- \
  ./run.sh --config experiments/claude/EXP-001/config.yaml
```

## Shared research rules

The selected provider reads only its own `research/`, state, memory, integration settings, and
`experiments/<backend>/` subtree. Root-level `discussion.md`, `result.md`, `error.md`, and `version.md`
are forbidden.

Before executing experiments, require all three positive attestations in the selected provider state:

1. DATASET leakage audit passed;
2. critic REV gate passed with no open blocker;
3. QA gate passed with no open critical issue.

Every delegated stage uses BRIEF → RESULT → evidence-grounded HANDOFF. Preserve negative and failed
runs. Keep Zotero as the reference authority and map every manuscript number to a reviewed experiment
or source ID. Use [the prompt book](docs/AI_RESEARCH_PROMPTS.md) for complete workflows.

Maintainers validate distribution changes with:

```bash
python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate release-check
```

See [SECURITY.md](SECURITY.md) and [docs/RELEASING.md](docs/RELEASING.md).
