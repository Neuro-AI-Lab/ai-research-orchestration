# Distribution release guide

**English** | [한국어](RELEASING.ko.md)

This is a maintainer checklist for packaging the template, not a user setup guide. A release is ready
only when all distribution checks pass from a clean candidate and no live research data, local
configuration, credentials, run history, or maintainer validation history is included.

| Phase | Required outcome |
|---|---|
| Prepare | dedicated clean release worktree |
| Inspect | empty provider templates and no live/ignored state in candidates |
| Verify | isolation, deterministic validation, tests, demo, and release check all pass |
| Package | explicit staged paths, reviewed staged diff, no secret or credential-bearing remote |

Never release from an active research checkout. Use a clean worktree so provider research state,
handoffs, settings, run logs, and memory remain local.

```bash
git worktree add ../orchestration-release -b release/<version>
cd ../orchestration-release

python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate demo
./orchestrate release-check
```

Inspect the clean seeds under each provider's `templates/research/` and `templates/memory/`
directories. Live research state and memory are generated only by `./orchestrate init`; they are
ignored and must never be copied into a release. Live settings, handoffs, run stores, experiment
outputs, paper clones, data, and `.local/` migration snapshots must also remain ignored.

Maintainer development/validation history is not a release artifact. Keep benchmark workspaces,
reports, bug diaries, captured example output, and internal validation notes in the gitignored paths
declared by `.gitignore`.

## CODEX

- Confirm `.codex/config.toml` has `max_depth = 1` and exactly eight specialist entries.
- Confirm no Codex orchestrator prompt, fleet row, config entry, or memory seed exists; the root is the
  conductor-orchestrator and `.codex/templates/memory/conductor/` is the clean seed.
- Confirm all three Codex fleet directories contain the same eight specialist roles.
- Confirm `.codex/research/`, `.codex/memory/`, `.codex/state/handoff.json`, `.codex/runs/`, and local
  settings are absent from distribution candidates.
- Exercise the Codex dry-run and native audit tests without adding generated ledgers.

## CLAUDE

- Confirm Claude lead-agent and specialist definitions agree with all three `.claude/fleets/`
  manifests.
- Confirm `.claude/research/`, `.claude/agent-memory/`, `.claude/state/handoff.json`, `.claude/runs/`,
  and local settings are absent from distribution candidates.
- Confirm Claude hooks and scripts reference only Claude-owned state and integrations.
- Exercise the Claude dry-run and provider-specific gate tests without copying Codex audit data.

The release gate fails when:

- a legacy root `discussion.md`, `result.md`, `error.md`, `version.md`, or `CODEX.md` exists;
- provider control files reference the other provider;
- a provider research or memory template contains live entries;
- live provider research state or memory is tracked or otherwise distribution-visible;
- secrets, credential-bearing remotes, ignored tests, invalid JSON, empty scripts, or diff errors exist.

Stage explicit paths; do not use `git add -A` in a personal checkout. Inspect the entire staged diff,
run `git diff --cached --check`, and verify the isolation command reports zero failures.
