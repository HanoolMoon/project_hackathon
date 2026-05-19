"""
Pet Health Analyzer CLI 진입점.
usage: python main.py --image <이미지 경로>
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / "config" / ".env")

from core.cv_analyzer import analyze
from core.health_report import build_report, print_report
from core.llm_advisor import get_advice
from core.pet_profile import setup_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="반려동물 대변 사진으로 건강 상태를 분석합니다."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="분석할 이미지 파일 경로 (예: ./data/input_images/photo.jpg)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_path = args.image

    if not Path(image_path).exists():
        print(f"\n[오류] 이미지 파일을 찾을 수 없습니다: {image_path}")
        print("  --image 옵션에 올바른 파일 경로를 입력해주세요.")
        sys.exit(1)

    pet_profile = setup_profile()

    print("\n  이미지를 분석하는 중...")
    try:
        cv_result = analyze(image_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"[오류] CV 분석 실패: {e}")
        sys.exit(1)

    if cv_result["class"] == "unknown":
        print(
            f"\n  [판단 불가] 모델 신뢰도({cv_result['confidence']:.1%})가 "
            "기준치(70%)에 미달합니다."
        )
        print("  더 선명하고 가까운 사진으로 다시 시도해주세요.\n")

    print(f"  분석 완료: {cv_result['class']} (신뢰도 {cv_result['confidence']:.1%})")

    print("\n  AI 조언을 생성하는 중...")
    try:
        advice = get_advice(cv_result, pet_profile)
    except EnvironmentError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"[오류] AI 조언 생성 실패: {e}")
        sys.exit(1)

    report = build_report(pet_profile, cv_result, advice)
    print_report(report)


if __name__ == "__main__":
    main()
