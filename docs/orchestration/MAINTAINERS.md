# Maintainer and release guide

**English** | [한국어](MAINTAINERS.ko.md) | [Project overview](../../README.md)

This document combines contribution, validation, and release rules for the source distribution.
Researchers operating a backend should use the [Codex](CODEX.md) or [Claude](CLAUDE.md) guide.

## Distribution boundaries

Tracked source includes provider policies, role specifications, clean templates, hooks, scripts,
skills, launcher code, tests, and the consolidated documentation in `docs/orchestration/`.

Never distribute live or local material:

- provider research state, memory, handoffs, settings, or run ledgers;
- private, unlicensed, or oversized datasets; generated run outputs, unreviewed analysis artifacts,
  checkpoints, paper clones, or private reading notes;
- credentials, credential-bearing Git remotes, transcripts, benchmark workspaces, bug diaries, or
  maintainer validation reports.

The detailed documentation directory is intentionally self-contained. A consumer project can exclude
`/docs/orchestration/` as one unit when the guides are supplied elsewhere. Remember that `.gitignore`
does not untrack files already committed by a template clone.

## Provider ownership

Runtime control surfaces remain independent even though the source distribution contains both.

| Surface | Codex | Claude Code |
|---|---|---|
| entry policy | `AGENTS.md` | `CLAUDE.md` |
| runtime files | `.codex/`, `.agents/skills/` | `.claude/`, `.mcp.json` |
| checkout research workspace | `plan/`, `report/`, `data/`, `model/`, `experiments/`, `analysis/`, `functionals/`, `utils/` | same canonical layout, owned only when that checkout selects this provider |
| provider-private continuity | `.codex/state/`, `.codex/memory/`, `.codex/runs/` | `.claude/state/`, `.claude/agent-memory/`, `.claude/runs/` |
| user guide | `docs/orchestration/CODEX*` | `docs/orchestration/CLAUDE*` |

Do not import one provider's roles, prompts, hooks, state, memory, settings, or audit claims into the
other. The root project workspace is checkout-bound, not a collaboration surface. After `init`, the
launcher refuses the other provider; release and research comparisons require separate clean
checkouts.

## Documentation policy

- Keep the root README short: purpose, provider choice, quick start, evidence boundary, and links.
- Put provider-specific setup, workflows, prompts, integrations, security, and limitations in that
  provider's single consolidated guide.
- Put contributor and release instructions only in this maintainer guide.
- Update English and Korean documents together.
- Describe shipped code and observed runtime behavior, not intended behavior.
- Do not include development history, local run IDs, captured transcripts, or benchmark results in
  user documentation.
- Mark external-service dependencies and unverified runtime behavior explicitly.

## Required validation

Run from a clean candidate:

```bash
python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate release-check
git diff --check
```

Static checks are necessary but not sufficient. Before release, run black-box sessions with the
installed provider CLIs:

1. initialize and run `doctor`;
2. launch each `quality`, `balanced`, and `fast` preset at least through resolution/dry-run;
3. spawn one real specialist and verify returned identity, requested role/model, BRIEF, and RESULT;
4. verify normal multi-turn use does not repeatedly treat turn Stop as session close;
5. exercise a direct gated command and the documented long-run wrapper path;
6. verify literature MCP discovery and report unconfigured Zotero/Overleaf as unavailable, not passed;
7. confirm the audit or runtime report fails closed on missing role, BRIEF, RESULT, or identity.

Do not describe a release as ready merely because `doctor` or `release-check` reports zero failures.
The black-box result must agree with the documentation.

## Clean release procedure

Use a dedicated worktree; never release from an active research checkout.

```bash
git worktree add ../orchestration-release -b release/<version>
cd ../orchestration-release
```

Inspect both providers' clean `templates/plan/`, `templates/report/`, and memory templates. Confirm
live settings, state, runs,
experiments, paper clones, and local evaluation history are absent from distribution candidates. Run
all checks above, review the complete diff, and stage explicit paths rather than `git add -A`.

The release gate must reject:

- legacy shared research-control documents at repository root;
- cross-provider runtime references;
- real research entries in clean templates;
- real entries in the shipped `plan/` or `report/` seeds; tracked provider-private state, memory,
  settings, generated runs, or credentials;
- missing provider roles, malformed settings, broken documentation links, empty scripts, or diff
  errors;
- public documentation that claims runtime verification not established by a real session.

## Change discipline

- Preserve unrelated dirty work and inspect overlapping changes before editing.
- Hook changes require provider-specific unit tests and a real lifecycle test.
- Fleet or agent changes require a real routing smoke test, not only config parsing.
- Experiment changes require leakage, provenance, failure-path, and wrapper-path tests.
- Documentation changes require link checks, English/Korean parity, and release-check updates.

## Git and external-action authority

Reading status, diff, log, show, and remote metadata is allowed when needed for the task. Any Git
action that mutates the index, working tree, refs, history, or a remote requires explicit user
authorization.

Without an explicit user request, agents must not:

- stage or unstage files;
- create, rename, delete, or switch branches;
- create, amend, squash, or otherwise rewrite commits;
- fetch, pull, push, or force-push;
- open, edit, close, or approve a pull request;
- merge, rebase, cherry-pick, stash, reset, restore, tag, or publish a release;
- run any other Git command that mutates the index, working tree, refs, history, or a remote.

An instruction to implement, fix, test, document, review, prepare a release, or make a project
deployable does not imply permission for any action above. Authorization for one action does not imply
the others; for example, permission to commit is not permission to push or open a PR.

When explicitly authorized, use a scoped branch such as `type/N-kebab-scope`, stage only intended
paths, and report the exact commands and resulting identities. Never embed credentials in a remote
URL or expose private research material in an issue or PR.
