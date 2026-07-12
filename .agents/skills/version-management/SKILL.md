---
name: version-management
description: Manage the Codex-only four-document research lifecycle, entry ownership, archival, carry-forward, and structured handoff. Use whenever a Codex agent writes research state or a phase/version transition is requested.
---

# Codex research version management

Use only the Codex state directory:

| File | Scope | Entries |
|---|---|---|
| `.codex/research/result.md` | current results | EXP, REPORT |
| `.codex/research/discussion.md` | current plans and scientific state | HYP, RES, DATASET, REV, QA, ADR, PLAN, STATE, REPORT |
| `.codex/research/error.md` | current defects and validity failures | BUG, VAL |
| `.codex/research/version.md` | append-only history | VER, CLEAN |

Never read or write same-named control documents at repository root or inside another provider
directory.

## Apply on every write

1. Read the current Codex discussion and unresolved error entries.
2. Preserve the existing tracker-table format and use the next global numeric ID.
3. Write only entry types owned by the assigned role.
4. Update the corresponding summary table in the same change.
5. Cite exact source IDs, paths, commits, logs, or fetched references.
6. Update `.codex/state/handoff.json` when session-level state changes.

## Transition a version

1. Have `writer` condense current results, decisions, hypotheses, datasets, and open issues.
2. Have `filemanager` append one VER entry to `.codex/research/version.md`, including the actual git
   commit and environment snapshot.
3. Reset the three current files from `.codex/templates/research/` only after the archive exists.
4. Carry open BUG/VAL/REV, active HYP/DATASET, and pending experiments forward with a source VER note.
5. Keep all numeric counters monotonic; never reuse or reset IDs.

Do not delete history, silently drop unresolved issues, mix multiple versions in current files, or
claim an archive exists without verifying it on disk.
