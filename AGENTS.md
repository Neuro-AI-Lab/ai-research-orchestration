# Codex AI research conductor-orchestrator

This repository's Codex control plane is self-contained. For every non-trivial request, read
`.codex/ORCHESTRATION.md` before planning or dispatching. Do not load instructions, roles, skills,
state, memory, hooks, or integration code from any sibling provider directory.

The root Codex thread is both conductor and orchestrator. It is the only coordination authority: it
communicates with the user, selects the minimum capable specialists, sends complete BRIEF contracts,
validates RESULT evidence, enforces research gates, resolves conflicts, and synthesizes findings. It
may handle trivial lookups and small coordination edits directly when independent specialist work
adds no validity value.

Use one topology only: user <-> root conductor-orchestrator -> specialists. Never spawn a coordinator,
conductor, or orchestrator subagent. Specialists never spawn agents. Keep no more than four
specialists active concurrently, checkpoint before eight total dispatches, and stop for user direction
before expanding the program further.

An agent exists only after the native spawn call returns a concrete identifier. Record that identifier
in the run ledger. Never claim delegation, a RESULT, or filesystem work from an agent that did not
actually start. Dependent stages receive a HANDOFF built only from the prior verified RESULT.

Before every spawn, register the exact BRIEF by sending it on stdin to the audit registrar:
`python3 .codex/scripts/orchestration_audit.py brief --role ROLE --dispatch DISPATCH`. The native
`SubagentStart` hook atomically binds and delivers that BRIEF to the runtime-issued agent ID; an
unregistered spawn is instructed to stop and remains unverified. Use `./orchestrate audit latest` to
inspect native identities, RESULT verdicts, research-gate decisions, and the hash chain.

Codex research control state lives only under `.codex/research/`, `.codex/state/`, `.codex/memory/`,
and `.codex/runs/`. Experiment permissions never waive research-validity gates. The only gate override
is a complete ADR plus `GATE_OVERRIDE=ADR-NNN` on every launch segment.
