# AI 연구 오케스트레이션 프롬프트 북

[English](AI_RESEARCH_PROMPTS.md) | **한국어**

자주 사용하는 AI 연구 작업을 위한 복사 가능 요청문 모음입니다. 저장소 내부 구조를 외우지 않아도
연구 범위, 역할 분리, 필요한 근거, 중단 조건, 최종 보고 형식을 구체적으로 요청할 수 있습니다.

## 사용 방법

1. `./orchestrate codex` 또는 `./orchestrate claude`로 선택 backend를 시작합니다.
2. 아래에서 목적에 맞는 요청문 하나를 복사하고 모든 `<...>`를 실제 값으로 바꿉니다.
3. 공통 계약과 선택한 backend의 계약만 포함합니다. 한 checkout에 두 provider 계약을 넣지 마세요.
4. 기간, dataset, metric, compute budget, privacy, deadline 등 실제 제약을 추가합니다.
5. 짧은 조회·설명은 agent를 spawn하지 말라고 지정하세요. 위임은 독립 검증 가치가 있을 때 사용합니다.

| 연구 목적 | 먼저 사용할 요청문 |
|---|---|
| 분야 조사·신규성 확인 | MCP 논문 리서치 |
| 아이디어를 검증 가능한 주장으로 만들기 | 아이디어와 가설 설계 |
| dataset·split 점검 | 데이터와 스플릿 설계 |
| 승인된 방법 구현 | 연구 구현 |
| 코드·연구 타당성 검토 | QA와 연구 타당성 검증 |
| 승인된 실험 실행 | 실험 실행 |
| 완료된 실행 해석 | 결과 분석 |
| 인용 정리 | Zotero 레퍼런스 관리 |
| 논문 초안·리뷰 | Overleaf 논문 작성과 리뷰 |
| 전체 제출 패키지 검토 | 논문 전체 최종 심사 |

역할 분리가 필요한 요청에는 실제 runtime ID와 계약 근거를 요구하고, 오케스트레이션 주장을 확인
없이 받아들이지 마세요.

## 모든 멀티에이전트 요청에 붙이는 공통 계약

```text
이 작업은 이 저장소의 AI research orchestration으로 수행해줘.
선택한 backend/fleet과 계획된 역할을 먼저 알려줘. 필요한 specialist를 실제 spawn하고,
선택 backend의 역할·skill·hook·research state·memory·experiment subtree·integration만 사용하고
상대 provider control plane은 읽지 마.
spawn이 반환한 agent/thread ID가 없는 작업은 위임으로 인정하지 마.
Codex에서는 root session이 유일한 conductor-orchestrator로 specialist를 직접 dispatch하고 다른
coordination layer를 만들지 마. 각 위임은 완전한 BRIEF를 사용하고, Codex에서는 exact BRIEF를
매 native spawn 전에 등록·전달해.
다음 단계는 이전 RESULT의 실제 산출물만 HANDOFF로 받아야 해.
최종 보고에 역할별 agent/thread ID, BRIEF 목적, RESULT 상태, 산출물 경로/문서 ID,
검증 명령, 미해결 gate를 요약해줘. Codex를 선택했다면 마지막에 `./orchestrate audit latest`를
실행하고 verification 판정도 인용해줘. spawn이나 hook이 실패하면 직접 수행한 것처럼 표현하지 마.
독립 읽기/감사는 병렬화하되 같은 파일 쓰기와 gate 의존 단계는 직렬화해줘.
```

## CODEX

다음 Codex 전용 계약을 추가하세요.

```text
Codex quality fleet의 root-conductor-direct topology로 수행해줘. Root Codex session이 유일한
conductor-orchestrator다. 구현 역할만 balanced를 써도 되지만 critic과 QA는 quality로 유지해줘.
`.codex/research/`와 `experiments/codex/`만 사용하고, 동시 specialist는 최대 4개, 총 dispatch
8개 전에 checkpoint해줘.
```

### Quality fleet + native audit

```text
Codex quality fleet으로 이 연구를 오케스트레이션해줘. brainstorm → critic → data → developer → qa를
의존 순서에 따라 실제 spawn해. 매 spawn 전에 exact BRIEF를 Codex audit registrar로 등록·전달하고,
각 runtime 발급 agent ID, RESULT 상태/근거, 미해결 gate를 보고해. 마지막에는
`./orchestrate audit latest`를 실행해 run ID, root 검증, specialist별 BRIEF/RESULT 판정, research gate
횟수, event-chain 상태, unverified claim 수를 포함해. 하나라도 unverified면 명시하고 완료된
오케스트레이션으로 바꾸어 표현하지 마.
```

