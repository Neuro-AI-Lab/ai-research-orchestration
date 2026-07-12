# 배포 릴리스 가이드

[English](RELEASING.md) | **한국어**

일반 사용자 설정이 아니라 템플릿을 배포하는 maintainer용 checklist입니다. Clean 후보에서 모든
배포 검사가 통과하고 실제 연구 데이터, local configuration, credential, run history, maintainer
검증 이력이 포함되지 않아야 release 준비가 끝납니다.

| 단계 | 필수 결과 |
|---|---|
| 준비 | 별도 clean release worktree |
| 검사 | 빈 provider template, 후보에 live/ignored state 없음 |
| 검증 | isolation, deterministic validation, test, demo, release check 모두 통과 |
| 포장 | 명시적 경로 stage, staged diff 검토, secret·credential remote 없음 |

활성 연구 checkout에서 배포하지 마세요. 별도 clean worktree를 사용하여 provider별 research state,
handoff, settings, run log와 memory를 보존합니다.

```bash
git worktree add ../orchestration-release -b release/<version>
cd ../orchestration-release

python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate demo
./orchestrate release-check
```

각 provider의 `templates/research/`와 `templates/memory/` 아래 clean seed를 검토합니다. 실제 연구
state와 memory는 `./orchestrate init`으로만 생성되며 ignore되므로 release에 복사하면 안 됩니다.
실제 settings, handoff, run store, experiment output, paper clone, data와 `.local/` migration snapshot도
계속 ignore 상태여야 합니다.

Maintainer 개발/검증 이력은 release artifact가 아닙니다. Benchmark workspace, report, bug diary,
captured example output, 내부 validation note는 `.gitignore`에 선언된 ignored 경로에만 둡니다.

## CODEX

- `.codex/config.toml`의 `max_depth = 1`과 정확히 8개 specialist entry를 확인합니다.
- Codex orchestrator prompt, fleet row, config entry, memory seed가 없어야 합니다. Root가
  conductor-orchestrator이고 `.codex/templates/memory/conductor/`가 clean seed입니다.
- Codex fleet 3개가 같은 8개 specialist role만 포함하는지 확인합니다.
- `.codex/research/`, `.codex/memory/`, `.codex/state/handoff.json`, `.codex/runs/`, local setting이
  배포 후보에서 제외되었는지 확인합니다.
- Generated ledger를 추가하지 않고 Codex dry-run과 native audit test를 실행합니다.

## CLAUDE

- Claude lead-agent/specialist definition과 `.claude/fleets/` 3개 manifest가 일치하는지 확인합니다.
- `.claude/research/`, `.claude/agent-memory/`, `.claude/state/handoff.json`, `.claude/runs/`, local
  setting이 배포 후보에서 제외되었는지 확인합니다.
- Claude hook/script가 Claude-owned state와 integration만 참조하는지 확인합니다.
- Codex audit data를 복사하지 않고 Claude dry-run과 provider-specific gate test를 실행합니다.

Release gate는 다음을 실패 처리합니다.

- 루트에 과거 공용 `discussion.md`, `result.md`, `error.md`, `version.md`, `CODEX.md`가 존재
- provider control file이 상대 provider를 참조
- provider research 또는 memory template에 실제 연구 entry가 존재
- 실제 provider research state 또는 memory가 tracked되거나 배포 후보에 노출
- secret, credential 포함 remote, ignored test, invalid JSON, 빈 script, diff 오류

개인 checkout에서 `git add -A`를 쓰지 말고 경로를 명시해 stage하세요. 전체 staged diff와
`git diff --cached --check`를 확인하고 isolation failure가 0인지 검증하세요.
