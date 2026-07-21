# Maintainer와 release 가이드

[English](MAINTAINERS.md) | **한국어** | [프로젝트 개요](../../README.ko.md)

소스 배포판의 contribution, validation, release 규칙을 통합한 문서입니다. Backend를 사용하는
연구자는 [Codex](CODEX.ko.md) 또는 [Claude](CLAUDE.ko.md) 가이드를 사용하세요.

## 배포 경계

Tracked source에는 provider 정책, role spec, clean template, hook, script, skill, launcher, test,
`docs/orchestration/`의 통합 문서가 포함됩니다.

다음 live/local 자료는 배포하지 않습니다.

- provider research state, memory, handoff, setting, run ledger;
- dataset, 생성된 run·analysis output, checkpoint, paper clone, reading note;
- credential, credential 포함 Git remote, transcript, benchmark workspace, bug diary, maintainer
  validation report.

상세 문서 directory는 하나의 단위로 구성됩니다. Guide를 별도로 제공하는 consumer project는
`/docs/orchestration/` 전체를 제외할 수 있습니다. `.gitignore`는 template clone에서 이미 commit된
file을 untrack하지 않는다는 점에 주의하세요.

## Provider ownership

소스 배포판에는 두 provider가 모두 있지만 runtime control surface는 독립적으로 유지합니다.

| Surface | Codex | Claude Code |
|---|---|---|
| 진입 정책 | `AGENTS.md` | `CLAUDE.md` |
| runtime file | `.codex/`, `.agents/skills/` | `.claude/`, `.mcp.json` |
| live plan/state | `.codex/research/` | `plan/`, `report/` |
| 생성 artifact | `experiments/codex/`, `analysis/codex/` | `experiments/runs/`, `analysis/` |
| 사용자 가이드 | `docs/orchestration/CODEX*` | `docs/orchestration/CLAUDE*` |

한 provider의 role, prompt, hook, state, memory, setting, audit claim을 다른 provider에 import하지
마세요. Shared project code와 data는 shared control plane이 아닙니다. Launcher는 non-default
backend 명시 실행을 경고 후 허용할 수 있지만, provider 비교와 release 검증은 별도 clean
checkout을 사용합니다.

## 문서 정책

- Root README에는 목적, provider 선택, quick start, evidence 경계, link만 둡니다.
- Provider-specific setup, workflow, prompt, integration, security, limitation은 해당 provider의
  단일 통합 가이드에 둡니다.
- Contributor와 release 절차는 이 maintainer 가이드에만 둡니다.
- 영문과 한국어 문서를 함께 수정합니다.
- 의도한 설계가 아니라 shipped code와 관찰된 runtime 동작을 설명합니다.
- 사용자 문서에 개발 이력, local run ID, transcript, benchmark 결과를 넣지 않습니다.
- 외부 service 의존성과 미검증 runtime 동작을 명시합니다.

## 필수 검증

Clean 후보에서 실행합니다.

```bash
python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate release-check
git diff --check
```

정적 검사는 필요하지만 충분하지 않습니다. Release 전 설치된 provider CLI로 black-box session을
실행합니다.

1. 초기화 후 `doctor` 실행;
2. `quality`, `balanced`, `fast` preset의 resolution/dry-run 확인;
3. 실제 specialist 하나를 spawn해 runtime ID, 요청 role/model, BRIEF, RESULT 확인;
4. 여러 normal turn에서 turn Stop을 session close로 반복 처리하지 않는지 확인;
5. direct gated command와 문서화된 long-run wrapper path 실행;
6. literature MCP discovery 확인, 미설정 Zotero/Overleaf는 passed가 아니라 unavailable로 보고;
7. role, BRIEF, RESULT, identity 누락 시 audit/runtime report가 fail-closed인지 확인.

`doctor` 또는 `release-check` failure가 0이라는 이유만으로 ready라고 설명하면 안 됩니다.
Black-box 결과가 문서와 일치해야 합니다.

## Clean release 절차

활성 연구 checkout이 아니라 전용 worktree를 사용합니다.

```bash
git worktree add ../orchestration-release -b release/<version>
cd ../orchestration-release
```

두 provider의 clean research·memory template을 검사합니다. Live setting, state, run, experiment,
paper clone, local evaluation history가 배포 후보에 없는지 확인합니다. 전체 검사를 실행하고 전체
diff를 검토하며 `git add -A` 대신 대상 path만 명시적으로 stage합니다.

Release gate는 다음을 거부해야 합니다.

- repository root의 legacy shared research-control 문서;
- cross-provider runtime reference;
- clean template의 실제 research entry;
- tracked live state, memory, setting, run, experiment, credential;
- missing provider role, malformed setting, broken documentation link, empty script, diff error;
- real session으로 확인되지 않은 runtime verification을 주장하는 public 문서.

## 변경 규율

- 무관한 dirty work를 보존하고 겹치는 변경은 편집 전에 검사합니다.
- Hook 변경에는 provider-specific unit test와 실제 lifecycle test가 필요합니다.
- Fleet·agent 변경에는 config parsing뿐 아니라 실제 routing smoke test가 필요합니다.
- Experiment 변경에는 leakage, provenance, failure, wrapper path test가 필요합니다.
- 문서 변경에는 link 검사, 영문/한국어 대응, release-check 갱신이 필요합니다.

## Git과 외부 action 권한

Task에 필요한 status, diff, log, show, remote metadata 읽기는 허용됩니다. Index, working tree,
ref, history 또는 remote를 바꾸는 Git action에는 사용자 명시 승인이 필요합니다.

사용자 명시 요청 없이 agent는 다음을 수행하면 안 됩니다.

- file stage·unstage;
- branch 생성·이름 변경·삭제·전환;
- commit 생성·amend·squash 또는 history rewrite;
- fetch, pull, push, force-push;
- PR 생성·수정·close·approve;
- merge, rebase, cherry-pick, stash, reset, restore, tag, release publish;
- index, working tree, ref, history 또는 remote를 바꾸는 그 밖의 Git command.

구현, 수정, test, 문서화, review, release 준비, deployable 상태 요청은 위 작업의 권한을 뜻하지
않습니다. 한 작업 승인은 다른 작업 승인으로 확대되지 않습니다. 예를 들어 commit 승인은 push나
PR 생성 승인이 아닙니다.

명시 승인을 받은 경우 `type/N-kebab-scope`처럼 제한된 branch를 사용하고 의도한 path만 stage하며
정확한 명령과 결과 ID를 보고합니다. Git remote URL에 credential을 넣거나 issue/PR에 private 연구
자료를 노출하면 안 됩니다.
