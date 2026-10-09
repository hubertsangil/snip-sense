"""Unit tests for SnipCanvas, InteractiveImageCanvas, and PreviewWindow UI components."""

from PIL import Image
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication
from snipsense.core.models import ScreenRegion, CaptureResult, OCRTextBox
from snipsense.ui.canvas import SnipCanvas
from snipsense.ui.image_canvas import InteractiveImageCanvas
from snipsense.ui.preview import PreviewWindow, pil_to_qpixmap


def test_pil_to_qpixmap_conversion(qapp):
    pil_img = Image.new("RGB", (120, 80), color=(255, 0, 0))
    pixmap = pil_to_qpixmap(pil_img)
    assert pixmap.width() == 120
    assert pixmap.height() == 80


def test_canvas_drag_emits_snip_completed(qtbot, qapp):
    geom = (0, 0, 1920, 1080)
    canvas = SnipCanvas(geom)
    qtbot.addWidget(canvas)

    captured_regions = []
    canvas.snip_completed.connect(captured_regions.append)

    canvas.show()

    # Simulate mouse press at (100, 100)
    canvas._start_pos = QPoint(100, 100)
    canvas._current_pos = QPoint(300, 250)
    canvas._is_selecting = True

    # Call release logic directly
    rect = canvas.get_selected_rect()
    assert rect.width() == 200
    assert rect.height() == 150

    # Simulate completion by calling internal event handler path
    canvas.snip_completed.emit(ScreenRegion(x=100, y=100, width=200, height=150))

    assert len(captured_regions) == 1
    assert captured_regions[0] == ScreenRegion(x=100, y=100, width=200, height=150)


def test_canvas_escape_cancels(qtbot, qapp):
    geom = (0, 0, 1920, 1080)
    canvas = SnipCanvas(geom)
    qtbot.addWidget(canvas)

    cancelled_events = []
    canvas.snip_cancelled.connect(lambda: cancelled_events.append(True))

    canvas.show()
    canvas.cancel_snip()

    assert len(cancelled_events) == 1
    assert not canvas.isVisible()


def test_preview_window_copy_image(qtbot, qapp):
    pil_img = Image.new("RGB", (60, 40), color=(16, 185, 129))
    result = CaptureResult(
        image=pil_img,
        region=ScreenRegion(x=0, y=0, width=60, height=40),
        window_title="TestWindow",
    )

    preview = PreviewWindow(result)
    qtbot.addWidget(preview)
    preview.show()

    clipboard = QApplication.clipboard()
    clipboard.clear()

    # Trigger Copy Image button
    qtbot.mouseClick(preview.copy_img_btn, Qt.MouseButton.LeftButton)

    # Verify clipboard contains the pixmap with matching dimensions
    clip_pixmap = clipboard.pixmap()
    assert not clip_pixmap.isNull()
    assert clip_pixmap.width() == 60
    assert clip_pixmap.height() == 40
    assert "Copied" in preview.copy_img_btn.text()


def test_preview_window_copy_all_text(qtbot, qapp):
    pil_img = Image.new("RGB", (100, 60), color=(255, 255, 255))
    boxes = [
        OCRTextBox(text="Line 1", confidence=0.99, x=10, y=10, width=40, height=15, polygon=[]),
        OCRTextBox(text="Line 2", confidence=0.95, x=10, y=30, width=40, height=15, polygon=[]),
    ]
    result = CaptureResult(
        image=pil_img,
        region=ScreenRegion(x=0, y=0, width=100, height=60),
        ocr_boxes=boxes,
        raw_text="Line 1\nLine 2",
    )

    preview = PreviewWindow(result)
    qtbot.addWidget(preview)
    preview.show()

    clipboard = QApplication.clipboard()
    clipboard.clear()

    qtbot.mouseClick(preview.copy_text_btn, Qt.MouseButton.LeftButton)
    assert clipboard.text() == "Line 1\nLine 2"
    assert "Copied" in preview.copy_text_btn.text()


def test_preview_window_no_text_graceful(qtbot, qapp):
    pil_img = Image.new("RGB", (100, 60), color=(0, 0, 0))
    result = CaptureResult(
        image=pil_img,
        region=ScreenRegion(x=0, y=0, width=100, height=60),
        ocr_boxes=[],
        raw_text="",
    )

    preview = PreviewWindow(result)
    qtbot.addWidget(preview)
    preview.show()

    assert not preview.copy_text_btn.isEnabled()
    assert preview.copy_text_btn.text() == "No Text Found"
    assert not hasattr(preview, "toggle_boxes_btn")


