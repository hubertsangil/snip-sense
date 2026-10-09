"""Interactive desktop preview window displaying the captured screenshot with OCR bounding boxes and save actions."""

from __future__ import annotations
import io
from pathlib import Path
from PIL import Image
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QWidget,
    QApplication,
)
from snipsense.core.models import CaptureResult
from snipsense.core.storage import StorageManager
from snipsense.core.vault import VaultDatabase
from snipsense.ui.styles import DARK_THEME_QSS
from snipsense.ui.image_canvas import InteractiveImageCanvas


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """Converts a PIL Image to a QPixmap with lossless fidelity."""
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    q_img = QImage.fromData(buffer.getvalue())
    return QPixmap.fromImage(q_img)


class PreviewWindow(QDialog):
    """Interactive preview dialog rendering the captured image, OCR bounding boxes, and save/clipboard actions."""

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
        self.storage = StorageManager()
        self.saved_path: Path | None = None

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

        # 3. Filename & Disk Save Bar
        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        name_label = QLabel("Save As:")
        name_label.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")
        name_row.addWidget(name_label)

        initial_name = self.capture_result.suggested_filename or "Snip.png"
        self.name_edit = QLineEdit(initial_name)
        self.name_edit.setObjectName("slugEdit")
        self.name_edit.setPlaceholderText("Enter filename...")
        self.name_edit.returnPressed.connect(self.save_image_to_disk)
        name_row.addWidget(self.name_edit, stretch=1)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setObjectName("primaryAction")
        self.save_btn.clicked.connect(self.save_image_to_disk)
        name_row.addWidget(self.save_btn)

        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.open_folder_btn.setObjectName("ghostAction")
        self.open_folder_btn.setVisible(False)
        self.open_folder_btn.clicked.connect(self._open_saved_location)
        name_row.addWidget(self.open_folder_btn)

        layout.addLayout(name_row)

        # 4. Bottom Action Bar
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

        # Copy Image Button
        self.copy_img_btn = QPushButton("🖼️ Copy Image")
        self.copy_img_btn.setObjectName("ghostAction")
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
        target_w = max(560, min(img_w + 40, 1020))
        target_h = max(420, min(img_h + 150, 740))
        self.resize(target_w, target_h)

    def _setup_shortcuts(self):
        copy_img_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_img_shortcut.activated.connect(self.copy_image_to_clipboard)

        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_image_to_disk)

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

    def save_image_to_disk(self):
        """Saves the captured image to disk using the filename in the text field."""
        filename = self.name_edit.text().strip() or "Snip.png"
        saved = self.storage.save_image(self.capture_result.image, filename)
        self.saved_path = saved

        # Automatically index capture into SQLite FTS5 Visual Memory
        try:
            VaultDatabase.get_instance().index_capture(
                file_path=saved,
                title=saved.stem,
                ocr_text=self.capture_result.raw_text,
                tags="",
                window_title=self.capture_result.window_title or "",
                created_at=self.capture_result.timestamp,
            )
        except Exception:
            pass

        # Update input field to reflect actual saved file name (e.g. if suffix was incremented)
        self.name_edit.setText(saved.name)

        # Show visual confirmation
        self.save_btn.setText("✓ Saved!")
        self.save_btn.setStyleSheet("background-color: #059669; color: #FFFFFF;")
        self.open_folder_btn.setVisible(True)

        self.status_badge.setText(f"✓ Saved to {saved.parent.name}/{saved.name}")
        self.status_badge.setStyleSheet("background-color: rgba(16, 185, 129, 0.25); color: #10B981;")

        QTimer.singleShot(1800, self._reset_save_btn)

    def _reset_save_btn(self):
        self.save_btn.setText("💾 Save")
        self.save_btn.setStyleSheet("")

    def _open_saved_location(self):
        """Opens the saved file in the system file explorer."""
        if self.saved_path and self.saved_path.exists():
            self.storage.open_in_explorer(self.saved_path)
        else:
            self.storage.open_in_explorer(self.storage.base_directory)

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
