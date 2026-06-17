# 토론을 통해 AI를 이겨라 (v3)

중학생용 AI 토론 연습 웹앱입니다.

## 🚀 빠른 시작 (로컬 PC에서 실행)

### 1. Python 설치
- Python 3.12.7 다운로드: https://www.python.org/downloads/release/python-3127/
- **설치 시 "Add python.exe to PATH" 반드시 체크!**

### 2. 패키지 설치
폴더에서 터미널(PowerShell) 열고:
```
pip install -r requirements.txt
```

### 3. 서버 실행
```
python main.py
```

### 4. 브라우저 접속
```
http://localhost:8000
```

### 5. 같은 Wi-Fi의 태블릿에서 접속하기
- PowerShell에서 `ipconfig` 입력 → IPv4 주소 확인 (예: 192.168.0.15)
- 태블릿 브라우저에서 `http://192.168.0.15:8000` 접속
- 방화벽 경고 시 "허용" 클릭

## ⚙️ 관리자 설정 (필수)

1. 우측 하단 [관리자] 클릭
2. 비밀번호: `admin1234`
3. **Google AI Studio API 키** 입력
   - 발급: https://aistudio.google.com → Get API Key
   - [API 연결 테스트] 클릭 → 성공 확인
4. **구글 시트 웹훅 URL** 입력 (선택)
   - 아래 "구글 시트 연동" 섹션 참고
   - [시트 연결 테스트] 클릭 → 시트에 데이터 들어오는지 확인!
5. [설정 저장]

## 📊 구글 시트 연동 (Apps Script)

### 1단계: 새 스프레드시트 만들기
- https://sheets.google.com → 새 시트

### 2단계: Apps Script 열기
- 메뉴: 확장 프로그램 → Apps Script

### 3단계: 코드 붙여넣기
- `google_apps_script.js` 파일 내용 전체 복사
- Apps Script 편집기에 붙여넣기 (기존 코드는 삭제)
- Ctrl+S로 저장

### 4단계: 권한 승인 (★ 가장 자주 실수하는 부분)
- 좌측 함수 선택: `doPost`
- 상단 [실행] 버튼 클릭
- 권한 승인 팝업 뜨면:
  - "고급" 클릭
  - "안전하지 않음(프로젝트명)으로 이동" 클릭
  - "허용" 클릭

### 5단계: 웹 앱 배포
- 우측 상단 [배포] → [새 배포]
- 톱니바퀴 → "웹 앱" 선택
- 설정:
  - 설명: 아무거나 (예: "토론앱 v1")
  - **다음으로 실행: 나**
  - **액세스 권한: 모든 사용자** ← 매우 중요!
- [배포] 클릭
- 표시된 URL 복사

### 6단계: 토론앱에 URL 등록
- 토론앱 관리자 설정에 붙여넣기
- [시트 연결 테스트] 클릭
- **구글 시트에 테스트 행이 추가되었는지 직접 확인!**

### ⚠️ 자주 발생하는 문제

| 증상 | 원인 | 해결 |
|:---|:---|:---|
| 연결 테스트는 성공인데 토론 후 기록 안 됨 | Apps Script 권한 미승인 | 4단계 다시 |
| 코드 수정 후에도 반영 안 됨 | "저장"만 함 | 반드시 [배포 > 새 배포] |
| 401, 403 오류 | "액세스: 모든 사용자" 안 됨 | 5단계 다시 |

## 🌐 인터넷 배포 (학생들이 어디서나 접속)

### Render.com 무료 배포

1. **GitHub 계정 만들기**: https://github.com (이미 있으면 생략)

2. **GitHub에 코드 업로드**
   - https://github.com/new → 새 저장소 만들기
   - 저장소 이름: `debate-app` (자유)
   - 공개(Public) 선택
   - 이 폴더의 모든 파일을 업로드
     - 또는 GitHub Desktop 사용

3. **Render.com 가입**: https://render.com (GitHub 계정으로 로그인)

4. **새 웹 서비스 만들기**
   - Dashboard → New + → Web Service
   - GitHub 저장소 연결 → `debate-app` 선택
   - 자동으로 설정 인식됨 (render.yaml)
   - [Create Web Service] 클릭

5. **환경변수 추가 (선택)**
   - 배포 후 Dashboard → Environment에서
   - GEMINI_API_KEY 등을 직접 설정도 가능

6. **배포 완료**
   - 약 3~5분 후 `https://debate-app-xxxx.onrender.com` 생성
   - 이 URL을 학생들에게 공유

### Render 무료 플랜 주의사항
- 15분 미사용 시 sleep → 첫 접속 시 약 30초 대기
- 수업 직전에 한 번 접속해두면 깨어남

## 📁 파일 구조

```
.
├── main.py                    # FastAPI 백엔드
├── requirements.txt           # 패키지 목록
├── templates/
│   └── index.html             # 프론트엔드
├── static/                    # 정적 파일
├── google_apps_script.js      # 구글 시트 연동 코드
├── render.yaml                # Render 배포 설정
├── Procfile                   # 호스팅용
├── runtime.txt                # Python 버전
├── .gitignore                 # Git 무시 파일
└── README.md                  # 이 문서
```

## 🎯 토론 진행 방식

1. **항상 찬성측이 먼저 발언**
2. 토론 흐름:
   - **입론** (찬성→반대, 각 3분): 자신의 입장 처음 밝히기
   - **반론 1차** (찬성→반대, 각 2분): 상대 주장 반박
   - **반론 2차** (찬성→반대, 각 2분): 더 강한 반박
   - **최종변론** (찬성→반대, 각 2분): 주장 정리 마무리
3. **AI 대기 시간**: 발언 시간의 20~30% 랜덤 시점에 응답
4. **시간 초과 감점**:
   - 0~10초: 감점 없음
   - 10~30초: -1점
   - 30~60초: -3점
   - 60초~: -5점

## 🐛 문제 해결

### "AI 응답 생성 오류" 메시지
- 관리자에서 API 키 재확인
- [API 연결 테스트] 실행
- 무료 등급 사용량 초과 시 잠시 대기

### 구글 시트 기록 안 됨
- PowerShell 터미널에서 `[시트 전송 실패]` 로그 확인
- Apps Script 편집기 → 좌측 "실행" 메뉴 → 최근 실행 로그 확인
- Apps Script "배포 → 새 배포" 다시 실행

### 태블릿 접속 안 됨
- PC와 태블릿이 같은 Wi-Fi인지 확인
- Windows 방화벽 → 포트 8000 허용
- `ipconfig`의 IPv4 주소가 정확한지 확인

---

문의사항이 있으시면 담당 개발자에게 연락해주세요.