이 prompt는 `./orchestrate codex`로 시작한 session에서만 native audit 의미가 있습니다. `codex`를
직접 실행한 session에는 project run ID가 없고, 독립 Claude system은 이 Codex ledger를 사용하지
않습니다.

## CLAUDE

다음 Claude 전용 계약을 추가하세요.

```text
이 checkout의 Claude quality fleet, agent, skill, hook, `.claude/research/`, memory,
`experiments/claude/`만 사용해. Claude-owned lead-agent routing을 따르고 반환된 모든 agent/thread
ID, BRIEF 목적, RESULT 근거, artifact, 검증 command, 미해결 gate를 보고해. Codex control file을
읽거나 Codex audit report를 이 run의 근거로 인용하지 마.
```

## 1. 전체 연구 프로젝트

```text
<연구 질문>을 이 저장소에서 종단간 연구 프로젝트로 오케스트레이션해줘.
제약은 <데이터/기간/컴퓨트/라이선스/프라이버시>, 주 메트릭은 <메트릭>, 예산은 <예산>이야.
brainstorm → critic → data → developer → qa → experiment-tracker → critic → writer 순서로
필요한 specialist를 실제 spawn해줘. 계획 REV, DATASET 누출 체크, QA 검증이 통과하기 전에는
실험하지 말고, 결과 critic 검토 전에는 논문 주장을 확정하지 마. 실패 실험과 음성 결과도 보존해줘.
각 단계의 agent/thread ID와 BRIEF/RESULT를 최종 오케스트레이션 보고에 포함해줘.
Codex를 선택했다면 native audit 최종 판정도 포함해줘.
```

## 2. MCP 논문 리서치

```text
<주제/연구 질문>의 <시작연도>-<종료연도> 선행연구를 조사해줘.
brainstorm specialist를 실제 spawn하고 Zotero library-first → literature MCP
(OpenAlex, arXiv, PubMed, Semantic Scholar) 순서로 검색해줘.
포함 기준은 <기준>, 제외 기준은 <기준>, 우선 venue는 <venue>야.
DOI/arXiv/PMID로 중복을 제거하고, 연구별 데이터·방법·베이스라인·메트릭·핵심 결과·한계를
근거표로 만들어 RES에 기록해줘. 초록 근거와 전문 근거를 구분하고, 전문 확인이 안 된 주장은
UNVERIFIED로 표시해. critic을 별도로 spawn해 인용 실재성과 종합 결론을 검토하게 해줘.
```

## 3. 아이디어와 가설 설계

```text
<문제>에 대해 서로 다른 메커니즘을 가진 연구 가설 <N>개를 설계해줘.
brainstorm을 실제 spawn해 각 HYP에 방향성 예측, 반증 조건, 데이터, 강한 베이스라인,
주/보조 메트릭, 최소 실험, 계산 예산, 누출·오염 위험, 관련 문헌을 명시하게 해줘.
그 다음 critic을 별도 spawn해 신규성, 반증 가능성, 교란요인, 평가 타당성을 비교하고
blocking REV를 작성하게 해. critic 승인 전에는 구현하지 말고, 추천안과 탈락 이유를 함께 보고해줘.
```

## 4. 데이터와 스플릿 설계

```text
HYP-<번호>를 위해 <데이터 위치/후보 데이터셋>을 감사하고 실험용 DATASET 엔트리를 설계해줘.
data specialist를 실제 spawn해 출처·버전·라이선스·해시·단위·라벨·결측·중복을 확인하고,
subject/group/time/site 기준의 누출 없는 train/validation/test split을 제안해줘.
전처리는 train에만 fit되는지, 중복/근접중복과 사전학습 오염 위험이 있는지 검사해.
critic 또는 QA가 독립적으로 split integrity를 검토하고 blocking 문제는 해결 전까지 열어둬.
```

## 5. 연구 구현

```text
승인된 HYP-<번호>, REV-<번호>, DATASET-<번호>만 근거로 최소 재현 구현을 만들어줘.
developer specialist를 실제 spawn해 베이스라인 1개와 처리군 1개의 얇은 수직 슬라이스를 구현하고,
환경·seed·config·checkpoint/resume·평가 진입점을 명시해. 무관한 리팩터링과 실험 실행은 제외해.
완료 후 qa를 별도 spawn해 테스트와 재현 명령을 독립 실행하게 하고, 실패를 숨기거나 테스트를
약화하지 마. developer와 QA의 agent/thread ID 및 RESULT를 모두 보고해줘.
```

## 6. QA와 연구 타당성 검증

