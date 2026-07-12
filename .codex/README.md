# Codex research system layout

## CODEX

This is the technical map of the complete Codex research control plane. Most researchers should start
with the root [README](../README.md) and [setup guide](../SETUP.md); use this page when reviewing Codex
ownership, configuration, or integration paths.

Files committed here are clean policies, prompts, templates, and tools. `./orchestrate init codex`
creates live research state, memory, settings, handoff, and run directories locally; those generated
files remain ignored and are not distribution content.

The root Codex session is the sole conductor-orchestrator. `config.toml` exposes exactly eight
specialists at depth 1; there is no orchestrator role prompt, fleet row, or agent config.

| Path | Purpose |
|---|---|
| `ORCHESTRATION.md` | authoritative routing, gates, state, and research workflow |
| `config.toml` | native agents, hooks, MCP, concurrency, and depth |
| `fleets/` | quality, balanced, and fast role configurations |
| `prompts/roles/` | role ownership and boundaries |
| `contracts/` | BRIEF, RESULT, HANDOFF, and run-ledger contracts |
| `hooks/` | Codex-only experiment, continuity, RESULT, and native audit enforcement |
| `scripts/` | Codex-only literature, Zotero, experiment, Overleaf, and audit tools |
| `docs/integrations/` | integration setup and operating notes |
| `research/` | current Codex scientific state |
| `templates/research/` | clean state templates |
| `state/` | ignored structured session handoff plus its committed example |
| `memory/` | ignored conductor/role durable lessons seeded from `templates/memory/` |
| `runs/` | ignored native-ID audit manifests and hash-chained events |

Repository-discoverable Codex skills remain in `.agents/skills/`, the native project skill location.
Do not place another provider's instructions or state anywhere in this control plane.

## MCP servers

Project MCP ownership lives in `config.toml`:

- `literature` exposes `lit_search` and `lit_fetch` through `scripts/literature_mcp.py`;
- `zotero` exposes library search, item/full-text retrieval, BibTeX, collections, and save-back
  through `scripts/zotero_mcp.py serve`.

Project MCP loads only after repository trust. On a fresh checkout, launch once, review/trust the
project, start a new session, then use `codex mcp list` to check that both servers are enabled. Restart
through `./orchestrate codex` after changing MCP configuration or local integration environment values;
tool availability is fixed when the session starts. Overleaf remains an explicitly authorized Git
script workflow, not an MCP server.
