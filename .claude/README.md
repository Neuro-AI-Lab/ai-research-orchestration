# Claude research system layout

## CLAUDE

This is the technical map of the complete Claude research control plane. Most researchers should start
with the root [README](../README.md) and [setup guide](../SETUP.md); use this page when reviewing Claude
ownership, configuration, or integration paths.

Files committed here are clean policies, prompts, templates, and tools. `./orchestrate init claude`
creates live research state, memory, settings, and handoff locally; those generated files remain
ignored and are not distribution content.

| Path | Purpose |
|---|---|
| `agents/` | role definitions and tool boundaries |
| `skills/` | reusable research procedures |
| `prompts/` | model-specific orchestration cores and contracts |
| `fleets/` | quality, balanced, and fast role manifests |
| `hooks/` | experiment, continuity, and RESULT enforcement |
| `scripts/` | literature, Zotero, experiment, and Overleaf tools |
| `research/` | current Claude scientific state |
| `templates/research/` | clean state templates |
| `state/` | ignored structured handoff plus its committed example |
| `agent-memory/` | role-specific durable lessons |

Keep this control plane independent. Do not load roles, rules, state, or memory from a sibling provider.
