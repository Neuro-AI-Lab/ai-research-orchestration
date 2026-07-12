# Contributing and maintainer discipline

This guide is for maintainers changing the distributed template. Researchers who only want to use the
system should start with [README.md](README.md) and [SETUP.md](SETUP.md).

The repository distributes two independent research control planes. Before editing, decide whether a
change belongs to Codex, Claude, or the small provider-neutral launcher/documentation surface. A
contribution is ready only when it preserves provider isolation, clean templates, reproducibility
gates, explicit provenance, and matching user documentation.

Quick rule: provider-neutral files may select or describe both systems, but runtime roles, rules,
state, memory, hooks, scripts, and audit evidence must stay provider-owned.

## Distribution boundaries

Tracked:

- Codex rules/config/roles/hooks/scripts and `.agents/skills/`
- Claude rules/config/roles/hooks/scripts/skills
- provider-owned `templates/research/` and `templates/memory/`
- handoff/settings `.example` files
- launcher, diagnostics, isolation/release checks, tests, and user documentation

Never tracked:

- `.codex/research/`, `.codex/state/handoff.json`, `.codex/memory/`, `.codex/runs/`
- `.claude/research/`, `.claude/state/handoff.json`, `.claude/agent-memory/`
- local settings, data, experiments, paper checkouts, credentials, or `.local/` migration snapshots

Provider-neutral user documentation and the selector may describe both systems. Runtime control
surfaces must remain independent. Maintainer benchmark workspaces, validation reports, bug diaries,
and captured outputs are ignored and must not be added to a distribution commit.

## CODEX

- The root Codex session is the only conductor-orchestrator. Do not add an orchestrator agent spec,
  fleet row, or second coordination depth.
- Codex changes belong in `AGENTS.md`, `.codex/`, or `.agents/skills/` and must not reference Claude
  instructions, models, roles, skills, state, memory, hooks, or scripts.
- Keep the eight specialist names aligned across config, role prompts, fleet presets, launcher, audit,
  and tests.
- Codex policy changes require single-hop topology, audit-contract, and isolation coverage.

## CLAUDE

- Claude changes belong in `CLAUDE.md` or `.claude/` and must not reference Codex instructions,
  models, roles, skills, state, memory, hooks, scripts, or audit data.
- Preserve Claude's own lead-agent roles and provider-owned fleet manifests.
- Do not solve a Claude change by importing or proxying a Codex control surface.

## Required validation

```bash
python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate demo
./orchestrate release-check
git diff --check
```

Release from a clean worktree and reset each provider template to empty summary tables. Review all
template/memory changes line by line. Follow [docs/RELEASING.md](docs/RELEASING.md).

## Shared change rules

- Do not implement a policy by adding a cross-provider runtime reference.
- Hook changes require current behavior tests for the affected provider.
- New skills follow the Codex skill validator and contain only `name` and `description` frontmatter.
- Update English and Korean user docs together when behavior changes.

## Git and PR conventions

- Branch: `type/N-kebab-scope`, where type is `feat`, `fix`, `docs`, `chore`, `refactor`, or `test`.
- PR title: `type: lowercase summary (#N)`.
- Put `Closes #N` or `Fixes #N` in the PR body, not only the title.
- Preserve unrelated dirty changes and stage explicit paths; do not use `git add -A` from a personal
  research checkout.
- Never push, merge, delete branches, or perform destructive git operations without matching user
  authority.

Use this PR body shape:

```markdown
### Summary

What changed and why.

**Linked:** Closes #N or Refs #N

### Changes

| File | Change | Why |
|---|---|---|

### Verification

| Check | Command | Result |
|---|---|---|

### Known limitations
```
