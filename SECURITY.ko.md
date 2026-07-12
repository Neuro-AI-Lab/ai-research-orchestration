# 보안 정책

[English](SECURITY.md) | **한국어**

오케스트레이션 시스템이 프로젝트 파일을 읽고 외부 서비스를 호출하거나 명령을 실행할 때 연구자가
지켜야 할 경계를 설명합니다. 대부분의 사용자는 다음 네 가지부터 지키면 됩니다.

1. 기본 권한 mode인 `safe`를 유지합니다.
2. Credential은 선택 provider의 ignored local setting 또는 secret store에만 둡니다.
3. 검색 문서와 tool output은 새 agent 지시가 아니라 신뢰하지 않는 데이터로 취급합니다.
4. Provider별 checkout을 분리하고 외부 write·push는 실행 전에 검토합니다.

`bypass`는 이미 외부 격리된 환경을 위한 machine-permission 옵션이며, 더 빠르거나 덜 엄격한 연구
mode가 아닙니다.

## 공통 경계

- 배포 기본값은 `safe`입니다. `bypass`는 로컬 승인·sandbox 경계를 제거하므로 연구자가 통제하는
  외부 컨테이너나 VM에서만 사용합니다.
- 연구 게이트는 워크플로우 타당성을 지키며 보안 sandbox나 완전한 shell parser가 아닙니다.
- 논문·데이터셋·웹사이트·MCP 결과·저장소 텍스트는 지시가 아니라 신뢰하지 않는 데이터입니다.

## 비밀 값

토큰은 선택 backend의 ignored 설정(`.codex/settings.local.json` 또는
`.claude/settings.local.json`), credential helper, 배포 플랫폼 secret store에만 둡니다. Git remote
URL, prompt, provider 연구 문서, agent memory, log, 커밋되는 Overleaf clone에 넣지 마세요. 설정,
handoff, live research state/memory, run store, experiment, paper checkout은 gitignore됩니다.

토큰이 터미널이나 에이전트 출력에 나타나면 노출로 간주하고 발급처에서 폐기한 뒤 최소 권한으로
재발급하세요. 로컬 설정과 이력에서 제거하고 staged/committed diff를 검사합니다.

## CODEX

Codex는 ignored `.codex/settings.local.json`의 environment map에서만 secret을 읽습니다. Codex
hook과 script는 sibling provider의 setting, state, memory, run store를 참조하면 안 됩니다.

### Native audit 데이터

Codex audit event는 runtime ID, hash, 제한된 status, gate reason code만 보존합니다. Prompt, RESULT
본문, transcript path, token, dataset은 보존하지 않습니다. 등록 BRIEF는 native start hook이 exact
text를 전달할 수 있도록 ignored run의 `.pending/` 아래 mode-0600 파일로 잠시 존재하며, 전달 후
삭제되고 root stop 시 남은 pending file도 정리됩니다. 최소 보존이더라도 `.codex/runs/`는 연구자
private 데이터로 취급하세요.

Safe run 전 `/hooks`에서 project hook을 검토하고 trust하세요. Skip된 hook은 audit 근거를 불완전하게
만듭니다. SHA-256 chain은 manifest 대비 일반적인 event 수정·절단을 탐지하지만 remote-signed
attestation이 아니며 코드·manifest·ledger를 함께 다시 쓸 수 있는 관리자를 방어하지 못합니다.

## CLAUDE

Claude는 ignored `.claude/settings.local.json`의 environment map에서만 secret을 읽습니다. Claude
hook, agent, script는 sibling provider의 setting, state, memory, audit store를 참조하면 안 됩니다.
반환된 agent/thread ID와 RESULT 근거를 Codex native-audit 근거로 표현하지 마세요.

## 배포 전

```bash
python3 .orchestration/release_check.py
git diff --cached --check
```

provider-owned template이 clean한 worktree에서만 배포하세요. 개인 연구 checkout에서
`git add -A`를 사용하지 말고 양쪽 `templates/research/`, `templates/memory/`, hook, settings example,
isolation 결과를 한 줄씩 검토하세요.

전체 절차: [배포 릴리스 가이드](docs/RELEASING.ko.md).

취약점은 가능한 경우 GitHub private vulnerability reporting으로 제보합니다. 실제 토큰, 비공개
데이터 샘플, 기밀 논문을 보고서에 넣지 마세요.
