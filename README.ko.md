# AI 연구 오케스트레이션 시스템

[English](README.md) | **한국어**

AI/ML 연구를 단계별로 계획하고 검토할 수 있게 만드는 provider 선택형 템플릿입니다. 하나의
에이전트에게 모든 일을 맡기는 대신 문헌 조사, 가설 설계, 데이터 점검, 구현, 독립 검증, 실험,
분석, 참고문헌 관리, 논문 리뷰를 역할과 게이트로 분리합니다.

이 템플릿은 연구 과정과 근거를 추적할 수 있게 정리하지만 과학적 주장의 진실을 보장하지는
않습니다. 또한 Codex와 Claude를 서로 협업시키지 않습니다. Checkout마다 backend 하나를
선택하세요.

## 제공 기능 요약

| 연구자가 하려는 일 | 이 저장소가 제공하는 것 |
|---|---|
| 연구 설계 | 문헌, 가설, 실행 가능성, critic 검토 단계 |
| 평가 타당성 보호 | 데이터 출처, 누출 점검, critic·QA 게이트 |
| 재현 가능한 구현·실행 | 구현/실행 역할 분리, config, seed, log, 상태 도구 |
| 불확실성을 보존한 분석 | 효과 크기, 불확실성, 실패 실행, 민감도, 한계 점검 |
| 논문 관리 | Zotero 참고문헌, Overleaf Git workflow, 과학·artifact 리뷰 |
| 오케스트레이션 확인 | runtime ID와 RESULT 근거, Codex의 native local audit ledger |

## Backend 하나 선택하기

| | CODEX | CLAUDE |
|---|---|---|
| 조정 방식 | root Codex session이 specialist를 직접 조정 | Claude 자체 lead-agent routing 사용 |
| 실행 근거 | native agent ID, BRIEF/RESULT 판정, local hash-chain audit | 반환된 agent/thread ID와 RESULT 근거 |
| 제어 파일 | `AGENTS.md`, `.codex/`, `.agents/skills/` | `CLAUDE.md`, `.mcp.json`, `.claude/` |
| 선택 기준 | 배포 환경에서 Codex를 사용할 때 | 배포 환경에서 Claude Code를 사용할 때 |

두 backend 모두 `quality`, `balanced`, `fast` fleet과 동일한 기본 연구 단계를 제공합니다. 그러나
실행 규칙, state, memory, integration, 근거 저장소는 완전히 분리됩니다. 비교하려면 하나의 활성
checkout에서 provider를 바꾸지 말고 clone 또는 worktree를 두 개 만드세요.

## 빠른 시작

다음 명령은 Codex checkout을 만들고, 설정을 검증한 뒤 연구 session을 엽니다.

```bash
git clone <this-repo> my-research-codex
cd my-research-codex
./orchestrate init codex
./orchestrate doctor codex
./orchestrate codex --preset quality
```

정상 설정이면 doctor 마지막에 `0 failure(s), 0 warning(s)`가 표시됩니다. Claude는 다른
checkout에서 `codex`를 `claude`로 바꾸세요. 속도·비용이 최대 reasoning effort보다 중요한 경우가
아니라면 처음에는 `quality`를 권장합니다.

Provider session이 열리면 연구 질문, 제약 조건, 요구 근거 수준, 중단 조건을 알려주세요. 문헌
조사, 아이디어 설계, 구현, QA, 분석, Zotero, Overleaf용 복사 가능 요청문은
[AI 연구 프롬프트 북](docs/AI_RESEARCH_PROMPTS.ko.md)에 있습니다.

## 문서 안내

| 필요한 정보 | 문서 |
|---|---|
| 첫 checkout 설치·실행 | [설정 가이드](SETUP.ko.md) |
| 연구 workflow 요청문 복사 | [AI 연구 프롬프트 북](docs/AI_RESEARCH_PROMPTS.ko.md) |
| 실제 구현 기능 확인 | [기능 레퍼런스](docs/FEATURES.ko.md) |
| OS·CLI·도구 요구 조건 확인 | [호환성](docs/COMPATIBILITY.ko.md) |
| credential·권한 mode 안전 설정 | [보안 정책](SECURITY.ko.md) |
| 배포 release 준비 | [배포 가이드](docs/RELEASING.ko.md) |

## 설계 단계부터 완전 분리

`./orchestrate init <backend>`는 선택 backend를 ignored 로컬 설정에 기록하고 해당 backend의
live state만 생성합니다. 두 시스템은 협업자가 아니라 대안입니다.

