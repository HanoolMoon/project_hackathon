"""
반려동물 프로필 관리 모듈.
config/pet_config.json을 읽어 프로필을 반환하며,
파일이 없거나 이름이 비어있을 때만 CLI로 입력을 받아 저장한다.
"""

import json
from pathlib import Path
from typing import Any

from config.settings import PET_CONFIG_PATH


def setup_profile() -> dict[str, Any]:
    """CLI로 반려동물 정보를 입력받아 config/pet_config.json에 저장한 후 반환한다."""
    print("\n반려동물 정보를 처음 등록합니다.")

    name = input("  이름: ").strip()

    print("  종 선택: 1) 개  2) 고양이  3) 기타")
    species_map = {"1": "개", "2": "고양이", "3": "기타"}
    species = species_map.get(input("  번호 입력: ").strip(), "기타")

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

    neutered = input("  중성화 여부 (y/n): ").strip().lower() == "y"
    food_type = input("  평소 사료 종류 (예: 건식, 습식, 생식): ").strip()

    profile: dict[str, Any] = {
        "name": name,
        "species": species,
        "age": age,
        "weight": weight,
        "neutered": neutered,
        "food_type": food_type,
    }

    path = Path(PET_CONFIG_PATH)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print(f"\n  '{name}' 정보가 저장되었습니다. 이후 실행부터는 자동으로 불러옵니다.\n")
    return profile


def load_profile() -> dict[str, Any]:
    """config/pet_config.json을 읽어 반환한다.
    파일이 없거나 name이 비어있으면 setup_profile()을 자동 호출한다.
    """
    path = Path(PET_CONFIG_PATH)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("name", "").strip():
                return data
        except (json.JSONDecodeError, OSError):
            pass

    return setup_profile()
