# AI 연구 오케스트레이션

[English](README.md) | **한국어**

AI/ML 연구를 명시적인 specialist 역할, 근거 계약, 검토 gate로 수행하기 위한 소스 배포판입니다.
문헌 조사, 가설 설계, 데이터 무결성, 구현, 독립 QA, 실험, 분석, 참고문헌, 논문 검토를 다룹니다.

이 저장소에는 서로 독립적인 두 provider 구현이 있습니다. 연구 checkout마다 provider 하나만
선택하며 두 시스템은 협업하거나 연구 state를 공유하지 않습니다. 초기화 후 launcher가 다른
provider 사용을 거부하므로 비교할 때는 별도 clone 또는 worktree가 필요합니다.

## Provider 선택

| Provider | 조정 방식 | 사용자 가이드 |
|---|---|---|
| Codex | root session이 direct specialist를 조정하도록 설계 | [Codex 가이드](docs/orchestration/CODEX.ko.md) |
| Claude Code | provider-owned lead-agent routing과 specialist | [Claude 가이드](docs/orchestration/CLAUDE.ko.md) |

Maintainer와 release 절차는 [maintainer 가이드](docs/orchestration/MAINTAINERS.ko.md)에 있습니다.
Template을 실제 project로 전환하기 전에 전체
[project 경로 지도](docs/orchestration/PROJECT_MAP.ko.md)를 검토하세요.

## 빠른 시작

전용 checkout에서 기본 provider를 초기화합니다.

```bash
git clone <this-repo> my-research
cd my-research
./orchestrate init codex       # 또는: ./orchestrate init claude
./orchestrate adapt codex      # 변경 없이 project 전환 권고 검토
./orchestrate doctor codex     # 같은 provider 사용
./orchestrate codex --preset quality --dry-run
./orchestrate codex --preset quality
```

`init`은 provider-private local state를 만들고 누락된 workspace seed를 채우며 checkout을 해당
provider에 고정합니다. 같은 checkout에서 다른 provider 실행은 거부됩니다.

`doctor`는 파일, 설정, CLI capability, local MCP handshake를 검사합니다. Native specialist가
선택 role, BRIEF, RESULT 계약을 실제로 받았다는 증거는 아닙니다. 본 연구를 시작하기 전에 선택
provider 가이드의 one-specialist smoke test를 실행하고 반환된 runtime ID와 근거를 확인하세요.

## 프로젝트 layout

| 영역 | 경로 | 목적 |
|---|---|---|
| 연구 개발 | `plan/`, `report/`, `data/` | PRD/checklist, 사용자-agent 연구 기록, dataset·preprocessing asset |
| 개발·배포 | `model/`, `experiments/`, `analysis/`, `functionals/`, `utils/` | model source, experiment code/config, analysis, 재사용 함수·utility |
| 생성 run | `experiments/runs/` | ignore되는 log, checkpoint, metric, run status |

`plan/`, `report/`, `data/`는 의도적으로 blanket-ignore하지 않습니다. 프로젝트의 privacy, license,
용량 정책이 허용하는 자료만 commit하세요.

## Agent team

두 provider는 research/build/ops specialist 책임 여덟 개를 공유합니다. Codex는 root session 자체가
conductor-orchestrator이며 lead agent를 spawn하지 않습니다. Claude는 specialist 여덟 개 외에 primary와
fallback lead definition 두 개를 제공합니다. 아래 표는 Claude `quality` fleet이며 Codex의 별도
quality pin은 `.codex/fleets/`에 있습니다.

