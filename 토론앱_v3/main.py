from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import uvicorn
import json
import os
import base64
import random
import asyncio
import traceback
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

app = FastAPI()

# CORS 설정 (태블릿 등 외부 접속용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 디렉토리 설정
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
SETTINGS_FILE = BASE_DIR / "settings.json"

TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ============================================================
# AI 응답 대기 시간 설정 (20% ~ 30% 랜덤)
# ============================================================
MIN_DELAY_RATIO = 0.20
MAX_DELAY_RATIO = 0.30

# 사용 가능한 모델 우선순위
MODEL_PRIORITY = [
    'models/gemini-2.5-flash',
    'models/gemini-2.5-flash-lite',
    'models/gemini-flash-latest',
    'models/gemini-flash-lite-latest',
    'models/gemini-2.0-flash-lite',
    'models/gemini-1.5-flash-latest',
    'models/gemini-1.5-flash-8b-latest',
    'models/gemini-1.5-flash',
]

def get_available_model(api_key):
    """사용 가능한 모델을 찾아서 반환"""
    genai.configure(api_key=api_key)
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)

    selected_model = None
    for model_name in MODEL_PRIORITY:
        if model_name in available_models:
            selected_model = model_name
            break

    if not selected_model and available_models:
        selected_model = available_models[0]

    return selected_model, available_models

# 설정 관리
def load_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "api_key": "",
        "admin_password": "admin1234",
        "sheet_webhook_url": "",
        "sheet_view_url": ""
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

settings = load_settings()

# ============================================================
# 메인 페이지
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ============================================================
# 관리자
# ============================================================
@app.post("/api/admin/login")
async def admin_login(request: Request):
    data = await request.json()
    if data.get("password") == settings.get("admin_password", "admin1234"):
        return {"success": True}
    return {"success": False, "error": "비밀번호가 틀렸습니다."}

@app.post("/api/admin/settings")
async def save_admin_settings(request: Request):
    global settings
    data = await request.json()
    settings["api_key"] = data.get("api_key", settings.get("api_key", ""))
    settings["sheet_webhook_url"] = data.get("sheet_webhook_url", settings.get("sheet_webhook_url", ""))
    settings["sheet_view_url"] = data.get("sheet_view_url", settings.get("sheet_view_url", ""))
    save_settings(settings)
    return {"success": True}

@app.get("/api/admin/settings")
async def get_admin_settings():
    return {
        "api_key": settings.get("api_key", ""),
        "sheet_webhook_url": settings.get("sheet_webhook_url", ""),
        "sheet_view_url": settings.get("sheet_view_url", "")
    }

# ============================================================
# API 연결 테스트
# ============================================================
@app.post("/api/test-connection")
async def test_connection(request: Request):
    data = await request.json()
    api_key = data.get("api_key", "")

    if not api_key:
        return {"success": False, "error": "API 키를 입력해주세요."}

    try:
        selected_model, available_models = get_available_model(api_key)
        if not selected_model:
            return {"success": False, "error": "사용 가능한 모델이 없습니다."}

        model = genai.GenerativeModel(selected_model.replace('models/', ''))
        response = model.generate_content("안녕")

        return {
            "success": True,
            "message": f"연결 성공! 모델: {selected_model}",
            "model": selected_model
        }
    except Exception as e:
        return {"success": False, "error": f"오류: {str(e)}"}

