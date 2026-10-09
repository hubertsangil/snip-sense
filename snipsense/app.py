"""Application coordinator linking hotkeys, canvas overlay, auto-naming, preview dialog, system tray, HUD, and deduplication."""

from __future__ import annotations
import sys
from PyQt6.QtCore import QObject, pyqtSlot, QThread, Qt, QRect
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtGui import (
    QKeySequence,
    QShortcut,
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QCloseEvent,
    QCursor,
    QGuiApplication,
)
from snipsense.core.capture import ScreenGrabber
from snipsense.core.models import ScreenRegion, CaptureResult
from snipsense.core.naming import get_foreground_window_title, generate_filename
from snipsense.core.storage import StorageManager
from snipsense.core.ocr_engine import OCREngine
from snipsense.core.vault import VaultDatabase
from snipsense.core.dedup import DuplicateCluster, DuplicateArchiver
from snipsense.core.ingestion import HistoricalScanner, IngestionWorker
from snipsense.core.hotkeys import GlobalHotkeyListener
from snipsense.core.hotkey import GlobalHotkeyManager
from snipsense.ui.canvas import SnipCanvas
from snipsense.ui.preview import PreviewWindow
from snipsense.ui.search_modal import SearchModal
from snipsense.ui.dedup_dialog import DedupDialog
from snipsense.ui.overlay_hud import OverlayHUD
from snipsense.ui.styles import DARK_THEME_QSS