| 경계 | CODEX checkout | CLAUDE checkout |
|---|---|---|
| 진입 정책 | `AGENTS.md` | `CLAUDE.md` |
| Control plane | `.codex/`, `.agents/skills/` | `CLAUDE.md`, `.mcp.json`, `.claude/` |
| 현재 연구 | `.codex/research/` | `.claude/research/` |
| Memory·handoff | `.codex/memory/`, `.codex/state/` | `.claude/agent-memory/`, `.claude/state/` |
| 생성 artifact | `experiments/codex/`, `analysis/codex/` | `experiments/claude/`, `analysis/claude/` |

권한 기본값은 `safe`입니다. `--permissions bypass --allow-unsafe-bypass`는 로컬 승인·sandbox
경계를 제거하므로 연구자가 통제하는 외부 container/VM 안에서만 사용하세요. Critic, QA,
data-leakage 등 연구 타당성 gate는 우회하지 않습니다.

## CODEX

Root Codex session이 conductor이자 orchestrator입니다. 사용자 의도를 해석하고, 최소 팀을
선택하고, BRIEF를 등록하고, native specialist를 직접 dispatch하고, RESULT와 gate를 평가하고,
충돌을 해결해 최종 결과를 종합합니다. 별도 conductor/orchestrator subagent는 없으며 specialist는
다른 agent를 spawn할 수 없습니다.

```text
user <-> root Codex conductor-orchestrator
                  |-- brainstorm          문헌·아이디어·가설
                  |-- data                출처·split·leakage
                  |-- critic              타당성·통계 gate
                  |-- developer           구현
                  |-- qa                  독립 검증
                  |-- experiment-tracker  재현 가능한 실행
                  |-- filemanager         저장소·version 관리
                  `-- writer              근거 기반 보고서·논문
```

Topology는 의도적으로 single-hop입니다. 동시 specialist는 최대 4개, 독립 작업만 병렬화하며,
총 dispatch 8개 전에 root가 checkpoint합니다. 불필요한 조정 계층 없이 specialist context 격리를
유지합니다.

```bash
./orchestrate codex --preset quality
./orchestrate codex --preset balanced --role brainstorm=fast
./orchestrate codex --role critic=gpt-5.6-sol@max
./orchestrate codex --dry-run
```

### MCP integration

Codex는 `.codex/config.toml`에서 project MCP server를 로드합니다.

- `literature`: arXiv, OpenAlex, PubMed, Semantic Scholar용 `lit_search`, `lit_fetch`;
- `zotero`: library 검색, item/full-text, BibTeX, collection, 선택 save-back.

```bash
./orchestrate codex --preset quality  # 첫 실행에서 project를 검토하고 trust
# trust 후 새 session을 시작하고 project directory에서 확인:
codex mcp list                        # 두 row가 모두 enabled여야 함
```

Project-scoped MCP는 trusted repository에서만 로드됩니다. Fresh checkout은 첫 trust 전까지
server가 목록에 나타나지 않을 수 있습니다. MCP tool은 session 시작 시 로드되므로 project
trust 또는 `.codex/config.toml`/
`.codex/settings.local.json`을 변경한 뒤 launcher로 새 session을 시작하세요. 이미 실행 중인
session에는 새 tool이 추가되지 않습니다. Zotero credential은 선택이지만 Zotero 호출에는 API
설정 또는 `ZOTERO_LOCAL=1`이 필요합니다. Overleaf는 MCP가 아니라 명시적으로 승인하는 Git sync
script를 사용합니다.

### 프로젝트 orchestration 사용 증명

실제 spawn은 Codex native harness가 수행합니다. 이 저장소는 role spec, skill, BRIEF 전달, hook,
gate, audit ledger를 제공합니다. `./orchestrate codex`로 시작한 session에는 run ID가 부여되고,
native lifecycle hook이 root session, runtime agent ID, BRIEF hash, RESULT 판정, research-gate
결정을 hash chain에 기록합니다.

```bash
./orchestrate runs list
./orchestrate audit latest
./orchestrate audit latest --json
```

예상 출력 형식:

```text
Run: ORCH-YYYYMMDD-001
Backend: codex
Fleet: quality
Topology: root-conductor-direct
Status: completed
Event chain: verified
Conductor-orchestrator: verified
Specialists:
  brainstorm  agent-123  BRIEF delivered  RESULT valid
  critic      agent-456  BRIEF delivered  RESULT valid
