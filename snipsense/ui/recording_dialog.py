"""Completion banner and action dialog for saved GIF/MP4 screen recordings."""

from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices, QClipboard, QImage
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
)
from PIL import Image

from snipsense.core.recorder import RecordingResult
from snipsense.ui.styles import DARK_THEME_QSS


def format_bytes(byte_count: int) -> str:
    """Formats raw byte counts to KB/MB."""
    if byte_count < 1024:
        return f"{byte_count} B"
    elif byte_count < 1024 * 1024:
        return f"{byte_count / 1024:.1f} KB"
    else:
        return f"{byte_count / (1024 * 1024):.1f} MB"


class RecordingCompletedDialog(QDialog):
    """Modal dialog presenting the completed screen recording with quick-share actions."""

    def __init__(
        self,
        encoded_files: Dict[str, Path],
        result: RecordingResult,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.encoded_files = encoded_files
        self.result = result

        self.setWindowTitle("Screen Clip Ready")
        self.setObjectName("previewWindow")
        self.setStyleSheet(DARK_THEME_QSS)
        self.setFixedSize(500, 360)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_label = QLabel("🎬 Screen Clip Recorded")
        title_label.setObjectName("headerTitle")
        header.addWidget(title_label)

        status_badge = QLabel("Saved")
        status_badge.setObjectName("statusBadge")
        header.addWidget(status_badge)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.accept)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Main Card Frame
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1A202C;
                border: 1px solid #2D3748;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(14)

        # Thumbnail Preview
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 110)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #0B0D10; border-radius: 6px;")

        if self.result.frames:
            first_frame = self.result.frames[0]
            # Convert PIL to QPixmap
            img_rgb = first_frame.convert("RGB")
            data = img_rgb.tobytes("raw", "RGB")
            qimg = QImage(data, img_rgb.width, img_rgb.height, img_rgb.width * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            scaled = pixmap.scaled(156, 106, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)

        card_layout.addWidget(self.thumb_label)

        # Meta Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(6)

        duration_text = f"Duration: {self.result.duration_seconds:.1f}s ({len(self.result.frames)} frames @ {self.result.fps} FPS)"
        dim_text = f"Resolution: {self.result.width} × {self.result.height}"

        dur_label = QLabel(duration_text)
        dur_label.setStyleSheet("color: #F1F5F9; font-weight: 600; font-size: 12px;")
        details_layout.addWidget(dur_label)

        dim_label = QLabel(dim_text)
        dim_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        details_layout.addWidget(dim_label)

        # File sizes
        for fmt, path in self.encoded_files.items():
            if path.exists():
                size_str = format_bytes(path.stat().st_size)
                fmt_label = QLabel(f"• {fmt.upper()}: {path.name} ({size_str})")
                fmt_label.setStyleSheet("color: #10B981; font-size: 11px;")
                details_layout.addWidget(fmt_label)

        details_layout.addStretch()
        card_layout.addLayout(details_layout)
        layout.addWidget(card)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.copy_btn = QPushButton("📋 Copy File Path")
        self.copy_btn.setObjectName("primaryAction")
        self.copy_btn.clicked.connect(self._copy_primary_file)
        btn_layout.addWidget(self.copy_btn)

        self.folder_btn = QPushButton("📂 Open Folder")
        self.folder_btn.setObjectName("ghostAction")
        self.folder_btn.clicked.connect(self._open_folder)
        btn_layout.addWidget(self.folder_btn)

        btn_layout.addStretch()

        done_btn = QPushButton("Done")
        done_btn.setObjectName("ghostAction")
        done_btn.clicked.connect(self.accept)
        btn_layout.addWidget(done_btn)

        layout.addLayout(btn_layout)

    def _get_primary_path(self) -> Optional[Path]:
        """Returns MP4 or GIF primary output path."""
        if "mp4" in self.encoded_files and self.encoded_files["mp4"].exists():
            return self.encoded_files["mp4"]
        if "gif" in self.encoded_files and self.encoded_files["gif"].exists():
            return self.encoded_files["gif"]
        return None

    def _copy_primary_file(self):
        """Copies primary file path to system clipboard."""
        primary = self._get_primary_path()
        if primary:
            clipboard = QApplication.clipboard()
            clipboard.setText(str(primary.resolve()))
            self.copy_btn.setText("Copied!")
            self.copy_btn.setStyleSheet("background-color: #059669; color: white;")

    def _open_folder(self):
        """Reveals output file or folder in native file manager."""
        primary = self._get_primary_path()
        if primary and primary.exists():
            target_dir = primary.parent
        elif self.encoded_files:
            target_dir = next(iter(self.encoded_files.values())).parent
        else:
            return

        if sys.platform == "darwin":
            subprocess.run(["open", str(target_dir)], check=False)
        elif sys.platform == "win32":
            os.startfile(str(target_dir))
        else:
            subprocess.run(["xdg-open", str(target_dir)], check=False)
