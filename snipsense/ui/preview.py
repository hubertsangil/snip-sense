"""Interactive desktop preview window displaying the captured screenshot with OCR bounding boxes."""

import io
from PIL import Image
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QApplication,
)
from snipsense.core.models import CaptureResult
from snipsense.ui.styles import DARK_THEME_QSS
from snipsense.ui.image_canvas import InteractiveImageCanvas


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """Converts a PIL Image to a QPixmap with lossless fidelity."""
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    q_img = QImage.fromData(buffer.getvalue())
    return QPixmap.fromImage(q_img)


class PreviewWindow(QDialog):
    """Interactive preview dialog rendering the captured image, OCR bounding boxes, and clipboard actions."""

    def __init__(self, capture_result: CaptureResult, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("previewWindow")
        self.setStyleSheet(DARK_THEME_QSS)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.capture_result = capture_result
        self.pixmap = pil_to_qpixmap(capture_result.image)

        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self):
        self.setWindowTitle("SnipSense — Capture Preview")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # 1. Top Header Bar
        header = QHBoxLayout()
        header.setSpacing(8)

        title_label = QLabel("SnipSense Preview")
        title_label.setObjectName("headerTitle")
        header.addWidget(title_label)

        line_count = len(self.capture_result.ocr_boxes)
        badge_text = f"{line_count} text {'blocks' if line_count != 1 else 'block'} detected" if line_count > 0 else "Captured"
        self.status_badge = QLabel(badge_text)
        self.status_badge.setObjectName("statusBadge")
        header.addWidget(self.status_badge)

        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # 2. Central Scrollable Image Canvas with Interactive OCR Boxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas = InteractiveImageCanvas(self.pixmap, self.capture_result.ocr_boxes)
        self.canvas.text_copied.connect(self._on_snippet_copied)
        scroll.setWidget(self.canvas)

        layout.addWidget(scroll, stretch=1)

        # 3. Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        dim_label = QLabel(f"{self.capture_result.width} × {self.capture_result.height} px")
        dim_label.setObjectName("dimensionPill")
        bottom_bar.addWidget(dim_label)

        # Toggle Text Box Overlays Button
        if self.capture_result.ocr_boxes:
            self.toggle_boxes_btn = QPushButton("👁️ Boxes")
            self.toggle_boxes_btn.setObjectName("ghostAction")
            self.toggle_boxes_btn.setCheckable(True)
            self.toggle_boxes_btn.setChecked(True)
            self.toggle_boxes_btn.clicked.connect(self._toggle_boxes)
            bottom_bar.addWidget(self.toggle_boxes_btn)

        bottom_bar.addStretch()

        # Copy All Text Button
        self.copy_text_btn = QPushButton("📋 Copy All Text")
        self.copy_text_btn.setObjectName("ghostAction")
        if self.capture_result.raw_text.strip():
            self.copy_text_btn.clicked.connect(self.copy_all_text_to_clipboard)
        else:
            self.copy_text_btn.setText("No Text Found")
            self.copy_text_btn.setEnabled(False)
        bottom_bar.addWidget(self.copy_text_btn)

        # Copy Image Button (Primary Action)
        self.copy_img_btn = QPushButton("🖼️ Copy Image")
        self.copy_img_btn.setObjectName("primaryAction")
        self.copy_img_btn.clicked.connect(self.copy_image_to_clipboard)
        bottom_bar.addWidget(self.copy_img_btn)

        dismiss_btn = QPushButton("Close")
        dismiss_btn.setObjectName("ghostAction")
        dismiss_btn.clicked.connect(self.close)
        bottom_bar.addWidget(dismiss_btn)

        layout.addLayout(bottom_bar)

        # Clamped initial dialog dimensions
        img_w = self.capture_result.width
        img_h = self.capture_result.height
        target_w = max(520, min(img_w + 40, 1020))
        target_h = max(380, min(img_h + 110, 720))
        self.resize(target_w, target_h)

    def _setup_shortcuts(self):
        copy_img_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_img_shortcut.activated.connect(self.copy_image_to_clipboard)

        if self.capture_result.raw_text.strip():
            copy_text_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
            copy_text_shortcut.activated.connect(self.copy_all_text_to_clipboard)

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

    def _toggle_boxes(self):
        """Toggles rendering of the OCR bounding boxes on the canvas."""
        is_visible = self.toggle_boxes_btn.isChecked()
        self.canvas.set_boxes_visible(is_visible)

    def _on_snippet_copied(self, text: str):
        """Displays transient visual confirmation in the header when a specific text box is clicked."""
        truncated = text if len(text) <= 30 else text[:27] + "..."
        orig_text = self.status_badge.text()
        self.status_badge.setText(f"✓ Copied: \"{truncated}\"")
        self.status_badge.setStyleSheet("background-color: rgba(16, 185, 129, 0.35); color: #FFFFFF;")

        def _restore():
            self.status_badge.setText(orig_text)
            self.status_badge.setStyleSheet("")

        QTimer.singleShot(1400, _restore)

    def copy_image_to_clipboard(self):
        """Copies the captured QPixmap onto the system clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.pixmap)

        self.copy_img_btn.setText("✓ Copied Image!")
        self.copy_img_btn.setStyleSheet("background-color: #059669; color: #FFFFFF;")
        QTimer.singleShot(1200, self._reset_copy_img_btn)

    def _reset_copy_img_btn(self):
        self.copy_img_btn.setText("🖼️ Copy Image")
        self.copy_img_btn.setStyleSheet("")

    def copy_all_text_to_clipboard(self):
        """Copies all recognized OCR lines into the clipboard as formatted plain text."""
        if not self.capture_result.raw_text.strip():
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self.capture_result.raw_text)

        self.copy_text_btn.setText("✓ Copied All Text!")
        self.copy_text_btn.setStyleSheet("background-color: #059669; color: #FFFFFF;")
        QTimer.singleShot(1200, self._reset_copy_text_btn)

    def _reset_copy_text_btn(self):
        self.copy_text_btn.setText("📋 Copy All Text")
        self.copy_text_btn.setStyleSheet("")
