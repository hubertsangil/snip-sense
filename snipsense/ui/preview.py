"""Interactive desktop preview window displaying the captured screenshot with clipboard actions."""

import io
from PIL import Image
from PyQt6.QtCore import Qt, QTimer, QSize
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


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """Converts a PIL Image to a QPixmap with lossless fidelity."""
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    q_img = QImage.fromData(buffer.getvalue())
    return QPixmap.fromImage(q_img)


class PreviewWindow(QDialog):
    """Interactive preview dialog rendering the captured image and clipboard actions."""

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

        status_badge = QLabel("Captured")
        status_badge.setObjectName("statusBadge")
        header.addWidget(status_badge)

        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # 2. Central Image Scroll View
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setPixmap(self.pixmap)
        scroll.setWidget(self.image_label)

        layout.addWidget(scroll, stretch=1)

        # 3. Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        dim_label = QLabel(f"{self.capture_result.width} × {self.capture_result.height} px")
        dim_label.setObjectName("dimensionPill")
        bottom_bar.addWidget(dim_label)

        bottom_bar.addStretch()

        self.copy_btn = QPushButton("📋 Copy Image")
        self.copy_btn.setObjectName("primaryAction")
        self.copy_btn.clicked.connect(self.copy_image_to_clipboard)
        bottom_bar.addWidget(self.copy_btn)

        dismiss_btn = QPushButton("Close")
        dismiss_btn.setObjectName("ghostAction")
        dismiss_btn.clicked.connect(self.close)
        bottom_bar.addWidget(dismiss_btn)

        layout.addLayout(bottom_bar)

        # Determine reasonable dialog dimensions (clamped to screen size)
        img_w = self.capture_result.width
        img_h = self.capture_result.height
        target_w = max(450, min(img_w + 40, 960))
        target_h = max(350, min(img_h + 100, 680))
        self.resize(target_w, target_h)

    def _setup_shortcuts(self):
        # Ctrl+C triggers copy image
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_image_to_clipboard)

        # Esc or Ctrl+W closes window
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

    def copy_image_to_clipboard(self):
        """Copies the captured QPixmap directly onto the OS system clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.pixmap)

        # Visual feedback: update button text for 1.2 seconds
        self.copy_btn.setText("✓ Copied!")
        self.copy_btn.setStyleSheet("background-color: #059669; color: #FFFFFF;")
        QTimer.singleShot(1200, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.copy_btn.setText("📋 Copy Image")
        self.copy_btn.setStyleSheet("")
