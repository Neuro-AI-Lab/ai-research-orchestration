# 프로젝트 경로 지도 — 유지·삭제·재작성

[English](PROJECT_MAP.md) | [프로젝트 개요](../../README.ko.md)

Dual-provider 배포판을 실제 AI 연구 프로젝트 하나로 전환할 때 사용하는 권위 있는 사람용
inventory입니다. `.orchestration/project_map.json`이 `./orchestrate init`과
`./orchestrate adapt`가 읽는 기계가독 원본이며, release check는 모든 tracked path가 이 지도에
포함되는지 검증합니다.

## 1. 적응 결정

Checkout마다 provider 하나만 선택합니다. 초기화 후 선택 provider의 control plane은 유지하고
미선택 provider는 제거합니다. 연구 workspace는 유지합니다. Template maintainer asset은 검토 후
보통 제거하며, project-owned file은 템플릿 정체성을 그대로 두지 말고 재작성합니다.

```bash
./orchestrate init codex            # 또는: claude
./orchestrate adapt codex           # 권고 text만 출력; 변경 없음
./orchestrate adapt codex --json    # 기계가독 권고 report
```

Advisor는 삭제·truncate·재작성을 수행하지 않습니다. 승인한 subset만 선택 provider의 root
orchestrator에게 적용하도록 요청하세요. 삭제, license 선택, Git 작업에는 명시적 사용자 지시가
필요합니다.

## 2. 연구 workspace — 유지

| Tracked 경로 | 용도 | 첫 project 작업 |
|---|---|---|
| `plan/PRD.md`, `plan/CHECKLIST.md` | 사용자 승인 scope와 evidence-linked workflow | `<project name>`을 바꾸고 root orchestrator와 작성 |
| `report/{discussion,issue,result,version}.md` | live 4-document 연구 기록 | clean seed를 유지하고 typed project entry만 append |
| `data/.gitkeep` | dataset, manifest, split, dataset-specific preprocessing | 실제 content가 생기면 `.gitkeep` 제거; license/privacy/size 정책 적용 |
| `model/.gitkeep` | model source | project code로 교체 |
| `experiments/.gitkeep` | experiment code/config; 생성 run은 ignored `runs/` 아래 | project code로 교체 |
| `analysis/.gitkeep` | EDA와 result-analysis code/artifact | project content로 교체 |
| `functionals/.gitkeep`, `utils/.gitkeep` | 재사용 연구 함수와 일반 helper | project code로 교체 |
| `run.sh`, `evaluate.sh` | gated training/evaluation entrypoint | fail-closed placeholder 교체 |

`plan/`, `report/`, `data/`는 의도적으로 ignore하지 않습니다. Project의 privacy, license, size,
collaboration 정책이 허용하는 data와 연구 기록만 commit합니다.

## 3. 선택 provider orchestration core — 하나만 유지

| 선택 | 유지 | Init 후 제거 |
|---|---|---|
| Codex | `AGENTS.md`, `.codex/**`, `.agents/**` | `CLAUDE.md`, `.claude/**`, `.mcp.json` |
| Claude | `CLAUDE.md`, `.claude/**`, `.mcp.json` | `AGENTS.md`, `.codex/**`, `.agents/**` |

Codex inventory: `.codex/{ORCHESTRATION.md,config.toml}`, BRIEF/RESULT contract, 8-role fleet 세 개,
role prompt 여덟 개, hook 다섯 개, integration/audit script 일곱 개, settings/handoff example,
plan/report/memory template, 모든 `.agents/skills/**` 절차입니다.

Claude inventory: `.claude/agents/*.md` 열 개, fleet manifest 세 개와 README, hook 네 개, prompt
다섯 개, script 일곱 개, provider settings/state example, skill 여덟 개, plan/report/memory
template입니다. `.mcp.json`은 Claude MCP 등록입니다.

두 provider의 role, instruction, state, memory, hook, run ledger를 섞지 마세요. 비교에는 별도
clone/worktree를 사용합니다.

## 4. Shared orchestration runtime — agent 사용 중 유지

| 경로 | 역할 |
|---|---|
| `orchestrate` | provider-bound init, adapt, doctor, launch, audit, run-list entrypoint |
| `.orchestration/launcher.py` | preset/permission 해석, provider lock, adaptation advisor, process lifecycle |
| `.orchestration/isolation.py` | doctor가 사용하는 선택-provider isolation 검사 |
| `.orchestration/config.local.json.example` | ignored local launcher preference의 schema seed |
| `.orchestration/project_map.json` | 이 inventory의 기계 원본; adaptation 완료 후 선택적으로 제거 가능 |

