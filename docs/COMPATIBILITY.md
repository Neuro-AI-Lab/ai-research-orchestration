# Compatibility

**English** | [한국어](COMPATIBILITY.ko.md)

Use this page before installation or when doctor reports a missing capability. Compatibility is based
on what the installed CLI can do, not on a hard-coded historical version number. The launcher checks
the selected runtime and fails clearly rather than silently replacing an unsupported fleet setting.

## Deployment overview

| Environment | Guidance |
|---|---|
| Linux | primary deployment target |
| macOS | use compatible Python, Git, shell, and process tools |
| Windows | use WSL2 or a Linux container/VM |
| Offline core use | initialization, diagnostics without external auth calls, tests, and demo are local |
| External integrations | literature, Zotero, and Overleaf require the corresponding network/service access |

Use a separate checkout for each provider. After initialization, `./orchestrate doctor <backend>` is
the authoritative local check; `--dry-run` then shows the exact resolved launch command.

## Shared requirements

| Component | Requirement |
|---|---|
| Python | 3.8+ for the orchestration core; 3.11 recommended for maintainers |
| Git | required |
| Shell | POSIX-compatible; WSL2 or Linux container/VM on Windows |
| Process tools | `setsid` recommended for long-run isolation |
| Network | outbound HTTPS only for optional literature/Zotero/Overleaf operations |
| Tests | `requirements-dev.txt` installs pytest tooling |

Overleaf Git access depends on the user's Overleaf account and plan.

## CODEX

The installed Codex CLI must expose native `multi_agent` and `hooks` features and a bundled model
catalog containing every selected fleet model/effort combination. Launch preflight checks these
requirements and fails instead of silently substituting a model.

Codex native audit requires lifecycle hook payloads with root session identity, specialist
`agent_id`/role fields, and the stopped specialist's last message. If these fields are unavailable,
the system cannot invent them; the run remains unverified.

```bash
codex --version
./orchestrate init codex
./orchestrate doctor codex
./orchestrate codex --dry-run
```

## CLAUDE

The installed Claude Code CLI must support project agents, hooks, skills, MCP configuration, model
aliases used by `.claude/fleets/`, and programmatic agent overlays for non-quality presets/overrides.
Fleet validation rejects unsupported aliases, efforts, or rows below research-gate floors.

```bash
claude --version
./orchestrate init claude
./orchestrate doctor claude
./orchestrate claude --dry-run
```

## Maintainer checks

```bash
python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate release-check
```
