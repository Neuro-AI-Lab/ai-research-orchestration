# discussion.md

Hypotheses, research notes, decisions, reviews, plans, and state. Multi-writer document sectioned by entry prefix.

## Plan tracker

| Plan | Goal | Status |
|:--|:--|:--|
| PLAN-2026-28 | Adversarial submission-grade review of example.pdf + multiagent usability report | complete — firm verdict MAJOR REVISION (JBHI); two report files delivered; critic gate passed (4 defects incl. one AUROC misquote corrected + verified) |
| PLAN-2026-28b | Usability re-verification of the orchestration system, headlined by functional verification of the paper-research MCP servers (literature + zotero) | complete — MCP servers PASS (live-verified) but research-agent wiring FAIL (BUG-003); coverage 4 backends / ~300M+ unique works; hooks 7/8 (BUG-001 critical: gate override bypass); v2 report delivered, critic gate PASS-WITH-FIXES, fixes applied + verified |
| PLAN-2026-28c | README coverage section + fix BUG-001/002/003 + hygiene items; usability-folder follow-ups dropped by user | complete — README coverage block added (figures byte-matched); all three BUGs fixed and qa-verified resolved (tests/repro 10/10 green; live MCP re-probe passed); ADR-001 grants applied; hygiene done; usability follow-ups dropped-by-user |
| PLAN-2026-28d | Split unpushed bfc4e00 into 5 per-concern branches/PRs (fix gate / feat MCP access / docs README / chore hygiene / docs research-log) | complete — approved + executed; 5 branches pushed, 5 PRs open (merge docs/research-log PR last), 3 follow-up issues created |

## [PLAN-2026-28] Manuscript review of example.pdf for JBHI fit | 2026-07-08 | orchestrator-opus

**Goal:** Deliver a rigorous, fair, submission-grade peer review of example.pdf (research validity/타당성, novelty, experimental & statistical analysis, per-claim strength-of-evidence, JBHI-fit + explicit recommendation) plus a grounded usability evaluation of this multiagent system, as two temporary report files distinct from the four root docs.

### Subtasks

| # | Subtask | Specialist | Success criterion | Gate |
|:--|:--|:--|:--|:--|
| 1 | Adversarial validity review: statistics, multiple comparisons across 152 features, XAI-attribution soundness, sample size/power, leakage symptoms, overclaiming, confounds, generalizability | critic | `_review_critic.md` written; every cited number has a page/section locator or is marked UNVERIFIED | — |
| 2 | Statistical/analysis-design soundness: LMM specification, 152-feature extraction, Zero–Low–High labeling construct, class balance, subject- vs window-level leakage risk from the described pipeline | data | `_review_data.md` written; findings grounded in PDF locators; no fabricated numbers | — |
| 3 | Novelty & literature positioning vs prior craving-detection / wearable autonomic physiomarker / VR cue-reactivity / XAI-screening work | brainstorm | `_review_brainstorm.md` written; ≥3–5 closest prior works with verifiable identifiers | — |
| 4 | Synthesize Report 1 (manuscript review) + Report 2 (multiagent usability) | writer | `REVIEW_manuscript_example.md` + `REPORT_multiagent_usability.md` written; every number traces to a locator or is UNVERIFIED | — |
| 5 | Faithfulness gate on Report 1 | critic | no overclaim / fabricated number in Report 1; JBHI recommendation defensible against the evidence | critic-before-report (mandatory) |

**Sequence:** subtasks 1–3 parallel (independent reads) → 4 (synthesis) → 5 (gate) → one writer fix if the gate flags issues.
**Blocking:** No experiments run in this task; the pre-experiment gates (qa code, data-split) are not triggered. The critic-before-report gate is mandatory and fires at subtask 5.
**Note:** example.pdf is the user's own manuscript being prepared for JBHI. The review must be adversarial and fair (genuine strengths listed too), truth-oriented on whether it survives JBHI review. This is a review of the PDF as written — no reproduced numbers may be fabricated; every claimed value is quoted with a locator or marked UNVERIFIED.

---

## [STATE-2026-07-08] | orchestrator-opus

**Task:** PLAN-2026-28 — deep review of example.pdf for JBHI fit + multiagent usability report.

**Outcome:** BLOCKED on the source file. example.pdf is structurally truncated — missing `trailer`/`xref`/`%%EOF`; only 7 of 13 declared page objects recoverable; pages 2–6 have empty `/Resources` (no `/Font`), the 7th recovered page object has no `/Contents`. Only page 1 (title / abstract / index terms / intro) is readable. Confirmed independently by data (byte-level forensics + `pikepdf`/`qpdf` carving), critic, and brainstorm (all hit page-1-only). A full validity/statistical/experimental-analysis review and a firm JBHI verdict are not possible until an intact file is supplied.

**Delivered (two temporary report files — NOT root docs):**

| File | Content | Gate |
|:--|:--|:--|
| `REVIEW_manuscript_example.md` | Honest PARTIAL manuscript review: blocker banner; novelty & positioning COMPLETABLE-NOW (brainstorm, 11 verified prior works); validity/stats/experimental-analysis/final-JBHI-verdict BLOCKED-PENDING-FILE; provisional lean only | critic faithfulness gate PASS |
| `USABILITY_multiagent_system.md` | Full grounded usability evaluation of this run | — (process report) |

