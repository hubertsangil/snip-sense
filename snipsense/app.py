"""Application coordinator linking hotkeys, canvas overlay, and preview dialog."""

from __future__ import annotations
import sys
from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt6.QtGui import QKeySequence, QShortcut
from snipsense.core.capture import ScreenGrabber
from snipsense.core.models import ScreenRegion, CaptureResult
from snipsense.ui.canvas import SnipCanvas
from snipsense.ui.preview import PreviewWindow
from snipsense.ui.styles import DARK_THEME_QSS


class ControlWindow(QMainWindow):
    """Minimal control window offering launcher buttons and global shortcuts."""

    def __init__(self, app_controller: "SnipSenseApp"):
        super().__init__()
        self.app_controller = app_controller
        self.setObjectName("controlWindow")
        self.setStyleSheet(DARK_THEME_QSS)
        self.setWindowTitle("SnipSense Studio")
        self.resize(360, 180)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("🔮 SnipSense")
        title.setObjectName("headerTitle")
        header.addWidget(title)

        badge = QLabel("100% Offline")
        badge.setObjectName("statusBadge")
        header.addWidget(badge)
        header.addStretch()
        layout.addLayout(header)

        desc = QLabel("Press Ctrl+Shift+S anywhere to snip an area.")
        desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc)

        btn_row = QHBoxLayout()
        snip_btn = QPushButton("✂️ New Snip (Ctrl+Shift+S)")
        snip_btn.setObjectName("primaryAction")
        snip_btn.clicked.connect(self.app_controller.start_snip)
        btn_row.addWidget(snip_btn)
        layout.addLayout(btn_row)

        # In-app shortcut
        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut.activated.connect(self.app_controller.start_snip)


class SnipSenseApp(QObject):
    """Coordinates canvas spawning, image grabbing, and preview window presentation."""

    def __init__(self):
        super().__init__()
        self.grabber = ScreenGrabber()
        self.canvas: SnipCanvas | None = None
        self.preview: PreviewWindow | None = None
        self.control_win: ControlWindow | None = None

    def start_snip(self):
        """Spawns the transparent selection canvas covering all connected monitors."""
        if self.control_win:
            self.control_win.showMinimized()

        virtual_geom = self.grabber.get_virtual_geometry()
        self.canvas = SnipCanvas(virtual_geom)
        self.canvas.snip_completed.connect(self.on_snip_completed)
        self.canvas.snip_cancelled.connect(self.on_snip_cancelled)
        self.canvas.show()
        self.canvas.activateWindow()

    @pyqtSlot(ScreenRegion)
    def on_snip_completed(self, region: ScreenRegion):
        """Captures the requested region and opens the preview window."""
        try:
            result = self.grabber.capture_region(region)
            self.preview = PreviewWindow(result)
            self.preview.show()
            self.preview.activateWindow()
        finally:
            if self.control_win:
                self.control_win.showNormal()

    @pyqtSlot()
    def on_snip_cancelled(self):
        """Restores control window if a snip is aborted."""
        if self.control_win:
            self.control_win.showNormal()

    def run(self):
        """Starts the main Qt event loop."""
        app = QApplication.instance() or QApplication(sys.argv)
        app.setStyleSheet(DARK_THEME_QSS)
        self.control_win = ControlWindow(self)
        self.control_win.show()
        return app.exec()
