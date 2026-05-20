"""
FastAPI 서버.
실행: uvicorn api:app --reload --port 8000
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / "config" / ".env")

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config.settings import BASE_DIR, PET_CONFIG_PATH
from core.cv_analyzer import analyze
from core.llm_advisor import get_advice

RECORDS_PATH = BASE_DIR / "records.json"

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
    categories: str = Form(default=""),
):
    """이미지·프로필·카테고리 정보를 받아 CV 분석 결과 및 GPT 조언을 반환한다."""
    YOLO_SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".avif", ".heic"}
    ALIAS = {".jfif": ".jpg", ".jpe": ".jpg"}
    suffix = Path(file.filename or "image.jpg").suffix.lower()
    suffix = ALIAS.get(suffix, suffix)
    if suffix not in YOLO_SUPPORTED:
        suffix = ".jpg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cv_result = analyze(tmp_path)
        pet_profile = _resolve_profile(profile)

        categories_data: dict = {}
        if categories:
            try:
                categories_data = json.loads(categories)
            except json.JSONDecodeError:
                pass

        advice = get_advice(cv_result, pet_profile, categories_data)

        return {
            "cv_class": cv_result["class"],
            "bristol_grade": cv_result.get("bristol_grade", ""),
            "confidence": cv_result["confidence"],
            "description": cv_result.get("description", ""),
            "advice": advice,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.post("/record")
async def save_record(request: Request):
    """카테고리 데이터와 분석 결과를 records.json에 기록한다."""
    data = await request.json()
    records: list = []
    if RECORDS_PATH.exists():
        try:
            records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    records.append({**data, "saved_at": datetime.now(timezone.utc).isoformat()})
    RECORDS_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"status": "ok"}


@app.get("/records")
async def get_records():
    """저장된 기록 목록을 반환한다."""
    if not RECORDS_PATH.exists():
        return []
    try:
        return json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