## 5. Template 배포 전용 — 검토 후 제거

| Tracked 경로 | 배포 이유 | 실제 project 작업 |
|---|---|---|
| `docs/orchestration/{CODEX,CLAUDE,MAINTAINERS,PROJECT_MAP}{,.ko}.md` | distribution/user/maintainer 문서 | 먼저 읽고 `docs/` 제거 또는 참고용 유지 |
| `tests/{__init__.py,orchestration/**}` | dual-provider template 자체 test | orchestration system을 유지·수정하지 않으면 제거 |
| `.github/workflows/validate.yml` | template distribution CI | project CI로 교체 |
| `.orchestration/release_check.py`, `.orchestration/validate_system.py` | dual-provider release 검증 | template test와 함께 제거하거나 control plane 수정 시 유지 |
| `setup.sh` | 최초 init 편의 wrapper | `./orchestrate init` 후 선택 사항 |

미선택 provider를 제거하면 dual-provider `release-check`는 더 이상 적용되지 않습니다. 선택
provider의 `doctor`는 runtime 검사로 계속 사용할 수 있습니다.

## 6. 파일은 유지하고 내용은 재작성 또는 truncate

| 파일 | 필요한 결정 |
|---|---|
| `README.md`, `README.ko.md` | template 개요를 project README로 교체; 사용하지 않는 언어본은 삭제 |
| `LICENSE` | project license와 copyright holder 선택; agent가 추론하면 안 됨 |
| `requirements.txt` | 단일 dependency file을 유지하고 template-test dependency를 project dependency로 교체 |
| `.gitignore` | data, checkpoint, generated run, paper, local state, secret 규칙 검토 |
| `plan/PRD.md`, `plan/CHECKLIST.md` | 사용자 승인 scope와 acceptance criterion으로 작성 |
| `run.sh`, `evaluate.sh` | research gate를 보존하며 재현 가능한 project entrypoint 구현 |

의도적으로 `requirements-dev.txt`는 없습니다. 실제 project가 재작성하기 전까지 validation과
project dependency는 하나의 `requirements.txt`를 사용합니다.

## 7. 전체 tracked inventory와 coverage 규칙

다음 pattern이 `git ls-files`가 반환하는 모든 경로를 분류합니다(adapt file은 기능 category에도
동시에 속할 수 있습니다).

| Category | 전체 경로 pattern |
|---|---|
| 연구 workspace | `plan/**`, `report/**`, `data/**`, `model/**`, `experiments/**`, `analysis/**`, `functionals/**`, `utils/**`, `run.sh`, `evaluate.sh` |
| Codex core | `AGENTS.md`, `.codex/**`, `.agents/**` |
| Claude core | `CLAUDE.md`, `.claude/**`, `.mcp.json` |
| shared runtime/adaptation | `orchestrate`, `.orchestration/{launcher,isolation,project_map}.py`(해당 확장자 기준), `.orchestration/config.local.json.example` |
| distribution validation | `tests/**`, `.github/**`, `docs/**`, `.orchestration/{release_check,validate_system}.py`, `setup.sh` |
| project-owned rewrite | `README.md`, `README.ko.md`, `LICENSE`, `requirements.txt`, `.gitignore` |

실제 shared literal 경로는 `.orchestration/launcher.py`, `.orchestration/isolation.py`,
`.orchestration/project_map.json`입니다. 위 brace 표기는 서로 다른 확장자를 읽기 쉽게 묶은
표현일 뿐입니다. Tracked file이 분류되지 않거나, workspace 경로가 ignore되거나, 영·한 guide
구조가 달라지거나, 두 번째 requirements file이 생기면 release validation이 실패합니다.

## 8. 안전한 adaptation workflow

1. `./orchestrate adapt <selected-provider> --json`을 실행해 모든 제안 경로를 검토합니다.
2. Provider 제거, template docs/test/CI 제거, license, README 언어, dependency, data/privacy 정책을
   사용자와 결정합니다.
3. 선택 provider의 root orchestrator에게 승인된 subset만 적용하도록 요청합니다.
4. `./orchestrate doctor <selected-provider>`와 project test를 실행합니다.
5. Branch, commit, push, PR 작업은 사용자가 각 class를 명시적으로 요청한 경우에만 수행합니다.
