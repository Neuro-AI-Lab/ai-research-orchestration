---
name: version-management
description: Manage the Codex-only four-document research lifecycle, entry ownership, archival, carry-forward, and structured handoff. Use whenever a Codex agent writes research state or a phase/version transition is requested.
---

# Codex research version management

Use only the checkout-bound Codex research workspace:

| File | Scope | Entries |
|---|---|---|
| `plan/PRD.md` | approved scope | requirements, constraints, acceptance criteria |
| `plan/CHECKLIST.md` | workflow state | stage, owner, status, evidence |
| `report/result.md` | current results | EXP, REPORT |
| `report/discussion.md` | current scientific state | HYP, RES, DATASET, REV, QA, ADR, PLAN, STATE |
| `report/issue.md` | current defects and validity failures | BUG, VAL |
| `report/version.md` | append-only history | VER, CLEAN |

Never read another provider's control directory or create parallel provider-private research state
and artifact subtrees outside the canonical workspace.

## Apply on every write

1. Read the current Codex discussion and unresolved issue entries.
2. Preserve the existing tracker-table format and use the next global numeric ID.
3. Write only entry types owned by the assigned role.
4. Update the corresponding summary table in the same change.
5. Cite exact source IDs, paths, commits, logs, or fetched references.
6. Update `.codex/state/handoff.json` when session-level state changes.

## Transition a version

1. Have `writer` condense current results, decisions, hypotheses, datasets, and open issues.
2. Have `filemanager` append one VER entry to `report/version.md`, including the verified git state
   (or `uncommitted`) and environment snapshot.
3. Reset the three current files from `.codex/templates/report/` only after the archive exists.
4. Carry open BUG/VAL/REV, active HYP/DATASET, and pending experiments forward with a source VER note.
5. Keep all numeric counters monotonic; never reuse or reset IDs.

Do not delete history, silently drop unresolved issues, mix multiple versions in current files, or
claim an archive exists without verifying it on disk.