| Tier | Agent | Model | Effort | 소유 영역 |
|---|---|---|---|---|
| 1 — coordination | orchestrator | Fable 5(또는 Opus 4.8 + backport prompt) | xhigh | lead routing, gate, synthesis |
| 1 — coordination | orchestrator-opus | Opus 4.8 | xhigh | orchestrator의 fallback twin |
| 2 — research | brainstorm | Sonnet 5 | high | 가설, 문헌, method 설계 |
| 2 — research | data | Sonnet 5 | medium | `data/`, `analysis/` |
| 2 — research | critic | Sonnet 5 | max | validity 적대적 검토 |
| 3 — build | developer | Sonnet 5 | medium | `model/`, `experiments/`, `functionals/`, `utils/`, entry point |
| 3 — verify | qa | Sonnet 5 | high | `tests/`, bug isolation, 실험 전 code gate |
| 4 — ops | experiment-tracker | Sonnet 5 | low | `experiments/runs/` per-run 기록 |
| 4 — ops | filemanager | Sonnet 5 | low | repo 구조, git, env, dependency file |
| 4 — ops | writer | Sonnet 5 | medium | `docs/`, 사용자용 문서, README |

세션 단위로 더 저렴한 preset을 선택할 수 있습니다 — `./orchestrate claude --preset
balanced|fast`(Codex 대응: `.codex/fleets/`) — role별 override도 가능합니다. Research-gate floor는
preset과 무관하게 검증 수준을 지킵니다: `critic`/`qa`는 `sonnet@high` 아래로, `data`는
`sonnet@medium` 아래로 내려가지 않으며 lead role은 항상 Fable 5 또는 Opus 4.8입니다. 전체 표는
[Claude fleet 가이드](.claude/fleets/README.md)와 [CLAUDE.md](CLAUDE.md)를 참고하세요. Codex
plane에도 동일한 role 구성이 있습니다(`.codex/prompts/roles/`, `.agents/skills/`).

## Quality gate와 연구 기록

실험 실행 전 세 가지 mandatory gate를 통과해야 합니다.

1. **Critic**이 plan을 검토합니다(`REV` entry가 `Gate: passed`를 기록; blocking `REV`가 열려 있지
   않아야 함).
2. **QA**가 실제 implementation state/diff를 검증합니다(`QA` entry가 통과 판정을 기록; critical
   `BUG`가 열려 있지 않아야 함).
3. **Data**가 split을 문서화하고 leakage checklist를 실행합니다(`DATASET` entry가 통과한 leakage
   audit을 기록).

이는 절차뿐 아니라 기계적으로도 강제됩니다: `PreToolUse` hook(`.claude/hooks/experiment_gate.py`,
Codex 대응 `.codex/hooks/experiment_gate.py`)이 gate가 하나라도 충족되지 않으면
`run.sh`/`evaluate.sh`/`python model/*.py` 실행을 차단합니다. 문서화된 bypass는 건너뛴 규칙, 이유,
rollback plan을 명시한 `ADR` entry를 작성한 뒤 실행 command 앞에 `GATE_OVERRIDE=ADR-NNN`을 붙여야
하며, hook은 해당 ADR이 존재하고 필수 field를 갖췄는지 확인한 뒤에만 실행을 허용합니다.

연구 state는 `report/` 아래 **version-gated 4-document record**로 관리됩니다. `result.md`,
`discussion.md`, `issue.md`는 현재 version의 typed, append-only entry만 담고(`HYP`/`EXP`/`REV`/
`QA`/`BUG`/`ADR`/... 상호 참조 포함), `version.md`는 milestone 경계마다 각 version의 내용을 흡수하는
누적 archive입니다. Session continuity는 두 layer로 이루어집니다. 선택 provider의 `SessionStart`
hook이 ignored machine-readable hand-off, 열린 gate, 실행 중/orphan experiment를 주입합니다.
Claude는 close 시 hand-off freshness를 강제할 수 있습니다. Codex는 `Stop`을 turn boundary로 기록해
process exit로 오인하지 않으며 launcher가 실제 Codex process exit를 audit ledger에 기록합니다.

## Research features

기본 제공되는 integration과 연구 discipline입니다.

