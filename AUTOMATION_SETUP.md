# 설문 → 자동 리포트 이메일 설정 가이드 (GitHub Actions)

Google Forms 응답 시트에 새 행이 들어오면 GitHub Actions가 30분마다(또는 즉시) 확인해서
영어·한글 Word 리포트 2개를 만들고 `andy.lee@eliteprep.com`으로 첨부 발송합니다.

```
Google Form 응답 시트 ──▶ GitHub Actions (automation/survey_worker.py)
                              │  1. 미처리 행 읽기
                              │  2. 답변을 텍스트로 합쳐 파이프라인 실행 (Claude)
                              │  3. EN + KR .docx 생성
                              │  4. Gmail SMTP로 첨부 발송
                              └▶ 시트 "Report Status" 열에 SENT/ERROR 기록
```

한 번만 설정하면 됩니다. 아래 4단계 모두 브라우저에서 진행하며 약 20분 걸립니다.

---

## 1단계. Google 서비스 계정 만들기 (시트 읽기/쓰기용)

1. https://console.cloud.google.com 접속 → `andy.lee@eliteprep.com` 로그인
2. 상단 프로젝트 선택 → **새 프로젝트** → 이름 `caws-survey-worker` → 만들기
3. 왼쪽 메뉴 **API 및 서비스 → 라이브러리** → `Google Sheets API` 검색 → **사용**
4. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → 서비스 계정**
   - 이름: `survey-worker` → 만들기 → (역할은 건너뛰어도 됨) → 완료
5. 만들어진 서비스 계정 클릭 → **키** 탭 → **키 추가 → 새 키 만들기 → JSON** → 다운로드
   - 이 JSON 파일 내용 전체가 3단계의 `GOOGLE_SERVICE_ACCOUNT_JSON` 입니다.
6. 서비스 계정 이메일(`survey-worker@caws-survey-worker.iam.gserviceaccount.com` 형태)을 복사
7. **응답 시트 열기 → 공유 → 이 이메일을 편집자로 추가** (알림 보내기 체크 해제)

> Google Workspace 관리자가 "외부 공유"를 막아 둔 경우 서비스 계정 공유가 거부될 수 있습니다.
> 그때는 관리자 콘솔에서 서비스 계정 도메인(`iam.gserviceaccount.com`)을 허용해야 합니다.

## 2단계. Gmail 앱 비밀번호 만들기 (발송용)

1. https://myaccount.google.com/security → `andy.lee@eliteprep.com` 로그인
2. **2단계 인증**이 꺼져 있으면 먼저 켭니다.
3. https://myaccount.google.com/apppasswords → 앱 이름 `caws-worker` → **만들기**
4. 표시되는 **16자리 비밀번호**를 복사 (공백 제거). 이것이 `GMAIL_APP_PASSWORD` 입니다.

> "앱 비밀번호" 메뉴가 안 보이면 Workspace 관리자가 막아 둔 것입니다.
> 관리자 콘솔 → 보안 → 2단계 인증에서 허용하거나, 다른 Gmail 계정을 발신자로 써야 합니다.

## 3단계. GitHub Secrets 등록

https://github.com/andyeunholee/caws-college-list-04292026/settings/secrets/actions

**Secrets** 탭 → New repository secret (4개):

| 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | `.env`에 있는 `sk-ant-...` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | 1단계에서 받은 JSON 파일 내용 전체 (`{` 부터 `}` 까지) |
| `GMAIL_USER` | `andy.lee@eliteprep.com` |
| `GMAIL_APP_PASSWORD` | 2단계의 16자리 |

**Variables** 탭 (선택 — 기본값이 이미 workflow에 들어 있어 바꾸고 싶을 때만):

| 이름 | 기본값 | 의미 |
|---|---|---|
| `REPORT_RECIPIENTS` | `andy.lee@eliteprep.com` | 쉼표로 여러 명 가능 |
| `SHEET_ID` / `SHEET_GID` | 현재 시트 | 시트를 바꿀 때 |
| `DISABLE_GROUNDING` | `1` | `0`이면 Elite 데이터셋 사용 |
| `RESEARCH_MODEL` | (비어 있음) | `claude-opus-4-7` 등 |
| `MAX_ROWS_PER_RUN` | `3` | 한 번에 처리할 최대 응답 수 |

## 4단계. 첫 실행 테스트

1. GitHub → **Actions** 탭 → "Survey → College List Report" → **Run workflow** → Run
2. 2–5분 후 실행 로그 확인. 시트에 `Report Status` 열이 생기고 처리된 행에 `SENT 2026-08-24 …`가 찍히면 성공.
3. `andy.lee@eliteprep.com` 받은편지함에 `[CAWS] College List Report — <학생명>` 메일이 와 있는지 확인.

> 기존 응답이 많다면 첫 실행에서 최대 3개만 처리하고, 30분마다 3개씩 이어서 처리합니다.
> 이미 처리한 옛 응답을 건너뛰고 싶으면 그 행들의 `Report Status` 칸에 미리 `SENT (skip)` 이라고 적어 두세요.

---

## (선택) 즉시 실행 — Apps Script 트리거

30분 대기가 길면 폼 제출 즉시 실행되게 할 수 있습니다.
`automation/apps_script.gs` 파일 상단의 안내대로 설정하세요 (GitHub PAT 1개 필요).

## 동작 규칙

- 처리 상태는 시트의 `Report Status` 열에 기록됩니다: `PROCESSING` → `SENT` / `ERROR …` / `SKIPPED`
- `SENT`로 시작하지 않는 행은 다음 실행 때 다시 시도합니다 (ERROR 자동 재시도).
- 같은 행이 두 번 발송되는 일은 없습니다 (`concurrency` + 상태 열).
- 학생에게는 보내지 않습니다. 수신자는 `REPORT_RECIPIENTS`에 적힌 주소뿐입니다.
- 비용: 응답 1건당 Claude 약 $0.5–1. GitHub Actions는 무료 한도(월 2,000분) 내에서 동작합니다
  (30분 간격 확인 ≈ 월 700분, 리포트 생성 1건당 약 4–5분 추가).

## 문제 해결

| 증상 | 원인 / 조치 |
|---|---|
| `Missing required environment variable` | 3단계 Secret 이름 오타 |
| `PERMISSION_DENIED` / `SpreadsheetNotFound` | 1-7단계 시트 공유 누락, 또는 SHEET_ID 오류 |
| `Username and Password not accepted` | 앱 비밀번호 오류. 2단계 다시 발급 |
| 상태 열에 `ERROR … RuntimeError: Student profile extraction failed` | 응답 내용이 너무 빈약. 폼 항목(이름, 학교, 주, GPA, SAT 등) 확인 |
| 메일은 왔는데 첨부가 없음 | Actions 로그의 "Upload generated reports" 아티팩트 확인 후 문의 |
