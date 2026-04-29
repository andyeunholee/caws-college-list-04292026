# 배포 가이드 — Streamlit Cloud (private repo)

## 0. 로컬 동작 확인 (이미 완료된 단계)
```bash
pip install -r requirements.txt
streamlit run app.py
# → http://localhost:8501 에서 GUI 확인
```

---

## 1. Elite 데이터셋을 repo 안으로 이동

현재 `H:/My Drive/Automation-H/AntiGravity/Elite US College Data Sheet` 에 있는 데이터셋은
프로젝트 폴더 **밖**에 있어서, GitHub에 push하면 클라우드 서버는 접근하지 못합니다.

repo 안에 `data/elite/` 폴더를 만들고 데이터셋을 복사:

```bash
# repo 루트에서
mkdir -p data/elite
cp -r "H:/My Drive/Automation-H/AntiGravity/Elite US College Data Sheet/." data/elite/
```

그리고 로컬 `.env` 의 `ELITE_DATA_DIR`을 상대 경로로 바꿉니다:
```
ELITE_DATA_DIR=data/elite
```
(로컬에서도 동일하게 동작하는지 한 번 더 `streamlit run app.py` 로 확인하세요.)

---

## 2. GitHub 비공개 repo 생성 + push

```bash
# 1) GitHub 웹 또는 gh CLI 로 private repo 생성
gh repo create caws-college-list --private --source=. --remote=origin

# 또는 수동으로:
git init
git add .
git commit -m "feat: streamlit web GUI for CAWS"
git remote add origin git@github.com:<your-username>/caws-college-list.git
git push -u origin main
```

`.env`, `output/`, `~$*.docx` 는 `.gitignore` 로 이미 제외되어 있으니 커밋되지 않습니다.

---

## 3. Streamlit Community Cloud 에 연결

1. https://share.streamlit.io 접속 → GitHub 계정 로그인
2. **New app** → 비공개 repo 선택 (Streamlit Cloud는 무료 플랜에서 private repo 지원)
3. Branch: `main`, Main file path: `app.py`
4. **Advanced settings → Secrets** 에 다음 입력:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-api03-..."
   ELITE_DATA_DIR = "data/elite"
   ```
5. **Deploy** 클릭. 1-2분 후 빌드가 끝나면
   `https://<your-app>.streamlit.app` 형태의 public URL이 발급됩니다.

---

## 4. 본인 웹사이트에 연결

발급된 URL을 그대로 버튼/링크로 걸면 됩니다.

```html
<!-- 새 탭으로 열기 -->
<a href="https://your-app.streamlit.app" target="_blank" rel="noopener"
   style="display:inline-block;padding:12px 24px;background:#FF4B4B;color:white;
          border-radius:8px;text-decoration:none;font-weight:600;">
  📋 College List 생성하기
</a>

<!-- 또는 iframe 임베드 (헤더 보존이 안 될 수 있음) -->
<iframe src="https://your-app.streamlit.app/?embedded=true"
        width="100%" height="900" style="border:0"></iframe>
```

`?embedded=true` 쿼리 파라미터를 붙이면 Streamlit 메뉴/햄버거가 숨겨져서 임베드용으로 깔끔합니다.

---

## 5. 운영 팁

| 상황 | 해결 |
|---|---|
| 앱이 자주 sleep 모드로 들어감 | 무료 플랜은 비활성 시 sleep. 첫 방문자가 깨우는 데 30초쯤 걸림. 트래픽 많으면 유료 전환 고려 |
| API key 노출 위험 | secrets.toml은 절대 커밋 금지 (`.gitignore`에 이미 있음). Streamlit Cloud secrets UI 만 사용 |
| Elite 데이터 업데이트 | repo에 commit & push 하면 자동 재배포 |
| 비용 모니터링 | 학생 1명당 약 $0.40-$0.60. 외부 공개 시 rate limiting 또는 비밀번호 게이트 추가 권장 |

---

## 6. (옵션) 비밀번호 게이트 추가

URL을 아무나 사용하지 못하게 하려면 `app.py` 상단에 간단한 패스워드 게이트:

```python
if "auth_ok" not in st.session_state:
    pw = st.text_input("접근 비밀번호", type="password")
    if pw and pw == st.secrets.get("APP_PASSWORD"):
        st.session_state.auth_ok = True
        st.rerun()
    else:
        st.stop()
```

그리고 Streamlit Cloud secrets 에 `APP_PASSWORD = "..."` 추가.
