from pathlib import Path

from meterweb.application.ports import OCRProvider, OCRResult
from meterweb.application.use_cases import OCRRunUseCase


class StubOCRProvider(OCRProvider):
    def __init__(self, text: str, confidence: float = 0.73) -> None:
        self._result = OCRResult(text=text, confidence=confidence)

    def extract_text(self, image_path: Path) -> OCRResult:
        del image_path
        return self._result


def test_ocr_run_use_case_prefers_integer_with_more_digits() -> None:
    use_case = OCRRunUseCase(StubOCRProvider("serial 2024 date 01.11 reading 49876"))

    result = use_case.execute(Path("dummy.jpg"))

    assert result.best_candidate is not None
    assert result.best_candidate.value == 49876


def test_ocr_run_use_case_prefers_larger_integer_when_digit_count_matches() -> None:
    use_case = OCRRunUseCase(StubOCRProvider("value 1234 alt 9876"))

    result = use_case.execute(Path("dummy.jpg"))

    assert result.best_candidate is not None
    assert result.best_candidate.value == 9876
