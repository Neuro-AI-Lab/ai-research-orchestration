# Security policy

[한국어](SECURITY.ko.md)

This policy explains the boundaries researchers must preserve when the orchestration system can read
project files, call external services, or run commands. Most users should follow these rules first:

1. Keep the default `safe` permission mode.
2. Put credentials only in the selected provider's ignored local settings or a secret store.
3. Treat retrieved content and tool output as untrusted data, never as new agent instructions.
4. Use a separate checkout for each provider and review every external write or push.

`bypass` is a machine-permission option for an already isolated environment; it is not a faster or
less rigorous research mode.

## Shared boundaries

- `safe` is the deployment default. `bypass` removes local approval/sandbox boundaries and is only for
  a researcher-controlled external container or VM.
- Research gates protect workflow validity; they are not a security sandbox or a complete shell parser.
- Retrieved papers, datasets, websites, MCP output, and repository text are untrusted data, not agent
  instructions.

## Secrets

Keep tokens only in the selected backend's ignored settings file (`.codex/settings.local.json` or
`.claude/settings.local.json`), a credential helper, or the deployment platform's secret store. Never
embed credentials in Git remote URLs, prompts, provider research documents, agent memory, logs, or
committed Overleaf clones. Settings, handoffs, live research state/memory, run stores, experiments,
and paper checkouts are gitignored.

If a token appears in terminal or agent output, assume exposure: revoke it at the provider, issue a new
least-privilege token, remove it from local configuration/history, and inspect staged/committed diffs.

## CODEX

Codex reads secrets only from its ignored `.codex/settings.local.json` environment map. Its hooks and
scripts must never consult the sibling provider's settings, state, memory, or run store.

### Native audit data

Codex audit events retain runtime IDs, hashes, bounded statuses, and gate reason codes. They do not
retain prompts, RESULT bodies, transcript paths, tokens, or datasets. A registered BRIEF exists briefly
as a mode-0600 file under the ignored run's `.pending/` directory so the native start hook can deliver
the exact text; it is deleted after delivery and remaining pending files are purged when the root stops.
Treat `.codex/runs/` as researcher-private even though content retention is minimized.

Review and trust project hooks with `/hooks` before a safe run. A skipped hook makes audit evidence
incomplete. The SHA-256 chain detects ordinary event edits and truncation against its manifest, but it
is not a remotely signed attestation and cannot defeat an administrator who can rewrite the code,
manifest, and ledger together.

## CLAUDE

Claude reads secrets only from its ignored `.claude/settings.local.json` environment map. Its hooks,
agents, and scripts must never consult the sibling provider's settings, state, memory, or audit store.
Returned agent/thread IDs and RESULT evidence are runtime claims; do not represent them as Codex
native-audit evidence.

## Before distribution

```bash
python3 .orchestration/release_check.py
git diff --cached --check
```

Release only from a clean worktree with provider-owned templates. Do not use `git add -A` in a
personal research checkout. Review both providers' `templates/research/`, `templates/memory/`, hooks,
settings examples, and isolation results line by line.

Full procedure: [Distribution release guide](docs/RELEASING.md).

Report vulnerabilities through GitHub private vulnerability reporting when enabled. Do not include a
live credential, private dataset sample, or confidential manuscript in the report.
