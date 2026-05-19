"""
전역 상수 설정 모듈.
모델 경로, CV 임계값, API 설정 등 프로젝트 전반에서 사용하는 상수를 정의한다.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = str(BASE_DIR / "models" / "poop_classifier.pt")
CV_CONFIDENCE_THRESHOLD = 0.70
OPENAI_MODEL = "gpt-4o-mini"
MAX_TOKENS = 512
CLASSES = ["normal", "diarrhea", "lack-of-water", "soft-poop"]

SYSTEM_PROMPT_PATH = str(BASE_DIR / "prompts" / "system_prompt.txt")
USER_TEMPLATE_PATH = str(BASE_DIR / "prompts" / "user_template.txt")

BRISTOL_MAP: dict[str, str] = {
    "normal": "3~4",
    "soft-poop": "5~6",
    "diarrhea": "7",
    "lack-of-water": "1~2",
}

BRISTOL_DESCRIPTION: dict[str, str] = {
    "normal": "정상적인 변 형태로 건강한 상태",
    "soft-poop": "변이 다소 무르고 형태가 불안정한 상태",
    "diarrhea": "변이 액체에 가까운 심한 묽은 상태",
    "lack-of-water": "변이 매우 딱딱하고 건조한 상태",
}
