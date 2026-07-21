# 프로젝트 경로 지도 — 실사용 프로젝트에서 유지·삭제·재작성 구분

이 템플릿 clone을 실제 AI 연구 프로젝트로 전환할 때 보는 한 장짜리 가이드입니다. 두 컨트롤
플레인(Codex·Claude)이 같은 지도를 사용하며, `./orchestrate init`이 소비하는 기계가독 원본은
`.orchestration/project_map.json`입니다 — init이 어느 백엔드에서든 이 적응 체크리스트를 자동
출력합니다.

## 1. 연구 워크스페이스 — 유지 (당신의 프로젝트 자체)

| 경로 | 용도 | 수명주기 |
|---|---|---|
| `plan/` | `PRD.md`, `CHECKLIST.md` — 사용자와 합의, orchestrator가 관리 | 개발 전용 |
| `report/` | `discussion.md`, `issue.md`, `result.md`, `version.md` — 사용자와 에이전트 팀의 문서 논의 공간 | 개발 전용 |
| `data/` | 데이터셋, 스플릿, 전처리 | 개발 전용 |
| `model/` | 모델 소스코드 | 개발·배포 |
| `experiments/` | 실험·평가 코드; 실행 기록은 `runs/` | 개발·배포 |
| `analysis/` | 결과 분석 코드·노트북·읽기 노트 | 개발·배포 |
| `functionals/` | 공식 배포 규격을 따르는 연구 함수 | 개발·배포 |
| `utils/` | 공식 배포 규격을 따르는 유틸리티 | 개발·배포 |

## 2. 오케스트레이션 코어 — 유지 (에이전트 시스템 필수)

| 경로 | 역할 |
|---|---|
| `CLAUDE.md`, `.claude/` | Claude 컨트롤 플레인: 정책·에이전트·스킬·프롬프트·훅·fleet·템플릿 |
| `AGENTS.md`, `.codex/`, `.agents/` | Codex 컨트롤 플레인 |
| `orchestrate`, `.orchestration/` | 런처, init/doctor, 격리·릴리스 검사, 경로 지도 원본 |
| `.mcp.json` | 문헌/Zotero MCP 서버 |
| `run.sh`, `evaluate.sh`, `setup.sh`, `.gitignore` | 게이트 걸린 엔트리 포인트와 위생 |

## 3. 템플릿 배포 전용 — 실사용 프로젝트에서 삭제 가능

| 경로 | 존재 이유 | 당신의 프로젝트에서는 |
|---|---|---|
| `docs/` | 템플릿 사용 가이드(이 파일 포함) | 읽은 뒤 삭제하거나 참고용으로 보관 |
| `tests/` | 템플릿 자체의 오케스트레이션 시스템 검증 | 시스템을 수정·재검증할 계획이 없으면 삭제 |
| `.github/` | 템플릿의 배포 CI | 당신 프로젝트의 CI로 교체 |

## 4. 파일은 유지, 내용은 재작성

| 파일 | 할 일 |
|---|---|
| `README.md` / `README.ko.md` | 비우고 당신 프로젝트의 README 작성 |
| `LICENSE` | 라이선스·저작권자 확정 |
| `requirements.txt` | 단일 의존성 파일 — 프로젝트 의존성으로 교체 (`tests/` 삭제 시 pytest 줄 제거) |
| `plan/PRD.md`, `plan/CHECKLIST.md` | 첫 세션에서 orchestrator와 함께 채움 |

## 에이전트 시스템의 지원

`./orchestrate init <backend>`가 트리를 이 지도와 대조해 구체적 권고(잔존 템플릿 전용 경로,
템플릿 내용이 남은 재작성 대상)를 출력합니다. 세션에서 orchestrator에게 "PROJECT_MAP 적응을
적용해줘"라고 요청하면 삭제·재작성을 확인받은 뒤 수행하며, git 작업은 항상 명시적 요청을
요구합니다.
