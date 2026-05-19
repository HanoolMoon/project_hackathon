"""
CV 분석 모듈 테스트.
model_loader와 cv_analyzer를 단독으로 테스트한다.
실제 pkl 파일 없이 모의 모델로 핵심 로직만 검증한다.
"""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestModelLoader(unittest.TestCase):

    def test_predict_returns_unknown_below_threshold(self) -> None:
        """신뢰도가 임계값 미만이면 class가 'unknown'이어야 한다."""
        import torch
        import torch.nn as nn

        fake_model = MagicMock(spec=nn.Module)
        low_confidence_output = torch.tensor([[0.30, 0.25, 0.25, 0.20]])
        fake_model.return_value = low_confidence_output
        fake_model.eval = MagicMock(return_value=fake_model)

        with (
            patch("models.model_loader._model_cache", None),
            patch("models.model_loader.load_model", return_value=fake_model),
            patch("PIL.Image.open") as mock_open,
        ):
            mock_img = MagicMock()
            mock_img.convert.return_value = mock_img
            mock_open.return_value = mock_img

            from models.model_loader import predict

            with patch("pathlib.Path.exists", return_value=True):
                result = predict("fake/path/image.jpg")

        self.assertEqual(result["class"], "unknown")
        self.assertLess(result["confidence"], 0.70)

    def test_predict_returns_valid_class_above_threshold(self) -> None:
        """신뢰도가 임계값 이상이면 유효한 클래스를 반환해야 한다."""
        import torch
        import torch.nn as nn

        from config.settings import CLASSES

        fake_model = MagicMock(spec=nn.Module)
        high_confidence_output = torch.tensor([[0.91, 0.03, 0.03, 0.03]])
        fake_model.return_value = high_confidence_output
        fake_model.eval = MagicMock(return_value=fake_model)

        with (
            patch("models.model_loader.load_model", return_value=fake_model),
            patch("PIL.Image.open") as mock_open,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_img = MagicMock()
            mock_img.convert.return_value = mock_img
            mock_open.return_value = mock_img

            from models.model_loader import predict

            result = predict("fake/path/image.jpg")

        self.assertIn(result["class"], CLASSES)
        self.assertGreaterEqual(result["confidence"], 0.70)

    def test_predict_raises_on_missing_image(self) -> None:
        """존재하지 않는 이미지 경로면 FileNotFoundError가 발생해야 한다."""
        from models.model_loader import predict

        with self.assertRaises(FileNotFoundError):
            predict("nonexistent/path/image.jpg")


class TestCvAnalyzer(unittest.TestCase):

    def test_analyze_unknown_class_on_low_confidence(self) -> None:
        """신뢰도 미달 시 analyze가 'unknown' 결과를 반환해야 한다."""
        mock_predict_result = {"class": "unknown", "confidence": 0.50}

        with patch("core.cv_analyzer.predict", return_value=mock_predict_result):
            from core.cv_analyzer import analyze
            result = analyze("fake/image.jpg")

        self.assertEqual(result["class"], "unknown")
        self.assertEqual(result["bristol_grade"], "판단 불가")

    def test_analyze_normal_class(self) -> None:
        """normal 분류 시 Bristol 등급이 3~4이어야 한다."""
        mock_predict_result = {"class": "normal", "confidence": 0.92}

        with patch("core.cv_analyzer.predict", return_value=mock_predict_result):
            from core.cv_analyzer import analyze
            result = analyze("fake/image.jpg")

        self.assertEqual(result["class"], "normal")
        self.assertEqual(result["bristol_grade"], "3~4")

    def test_analyze_diarrhea_class(self) -> None:
        """diarrhea 분류 시 Bristol 등급이 7이어야 한다."""
        mock_predict_result = {"class": "diarrhea", "confidence": 0.88}

        with patch("core.cv_analyzer.predict", return_value=mock_predict_result):
            from core.cv_analyzer import analyze
            result = analyze("fake/image.jpg")

        self.assertEqual(result["bristol_grade"], "7")

    def test_analyze_lack_of_water_class(self) -> None:
        """lack-of-water 분류 시 Bristol 등급이 1~2이어야 한다."""
        mock_predict_result = {"class": "lack-of-water", "confidence": 0.75}

        with patch("core.cv_analyzer.predict", return_value=mock_predict_result):
            from core.cv_analyzer import analyze
            result = analyze("fake/image.jpg")

        self.assertEqual(result["bristol_grade"], "1~2")


if __name__ == "__main__":
    unittest.main()
