# AI 연구 오케스트레이션 시스템

[English](README.md) | **한국어**

[Claude Code](https://code.claude.com) 기반의 AI/ML 연구용 프로덕션급 멀티에이전트 오케스트레이션
시스템입니다. 프런티어 모델 **오케스트레이터**(Claude Fable 5, 검증된 Opus 4.8 백포트 포함)가
**Sonnet 5 전문가 에이전트** 함대를 지휘하여 연구 전체 사이클 — 가설 → 적대적 리뷰 → 데이터 →
코드 → 검증 → 실험 → 논문 — 을 수행합니다. 기계적으로 강제되는 품질 게이트, 재현성 규율,
세션 간 기억, Overleaf 협업을 갖추고 있습니다.

이 시스템의 핵심 동작은 모두 측정된 평가 배터리로 검증되었습니다(11/11 시나리오 통과 —
`.claude/prompts/orchestration-evals.md`, `.claude/ROADMAP.md` 참고).

## 왜 만들었나

멀티에이전트 연구 시스템은 예측 가능한 방식으로 실패합니다: 모호한 위임, 마감 압박에 의한
게이트 생략, 결과 날조, 테스트 데이터 누출, 잊혀지는 장시간 작업, 세션과 함께 사라지는 지식.
이 시스템은 각 실패 모드를 설계로 제거합니다:

| 실패 모드 | 대응책 (전부 구현·테스트 완료) |
|---|---|
| 모호한 위임 | 모든 디스패치에 BRIEF/RESULT/HANDOFF 계약 적용 (`.claude/prompts/result-contract.md`) |
| 마감 압박에 의한 게이트 생략 | 프롬프트 게이트 + critical 버그/블로킹 리뷰/미문서화 데이터셋 존재 시 실험 실행을 기계적으로 차단하는 `PreToolUse` 훅 |
| 수치·인용 날조 | 증거 기반 완료(✅/⚠️/❌ 라인), "받지 않은 결과는 존재하지 않는다" 원칙, 문헌 검증 도구 |
| 데이터 누출 | 6개 에이전트가 누출 책임 분담, 모든 데이터셋에 스플릿 무결성 체크리스트 게이트 |
| 유실되는 장시간 실행 | 상태 래퍼 프로토콜(`status.json` 하트비트, 세션 시작 시 고아 런 자동 입양) |
| 세션 간 기억상실 | 이중 레이어 연속성: 사람용 마크다운 문서 + 기계용 `handoff.json` + 역할별 에이전트 메모리, 세션 시작 시 자동 주입 |

## 아키텍처

```
사용자
 │
 ▼
Conductor (메인 Claude 세션)               요청 분류, 디스패치
 │
 ▼
orchestrator (model: fable)                계획, 라우팅, 게이트 강제, 종합
 │   폴백: orchestrator-opus (model: opus, Fable 5 백포트 프롬프트)
 │
 ├─► brainstorm (sonnet)          가설, 문헌                  ─┐
 ├─► critic (sonnet)              적대적 타당성 리뷰            │  격리된 컨텍스트,
 ├─► data (sonnet)                데이터셋, 스플릿, EDA         │  BRIEF로 브리핑 받고
 ├─► developer (sonnet)           모델/평가 코드               │  RESULT로 보고;
 ├─► qa (sonnet)                  테스트, 버그 격리, 게이트      │  서로 직접 호출 금지
 ├─► experiment-tracker (sonnet)  실행, 스윕, 결과 기록         │
 ├─► filemanager (sonnet)         저장소, git, 환경, 아카이브    │
 └─► writer (sonnet)              리포트, README, LaTeX 논문   ─┘
```

오케스트레이터 프롬프트는 Anthropic의 모델별 시스템 프롬프트에서 역설계했습니다: Opus 4.8
변형은 Fable 5 전용 행동 레이어(커뮤니케이션, 자율성, 심층 성찰)를 이식하고 명시적 Gate 0–8
절차를 추가했습니다. Sonnet 전문가들은 `specialist-core` 스킬로 worker 비용에 프런티어급
추론 규율을 얻습니다. 상세·출처: `.claude/prompts/README.md`.

## 요구 사항

- [Claude Code](https://code.claude.com) CLI (에이전트·스킬·훅·MCP를 전면 활용)
- Python 3.8+ (모든 도구가 표준 라이브러리만 사용 — pip 설치 불필요)
- git, 문헌 API용 인터넷 연결
- 선택: Overleaf 계정(git integration — premium) — 논문 협업용
- 선택: [Semantic Scholar API 키](https://www.semanticscholar.org/product/api) — 문헌 검색 쿼터 상향

## 빠른 시작

```bash
git clone <this-repo> my-research && cd my-research
cp .claude/settings.local.json.example .claude/settings.local.json   # 원하는 값만 채우기 (전부 선택)
claude                                                               # Claude Code 시작
```

**핵심 연구 파이프라인은 자격증명 없이 동작합니다.** 비밀 값은 선택적 통합(Zotero, Overleaf,
문헌 API 상향)을 켤 때만 하나씩 추가하면 됩니다. **전체 설정·마스크된 자격증명 가이드:
[SETUP.md](SETUP.md).**

첫 세션에서 시스템이 스스로 상황을 알려줍니다: `SessionStart` 훅이 연속성 브리핑(열린 게이트,
실행 중인 실험, 마지막 인수인계)을 주입하고 문헌·Zotero MCP 서버가 로드됩니다. 이후 연구 목표를
평범한 언어로 말하면 됩니다:

```
"back-translation 증강이 소수 클래스 F1을 개선하는지
 내 데이터셋에서 실험을 설계하고 실행해줘."
```

오케스트레이터가 이어받습니다: 부트스트랩 감사 → 가설(brainstorm) → 적대적 리뷰(critic) →
누출 체크리스트 포함 데이터셋 카드(data) → 구현(developer) → 검증(qa) → 게이트 통과 후 실험
실행(experiment-tracker) → 결과 리뷰(critic) → 리포트(writer). 사소한 조회("HYP-003 내용이
뭐야?")는 에이전트 없이 즉답합니다.

### 사용자별 입력 값 (직접 기입; 전부 선택, 전부 마스킹/gitignore)

전체 안내는 [SETUP.md](SETUP.md). 요약:

| 값 | 켜지는 기능 | 발급처 |
|---|---|---|
| `ZOTERO_API_KEY` + `ZOTERO_USER_ID` (또는 `ZOTERO_GROUP_ID`; 또는 `ZOTERO_LOCAL=1`로 로컬 Zotero 데스크톱 앱 사용, 키 불필요) | Zotero 검색·PDF 정독·save-back·BibTeX | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) — `.claude/ZOTERO.md` |
| `OVERLEAF_GIT_TOKEN` | Overleaf 논문 동기화 | Overleaf → Account Settings → Git Integration — `.claude/OVERLEAF.md` |
| `S2_API_KEY` | Semantic Scholar 쿼터 상향 | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) |
| `LIT_CONTACT_EMAIL` | OpenAlex polite pool(더 빠름) | 본인 이메일 (가입 불필요) |
| `GITHUB_TOKEN` | 에이전트가 레포 push / PR | GitHub → Developer settings → fine-grained PAT |

## 무엇을 할 수 있나

**연구 파이프라인** — 위의 기본 흐름. 모든 실험 전 3중 필수 게이트: critic의 계획 리뷰, qa의
코드 검증, data의 스플릿 문서화. 게이트는 이중으로 강제됩니다: 오케스트레이터 프롬프트 +
`.claude/hooks/experiment_gate.py`(게이트 미충족 시 `run.sh` / `evaluate.sh` /
`python models/*.py` 차단). 정당한 우회: ADR 기록(생략 규칙, 사유, 롤백 계획) 후 명령에
`GATE_OVERRIDE=ADR-NNN` 접두 — 훅이 해당 ADR의 실존을 검증합니다.

**문헌 리서치** — arXiv, OpenAlex(저널 + 톱티어 학회, 인용수, OA PDF 링크), PubMed,
Semantic Scholar를 CLI와 MCP 서버(`.mcp.json`) 양쪽으로 검색:

```bash
python3 .claude/scripts/lit_search.py openalex "EEG emotion recognition" \
    --venue "IEEE Transactions on Affective Computing" --year 2022-2026 --limit 5
```

**Zotero 라이브러리**가 일급 시민입니다(`.claude/ZOTERO.md`): 에이전트가 오픈 웹보다 먼저
사용자의 라이브러리를 검색하고, 저장된 PDF를 읽고, 중요해진 발견 논문을 가설 태그와 함께
라이브러리에 저장(write-back)하며, Overleaf 논문의 `.bib`에 BibTeX를 추출합니다. 저장 규약:
Zotero = 정본 서지 저장소, 원문 PDF는 `papers/`, 버전 전환에도 살아남는 정독 노트는
`papers/notes/`, 현재 버전의 관련성 요약은 `discussion.md`의 RES 엔트리. (ResearchGate는 공개
API가 없어 의도적으로 제외 — OpenAlex/S2가 대체합니다.)

**문헌 검색 커버리지** — 문헌 MCP(`lit_search` / `lit_fetch`, `.mcp.json`)가 실제로 도달할 수
있는 범위입니다. 각 제공처의 API/소개 페이지를 2026-07-08에 직접 확인했습니다:

| 백엔드 | 색인 범위 | 확인된 규모 |
|---|---|---|
| arXiv | 프리프린트 — 물리학, 수학, CS, 정량생물학 등 (8개 주제 분야) | 3,000,000편 이상 |
| OpenAlex | 저널·학회 proceedings·리포지터리를 아우르는 집계 색인 | 소스 282,505개에 걸친 논문 319,077,593편 |
| PubMed / MEDLINE | 생의학·생명과학 문헌 | 인용 40,830,218건; MEDLINE 색인 저널 5,200개 이상 |
| Semantic Scholar | CS·생의학 등 전 분야 논문 | 200,000,000편 이상 (제공처가 저널·소스 수를 공개하지 않음 — UNVERIFIED) |

실질적 도달 범위: 중복 제거 후 대략 **저널/학회/아카이브 약 290,000곳 이상에 걸친 고유 논문
약 3억편 이상**입니다. OpenAlex와 Semantic Scholar 둘 다 arXiv·PubMed/MEDLINE을 재색인하므로
위 표 네 행을 단순 합산하면 크게 중복 계산됩니다 — 약 3억/약 29만이라는 수치는 표의 합이 아니라
정직하게 중복 제거한 추정치입니다. 이 규모에서는 개별 저널명을 나열할 수 없으므로, 위 표는
저널 목록이 아니라 각 플랫폼이 다루는 범위의 성격을 나타냅니다.

콘텐츠 깊이: `lit_search` / `lit_fetch`는 arXiv·OpenAlex·Semantic Scholar에 대해 초록 +
메타데이터를 반환하고, PubMed 경로는 메타데이터만 반환합니다(초록 없음). 두 도구 모두 PDF를
전문(full text)으로 파싱하지 않습니다 — 전문 읽기는 사용자 라이브러리에 이미 있는 항목에 한해
별도의 Zotero 경로(`zotero_fulltext`)로만 가능하거나, PDF를 직접 `papers/`에 내려받아야 합니다.

실무상 주의점: `S2_API_KEY` 없이는 Semantic Scholar가 공용 쿼터를 공유하므로 `all` 소스
팬아웃 검색에서 `HTTP 429`가 날 수 있습니다(해결법은 위 자격증명 표 참고).

플랫폼 통계는 시간에 따라 변합니다 — 위 수치는 2026-07-08에 실시간으로 확인한 값입니다;
다른 곳에 인용하기 전에 재확인하세요.

**장시간 실험** — 약 2분을 넘는 작업은 `.claude/scripts/run_with_status.sh`로 실행되어
`status.json` 하트비트를 유지하고 세션이 죽어도 생존합니다; 다음 세션이 고아 런을 자동 감지해
입양합니다. 스윕/ablation 그리드는 병렬 sub-run + 단일 fan-in 비교 테이블
(`.claude/scripts/sweep_summary.py`)을 가진 하나의 실험으로 실행됩니다.

**Overleaf 논문 작성** — Overleaf 프로젝트를 1회 연동
(`.claude/scripts/overleaf_sync.sh clone <project-id> docs/paper-<이름>`)하면 writer 에이전트가
pull → 수치마다 출처 주석(`% source: EXP-003`)을 달아 편집 → push 하고, 사용자는 Overleaf
웹에서 실시간으로 확인·컴파일합니다. push 안전장치: 시크릿/데이터 차단, 웹 동시 편집 통합,
토큰 마스킹. 전체 가이드: `.claude/OVERLEAF.md`.

## 프로젝트 모니터링 (이중 레이어)

**사람용 레이어 — 이 마크다운 파일들을 읽으세요:**

| 파일 | 내용 |
|---|---|
| `discussion.md` | 가설(HYP), 문헌 노트(RES), 데이터셋 카드(DATASET), 리뷰(REV), 결정(ADR), 계획, 세션 상태(STATE) |
| `result.md` | 실험 기록(EXP — 설정/메트릭), 서술 리포트(REPORT) |
| `error.md` | 버그(BUG)와 타당성 이슈(VAL) — 심각도·상태 포함 |
| `version.md` | 버전 아카이브 — 단계별 압축 이력(VER) |

각 문서 상단에 요약 테이블이 있어 한눈에 상태를 파악할 수 있습니다. 단계 경계에서 작업 문서는
`version.md`로 아카이브되고 리셋됩니다(버전 게이트 문서 시스템).

**에이전트용 레이어 — 기계용, 직접 만질 일 거의 없음:**
`.claude/state/handoff.json`(구조화된 세션 인수인계 — 기록 없이 세션이 끝나려 하면 Stop 훅이
차단) + `.claude/agent-memory/<역할>/`(역할별 세션 간 교훈). SessionStart 훅이 매 세션 둘 다
주입합니다.

## 저장소 구조

```
├── CLAUDE.md                  # 시스템 헌법 — 라우팅, 게이트, 문서 포맷 (도메인에 맞게 수정)
├── README.md / README.ko.md   # 이 파일 (영어 / 한국어)
├── SETUP.md                   # 최초 설정 + 마스크된 자격증명 가이드 + 사용 시나리오
├── LICENSE                    # MIT
├── discussion.md / result.md / error.md / version.md   # 4대 연구 문서
├── .claude/
│   ├── agents/                # 에이전트 스펙 10개 (orchestrator 2변형 + 전문가 8)
│   ├── skills/                # 스킬 8개 (연구 규율 6 + orchestration + specialist-core)
│   ├── prompts/                # 오케스트레이터 프롬프트 코어, 위임 계약, 평가 시나리오
│   ├── hooks/                  # 실험 게이트, 세션 브리핑, 세션 종료 게이트
│   ├── scripts/                # lit_search, literature_mcp, zotero_mcp, overleaf_sync, run_with_status, sweep_summary
│   ├── agent-memory/            # 역할별 영속 메모리
│   ├── state/                   # handoff.json (세션 연속성)
│   ├── OVERLEAF.md              # 프로젝트별 Overleaf 연동 가이드
│   ├── ZOTERO.md                # Zotero 라이브러리 연동 가이드
│   ├── ROADMAP.md               # 평가 증거 + 단계별 고도화 계획
│   ├── settings.json            # 훅 + 권한 allowlist (커밋됨)
│   └── settings.local.json      # 개인 토큰 (gitignore; .example에서 복사)
├── .mcp.json                  # MCP 서버: literature (arXiv/OpenAlex/PubMed/S2) + zotero
├── papers/                    # 참고 PDF + notes/ (영속 정독 노트)
├── data/ · experiments/       # 데이터셋·실행 산출물 (gitignore)
├── models/ · evaluation/ · analysis/ · tests/ · docs/
└── run.sh · evaluate.sh · setup.sh · requirement.txt
```

## 시스템 검증

오케스트레이터에는 14-시나리오 평가 배터리가 동봉됩니다
(`.claude/prompts/orchestration-evals.md`): 날조 미끼, 게이트 압박 트랩, 전문가 결과 상충,
함대 크기 트랩, 프롬프트 주입 트랩 등 — 5개 기준 루브릭으로 채점. 프롬프트 코어를 변경하면
배터리를 재실행하세요 — 기록된 기준선은 11/11입니다. 로드맵·평가 증거·알려진 한계:
`.claude/ROADMAP.md`.

## 커스터마이징

1. **`CLAUDE.md`** — 도메인 규칙 추가 (프라이버시, 라이선스, 평가 기준).
2. **에이전트 스펙** (`.claude/agents/`) — 도메인 체크리스트 추가; RESULT 계약과 버전 관리
   블록은 유지.
3. **프롬프트 코어** (`.claude/prompts/`) — 정책 변경은 두 오케스트레이터 코어(간결한 Fable
   형 + 게이트형 Opus 형)에 함께 반영하고 평가 배터리 재실행 필수.
4. **파이프라인** — `setup.sh`, `run.sh`, `evaluate.sh`, `models/`, `evaluation/`을 도메인에
   맞게 구현; 30분 초과 학습 루프는 체크포인트와 `--resume-from` 필수.

## 보안·배포 참고

- 실제 토큰은 `.claude/settings.local.json`(gitignore)에만 존재. 커밋되는 `.example` 파일은
  플레이스홀더만 포함.
- `data/`, `experiments/`, `docs/paper*/`(토큰이 내장된 Overleaf 클론)는 gitignore;
  filemanager 에이전트가 커밋마다 데이터/시크릿 스테이징을 감사.
- 실험 게이트 훅은 의도적으로 보수적입니다: 게이트 미충족 상태에서는 `run.sh`를 *언급*만 하는
  명령도 차단될 수 있습니다. 이것은 기능입니다.

## 라이선스

[MIT](LICENSE) — 연구 템플릿의 표준 선택(허용적·단순). (기업 기여자를 위한 명시적 특허 조항이
필요하면 Apache-2.0이 대안입니다.)

참고: 설계 출처로 사용된 서드파티 시스템 프롬프트 모음은 이 저장소에 **포함되지 않습니다**
(gitignore 처리); 출처는 `.claude/prompts/README.md`에 기록되어 있습니다.
