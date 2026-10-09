"""Application coordinator linking hotkeys, canvas overlay, auto-naming, preview dialog, system tray, HUD, and deduplication."""

from __future__ import annotations
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSlot, QThread, Qt, QRect
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
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
from snipsense.core.recorder import ScreenRecorder, RecordingResult
from snipsense.core.encoder import ClipEncoder
from snipsense.ui.canvas import SnipCanvas
from snipsense.ui.preview import PreviewWindow
from snipsense.ui.search_modal import SearchModal
from snipsense.ui.dedup_dialog import DedupDialog
from snipsense.ui.overlay_hud import OverlayHUD
from snipsense.ui.recorder_pill import RecorderPill
from snipsense.ui.recording_dialog import RecordingCompletedDialog
from snipsense.ui.window_frame import CustomWindowContainer
from snipsense.ui.styles import DARK_THEME_QSS
from snipsense.ui.motion import animate_window_entrance


def create_app_icon() -> QIcon:
    """Loads the official Razor Shears branding symbol (shears-v1-symbol.svg) for taskbar and tray."""
    candidates = [
        Path(__file__).resolve().parent.parent / "branding" / "shears-v1-symbol.svg",
        Path.cwd() / "branding" / "shears-v1-symbol.svg",
        Path(sys.executable).parent / "branding" / "shears-v1-symbol.svg",
    ]
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, Path(sys._MEIPASS) / "branding" / "shears-v1-symbol.svg")

    for candidate in candidates:
        if candidate.is_file():
            icon = QIcon(str(candidate))
            if not icon.isNull():
                return icon

    # Fallback in case asset file is missing
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(QColor("#0F172A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 12, 12)
    p.end()
    return QIcon(pix)


class ControlWindow(QMainWindow):
    """Minimal, modern borderless control window offering custom titlebar and dedicated controls."""

    def __init__(self, app_controller: "SnipSenseApp"):
        super().__init__()
        self.app_controller = app_controller
        self.setObjectName("controlWindow")
        self.setStyleSheet(DARK_THEME_QSS)
        self.setWindowTitle("SnipSense Studio")
        self.resize(450, 310)

        # Borderless frameless window configuration
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Root Custom Window Container with dedicated controls (minimize, expand, exit)
        self.container = CustomWindowContainer(
            parent_window=self,
            title="SnipSense",
            badge_text=None,
            can_maximize=True,
            can_minimize=True,
        )
        self.setCentralWidget(self.container)

        # Map titlebar and control buttons for external inspection & testing
        self.title_bar = self.container.title_bar
        self.badge = self.title_bar.badge_label
        self.btn_minimize = self.title_bar.btn_minimize
        self.btn_maximize = self.title_bar.btn_maximize
        self.btn_close = self.title_bar.btn_close

        # 1. Hero Primary Action: New Capture Trigger
        snip_btn = QPushButton("New Capture                                        Ctrl+Shift+S")
        snip_btn.setObjectName("heroActionBtn")
        snip_btn.setToolTip("Capture selected screen area (Ctrl+Shift+S)")
        snip_btn.clicked.connect(self.app_controller.start_snip)
        self.container.add_content_widget(snip_btn)

        # 2. 2x2 Quick Actions Matrix
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        record_btn = QPushButton("Record Screen           Ctrl+Shift+R")
        record_btn.setObjectName("toolCardBtn")
        record_btn.setToolTip("Record screen clip up to 30s (Ctrl+Shift+R)")
        record_btn.clicked.connect(self.app_controller.start_recording)
        grid.addWidget(record_btn, 0, 0)

        hud_btn = QPushButton("Overlay HUD                     Alt+Z")
        hud_btn.setObjectName("toolCardBtn")
        hud_btn.setToolTip("Open overlay HUD (Alt+Z)")
        hud_btn.clicked.connect(self.app_controller.open_hud)
        grid.addWidget(hud_btn, 0, 1)

        search_btn = QPushButton("Search Vault                    Alt+F")
        search_btn.setObjectName("toolCardBtn")
        search_btn.setToolTip("Search OCR text and history (Alt+F)")
        search_btn.clicked.connect(self.app_controller.open_search_vault)
        grid.addWidget(search_btn, 1, 0)

        self.clean_btn = QPushButton("Clean Duplicates")
        self.clean_btn.setObjectName("toolCardBtn")
        self.clean_btn.setToolTip("Detect and clean redundant duplicate captures")
        self.clean_btn.clicked.connect(self.app_controller.open_dedup_dialog)
        grid.addWidget(self.clean_btn, 1, 1)

        self.container.add_content_layout(grid)

        # 3. Footer Utility Row
        footer = QHBoxLayout()
        footer.setSpacing(8)

        folder_btn = QPushButton("Open Folder")
        folder_btn.setObjectName("ghostAction")
        folder_btn.setToolTip("Open screenshots directory in File Explorer")
        folder_btn.clicked.connect(self._open_screenshots_folder)
        footer.addWidget(folder_btn)

        footer.addStretch()

        self.hint_label = QLabel("Runs in system tray when closed")
        self.hint_label.setStyleSheet("color: #767676; font-size: 11px;")
        footer.addWidget(self.hint_label)

        self.container.add_content_layout(footer)

        # In-app shortcuts (Application-wide)
        self.snip_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.snip_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.snip_shortcut.activated.connect(self.app_controller.start_snip)

        self.record_shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        self.record_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.record_shortcut.activated.connect(self.app_controller.start_recording)

        self.hud_shortcut = QShortcut(QKeySequence("Alt+Z"), self)
        self.hud_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.hud_shortcut.activated.connect(self.app_controller.open_hud)

        self.search_shortcut = QShortcut(QKeySequence("Alt+F"), self)
        self.search_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.search_shortcut.activated.connect(self.app_controller.open_search_vault)

    def showEvent(self, event):
        """Applies purposeful entrance motion when window is shown."""
        super().showEvent(event)
        animate_window_entrance(self, duration_ms=180, slide_px=6)

    def set_status_text(self, text: str):
        """Updates the status text."""
        if self.badge:
            self.badge.setText(text)
        if hasattr(self, "hint_label") and self.hint_label:
            if text:
                self.hint_label.setText(f"{text} • Runs in tray")
            else:
                self.hint_label.setText("Runs in system tray when closed")

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
    """Coordinates canvas spawning, image grabbing, auto-naming, preview, system tray, HUD, search vault, deduplication, and screen recording."""

    def __init__(self):
        # Explicitly configure Windows AppUserModelID so tray popups, toast notifications,
        # and taskbar items identify as 'SnipSense' instead of 'python'.
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SnipSense.Desktop.CaptureStudio.1.0")
            except Exception:
                pass

        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.qt_app.setApplicationName("SnipSense")
        self.qt_app.setApplicationDisplayName("SnipSense")
        self.qt_app.setOrganizationName("SnipSense")
        self.qt_app.setOrganizationDomain("snipsense.local")
        self.qt_app.setWindowIcon(create_app_icon())
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
        self._recorder: ScreenRecorder | None = None
        self._recorder_pill: RecorderPill | None = None
        self.recording_dialog: RecordingCompletedDialog | None = None
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
                self.control_win.set_status_text(f"{indexed_count} indexed")

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

        snip_act = menu.addAction("New Snip (Ctrl+Shift+S)")
        snip_act.triggered.connect(self.start_snip)

        record_act = menu.addAction("Record Clip (Ctrl+Shift+R)")
        record_act.triggered.connect(self.start_recording)

        hud_act = menu.addAction("Overlay HUD (Alt+Z)")
        hud_act.triggered.connect(self.open_hud)

        search_act = menu.addAction("Search Vault (Alt+F)")
        search_act.triggered.connect(self.open_search_vault)

        folder_act = menu.addAction("Open Screenshots")
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
                "SnipSense",
                "Running in the background. Press Ctrl+Shift+S anytime to capture, or click the tray icon to reopen.",
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
        if self.hud and self.hud.isVisible():
            self.hud.close()
            return

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
        self.hud.record_requested.connect(self.start_recording)
        self.hud.search_requested.connect(self.open_search_vault)
        self.hud.clean_duplicates_requested.connect(self.open_dedup_dialog)

        # On macOS, activate the app AFTER showing the window so the window
        # server has a visible target to grant input focus to.
        self.hud.show()
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception:
                pass
        self.hud.raise_()
        self.hud.activateWindow()

    def open_search_vault(self):
        """Opens the visual memory search dialog."""
        self.search_modal = SearchModal(vault=self.vault)
        self.search_modal.show()
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception:
                pass
        self.search_modal.raise_()
        self.search_modal.activateWindow()
        self.search_modal.search_input.setFocus()

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

    def start_recording(self):
        """Starts a short screen clip recording session with the floating draggable pill."""
        if self._recorder and self._recorder.is_recording:
            return

        self._last_window_title = get_foreground_window_title()

        if self.control_win and self.control_win.isVisible():
            self._control_was_visible = True
            self.control_win.hide()
        else:
            self._control_was_visible = False

        self._recorder = ScreenRecorder(target_fps=15, max_duration_seconds=30.0)
        self._recorder_pill = RecorderPill(max_duration_seconds=30.0)

        self._recorder.tick.connect(self._recorder_pill.update_time)
        self._recorder.recording_finished.connect(self._on_recording_finished)
        self._recorder.recording_cancelled.connect(self._on_recording_cancelled)

        self._recorder_pill.stop_requested.connect(self.stop_recording)
        self._recorder_pill.cancel_requested.connect(self.cancel_recording)

        self._recorder_pill.show()
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception:
                pass
        self._recorder_pill.raise_()
        self._recorder_pill.activateWindow()

        self._recorder.start(window_title=self._last_window_title)

    def stop_recording(self):
        """Stops the active recording session and begins encoding."""
        if self._recorder_pill:
            self._recorder_pill.close()
            self._recorder_pill = None
        if self._recorder:
            self._recorder.stop()

    def cancel_recording(self):
        """Aborts recording and discards all frames."""
        if self._recorder_pill:
            self._recorder_pill.close()
            self._recorder_pill = None
        if self._recorder:
            self._recorder.cancel()

    @pyqtSlot(object)
    def _on_recording_finished(self, result: RecordingResult):
        """Encodes frames into MP4/GIF and displays the completion dialog."""
        encoder = ClipEncoder()
        encoded_files = encoder.encode_clip(
            frames=result.frames,
            window_title=result.window_title,
            fps=result.fps,
            generate_gif=True,
            generate_mp4=True,
        )

        self.recording_dialog = RecordingCompletedDialog(encoded_files, result)
        self.recording_dialog.show()
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception:
                pass
        self.recording_dialog.raise_()
        self.recording_dialog.activateWindow()

        if self.control_win and self._control_was_visible:
            self.control_win.showNormal()

    @pyqtSlot()
    def _on_recording_cancelled(self):
        """Restores control window if a recording session is cancelled."""
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
        if self._recorder_pill:
            self._recorder_pill.close()
        if self.recording_dialog:
            self.recording_dialog.close()
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
