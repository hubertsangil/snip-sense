"""Application coordinator linking hotkeys, canvas overlay, auto-naming, and preview dialog."""

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
from snipsense.core.naming import get_foreground_window_title, generate_filename
from snipsense.core.storage import StorageManager
from snipsense.core.ocr_engine import OCREngine
from snipsense.core.vault import VaultDatabase
from snipsense.core.dedup import DuplicateCluster, DuplicateArchiver
from snipsense.core.ingestion import HistoricalScanner, IngestionWorker
from snipsense.ui.canvas import SnipCanvas
from snipsense.ui.preview import PreviewWindow
from snipsense.ui.search_modal import SearchModal
from snipsense.ui.dedup_dialog import DedupDialog
from snipsense.ui.styles import DARK_THEME_QSS


class ControlWindow(QMainWindow):
    """Minimal control window offering launcher buttons, folder access, and global shortcuts."""

    def __init__(self, app_controller: "SnipSenseApp"):
        super().__init__()
        self.app_controller = app_controller
        self.setObjectName("controlWindow")
        self.setStyleSheet(DARK_THEME_QSS)
        self.setWindowTitle("SnipSense Studio")
        self.resize(420, 230)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("🔮 SnipSense")
        title.setObjectName("headerTitle")
        header.addWidget(title)

        self.badge = QLabel("100% Offline")
        self.badge.setObjectName("statusBadge")
        header.addWidget(self.badge)
        header.addStretch()
        layout.addLayout(header)

        desc = QLabel("Press Ctrl+Shift+S anywhere to snip an area.")
        desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        snip_btn = QPushButton("✂️ New Snip (Ctrl+Shift+S)")
        snip_btn.setObjectName("primaryAction")
        snip_btn.clicked.connect(self.app_controller.start_snip)
        btn_row.addWidget(snip_btn)

        search_btn = QPushButton("🔍 Vault (Alt+F)")
        search_btn.setObjectName("ghostAction")
        search_btn.clicked.connect(self.app_controller.open_search_vault)
        btn_row.addWidget(search_btn)

        layout.addLayout(btn_row)

        secondary_row = QHBoxLayout()
        secondary_row.setSpacing(8)

        self.clean_btn = QPushButton("🧹 Clean Dups")
        self.clean_btn.setObjectName("ghostAction")
        self.clean_btn.clicked.connect(self.app_controller.open_dedup_dialog)
        secondary_row.addWidget(self.clean_btn)

        folder_btn = QPushButton("📂 Open Folder")
        folder_btn.setObjectName("ghostAction")
        folder_btn.clicked.connect(self._open_screenshots_folder)
        secondary_row.addWidget(folder_btn)

        layout.addLayout(secondary_row)

        # In-app shortcuts
        self.snip_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.snip_shortcut.activated.connect(self.app_controller.start_snip)

        self.search_shortcut = QShortcut(QKeySequence("Alt+F"), self)
        self.search_shortcut.activated.connect(self.app_controller.open_search_vault)

    def set_status_text(self, text: str):
        """Updates the status badge text."""
        self.badge.setText(text)

    def _open_screenshots_folder(self):
        storage = StorageManager()
        storage.open_in_explorer(storage.base_directory)


class SnipSenseApp(QObject):
    """Coordinates canvas spawning, image grabbing, auto-naming, preview, search vault, and deduplication."""

    def __init__(self):
        super().__init__()
        self.grabber = ScreenGrabber()
        self.vault = VaultDatabase.get_instance()
        self.canvas: SnipCanvas | None = None
        self.preview: PreviewWindow | None = None
        self.search_modal: SearchModal | None = None
        self.dedup_dialog: DedupDialog | None = None
        self.control_win: ControlWindow | None = None
        self.duplicate_clusters: list[DuplicateCluster] = []
        self._last_window_title: str = ""
        self._ingestion_thread: QThread | None = None
        self._ingestion_worker: IngestionWorker | None = None

    def start_background_ingestion(self):
        """Dispatches non-blocking historical screenshot scan and perceptual deduplication."""
        self._ingestion_thread = QThread()
        self._ingestion_worker = IngestionWorker()
        self._ingestion_worker.moveToThread(self._ingestion_thread)

        self._ingestion_thread.started.connect(self._ingestion_worker.run)
        self._ingestion_worker.clusters_ready.connect(self._on_clusters_ready)
        self._ingestion_worker.finished.connect(self._on_ingestion_finished)
        self._ingestion_worker.finished.connect(self._ingestion_thread.quit)
        self._ingestion_thread.finished.connect(self._ingestion_worker.deleteLater)
        self._ingestion_thread.finished.connect(self._ingestion_thread.deleteLater)

        self._ingestion_thread.start()

    @pyqtSlot(list)
    def _on_clusters_ready(self, clusters: list):
        self.duplicate_clusters = clusters

    @pyqtSlot(int, int)
    def _on_ingestion_finished(self, indexed_count: int, dup_count: int):
        if self.control_win:
            if dup_count > 0:
                self.control_win.set_status_text(f"{indexed_count} indexed | {dup_count} duplicate bursts")
            else:
                self.control_win.set_status_text(f"{indexed_count} indexed • 100% Offline")

    def open_dedup_dialog(self):
        """Opens the review and deduplication modal."""
        self.dedup_dialog = DedupDialog(self.duplicate_clusters)
        self.dedup_dialog.cleaning_completed.connect(self._on_duplicates_cleaned)
        self.dedup_dialog.show()
        self.dedup_dialog.activateWindow()
        self.dedup_dialog.raise_()

    @pyqtSlot(int, int)
    def _on_duplicates_cleaned(self, cleaned_count: int, reclaimed_bytes: int):
        if self.control_win:
            self.control_win.set_status_text(f"Cleaned {cleaned_count} duplicates")

    def open_search_vault(self):
        """Opens the visual memory search dialog."""
        self.search_modal = SearchModal(vault=self.vault)
        self.search_modal.show()
        self.search_modal.activateWindow()
        self.search_modal.raise_()

    def start_snip(self):
        """Captures active window context and spawns the transparent selection canvas."""
        # Query active window title before modifying window state
        self._last_window_title = get_foreground_window_title()

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
        """Captures the requested region, runs OCR, synthesizes filename, and opens preview."""
        try:
            result = self.grabber.capture_region(region, window_title=self._last_window_title)

            # 1. Run in-process OCR extraction
            boxes, raw_text = OCREngine.get_instance().extract_text(result.image)
            result.ocr_boxes = boxes
            result.raw_text = raw_text

            # 2. Synthesize intelligent auto-name
            result.suggested_filename = generate_filename(
                window_title=result.window_title or "",
                ocr_boxes=result.ocr_boxes,
                timestamp=result.timestamp,
            )

            # 3. Present preview window
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
        """Starts the main Qt event loop and kicks off background ingestion."""
        app = QApplication.instance() or QApplication(sys.argv)
        app.setStyleSheet(DARK_THEME_QSS)
        self.control_win = ControlWindow(self)
        self.control_win.show()
        self.start_background_ingestion()
        return app.exec()
