# Setup guide

Everything a first-time user needs to configure this orchestration system. [한국어 안내는 아래](#한국어-빠른-설정)

## TL;DR

```bash
git clone <this-repo> my-research && cd my-research
cp .claude/settings.local.json.example .claude/settings.local.json   # then fill in what you want
claude                                                               # start Claude Code
```

The **core research pipeline needs zero credentials** — hypotheses, code, experiments, gates, and
reports all work out of the box. You only add secrets to unlock optional integrations (Zotero,
Overleaf, higher literature rate limits). Add them incrementally, whenever you want the feature.

## Step 1 — copy the secrets template

```bash
cp .claude/settings.local.json.example .claude/settings.local.json
```

`.claude/settings.local.json` is **gitignored** — your real tokens never get committed. The
`.example` file (committed) holds only placeholders. Claude Code loads this file's `env` block at
session start, so restart the session after editing it.

## Step 2 — fill in the values you want (all optional, all masked)

Edit `.claude/settings.local.json`. Every value is optional; leave it as `""` to keep the feature
off. Where to get each one:

| Value | Required? | What it unlocks | Where to get it |
|---|---|---|---|
| `ZOTERO_API_KEY` | recommended | Agents search your Zotero library, read stored PDFs, save discoveries back, export BibTeX | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) → *Create new private key*. Enable **library access** (read) and **write access** (for save-back) |
| `ZOTERO_USER_ID` | with the key | your personal library | the number at the top of the same keys page |
| `ZOTERO_GROUP_ID` | for a group library | use a shared group library instead of your personal one (takes precedence) | the number in a group's URL `zotero.org/groups/<id>/…`, or ask this system to list your groups |
| `OVERLEAF_GIT_TOKEN` | for paper writing | the `writer` agent edits your LaTeX paper and syncs with Overleaf | Overleaf → Account Settings → **Git Integration** (premium feature) |
| `S2_API_KEY` | optional | higher Semantic Scholar rate limits | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) |
| `LIT_CONTACT_EMAIL` | optional | faster OpenAlex "polite pool" for literature search | just your email — no signup |
| `GITHUB_TOKEN` | optional | agents push this repo / open PRs for you | GitHub → Settings → Developer settings → Personal access tokens. Prefer a **fine-grained** token scoped to the one repo (Contents: read/write) |

Security: these live only in the gitignored file. Never paste a token into `CLAUDE.md`, an agent
spec, or any of the four research docs — those are committed. If a token was ever exposed, rotate
it at its source and update this file.

## Step 3 — verify what you configured (optional)

```bash
# Zotero: should list your collections
python3 .claude/scripts/zotero_mcp.py collections

# Literature search (needs nothing): should return real papers
python3 .claude/scripts/lit_search.py openalex "your topic" --limit 3

# Overleaf: link a paper project (repeat per project)
.claude/scripts/overleaf_sync.sh clone <project-id> docs/paper-<name>
```

Per-integration detail lives in `.claude/ZOTERO.md` and `.claude/OVERLEAF.md`.

## Step 4 — first research session

Start `claude` and describe your goal in plain language. On a fresh project the orchestrator runs
the **bootstrap** first (environment audit, dataset documentation, `VER-001`), then the pipeline.

## Usage scenarios

Concrete things to say to the system, and what happens.

**Scenario A — run an experiment.**
> "Test whether back-translation augmentation improves minority-class F1 on my dataset in `data/`."

Orchestrator → brainstorm writes a falsifiable HYP → critic reviews it (gate) → data documents the
split with a leakage checklist (gate) → developer implements → qa verifies (gate) →
experiment-tracker runs it (the mechanical gate hook confirms all three gates passed) → critic
reviews the result → writer produces a grounded report. You read `result.md` for the numbers.

**Scenario B — literature review with your Zotero library.**
> "Survey recent work on curriculum learning for EEG decoding and add the key papers to Zotero."

brainstorm searches your Zotero library first, then the open web (arXiv/OpenAlex/PubMed/S2), reads
the papers, writes RES entries in `discussion.md` + durable notes in `papers/notes/`, and saves
load-bearing discoveries back into your Zotero library tagged by hypothesis.

**Scenario C — write the paper on Overleaf.**
> "Draft the results section from EXP-003 and EXP-004 in our Overleaf paper."

writer pulls the latest from Overleaf, drafts the section with every number carrying a
`% source: EXP-NNN` provenance comment, exports BibTeX from Zotero into the `.bib`, pushes back to
Overleaf (you compile there), and the section passes critic review before it's called done.

**Scenario D — quick lookups (no agents).**
> "What does HYP-003 say?"  /  "List open bugs."

Answered directly from the docs — trivial lookups don't spin up the agent fleet.

**Scenario E — resume after days away.**
Just start a session. The SessionStart hook injects a brief: open gates, experiments still running
(or orphaned and needing adoption), and the last hand-off — so the agents pick up exactly where
they left off.

## What runs where (mental model)

