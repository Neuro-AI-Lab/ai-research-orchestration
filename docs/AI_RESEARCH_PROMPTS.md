# AI Research Orchestration Prompt Book

**English** | [한국어](AI_RESEARCH_PROMPTS.ko.md)

This is a copy-ready request library for common AI research tasks. It helps the researcher specify
scope, role separation, evidence, stopping conditions, and the final report without memorizing the
repository's internal layout.

## How to use this book

1. Start the selected backend through `./orchestrate codex` or `./orchestrate claude`.
2. Copy one task template below and replace every `<...>` placeholder.
3. Include the common contract and only the selected backend's contract; never include both provider
   contracts in one checkout.
4. Add concrete constraints such as date range, dataset, metric, compute budget, privacy, and deadline.
5. For a short lookup or explanation, say not to spawn agents; delegation should add independent value.

| Your goal | Start with |
|---|---|
| survey a field or verify novelty | Literature review with MCP |
| turn an idea into testable claims | Ideas and hypotheses |
| check a dataset or split | Data and split design |
| build an accepted method | Implementation |
| review code or research validity | QA and validity review |
| run an approved experiment | Experiment execution |
| interpret completed runs | Result analysis |
| organize citations | Zotero reference management |
| draft or review a manuscript | Overleaf writing and review |
| review the complete package | Full pre-submission review |

For delegated work, require observable runtime identities and contract evidence rather than accepting
an orchestration claim on trust.

## Contract to append to every multiagent request

```text
Use this repository's AI research orchestration for this task. State the selected backend/fleet and
planned roles first. Use only that backend's roles, skills, hooks, research state, memory, experiment
subtree, and integrations; never load the sibling provider control plane. Actually spawn the required
specialists; work without a returned agent/thread ID does not count as delegated. Use a complete BRIEF
for every dispatch and build each HANDOFF only from the preceding RESULT. On Codex, the root session is
the sole conductor-orchestrator: register the exact BRIEF before every native spawn and dispatch the
specialist directly. Never create another coordination layer. In the final report list each role's agent/thread
ID, BRIEF objective, RESULT status, artifact paths/document IDs, verification commands, and unresolved
gates. For Codex, also run `./orchestrate audit latest` and quote its verification verdict. Never claim
a spawn or hook succeeded if it failed. Parallelize independent reads/audits; serialize shared writes
and gate-dependent stages.
```

## CODEX

Append this Codex-specific contract:

```text
Use the Codex quality fleet with root-conductor-direct topology. The root Codex session is the only
conductor-orchestrator. The developer may use balanced, but keep critic and QA on quality. Use
`.codex/research/` and `experiments/codex/` only. Keep concurrency at four or fewer specialists and
checkpoint before eight total dispatches.
```

### Quality fleet with native audit

```text
Use the Codex quality fleet to orchestrate this research. Actually spawn brainstorm → critic → data →
developer → qa in dependency order. Before each spawn, register and deliver the exact BRIEF through the
Codex audit registrar. Report every runtime-issued agent ID, RESULT status/evidence, and unresolved
gate. At the end, run `./orchestrate audit latest`; include the run ID, root verification, each
specialist's BRIEF/RESULT verdict, research-gate counts, event-chain status, and unverified-claim count.
If anything is unverified, say so explicitly and do not relabel it as completed orchestration.
```

This prompt is meaningful only in a session started by `./orchestrate codex`; a direct `codex` session
has no project run ID. The independent Claude system does not consume this Codex ledger.

## CLAUDE

Append this Claude-specific contract:

```text
Use only this checkout's Claude quality fleet, agents, skills, hooks, `.claude/research/`, memory, and
`experiments/claude/`. Follow the Claude-owned lead-agent routing and report every returned agent/thread
ID, BRIEF objective, RESULT evidence, artifact, verification command, and unresolved gate. Do not read
Codex control files or cite a Codex audit report as evidence for this run.
```

## End-to-end research

```text
Orchestrate <research question> end to end in this repository. Constraints: <data/time/compute/license/
privacy>; primary metric: <metric>; budget: <budget>. Actually spawn brainstorm → critic → data →
developer → qa → experiment-tracker → critic → writer as staged specialists. Do not experiment before
the plan REV, DATASET leakage review, and QA gate pass; do not finalize paper claims before result
review. Preserve failed and negative runs. Include every agent/thread ID and BRIEF/RESULT in the final
orchestration report, and include the Codex native-audit verdict when Codex is selected.
```

## Literature review with MCP

