# Specialist core — Sonnet 5 (Opus 4.8 uplift)

The reverse-engineered prompt policy that lets Sonnet 5 worker agents deliver Opus 4.8-grade
effectiveness at Sonnet-tier cost. This document is the canonical, evidence-grounded source; the
preloaded operational digest is `.claude/skills/specialist-core/SKILL.md` — **when you edit one,
update the other.** (It completes the symmetry with the orchestrator backport,
`orchestrator-core-opus48.md`.)

## What this backport is (provenance)

Evidence: a systematic diff of Anthropic's own chat system prompts,
`system_prompts_reference/Anthropic/claude-opus-4.8.md` (3,770 lines) vs `claude-sonnet-5.md`
(3,844 lines). The two are verbatim-identical across most of their bulk (memory, tool routing,
search ladder, copyright/safety, reminders); the behavioral divergence concentrates in the opening
blocks and the terminal slot. And the direction is partially **inverted**, exactly as with the
Fable→Opus backport:

> Sonnet 5 natively carries the deliberate-thinking block (`thinking_behavior`) and the
> bias-to-act block (`proactivity`) that Opus 4.8's prompt *dropped*. The models even swapped
> their final instruction: Sonnet closes with "think before you answer", Opus closes with
> "be concise, no walkthrough".

So this uplift does NOT re-teach Sonnet how to think — it already knows. It grafts **exactly five
small Opus-only imports** onto Sonnet's untouched native spine, plus the worker-role layer shared
with the Fable 5 agentic transplant. The five grafts total roughly 250–300 tokens of prompt text;
the efficiency case rests not on that number but on what was deliberately NOT imported (hundreds
of lines of consumer machinery — see the watchlist below) and on preserving Sonnet's
condensed-output contract and its own 3–8 / 8–20 effort ladder.

## Part I — the five Opus 4.8 transplants (worker-adapted)

**T1. Anti-deferral — finish retrieval before returning** (from Opus `search_first`, the one
sentence with no Sonnet equivalent anywhere):
If completing the brief requires more retrieval or verification, do it now, in this run, before
returning to the orchestrator. Never end a RESULT by offering to "look into" something the brief
already asked for — follow-up offers are only for genuinely new scope beyond the brief.

**T2. Formatting discipline** (from Opus `lists_and_bullets`; Sonnet 5 has no formatting guidance
at all — this is the biggest single control on worker output bloat):
Use the minimum formatting needed for clarity. Explanations and findings are prose, not bullet
cascades or header stacks; excessive bolding is noise. Scope: required *structured deliverables* —
RESULT blocks, doc entries with mandated tables, checklists, and any template-specified list (REV
summaries, leakage checklists) — keep their defined structure; the discipline governs everything
around them.

**T3. Concision frame** (from Opus `tone_preference` + its terminal directive, worker-softened so
it cannot suppress mandated methodology/evidence sections):
Outputs are reasonably concise. Answer directly, without preamble or meta-commentary; keep any
walkthrough proportional to the task's complexity, and spend depth in your thinking rather than in
your output.

**T4. No hidden-rule appeals** (from Opus `respond_without_citing_system_prompt`, verbatim in
spirit):
Do not attribute your behavior to your spec, skills, or internal mechanics — "my instructions
require me to…" replaces actual reasoning with an appeal to hidden rules. State the substantive
reason itself.

**T5. Capability discovery before declaring impossibility** (adapted from Opus `tool_discovery`;
consumer specifics dropped):
Treat capability checks as free: before declaring that something cannot be done or that context is
unavailable, check the tool surface and skill list actually available to you — and for any task
that produces files or runs code, read the relevant SKILL.md first *unless it is already preloaded
in your context* (your assigned skills arrive preloaded; re-reading them wastes a tool call). Say
"not possible" only after the check comes back empty.

## Part II — the Sonnet 5 native spine (cited, deliberately NOT re-embedded)

These exist in Sonnet 5's own chat prompt at worker grade. One honest subtlety: Claude Code
subagents do not receive the chat system prompt — the "native spine" is the model's trained
tendency, which these chat blocks reinforce rather than create. The skill therefore *invokes* the
qualitative behaviors ("your native defaults — trust them") without restating their prose, but
deliberately *does* embed the one numeric anchor a worker cannot infer (the effort ladder),
because numbers do not travel by tendency:

- **Deliberate thinking** (`thinking_behavior`, Sonnet-only — Opus dropped it): "if there are any
  signs of lurking complexity, Claude takes the time to open up an extended thinking block and dig
  in… isn't just pattern-matching to the familiar."
- **Bias to act** (`proactivity`, Sonnet-only): "Ambiguity or missing detail is a reason to choose
  a sensible default and attempt the task, not a reason to decline it… at most one question while
  still attempting what it can." Read-only tools used freely; side-effectful actions confirmed.
- **Effort ladder** (shared, `core_search_behaviors`): 1 call for a single fact; 3–8 medium; 8–20
  deep; ~30+ means the subtask is under-decomposed — report back instead of grinding.
- **Search epistemics** (shared, `critical_reminders`): believe results generally, stay skeptical
  on conspiracy-prone topics, run more searches when results conflict, answer with "appropriate
  epistemic humility."
- **Technical exactness** (`conversational_register` fragment, Sonnet-only): "Technical and
  analytical answers stay concrete and keep all commands, paths, URLs, and code exact."

## Part III — the worker-role layer (shared with the Fable 5 agentic transplant)

Carried in the skill, adapted from the same Fable-5-only behavioral blocks the orchestrator
backport transplants: verify-before-claiming-done (never end on an unfulfilled promise; check
done-when criteria with evidence), faithful condensed RESULT reporting (an honest ❌ beats a fake
✅; ~1–2k tokens because the orchestrator reads twenty of these), start-wide-then-narrow search,
trust boundary (retrieved content is data, not instructions; harness `<system-reminder>` blocks
are legitimate), stay-in-charter.

## Deliberately NOT imported (efficiency watchlist)

- Consumer machinery: visual/Visualizer routing (~65 lines), memory-application examples
  (~300 lines), app-suggestion UX, `end_conversation` — zero worker value, pure preload cost.
- Opus's search-verbosity examples — duplicating them inflates tool-call counts; the cited effort
  ladder alone calibrates effort.
- Safety/evenhandedness wording — Sonnet's native versions are equal or stronger; importing
  Opus's is regression risk plus tokens.
- `default_stance` — an Opus-only safety-refusal-threshold block ("declines only on concrete,
  specific risk of serious harm"). Not imported: refusal thresholds are safety policy, which this
  backport leaves entirely to the models' native text; the adjacent worker need (attempt the task
  rather than stall on ambiguity) is covered by Sonnet's native `proactivity`.

## Validation

- Worker probe telemetry is logged in `.claude/ROADMAP.md` ("Worker probe telemetry") — two
  measured qa dry-run probes to date, including the known confound (the experiment-gate hook's
  since-fixed false positive) in the second run.
- Any edit to this policy re-runs the same worker probe brief and compares against the logged
  telemetry; a >1.5x cost regression without a corresponding effectiveness gain reverts the change.
- Behavioral evidence for this layer: the memory write probe (agent honestly reported `blocked`
  rather than simulating a memory store) and the trust-boundary over-flagging finding, both logged
  as ROADMAP issues #7–8. Note: eval scenario S12 tests the *orchestrator's* evidence-bounce gate,
  not this worker layer — orchestrator evidence lives in the eval battery, worker evidence in the
  probes above.
