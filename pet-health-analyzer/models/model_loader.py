"""
PyTorch 모델 로더 모듈.
poop_classifier.pkl 파일을 불러와 eval 모드로 전환하고,
이미지를 전처리한 뒤 클래스 및 신뢰도를 반환하는 predict 함수를 제공한다.
"""

import pickle
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms

from config.settings import (
    CLASSES,
    CV_CONFIDENCE_THRESHOLD,
    MODEL_PATH,
)

_IMAGE_MEAN = [0.485, 0.456, 0.406]
_IMAGE_STD = [0.229, 0.224, 0.225]

_preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=_IMAGE_MEAN, std=_IMAGE_STD),
])

_model_cache: nn.Module | None = None


def load_model() -> nn.Module:
    """pkl 파일에서 모델을 로드하고 eval 모드로 전환한다."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(
            f"[오류] 모델 파일을 찾을 수 없습니다: {MODEL_PATH}\n"
            "Colab에서 학습한 poop_classifier.pkl 파일을 models/ 폴더에 넣어주세요."
        )

    try:
        model: Any = torch.load(model_path, map_location="cpu", weights_only=False)
    except Exception:
        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
        except Exception as e:
            raise RuntimeError(
                f"[오류] 모델 로드에 실패했습니다: {e}\n"
                "pkl 파일이 올바른 PyTorch 모델인지 확인해주세요."
            ) from e

    if hasattr(model, "eval"):
        model.eval()

    _model_cache = model
    return model


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

    try:
        image = Image.open(path).convert("RGB")
    except Exception as e:
        raise ValueError(
            f"[오류] 이미지 파일을 열 수 없습니다: {e}"
        ) from e

    model = load_model()
    tensor = _preprocess(image).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)
        probabilities = torch.softmax(output, dim=1)[0]

    confidence = float(probabilities.max().item())
    predicted_index = int(probabilities.argmax().item())

    if confidence < CV_CONFIDENCE_THRESHOLD:
        return {"class": "unknown", "confidence": confidence}

    return {
        "class": CLASSES[predicted_index],
        "confidence": confidence,
    }