def create_app_icon() -> QIcon:
    """Generates an emerald camera/snip studio icon for taskbar and tray."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    # Emerald rounded rectangle badge
    p.setBrush(QColor("#10B981"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    # Scissor symbol
    p.setPen(QColor("#FFFFFF"))
    font = QFont("Segoe UI Emoji", 26)
    p.setFont(font)
    p.drawText(QRect(0, 0, 64, 64), Qt.AlignmentFlag.AlignCenter, "✂")
    p.end()
    return QIcon(pix)


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

        snip_btn = QPushButton("✂️ Snip (Ctrl+Shift+S)")
        snip_btn.setObjectName("primaryAction")
        snip_btn.clicked.connect(self.app_controller.start_snip)
        btn_row.addWidget(snip_btn)

        hud_btn = QPushButton("🔮 HUD (Alt+Z)")
        hud_btn.setObjectName("ghostAction")
        hud_btn.clicked.connect(self.app_controller.open_hud)
        btn_row.addWidget(hud_btn)

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

        # In-app shortcuts (Application-wide)
        self.snip_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.snip_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.snip_shortcut.activated.connect(self.app_controller.start_snip)

        self.hud_shortcut = QShortcut(QKeySequence("Alt+Z"), self)
        self.hud_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.hud_shortcut.activated.connect(self.app_controller.open_hud)

        self.search_shortcut = QShortcut(QKeySequence("Alt+F"), self)
        self.search_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.search_shortcut.activated.connect(self.app_controller.open_search_vault)

    def set_status_text(self, text: str):
        """Updates the status badge text."""
        self.badge.setText(text)

    def _open_screenshots_folder(self):
        self.app_controller.open_screenshots_folder()

    def closeEvent(self, event: QCloseEvent):
        """Minimizes window to system tray when closed instead of terminating application."""
        if self.app_controller.is_tray_available():
            event.ignore()
            self.hide()
            self.app_controller.notify_minimized_to_tray()
        else:
            event.accept()


class SnipSenseApp(QObject):
    """Coordinates canvas spawning, image grabbing, auto-naming, preview, system tray, HUD, search vault, and deduplication."""

    def __init__(self):
        super().__init__()
        self.grabber = ScreenGrabber()
        self.vault = VaultDatabase.get_instance()
        self.hotkey_listener = GlobalHotkeyListener(self)
        self.hotkey_manager = self.hotkey_listener
        self.tray_icon: QSystemTrayIcon | None = None
        self._has_shown_tray_balloon: bool = False
        self.canvas: SnipCanvas | None = None
        self.preview: PreviewWindow | None = None
        self.hud: OverlayHUD | None = None
        self.search_modal: SearchModal | None = None
        self.dedup_dialog: DedupDialog | None = None
        self.control_win: ControlWindow | None = None
        self.duplicate_clusters: list[DuplicateCluster] = []
        self._last_window_title: str = ""
        self._control_was_visible: bool = False
        self._ingestion_thread: QThread | None = None
        self._ingestion_worker: IngestionWorker | None = None

        # Global system-wide hotkeys (Alt+Z, Ctrl+Shift+S, Alt+F)
        self.hotkey_listener.hud_triggered.connect(self.open_hud)
        self.hotkey_listener.snip_triggered.connect(self.start_snip)
        self.hotkey_listener.search_triggered.connect(self.open_search_vault)
        self.hotkey_listener.start()

    def start_background_ingestion(self):
        """Dispatches non-blocking historical screenshot scan and perceptual deduplication."""
        self._ingestion_thread = QThread()
        self._ingestion_worker = IngestionWorker()
        self._ingestion_worker.moveToThread(self._ingestion_thread)

        self._ingestion_thread.started.connect(self._ingestion_worker.run)
        self._ingestion_worker.finished.connect(self._on_ingestion_finished)
        self._ingestion_worker.finished.connect(self._ingestion_thread.quit)
        self._ingestion_thread.finished.connect(self._ingestion_thread.deleteLater)

        self._ingestion_thread.start()

    @pyqtSlot(int, int)
    def _on_ingestion_finished(self, indexed_count: int, dup_count: int):
        # Retrieve clusters directly from the worker (avoids cross-thread list serialization)
        if self._ingestion_worker:
            self.duplicate_clusters = self._ingestion_worker.clusters
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

    def is_tray_available(self) -> bool:
        """Returns True if the system tray is supported and icon is active."""
        return self.tray_icon is not None and QSystemTrayIcon.isSystemTrayAvailable()

    def setup_system_tray(self):
        """Initializes system tray icon, notifications, and context menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = create_app_icon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("SnipSense Studio (Ctrl+Shift+S to snip)")

        menu = QMenu()
        menu.setStyleSheet(DARK_THEME_QSS)

        snip_act = menu.addAction("✂️ New Snip (Ctrl+Shift+S)")
        snip_act.triggered.connect(self.start_snip)

        hud_act = menu.addAction("🔮 HUD (Alt+Z)")
        hud_act.triggered.connect(self.open_hud)

        search_act = menu.addAction("🔍 Search Vault (Alt+F)")
        search_act.triggered.connect(self.open_search_vault)

        folder_act = menu.addAction("📂 Open Screenshots")
        folder_act.triggered.connect(self.open_screenshots_folder)

        menu.addSeparator()

        toggle_act = menu.addAction("Show / Hide Studio")
        toggle_act.triggered.connect(self.toggle_control_window)

        menu.addSeparator()

        exit_act = menu.addAction("Exit SnipSense")
        exit_act.triggered.connect(self.quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Toggles main control launcher when tray icon is clicked."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.toggle_control_window()

    def toggle_control_window(self):
        """Toggles the visibility of the control window."""
        if not self.control_win:
            return
        if self.control_win.isVisible() and not self.control_win.isMinimized():
            self.control_win.hide()
        else:
            self.control_win.showNormal()
            self.control_win.raise_()
            self.control_win.activateWindow()

    def notify_minimized_to_tray(self):
        """Displays a one-time balloon tip indicating background operation."""
        if self.tray_icon and not self._has_shown_tray_balloon:
            self.tray_icon.showMessage(
                "SnipSense is running in the background",
                "Press Ctrl+Shift+S anytime to capture, or click the tray icon to reopen.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            self._has_shown_tray_balloon = True

    def open_screenshots_folder(self):
        """Opens the user's default screenshot storage directory in File Explorer."""
        storage = StorageManager()
        storage.open_in_explorer(storage.base_directory)

    def open_hud(self):
        """Opens the frosted-glass overlay HUD (Alt + Z)."""
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception:
                pass

        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()

        self.hud = OverlayHUD(vault=self.vault)
        if screen:
            sg = screen.geometry()
            self.hud.move(
                sg.x() + (sg.width() - self.hud.width()) // 2,
                sg.y() + (sg.height() - self.hud.height()) // 2,
            )

        self.hud.snip_requested.connect(self.start_snip)
        self.hud.search_requested.connect(self.open_search_vault)
        self.hud.clean_duplicates_requested.connect(self.open_dedup_dialog)
        self.hud.show()
        self.hud.raise_()
        self.hud.activateWindow()

    def open_search_vault(self):
        """Opens the visual memory search dialog."""
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception:
                pass

        self.search_modal = SearchModal(vault=self.vault)
        self.search_modal.show()
        self.search_modal.raise_()
        self.search_modal.activateWindow()

    def start_snip(self):
        """Captures active window context, freezes the screen, and spawns the precision canvas."""
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception:
                pass

        # Query active window title before modifying window state
        self._last_window_title = get_foreground_window_title()

        self._control_was_visible = bool(
            self.control_win and self.control_win.isVisible() and not self.control_win.isMinimized()
        )
        if self.control_win and self._control_was_visible:
            self.control_win.hide()

        # Capture frozen screen buffer instantly (~10ms)
        frozen_pixmap, dpr, virt_geom = self.grabber.capture_frozen_screen()

        self.canvas = SnipCanvas(
            virtual_geometry=virt_geom,
            frozen_pixmap=frozen_pixmap,
            dpr=dpr,
        )
        self.canvas.snip_completed.connect(self.on_snip_completed)
        self.canvas.snip_cancelled.connect(self.on_snip_cancelled)
        self.canvas.show()
        self.canvas.raise_()
        self.canvas.activateWindow()

    @pyqtSlot(ScreenRegion)
    @pyqtSlot(ScreenRegion, object)
    def on_snip_completed(self, region: ScreenRegion, image: object = None):
        """Processes the captured region, runs OCR, synthesizes filename, and opens preview."""
        try:
            if image is not None:
                result = CaptureResult(
                    image=image,
                    region=region,
                    window_title=self._last_window_title,
                )
            else:
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
            self.preview.raise_()
            self.preview.activateWindow()
        finally:
            if self.control_win and self._control_was_visible:
                self.control_win.showNormal()

    @pyqtSlot()
    def on_snip_cancelled(self):
        """Restores control window if a snip is aborted and it was visible before."""
        if self.control_win and self._control_was_visible:
            self.control_win.showNormal()

    def quit(self):
        """Cleanly terminates the application and all background listeners."""
        self.hotkey_listener.stop()
        if self.tray_icon:
            self.tray_icon.hide()
        if self.canvas:
            self.canvas.close()
        if self.preview:
            self.preview.close()
        if self.hud:
            self.hud.close()
        if self.search_modal:
            self.search_modal.close()
        if self.dedup_dialog:
            self.dedup_dialog.close()
        if self.control_win:
            self.control_win.close()
        app = QApplication.instance()
        if app:
            app.quit()

    def run(self):
        """Starts the main Qt application and background hotkey listener."""
        app = QApplication.instance() or QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setStyleSheet(DARK_THEME_QSS)

        icon = create_app_icon()
        app.setWindowIcon(icon)

        self.control_win = ControlWindow(self)
        self.control_win.setWindowIcon(icon)
        self.setup_system_tray()

        self.control_win.show()
        self.control_win.raise_()
        self.control_win.activateWindow()
        self.start_background_ingestion()
        try:
            return app.exec()
        finally:
            self.hotkey_listener.stop()
