"""
FastAPI 서버.
실행: uvicorn api:app --reload --port 8000
"""

import json
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / "config" / ".env")

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config.settings import BASE_DIR, PET_CONFIG_PATH
from core.cv_analyzer import analyze
from core.llm_advisor import get_advice, get_weekly_summary

RECORDS_PATH = BASE_DIR / "records.json"

app = FastAPI(title="Pet Health Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


_STATUS_PRIORITY: dict[str, int] = {
    "diarrhea": 1,
    "lack-of-water": 1,
    "caution": 2,
    "soft-poop": 2,
    "normal": 3,
}


def _mode(values: list[str]) -> str:
    counts: dict[str, int] = {}
    for v in values:
        if v:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.__getitem__) if counts else ""


def _aggregate_by_day(records: list) -> list:
    """records를 UTC 날짜 기준으로 집계해 날짜 1개당 1개 레코드로 반환한다."""
    groups: dict[str, list] = defaultdict(list)
    for r in records:
        date_key = r.get("saved_at", "")[:10]
        if date_key:
            groups[date_key].append(r)

    result = []
    for date_key in sorted(groups.keys()):
        day = groups[date_key]

        # cv_class: 하루 중 가장 나쁜 상태 (priority 낮을수록 나쁨)
        worst = min(
            day,
            key=lambda r: _STATUS_PRIORITY.get(
                r.get("result", {}).get("cv_class", "normal"), 3
            ),
        )
        cv_class = worst.get("result", {}).get("cv_class", "normal")
        advice   = worst.get("result", {}).get("advice", "")

        # walkMinutes: 합산
        total_walk = sum(
            int(r.get("categories", {}).get("activity", {}).get("walkMinutes") or 0)
            for r in day
        )

        # energy / appetite / vomiting: 최빈값
        def _field(r: dict, *keys: str) -> str:
            val = r.get("categories", {})
            for k in keys:
                val = val.get(k, {}) if isinstance(val, dict) else {}
            return val if isinstance(val, str) else ""

        energy   = _mode([_field(r, "condition", "energy")   for r in day])
        appetite = _mode([_field(r, "condition", "appetite")  for r in day])
        vomiting = _mode([_field(r, "condition", "vomiting")  for r in day])

        # 나머지 필드: 하루 마지막 레코드 기준
        last_cats = day[-1].get("categories", {})

        result.append({
            "saved_at": day[0]["saved_at"],
            "categories": {
                "meal":        last_cats.get("meal", {}),
                "activity":    {**last_cats.get("activity", {}), "walkMinutes": str(total_walk)},
                "condition":   {**last_cats.get("condition", {}), "energy": energy, "appetite": appetite, "vomiting": vomiting},
                "environment": last_cats.get("environment", {}),
            },
            "result": {"cv_class": cv_class, "advice": advice},
        })

    return result


def _append_record(record: dict) -> None:
    """records.json에 레코드 하나를 추가한다."""
    records: list = []
    if RECORDS_PATH.exists():
        try:
            records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    records.append(record)
    RECORDS_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
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

        response_data = {
            "cv_class": cv_result["class"],
            "bristol_grade": cv_result.get("bristol_grade", ""),
            "confidence": cv_result["confidence"],
            "description": cv_result.get("description", ""),
            "advice": advice,
        }

        _append_record({
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "categories": categories_data,
            "result": {
                "cv_class": cv_result["class"],
                "advice": advice,
            },
        })

        return response_data
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.post("/record")
async def save_record(request: Request):
    """카테고리 데이터와 분석 결과를 records.json에 기록한다."""
    data = await request.json()
    _append_record({**data, "saved_at": datetime.now(timezone.utc).isoformat()})
    return {"status": "ok"}


@app.get("/records")
async def get_records():
    """날짜별로 집계된 기록 목록을 반환한다."""
    if not RECORDS_PATH.exists():
        return []
    try:
        raw = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
        return _aggregate_by_day(raw)
    except (json.JSONDecodeError, OSError):
        return []


@app.get("/weekly-summary")
async def weekly_summary():
    """최근 7일치 집계 데이터를 LLM에 전달하여 종합 건강 코멘트를 반환한다."""
    records: list = []
    if RECORDS_PATH.exists():
        try:
            records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    aggregated = _aggregate_by_day(records)
    recent = aggregated[-7:] if len(aggregated) > 7 else aggregated
    summary = get_weekly_summary(recent)
    return {"summary": summary}
