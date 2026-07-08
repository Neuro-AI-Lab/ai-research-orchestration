# error.md

Bugs and validity issues. Entry types: BUG (qa), VAL (critic).

## Bug and validity issue tracker

| ID | Title | Severity | Component | Status |
|:--|:--|:--|:--|:--|
| BUG-001 | `GATE_OVERRIDE`/env-prefixed run.sh bypasses the experiment gate entirely | critical | `.claude/hooks/experiment_gate.py` | resolved |
| BUG-002 | Read-only mentions of `python models/*.py` are falsely blocked | major | `.claude/hooks/experiment_gate.py` | resolved |
| BUG-003 | MCP/CLI literature-Zotero integration unreachable from research agents | major | `.claude/agents/brainstorm.md`, `.claude/agents/critic.md`, `.claude/agents/writer.md` | resolved |

## [BUG-001] GATE_OVERRIDE/env-prefixed run.sh bypasses the experiment gate entirely | 2026-07-08 | qa

**Severity:** critical
**Component:** `.claude/hooks/experiment_gate.py`
**Linked:** none (no EXP has used this code path yet; found during PLAN-2026-28b mechanical hook verification)
**Status:** open

### Reproduction

| Step | Action |
|:--|:--|
| 1 | Confirm all three pre-experiment gates are currently unmet: `grep '^## \[DATASET-' discussion.md` -> no match; `grep '^## \[BUG-' error.md` -> no open critical BUG before this entry; `grep '^## \[REV-' discussion.md` -> no match. |
| 2 | Feed the hook a plain launch: `echo '{"tool_name":"Bash","tool_input":{"command":"./run.sh test"}}' \| CLAUDE_PROJECT_DIR=$PWD python3 .claude/hooks/experiment_gate.py`. Result: exit 2, "GATE BLOCKED ... no DATASET entry". Correct. |
| 3 | Feed the hook the exact override syntax CLAUDE.md documents, citing an ADR that does not exist: `echo '{"tool_name":"Bash","tool_input":{"command":"GATE_OVERRIDE=ADR-999 ./run.sh test"}}' \| CLAUDE_PROJECT_DIR=$PWD python3 .claude/hooks/experiment_gate.py`. |
| 4 | Also try a routine, non-override env-prefixed launch: `command:"FOO=bar ./run.sh test"` through the same invocation. |

**Expected:** Per CLAUDE.md ("When to break the rules"): "the mechanical gate hook verifies that the cited ADR actually exists in discussion.md before letting the run through. An override citing a nonexistent ADR is rejected." Step 3 should exit 2 with a stderr message naming ADR-999 as not found (this is also QA test item 2 in the PLAN-2026-28b brief). Step 4 should exit 2 exactly like step 2, since no override was even claimed and the gates remain unmet.

**Actual:** Both step 3 and step 4 exit **0** (silent allow), with empty stdout/stderr — no rejection message, no block. Root cause: `EXP_LAUNCH`'s run.sh/evaluate.sh alternative requires the match to begin at start-of-string/segment, immediately after a shell operator (`;`, `&`, `\|`, `(`), or immediately after an executor keyword (`bash`/`sh`/`setsid`/`nohup`/`exec`) followed by whitespace:
```python
EXP_LAUNCH = re.compile(
    r'(^|[;&|(]\s*|\b(?:bash|sh|setsid|nohup|exec)\s+)(\./)?(run|evaluate)\.sh\b'
    r'|python[0-9.]*\s+\S*models/\S+\.py'
)
```
A leading `NAME=value ` assignment (standard POSIX shell syntax, and the exact form `GATE_OVERRIDE=ADR-NNN <cmd>` that CLAUDE.md itself prescribes) sits between the anchor and `run.sh`/`evaluate.sh`, so none of the anchor alternatives match. `EXP_LAUNCH.search(cmd)` returns `None`, and `main()` returns 0 immediately (line "if not EXP_LAUNCH.search(cmd): return 0") — the override-validation branch, and the gate-check branch, are never reached. This means: (a) the documented override mechanism is unreachable for `run.sh`/`evaluate.sh` when invoked exactly as instructed — the ADR-existence check is dead code for this launch path; (b) more broadly, prefixing *any* environment variable assignment (e.g. a routine `CUDA_VISIBLE_DEVICES=0 ./run.sh train`) silently defeats the gate with no override intent at all.

**Minimal repro:** `tests/repro/test_bug_001.py` (currently 2 of 3 tests FAIL against the unpatched hook, reproducing both the documented-override case and the general env-prefix case; the plain `./run.sh` sanity case passes).

