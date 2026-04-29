# 12학년 학생 College List 생성기 (CAWS)

학생이 보낸 이메일 텍스트 한 번만 paste하면 → Claude Sonnet API가
1. 학생 정보를 정형 JSON으로 추출하고
2. Reach / Match / Safety × National / In-state / LAC × ED / EA 로 나눈 college list를 만들고
3. 프로필 기반 액션플랜까지 더해
4. 단정한 Word(.docx) 한 파일로 저장합니다.

---

## 1. 첫 실행 전 준비

1. **Python 3.11+** 설치 확인
   ```bash
   python --version
   ```
2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` 파일 생성
   ```bash
   cp .env.example .env
   ```
   그리고 `.env` 안에 본인의 Anthropic API key를 입력:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
   키 발급: https://console.anthropic.com/
4. (선택) Elite US College Data Sheet 경로 확인
   기본값이 `H:/My Drive/Automation-H/AntiGravity/Elite US College Data Sheet` 입니다.
   다른 위치라면 `.env`의 `ELITE_DATA_DIR`을 수정하세요.

---

## 2. 사용법

### 가장 일반적인 흐름
```bash
python generate.py
```
- 학생 이메일 텍스트를 paste 한 뒤, 빈 줄 두 번 또는 `EOF`만 적힌 줄을 입력하면 종료.
- 약 60-120초 후 `output/<학생이름>_<날짜>/<학생이름>_college_list_<날짜>.docx` 생성.

### 파일에서 읽기
```bash
python generate.py --input path/to/student_email.txt
```

### Markdown 미리보기만 (Word 파일 안 만듦, 비용↓)
```bash
python generate.py --input samples/sample_student_email_kr.txt --dry-run
```

### 특정 섹션만 재생성
```bash
python generate.py --resume "Yena Seo" --scope national
# scope 선택: national | instate | lac | ed_ea | action | all
```

---

## 3. 결과 폴더 구조
```
output/
└── Yena_Seo_2026-04-29/
    ├── student_profile.json          # 추출된 학생 데이터
    ├── raw_responses/
    │   ├── national.json             # Claude 원본 응답 (디버그/재실행용)
    │   ├── instate.json
    │   ├── lac.json
    │   └── action_plan.json
    └── Yena_Seo_college_list_2026-04-29.docx
```

---

## 4. 비용 가이드

학생 1명당 약 **$0.40 - $0.60**, 시간 약 60-120초.
Prompt caching 덕분에 `--scope` 재실행은 훨씬 저렴합니다.
호출마다 한국어로 토큰 사용량과 비용 추정이 콘솔에 표시됩니다.

---

## 5. 트러블슈팅

| 증상 | 해결 |
|---|---|
| `ANTHROPIC_API_KEY not set` | `.env` 파일 위치/내용 확인 |
| 추출 단계에서 JSON 오류 | 학생 이메일에 명확한 항목 표시(SAT, GPA 등)가 부족할 때 발생. 다시 paste 또는 `samples/sample_student_email_kr.txt` 형식 참고 |
| In-state 리스트가 50개 미달 | 정상. 주에 4년제 대학 자체가 적은 경우 가용 수만 출력 |
| 표가 페이지 밖으로 넘침 | docx를 Word에서 열고 페이지 방향을 가로로 바꿔도 됨 |

---

## 6. 모듈 개요
- `generate.py` — CLI 엔트리. 파이프라인 조율
- `src/extractor.py` — 학생 이메일 텍스트 → `student_profile.json`
- `src/grounding.py` — Elite 데이터셋 로드 & scope별 사실 큐레이션
- `src/generator.py` — Claude Sonnet API 3 scope 호출 (caching)
- `src/validator.py` — Claude 응답 vs Elite 사실 cross-check
- `src/early_decision.py` — ED / EA 섹션 분리
- `src/action_plan.py` — 개인화 로드맵
- `src/docx_builder.py` — Word 어셈블러
