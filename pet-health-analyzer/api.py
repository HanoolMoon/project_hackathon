"""
FastAPI 서버.
프론트엔드에서 업로드한 이미지를 CV 모델로 분류하고 GPT 조언을 반환한다.
실행: uvicorn api:app --reload --port 8000
"""

import json
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / "config" / ".env")

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config.settings import PET_CONFIG_PATH
from core.cv_analyzer import analyze
from core.llm_advisor import get_advice

app = FastAPI(title="Pet Health Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_profile(profile_json: str) -> dict:
    """프론트에서 받은 JSON 프로필을 파싱한다. 없으면 pet_config.json을 읽는다."""
    if profile_json:
        try:
            data = json.loads(profile_json)
            if data.get("name"):
                return data
        except json.JSONDecodeError:
            pass

    path = Path(PET_CONFIG_PATH)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("name"):
                return data
        except (json.JSONDecodeError, OSError):
            pass

    return {"name": "반려동물", "species": "알 수 없음", "age": 0, "weight": 0}


@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    profile: str = Form(default=""),
):
    """이미지와 프로필을 받아 CV 분석 결과 및 GPT 조언을 반환한다."""
    SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    suffix = Path(file.filename or "image.jpg").suffix.lower()
    if suffix not in SUPPORTED:
        suffix = ".jpg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cv_result = analyze(tmp_path)
        pet_profile = _resolve_profile(profile)
        advice = get_advice(cv_result, pet_profile)

        return {
            "cv_class": cv_result["class"],
            "bristol_grade": cv_result.get("bristol_grade", ""),
            "confidence": cv_result["confidence"],
            "description": cv_result.get("description", ""),
            "advice": advice,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)