**Evidence base retained:** `_review_critic.md`, `_review_data.md`, `_review_brainstorm.md` (repo root) — the detailed findings the reports synthesize.

**Resume point:** on receipt of an intact/re-exported example.pdf, re-run critic + data on pages 2–13, then have writer convert the BLOCKED-PENDING-FILE sections of `REVIEW_manuscript_example.md` into confirmed findings and issue a firm accept/minor/major/reject recommendation. The brainstorm novelty section already stands.

**Open:** awaiting intact example.pdf from user. No experiments run; no BUG/VAL filed.

---

## [STATE-2026-07-08 · resume complete] | orchestrator-opus

**Task:** PLAN-2026-28 — review of example.pdf for JBHI fit + multiagent usability report. **Now COMPLETE** (source file restored & verified; supersedes the blocked-phase snapshot above).

**Firm verdict:** MAJOR REVISION (equivalent) for JBHI. Credible, honestly-reported core (converging LMM + XAI signals on EDA/HRV; graded craving labels with real reliability numbers r=0.915 / ρ mean 0.639, Figs 7–8; appropriate subject + session-nested LMM random-effects, Eq 2/3 p.5 §III-E), but headline effect magnitudes cannot be certified as worded due to three confirmed, data-collection-free gaps: (1) no multiplicity correction across the 152-feature LMM screen (α=.05 uncorrected, p.5 §III-E); (2) subject-level leakage — 5-fold CV grouped at trial level, no subject grouping (p.6 §IV-A), inflating classifier metrics (Tables III–VII) and SHAP rankings (Fig.11 p.9), directly threatening the "EDA strongest" claim; (3) selection-then-validation double-dipping (p.6 §IV-A / p.10 Table VII). Also: no classifier variance/CI/seed, no per-class N, no external validation, Abstract JITAI overreach, uncleared "< 250 words" placeholder (p.1), no formal ICC/Cronbach, no COI statement.

