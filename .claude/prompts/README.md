# Orchestration prompt cores

System-prompt source documents for the multiagent orchestration system. Agent specs in
`.claude/agents/` reference these files as mandatory reads; the `multiagent-orchestration` skill
carries the shared playbook.

## Architecture

```
User
 │
 ▼
Conductor (main session, Fable 5)          — classifies the request, invokes the orchestrator
 │
 ▼
orchestrator (model: fable)                — plans, routes, gates, synthesizes, reports
 │    fallback: orchestrator-opus (model: opus, Fable 5 backport prompt)
 │
 ├─► brainstorm (sonnet)   ─┐
 ├─► data (sonnet)          │  specialists work in isolated contexts,
 ├─► critic (sonnet)        │  briefed via BRIEF, replying via RESULT;
 ├─► developer (sonnet)     │  they never call each other — all
 ├─► qa (sonnet)            │  coordination passes through the lead
 ├─► experiment-tracker (sonnet)
 ├─► filemanager (sonnet)   │
 └─► writer (sonnet)       ─┘
```

Design sources, in order of authority (the reference collections below are third-party material
and are **not redistributed** with this repository — the paths exist only on the original
development machine; the derived policy is fully contained in the files here):
1. **The official Claude Code model diff** — `system_prompts_reference/Anthropic/Claude Code/`
   `claude-code-2.1.172-fable-5.md` vs `claude-code-2.1.172-opus-4.8.md`: same harness, same
   version, byte-identical tool schemas; the entire diff is ~53 preamble lines of behavioral text.
2. Anthropic production orchestration prompts — `system_prompts_reference/Anthropic/`
   `research_instructions.md` (Research lead), `claude-cowork-dispatch.md` (Cowork Dispatch),
   `claude-cowork.md` (worker verification loop).
3. The Fable 5 / Opus 4.8 / Sonnet 5 chat prompts (both reference collections).
4. Anthropic's published orchestrator-worker research system; vendor agentic prompts (Devin, Manus,
   Factory, Cline, OpenAI Codex/Agents SDK); Cognition's parallel-reads/serial-writes principle.

## Files

| File | Role |
|---|---|
| `orchestrator-core-fable5.md` | Orchestration core for the Fable 5 orchestrator. Terse, high-trust judgment statements — the Fable 5 prompting style. |
| `orchestrator-core-opus48.md` | The Fable 5 **backport** for Opus 4.8: Part I transplants the Fable-only behavioral layer (communication, autonomy, deliberate reflection) near-verbatim; Part II adds the lab's explicit gate sequence (Gate 0–8) as reliability scaffolding. |
| `result-contract.md` | The BRIEF / RESULT / HANDOFF schemas — the only channel between orchestrator and specialists. Authoritative for those schemas. |
| `specialist-core-sonnet5.md` | The Opus 4.8 → **Sonnet 5 backport** for workers: five small Opus-only transplants grafted onto Sonnet's untouched native spine (which already carries the thinking/proactivity blocks Opus dropped). Canonical source for the `specialist-core` skill. |
| `orchestration-evals.md` | 14 eval scenarios + judging rubric for comparing the two orchestrator variants. |

The worker backport preloads into every specialist as the `specialist-core` skill
(`.claude/skills/specialist-core/SKILL.md` — the operational digest of
`specialist-core-sonnet5.md`; edit them together). The conductor protocol for a main session
running on Opus 4.8 is in CLAUDE.md ("Conductor protocol").

## The backport principle (v2, corrected)

The authoritative evidence inverted the v1 assumption. In Anthropic's own Claude Code prompts, the
rich behavioral layer ("Communicating with the user"; the autonomy/turn-completion block) ships
**only in the Fable 5 version** — Opus 4.8's stock prompt omits it, and 4.8 also dropped the
deliberate-thinking guidance that Opus 4.7 carried, in favor of "be concise, no walkthrough"
tuning. So the backport is a **transplant**, not compensation: Part I of the Opus core carries the
Fable behavioral text near-verbatim (adapted to fan-out: the closing report carries everything,
because the user never sees worker output), and explicitly re-enables deliberate reflection after
each specialist RESULT — the one place 4.8's conciseness tuning actively hurts orchestration. The
lab gate sequence remains as process scaffolding: orchestration failures are dominantly process
failures, and gates make the process checkable. The two core files encode identical policy;
**when you edit one, update the other.** Identity is never backported: the Opus core explicitly
forbids claiming to be Fable 5 or Mythos-class.

## Maintenance rules

1. Policy changes go into BOTH core files (terse form in fable5, gated form in opus48).
2. Schema changes go into `result-contract.md` only; the cores and agent specs reference it.
3. Shared playbook changes (fleet sizing, failure ladders, anti-patterns) go into
   `.claude/skills/multiagent-orchestration/SKILL.md`.
4. New specialists: add the spec under `.claude/agents/` with `model: sonnet`, the version
   management block, and the Result contract section; add rows to CLAUDE.md's agent and skills
   tables.
