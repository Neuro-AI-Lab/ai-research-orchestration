# AI Research Orchestration System

**English** | [한국어](README.ko.md)

A production-grade multiagent orchestration system for AI/ML research, built on [Claude Code](https://code.claude.com).
A frontier-model **orchestrator** (Claude Fable 5, with a validated Opus 4.8 backport) conducts a
fleet of **Sonnet 5 specialist agents** through the full research lifecycle — hypothesis → adversarial
review → data → code → verification → experiments → paper — with mechanically enforced quality
gates, reproducibility discipline, cross-session memory, and Overleaf collaboration.

Every load-bearing behavior in this system was validated by a measured evaluation battery
(11/11 scenarios passed; see `.claude/prompts/orchestration-evals.md` and `.claude/ROADMAP.md`).

## Why this exists

Multiagent research systems fail in predictable ways: vague delegation, skipped quality gates,
fabricated results, leaked test data, forgotten long-running jobs, and knowledge that dies with
each session. This system engineers each failure mode away:

| Failure mode | Countermeasure (all implemented and tested) |
|---|---|
| Vague delegation | BRIEF/RESULT/HANDOFF contracts on every dispatch (`.claude/prompts/result-contract.md`) |
| Skipped gates under deadline pressure | Prompt-level gates + a `PreToolUse` hook that mechanically blocks experiment launches while a critical bug / blocking review / undocumented dataset exists |
| Fabricated numbers or citations | Evidence-gated completion (✅/⚠️/❌ lines), "a result you did not receive does not exist", literature verification tooling |
| Data leakage | Six agents share leakage responsibility; split-integrity checklist gates every dataset |
| Lost long runs | Status-wrapper protocol (`status.json` heartbeat, orphan adoption at session start) |
| Amnesia between sessions | Dual-layer continuity: human-readable markdown docs + machine-readable `handoff.json` + per-role agent memory, injected automatically at session start |

## Architecture

```
User
 │
 ▼
Conductor (main Claude session)            classifies requests, dispatches
 │
 ▼
orchestrator (model: fable)                plans, routes, enforces gates, synthesizes
 │   fallback: orchestrator-opus (model: opus, Fable-5-backport prompt)
 │
 ├─► brainstorm (sonnet)          hypotheses, literature      ─┐
 ├─► critic (sonnet)              adversarial validity review  │  isolated contexts,
 ├─► data (sonnet)                datasets, splits, EDA        │  briefed via BRIEF,
 ├─► developer (sonnet)           model/eval code              │  replying via RESULT;
 ├─► qa (sonnet)                  tests, bug isolation, gates  │  never call each other
 ├─► experiment-tracker (sonnet)  runs, sweeps, result records │
 ├─► filemanager (sonnet)         repo, git, env, archives     │
 └─► writer (sonnet)              reports, README, LaTeX paper ─┘
```

The orchestrator prompts are reverse-engineered from Anthropic's own model-specific system prompts:
the Opus 4.8 variant transplants the Fable-5-only behavioral layer (communication, autonomy,
deliberate reflection) and adds an explicit Gate 0–8 process. Sonnet specialists carry a
`specialist-core` skill that uplifts worker reasoning to frontier discipline at worker-tier cost.
Details and provenance: `.claude/prompts/README.md`.

## Requirements

- [Claude Code](https://code.claude.com) CLI (agents, skills, hooks, and MCP are used heavily)
- Python 3.8+ (all tooling is stdlib-only — no pip installs required)
- git; internet access for literature APIs
- Optional: an Overleaf account with git integration (premium) for paper collaboration
- Optional: a [Semantic Scholar API key](https://www.semanticscholar.org/product/api) for higher literature-search rate limits

## Quick start

```bash
git clone <this-repo> my-research && cd my-research
cp .claude/settings.local.json.example .claude/settings.local.json   # fill in what you want (all optional)
claude                                                               # start Claude Code
```

The **core research pipeline needs no credentials** — it works out of the box. Secrets only unlock
optional integrations (Zotero, Overleaf, higher literature rate limits); add them incrementally.
**Full walkthrough and the masked-credentials guide: [SETUP.md](SETUP.md).**

On the first session the system introduces itself: a `SessionStart` hook injects a continuity
brief (open gates, running experiments, last hand-off), and the literature + Zotero MCP servers
load. Then just describe your research goal in plain language:

```
"Design and run an experiment testing whether back-translation augmentation
 improves minority-class F1 on my dataset."
```

The orchestrator takes over: bootstrap audit → hypothesis (brainstorm) → adversarial review
(critic) → dataset card with leakage checklist (data) → implementation (developer) → verification
(qa) → gated experiment run (experiment-tracker) → result review (critic) → report (writer).
Trivial lookups ("What does HYP-003 say?") are answered directly without agent overhead.

### User-specific values (fill in yourself; all optional, all masked/gitignored)

Full instructions in [SETUP.md](SETUP.md). Summary:

| Value | Unlocks | Where to get it |
|---|---|---|
| `ZOTERO_API_KEY` + `ZOTERO_USER_ID` (or `ZOTERO_GROUP_ID`; or `ZOTERO_LOCAL=1` for a local Zotero desktop app, no key needed) | Zotero library search, PDF reading, save-back, BibTeX | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) — see `.claude/ZOTERO.md` |
| `OVERLEAF_GIT_TOKEN` | Overleaf paper sync | Overleaf → Account Settings → Git Integration — see `.claude/OVERLEAF.md` |
| `S2_API_KEY` | higher Semantic Scholar rate limits | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) |
| `LIT_CONTACT_EMAIL` | faster OpenAlex "polite pool" | your email (no signup) |
| `GITHUB_TOKEN` | agents push the repo / open PRs | GitHub → Developer settings → fine-grained PAT |

## What you can do

**Research pipeline** — the default flow above, with three mandatory gates before any experiment:
critic has reviewed the plan, qa has verified the code, data has documented the split. Gates are
enforced twice: in the orchestrator's prompts *and* by `.claude/hooks/experiment_gate.py`, which
blocks `run.sh` / `evaluate.sh` / `python models/*.py` while a gate is unmet. Legitimate bypass:
record an ADR (rule skipped, reason, rollback plan), then prefix the command with
`GATE_OVERRIDE=ADR-NNN` — the hook verifies the ADR actually exists.

**Literature research** — structured search over arXiv, OpenAlex (journals + top-tier conferences,
citation counts, open-access PDF links), PubMed, and Semantic Scholar, as both a CLI and an MCP
server (`.mcp.json`):

```bash
python3 .claude/scripts/lit_search.py openalex "EEG emotion recognition" \
    --venue "IEEE Transactions on Affective Computing" --year 2022-2026 --limit 5
```

Your **Zotero library** is a first-class citizen (`.claude/ZOTERO.md`): agents search it before
the open web, read its stored PDFs, save load-bearing discoveries back into it (tagged by
hypothesis), and export BibTeX from it into the Overleaf paper's `.bib`. Storage convention:
Zotero = canonical bibliographic store, original PDFs in `papers/`, durable per-paper reading
notes in `papers/notes/`, current-version relevance summaries as RES entries in `discussion.md`.
(ResearchGate is deliberately excluded — it has no public API; OpenAlex/S2 cover the need.)

**Literature search coverage** — what the literature MCP (`lit_search` / `lit_fetch`, `.mcp.json`)
can actually reach, verified live against each provider's own API/about pages on 2026-07-08:

| Backend | Indexes | Verified scale |
|---|---|---|
| arXiv | preprints — physics, math, CS, quantitative biology, and more (8 subject areas) | >3,000,000 preprints |
| OpenAlex | aggregator spanning journals, conference proceedings, and repositories | 319,077,593 works across 282,505 sources |
| PubMed / MEDLINE | biomedical and life-sciences literature | 40,830,218 citations; >5,200 MEDLINE-indexed journals |
| Semantic Scholar | papers across CS, biomedicine, and beyond | >200,000,000 papers (per-venue source count not published by the provider — UNVERIFIED) |

Effective reach: on the order of **~300M+ unique works across ~290,000+ journals/venues/archives**
after de-duplication. OpenAlex and Semantic Scholar both re-index arXiv and PubMed/MEDLINE, so a
gross sum of the four rows above double-counts heavily — the ~300M/~290k figures are the honest,
de-duplicated estimate, not a sum of the table. Individual venue names aren't enumerable at that
scale, so the table above characterizes what each platform spans rather than listing venues.

Content depth: `lit_search` / `lit_fetch` return abstract + metadata for arXiv, OpenAlex, and
Semantic Scholar; the PubMed path returns metadata only (no abstract). Neither tool parses PDFs
into full text — full-text reading is available only through the separate Zotero path
(`zotero_fulltext`) for items already in the user's library, or by downloading a PDF manually into
`papers/`.

Practical caveat: without an `S2_API_KEY`, Semantic Scholar shares a public rate-limit pool and can
return `HTTP 429` on `all`-source fan-out searches (see the credentials table above to fix this).

Platform stats change over time — the figures above were live-verified on 2026-07-08; re-check
before citing them elsewhere.

**Long-running experiments** — anything over ~2 minutes launches through
`.claude/scripts/run_with_status.sh`, which maintains a `status.json` heartbeat and survives
session death; the next session automatically detects and adopts orphaned runs. Sweeps and
ablation grids run as ONE experiment with parallel sub-runs and a single fan-in comparison table
(`.claude/scripts/sweep_summary.py`).

**Paper writing on Overleaf** — link any Overleaf project once
(`.claude/scripts/overleaf_sync.sh clone <project-id> docs/paper-<name>`), then the writer agent
pulls, edits with per-number provenance comments (`% source: EXP-003`), and pushes; you watch and
compile live on Overleaf. Push safety: secrets/data blocked, concurrent web edits integrated,
token masked. Full guide: `.claude/OVERLEAF.md`.

## Monitoring your project (two layers)

**Human layer — read these markdown files:**

| File | What you see |
|---|---|
| `discussion.md` | Hypotheses (HYP), literature notes (RES), dataset cards (DATASET), reviews (REV), decisions (ADR), plans, session state (STATE) |
| `result.md` | Experiment records (EXP) with configs/metrics, narrative reports (REPORT) |
| `error.md` | Bugs (BUG) and validity issues (VAL) with severity and status |
| `version.md` | Version archive — each phase's condensed history (VER) |

Each doc has summary tables at the top for at-a-glance status. At phase boundaries the working
docs are archived into `version.md` and reset (version-gated document system).

**Agent layer — machine-readable, you rarely touch it:**
`.claude/state/handoff.json` (structured session hand-off, auto-checked by a Stop hook before any
session ends with unrecorded changes) and `.claude/agent-memory/<role>/` (cross-session lessons
per role). A SessionStart hook injects both into every new session.

## Repository structure

```
├── CLAUDE.md                  # system constitution — routing, gates, doc formats (edit per domain)
├── README.md / README.ko.md   # this file (English / Korean)
├── SETUP.md                   # first-time setup + masked-credentials guide + usage scenarios
├── LICENSE                    # MIT
├── discussion.md / result.md / error.md / version.md   # the four research docs
├── .claude/
│   ├── agents/                # 10 agent specs (2 orchestrator variants + 8 specialists)
│   ├── skills/                # 8 skills (6 research disciplines + orchestration + specialist-core)
│   ├── prompts/                # orchestrator prompt cores, delegation contracts, eval scenarios
│   ├── hooks/                  # experiment gate, session brief, session close gate
│   ├── scripts/                # lit_search, literature_mcp, zotero_mcp, overleaf_sync, run_with_status, sweep_summary
│   ├── agent-memory/            # persistent per-role memory
│   ├── state/                   # handoff.json (session continuity)
│   ├── OVERLEAF.md              # per-project Overleaf linking guide
│   ├── ZOTERO.md                # Zotero library integration guide
│   ├── ROADMAP.md               # eval evidence + phased improvement plan
│   ├── settings.json            # hooks + permission allowlist (committed)
│   └── settings.local.json      # YOUR tokens (gitignored; copy from .example)
├── .mcp.json                  # MCP servers: literature (arXiv/OpenAlex/PubMed/S2) + zotero
├── papers/                    # reference PDFs + notes/ (durable reading notes)
├── data/ · experiments/       # datasets and run artifacts (gitignored)
├── models/ · evaluation/ · analysis/ · tests/ · docs/
└── run.sh · evaluate.sh · setup.sh · requirement.txt
```

## Validating the system

The orchestrators ship with a 14-scenario evaluation battery
(`.claude/prompts/orchestration-evals.md`): fabrication baits, gate-pressure traps, conflicting
specialist results, fleet-sizing traps, prompt-injection traps, and more, each scored on a
5-criterion rubric. Re-run it after changing any prompt core — the recorded baseline is 11/11.
Roadmap, eval evidence, and known limitations: `.claude/ROADMAP.md`.

## Customization

1. **`CLAUDE.md`** — add domain rules (privacy, licensing, evaluation criteria).
2. **Agent specs** (`.claude/agents/`) — add domain-specific checklists; keep the RESULT contract
   and version-management blocks intact.
3. **Prompt cores** (`.claude/prompts/`) — policy changes go into BOTH orchestrator cores (terse
   Fable form + gated Opus form) and require re-running the eval battery.
4. **Pipelines** — implement `setup.sh`, `run.sh`, `evaluate.sh`, `models/`, `evaluation/` for
   your domain; training loops >30 min must checkpoint and accept `--resume-from`.

## Security and distribution notes

- Real tokens live only in `.claude/settings.local.json` (gitignored). The committed
  `.example` file contains placeholders.
- `data/`, `experiments/`, and `docs/paper*/` (Overleaf clones with embedded tokens) are
  gitignored; the filemanager agent audits every commit for staged data/secrets.
- The experiment gate hook is conservative by design: a command merely *quoting* `run.sh` can be
  blocked while gates are unmet. That is a feature.

## License

[MIT](LICENSE) — permissive and simple, the standard choice for research templates. (If you need
an explicit patent grant for corporate contributors, Apache-2.0 is the alternative.)

Note: the third-party system-prompt collections used as design sources are **not** part of this
repository (gitignored); `.claude/prompts/README.md` documents the provenance.
