# Claude orchestration prompt cores

## CLAUDE

These files are runtime policy and contract inputs for the Claude research control plane.

```text
main session / lead agent
  |-- brainstorm
  |-- data
  |-- critic
  |-- developer
  |-- qa
  |-- experiment-tracker
  |-- filemanager
  `-- writer
```

Specialists work in isolated contexts and communicate through BRIEF, RESULT, and HANDOFF contracts.
They do not call one another; coordination returns to the lead.

| File | Purpose |
|---|---|
| `orchestrator-core-fable5.md` | primary lead-agent routing, gates, synthesis, and reporting policy |
| `orchestrator-core-opus48.md` | alternate lead-agent policy with the same research invariants |
| `specialist-core-sonnet5.md` | shared specialist execution and evidence discipline |
| `result-contract.md` | authoritative BRIEF, RESULT, and HANDOFF schemas |

Maintenance rules:

1. Keep routing and research invariants aligned across both lead-agent cores.
2. Change contract schemas in `result-contract.md` and update the small mirrors in agent specs.
3. Keep reusable fleet-sizing/failure policy in `.claude/skills/multiagent-orchestration/SKILL.md`.
4. Keep specialist evidence discipline aligned with `.claude/skills/specialist-core/SKILL.md`.
5. New roles require an agent spec and a matching row in every Claude fleet manifest.

Do not place live research state, evaluation transcripts, or maintainer experiment reports here.
