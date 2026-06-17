# 깃허브 + Render 배포 가이드 (학생 태블릿용)

이 가이드를 따라하면 **인터넷 어디서나 접속 가능한 토론앱 웹사이트**가 만들어집니다.

---

## 🎯 최종 결과
- `https://debate-app-xxxx.onrender.com` 형태의 URL 생성
- 학생들이 태블릿에서 이 URL로 접속하면 토론앱 사용 가능
- 선생님 노트북을 켜둘 필요 없음!

---

## 📋 준비물
1. 구글 계정 (Apps Script, AI Studio 용)
2. GitHub 계정 (없으면 만들기: https://github.com/signup)
3. Render.com 계정 (GitHub 계정으로 가입)

---

## 🚀 STEP 1: GitHub에 코드 업로드

### 방법 A: 웹브라우저로 (가장 쉬움)

1. **새 저장소 만들기**
   - https://github.com/new
   - Repository name: `debate-app` (자유)
   - **Public** 선택 (Private도 가능)
   - "Add a README file" 체크 안 함
   - [Create repository] 클릭

2. **파일 업로드**
   - 만들어진 저장소 화면에서 [uploading an existing file] 클릭
   - 토론앱 폴더의 **모든 파일과 폴더**를 드래그 앤 드롭:
     - `main.py`
     - `requirements.txt`
     - `templates/` 폴더 (안에 index.html)
     - `static/` 폴더
     - `Procfile`
     - `render.yaml`
     - `runtime.txt`
     - `.gitignore`
     - `README.md`
   - **`settings.json` 파일은 업로드 하지 마세요!** (API 키가 들어있어서 위험)
   - 아래 "Commit changes" 클릭

### 방법 B: GitHub Desktop 사용

1. https://desktop.github.com 다운로드 & 설치
2. 로그인 → File → New repository → 토론앱 폴더 선택
3. "Publish repository" 클릭

---

## 🚀 STEP 2: Render.com 배포

1. **Render.com 가입**
   - https://render.com → "Get Started" → GitHub로 가입

2. **새 웹 서비스 만들기**
   - 대시보드 우측 상단 [New +] → [Web Service]
   - "Build and deploy from a Git repository" 선택 → [Next]

3. **GitHub 저장소 연결**
   - 처음이면 GitHub 연동 권한 승인
   - 방금 만든 `debate-app` 저장소 선택 → [Connect]

4. **설정 확인**
   - Name: `debate-app` (URL에 들어감, 자유)
   - Region: `Singapore` (한국에서 가장 빠름)
   - Branch: `main`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type: Free** ← 무료!

5. **[Create Web Service] 클릭**
   - 빌드 시작 (약 3~5분)
   - 로그에 "Your service is live" 나오면 완료!

6. **URL 확인 및 접속**
   - 상단의 `https://debate-app-xxxx.onrender.com` 클릭
   - 토론앱 메인 화면이 보이면 성공!

---

## ⚙️ STEP 3: 관리자 설정 (필수)

배포된 URL로 접속해서:

1. 우측 하단 [관리자] 클릭
2. 비밀번호: `admin1234`
3. **Google AI Studio API 키** 입력
4. **구글 시트 웹훅 URL** 입력
5. 각각 [연결 테스트] 클릭
6. [설정 저장]

> 💡 **주의**: Render의 무료 플랜에서는 서버가 재시작되면 settings.json이 사라질 수 있습니다.
> 매번 관리자 설정을 다시 해야 할 수 있어요.
> 영구 저장을 원하면 환경 변수를 사용하거나 유료 플랜으로 업그레이드.

---

## 🎓 STEP 4: 학생들에게 배포

- 학생 태블릿 브라우저(크롬 권장)에 URL 입력
- 북마크 추가하면 편리!
- QR 코드로 만들어서 공유하면 더 편함:
  - https://qr.naver.com 등에서 URL → QR 변환

---

## ⚠️ 무료 플랜 주의사항

### 자동 절전 (Sleep)
- 15분 동안 접속이 없으면 서버가 잠듦
- 첫 접속자는 약 30~60초 기다려야 함
- **해결**: 수업 시작 5분 전에 선생님이 미리 접속해두기

### 월 사용량 제한
- 무료: 월 750시간 (한 달 내내 켜둬도 OK)
- 한도 초과 시 자동 정지

### 보안
- API 키는 절대 GitHub에 올리지 마세요
- `settings.json`은 `.gitignore`에 등록되어 있어 안전
- 관리자 비밀번호는 변경 권장 (코드에서 수정 가능)

---

## 🔄 코드 업데이트 방법

1. 로컬에서 코드 수정
2. GitHub 저장소에 다시 업로드 (또는 git push)
3. Render가 자동으로 감지하고 재배포 (약 2~3분)

---

## 🐛 문제 해결

| 증상 | 해결 |
|:---|:---|
| 배포 실패 | Render 로그 확인 → requirements.txt 패키지 버전 확인 |
| 첫 접속이 너무 느림 | 무료 플랜 sleep 때문, 정상. 수업 전 미리 접속 |
| API 키 자꾸 초기화됨 | Render 환경변수에 저장하거나 유료 플랜 사용 |
| 한국어 깨짐 | runtime.txt에 python-3.12.7 명시되어 있어야 함 |

---

## 📞 도움이 필요하면

각 단계에서 화면 캡처와 함께 질문해주시면 도와드릴 수 있습니다.