```text
<코드/PR/커밋/HYP>를 읽기 전용으로 검증해줘.
qa를 실제 spawn해 단위·통합·회귀 테스트, metric 방향, seed 결정성, split 경계,
train-only preprocessing, artifact/log 출처를 확인하게 해. critic도 독립 spawn해 데이터 누출,
baseline 공정성, 통계적 오류, 과도한 일반화 가능성을 검토하게 해.
각 문제를 BUG 또는 VAL로 severity와 해결 조건까지 기록하고, 수정은 수행하지 마.
```

## 7. 실험 실행

```text
HYP-<번호>의 승인된 계획을 <컴퓨트 예산> 안에서 실행해줘.
먼저 passed critic REV, passed QA-NNN, passed DATASET 누출 감사와 열린 blocking/critical 상태를
확인하고 하나라도 미통과면 멈춰줘.
experiment-tracker를 실제 spawn하고 2분 이상 작업은 run_with_status로 실행해 명령, 환경,
코드 버전, config, seed, 로그, artifact, 상태를 EXP-<번호>에 기록해.
스윕은 하나의 EXP와 병렬 sub-run으로 관리하고, 실패/중단/음성 결과도 삭제하지 마.
완료 후 결과 critic을 별도 spawn하기 전에는 결론을 확정하지 마.
```

## 8. 결과 분석

```text
EXP-<번호들>을 분석해 <연구 질문>에 답해줘.
experiment-tracker가 로그와 표의 수치를 독립 재확인하고, critic이 별도 agent로 분석 타당성을
검토하게 해. 사전 선언 주 메트릭, 베이스라인 차이, 표본 수, 변동/신뢰구간, 실패 seed,
다중 비교, ablation을 포함해 측정 사실·해석·추측을 분리해줘.
인과나 일반화 주장은 증거 범위를 넘지 않게 하고, 불일치 수치는 평균내지 말고 원인을 추적해.
검토된 결론, 반증된 가설, 미해결 한계를 RESULT와 REPORT에 기록해줘.
```

## 9. Zotero 레퍼런스 관리

```text
<HYP/논문 섹션/주제>의 참고문헌을 Zotero MCP로 정리해줘.
brainstorm 또는 writer specialist를 실제 spawn해 기존 라이브러리를 먼저 검색하고,
각 항목의 DOI/제목/저자/연도/venue를 교차 확인해. 핵심 논문만 <HYP 태그>로 save-back하고,
전문을 읽은 논문은 선택 backend의 `papers/notes/<backend>/`에 정독 노트를 남겨줘. 중복·철회·정정
논문을 확인하고,
최종 citekey/BibTeX는 Zotero에서 내보내며 손으로 만들어내지 마. 추가/수정한 Zotero 항목과
검증되지 않은 서지를 목록으로 보고해줘.
```

## 10. Overleaf 논문 작성과 리뷰

```text
검토 완료된 <EXP/REPORT/RES ID>만 사용해 Overleaf의 <섹션>을 작성해줘.
writer를 실제 spawn해 먼저 pull하고, 모든 수치 옆에 % source: EXP-NNN 출처를 남기며,
Zotero에서 BibTeX를 동기화해. 측정하지 않은 결과나 존재를 확인하지 않은 인용은 쓰지 마.
초안 후 critic을 별도 spawn해 주장-근거 정합성, 인용 실재성, 한계, 표-본문 수치,
재현 가능성을 검토하게 해. blocking REV를 해결하기 전에는 push하거나 완료로 표시하지 마.
최종 보고에 변경 파일, 사용한 EXP/RES, critic RESULT, Overleaf sync 상태를 포함해줘.
```

## 11. 논문 전체 최종 심사

```text
이 논문을 제출 전 내부 리뷰 파이프라인으로 검증해줘. writer는 수정하지 말고 현재 초안을 고정해.
critic을 실제 spawn해 주장-근거·통계·한계·신규성을, qa를 spawn해 표/그림/본문 수치와 재현 명령을,
brainstorm을 spawn해 관련연구 누락과 경쟁 설명을 각각 독립 검토하게 해.
독립 리뷰가 끝난 뒤에만 orchestrator가 중복을 합치고 severity별 REV/BUG/VAL 목록과
필수 수정·권장 수정·반박 가능한 의견을 구분해줘. 합의되지 않은 리뷰는 숨기지 마.
```

## 짧은 작업에서는 이렇게 요청하세요

간단한 문서 조회나 단일 파일 설명은 멀티에이전트가 필요 없습니다.

```text
HYP-003의 현재 상태와 열린 blocking REV만 문서에서 조회해줘. 에이전트는 spawn하지 마.
```

비용을 제한하고 싶다면 다음을 덧붙입니다.

```text
최대 동시 specialist는 3명, 총 dispatch는 6회로 제한해. 한도에 도달하면 체크포인트를 보고하고 멈춰.
```
