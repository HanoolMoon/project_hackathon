"""
LLM 조언 모듈 테스트.
GPT API 호출을 모의(mock)하여 llm_advisor와 health_report를 단독으로 테스트한다.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestLlmAdvisor(unittest.TestCase):

    def _make_cv_result(self, cv_class: str = "normal", confidence: float = 0.92) -> dict:
        return {
            "class": cv_class,
            "confidence": confidence,
            "bristol_grade": "3~4",
            "description": "정상적인 변 형태",
        }

    def _make_pet_profile(self) -> dict:
        return {
            "name": "초코",
            "species": "개",
            "age": 3.0,
            "weight": 5.5,
            "neutered": True,
            "food_type": "건식",
        }

    def test_get_advice_returns_string(self) -> None:
        """get_advice가 문자열을 반환해야 한다."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "정상적인 변이므로 걱정하지 않아도 됩니다."

        with (
            patch("core.llm_advisor._get_client") as mock_client_fn,
            patch("core.llm_advisor._read_prompt_file", return_value="test prompt"),
        ):
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            from core.llm_advisor import get_advice
            result = get_advice(self._make_cv_result(), self._make_pet_profile())

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_get_advice_unknown_class_skips_api(self) -> None:
        """class가 'unknown'이면 API 호출 없이 안내 메시지를 반환해야 한다."""
        unknown_cv = {"class": "unknown", "confidence": 0.45, "bristol_grade": "판단 불가"}

        with patch("core.llm_advisor._get_client") as mock_client_fn:
            from core.llm_advisor import get_advice
            result = get_advice(unknown_cv, self._make_pet_profile())

        mock_client_fn.assert_not_called()
        self.assertIn("신뢰도", result)

    def test_get_advice_missing_api_key(self) -> None:
        """API 키가 없으면 EnvironmentError를 발생시켜야 한다."""
        with patch("core.llm_advisor._get_client", side_effect=EnvironmentError("[오류] OPENAI_API_KEY")):
            from core.llm_advisor import get_advice
            with self.assertRaises(EnvironmentError):
                get_advice(self._make_cv_result(), self._make_pet_profile())


class TestHealthReport(unittest.TestCase):

    def _make_report(self) -> dict:
        return {
            "pet_profile": {"name": "초코", "species": "개", "age": 3.0, "weight": 5.5,
                            "neutered": True, "food_type": "건식"},
            "cv_result": {"class": "normal", "confidence": 0.92,
                          "bristol_grade": "3~4", "description": "정상적인 변"},
            "advice": "건강한 상태입니다. 현재 식단을 유지하세요.",
        }

    def test_build_report_structure(self) -> None:
        """build_report가 올바른 키를 가진 딕셔너리를 반환해야 한다."""
        from core.health_report import build_report

        report = build_report(
            pet_profile=self._make_report()["pet_profile"],
            cv_result=self._make_report()["cv_result"],
            advice="테스트 조언",
        )

        self.assertIn("pet_profile", report)
        self.assertIn("cv_result", report)
        self.assertIn("advice", report)
        self.assertNotIn("timestamp", report)

    def test_print_report_no_error(self) -> None:
        """print_report가 예외 없이 실행되어야 한다."""
        from core.health_report import print_report

        try:
            print_report(self._make_report())
        except Exception as e:
            self.fail(f"print_report가 예외를 발생시켰습니다: {e}")


if __name__ == "__main__":
    unittest.main()
