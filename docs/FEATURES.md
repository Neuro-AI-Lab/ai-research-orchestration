# Feature Reference

**English** | [한국어](FEATURES.ko.md)

Use this page to confirm what the distributed system does and where a capability belongs. New users
should start with the [README](../README.md) and [setup guide](../SETUP.md); this reference describes
shipped behavior only, not plans or development history.

## At a glance

| Question | Answer |
|---|---|
| Can one checkout run both providers? | No. Initialize one backend and use another checkout for comparison. |
| Are specialist calls observable? | A delegated stage must report its runtime agent/thread identity and RESULT evidence. |
| Does `bypass` skip scientific review? | No. It changes machine permissions, not critic, QA, leakage, or RESULT gates. |
| Is native hash-chained auditing shared? | No. It is a Codex-owned capability; Claude reports its own runtime evidence. |
| Does the template guarantee a correct finding? | No. It exposes evidence, checks, uncertainty, disagreement, and missing verification. |

## Shared distribution features

| Feature | Interface | Behavior |
|---|---|---|
| Provider selection | `./orchestrate codex|claude` | one backend per checkout |
| Provider-specific initialization | `./orchestrate init <backend>` | creates only selected live state and locks checkout |
| Provider-specific diagnostics | `./orchestrate doctor <backend>` | checks only selected local settings/state and selected CLI |
| Fleet selection | `--preset quality|balanced|fast` | research quality/cost trade-off |
| Specialist override | `--role ROLE=PRESET|MODEL@EFFORT` | provider-valid role/model resolution |
| Permission posture | `--permissions safe|bypass` | safe default; explicit unsafe acknowledgement |
| Research gates | provider-owned hooks | passed critic, QA, and leakage attestations before execution |
| Delegation contract | BRIEF → RESULT → HANDOFF | bounded scope and evidence-grounded dependency transfer |
| Literature and references | literature/Zotero MCP and CLI | primary-source and metadata hygiene |
| Paper workflow | Overleaf Git tools | pull, grounded drafting, critic/QA review, authorized push |
| Long runs | `run_with_status.sh` | status, heartbeat, logs, exit code, resume visibility |
| Release hygiene | `./orchestrate release-check` | state, secrets, docs, tests, isolation, ignored history |

## CODEX

### Conductor-orchestrator

The root Codex session is both conductor and orchestrator and is the only coordination authority.
It directly dispatches eight configured specialists: `brainstorm`, `data`, `critic`, `developer`,
`qa`, `experiment-tracker`, `filemanager`, and `writer`.

- No conductor/orchestrator subagent or lead-agent fleet row exists.
- `max_depth = 1`; specialists cannot delegate.
- At most four specialists are active concurrently.
- The root checkpoints before eight total dispatches.
- Independent work may run in parallel; shared writes and gate-dependent stages remain serialized.

The `quality`, `balanced`, and `fast` presets contain exactly these eight roles. `orchestrator` is not
a valid Codex role override because coordination belongs to the root session.

### Native orchestration audit

A launch through `./orchestrate codex` creates an ignored Codex-owned run ledger. Native hooks record:

- root session observation and completion;
- runtime-issued specialist IDs and roles;
- pre-registered/delivered BRIEF hashes;
- RESULT contract verdicts and body hashes;
- experiment-gate allow/block decisions;
- a sequence-checked SHA-256 event chain.

```bash
./orchestrate runs list
./orchestrate audit latest
./orchestrate audit <run-id> --json
```

The report uses `Conductor-orchestrator: verified` and lists every observed specialist's BRIEF and
RESULT verdict. Missing hooks, unbound BRIEFs, invalid/missing RESULTs, incomplete root sessions, or
event-chain changes produce unverified claims and a non-zero audit result.

The ledger retains bounded metadata and hashes, not prompt/RESULT bodies, transcript paths, tokens, or
datasets. It is local tamper evidence, not a remote signed attestation. A direct `codex` session has no
project run ID and cannot become a verified project-orchestrated run.

### Codex-owned research capabilities

- repository skills for literature evidence, hypotheses, leakage, reproducibility, statistics,
  validity review, grounded writing, papers, and version management;
- Codex-owned role prompts, fleets, hooks, settings, research state, memory, and handoff;
- literature and Zotero MCP servers configured in `.codex/config.toml`;
- Codex-owned Overleaf, long-run, sweep, and reference scripts.

## CLAUDE

Claude ships an independent control plane with its own lead-agent roles, eight research specialists,
fleet manifests, prompts, skills, hooks, settings, research state, memory, handoff, and integrations.

- `quality`, `balanced`, and `fast` are resolved only from `.claude/fleets/` and `.claude/agents/`.
- Provider-specific critic/data/QA floors prevent a cheaper preset from weakening research gates.
- Claude's hooks enforce RESULT, session, experiment, and provider-state rules using only `.claude/`.
- Claude literature, Zotero, Overleaf, long-run, and sweep tools live only in `.claude/scripts/`.
- Runtime reports must include returned agent/thread IDs and RESULT evidence.

Claude does not read or write `.codex/runs/`. The Codex native audit report is therefore unavailable
for Claude runs and must not be presented as Claude evidence.

## Current limitations

- Optional literature, Zotero, and Overleaf operations depend on their external services and accounts.
- Research gates are workflow-validity controls, not a security sandbox or complete shell parser.
- Local audit evidence cannot defend against an administrator able to rewrite both code and ledger.
- The template cannot guarantee scientific truth; it makes evidence, uncertainty, disagreements, and
  missing verification explicit.
