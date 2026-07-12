# 기능 레퍼런스

[English](FEATURES.md) | **한국어**

이 문서는 배포 시스템이 실제로 무엇을 하고 각 기능을 어느 provider가 소유하는지 확인할 때
사용합니다. 처음 사용하는 경우 [README](../README.ko.md)와
[설정 가이드](../SETUP.ko.md)를 먼저 보세요. 여기에는 roadmap이나 개발 이력이 아니라 현재
배포되는 동작만 기록합니다.

## 한눈에 보기

| 질문 | 답 |
|---|---|
| 한 checkout에서 두 provider를 함께 실행할 수 있나요? | 아니요. Backend 하나를 초기화하고 비교용 checkout을 따로 만드세요. |
| Specialist 호출 여부를 확인할 수 있나요? | 위임된 단계는 runtime agent/thread ID와 RESULT 근거를 보고해야 합니다. |
| `bypass`가 과학적 검토도 건너뛰나요? | 아니요. Machine permission만 바꾸며 critic, QA, leakage, RESULT gate는 유지합니다. |
| Native hash-chain audit을 둘 다 사용하나요? | 아니요. Codex 전용이며 Claude는 자체 runtime 근거를 보고합니다. |
| 올바른 연구 결론을 보장하나요? | 아니요. 근거, 점검, 불확실성, 이견, 미검증 항목을 드러내는 시스템입니다. |

## 공통 배포 기능

| 기능 | Interface | 동작 |
|---|---|---|
| Provider 선택 | `./orchestrate codex|claude` | checkout당 backend 하나 |
| Provider별 초기화 | `./orchestrate init <backend>` | 선택 live state만 생성하고 checkout 고정 |
| Provider별 진단 | `./orchestrate doctor <backend>` | 선택 local setting/state와 CLI만 검사 |
| Fleet 선택 | `--preset quality|balanced|fast` | 연구 품질·비용 trade-off |
| Specialist override | `--role ROLE=PRESET|MODEL@EFFORT` | provider-valid role/model 해석 |
| 권한 자세 | `--permissions safe|bypass` | safe 기본, unsafe 명시 확인 |
| 연구 gate | provider-owned hook | 실행 전 critic·QA·leakage positive attestation |
| 위임 계약 | BRIEF → RESULT → HANDOFF | 제한된 scope와 근거 기반 dependency 전달 |
| 문헌·reference | literature/Zotero MCP·CLI | primary source·metadata hygiene |
| 논문 workflow | Overleaf Git tool | pull, 근거 작성, critic/QA review, 승인 push |
| 장기 실행 | `run_with_status.sh` | status, heartbeat, log, exit code, resume visibility |
| 배포 hygiene | `./orchestrate release-check` | state, secret, 문서, test, 격리, ignored history |

## CODEX

### Conductor-orchestrator

Root Codex session은 conductor이자 orchestrator이며 유일한 coordination authority입니다. 다음
8개 specialist를 직접 dispatch합니다: `brainstorm`, `data`, `critic`, `developer`, `qa`,
`experiment-tracker`, `filemanager`, `writer`.

- Conductor/orchestrator subagent나 lead-agent fleet row가 없습니다.
- `max_depth = 1`이며 specialist는 delegate하지 못합니다.
- 동시 active specialist는 최대 4개입니다.
- 총 dispatch 8개 전에 root가 checkpoint합니다.
- 독립 작업만 병렬화하고 shared write와 gate-dependent stage는 직렬화합니다.

`quality`, `balanced`, `fast` preset은 정확히 이 8개 role만 포함합니다. Coordination은 root가
소유하므로 `orchestrator`는 Codex role override가 아닙니다.

### Native orchestration audit

`./orchestrate codex` 실행은 ignored Codex-owned run ledger를 만듭니다. Native hook은 다음을
기록합니다.

- root session 관찰과 완료;
- runtime-issued specialist ID와 role;
- pre-registered/delivered BRIEF hash;
- RESULT contract 판정과 body hash;
- experiment-gate allow/block 결정;
- sequence 검증 SHA-256 event chain.

```bash
./orchestrate runs list
./orchestrate audit latest
./orchestrate audit <run-id> --json
```

Report는 `Conductor-orchestrator: verified`를 표시하고 관찰된 모든 specialist의 BRIEF와 RESULT
판정을 나열합니다. Missing hook, unbound BRIEF, invalid/missing RESULT, 미완료 root session,
event-chain 변경은 unverified claim과 non-zero audit 결과를 만듭니다.

Ledger는 제한된 metadata와 hash만 보존하고 prompt/RESULT 본문, transcript path, token, dataset은
보존하지 않습니다. 이는 local tamper evidence이며 remote signed attestation이 아닙니다. 직접
`codex`를 실행한 session은 project run ID가 없어 verified project orchestration이 될 수 없습니다.

### Codex-owned 연구 기능

- 문헌 evidence, 가설, leakage, 재현성, 통계, validity review, grounded writing, paper,
  version management용 repository skill;
- Codex-owned role prompt, fleet, hook, setting, research state, memory, handoff;
- `.codex/config.toml`에 설정된 literature·Zotero MCP server;
- Codex-owned Overleaf, long-run, sweep, reference script.

## CLAUDE

Claude는 자체 lead-agent role, 8개 research specialist, fleet manifest, prompt, skill, hook,
setting, research state, memory, handoff, integration을 가진 독립 control plane입니다.

- `quality`, `balanced`, `fast`는 `.claude/fleets/`, `.claude/agents/`만으로 해석합니다.
- Provider-specific critic/data/QA floor가 저비용 preset으로 research gate를 약화하지 못하게 합니다.
- Claude hook은 `.claude/`만 사용해 RESULT, session, experiment, provider-state rule을 적용합니다.
- Claude literature, Zotero, Overleaf, long-run, sweep tool은 `.claude/scripts/`에만 있습니다.
- Runtime report에는 반환된 agent/thread ID와 RESULT 근거가 있어야 합니다.

Claude는 `.codex/runs/`를 읽거나 쓰지 않습니다. 따라서 Codex native audit report를 Claude run
근거로 제시하면 안 됩니다.

## 현재 한계

- Literature, Zotero, Overleaf 선택 기능은 외부 service와 account에 의존합니다.
- Research gate는 workflow-validity control이며 보안 sandbox나 완전한 shell parser가 아닙니다.
- Local audit은 code와 ledger를 모두 수정할 수 있는 관리자를 방어하지 못합니다.
- 템플릿이 과학적 진실을 보장하지는 않지만 evidence, uncertainty, disagreement, missing
  verification을 명시적으로 드러냅니다.
