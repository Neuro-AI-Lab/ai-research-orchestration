# Delegation and result contracts

Fixed schemas for every orchestrator ↔ specialist exchange. The orchestrator sends a BRIEF; every
specialist ends its final message with a RESULT block. These schemas exist because a subagent has no
memory of the parent conversation and the orchestrator never sees the subagent's intermediate work —
the brief and the result are the *only* channel, so nothing load-bearing may live outside them.

## BRIEF — orchestrator → specialist

Include this block in every subagent prompt. Omit no field; write `none` explicitly if empty.

```markdown
## BRIEF
**Objective:** one sentence — what outcome, not what activity.
**Deliverable:** exact artifact(s) — entry type + destination doc, or file paths.
**Context:** doc IDs to read first (HYP-, EXP-, DATASET-, REV-, BUG-, ADR-), relevant file paths.
**Constraints:** conditions from prior reviews or decisions that bind this work (cite the IDs).
**Done when:** verifiable completion criteria — a check the specialist can run, not a vibe.
**Out of scope:** what NOT to do, including work owned by other agents.
```

Rules for the orchestrator:
- One objective per dispatch. Two objectives means two dispatches.
- Success criteria must be checkable by the specialist itself (a command, a doc entry existing,
  a checklist passing) — "do a good job" is not a criterion.
- Pass entry IDs, not summaries of entries, wherever possible: the specialist reads the doc itself
  and cannot inherit your misreadings.

## RESULT — specialist → orchestrator

Every specialist ends its final message with this block. The final message is data returned to the
orchestrator, not prose for a human — keep it dense.

```markdown
## RESULT
**Status:** complete | partial | blocked | failed
**Deliverables:** exact entry IDs appended and files written (paths).
**Evidence:** each verification actually run, prefixed ✅ (pass), ⚠️ (limitation), ❌ (fail),
with the exact command or check named. Key numbers include their source (log path or entry ID).
**Open items:** unresolved work. If blocked: the blocking question, quoted verbatim.
**Next:** the single recommended next action for the orchestrator (or `none`).
```

Rules for specialists:
- `complete` requires all done-when criteria met with evidence lines. Failing tests, partial
  implementations, or unresolved errors mean `partial` or `failed` — never `complete`.
- Evidence lines report what actually happened. Never fabricate a pass, weaken a check to make it
  pass, or mock data to appear successful. A ❌ with honest context is a good result.
- Numbers appear only with a source. A number you cannot source does not go in the block.
- If you deviated from the brief, say so in Open items with the reason.

## Handoff packet — for multi-stage work

When the orchestrator chains specialists (A's output feeds B), the dispatch prompt for B includes a
handoff packet built from A's RESULT:

```markdown
## HANDOFF
**Prior work:** what A did and its status (from A's RESULT, not re-imagined).
**Artifacts:** the exact IDs/paths A produced that B must consume.
**Known issues:** A's open items that affect B, quoted.
**This stage:** B's BRIEF (full schema above).
```
