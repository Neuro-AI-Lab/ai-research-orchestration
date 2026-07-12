# 호환성

[English](COMPATIBILITY.md) | **한국어**

설치 전 요구 조건을 확인하거나 doctor가 capability 누락을 보고할 때 보는 문서입니다. 고정된 과거
CLI version 번호가 아니라 현재 설치된 CLI의 실제 기능을 기준으로 호환성을 판단합니다. Launcher는
지원하지 않는 fleet 설정을 임의로 대체하지 않고 명확하게 실패합니다.

## 배포 환경 요약

| 환경 | 안내 |
|---|---|
| Linux | 주 배포 대상 |
| macOS | 호환되는 Python, Git, shell, process tool 필요 |
| Windows | WSL2 또는 Linux container/VM 사용 |
| Offline core 사용 | 외부 인증 호출이 없는 초기화·진단, test, demo는 로컬 실행 |
| 외부 integration | literature, Zotero, Overleaf는 해당 network/service 접근 필요 |

Provider별 별도 checkout을 사용하세요. 초기화 후 `./orchestrate doctor <backend>`가 현재 환경의
기준 진단이며, 이어서 `--dry-run`으로 실제 해석된 launch command를 볼 수 있습니다.

## 공통 요구 조건

| 구성 요소 | 요구 조건 |
|---|---|
| Python | orchestration core 3.8+, maintainer는 3.11 권장 |
| Git | 필수 |
| Shell | POSIX 호환; Windows는 WSL2 또는 Linux container/VM |
| Process tool | 장기 실행 격리를 위해 `setsid` 권장 |
| Network | 선택 literature/Zotero/Overleaf 작업에만 outbound HTTPS |
| Test | `requirements-dev.txt`가 pytest 도구 설치 |

Overleaf Git 접근은 사용자 account와 plan에 의존합니다.

## CODEX

설치된 Codex CLI는 native `multi_agent`, `hooks` feature와 선택 fleet의 모든 model/effort 조합을
포함하는 bundled model catalog를 제공해야 합니다. Launch preflight는 이를 검사하며 model을
조용히 대체하지 않고 실패합니다.

Codex native audit에는 root session identity, specialist `agent_id`/role, 종료 specialist의 last
message가 포함된 lifecycle hook payload가 필요합니다. Field가 없다면 대체 값을 만들 수 없으므로
run은 unverified로 남습니다.

```bash
codex --version
./orchestrate init codex
./orchestrate doctor codex
./orchestrate codex --dry-run
```

## CLAUDE

설치된 Claude Code CLI는 project agent, hook, skill, MCP 설정, `.claude/fleets/`의 model alias,
non-quality preset/override용 programmatic agent overlay를 지원해야 합니다. Fleet 검증은 지원하지
않는 alias·effort 또는 research-gate floor보다 낮은 row를 거부합니다.

```bash
claude --version
./orchestrate init claude
./orchestrate doctor claude
./orchestrate claude --dry-run
```

## Maintainer check

```bash
python3 .orchestration/isolation.py
python3 .orchestration/validate_system.py
python3 -m pytest tests/orchestration -q
./orchestrate release-check
```
