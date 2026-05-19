"""
건강 보고서 조립·출력·저장 모듈.
CV 분석 결과, 반려동물 프로필, GPT 조언을 하나의 보고서 딕셔너리로 묶어
CLI에 출력하고 날짜별 JSON 로그로 저장한다.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import LOG_DIR


def build_report(
    pet_profile: dict[str, Any],
    cv_result: dict[str, Any],
    advice: str,
) -> dict[str, Any]:
    """세 가지 데이터를 하나의 보고서 딕셔너리로 조립한다."""
    return {
        "timestamp": datetime.now().isoformat(),
        "pet_profile": pet_profile,
        "cv_result": cv_result,
        "advice": advice,
    }


def print_report(report: dict[str, Any]) -> None:
    """보고서를 CLI에 보기 좋게 출력한다."""
    profile = report["pet_profile"]
    cv = report["cv_result"]
    advice = report["advice"]
    timestamp = report.get("timestamp", "")

    divider = "=" * 55

    print(f"\n{divider}")
    print("  반려동물 건강 분석 보고서")
    print(f"  분석 일시: {timestamp[:19].replace('T', ' ')}")
    print(divider)

    print(f"\n  [반려동물 정보]")
    print(f"  이름    : {profile.get('name', '-')}")
    print(f"  종      : {profile.get('species', '-')}")
    print(f"  나이    : {profile.get('age', '-')}세")
    print(f"  체중    : {profile.get('weight', '-')}kg")
    print(f"  중성화  : {'완료' if profile.get('neutered') else '미완료'}")
    print(f"  사료    : {profile.get('food_type', '-')}")

    print(f"\n  [대변 분석 결과]")
    cv_class = cv.get("class", "unknown")
    if cv_class == "unknown":
        print("  분류    : 판단 불가 (신뢰도 미달)")
    else:
        print(f"  분류    : {cv_class}")
    print(f"  Bristol : {cv.get('bristol_grade', '-')}등급")
    print(f"  신뢰도  : {cv.get('confidence', 0):.1%}")
    print(f"  설명    : {cv.get('description', '-')}")

    print(f"\n  [AI 건강 조언]")
    for line in advice.splitlines():
        print(f"  {line}")

    print(f"\n{divider}\n")


def save_log(report: dict[str, Any]) -> str:
    """보고서를 data/analysis_logs/YYYY-MM-DD_HH-MM.json으로 저장하고 경로를 반환한다."""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = report.get("timestamp", datetime.now().isoformat())
    file_ts = timestamp[:16].replace("T", "_").replace(":", "-")
    log_path = log_dir / f"{file_ts}.json"

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"  로그 저장 완료: {log_path}")
    return str(log_path)
