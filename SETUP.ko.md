# 설정 가이드

[English](SETUP.md) | **한국어**

이 문서는 새 clone을 만들고 첫 연구 session을 진단·실행하는 과정까지 안내합니다. 설정은 provider
하나 초기화, 진단 실행, fleet 시작의 세 단계입니다. 내장 demo에는 선택 기능인 문헌·논문
integration이 필요하지 않습니다.

## 시작 전 확인

Checkout 하나에는 provider 하나만 설정합니다. Codex와 Claude를 비교하려면 live research,
memory, experiment, paper draft가 섞이지 않도록 clone 또는 worktree를 두 개 사용하세요.

| 요구 항목 | 필요한 이유 | 확인 명령 |
|---|---|---|
| Python 3.8+ | launcher, hook, MCP server, 검증 실행 | `python3 --version` |
| Git | 저장소와 Overleaf workflow | `git --version` |
| POSIX shell | 실행·연구 utility script | `bash --version` |
| Codex 또는 Claude Code CLI | 선택한 agent runtime | `codex --version` 또는 `claude --version` |

Linux가 주 대상입니다. Windows에서는 WSL2 또는 Linux container/VM을 사용하세요. 인터넷은 provider
login과 선택 기능인 literature, Zotero, Overleaf 작업에만 필요합니다.

## 설정 명령이 하는 일

| 명령 | 결과 |
|---|---|
| `./orchestrate init <backend>` | clean template에서 ignored local state를 만들고 checkout을 해당 backend로 고정 |
| `./orchestrate doctor <backend>` | 필수 파일, CLI capability, fleet/topology, local 설정, 격리 점검 |
| `./orchestrate <backend> --preset quality` | 선택 provider를 이 저장소의 연구 control plane과 함께 시작 |

Doctor가 failure를 보고하면 다음 단계로 진행하지 마세요. 준비된 checkout은 마지막에
`0 failure(s), 0 warning(s)`가 표시됩니다. 아래 예시는 연구 핵심 추론·검토용 기본값인
`quality`를 사용하며, 저비용 preset은 선택 사항입니다.

## CODEX

### 초기화와 진단

```bash
git clone <this-repo> my-research-codex
cd my-research-codex
codex --version
./orchestrate init codex
./orchestrate doctor codex
./orchestrate demo                     # 선택: dependency 없는 onboarding 실행
./orchestrate codex --preset quality
```

초기화는 비파괴적이며 clean template으로부터 Codex-owned ignored live file만 만듭니다. 이
checkout은 `codex`로 고정됩니다. Root Codex session이 유일한 conductor-orchestrator로 자동
로드되므로 별도 `orchestrator` subagent를 만들거나 설정하지 마세요.

Fleet 설정 팁:

- 가설 선택, critic/QA gate, 결과 분석, 논문 review는 `quality`를 사용합니다.
- 일반 구현과 제한된 탐색은 `balanced`를 사용합니다.
- 넓은 1차 검색과 기계적 작업은 `fast`를 사용합니다.
- Root 조정 역할이 아니라 specialist만 override합니다: `--role brainstorm=fast` 또는
  `--role critic=gpt-5.6-sol@max`.
- 동시 specialist는 최대 4개로 두고 총 dispatch 8개 전에 checkpoint합니다.

실행하지 않고 command를 확인할 수 있습니다.

```bash
./orchestrate codex --preset quality --dry-run
```

첫 safe 실행에서 Codex UI의 project hook을 검토하고 trust하세요. Hook trust를 건너뛰면 audit이
unverified로 남습니다. 외부 격리 환경에서만 다음을 사용하세요.

```bash
./orchestrate codex --preset quality \
  --permissions bypass --allow-unsafe-bypass
```

Bypass는 로컬 승인과 sandbox를 제거하지만 critic, QA, data-leakage, RESULT, session gate는
제거하지 않습니다.

### 선택 integration

초기화가 만든 ignored `.codex/settings.local.json`만 편집합니다. Secret을 tracked file에 넣지
마세요. 지원 값은 `LIT_CONTACT_EMAIL`, `S2_API_KEY`, `ZOTERO_API_KEY`, `ZOTERO_USER_ID` 또는
`ZOTERO_GROUP_ID`, `ZOTERO_LOCAL`, `OVERLEAF_GIT_TOKEN`입니다.

```bash
codex mcp list  # 첫 project trust 후 실행
python3 .codex/scripts/lit_search.py openalex "your topic" --limit 3
python3 .codex/scripts/zotero_mcp.py collections
python3 .codex/scripts/zotero_mcp.py search "your topic" --limit 10
.codex/scripts/overleaf_sync.sh clone <project-id> docs/paper-codex-my-paper
```