| Capability | 제공 내용 | 위치 |
|---|---|---|
| 문헌 검색 MCP | arXiv, OpenAlex, PubMed, Semantic Scholar search + link fetch, credential 불필요 | `lit_search`/`lit_fetch` tool; server `.claude/scripts/literature_mcp.py`(Codex:
`.codex/scripts/literature_mcp.py`); `.mcp.json`에 등록 |
| Zotero MCP | Search, full-text, collections, add-item, 논문 `.bib`로 바로 export되는 BibTeX — writer가
citation을 손으로 작성하지 않음 | `.claude/scripts/zotero_mcp.py`; Zotero 계정 key 또는 local
desktop API 필요(provider 가이드 참고) |
| Overleaf integration | Git 기반 sync(`clone`/`pull`/`push`/`status`); writer가 소유하는 paper
workflow; compile은 Overleaf 서버에서 수행되어 local LaTeX toolchain 불필요; push guard가 staged
data/secret 경로와 초과 용량 파일을 거부 | `.claude/scripts/overleaf_sync.sh`; Overleaf git token
필요(premium 기능 또는 self-hosted) |
| Reproducibility discipline | `experiments/runs/` 아래 per-run 기록, 실행 전 metadata
capture(commit, config, seed, environment), 매 run 전 dataset-hash 재검증 | `experiment-
reproducibility` skill; `experiment-tracker`, `developer` |
| Leakage defense | 6개 role이 공유하는 split-integrity checklist; leakage가 발견된 experiment는
무효화되어 재실행되며 조용히 삭제되지 않음 | `data-leakage-audit` skill |
| Adversarial review | `max` effort budget을 가진 전담 critic role이 실험 전 plan과 보고 전 result를
검토 | `research-validity-review` skill |
| 신규 project 적응 | `./orchestrate init`과 `./orchestrate adapt <provider>`가 checkout을 machine-readable project map과 비교해 구체적인 비변경 적응 checklist를 출력 | `.orchestration/project_map.json`; [사람용 가이드](docs/orchestration/PROJECT_MAP.ko.md) |

## 연구 workflow

```text
문헌 -> 가설 -> critic -> data/leakage -> 구현 -> QA
     -> 실험 -> 분석/critic -> 작성 -> artifact/reference 검토
```

Runtime이 agent/thread ID와 근거가 있는 RESULT를 반환한 경우에만 위임된 작업으로 인정합니다.
검색 snippet은 인용 근거가 아니라 후보입니다. 실험 전에는 data, critic, QA 승인이 필요하며 논문
주장은 검토된 source 또는 experiment artifact로 추적되어야 합니다.

## 권한과 외부 서비스

기본값은 `safe`입니다. `bypass`는 로컬 승인과 sandbox 경계를 제거하므로 연구자가 통제하는 외부
container 또는 VM에서만 사용합니다. Permission flag는 scientific gate 실행 근거가 아닙니다.
Gate와 runtime report를 별도로 확인하세요.

구현, test, review, 문서화, release 준비는 working-tree 편집만 허용합니다. 사용자가 정확한 작업을
명시적으로 요청하지 않았다면 agent는 stage, branch, commit, pull, push, PR 생성·수정, merge 또는
그 밖의 Git 변경 작업을 수행하면 안 됩니다.

문헌 검색은 private credential 없이 사용할 수 있습니다. Zotero와 Overleaf는 선택 provider
가이드의 account·network 설정이 필요합니다. Local setting, token, provider-private handoff·memory·
run ledger, 생성 run output, paper checkout을 commit하지 마세요. Data는 license, privacy, file size를,
생성 analysis artifact는 배포 적합성을 검토한 뒤 commit합니다.

## 문서 footprint

상세 배포 문서는 모두 `docs/orchestration/` 아래로 통합되어 consumer project에서 한 번에 제외할
수 있습니다.

```gitignore
/docs/orchestration/
```

Git은 untracked 파일만 ignore합니다. 이 소스 저장소를 clone한 프로젝트에서는 ignore rule만
추가해도 이미 tracked된 문서가 untrack되지 않습니다. `AGENTS.md`, `CLAUDE.md`, `.codex/`,
`.claude/` 같은 runtime 정책은 배포 문서가 아니므로 사용하는 provider에서 제거하면 안 됩니다.

## 범위

이 시스템은 연구 과정을 구조화하고 누락된 근거를 드러내지만 연구 주장의 진실을 보장하지
않습니다. Local audit record는 tamper-evident metadata이며 remote-signed attestation이 아닙니다.

## License

[MIT](LICENSE)
