---
name: version-management
description: >-
  Manage the four-document version lifecycle: report/result.md (current version results),
  report/discussion.md (current version hypotheses, reviews, decisions), report/error.md (current
  version bugs and validity issues), report/version.md (historical archive). Trigger this
  skill when a version bump is needed, when archiving current work before a new
  phase, or when any agent writes to report/result.md, report/discussion.md, or report/error.md. Every
  agent must cognize these rules before writing to any report file.
---

# Version management

## The four documents

| File | Scope | Contains | Reset on version bump? |
|:-----|:------|:---------|:-----------------------|
| `report/result.md` | Current version only | Experiment results (EXP) and narrative summaries (REPORT) | Yes (archived first) |
| `report/discussion.md` | Current version only | Hypotheses, reviews, datasets, QA attestations, plans, decisions, state (HYP/RES/DATASET/REV/QA/ADR/PLAN/STATE/REPORT) | Yes (archived first) |
| `report/error.md` | Current version only | Bugs (BUG, filed by qa) and validity issues (VAL, filed by critic) | Yes (archived first) |
| `report/version.md` | All versions | Historical archive of all past working-doc content, errors, decisions | No (append-only) |

## Rules (every agent must follow)

### Rule 1: report/result.md, report/discussion.md, and report/error.md are current-version only
- These files contain ONLY the latest version's content.
- They are the working documents for the active version.
- Old entries from previous versions must never accumulate here.

### Rule 2: report/version.md is the append-only historical archive
- All past versions' results, discussions, errors, and decisions live here.
- Never delete content from report/version.md.
- Each archived version is stamped with `## [VER-NNN] <title> | YYYY-MM-DD`.

### Rule 3: archive before reset
- Before starting a new version, the current report/result.md, report/discussion.md, and report/error.md content MUST be archived into report/version.md first.
- Only then may the three working docs be cleared and reset for the new version.
- Unresolved items (open BUGs, open REVs, active HYPs, active DATASETs, pending experiments) carry forward into the new version's docs with a `Carried from VER-NNN` annotation.

### Rule 4: bugs and validity issues belong in report/error.md
- Bugs (BUG-NNN, filed by qa) and validity issues (VAL-NNN, filed by critic) are written to report/error.md for the current version — not to report/discussion.md and not to ad-hoc files.
- report/error.md follows the same lifecycle as the other working docs: current version only, archived into report/version.md at every version bump, open items carried forward.

### Rule 5: agent context priority
- Every agent must read context in this priority order (per CLAUDE.md):
  1. **User prompt** (highest priority) -- the user's current request overrides all other context.
  2. **CLAUDE.md** -- system-level rules, gates, and routing structure.
  3. **report/discussion.md** -- the current version's active context (open reviews, active hypotheses, decisions).
  4. **Own agent spec and assigned skills** -- capabilities, constraints, mandatory checklists.
  5. **report/version.md summary tables** -- historical context, only when needed.

## Version bump procedure

When a version milestone occurs (major code change, experiment batch complete, user request):

```
Step 1: Archive current version
  - Append to report/version.md under ## [VER-NNN] <title> | YYYY-MM-DD:
    a. Summary of what this version accomplished (condensed by writer)
    b. Condensed content of report/result.md (results, metrics, findings)
    c. Condensed content of report/discussion.md (hypotheses, decisions, reviews)
    d. Condensed content of report/error.md (BUG/VAL items, resolved vs carried)
    e. Environment snapshot (deps, hardware, git state)

Step 2: Reset working documents
  - Clear report/result.md to fresh template (header + empty summary tables)
  - Clear report/discussion.md to fresh template (header + carried-forward items only)
  - Clear report/error.md to fresh template (header + carried-forward open BUG/VAL items)

Step 3: Begin new version
  - report/result.md starts with clean summary tables
  - report/discussion.md and report/error.md start with only unresolved carry-forward items,
    each annotated `Carried from VER-NNN`
```

## Who triggers a version bump

- `orchestrator` decides when a version milestone is reached.
- `filemanager` executes the archive (writes to report/version.md).
- `writer` summarizes the version content for archiving.
- Any agent may request a version bump through `orchestrator`.

## What constitutes a version

A version represents a coherent phase of work. Examples:
- Initial preprocessing pipeline (VER-001)
- Feature extraction complete (VER-002)
- First experiment batch (VER-003)
- Pipeline correction and re-run (VER-004)
- New model architecture experiments (VER-005)

## Anti-patterns (do not do these)

1. **Rewriting report/result.md, report/discussion.md, or report/error.md without archiving first** -- this loses history.
2. **Filing bugs or validity issues outside report/error.md** -- BUG/VAL entries scattered across report/discussion.md or ad-hoc files break the gate checks that grep report/error.md.
3. **Accumulating entries from multiple versions in the working docs** -- leads to unreadable walls of text.
4. **Skipping the archive step** -- report/version.md must always contain the full history.
5. **Ignoring user prompt in favor of document context** -- user prompt is always highest priority.
