---
name: codex-multiagent-orchestration
description: Coordinate Codex AI-research specialists through the single-hop root conductor-orchestrator, native agent IDs, BRIEF/RESULT/HANDOFF contracts, bounded parallelism, validity gates, and faithful synthesis. Use before every Codex specialist dispatch or multi-stage research pipeline.
---

# Codex multi-agent orchestration

Read `.codex/ORCHESTRATION.md` and `.codex/contracts/agent-contracts.md` before dispatching. Use only
roles configured in `.codex/config.toml`; never load another provider's control plane.

## Route minimally

- Answer a verified document lookup at the root.
- Use one specialist for one bounded domain.
- Use two to four specialists only for independent comparison, evidence collection, or audits.
- Serialize developer -> QA and every evidence-consuming dependency.
- The root Codex thread is the conductor-orchestrator. Never spawn another coordinator or
  orchestrator. Specialists never spawn agents.

Parallelize independent reads and checks. Serialize code edits, research-state writes, decisions, and
experiment fan-in. A hyperparameter sweep is one tracker-owned EXP with process sub-runs, not an agent
per configuration.

## Dispatch faithfully

Send one complete BRIEF per objective. Preserve critical user wording, name exact IDs and paths, state
checkable Done-when criteria, and separate parallel responsibilities. Register the exact block before
spawn with `python3 .codex/scripts/orchestration_audit.py brief --role ROLE --dispatch DISPATCH` on
stdin. The native start hook delivers it and binds the runtime-issued identifier; a dispatch exists
only after that identifier returns. Never repair missing registration retroactively.

Accept RESULT `complete` only when every criterion has evidence. Continue the same agent once for a
contract repair, then mark the stage partial/blocked. Build dependent HANDOFF packets from the actual
RESULT and verified artifacts. Reconcile disagreement with targeted evidence, never preference.

## Enforce research validity

Require a passed DATASET leakage audit, critic plan gate, and QA code gate before experiments. Require
critic result review before reporting a finding. Only a complete ADR plus `GATE_OVERRIDE=ADR-NNN` may
override a research gate; machine permission mode is irrelevant.

Keep at most four specialists active at once and checkpoint before eight total dispatches without a
user-visible result. After one repaired brief and one reroute/decomposition, stop and report the
blocker. Final synthesis names the actual agent IDs, state IDs, evidence paths, unresolved gates, and
next action without inventing provenance.
Confirm the ledger with `./orchestrate audit latest`; if it reports an unverified claim, report that
limitation instead of claiming successful orchestration.
