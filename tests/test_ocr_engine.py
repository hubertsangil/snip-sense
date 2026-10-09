"""Unit tests for the in-process OCREngine and OCRTextBox data model."""

import numpy as np
from PIL import Image, ImageDraw
from snipsense.core.models import OCRTextBox
from snipsense.core.ocr_engine import OCREngine


def test_ocr_text_box_contains_point():
    box = OCRTextBox(
        text="Sample",
        confidence=0.95,
        x=50,
        y=100,
        width=150,
        height=30,
        polygon=[(50.0, 100.0), (200.0, 100.0), (200.0, 130.0), (50.0, 130.0)],
    )

    # Inside box
    assert box.contains_point(50, 100) is True
    assert box.contains_point(100, 115) is True
    assert box.contains_point(200, 130) is True

    # Outside box
    assert box.contains_point(49, 100) is False
    assert box.contains_point(100, 99) is False
    assert box.contains_point(201, 115) is False
    assert box.contains_point(100, 131) is False


def test_ocr_engine_singleton():
    inst1 = OCREngine.get_instance()
    inst2 = OCREngine.get_instance()
    assert inst1 is inst2


def test_ocr_engine_extracts_rendered_text():
    # Generate synthetic image with clear high-contrast text
    img = Image.new("RGB", (400, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "SnipSense OCR Engine", fill=(0, 0, 0))

    engine = OCREngine.get_instance()
    boxes, raw_text = engine.extract_text(img)

    assert len(boxes) >= 1
    assert "SnipSense" in raw_text or "Engine" in raw_text or "OCR" in raw_text
    
    first_box = boxes[0]
    assert first_box.width > 10
    assert first_box.height > 5
    assert first_box.confidence > 0.5
    assert len(first_box.polygon) == 4


def test_ocr_engine_blank_image_returns_empty():
    blank = Image.new("RGB", (300, 150), color=(20, 20, 20))
    engine = OCREngine.get_instance()
    boxes, raw_text = engine.extract_text(blank)

    assert boxes == []
    assert raw_text == ""
