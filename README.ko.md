# AI 연구 오케스트레이션

[English](README.md) | **한국어**

AI/ML 연구를 명시적인 specialist 역할, 근거 계약, 검토 gate로 수행하기 위한 소스 배포판입니다.
문헌 조사, 가설 설계, 데이터 무결성, 구현, 독립 QA, 실험, 분석, 참고문헌, 논문 검토를 다룹니다.

이 저장소에는 서로 독립적인 두 provider 구현이 있습니다. 연구 checkout마다 기본 provider 하나를
선택하며 두 시스템은 협업하거나 연구 state를 공유하지 않습니다. Provider를 비교할 때는 별도
clone 또는 worktree를 사용하는 것이 가장 안전합니다.

## Provider 선택

| Provider | 조정 방식 | 사용자 가이드 |
|---|---|---|
| Codex | root session이 direct specialist를 조정하도록 설계 | [Codex 가이드](docs/orchestration/CODEX.ko.md) |
| Claude Code | provider-owned lead-agent routing과 specialist | [Claude 가이드](docs/orchestration/CLAUDE.ko.md) |

Maintainer와 release 절차는 [maintainer 가이드](docs/orchestration/MAINTAINERS.ko.md)에 있습니다.

## 빠른 시작

전용 checkout에서 기본 provider를 초기화합니다.

```bash
git clone <this-repo> my-research
cd my-research
./orchestrate init codex       # 또는: ./orchestrate init claude
./orchestrate doctor codex     # 같은 provider 사용
./orchestrate codex --preset quality --dry-run
./orchestrate codex --preset quality
```

`init`은 ignored provider-owned local state를 만들고 기본 provider를 저장합니다. 다른 provider를
명시적으로 실행하면 경고 후 허용되지만 data, evaluation, entry-point 경로는 여전히 공유됩니다.
동일 파일에서 두 provider를 동시에 실행하지 마세요.

`doctor`는 파일, 설정, CLI capability, local MCP handshake를 검사합니다. Native specialist가
선택 role, BRIEF, RESULT 계약을 실제로 받았다는 증거는 아닙니다. 본 연구를 시작하기 전에 선택
provider 가이드의 one-specialist smoke test를 실행하고 반환된 runtime ID와 근거를 확인하세요.

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
가이드의 account·network 설정이 필요합니다. Local setting, token, research state, run ledger,
dataset, 생성된 run·analysis output, paper checkout을 commit하지 마세요.

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
