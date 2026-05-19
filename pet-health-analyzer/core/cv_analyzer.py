"""
CV 이미지 분석 모듈.
model_loader.predict()를 호출하고, Bristol 등급 및 설명을 포함한
표준화된 분석 결과 딕셔너리를 반환한다.
"""

from typing import Any

from config.settings import BRISTOL_DESCRIPTION, BRISTOL_MAP
from models.model_loader import predict


def analyze(image_path: str) -> dict[str, Any]:
    """이미지를 분석해 클래스, 신뢰도, Bristol 등급, 설명을 반환한다.

    Returns:
        {
            "class": str,
            "confidence": float,
            "bristol_grade": str,
            "description": str,
        }
        class가 "unknown"이면 판단 불가 상태.
    """
    result = predict(image_path)
    cv_class = result["class"]
    confidence = result["confidence"]

    if cv_class == "unknown":
        return {
            "class": "unknown",
            "confidence": confidence,
            "bristol_grade": "판단 불가",
            "description": (
                f"모델 신뢰도({confidence:.1%})가 기준치에 미달해 분류할 수 없습니다. "
                "선명한 사진으로 다시 시도해주세요."
            ),
        }

    bristol_grade = BRISTOL_MAP.get(cv_class, "알 수 없음")
    description = BRISTOL_DESCRIPTION.get(cv_class, "설명 없음")

    return {
        "class": cv_class,
        "confidence": confidence,
        "bristol_grade": bristol_grade,
        "description": description,
    }
