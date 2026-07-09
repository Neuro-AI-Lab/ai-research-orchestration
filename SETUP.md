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

## Why `settings.json` and `settings.local.json` look different

Claude Code reads two separate settings files, and they exist for different reasons — that is
also why they don't share the same shape:

- **`.claude/settings.json`** — the project's *shared* configuration: which Bash commands and MCP
  tools the agents may call (`permissions.allow`) and the three lifecycle hooks (`PreToolUse`
  experiment gate, `SessionStart` continuity brief, `Stop` close-check). It has no `env` key —
  nothing in it is a secret, so it is committed and identical for every clone of this repo.
- **`.claude/settings.local.json`** — *your* file. Claude Code loads its `env` block as
  environment variables for every session (your Zotero key, Overleaf token, and so on). It is
  listed in `.gitignore`, so it never leaves your machine.
- **`.claude/settings.local.json.example`** — the committed placeholder for the file above: the
  same `env` shape, every real value left as `""`. You `cp` it to create your actual
  `settings.local.json` (Step 1). Each real key (e.g. `ZOTERO_API_KEY`) is paired with an
  underscore-prefixed description key (e.g. `_zotero`) that exists purely to explain the field to
  a human reader — leave those lines as-is; Claude Code loads them into the environment too, but
  an unused, string-valued environment variable is harmless.

In short: `settings.json` answers "what are agents allowed to do" (behavior — safe to share);
`settings.local.json` answers "what secrets does this session have" (identity — must stay
private). Different question, different shape.

## Step 2 — fill in the values you want (all optional, all masked)

Edit `.claude/settings.local.json`. Every value is optional; leave it as `""` to keep the feature
off. Where to get each one:

| Value | Required? | What it unlocks | Where to get it |
|---|---|---|---|
| `ZOTERO_API_KEY` | recommended | Agents search your Zotero library, read stored PDFs, save discoveries back, export BibTeX | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) → *Create new private key*. Enable **library access** (read) and **write access** (for save-back) |
| `ZOTERO_USER_ID` | with the key | your personal library | the number at the top of the same keys page |
| `ZOTERO_GROUP_ID` | for a group library | use a shared group library instead of your personal one (takes precedence) | the number in a group's URL `zotero.org/groups/<id>/…`, or ask this system to list your groups |
| `ZOTERO_LOCAL` | optional alternative to the API key | same Zotero features via the desktop app's local API — no key or user ID needed | set to `"1"`; requires Zotero desktop running on this machine (`http://localhost:23119`) |
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

## Appendix — what a worked entry cycle looks like (illustrative)

The four docs stay empty until your first research session. Below is a compact, made-up example of
one hypothesis-to-report cycle so you know what to expect once they fill in — the same bold-label,
markdown-table, `###`-subsection style described in `CLAUDE.md`'s "Document formatting standard."
**The IDs and numbers here are illustrative placeholders, not results from this project.**

`discussion.md` — brainstorm proposes a falsifiable hypothesis:
```markdown
## [HYP-001] back-translation improves minority-class F1 | 2026-01-05 | brainstorm

**Claim:** back-translation augmentation on the minority class improves its F1 by >=3 points
over the no-augmentation baseline on the same test split.
**Prediction:** minority-class F1 rises without a corresponding drop in majority-class F1.
**Falsifier:** minority F1 improvement <3 points, or majority F1 drops >1 point.

| Requirement | Details |
|:--|:--|
| Data | DATASET-001, stratified 70/15/15 split |
| Baselines | no-augmentation, random oversampling |
| Metrics | per-class F1, macro F1 |
---
```

`discussion.md` — critic reviews it before anything runs (gate):
```markdown
## [REV-001] HYP-001 review | 2026-01-05 | critic

**Target:** HYP-001   **Severity:** minor   **Status:** open

### Issues
| # | Issue | Evidence | Severity |
|:--|:--|:--|:--|
| 1 | back-translation must run before the split is frozen, not after | HYP-001 requirement table | minor |
---
```