# ============================================================
# 구글 시트 연결 테스트
# ============================================================
@app.post("/api/test-sheet")
async def test_sheet(request: Request):
    data = await request.json()
    webhook_url = data.get("sheet_webhook_url", "")

    if not webhook_url:
        return {"success": False, "error": "웹훅 URL을 입력해주세요."}

    try:
        test_payload = {
            "type": "test",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "토론앱 연결 테스트"
        }
        result = await send_to_sheet(webhook_url, test_payload)
        if result["success"]:
            return {"success": True, "message": "구글 시트 연결 성공! 시트를 확인해주세요."}
        else:
            return {"success": False, "error": result.get("error", "알 수 없는 오류")}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def send_to_sheet(webhook_url, payload):
    """구글 시트에 데이터 전송 (상세 로깅)"""
    try:
        print(f"\n{'='*60}")
        print(f"[시트 전송] {datetime.now().strftime('%H:%M:%S')}")
        print(f"[시트 전송] URL: {webhook_url[:80]}...")
        print(f"[시트 전송] Payload type: {payload.get('type', 'unknown')}")

        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            webhook_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        # 비동기 실행을 위해 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=30))

        response_text = response.read().decode("utf-8")
        status_code = response.status

        print(f"[시트 전송] 응답 상태: {status_code}")
        print(f"[시트 전송] 응답 내용: {response_text[:200]}")
        print(f"{'='*60}\n")

        return {"success": True, "response": response_text, "status": status_code}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if hasattr(e, 'read') else ""
        print(f"[시트 전송 실패] HTTP {e.code}: {error_body[:300]}")
        print(f"{'='*60}\n")
        return {"success": False, "error": f"HTTP {e.code}: {error_body[:200]}"}
    except Exception as e:
        print(f"[시트 전송 실패] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}

# ============================================================
# AI 응답 생성 (단계별 명확한 프롬프트)
# ============================================================
@app.post("/api/ai-response")
async def generate_ai_response(request: Request):
    data = await request.json()

    api_key = settings.get("api_key", "")
    if not api_key:
        return {"success": False, "error": "API 키가 설정되지 않았습니다."}

    topic = data.get("topic", "")
    student_position = data.get("student_position", "찬성")
    ai_position = "반대" if student_position == "찬성" else "찬성"
    stage = data.get("stage", "")  # "입론", "반론1", "반론2", "최종변론"
    student_argument = data.get("student_argument", "")
    debate_history = data.get("debate_history", [])
    image_base64 = data.get("image_base64", "")
    time_limit = data.get("time_limit", 120)  # 초 단위

    try:
        selected_model, _ = get_available_model(api_key)
        if not selected_model:
            return {"success": False, "error": "사용 가능한 모델이 없습니다."}

        model = genai.GenerativeModel(selected_model.replace('models/', ''))

        # 토론 히스토리
        history_text = ""
        for h in debate_history:
            history_text += f"[{h.get('speaker', '')}]: {h.get('content', '')}\n"

        # 단계별 명확한 프롬프트 (선생님 요구사항 반영)
        stage_instructions = {
            "입론": f"""[현재 단계: 입론]
입론은 **각자의 입장을 처음으로 밝히는 단계**입니다.
상대방의 주장을 반박하는 것이 아니라, 당신({ai_position}측)의 핵심 주장과 근거를 제시하세요.
- 논제에 대한 명확한 입장 선언
- 그렇게 주장하는 핵심 이유 2~3가지
- 각 이유를 뒷받침하는 통계, 전문가 의견, 실제 사례, 법률 등 구체적 근거 인용
- 상대방 주장을 직접 반박하지 마세요 (이건 입론입니다)""",

            "반론1": f"""[현재 단계: 반론 1차]
반론은 **상대방의 주장을 반박하는 단계**입니다.
상대방(학생, {student_position}측)이 입론에서 제시한 주장의 약점을 지적하고 반박하세요.
- 상대방 주장의 논리적 허점, 근거 부족, 사실 오류 등을 구체적으로 지적
- 반박을 뒷받침하는 통계, 전문가 의견, 실제 사례, 법률 등 인용
- 동시에 당신({ai_position}측)의 입장을 강화하는 추가 근거 제시""",

            "반론2": f"""[현재 단계: 반론 2차]
2차 반론입니다. 상대방이 1차 반론 이후 제시한 추가 주장이나 재반박을 다시 반박하세요.
- 이전 반론에서 다루지 못한 새로운 약점 지적
- 더 강력한 통계, 사례, 전문가 의견 인용
- 당신({ai_position}측) 주장의 우위를 명확히 드러내세요""",

            "최종변론": f"""[현재 단계: 최종 변론]
최종 변론은 **각자의 주장을 정리하며 마무리하는 단계**입니다.
새로운 반박을 하기보다, 전체 토론을 통해 당신({ai_position}측)이 주장한 내용을 정리하세요.
- 지금까지 당신이 제시한 핵심 주장 요약
- 가장 강력한 근거 1~2개 재강조
- 청중(심사위원)에게 호소하는 마무리 멘트
- 왜 당신의 입장이 옳은지 확신을 주는 결론"""
        }

        stage_guide = stage_instructions.get(stage, stage_instructions["입론"])

        # 이미지가 첨부된 경우 추가 지시
        image_instruction = ""
        if image_base64:
            image_instruction = "\n\n[이미지 분석] 상대방이 첨부한 이미지를 분석하고, 이미지 내용을 토론에 반영하여 답변하세요."

        prompt = f"""당신은 토론 대회에 참가한 AI 토론자입니다.

==== 토론 정보 ====
논제: {topic}
당신의 입장: {ai_position}측
상대방(학생) 입장: {student_position}측

==== 지금까지의 토론 흐름 ====
{history_text if history_text else "(아직 발언 없음)"}

==== 상대방의 직전 발언 ====
{student_argument if student_argument else "(없음)"}

==== 이번 단계 지시사항 ====
{stage_guide}
{image_instruction}

==== 답변 작성 규칙 ====
1. 반드시 {ai_position}측 입장에서 답변하세요.
2. 중학생이 이해할 수 있는 수준의 어휘를 사용하세요.
3. 반드시 다음 중 2가지 이상을 인용하세요:
   - 구체적 통계 수치 (예: "OECD 자료에 따르면 ~%")
   - 전문가/학자의 의견 (예: "○○대학교 교수에 따르면")
   - 실제 사례나 사건 (예: "20○○년 ○○사건에서")
   - 법률/제도 (예: "헌법 제○조에 따르면")
   - 권위 있는 기관 보고서 (예: "유엔 보고서에 따르면")
4. 300자 내외로 작성하세요.
5. 존댓말을 사용하세요.
6. 위 단계 지시사항을 반드시 따르세요.

이제 {ai_position}측 입장으로 [{stage}] 발언을 작성하세요:"""

        # 이미지 포함 여부에 따라 호출
        if image_base64:
            try:
                # base64 디코딩
                if image_base64.startswith("data:"):
                    image_base64 = image_base64.split(",", 1)[1]
                image_data = base64.b64decode(image_base64)

                image_part = {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
                response = model.generate_content([prompt, image_part])
            except Exception as img_err:
                print(f"이미지 처리 오류: {img_err}, 텍스트만으로 처리")
                response = model.generate_content(prompt)
        else:
            response = model.generate_content(prompt)

        ai_response = response.text

        # ============ AI 대기 시간 (20~30% 랜덤) ============
        delay_ratio = random.uniform(MIN_DELAY_RATIO, MAX_DELAY_RATIO)
        delay_seconds = time_limit * delay_ratio
        print(f"[AI 대기] {delay_seconds:.1f}초 ({delay_ratio*100:.1f}%) 후 응답 표시")
        await asyncio.sleep(delay_seconds)

        return {
            "success": True,
            "response": ai_response,
            "model": selected_model,
            "delay_seconds": round(delay_seconds, 1)
        }

    except Exception as e:
        error_msg = str(e)
        print(f"AI 응답 생성 오류: {error_msg}")
        traceback.print_exc()
        return {"success": False, "error": f"AI 응답 생성 중 오류: {error_msg}"}

# ============================================================
# 토론 평가 + 구글 시트 전송
# ============================================================
@app.post("/api/evaluate")
async def evaluate_debate(request: Request):
    data = await request.json()

    api_key = settings.get("api_key", "")
    if not api_key:
        return {"success": False, "error": "API 키가 설정되지 않았습니다."}

    topic = data.get("topic", "")
    student_position = data.get("student_position", "")
    debate_history = data.get("debate_history", [])
    student_info = data.get("student_info", {})
    overtime_penalty = data.get("overtime_penalty", 0)  # 시간 초과 감점

    try:
        selected_model, _ = get_available_model(api_key)
        if not selected_model:
            return {"success": False, "error": "사용 가능한 모델이 없습니다."}

        model = genai.GenerativeModel(selected_model.replace('models/', ''))

        history_text = ""
        for h in debate_history:
            history_text += f"[{h.get('speaker', '')}] ({h.get('stage', '')}): {h.get('content', '')}\n\n"

        prompt = f"""다음 토론을 평가해주세요.

논제: {topic}
학생 입장: {student_position}측
시간 초과 감점: {overtime_penalty}점

==== 토론 전체 내용 ====
{history_text}

==== 평가 기준 ====
1. 논리성 (1~10점): 주장이 논리적으로 일관되고 타당한가
2. 근거의 질 (1~10점): 통계, 사례, 전문가 의견 등 근거가 적절하고 신뢰성 있는가
3. 반박 능력 (1~10점): 상대 주장을 효과적으로 반박했는가
4. 표현력 (1~10점): 명확하고 설득력 있게 표현했는가

==== 출력 형식 ====
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

{{
    "winner": "학생" 또는 "AI",
    "logic_score": 1-10 사이 정수,
    "evidence_score": 1-10 사이 정수,
    "rebuttal_score": 1-10 사이 정수,
    "expression_score": 1-10 사이 정수,
    "subtotal": 4개 점수 합계 (40점 만점),
    "overtime_penalty": {overtime_penalty},
    "total_score": subtotal - overtime_penalty,
    "strengths": "학생이 잘한 점 (3문장 이상)",
    "improvements": "학생이 개선할 점 (3문장 이상)",
    "key_moments": "토론에서 인상적이었던 순간",
    "summary": "토론 전체 요약 (5문장 이상)"
}}"""

        response = model.generate_content(prompt)
        result_text = response.text

        # JSON 파싱
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(result_text)
        except Exception as parse_err:
            print(f"JSON 파싱 실패: {parse_err}, 기본값 사용")
            result = {
                "winner": "무승부",
                "logic_score": 7,
                "evidence_score": 7,
                "rebuttal_score": 7,
                "expression_score": 7,
                "subtotal": 28,
                "overtime_penalty": overtime_penalty,
                "total_score": 28 - overtime_penalty,
                "strengths": "토론에 성실하게 참여했습니다.",
                "improvements": "더 구체적인 근거 제시가 필요합니다.",
                "key_moments": "전반적으로 침착한 진행이 인상적이었습니다.",
                "summary": "양측 모두 좋은 논점을 제시했습니다."
            }

        # ============ 구글 시트 자동 전송 ============
        webhook_url = settings.get("sheet_webhook_url", "")
        sheet_status = "전송 안함 (웹훅 URL 미설정)"

        if webhook_url:
            print("\n[평가 완료] 구글 시트로 전송 시도...")
            sheet_payload = {
                "type": "debate_result",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "grade": student_info.get("grade", ""),
                "class": student_info.get("class_name", ""),
                "number": student_info.get("number", ""),
                "name": student_info.get("name", ""),
                "topic": topic,
                "student_position": student_position,
                "winner": result.get("winner", ""),
                "logic_score": result.get("logic_score", 0),
                "evidence_score": result.get("evidence_score", 0),
                "rebuttal_score": result.get("rebuttal_score", 0),
                "expression_score": result.get("expression_score", 0),
                "subtotal": result.get("subtotal", 0),
                "overtime_penalty": result.get("overtime_penalty", 0),
                "total_score": result.get("total_score", 0),
                "strengths": result.get("strengths", ""),
                "improvements": result.get("improvements", ""),
                "key_moments": result.get("key_moments", ""),
                "summary": result.get("summary", ""),
                "debate_log": history_text
            }
            sheet_result = await send_to_sheet(webhook_url, sheet_payload)
            if sheet_result["success"]:
                sheet_status = "전송 성공"
            else:
                sheet_status = f"전송 실패: {sheet_result.get('error', '')}"

        return {
            "success": True,
            "evaluation": result,
            "sheet_status": sheet_status,
            "sheet_view_url": settings.get("sheet_view_url", "")
        }

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# ============================================================
# 서버 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("토론을 통해 AI를 이겨라 - 서버 시작 (v3)")
    print("=" * 60)
    print("로컬 접속: http://localhost:8000")
    print("같은 Wi-Fi 접속: http://[본인 IP]:8000")
    print("  -> IP 확인: PowerShell에서 'ipconfig' 입력 후 IPv4 주소")
    print("관리자 비밀번호: admin1234")
    print("=" * 60)

    # Render.com 등 호스팅 환경 PORT 환경변수 지원
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
