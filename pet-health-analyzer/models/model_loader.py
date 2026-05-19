"""
PyTorch 모델 로더 모듈.
poop_classifier.pt 파일을 YOLO로 불러와 이미지를 분류하고
클래스 및 신뢰도를 반환하는 predict 함수를 제공한다.
"""

from pathlib import Path
from typing import Any

from ultralytics import YOLO

from config.settings import (
    CLASSES,
    CV_CONFIDENCE_THRESHOLD,
    MODEL_PATH,
)

_model_cache: YOLO | None = None


def load_model() -> YOLO:
    """pt 파일에서 YOLO 모델을 로드한다."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(
            f"[오류] 모델 파일을 찾을 수 없습니다: {MODEL_PATH}\n"
            "poop_classifier.pt 파일을 models/ 폴더에 넣어주세요."
        )

    _model_cache = YOLO(str(model_path))
    return _model_cache


def predict(image_path: str) -> dict[str, Any]:
    """이미지 경로를 받아 분류 결과와 신뢰도를 반환한다.

    Returns:
        {"class": str, "confidence": float}
        신뢰도가 CV_CONFIDENCE_THRESHOLD 미만이면 class를 "unknown"으로 반환.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(
            f"[오류] 이미지 파일을 찾을 수 없습니다: {image_path}"
        )

    model = load_model()
    results = model(str(path))
    probs = results[0].probs

    confidence = float(probs.top1conf.item())
    predicted_index = int(probs.top1)

    if confidence < CV_CONFIDENCE_THRESHOLD:
        return {"class": "unknown", "confidence": confidence}

    return {
        "class": CLASSES[predicted_index],
        "confidence": confidence,
    }