Project trust 후 `literature`, `zotero` row가 모두 `enabled`여야 합니다. Trust 전에는 doctor가
activation pending으로 표시하지만 project config와 두 server handshake는 계속 검증합니다. 이
local STDIO server에서
`Auth: Unsupported` 표시는 Codex-managed OAuth가 적용되지 않는다는 뜻이며, Zotero credential은
ignored local environment로 전달합니다. 위 CLI command는 같은 구현을 직접 실행합니다. MCP 설정이나
credential을 바꾼 뒤에는 새 Codex session을 시작하세요.

`.codex/docs/integrations/ZOTERO.md`, `.codex/docs/integrations/OVERLEAF.md`를 참고하세요. 검색
결과는 후보이므로 인용 전에 stable ID와 primary source를 검증합니다. Overleaf는 편집 전 pull하고
사용자가 명시적으로 허가한 경우에만 push합니다.

### 연구 시작과 audit

```text
Codex quality fleet을 사용하라. 유일한 root conductor-orchestrator로서 <research question>에
필요한 최소 specialist를 직접 spawn하라. Spawn 전 정확한 BRIEF를 등록하라. Critic 승인 전에
구현하지 말고 DATASET leakage와 QA gate가 통과하기 전에 실험하지 마라. Native agent ID,
RESULT 근거, artifact, 검증 command, 미해결 gate를 보고하고 마지막에
`./orchestrate audit latest`를 실행하라.
```

Codex session을 종료한 뒤:

```bash
./orchestrate runs list
./orchestrate audit latest
./orchestrate audit latest --json
```

Verified run에는 native root session, 시작된 모든 specialist의 delivered BRIEF와 valid RESULT,
정상 event chain, 완료된 root session이 필요합니다. 직접 `codex`를 실행한 session은 project run
ID가 없어 이 판정을 만들 수 없습니다.

장시간 job:

```bash
.codex/scripts/run_with_status.sh EXP-001 -- \
  ./run.sh --config experiments/codex/EXP-001/config.yaml
```

## CLAUDE

### 초기화와 진단

```bash
git clone <this-repo> my-research-claude
cd my-research-claude
claude --version
./orchestrate init claude
./orchestrate doctor claude
./orchestrate demo
./orchestrate claude --preset quality
```

초기화는 Claude-owned ignored live file만 만들고 checkout을 `claude`로 고정합니다. Claude는
자체 lead-agent topology와 specialist definition을 유지합니다. Claude fleet row만 사용하세요.

```bash
./orchestrate claude --preset fast --role critic=quality
./orchestrate claude --dry-run
```

`.claude/settings.local.json`만 편집합니다. Claude integration command는 `.claude/scripts/`를
사용합니다.

```bash
python3 .claude/scripts/lit_search.py openalex "your topic" --limit 3
python3 .claude/scripts/zotero_mcp.py search "your topic" --limit 10
.claude/scripts/overleaf_sync.sh clone <project-id> docs/paper-claude-my-paper
```

`.claude/ZOTERO.md`, `.claude/OVERLEAF.md`를 참고하세요. Claude는 반환된 agent/thread ID와
RESULT 근거를 보고해야 하지만 Codex native audit ledger는 읽거나 쓰지 않습니다.

장시간 job:

```bash
.claude/scripts/run_with_status.sh EXP-001 -- \
  ./run.sh --config experiments/claude/EXP-001/config.yaml
```

## 공통 연구 규칙

선택 provider는 자체 `research/`, state, memory, integration setting,
`experiments/<backend>/`만 읽습니다. Root `discussion.md`, `result.md`, `error.md`, `version.md`는
금지됩니다.

실험 실행 전에 선택 provider state에 다음 positive attestation 3개가 모두 있어야 합니다.

1. DATASET leakage audit passed;
2. open blocker가 없는 critic REV gate passed;
3. open critical issue가 없는 QA gate passed.

모든 위임 단계는 BRIEF → RESULT → evidence 기반 HANDOFF를 사용합니다. 실패·negative run도
보존합니다. Zotero를 reference authority로 유지하고 manuscript의 모든 수치를 reviewed
experiment/source ID에 연결합니다. 전체 workflow prompt는
[prompt book](docs/AI_RESEARCH_PROMPTS.ko.md)을 보세요.

Maintainer 배포 검증 command:

```bash
python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate release-check
```

[SECURITY.ko.md](SECURITY.ko.md), [docs/RELEASING.ko.md](docs/RELEASING.ko.md)를 참고하세요.