**Provisional-flag resolution:** 8 original abstract-stage provisional flags (Major #1–7 + Minor #1) plus 2 new full-text flags (Major #8 trial-level CV; Major #9 no classifier variance/CI/seed) = 10 resolved items; verdict split 7 fully confirmed / 2 partially confirmed (per-class N/power; COI statement) / 1 retracted (label reliability — r=0.915 / ρ do exist, though not a formal ICC/Cronbach). data resolved the leakage checklist to 3 PASS / 1 FAIL (group split) / 1 not-reported / 1 N/A. brainstorm confirmed the 4 relevant prior works are uncited (Tsai 2021, Zhang 2023, Carreiro 2020, Chen 2022; refs [1]–[48], pp.11–13); novelty = incremental synthesis (Zhang 2023 null skin-conductance tensions the EDA claim).

**Gate:** critic-before-report gate ran on the firm review; flagged 4 locator/number defects (incl. a synthesis-introduced AUROC misquote, PTT-only RF 61.15→59.47 Table V p.8) — all corrected and orchestrator-verified via grep. No blocking VAL; no BUG.

**Deliverables (two temporary report files — NOT root docs):** `REVIEW_manuscript_example.md` (firm review, corrected + verified) and `USABILITY_multiagent_system.md` (usability eval + resume-phase addendum). Evidence base retained: `_review_critic.md`, `_review_data.md`, `_review_brainstorm.md`.

**Open/next:** optional — a formal critic re-gate token on the corrected review before external circulation, and confirmation of two remaining candidate citation gaps (Zeng 2026, Newlin 1985). No experiments run.

---

## [PLAN-2026-28b] Usability re-verification incl. paper-research MCP | 2026-07-08 | orchestrator

**Goal:** Re-run the usability verification of the AI research orchestration system (previous run: `usability_local_test/USABILITY_multiagent_system.md`, orchestrator-opus, 2026-07-08), this time headlined by a functional check of the paper-research MCP integration (literature + zotero servers), with concrete pass/fail evidence per item rather than design-level opinion. This run uses the Fable 5 orchestrator.

### Subtasks

| # | Subtask | Specialist | Success criterion | Gate |
|:--|:--|:--|:--|:--|
| 1 | MCP verification: (a) config/source correctness of `.mcp.json`, `literature_mcp.py`, `zotero_mcp.py`, credential handling; (b) live MCP calls (lit_search/lit_fetch, zotero_search/collections) returning real results; (c) CLI counterparts exercised | general-purpose worker | `usability_local_test/_verify_mcp.md` written; every claim carries the exact command/tool call + observed output; no credentials leaked into the file | — |
| 2 | Empirical MCP-reachability probe from a research agent: does `brainstorm` actually have the MCP tools its spec/CLAUDE.md claim? | brainstorm | RESULT reports the actual tool inventory and the outcome of an attempted lit_search call | — |
| 3 | Mechanical hook/gate verification: `experiment_gate.py` (block + GATE_OVERRIDE with fake ADR rejected), `session_brief.py`, `session_close_gate.py`, `run_with_status.sh`, `sweep_summary.py` | qa | `usability_local_test/_verify_hooks.md` written; per-item PASS/FAIL with the exact command run | — |
| 4 | Structural consistency audit: 10 agent specs (frontmatter model/skills/tools vs CLAUDE.md tables), 8 skills, prompts, hook registration in settings, handoff.json validity/freshness, agent-memory dirs | filemanager | `usability_local_test/_verify_structure.md` written; per-item PASS/FAIL/MISMATCH with file evidence | — |
| 5 | Synthesize v2 usability report superseding the prior one, with pass/fail matrix and comparison to the previous run's findings | writer | `usability_local_test/USABILITY_multiagent_system.md` updated: v2 report on top, prior run preserved as appendix; every claim traces to a `_verify_*.md` finding | — |
| 6 | Faithfulness gate on the v2 report | critic | No overclaim/fabricated evidence; pass/fail verdicts match the underlying findings files | critic-before-report (mandatory) |

**Sequence:** subtasks 1–4 parallel (independent verifications, separate findings files) → 5 (synthesis) → 6 (gate) → one writer fix round if flagged.
**Blocking:** No experiments run; pre-experiment gates not triggered (hook tests simulate inputs, they do not launch real runs). Critic-before-report gate is mandatory at subtask 6.

**Status update (2026-07-08, subtask 1 complete):** MCP verification worker returned `complete`: both MCP servers implemented properly and fully functional — static audit PASS (JSON-RPC stdio protocol correct incl. -32601 fallback; `zotero_mcp.py` reads creds from env only; `settings.local.json` gitignored at `.gitignore:38`, no secret committed); direct stdio handshake PASS on both servers; live MCP calls PASS (`lit_search` "Attention Is All You Need" → real paper, cites 6582; `lit_fetch` arxiv 1706.03762 resolves; `zotero_search` "craving" → 5 real items; `zotero_collections` → ~100 collections; `zotero_item`/`zotero_bibtex` → full metadata + valid BibTeX; no writes); CLI counterparts PASS. FAIL item (HIGH): `brainstorm.md:4`, `critic.md:4`, `writer.md:4` `tools:` frontmatter grants neither `Bash` nor any `mcp__*` tool — the commit-92be108 claim "wired into research agents" is documentary only. LOW: `lit_search.py:235-238` no-arg output is a docstring dump, not real argparse help. Evidence: `usability_local_test/_verify_mcp.md`. Corroborates subtask 2's empirical probe.

**Status update (2026-07-08, subtask 4 complete):** Structural audit returned `complete`: all 10 agent specs match CLAUDE.md model-tier and skills tables exactly (incl. developer version-management carve-out); 8 skills present, no orphans; 3 prompts present and cross-referenced; 3 hooks registered on correct events in `.claude/settings.json`; `handoff.json` valid JSON with documented keys; `.gitignore` verified via `git check-ignore` (data/, experiments/, settings.local.json; no secrets tracked); HEAD = 052ab17. MISMATCH (minor): CLAUDE.md agent-memory layout comment names 3 roles but 4 populated dirs exist (`orchestrator-opus/` unmentioned); `.pytest_cache/` not gitignored. Incidental finding handed to qa for confirmation: `experiment_gate.py` regex false-positive — anchor `\bsh\s+` matches the tail of any `*.sh` filename followed by a space, so e.g. `wc -l ... setup.sh evaluate.sh` was blocked as an "experiment launch". Evidence: `usability_local_test/_verify_structure.md`.

**Status update (2026-07-08, subtask 1b complete):** Coverage/read-and-reason worker returned `complete`. Q1 coverage PASS: exactly 4 backends in `literature_mcp.py` `SOURCES` (arXiv, OpenAlex, PubMed, Semantic Scholar; `all` = fan-out over the four, ResearchGate deliberately excluded per ToS; no dead backend). URL-sourced coverage 2026-07-08: arXiv >3M preprints (info.arxiv.org/about); OpenAlex 319,077,593 works / 282,505 sources (live api.openalex.org meta.count); PubMed 40,830,218 citations, MEDLINE >5,200 journals (nlm.nih.gov); S2 >200M papers (venue count UNVERIFIED). Honest caveat: de-duplicated unique reach ≈ ~300M+ works across ~290,000+ venues — the ~560M gross sum double-counts aggregator re-indexing. Q2 read-and-reason: content depth PARTIAL — literature MCP stops at abstract+metadata (`lit_fetch` on a PDF URL returns raw `%PDF-1.5` bytes, no parser; PubMed path returns a no-abstract placeholder, `literature_mcp.py:160`); reasoning PASS — demonstrated live on arxiv:1706.03762 (grounded 28.4/41.8 BLEU) AND on post-cutoff arXiv:2605.26355 (submitted 2026-05-25, grounded-vs-background labeled), proving reasoning depends on fetched content, not memory. `zotero_fulltext` returned 58.8 KB parsed full text (read-only) — the only true full-text-reading path, and it works. Usability limit: keyless S2 hits HTTP 429 on the `all` fan-out without `S2_API_KEY`. Evidence: `usability_local_test/_verify_mcp_coverage.md`.

**Status update (2026-07-08, subtask 3 complete — wave 1 done 5/5):** qa hook verification returned `complete`: 7/8 PASS — gate blocks `./run.sh test` / `./evaluate.sh x` / `python models/train.py` with unmet-gate messages (exit 2); harmless commands pass; `session_brief.py` emits correct handoff/STATE/run-scan context; `session_close_gate.py` correctly blocks on stale handoff.json, loop-guards on `stop_hook_active`, confirmed read-only; `run_with_status.sh` status.json lifecycle correct (completed/failed + run.log capture); `sweep_summary.py` builds correct comparison table, flags incomplete runs, graceful error exits (66/64). FAIL: `GATE_OVERRIDE=ADR-999 ./run.sh test` → exit 0 SILENT ALLOW instead of override rejection — any `NAME=value ` prefix (including the exact override syntax CLAUDE.md prescribes) breaks the launch-regex anchor, so the hook allows before override validation is reached → **BUG-001 (critical)** filed to error.md with red regression test `tests/repro/test_bug_001.py`. Also **BUG-002 (major)**: python-path and override regexes lack command-position anchors → false positives (qa's own echoed JSON payload tripped the live gate mid-test) — same root-cause family as subtask 4's incidental `\bsh\s+` tail-match finding; regression test `tests/repro/test_bug_002.py`. Noted for filemanager: `pytest-timeout` absent from requirement.txt. Orchestrator verified both BUG entries exist in error.md (grep). Evidence: `usability_local_test/_verify_hooks.md`. Proceeding to writer synthesis (subtask 5).

**Status update (2026-07-08, PLAN COMPLETE):** Writer fix round applied all three changes (check-7 misattribution corrected to checks 5–6; "never attempted" inference replaced with the gate's hedge; wiring-gap row cites BUG-003) with appendix untouched; qa filed **BUG-003 (major, open)** — MCP/CLI literature-Zotero integration unreachable from research agents (`error.md:11` tracker row + `:66` entry). Orchestrator fan-in verification: grep confirms BUG-003 in error.md, BUG-003 cross-reference at report line 113, corrected check-5/6 wording at line 160. Per the critic gate, no re-gate needed (fixes stayed within the two cited sentences + one cross-reference, no numbers/verdicts touched). Deliverable final: `usability_local_test/USABILITY_multiagent_system.md` (v2 + prior run as appendix).

**Status update (2026-07-08, subtasks 5–6):** Writer delivered the v2 report (prior run preserved verbatim as appendix; done-when greps verified; no REPORT_* file created). Critic-before-report gate ran fresh-context: verdict **PASS-WITH-FIXES** (`usability_local_test/_gate_critic_v2.md`) — all coverage figures, verdict-matrix rows, defect severities, UNVERIFIED markings, and hedging verified faithful (arithmetic checked, e.g. ≈563M gross sum); Issue 1 (major): report lines 158–160 misattribute a ⚠️ to `_verify_structure.md` RESULT check-7 (only checks 5–6 carry ⚠️, verified by critic grep); Issue 2 (minor): one unsupported inference in the comparison-with-appendix section. No VAL filed (wording defect, not process validity). Critic recommendation adopted: formally file the HIGH MCP wiring gap to error.md before plan close. Next: writer fix round (Issues 1+2, one round) in parallel with qa BUG filing (wiring gap) — different files, write-safe.

**Status update (2026-07-08):** User scope addition mid-run (verbatim: "literature MCP는 탐색가능한 conference, journal, paper search platform등 총 몇개의 학술지/아카이브 등을 탐색할 수 있으며, 실제로 탐색한 논문을 읽고 사고할 수 있는가에 대한 평가가 이뤄져야 한다."). Added subtask 1b (general-purpose worker → `usability_local_test/_verify_mcp_coverage.md`): (i) coverage count — enumerate literature-MCP backends from the implementation source; report direct backend count AND documented effective venue/index coverage per aggregator, every number sourced or marked UNVERIFIED; (ii) read-and-reason — live end-to-end search → fetch → substantive reasoning over the fetched content, reporting retrievable content depth per backend and where the capability stops. Subtask 2 (brainstorm probe) complete: brainstorm has NO MCP tools and NO Bash (live allowlist `Read, Grep, Glob, WebSearch, WebFetch, Write, Edit`); both MCP calls returned "No such tool available" verbatim — the CLAUDE.md "wired into research agents" claim fails for brainstorm as configured (evidence: `usability_local_test/_verify_brainstorm_probe.md`).

---

## [PLAN-2026-28c] README coverage list + bug fixes (BUG-001/002/003) | 2026-07-08 | orchestrator

**Goal:** Execute the user's decision (verbatim: "README에 탐색 가능 커버리지 list (학술지/학회/아카이브 명칭 등) 정리해두고, 버그 픽스하자. 그리고 usability 폴더 관련 태스크는 이제 신경꺼도 된다."): (1) add a literature-search coverage section to README.md grounded strictly in `usability_local_test/_verify_mcp_coverage.md`; (2) fix BUG-001 (critical), BUG-002 (major), BUG-003 (major) plus the minor hygiene items; (3) drop all remaining usability-folder follow-up tasks (dropped-by-user, not carried).

### Subtasks

| # | Subtask | Specialist | Success criterion | Gate |
|:--|:--|:--|:--|:--|
| 1 | README coverage section: 4 backends named + verified figures, effective de-duplicated reach, content depth per path, S2_API_KEY caveat — no new numbers | writer | Section present in README.md; every figure matches `_verify_mcp_coverage.md` | — |
| 2 | Fix BUG-001 + BUG-002 in `.claude/hooks/experiment_gate.py` (env-prefix bypass; regex anchoring) | developer | `tests/repro/test_bug_001.py` + `test_bug_002.py` green; legit blocking and valid-ADR override behavior preserved (developer re-runs qa's original test matrix) | qa re-verify (subtask 5) |
| 3 | Fix BUG-003 per ADR-001: add scoped `mcp__*` tool names to brainstorm/critic/writer frontmatter (no Bash) + hygiene items (`.pytest_cache/` gitignore, `pytest-timeout` in requirement.txt, CLAUDE.md agent-memory comment) | filemanager | Frontmatter lists match ADR-001 exactly; hygiene items applied; .gitignore edit is a minimal append (user has file open in IDE) | live re-probe (subtask 4) |
| 4 | Live re-probe: brainstorm agent calls `mcp__literature__lit_search` + `mcp__zotero__zotero_search` for real | brainstorm | Both calls return real results (or honest failure reported verbatim) | — |
| 5 | qa re-verifies all three BUGs with recorded repro steps; appends status lines to error.md (no edits of prior text) | qa | BUG-001/002/003 status lines appended with evidence; tests green | — |
| 6 | Commit fixes + update handoff.json (usability follow-ups marked dropped-by-user) | filemanager | Commit references doc IDs, no emojis, no attribution footer; handoff.json parses with 5 keys | — |

**Sequence:** 1–3 parallel (disjoint files: README.md / experiment_gate.py+tests / agents+gitignore+requirement.txt+CLAUDE.md) → 4 (needs 3) → 5 (needs 2+4) → 6 (needs 5) + STATE entry.
**Blocking:** none — no experiments run; critic gate not triggered (code fix + doc prose from verified numbers, no new research claims). qa re-verification is the code gate for the hook fix.
**Dropped by user (not carried):** optional critic re-gate on `REVIEW_manuscript_example.md`; Zeng 2026 / Newlin 1985 citation-status checks; any further edits to `usability_local_test/` deliverables.

**Status update (2026-07-08, subtask 1 complete):** Writer added "Literature search coverage" block to README.md (lines 128–154, inside "What you can do" after the Zotero paragraph): 4-backend table with verified scales, effective-reach framing (~300M+ unique works / ~290,000+ venues, double-counting caveat, venue-names-not-enumerable note), content-depth paragraph (abstract+metadata via lit_search/lit_fetch; PubMed no-abstract caveat; full text via zotero_fulltext or manual PDF), S2_API_KEY/HTTP 429 caveat, 2026-07-08 live-verification pointer. All figures byte-checked against `_verify_mcp_coverage.md`; greps for 319,077,593 and zotero_fulltext hit; no other README content touched.

**Status update (2026-07-08, subtask 2 complete):** Developer fixed `experiment_gate.py` in place: replaced the `\b`-anchored `EXP_LAUNCH` regex with command-segment-position detection (`_segment_starts()` + `re.match` at segment offsets; `_ENV_CHAIN` prefix handles `NAME=value` chains; `GATE_OVERRIDE` detection scoped to the matched launch's own env-chain). Evidence: `pytest tests/repro/test_bug_001.py test_bug_002.py` 5/5 green; full 11-case matrix correct via simulated hook stdin — incl. `GATE_OVERRIDE=ADR-999 ./run.sh test` → exit 2 with "ADR-999" in stderr (BUG-001 fixed), `GATE_OVERRIDE=ADR-001 ./run.sh test` → exit 0 (valid override preserved), `FOO=bar ./run.sh test` → exit 2, `echo "python models/train.py"` → exit 0 and `wc -l setup.sh evaluate.sh` → exit 0 (BUG-002 + `\bsh` symptom fixed); `pytest tests/` 10/10 (new `tests/repro/test_bug_001_002_fix.py` adds the positive-override and `.sh`-tail cases). Developer independently re-flagged the user-side `.gitignore:50` `tests` line (new test file is untracked-and-ignored).

**Status update (2026-07-08, subtasks 3–4 complete):** Filemanager applied ADR-001 exactly: brainstorm +8 `mcp__*` tools, critic +7, writer +7 (`zotero_add` confined to brainstorm — frontmatter-scoped grep verified; no Bash granted); hygiene: `.pytest_cache/` gitignored (`git check-ignore` passes), `pytest-timeout==2.4.0` added to previously-empty requirement.txt, CLAUDE.md agent-memory comment now names orchestrator-opus. Live re-probe (fresh brainstorm session) confirms BUG-003 failure mode resolved: all 8 MCP tools enumerated; `lit_search("electrodermal activity craving detection")` → real 15-row result table (arXiv/OpenAlex/PubMed; one informational S2 429); `zotero_search("craving")` → 5 real items incl. [YUCAN6SP], [R7HAWDG4]; `zotero_add` present, not called. Evidence: scratchpad `reprobe_brainstorm.md` (to be quoted in qa's BUG-003 status line). NOTE for close-out: pre-existing uncommitted user-side `.gitignore` lines `usability_local_test` and `tests` — the `tests` line will exclude qa's new regression tests from commits; flag to user, do not override.

---

## [ADR-001] BUG-003 remedy: scoped MCP tool grants, no Bash, for research agents | 2026-07-08 | orchestrator

**Context:** BUG-003 (error.md): brainstorm/critic/writer cannot reach the literature/Zotero integration — frontmatter grants neither `Bash` nor any `mcp__*` tool. User authorized the fix without picking a remedy. Options: (a) grant `Bash` (unlocks CLI path but gives non-executing agents arbitrary shell), (b) grant all eight `mcp__*` tools to all three, (c) scoped per-agent MCP grants, no Bash.
**Decision:** Option (c), least privilege. `brainstorm` (library curator, owns papers/): all eight — `mcp__literature__lit_search`, `mcp__literature__lit_fetch`, `mcp__zotero__zotero_search`, `mcp__zotero__zotero_item`, `mcp__zotero__zotero_fulltext`, `mcp__zotero__zotero_collections`, `mcp__zotero__zotero_add`, `mcp__zotero__zotero_bibtex`. `critic` and `writer`: the same minus `mcp__zotero__zotero_add` — reviewers and prose writers read the user's Zotero library but must not write to it. No `Bash` for any of the three: critic and writer are deliberately non-executing agents, and the MCP path makes the CLI fallback unnecessary.
**Consequences:** Documented integration becomes reachable (validated by live re-probe, PLAN-2026-28c subtask 4); Zotero library writes remain confined to brainstorm; if the re-probe fails, remedy escalates (revisit this ADR) rather than silently granting Bash.
**Linked:** BUG-003, PLAN-2026-28c, `usability_local_test/_verify_mcp.md`, `usability_local_test/_verify_brainstorm_probe.md`.

---

## [PLAN-2026-28d] Re-land bfc4e00 as per-concern branches/PRs | 2026-07-08 | orchestrator

**Goal:** Per user decision (verbatim: "test 폴더는 ignore다. 관심사 별로 PR description, branch 개설 등 계획 보고하라."), plan — planning only, no git mutations until approval — the split of unpushed commit `bfc4e00` (19 files; local main = origin/main `052ab17` + this one commit) into per-concern topic branches, each PR'ing into main. The `tests` gitignore decision is final: regression tests stay local-only.

### Proposed split (file lists disjoint across branches — no cross-branch conflicts)

| # | Branch | Concern | Files (carved from bfc4e00) | Merge order |
|:--|:--|:--|:--|:--|
| 1 | `fix/experiment-gate-regex` | Gate bypass + false positives (BUG-001, BUG-002) | `.claude/hooks/experiment_gate.py` | any, before #5 |
| 2 | `feat/research-agent-mcp-access` | MCP wiring (BUG-003, ADR-001) | `.claude/agents/brainstorm.md`, `critic.md`, `writer.md` | any, before #5 |
| 3 | `docs/readme-literature-coverage` | README coverage list (PLAN-2026-28c) | `README.md` | any, before #5 (no hard dep on #2 — the section documents server coverage, not agent grants) |
| 4 | `chore/repo-hygiene` | Ignore rules, deps, layout notes | `.gitignore` (+`.pytest_cache/`, +`usability_local_test`, +`tests` — user-ratified), `requirement.txt` (`pytest-timeout==2.4.0`), `CLAUDE.md` (agent-memory comment; plus NEW one-line note that `tests/` is local-only in this deployment — beyond bfc4e00, recommended) | any, before #5 |
| 5 | `docs/research-log-2026-07-08` | Root docs + session state + agent memory | `error.md`, `discussion.md`, `.claude/state/handoff.json`, 8 agent-memory files (critic: MEMORY.md, pdf_multipage_render_bug.md; orchestrator: MEMORY.md, harness-tool-fallbacks.md, usability-verification-preferences.md; orchestrator-opus: MEMORY.md, mcp_lit_tools_availability.md, pdf_input_preflight.md) | LAST |

**Root-doc placement decision:** one consolidated docs/state PR (#5), not distributed to causal PRs. Rationale: error.md/discussion.md are append-only multi-writer logs whose entries interleave all three concerns inside shared tables (one BUG tracker, one plan tracker) — splitting per-PR guarantees same-hunk merge conflicts between topic branches; handoff.json is one indivisible snapshot; the four-doc system's unit of coherence is the session, not the code concern. Cost: PRs 1–3 cite doc IDs that land with #5 — mitigated by merging #5 last so main's logs always describe merged reality.

**Verification wording (binds PRs 1–2):** tests/repro is local-only by user decision, so fix PR descriptions state verification via recorded exit codes and qa evidence in error.md BUG resolutions (11-case simulated-stdin matrix for #1; frontmatter grep + live brainstorm re-probe for #2), not in-repo CI tests.

**Execution mechanics (on approval):** (1) cut 5 branches at `052ab17`; (2) populate each via `git checkout bfc4e00 -- <files>` per the table (branch #5 takes the CURRENT working-tree doc state, a superset of bfc4e00 that includes this entry); (3) stash uncommitted doc edits before `git reset --hard origin/main` on local main and pop onto branch #5 — the reset must not destroy post-bfc4e00 doc appends; (4) push branches, open PRs 1–4 (parallel) then 5; (5) nothing force-pushed — origin/main was never ahead.

**Status:** awaiting user approval. No branch, reset, or push executed.

**Status update (2026-07-08):** APPROVED by user (verbatim: "detailed description과 함께 Branch 별 PR 날리자. ISSUE도 만들어야 하는 거 있으면 만들자.") and EXECUTED. Branches: fix/experiment-gate-regex a0a9d9b, feat/research-agent-mcp-access f17a6c7, docs/readme-literature-coverage 9272907, chore/repo-hygiene c566c82, docs/research-log-2026-07-08 dc928e8 (+ this commit). Local main reset to 052ab17; five branches pushed, no force; 19/19 bfc4e00 files reconciled, stashed doc edits preserved. PRs: PR1 https://github.com/DrNeuroAI/ai-research-orchestration/pull/4 (fix/experiment-gate-regex), PR2 https://github.com/DrNeuroAI/ai-research-orchestration/pull/5 (feat/research-agent-mcp-access), PR3 https://github.com/DrNeuroAI/ai-research-orchestration/pull/6 (docs/readme-literature-coverage), PR4 https://github.com/DrNeuroAI/ai-research-orchestration/pull/7 (chore/repo-hygiene), PR5 https://github.com/DrNeuroAI/ai-research-orchestration/pull/8 (docs/research-log-2026-07-08, "merge PR5 LAST"). Issues: A (MCP re-probe) https://github.com/DrNeuroAI/ai-research-orchestration/issues/1, B (S2_API_KEY) https://github.com/DrNeuroAI/ai-research-orchestration/issues/2, C (pytest-timeout install) https://github.com/DrNeuroAI/ai-research-orchestration/issues/3. Retroactive issues for resolved BUG-001/002/003 deliberately not created — error.md and the PR descriptions carry that record; closed-on-arrival issues would be noise.

---

## [STATE-2026-07-08 · fixes complete, all BUGs resolved] | orchestrator

**Task:** PLAN-2026-28c — user-authorized follow-up to PLAN-2026-28b: README coverage list, fixes for BUG-001/002/003, hygiene items; usability-folder follow-ups dropped by user.

**Outcome:** Complete. README.md gained a "Literature search coverage" block (4-backend table, effective reach ~300M+ unique works / ~290,000+ venues, content-depth per path, S2 rate-limit caveat — all figures byte-matched to `_verify_mcp_coverage.md`). `experiment_gate.py` rewritten to command-segment-position matching: env-prefix bypass (BUG-001) and mention/filename false positives (BUG-002) both fixed; valid `GATE_OVERRIDE=ADR-001` still allowed, `ADR-999` rejected; `tests/repro/` 10/10 green. ADR-001 MCP grants applied (brainstorm 8 / critic 7 / writer 7 tools, `zotero_add` brainstorm-only, no Bash); live brainstorm re-probe returned real lit_search (15 rows) and zotero_search (5 items) results. qa independently re-verified all three fixes with recorded exit codes and appended resolution status lines; error.md tracker shows BUG-001/002/003 **resolved**. Hygiene: `.pytest_cache/` gitignored, `pytest-timeout==2.4.0` in requirement.txt, CLAUDE.md agent-memory comment updated.

**Open bugs:** none (all resolved).
**Pending reviews:** none.
**Residuals for user awareness:** (1) user-side `.gitignore` lines `usability_local_test` and `tests` — the `tests` line keeps `tests/repro/*.py` regression tests out of git (contradicts CLAUDE.md's tracked-tests layout; left untouched pending user confirmation); (2) critic/writer MCP grants verified statically only (mechanism proven live via brainstorm; noted in BUG-003 resolution); (3) `pytest-timeout` listed in requirement.txt but not pip-installed in this environment; (4) no `S2_API_KEY` — Semantic Scholar rate-limits on `all`-source searches.
**Dropped by user (not carried):** critic re-gate on `REVIEW_manuscript_example.md`; Zeng 2026 / Newlin 1985 citation checks; further `usability_local_test/` work.

---

## [STATE-2026-07-08 · usability re-verification complete] | orchestrator

**Task:** PLAN-2026-28b — usability re-verification of the orchestration system, headlined by the paper-research MCP functional check (Fable 5 orchestrator run; prior run was orchestrator-opus).

**Outcome:** Complete. Headline: both MCP servers (literature + zotero) are properly implemented and fully functional — verified statically, via direct stdio JSON-RPC handshake, via live MCP calls (real results from public APIs and the user's actual Zotero library), and via CLI. However, the "wired into research agents" claim (commit 92be108) is documentary only: `brainstorm`/`critic`/`writer` frontmatter grants neither `Bash` nor any `mcp__*` tool → **BUG-003 (major, open)**. Coverage (user scope addition): 4 direct backends, effective de-duplicated reach ~300M+ unique works across ~290,000+ venues; read-and-reason works at abstract+metadata depth (proven on post-cutoff arXiv:2605.26355); full text only via `zotero_fulltext` (58.8 KB retrieved live). Hooks: 7/8 PASS but **BUG-001 (critical, open)** — `GATE_OVERRIDE=`/any env-prefix silently bypasses the experiment gate — and **BUG-002 (major, open)** — unanchored regexes cause false positives. Structure: 10/10 checks pass bar minor doc staleness.

**Deliverable:** `usability_local_test/USABILITY_multiagent_system.md` (v2 report; prior run preserved as appendix). Evidence base: `usability_local_test/_verify_mcp.md`, `_verify_mcp_coverage.md`, `_verify_brainstorm_probe.md`, `_verify_hooks.md`, `_verify_structure.md`, `_gate_critic_v2.md`. Critic-before-report gate: PASS-WITH-FIXES, both fixes applied and orchestrator-verified.

**Open bugs:** BUG-001 (critical — fix `experiment_gate.py` regex anchoring before any real experiment; red regression tests at `tests/repro/`), BUG-002 (major), BUG-003 (major — decide whether to grant `mcp__*` tools and/or `Bash` to brainstorm/critic/writer, then re-probe).
**Pending reviews:** none — no blocking REV/VAL open.
**Next:** user decision on fix authorization for BUG-001/002/003; minor hygiene items (CLAUDE.md agent-memory comment, `.pytest_cache/` gitignore, `pytest-timeout` in requirement.txt, `S2_API_KEY` for rate-limit-free `all`-source searches).

---

## [STATE-2026-07-08 · PLAN-2026-28d executed: 5 PRs open] | orchestrator

**Task:** PLAN-2026-28d — user-approved split of unpushed commit `bfc4e00` into 5 per-concern branches/PRs, plus follow-up issues for residual open items.

**Repo state:** local `main` reset to `origin/main` `052ab17`; the work is re-landed as five one-commit branches, all pushed to origin, nothing merged into `main`.

**Pull requests (base `main`, all open):**

| PR | Branch | Commit | Description |
|:--|:--|:--|:--|
| [#4](https://github.com/DrNeuroAI/ai-research-orchestration/pull/4) | `fix/experiment-gate-regex` | a0a9d9b | Fix experiment gate env-prefix bypass and mention false positives (BUG-001, BUG-002) |
| [#5](https://github.com/DrNeuroAI/ai-research-orchestration/pull/5) | `feat/research-agent-mcp-access` | f17a6c7 | Grant scoped MCP literature/Zotero access to research agents (BUG-003, ADR-001) |
| [#6](https://github.com/DrNeuroAI/ai-research-orchestration/pull/6) | `docs/readme-literature-coverage` | 9272907 | Add literature search coverage section to README (PLAN-2026-28c) |
| [#7](https://github.com/DrNeuroAI/ai-research-orchestration/pull/7) | `chore/repo-hygiene` | c566c82 | Repo hygiene: ignore rules, test dependency, layout notes (PLAN-2026-28c) |
| [#8](https://github.com/DrNeuroAI/ai-research-orchestration/pull/8) | `docs/research-log-2026-07-08` | dc928e8 + this commit | Record 2026-07-08 verification and fix cycle in project docs |

**Follow-up issues:**

| Issue | Tag | Description |
|:--|:--|:--|
| [#1](https://github.com/DrNeuroAI/ai-research-orchestration/issues/1) | MCP re-probe | Live re-probe critic and writer MCP tool access (ADR-001 residual) |
| [#2](https://github.com/DrNeuroAI/ai-research-orchestration/issues/2) | S2_API_KEY | Configure S2_API_KEY to avoid Semantic Scholar rate limiting on all-source searches |
| [#3](https://github.com/DrNeuroAI/ai-research-orchestration/issues/3) | pytest-timeout | Install pytest-timeout in the environment (pinned in requirement.txt but missing) |

**Merge order:** PRs #4–#7 may merge in any order; PR #8 (`docs/research-log-2026-07-08`) merges LAST so main's logs describe merged reality.

**Next actions:** user merges the PRs; issue #1 is the only agent-actionable follow-up (issues #2 and #3 are environment/credential actions for the user). Retroactive issues for resolved BUG-001/002/003 were deliberately not filed — error.md and the PR descriptions carry that record.

---

<!-- Entries are append-only. Formats:

## [HYP-NNN] short title | YYYY-MM-DD | brainstorm
Claim: <single falsifiable sentence>
Prediction: <what should be observed if true>
Falsifier: <what observation would refute it>
Required data: ...
Required baselines: ...
Required metrics: ...
Linked papers: ...
---

## [RES-NNN] short title | YYYY-MM-DD | brainstorm
Source: <full citation + URL>
Summary: ...
Relevance: ...
---

## [DATASET-NNN] dataset name | YYYY-MM-DD | data
Source: <URL + license>
Cohort: <inclusion/exclusion criteria>
Size: total=N, train=N, val=N, test=N
Split policy: ...
Known leakage risks: ...
Hash: <SHA256 of split files>
Linked: HYP-...
---

## [REV-NNN] short title | YYYY-MM-DD | critic
Target: <HYP-..., EXP-..., or file path>
Severity: blocking | major | minor
Issues:
  1. ...
Status: open
---

## [ADR-NNN] short title | YYYY-MM-DD | orchestrator
Context: ...
Decision: ...
Consequences: ...
Linked: ...
---

## [PLAN-YYYY-WW] plan title | YYYY-MM-DD | orchestrator
Goal: ...
Sequence: ...
Blocking: ...
---

## [STATE-YYYY-MM-DD] | orchestrator
Active hypotheses: ...
Open bugs: ...
Pending reviews: ...
---

## [REPORT-YYYY-WW] week summary | writer
Done: ...
In progress: ...
Blocked: ...
Next: ...
---
-->
