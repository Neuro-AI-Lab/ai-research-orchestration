# Claude fleet manifests

## CLAUDE

Each JSON manifest assigns a Claude model alias and reasoning effort to every Claude-owned role.

```bash
./orchestrate claude --preset quality
./orchestrate claude --preset fast --role critic=quality
./orchestrate claude --role developer=sonnet@high
```

`quality` with no override launches the committed agent definitions directly. Other presets and
overrides are resolved from these manifests and injected as a programmatic agent overlay; committed
agent files are never rewritten.

Manifest shape:

```json
{
  "preset": "quality|balanced|fast",
  "description": "one line",
  "roles": {
    "<role>": {"model": "fable|opus|sonnet|haiku", "effort": "high"}
  }
}
```

All ten Claude roles are required: `orchestrator`, eight research specialists, and
`orchestrator-opus`. `orchestrator-opus` follows the selected manifest and is not addressable through
`--role`. A `haiku` row uses `null` effort; select it by borrowing a preset row rather than a custom
`MODEL@EFFORT` override.

Research-gate floors are enforced by the launcher:

| Role | Minimum |
|---|---|
| `critic` | `sonnet@high` |
| `qa` | `sonnet@high` |
| `data` | `sonnet@medium` |
| lead roles | `fable` or `opus` |

Permission posture is independent of these floors and of the experiment gate. Manifest changes must
remain aligned with `.claude/agents/` quality frontmatter and pass the distribution validator.
