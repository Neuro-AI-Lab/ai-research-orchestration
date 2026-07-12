# Codex delegation contracts

Use these schemas for every root conductor-orchestrator and specialist exchange. Omit no field; write `none`
explicitly when a field is empty.

## BRIEF

```markdown
## BRIEF
**Dispatch:** ORCH-<timestamp>-<sequence>
**Role:** exact configured specialist role
**Objective:** one bounded outcome, not an activity list
**Deliverables:** exact entry types and destination paths
**Context:** verified Codex state IDs and artifact paths to read first
**Constraints:** binding user requirements, REV/ADR/BUG conditions, resource limits
**Done when:** checks the specialist can run and report as evidence
**Out of scope:** work owned by another role and forbidden side effects
```

The root preserves critical user wording, verifies every referenced ID/path, and assigns one objective
per dispatch. Independent dispatches may run in parallel; dependent work waits for a valid RESULT.
Before the native spawn, pipe the exact block to:

```bash
python3 .codex/scripts/orchestration_audit.py brief --role ROLE --dispatch DISPATCH
```

`--dispatch` and `--role` must match the block. The native start hook binds and delivers the registered
BRIEF to the runtime-issued agent ID. Registration after the spawn cannot satisfy the contract.

## RESULT

Every specialist ends its final message with this exact block:

```markdown
## RESULT
**Status:** complete | partial | blocked | failed
**Deliverables:** exact IDs and paths created or changed
**Evidence:** checks actually run, each prefixed ✅, ⚠️, or ❌; numbers name their source
**Open items:** unresolved work, deviations, and exact blockers
**Next:** one recommended next action or `none`
```

`complete` requires every Done-when condition and at least one concrete passing evidence line. A failed
test, unavailable source, unresolved gate, or partial artifact cannot be called complete. Never invent
an agent result, citation, number, path, or check.

## HANDOFF

```markdown
## HANDOFF
**Prior dispatch:** exact dispatch and returned agent identifier
**Prior status:** status copied from RESULT
**Artifacts:** exact verified IDs and paths produced
**Evidence:** evidence needed by this stage
**Known issues:** prior Open items quoted without reinterpretation
**This stage:** complete BRIEF for the dependent specialist
```

Build a HANDOFF only from the actual returned RESULT and artifacts verified on disk. When specialists
disagree, record the conflict and obtain targeted evidence; never silently choose or average.

## Run ledger

The launcher creates `.codex/runs/ORCH-YYYYMMDD-NNN/`. Native lifecycle hooks record the root session,
runtime-issued agent IDs, delivered BRIEF hashes, RESULT hashes/verdicts, and experiment-gate decisions
in an append-only SHA-256 chain. Prompt and RESULT bodies are not retained. A claim is verified only
when its native agent identifier, delivered BRIEF, and valid RESULT all exist. Inspect it with
`./orchestrate audit latest` or `./orchestrate audit RUN-ID --json`.