- **You monitor** the four markdown docs (`discussion.md`, `result.md`, `error.md`, `version.md`) —
  human-readable, summary tables on top.
- **Agents coordinate** through `.claude/state/handoff.json` and `.claude/agent-memory/` —
  machine-readable, injected automatically. You rarely touch these.
- **Nothing sensitive is committed:** `data/`, `experiments/`, Overleaf clones, and your secrets
  are all gitignored.

Optional — session continuity across restarts: `cp .claude/state/handoff.json.example
.claude/state/handoff.json`. The live file is gitignored and holds your project's real state; the
committed `.example` is an empty schema. This is not required — the SessionStart/Stop hooks that
read it degrade gracefully (print "no hand-off yet") when the live file is absent.

---

## 한국어 빠른 설정

### 핵심

```bash
git clone <this-repo> my-research && cd my-research
cp .claude/settings.local.json.example .claude/settings.local.json   # 원하는 값만 채우기
claude
```

**핵심 연구 파이프라인은 자격증명 없이 바로 동작합니다** — 가설·코드·실험·게이트·리포트 전부.
비밀 값은 선택적 통합(Zotero, Overleaf, 문헌 API 상향)을 켤 때만, 필요한 시점에 하나씩 추가하면
됩니다.

선택 사항 — 세션 간 연속성: `cp .claude/state/handoff.json.example .claude/state/handoff.json`.
실시간 파일은 gitignore 대상이며 실제 프로젝트 상태를 담고, 커밋된 `.example`은 빈 스키마입니다.
필수는 아닙니다 — 이 파일을 읽는 SessionStart/Stop 훅은 파일이 없어도 "no hand-off yet"을 출력하며
정상적으로 동작합니다.

### 채워 넣을 값 (전부 선택, 전부 마스킹·gitignore)

`.claude/settings.local.json`을 편집합니다. 비워두면(`""`) 해당 기능은 꺼집니다. 세션 시작 시
로드되므로 편집 후 세션을 재시작하세요.

| 값 | 필요도 | 켜지는 기능 | 발급처 |
|---|---|---|---|
| `ZOTERO_API_KEY` | 권장 | 에이전트가 Zotero 라이브러리 검색·PDF 정독·발견 논문 저장·BibTeX 추출 | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) → 새 키 생성, library(read) + write(save-back용) 체크 |
| `ZOTERO_USER_ID` | 키와 함께 | 개인 라이브러리 | 같은 페이지 상단의 숫자 |
| `ZOTERO_GROUP_ID` | 그룹 사용 시 | 개인 대신 공유 그룹 라이브러리(우선순위 높음) | 그룹 URL `zotero.org/groups/<번호>`의 번호, 또는 시스템에 "내 그룹 목록 보여줘" |
| `OVERLEAF_GIT_TOKEN` | 논문 작업 시 | writer가 LaTeX 논문을 편집하고 Overleaf와 동기화 | Overleaf → Account Settings → Git Integration (premium) |
| `S2_API_KEY` | 선택 | Semantic Scholar 쿼터 상향 | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) |
| `LIT_CONTACT_EMAIL` | 선택 | OpenAlex polite pool(더 빠른 문헌 검색) | 본인 이메일 — 가입 불필요 |
| `GITHUB_TOKEN` | 선택 | 에이전트가 레포 push / PR 생성 | GitHub → Developer settings → PAT. 단일 레포 대상 fine-grained(Contents read/write) 권장 |

보안: 이 값들은 gitignore된 파일에만 존재합니다. `CLAUDE.md`·에이전트 스펙·연구 문서 4종(전부
커밋됨)에는 절대 넣지 마세요. 노출된 토큰은 발급처에서 재발급 후 이 파일만 갱신하면 됩니다.

### 사용 시나리오

- **실험 실행**: "내 데이터로 back-translation 증강이 소수 클래스 F1을 개선하는지 테스트해줘"
  → 가설 → critic 게이트 → 데이터셋 카드(누출 체크) → 구현 → qa 게이트 → 실험 → 결과 리뷰 →
  리포트. 게이트 미충족 시 실험 실행은 훅이 기계적으로 차단.
- **Zotero 문헌 조사**: "EEG 디코딩용 커리큘럼 학습 최신 연구 조사하고 핵심 논문 Zotero에 추가해줘"
  → 라이브러리 우선 검색 → 오픈 웹 → 정독 노트 → 발견 논문 Zotero 저장(가설 태그).
- **Overleaf 논문 작성**: "EXP-003, EXP-004 결과로 Overleaf 논문 results 섹션 작성해줘"
  → pull → 수치마다 `% source: EXP-NNN` → Zotero BibTeX 추출 → push → critic 리뷰.
- **빠른 조회**: "HYP-003 뭐야?" → 문서에서 즉답, 에이전트 미가동.
- **재개**: 세션만 시작하면 SessionStart 훅이 열린 게이트·실행 중 실험·마지막 인수인계를 주입.
