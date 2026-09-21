"""
Screen OCR Scanner:
Local CPU-optimized Optical Character Recognition to extract text from custom canvas,
Electron, or graphic interfaces where the UI Automation tree is not available.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from core.config import PROJECT_ROOT
from core.logger import logger, log_latency

class ScreenOCRScanner:
    def __init__(self):
        self._ocr_engine = None
        self._init_ocr()

    def _init_ocr(self) -> None:
        """Initialize RapidOCR or lightweight fallback."""
        try:
            from rapidocr_onnxruntime import RapidOCR
            with log_latency("OCR._init_rapidocr"):
                self._ocr_engine = RapidOCR()
            logger.info("[AWARENESS] RapidOCR engine initialized.")
        except Exception:
            try:
                import pytesseract
                self._ocr_engine = "tesseract"
                logger.info("[AWARENESS] PyTesseract engine initialized.")
            except Exception:
                logger.debug("[AWARENESS] OCR engine not installed. OCR tool available in mock/fallback mode.")

    def extract_text_from_image(self, image_path: Path) -> List[Dict[str, Any]]:
        """Extract text lines and bounding boxes from an image file."""
        if not image_path.exists():
            return []

        results = []
        with log_latency("OCR.extract_text_from_image", image_path.name):
            try:
                if hasattr(self._ocr_engine, "__call__"):
                    ocr_results, _ = self._ocr_engine(str(image_path))
                    if ocr_results:
                        for item in ocr_results:
                            bbox, text, score = item
                            results.append({"text": text.strip(), "confidence": round(float(score), 2), "bbox": bbox})
                elif self._ocr_engine == "tesseract":
                    from PIL import Image
                    import pytesseract
                    img = Image.open(image_path)
                    text = pytesseract.image_to_string(img)
                    for line in text.splitlines():
                        if line.strip():
                            results.append({"text": line.strip(), "confidence": 0.9, "bbox": None})
            except Exception as e:
                logger.error(f"[AWARENESS] OCR extraction failed: {e}")

        return results

    def capture_screen(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Capture full screen or active window screenshot."""
        save_path = output_path or (PROJECT_ROOT / "data" / "screenshots" / "latest_screen.png")
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(save_path)
            return save_path
        except Exception as e:
            logger.error(f"[AWARENESS] Screenshot capture failed: {e}")
            return None