```text
Review <topic/question> from <start>-<end>. Spawn brainstorm and search Zotero library-first, then the
literature MCP across OpenAlex, arXiv, PubMed, and Semantic Scholar. Apply inclusion <...>, exclusion
<...>, and venue priorities <...>. Deduplicate by DOI/arXiv/PMID and create RES evidence tables covering
data, method, baselines, metrics, findings, and limitations. Separate abstract evidence from full-text
evidence and mark unverified claims. Spawn critic independently to verify citation existence and the
synthesis.
```

## Ideas and hypotheses

```text
Design <N> hypotheses for <problem> using distinct mechanisms. Spawn brainstorm to give each HYP a
directional prediction, falsifier, data, strong baselines, primary/secondary metrics, minimal experiment,
compute budget, contamination/leakage risk, and literature grounding. Then spawn critic independently to
compare novelty, falsifiability, confounds, and evaluation validity. Do not implement before blocking REV
issues are resolved; report the recommendation and reasons for rejecting alternatives.
```

## Data and split design

```text
Audit <data location/candidates> for HYP-<id>. Spawn data to document source, version, license, hash,
unit, labels, missingness, and duplicates, then design leakage-safe subject/group/time/site splits.
Verify train-only preprocessing, near duplicates, and pretraining contamination. Have critic or QA
independently review split integrity and leave blocking issues open until resolved.
```

## Implementation

```text
Implement only the accepted HYP-<id>, REV-<id>, and DATASET-<id>. Spawn developer to build a thin,
reproducible vertical slice with one baseline and one treatment, recording environment, seeds, configs,
checkpoint/resume, and evaluation entrypoints. Exclude unrelated refactors and experiment execution.
Then spawn QA independently to run tests and reproduction commands. Never hide failures or weaken tests;
report both agent IDs and RESULTs.
```

## QA and validity review

```text
Perform a read-only review of <code/PR/commit/HYP>. Spawn QA for unit/integration/regression tests,
metric direction, determinism, split boundaries, train-only preprocessing, and artifact/log provenance.
Spawn critic independently for leakage, baseline fairness, statistical errors, and over-generalization.
Record each issue as BUG or VAL with severity and a resolution criterion; do not repair it.
```

## Experiment execution

```text
Run the accepted plan for HYP-<id> within <compute budget>. Stop unless a critic REV, QA-NNN, and
DATASET leakage audit explicitly pass, or while a blocking REV/critical BUG is open. Spawn
experiment-tracker; wrap jobs over two minutes with run_with_status and record command, environment,
code revision, config, seeds, logs, artifacts, and status in EXP. Keep failed/negative runs. Do not
finalize a conclusion before independent result analysis.
```

## Result analysis

```text
Analyze EXP-<ids> against <research question>. Have experiment-tracker independently reconcile log,
table, and artifact values, then spawn critic for analysis validity. Report the preregistered primary
metric, baseline differences, sample size, effect sizes, uncertainty, failed seeds, multiple-comparison
handling, sensitivity checks, and ablations. Separate measured facts, interpretation, and speculation;
trace inconsistent numbers instead of averaging them away, and keep causal/generalization language
within the evidence. Record supported, refuted, and unresolved claims with limitations.
```

## Zotero reference management

```text
Curate references for <HYP/section/topic> using Zotero MCP. Spawn brainstorm or writer, search the library
first, and cross-check DOI/title/authors/year/venue. Save only load-bearing papers back with <HYP tag>,
write full-text reading notes under the selected backend's `papers/notes/<backend>/`, check
duplicates/retractions/corrections, and export citekeys/BibTeX from Zotero rather than inventing
entries. Report changed Zotero items and unverified works.
```

## Overleaf writing and review

```text
Draft Overleaf <section> using only reviewed <EXP/REPORT/RES IDs>. Spawn writer to pull first, add
% source: EXP-NNN beside every reported value, and sync Zotero BibTeX. Do not use unmeasured results or
unverified citations. Then spawn critic independently to review claim-evidence alignment, citation
existence, limitations, table/text consistency, and reproducibility. Do not push or mark complete while a
blocking REV remains. Report changed files, source IDs, critic RESULT, and sync status.
```

## Full pre-submission review

```text
Freeze the current manuscript and run an internal pre-submission review. Spawn critic for claims,
statistics, limitations, and novelty; QA for table/figure/text consistency and reproduction commands;
and brainstorm for missing related work and competing explanations. Only after independent RESULTs may
the orchestrator deduplicate findings. Return severity-ranked REV/BUG/VAL items split into required fixes,
recommended fixes, and contestable reviewer opinions. Preserve disagreements.
```

For a direct lookup, explicitly avoid unnecessary delegation:

```text
Read the current state of HYP-003 and its open blocking REV entries. Do not spawn agents.
```

To bound cost, append: `Limit concurrency to 3 specialists and total dispatches to 6; checkpoint and stop
when the limit is reached.`
