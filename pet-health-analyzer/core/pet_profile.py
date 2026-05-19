"""
반려동물 프로필 관리 모듈.
CLI를 통해 프로필을 입력받아 JSON 파일에 저장하고, 저장된 프로필을 로드한다.
여러 마리의 반려동물을 리스트 구조로 관리한다.
"""

import json
from pathlib import Path
from typing import Any

from config.settings import PET_PROFILE_PATH


def _load_raw() -> list[dict[str, Any]]:
    """JSON 파일에서 프로필 리스트를 불러온다. 파일이 없으면 빈 리스트 반환."""
    path = Path(PET_PROFILE_PATH)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_raw(profiles: list[dict[str, Any]]) -> None:
    """프로필 리스트를 JSON 파일에 저장한다."""
    path = Path(PET_PROFILE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def setup_profile() -> dict[str, Any]:
    """CLI로 반려동물 정보를 입력받아 저장하고 해당 프로필을 반환한다."""
    print("\n반려동물 프로필을 등록합니다.")

    name = input("  이름: ").strip()

    print("  종 선택: 1) 개  2) 고양이  3) 기타")
    species_map = {"1": "개", "2": "고양이", "3": "기타"}
    species_input = input("  번호 입력: ").strip()
    species = species_map.get(species_input, "기타")

    while True:
        try:
            age = float(input("  나이 (세): ").strip())
            break
        except ValueError:
            print("  숫자로 입력해주세요.")

    while True:
        try:
            weight = float(input("  체중 (kg): ").strip())
            break
        except ValueError:
            print("  숫자로 입력해주세요.")

    neutered_input = input("  중성화 여부 (y/n): ").strip().lower()
    neutered = neutered_input == "y"

    food_type = input("  평소 사료 종류 (예: 건식, 습식, 생식): ").strip()

    profile: dict[str, Any] = {
        "name": name,
        "species": species,
        "age": age,
        "weight": weight,
        "neutered": neutered,
        "food_type": food_type,
    }

    profiles = _load_raw()
    profiles.append(profile)
    _save_raw(profiles)

    print(f"\n  '{name}' 프로필이 저장되었습니다.\n")
    return profile


def load_profile(index: int = 0) -> dict[str, Any]:
    """저장된 프로필을 인덱스로 로드한다. 없으면 setup_profile()을 자동 호출한다."""
    profiles = _load_raw()
    if not profiles:
        print("저장된 프로필이 없습니다. 새 프로필을 등록합니다.")
        return setup_profile()

    if index >= len(profiles):
        print(
            f"[오류] 인덱스 {index}에 해당하는 프로필이 없습니다. "
            f"(저장된 프로필 수: {len(profiles)})"
        )
        print("첫 번째 프로필을 사용합니다.")
        index = 0

    return profiles[index]


def list_profiles() -> list[dict[str, Any]]:
    """저장된 모든 프로필을 반환한다."""
    return _load_raw()
