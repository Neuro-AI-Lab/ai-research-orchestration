---
name: harness-tool-fallbacks
description: SendMessage/TaskUpdate can be disabled mid-session for the orchestrator; workarounds for scope changes and task tracking
metadata:
  type: project
---

SendMessage and TaskUpdate/TaskCreate can become unavailable mid-session in this harness ("exists but is not enabled in this context") even after working earlier in the same session.

**Why:** Observed 2026-07-08 during PLAN-2026-28b — TaskUpdate and SendMessage both failed with "not enabled in this context" after TaskCreate/TaskUpdate had worked minutes earlier; could not course-correct a running background worker.

**How to apply:** Never build a plan that depends on messaging a running subagent. For mid-run scope additions (users of this project do add scope mid-run), dispatch a NEW parallel worker with a distinct findings file and explicit out-of-scope boundaries against the running worker's deliverable — this worked cleanly. For task tracking, treat PLAN status-update lines in discussion.md as the primary tracker; harness Task tools are a bonus, not a dependency. Related: [[usability-verification-preferences]].
