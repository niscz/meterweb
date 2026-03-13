from pathlib import Path

from meterweb.application.ports import OCRProvider, OCRResult


class LocalTesseractOCRProvider(OCRProvider):
    def __init__(self, language: str = "deu") -> None:
        self._language = language

    def extract_text(self, image_path: Path) -> OCRResult:
        try:
            import cv2
            import pytesseract
        except ImportError as exc:  # pragma: no cover - depends on runtime system deps
            raise RuntimeError(
                "Lokaler OCR-Provider benötigt OpenCV (cv2) und pytesseract."
            ) from exc

        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Bild konnte nicht gelesen werden: {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        data = pytesseract.image_to_data(
            thresh,
            lang=self._language,
            output_type=pytesseract.Output.DICT,
        )
        words = [word for word in data.get("text", []) if word.strip()]
        confidences = [
            float(conf)
            for conf in data.get("conf", [])
            if conf not in {"-1", -1} and str(conf).strip()
        ]
        text = " ".join(words).strip()
        confidence = (sum(confidences) / len(confidences)) / 100 if confidences else 0.0
        return OCRResult(text=text, confidence=confidence)