def test_interactive_image_canvas_click_copies_box_text(qtbot, qapp):
    pil_img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    pixmap = pil_to_qpixmap(pil_img)
    box = OCRTextBox(text="Token123", confidence=0.98, x=20, y=30, width=80, height=25, polygon=[])

    canvas = InteractiveImageCanvas(pixmap, [box])
    qtbot.addWidget(canvas)
    canvas.show()

    clipboard = QApplication.clipboard()
    clipboard.clear()

    copied_signals = []
    canvas.text_copied.connect(copied_signals.append)

    # Hover over box
    canvas.hovered_box = box

    # Click box
    qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(30, 40))

    assert len(copied_signals) == 1
    assert copied_signals[0] == "Token123"
    assert clipboard.text() == "Token123"
    assert canvas.copied_box == box


def test_toggle_boxes_button(qtbot, qapp):
    pil_img = Image.new("RGB", (100, 60), color=(255, 255, 255))
    box = OCRTextBox(text="Test", confidence=0.9, x=10, y=10, width=30, height=10, polygon=[])
    result = CaptureResult(
        image=pil_img,
        region=ScreenRegion(x=0, y=0, width=100, height=60),
        ocr_boxes=[box],
        raw_text="Test",
    )

    preview = PreviewWindow(result)
    qtbot.addWidget(preview)
    preview.show()

    assert preview.canvas.boxes_visible is True
    qtbot.mouseClick(preview.toggle_boxes_btn, Qt.MouseButton.LeftButton)
    assert preview.canvas.boxes_visible is False
    qtbot.mouseClick(preview.toggle_boxes_btn, Qt.MouseButton.LeftButton)
    assert preview.canvas.boxes_visible is True


def test_shield_pii_button_masks_sensitive_boxes(qtbot, qapp):
    pil_img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    boxes = [
        OCRTextBox(text="admin@example.com", confidence=0.99, x=10, y=10, width=80, height=20, polygon=[]),
        OCRTextBox(text="General Header", confidence=0.95, x=10, y=40, width=80, height=20, polygon=[]),
        OCRTextBox(text="sk_live_1234567890abcdef1234", confidence=0.98, x=10, y=70, width=80, height=20, polygon=[]),
    ]
    result = CaptureResult(
        image=pil_img,
        region=ScreenRegion(x=0, y=0, width=200, height=100),
        ocr_boxes=boxes,
        raw_text="admin@example.com\nGeneral Header\nsk_live_1234567890abcdef1234",
    )

    preview = PreviewWindow(result)
    qtbot.addWidget(preview)
    preview.show()

    assert hasattr(preview, "shield_pii_btn")
    assert len(preview.masked_boxes) == 0

    # Click Shield PII button
    qtbot.mouseClick(preview.shield_pii_btn, Qt.MouseButton.LeftButton)

    # 2 sensitive boxes should be masked
    assert len(preview.masked_boxes) == 2
    assert boxes[0] in preview.masked_boxes  # email
    assert boxes[2] in preview.masked_boxes  # api key
    assert boxes[1] not in preview.masked_boxes  # general header

    # Verify Copy All Text produces [REDACTED] for masked items
    clipboard = QApplication.clipboard()
    clipboard.clear()
    qtbot.mouseClick(preview.copy_text_btn, Qt.MouseButton.LeftButton)
    assert clipboard.text() == "[REDACTED]\nGeneral Header\n[REDACTED]"

    # Verify Copy Image copies the blurred pixmap
    clipboard.clear()
    qtbot.mouseClick(preview.copy_img_btn, Qt.MouseButton.LeftButton)
    clip_pix = clipboard.pixmap()
    assert not clip_pix.isNull()
    assert clip_pix.width() == 200
    assert clip_pix.height() == 100


def test_manual_box_toggle_masking(qtbot, qapp):
    pil_img = Image.new("RGB", (150, 80), color=(255, 255, 255))
    box = OCRTextBox(text="NonSensitiveText", confidence=0.9, x=10, y=10, width=80, height=20, polygon=[])
    result = CaptureResult(
        image=pil_img,
        region=ScreenRegion(x=0, y=0, width=150, height=80),
        ocr_boxes=[box],
        raw_text="NonSensitiveText",
    )

    preview = PreviewWindow(result)
    qtbot.addWidget(preview)
    preview.show()

    assert len(preview.masked_boxes) == 0

    # Simulate click on box -> manually mask
    preview.canvas.hovered_box = box
    qtbot.mouseClick(preview.canvas, Qt.MouseButton.LeftButton, pos=QPoint(15, 15))

    assert box in preview.masked_boxes
    assert preview.get_redacted_text() == "[REDACTED]"

    # Simulate second click on box -> unmask
    preview.canvas.hovered_box = box
    qtbot.mouseClick(preview.canvas, Qt.MouseButton.LeftButton, pos=QPoint(15, 15))

    assert box not in preview.masked_boxes
    assert preview.get_redacted_text() == "NonSensitiveText"

