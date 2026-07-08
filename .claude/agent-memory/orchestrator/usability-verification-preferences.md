---
name: usability-verification-preferences
description: User wants verification runs with live functional tests and per-item pass/fail evidence, not design-level opinion; temporary verification artifacts live in usability_local_test/
metadata:
  type: user
---

The user (dhkim) evaluates this orchestration template itself and wants verification runs grounded in live functional tests with per-item PASS/FAIL evidence (exact command + observed output), explicitly not design-level opinion. When they say "등" (etc.) with a headline item, they mean: headline item verified deeply, plus a broad re-verification of the whole system.

**Why:** Stated in the 2026-07-08 re-verification request ("구현 제대로 되었는가?" + conductor note "concrete pass/fail evidence per item rather than design-level opinion"); mid-run they added two mandatory evaluation questions (literature-MCP coverage count with sourced numbers; live read-and-reason demonstration) — quantified, evidence-sourced answers were expected.

**How to apply:** For any verification/usability task: dispatch workers that execute the thing under test (live calls, simulated hook I/O, empirical agent probes), require findings files with verdict tables, and answer capability questions with sourced numbers or UNVERIFIED. Temporary verification artifacts (findings files, gate verdicts, reports) belong in `usability_local_test/` (gitignored), NOT the repo root or root docs. Do not create files matching `REPORT_*` from subagents — a harness write guard rejects that filename pattern (confirmed by probe in the 2026-07-08 v1 run). Related: [[harness-tool-fallbacks]].
