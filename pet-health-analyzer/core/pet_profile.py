"""
반려동물 프로필 입력 모듈.
실행 시마다 CLI로 반려동물 정보를 입력받아 딕셔너리로 반환한다.
저장·로드 기능 없이 단순 입력 전용으로 동작한다.
"""

from typing import Any


def setup_profile() -> dict[str, Any]:
    """CLI로 반려동물 정보를 입력받아 딕셔너리로 반환한다."""
    print("\n반려동물 정보를 입력해주세요.")

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

    return {
        "name": name,
        "species": species,
        "age": age,
        "weight": weight,
        "neutered": neutered,
        "food_type": food_type,
    }
