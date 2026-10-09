"""In-process Optical Character Recognition engine using RapidOCR ONNX."""

from typing import Optional
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
from snipsense.core.models import OCRTextBox


class OCREngine:
    """Embedded, in-process OCR engine for extracting text and bounding polygons from images."""

    _instance: Optional["OCREngine"] = None

    @classmethod
    def get_instance(cls) -> "OCREngine":
        """Returns a cached singleton instance of OCREngine to avoid re-initializing models."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Initializes RapidOCR with default embedded ONNX models (det + rec)
        self._engine = RapidOCR()

    def extract_text(self, image: Image.Image) -> tuple[list[OCRTextBox], str]:
        """Runs OCR inference on a PIL image and extracts bounding boxes and structured text.
        
        Args:
            image: PIL Image instance (RGB or RGBA).

        Returns:
            Tuple of (list of OCRTextBox, raw concatenated text string).
        """
        try:
            # Convert PIL Image to RGB numpy array
            rgb_img = image.convert("RGB")
            img_np = np.array(rgb_img)

            # RapidOCR returns: results (list of [box, text, score]) and elapse time
            results, _ = self._engine(img_np)
            if not results:
                return [], ""

            boxes: list[OCRTextBox] = []
            lines: list[str] = []

            for item in results:
                if len(item) < 3:
                    continue
                poly = item[0]
                text = str(item[1]).strip()
                score_raw = item[2]

                if not text:
                    continue

                try:
                    confidence = float(score_raw)
                except (ValueError, TypeError):
                    confidence = 0.0

                # Compute normalized bounding box (x, y, w, h) from 4 polygon vertices
                xs = [float(p[0]) for p in poly]
                ys = [float(p[1]) for p in poly]
                min_x = int(round(min(xs)))
                max_x = int(round(max(xs)))
                min_y = int(round(min(ys)))
                max_y = int(round(max(ys)))

                width = max(1, max_x - min_x)
                height = max(1, max_y - min_y)

                box = OCRTextBox(
                    text=text,
                    confidence=confidence,
                    x=min_x,
                    y=min_y,
                    width=width,
                    height=height,
                    polygon=[(float(p[0]), float(p[1])) for p in poly],
                )
                boxes.append(box)
                lines.append(text)

            raw_text = "\n".join(lines)
            return boxes, raw_text

        except Exception:
            # Graceful fallback: return empty result without crashing the application
            return [], ""