`result.md` — experiment-tracker logs the run; writer adds the narrative:
```markdown
## [EXP-001] back-translation vs baseline | 2026-01-06 | experiment-tracker
**Hypothesis:** HYP-001   **Dataset:** DATASET-001

### Results
| Metric | Baseline | Back-translation |
|:--|:--|:--|
| Minority F1 | 0.61 | 0.68 |
| Macro F1 | 0.74 | 0.76 |
---

## [REPORT-2026-01-06] back-translation result | writer
**Covers:** EXP-001   **Hypothesis:** HYP-001

### Summary
Back-translation raised minority-class F1 by 7 points over the baseline on a single run
(DATASET-001), consistent with HYP-001's >=3-point threshold; no seed variance has been measured
yet.

### Assessment
- **Consistent with:** HYP-001
- **Open:** single-seed result — statistical significance not yet established
---
```

That is the shape every real entry follows. You will not need to write these yourself — the agents
produce them; this appendix exists only so a first-time reader recognizes the format on sight.

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

### settings.json과 settings.local.json이 다른 이유

Claude Code는 설정 파일을 두 개 따로 읽으며, 존재 이유가 다르기 때문에 형식도 다릅니다.

- **`.claude/settings.json`** — 프로젝트의 *공용* 설정: 에이전트가 호출할 수 있는 Bash 명령·MCP
  도구 목록(`permissions.allow`)과 3개의 생명주기 훅(`PreToolUse` 실험 게이트, `SessionStart`
  연속성 브리핑, `Stop` 종료 점검). `env` 키가 없습니다 — 비밀 값이 전혀 없으므로 커밋되고, 이
  저장소를 클론한 모든 사람에게 동일하게 적용됩니다.
- **`.claude/settings.local.json`** — *개인* 파일. Claude Code가 매 세션 이 파일의 `env` 블록을
  환경 변수로 로드합니다(Zotero 키, Overleaf 토큰 등). `.gitignore`에 등록되어 있어 절대
  커밋되지 않습니다.
- **`.claude/settings.local.json.example`** — 위 파일의 커밋되는 플레이스홀더: 형태는 동일하고
  실제 값만 전부 `""`로 비어 있습니다. 이를 복사해(Step 1) 실제 `settings.local.json`을
  만듭니다. 실제 키(예: `ZOTERO_API_KEY`)마다 밑줄로 시작하는 설명용 키(예: `_zotero`)가 짝을
  이루는데, 이는 사람이 읽기 위한 주석일 뿐입니다 — 그대로 두세요; Claude Code가 이것도 함께
  로드하지만, 사용되지 않는 문자열 환경 변수라 문제되지 않습니다.

요약: `settings.json`은 "에이전트가 무엇을 해도 되는가"(행동 규칙 — 공유해도 안전)에 대한
답이고, `settings.local.json`은 "이 세션이 어떤 비밀을 갖고 있는가"(개인 정보 — 반드시 비공개)
에 대한 답입니다. 질문이 다르니 형식도 다릅니다.

### 채워 넣을 값 (전부 선택, 전부 마스킹·gitignore)

`.claude/settings.local.json`을 편집합니다. 비워두면(`""`) 해당 기능은 꺼집니다. 세션 시작 시
로드되므로 편집 후 세션을 재시작하세요.

| 값 | 필요도 | 켜지는 기능 | 발급처 |
|---|---|---|---|
| `ZOTERO_API_KEY` | 권장 | 에이전트가 Zotero 라이브러리 검색·PDF 정독·발견 논문 저장·BibTeX 추출 | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) → 새 키 생성, library(read) + write(save-back용) 체크 |
| `ZOTERO_USER_ID` | 키와 함께 | 개인 라이브러리 | 같은 페이지 상단의 숫자 |
| `ZOTERO_GROUP_ID` | 그룹 사용 시 | 개인 대신 공유 그룹 라이브러리(우선순위 높음) | 그룹 URL `zotero.org/groups/<번호>`의 번호, 또는 시스템에 "내 그룹 목록 보여줘" |
| `ZOTERO_LOCAL` | API 키 대안(선택) | 키·사용자 ID 없이 데스크톱 앱의 로컬 API로 동일 기능 사용 | `"1"`로 설정 — 이 기기에서 Zotero 데스크톱 실행 필요 (`http://localhost:23119`) |
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

문서에 예시로 채워진 항목이 실제로 어떤 모양인지(HYP → REV → EXP → REPORT 한 사이클)는 영어
섹션의 [Appendix](#appendix--what-a-worked-entry-cycle-looks-like-illustrative)를 참고하세요.
