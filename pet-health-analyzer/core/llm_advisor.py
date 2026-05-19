"""
GPT API 호출 모듈.
system_prompt.txt와 user_template.txt를 읽어 프롬프트를 구성하고,
반려동물 프로필 및 CV 분석 결과를 바탕으로 맞춤 건강 조언을 생성한다.
"""

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import APIError, AuthenticationError, OpenAI

from config.settings import (
    MAX_TOKENS,
    OPENAI_MODEL,
    SYSTEM_PROMPT_PATH,
    USER_TEMPLATE_PATH,
)

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")


def _get_client() -> OpenAI:
    """OpenAI 클라이언트를 생성한다. API 키가 없으면 오류를 발생시킨다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "[오류] OPENAI_API_KEY가 설정되지 않았습니다.\n"
            "config/.env 파일에 OPENAI_API_KEY=<키값> 형식으로 입력해주세요."
        )
    return OpenAI(api_key=api_key)


def _read_prompt_file(path: str) -> str:
    """프롬프트 텍스트 파일을 읽어 반환한다."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"[오류] 프롬프트 파일을 찾을 수 없습니다: {path}"
        )
    return p.read_text(encoding="utf-8").strip()


def get_advice(cv_result: dict[str, Any], pet_profile: dict[str, Any]) -> str:
    """CV 결과와 프로필을 바탕으로 GPT 건강 조언을 반환한다.
    오류 발생 시 1회 재시도 후 한국어 에러 메시지를 반환한다.
    """
    if cv_result.get("class") == "unknown":
        return (
            "대변 분류 신뢰도가 낮아 AI 조언을 제공할 수 없습니다.\n"
            "더 선명한 사진으로 다시 시도하거나 가까운 동물병원에 문의해주세요."
        )

    system_prompt = _read_prompt_file(SYSTEM_PROMPT_PATH)
    user_template = _read_prompt_file(USER_TEMPLATE_PATH)

    confidence_pct = f"{cv_result['confidence'] * 100:.1f}"
    user_message = user_template.format(
        pet_name=pet_profile.get("name", "이름 미상"),
        species=pet_profile.get("species", "알 수 없음"),
        age=pet_profile.get("age", "?"),
        weight=pet_profile.get("weight", "?"),
        cv_class=cv_result.get("class", "unknown"),
        bristol_grade=cv_result.get("bristol_grade", "?"),
        confidence=confidence_pct,
    )

    client = _get_client()

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except AuthenticationError:
            return (
                "[오류] OpenAI API 키가 유효하지 않습니다.\n"
                "config/.env 파일의 OPENAI_API_KEY를 확인해주세요."
            )
        except APIError as e:
            if attempt == 0:
                print(f"  GPT API 오류 발생, 재시도합니다... ({e})")
                time.sleep(2)
                continue
            return (
                f"[오류] GPT API 호출에 실패했습니다: {e}\n"
                "잠시 후 다시 시도해주세요."
            )

    return "[오류] 알 수 없는 오류로 조언을 가져오지 못했습니다."
