---
name: eval-battery-baseline
description: Baseline pass rate for the orchestration eval battery and the re-run rule for prompt-core changes
metadata:
  type: project
---

- 2026-07-07: Eval battery baseline (2026-07-07): 11/11 pass. Any prompt-core change in .claude/prompts/ requires re-running the battery (.claude/prompts/orchestration-evals.md) before merging.

**Why:** Establishes a known-good reference point for the orchestration eval battery so future regressions in prompt-core files are detectable against a concrete baseline rather than assumed.

**How to apply:** When reviewing any change touching `.claude/prompts/`, check whether `.claude/prompts/orchestration-evals.md` was re-run and compare the result against the 11/11 baseline before treating the change as validated. If the battery was not re-run for a prompt-core change, flag it (as a REV/VAL issue if severe enough) rather than assuming the change is safe.