Research gates: 1 allowed, 0 blocked
Unverified claims: 0
```

직접 `codex`를 실행해도 project guidance는 읽을 수 있지만 launcher run ID가 없으므로 검증된
project orchestration으로 보고할 수 없습니다. Ignored `.codex/runs/`에는 제한된 metadata와
hash만 남고 prompt/RESULT 본문, dataset, token, transcript path는 저장하지 않습니다.

복사해서 사용할 요청:

```text
Codex quality fleet으로 이 연구를 오케스트레이션해줘. Root Codex session이 유일한
conductor-orchestrator로서 brainstorm -> critic -> data -> developer -> qa를 의존 순서로 직접
spawn해라. 각 spawn 전에 정확한 BRIEF를 등록하라. 모든 native agent ID, RESULT 근거, artifact,
검증 명령, 미해결 gate를 보고하라. 마지막에 `./orchestrate audit latest`를 실행하고, 실패하거나
검증되지 않은 dispatch를 성공했다고 주장하지 마라.
```

상세 정책은 [.codex/README.md](.codex/README.md),
[.codex/ORCHESTRATION.md](.codex/ORCHESTRATION.md)에 있습니다. 선택 integration secret은 ignored
`.codex/settings.local.json`에만 둡니다. Codex 문헌·Zotero·장기 실행·sweep·Overleaf 도구는
`.codex/scripts/`가 소유합니다.

## CLAUDE

Claude는 자체 lead agent, specialist, skill, hook, fleet, prompt, research state, memory,
integration을 가진 독립 control plane입니다. Codex role, skill, state, audit record를 읽지 않습니다.

```bash
git clone <this-repo> my-research-claude
cd my-research-claude
./orchestrate init claude
./orchestrate doctor claude
./orchestrate claude --preset quality
./orchestrate claude --preset fast --role critic=quality
```

Claude 도구와 secret은 `.claude/scripts/`, ignored `.claude/settings.local.json`을 사용합니다.
Runtime contract는 반환된 agent/thread ID와 RESULT 근거를 보고합니다. Codex native ledger는
공유되지 않으므로 Claude run의 증거로 인용하면 안 됩니다. 자세한 구조는
[.claude/README.md](.claude/README.md)를 보세요.

## AI 연구 workflow

| 단계 | 담당 | 다음 의존 단계 전 필수 산출물 |
|---|---|---|
| 문헌 | `brainstorm` | 1차 출처 evidence map, stable ID, caveat |
| 가설 | `brainstorm` | 예측, falsifier, baseline, metric, effect threshold |
| 계획 심사 | `critic` | passed/blocked REV와 해결 조건 |
| 데이터 | `data` | 출처, license, split unit, hash, leakage audit |
| 구현 | `developer` | 승인 범위, immutable config, 집중 test |
| 독립 QA | `qa` | 실제 diff·명령 검증과 passed/blocked QA |
| 실험 | `experiment-tracker` | code/data/config provenance, seed, log, failure |
| 분석 | `critic` | effect size, uncertainty, sensitivity, limitation |
| 논문 | `writer` | claim-evidence map과 검증 reference |
| 최종 심사 | `critic`, 이후 `qa` | 과학적·artifact/citation clearance |

모든 위임은 BRIEF → RESULT 계약을 따르고, 의존 작업에는 실제 RESULT로만 만든 HANDOFF를
전달합니다. 실험 전 선택 provider의 state에 passed DATASET leakage audit, critic gate, QA gate가
있어야 하며 open critical issue가 없어야 합니다. Override는 완전한 ADR과 각 launch segment의
`GATE_OVERRIDE=ADR-NNN`이 필요합니다.

검색 결과와 abstract는 검증 evidence가 아니라 후보입니다. Lab library를 활용할 때 Zotero를
먼저 검색하고, primary source metadata/full text를 검증하며, 모순을 보존하고 citation을 만들지
마세요. Overleaf는 편집 전 pull하고, 명시적으로 허가된 push 전에 critic·QA review를 거칩니다.

## 프로젝트 layout

대부분의 연구 작업은 `data/`, `models/`, `evaluation/`, `experiments/`, `analysis/`, `papers/`에서
진행합니다. Provider directory는 orchestration control plane이므로 서로 role, state, setting을
복사하지 마세요. Live state directory는 초기화할 때 로컬에 생성되며 계속 ignore됩니다.

```text
AGENTS.md, .codex/, .agents/skills/   CODEX control plane
CLAUDE.md, .claude/                   CLAUDE control plane
.orchestration/                       selector, 진단, audit adapter, 배포 check
data/, models/, evaluation/           선택 backend가 소유하는 project source
experiments/<backend>/                실행 artifact·status
analysis/<backend>/                   생성 분석
papers/notes/<backend>/               reading note
docs/                                 배포 guide·paper checkout
tests/orchestration/                  현재 동작·격리 test
```

## 라이선스

[MIT](LICENSE)
