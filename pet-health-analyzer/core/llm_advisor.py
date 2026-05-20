"""
GPT API 호출 모듈.
system_prompt.txt와 user_template.txt를 읽어 프롬프트를 구성하고,
반려동물 프로필, CV 분석 결과, 추가 카테고리 정보를 바탕으로 건강 조언을 생성한다.
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "[오류] OPENAI_API_KEY가 설정되지 않았습니다.\n"
            "config/.env 파일에 OPENAI_API_KEY=<키값> 형식으로 입력해주세요."
        )
    return OpenAI(api_key=api_key)


def _read_prompt_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"[오류] 프롬프트 파일을 찾을 수 없습니다: {path}")
    return p.read_text(encoding="utf-8").strip()


def _build_extra_info(categories: dict) -> str:
    """카테고리 데이터에서 입력된 항목만 골라 추가 정보 문자열을 만든다."""
    parts = []

    meal = categories.get("meal", {})
    meal_lines = []
    if meal.get("food"):
        meal_lines.append(f"  먹은 음식: {meal['food']}")
    if meal.get("amount"):
        meal_lines.append(f"  식사량: {meal['amount']}")
    if meal.get("snack"):
        meal_lines.append(f"  간식: {meal['snack']}")
    if meal.get("water"):
        meal_lines.append(f"  물 섭취량: {meal['water']}")
    if meal_lines:
        parts.append("[식사]\n" + "\n".join(meal_lines))

    activity = categories.get("activity", {})
    act_lines = []
    if activity.get("walkMinutes"):
        act_lines.append(f"  산책: {activity['walkMinutes']}분")
    if activity.get("exercise"):
        act_lines.append(f"  운동량: {activity['exercise']}")
    if activity.get("location"):
        act_lines.append(f"  활동 장소: {activity['location']}")
    if act_lines:
        parts.append("[활동]\n" + "\n".join(act_lines))

    condition = categories.get("condition", {})
    cond_lines = []
    if condition.get("energy"):
        cond_lines.append(f"  기력: {condition['energy']}")
    if condition.get("appetite"):
        cond_lines.append(f"  식욕: {condition['appetite']}")
    if condition.get("vomiting"):
        cond_lines.append(f"  구토: {condition['vomiting']}")
    if condition.get("weight"):
        cond_lines.append(f"  체중: {condition['weight']}kg")
    if cond_lines:
        parts.append("[컨디션]\n" + "\n".join(cond_lines))

    environment = categories.get("environment", {})
    env_lines = []
    if environment.get("weather"):
        env_lines.append(f"  날씨: {environment['weather']}")
    if environment.get("temperature"):
        env_lines.append(f"  온도: {environment['temperature']}°C")
    if environment.get("stress"):
        env_lines.append(f"  스트레스 요인: {environment['stress']}")
    if env_lines:
        parts.append("[환경]\n" + "\n".join(env_lines))

    if not parts:
        return ""
    return "\n추가 정보:\n" + "\n\n".join(parts) + "\n"


def get_advice(
    cv_result: dict[str, Any],
    pet_profile: dict[str, Any],
    categories: dict[str, Any] | None = None,
) -> str:
    """CV 결과, 프로필, 카테고리 정보를 바탕으로 GPT 건강 조언을 반환한다.
    오류 발생 시 1회 재시도 후 한국어 에러 메시지를 반환한다.
    """
    if cv_result.get("class") == "unknown":
        return (
            "대변 분류 신뢰도가 낮아 AI 조언을 제공할 수 없습니다.\n"
            "더 선명한 사진으로 다시 시도하거나 가까운 동물병원에 문의해주세요."
        )

    system_prompt = _read_prompt_file(SYSTEM_PROMPT_PATH)
    user_template = _read_prompt_file(USER_TEMPLATE_PATH)

    extra_info = _build_extra_info(categories or {})
    confidence_pct = f"{cv_result['confidence'] * 100:.1f}"

    user_message = user_template.format(
        pet_name=pet_profile.get("name", "이름 미상"),
        species=pet_profile.get("species", "알 수 없음"),
        age=pet_profile.get("age", "?"),
        weight=pet_profile.get("weight", "?"),
        cv_class=cv_result.get("class", "unknown"),
        bristol_grade=cv_result.get("bristol_grade", "?"),
        confidence=confidence_pct,
        extra_info=extra_info,
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


def get_weekly_summary(records: list[dict]) -> str:
    """7일치 records를 바탕으로 종합 건강 코멘트를 생성한다."""
    if not records:
        return "데이터가 없어 코멘트를 생성할 수 없습니다."

    lines = []
    for r in records:
        date = r.get("saved_at", "")[:10]
        cv_class = r.get("result", {}).get("cv_class", "unknown")
        cats = r.get("categories", {})
        walk = cats.get("activity", {}).get("walkMinutes", "-")
        energy = cats.get("condition", {}).get("energy", "-")
        appetite = cats.get("condition", {}).get("appetite", "-")
        vomiting = cats.get("condition", {}).get("vomiting", "-")
        lines.append(
            f"{date}: 변상태={cv_class}, 산책={walk}분, 기력={energy}, 식욕={appetite}, 구토={vomiting}"
        )

    data_text = "\n".join(lines)
    system_prompt = (
        "너는 반려동물 건강 전문가야. "
        "일주일치 건강 데이터를 보고 전반적인 건강 추이와 "
        "개선 방향을 2~3문장으로 친근하게 설명해줘."
    )
    user_message = (
        f"아래는 반려동물의 최근 7일치 건강 데이터야:\n\n{data_text}\n\n"
        "전반적인 건강 상태와 개선 방향을 친근한 말투로 2~3문장으로 설명해줘."
    )

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "AI 코멘트를 불러올 수 없습니다. 잠시 후 다시 시도해주세요."