### Resolution

Independently re-verified (not taking developer's word) by simulating hook stdin directly against the live `.claude/hooks/experiment_gate.py`:

| Command | Expected | Observed | Exit |
|:--|:--|:--|:--|
| `GATE_OVERRIDE=ADR-999 ./run.sh test` | rejected, nonexistent ADR named | stderr: `GATE: override cited ADR-999, but no such ADR exists in discussion.md...` | 2 |
| `FOO=bar ./run.sh test` | blocked, gates unmet | `GATE BLOCKED ... open critical BUG-001 ... no DATASET entry` | 2 |
| `GATE_OVERRIDE=ADR-001 ./run.sh test` (ADR-001 exists in discussion.md) | allowed | silent allow, no stderr | 0 |
| `./run.sh test` (plain) | blocked, gates unmet | `GATE BLOCKED ... open critical BUG-001 ... no DATASET entry` | 2 |

All four match spec exactly. Regression suite: `python3 -m pytest tests/repro/ -v` → 10/10 passed (`tests/repro/test_bug_001.py` 3/3, `tests/repro/test_bug_001_002_fix.py` 5/5 incl. positive-override and real-launch-still-blocked cases, `tests/repro/test_bug_002.py` 2/2), exit 0. Ran without `--timeout`: `pytest-timeout` is listed in `requirement.txt` but not actually pip-installed in this environment (`python3 -c "import pytest_timeout"` → `ModuleNotFoundError`); flagged, not blocking (suite runs in 0.21s).

| Field | Value |
|:--|:--|
| Fixed by | uncommitted working-tree change to `.claude/hooks/experiment_gate.py` (command-segment-position matching via `_segment_starts()` + `re.match`, `_ENV_CHAIN` prefix, `GATE_OVERRIDE` scoped to the matched launch's env-chain); see PLAN-2026-28c subtask 2 status update, discussion.md. Not yet committed — pending PLAN-2026-28c subtask 6. |
| Regression test | `tests/repro/test_bug_001.py`, `tests/repro/test_bug_001_002_fix.py` |
| Verified by | qa, 2026-07-08 |

**Status:** resolved

---

## [BUG-002] Read-only mentions of `python models/*.py` are falsely blocked | 2026-07-08 | qa

**Severity:** major
**Component:** `.claude/hooks/experiment_gate.py`
**Linked:** none
**Status:** open

### Reproduction

| Step | Action |
|:--|:--|
| 1 | Confirm the intended reference behavior for the sibling pattern: `command:"cat run.sh"` through the hook -> exit 0 (pass-through), matching the hook's own docstring: "read-only mentions — `cat run.sh`, `grep foo evaluate.sh`, `bash -n run.sh` — pass through." |
| 2 | Feed the hook a read-only mention of a python model path: `echo '{"tool_name":"Bash","tool_input":{"command":"grep -rn '"'"'python models/train.py'"'"' README.md"}}' \| CLAUDE_PROJECT_DIR=$PWD python3 .claude/hooks/experiment_gate.py`. |

**Expected:** Per the hook's documented intent (applied consistently to both alternatives of `EXP_LAUNCH`), a read-only reference to a `python models/*.py` invocation inside a `grep`/`cat`/`echo` argument should pass through (exit 0), exactly as `cat run.sh` does.

**Actual:** Exit 2, blocked: `GATE BLOCKED - experiment launch stopped by the mechanical gate ... no DATASET entry in discussion.md`. Root cause: the second `EXP_LAUNCH` alternative, `python[0-9.]*\s+\S*models/\S+\.py`, carries no command-position anchor (unlike the first alternative's `(^|[;&|(]\s*|\b(?:bash|sh|setsid|nohup|exec)\s+)` prefix), so it matches the substring anywhere in the command text — inside quotes, comments, or grep patterns — with no notion of "am I actually the command being launched." Any command whose text happens to contain a string matching that pattern is blocked, regardless of whether it launches anything.

**Minimal repro:** `tests/repro/test_bug_002.py` (1 of 2 tests FAILs against the unpatched hook, reproducing the false-positive block; the `cat run.sh` reference-behavior sanity case passes).

### Resolution

Independently re-verified by simulating hook stdin directly against the live `.claude/hooks/experiment_gate.py`:

| Command | Expected | Observed | Exit |
|:--|:--|:--|:--|
| `echo "python models/train.py"` | read-only, allowed | silent allow, no stderr | 0 |
| `wc -l setup.sh evaluate.sh` | read-only, allowed | silent allow, no stderr | 0 |
| `python models/train.py` (real launch) | still blocked, gates unmet | `GATE BLOCKED ... open critical BUG-001 ... no DATASET entry` | 2 |
| `./evaluate.sh x` (real launch) | still blocked, gates unmet | `GATE BLOCKED ... open critical BUG-001 ... no DATASET entry` | 2 |

All four match spec exactly — false-positive fixed without weakening real-launch detection. Regression suite: `python3 -m pytest tests/repro/ -v` → 10/10 passed, exit 0 (same run as BUG-001; `tests/repro/test_bug_002.py` 2/2 green). `pytest-timeout` not run (not pip-installed despite being in `requirement.txt`; `ModuleNotFoundError` on import) — ran plain `pytest`, not blocking.

| Field | Value |
|:--|:--|
| Fixed by | uncommitted working-tree change to `.claude/hooks/experiment_gate.py` (command-position anchoring applied to the python alternative via `_SCRIPT_LAUNCH`/`_PY_LAUNCH` + `re.match` at segment offsets, replacing the old unanchored `\b`-based regex); see PLAN-2026-28c subtask 2 status update, discussion.md. Not yet committed — pending PLAN-2026-28c subtask 6. |
| Regression test | `tests/repro/test_bug_002.py`, `tests/repro/test_bug_001_002_fix.py` (`.sh`-tail cases) |
| Verified by | qa, 2026-07-08 |

**Status:** resolved

---

## [BUG-003] MCP/CLI literature-Zotero integration unreachable from research agents | 2026-07-08 | qa

**Severity:** major
**Component:** `.claude/agents/brainstorm.md:4`, `.claude/agents/critic.md:4`, `.claude/agents/writer.md:4` (`tools:` frontmatter line in each)
**Linked:** none (no EXP has used the literature/Zotero path; found during PLAN-2026-28b usability re-verification)
**Status:** open

### Reproduction

| Step | Action |
|:--|:--|
| 1 | Static frontmatter audit — grep the `tools:` line in all three agent specs: `grep -n '^tools:' .claude/agents/brainstorm.md .claude/agents/critic.md .claude/agents/writer.md`. Confirmed values: `brainstorm.md:4` = `Read, Grep, Glob, WebSearch, WebFetch, Write, Edit`; `critic.md:4` = `Read, Grep, Glob, Write, Edit`; `writer.md:4` = `Read, Grep, Glob, Write, Edit`. None lists `Bash` or any `mcp__*` tool. Full audit trail: `usability_local_test/_verify_mcp.md` check 5 (table, lines 98-103). |
| 2 | Empirical confirmation — live `brainstorm` session tool inventory enumerated from its own function-call interface: `Read, WebSearch, WebFetch, Write, Edit, Grep, Glob` — no `Bash`, no `mcp__*`, matching the frontmatter exactly. Full trace: `usability_local_test/_verify_brainstorm_probe.md` section 1. |
| 3 | Live call `mcp__literature__lit_search(query="electrodermal activity craving detection")` from the same brainstorm session. Verbatim result: `<tool_use_error>Error: No such tool available: mcp__literature__lit_search</tool_use_error>` (`_verify_brainstorm_probe.md` section 2). |
| 4 | Live call `mcp__zotero__zotero_search(query="craving")` from the same session. Verbatim result: `<tool_use_error>Error: No such tool available: mcp__zotero__zotero_search</tool_use_error>` (`_verify_brainstorm_probe.md` section 3). |

**Expected:** Per CLAUDE.md ("Zotero library integration (CLI + MCP) wired into research agents", commit 92be108) and each agent's own body prose (`brainstorm.md:55-58`, `critic.md:47-48`, `writer.md:113` all instruct calling `python3 .claude/scripts/lit_search.py` / `zotero_mcp.py`), the research agents should be able to reach the integration via at least one of: the MCP tools (`mcp__literature__lit_search`, `mcp__literature__lit_fetch`, `mcp__zotero__zotero_search`, `zotero_item`, `zotero_fulltext`, `zotero_bibtex`, `zotero_collections`, `zotero_add`), or `Bash` (for the documented CLI fallback `.claude/scripts/lit_search.py`, `.claude/scripts/zotero_mcp.py`).

**Actual:** Both access paths are dead for `brainstorm`, `critic`, and `writer`. The MCP servers themselves are implemented correctly and fully functional (`_verify_mcp.md` checks 1-4 all PASS — protocol handshake, tool schemas, credential handling, and live calls to `lit_search`, `lit_fetch`, `zotero_search`, `zotero_item`, `zotero_bibtex`, `zotero_collections` all returned real data when invoked directly / via a session with the tools granted). But none of the three research agents' `tools:` frontmatter grants `Bash` or any `mcp__*` tool name, so from inside an actual agent session both the MCP path and the CLI fallback return "No such tool available" / are simply absent from the tool list — the agent silently falls back to `WebSearch`/`WebFetch` with no error surfaced, so the Zotero-library-first policy documented in `.claude/ZOTERO.md` and the agent bodies is never honored in practice. The prose and the frontmatter allowlist have drifted apart.

**Minimal repro:** none added — this is a static frontmatter defect (a one-line list omission in three YAML headers), not a code-path bug reproducible via a `tests/` fixture; the two verification files above (`usability_local_test/_verify_mcp.md`, `usability_local_test/_verify_brainstorm_probe.md`) constitute the reproduction record. Fix is a frontmatter edit (developer/filemanager remit, pending user decision on whether to grant `mcp__*` tools, `Bash`, or both) — out of scope for this entry.

### Resolution

Independently re-verified via static frontmatter grep plus the live re-probe file (I cannot dispatch agents myself, so the probe file is the authoritative runtime check; its findings are cited, not taken on faith — the probe's own text was inspected directly):

`grep -n '^tools:' .claude/agents/{brainstorm,critic,writer}.md` →
- `brainstorm.md:4` — 8 `mcp__*` names (`lit_search`, `lit_fetch`, `zotero_search`, `zotero_item`, `zotero_fulltext`, `zotero_collections`, `zotero_add`, `zotero_bibtex`)
- `critic.md:4` — 7 `mcp__*` names (same set minus `zotero_add`)
- `writer.md:4` — 7 `mcp__*` names (same set minus `zotero_add`)

`zotero_add` confirmed present only in brainstorm's `tools:` line (the other three hits are body-prose mentions, not grants). `grep -n '^tools:.*Bash' .claude/agents/{brainstorm,critic,writer}.md` → no match (exit 1) — no Bash added to any of the three, matching ADR-001's least-privilege decision.

Runtime evidence, quoted from `/tmp/claude-1000/-home-neuroai-users-dhkim-neuroai-agent-template/bbec35b7-668b-4d33-ae3e-f42f67b03f2e/scratchpad/reprobe_brainstorm.md` (live brainstorm session, 2026-07-08): "BUG-003's failure mode ('No such tool available' on `mcp__*` calls) is resolved for the brainstorm agent: all 8 MCP tool names are present in this session's interface, and both a literature-search and a Zotero-search call returned real, verbatim, on-topic data rather than errors." The probe's `lit_search` call returned a real 15-row table (incl. arXiv:1707.08287v1 and a directly on-topic craving-detection PubMed hit); `zotero_search("craving")` returned 5 real user-library items incl. `[YUCAN6SP]`, `[R7HAWDG4]`; `zotero_add` confirmed present but not invoked (presence-only check, as instructed).

Frontmatter grants for critic/writer were not independently re-probed live in this pass (no dispatch authority) — resolution for those two rests on the static grep match to ADR-001's spec plus the shared code path (same MCP servers, same tool-grant mechanism proven working for brainstorm); flagged as a minor residual gap, not sufficient to withhold `resolved` given the static evidence is unambiguous and the mechanism is identical.

| Field | Value |
|:--|:--|
| Fixed by | uncommitted working-tree change to `.claude/agents/{brainstorm,critic,writer}.md` frontmatter (`tools:` line), per ADR-001 (discussion.md); see PLAN-2026-28c subtasks 3-4 status update, discussion.md. Not yet committed — pending PLAN-2026-28c subtask 6. |
| Regression test | none (static frontmatter defect, no `tests/` fixture applicable — see original Minimal repro note); runtime evidence is `/tmp/claude-1000/.../scratchpad/reprobe_brainstorm.md` |
| Verified by | qa, 2026-07-08 |

**Status:** resolved

---

<!-- Entries are append-only. Format:

## [BUG-NNN] short title | YYYY-MM-DD | qa
Severity: critical | major | minor
Component: <file path>
Steps to reproduce:
  1. ...
Expected: ...
Actual: ...
Linked: EXP-... (if any experiment uses this code path)
Status: open
---

## [VAL-NNN] validity issue | YYYY-MM-DD | critic
Target: EXP-... or PLAN-...
Issue: <one sentence>
Why blocking: <reasoning>
Linked review: REV-NNN
Status: open
---
-->
