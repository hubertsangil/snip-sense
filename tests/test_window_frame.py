"""Unit tests for CustomTitleBar, CustomWindowContainer, and frameless window controls."""

from __future__ import annotations
import pytest
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QMainWindow, QSystemTrayIcon
from PyQt6.QtGui import QMouseEvent, QCloseEvent
from snipsense.ui.window_frame import CustomTitleBar, CustomWindowContainer
from snipsense.app import ControlWindow, SnipSenseApp


def test_custom_title_bar_initialization(qtbot):
    dummy_win = QWidget()
    qtbot.addWidget(dummy_win)

    title_bar = CustomTitleBar(
        parent_window=dummy_win,
        title="Test Window",
        badge_text="Beta",
        can_maximize=True,
        can_minimize=True,
    )
    qtbot.addWidget(title_bar)

    assert title_bar.title_label.text() == "Test Window"
    assert title_bar.badge_label is not None
    assert title_bar.badge_label.text() == "Beta"
    assert title_bar.btn_minimize is not None
    assert title_bar.btn_maximize is not None
    assert title_bar.btn_close is not None


def test_custom_title_bar_disabled_controls(qtbot):
    dummy_win = QWidget()
    qtbot.addWidget(dummy_win)

    title_bar = CustomTitleBar(
        parent_window=dummy_win,
        title="Fixed Window",
        badge_text=None,
        can_maximize=False,
        can_minimize=False,
    )
    qtbot.addWidget(title_bar)

    assert title_bar.badge_label is None
    assert title_bar.btn_minimize is None
    assert title_bar.btn_maximize is None
    assert title_bar.btn_close is not None


def test_custom_title_bar_setters(qtbot):
    dummy_win = QWidget()
    qtbot.addWidget(dummy_win)

    title_bar = CustomTitleBar(
        parent_window=dummy_win,
        title="Original",
        badge_text="Old",
    )
    qtbot.addWidget(title_bar)

    title_bar.set_title("Updated")
    assert title_bar.title_label.text() == "Updated"

    title_bar.set_badge_text("New")
    assert title_bar.badge_label.text() == "New"


def test_custom_title_bar_signals_and_actions(qtbot):
    win = QWidget()
    qtbot.addWidget(win)
    win.resize(300, 200)
    win.show()

    title_bar = CustomTitleBar(
        parent_window=win,
        title="SnipSense",
        can_maximize=True,
        can_minimize=True,
    )
    qtbot.addWidget(title_bar)

    min_signals = []
    max_signals = []
    close_signals = []

    title_bar.minimize_clicked.connect(lambda: min_signals.append(True))
    title_bar.maximize_clicked.connect(lambda: max_signals.append(True))
    title_bar.close_clicked.connect(lambda: close_signals.append(True))

    # Test Minimize
    qtbot.mouseClick(title_bar.btn_minimize, Qt.MouseButton.LeftButton)
    assert len(min_signals) == 1
    assert win.isMinimized()

    # Test Maximize / Restore
    win.showNormal()
    assert not win.isMaximized()
    assert title_bar.btn_maximize.text() == "□"

    qtbot.mouseClick(title_bar.btn_maximize, Qt.MouseButton.LeftButton)
    assert len(max_signals) == 1
    assert win.isMaximized()
    assert title_bar.btn_maximize.text() == "❐"

    qtbot.mouseClick(title_bar.btn_maximize, Qt.MouseButton.LeftButton)
    assert len(max_signals) == 2
    assert not win.isMaximized()
    assert title_bar.btn_maximize.text() == "□"

    # Test Close
    qtbot.mouseClick(title_bar.btn_close, Qt.MouseButton.LeftButton)
    assert len(close_signals) == 1
    assert not win.isVisible()


def test_custom_title_bar_double_click_maximize(qtbot):
    win = QWidget()
    qtbot.addWidget(win)
    win.resize(300, 200)
    win.show()

    title_bar = CustomTitleBar(
        parent_window=win,
        title="SnipSense",
        can_maximize=True,
    )
    qtbot.addWidget(title_bar)

    # Double click to maximize
    qtbot.mouseDClick(title_bar, Qt.MouseButton.LeftButton)
    assert win.isMaximized()
    assert title_bar.btn_maximize.text() == "❐"

    # Double click to restore
    qtbot.mouseDClick(title_bar, Qt.MouseButton.LeftButton)
    assert not win.isMaximized()
    assert title_bar.btn_maximize.text() == "□"


def test_custom_title_bar_dragging(qtbot):
    win = QWidget()
    qtbot.addWidget(win)
    win.move(100, 100)
    win.show()

    title_bar = CustomTitleBar(parent_window=win, title="Drag Test")
    qtbot.addWidget(title_bar)

    initial_pos = win.pos()

    # Simulate mouse press on titlebar
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(50, 15),
        QPointF(150, 115),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    title_bar.mousePressEvent(press_event)
    assert title_bar._drag_pos is not None

    # Simulate drag move
    move_event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(80, 25),
        QPointF(180, 125),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    title_bar.mouseMoveEvent(move_event)
    # The parent window should have moved by the delta
    assert win.pos() != initial_pos

    # Simulate mouse release
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(80, 25),
        QPointF(180, 125),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    title_bar.mouseReleaseEvent(release_event)
    assert title_bar._drag_pos is None


def test_custom_window_container_content(qtbot):
    win = QWidget()
    qtbot.addWidget(win)

    container = CustomWindowContainer(
        parent_window=win,
        title="Container Test",
        badge_text="Active",
    )
    qtbot.addWidget(container)

    label = QLabel("Test Content")
    container.add_content_widget(label)
    assert label.parent() == container.content_widget

    sub_layout = QVBoxLayout()
    btn = QPushButton("Button inside sub-layout")
    sub_layout.addWidget(btn)
    container.add_content_layout(sub_layout)
    assert btn.parent() == container.content_widget


def test_control_window_frameless_integration(qtbot, monkeypatch):
    monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", lambda: True)
    app = SnipSenseApp()
    app.setup_system_tray()

    win = ControlWindow(app)
    qtbot.addWidget(win)

    # Check window flags & translucent attribute
    flags = win.windowFlags()
    assert bool(flags & Qt.WindowType.FramelessWindowHint)
    assert win.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # Check titlebar and buttons mapped
    assert win.title_bar is not None
    assert win.btn_minimize is not None
    assert win.btn_maximize is not None
    assert win.btn_close is not None
    assert win.badge is None

    # Verify close button routes through closeEvent and minimizes to tray
    win.show()
    assert win.isVisible()

    qtbot.mouseClick(win.btn_close, Qt.MouseButton.LeftButton)
    # Since tray is available, closeEvent ignores the event and hides the window
    assert not win.isVisible()


def test_popup_dialogs_frameless_container_integration(qtbot, tmp_path):
    from PIL import Image
    from snipsense.core.models import CaptureResult, ScreenRegion
    from snipsense.core.recorder import RecordingResult
    from snipsense.core.dedup import DuplicateCluster, ScreenshotCandidate, DuplicateArchiver
    from snipsense.core.vault import VaultDatabase
    from snipsense.ui.preview import PreviewWindow
    from snipsense.ui.search_modal import SearchModal
    from snipsense.ui.dedup_dialog import DedupDialog
    from snipsense.ui.recording_dialog import RecordingCompletedDialog

    # 1. PreviewWindow
    img = Image.new("RGB", (80, 80), color=(10, 10, 10))
    cap = CaptureResult(image=img, region=ScreenRegion(x=0, y=0, width=80, height=80))
    preview = PreviewWindow(cap)
    qtbot.addWidget(preview)
    assert bool(preview.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert preview.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert hasattr(preview, "container")
    assert isinstance(preview.container, CustomWindowContainer)
    assert preview.container.title_bar.btn_close is not None

    # 2. SearchModal
    db_file = tmp_path / "test_frame_vault.db"
    vault = VaultDatabase(db_path=db_file)
    search = SearchModal(vault=vault)
    qtbot.addWidget(search)
    assert bool(search.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert search.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert hasattr(search, "container")
    assert isinstance(search.container, CustomWindowContainer)
    assert search.container.title_bar.btn_close is not None

    # 3. DedupDialog
    cand = ScreenshotCandidate(file_path="dummy.png", created_at=1.0, perceptual_hash="1111", file_size_bytes=100)
    cluster = DuplicateCluster(cluster_id="c1", primary=cand, duplicates=[])
    dedup = DedupDialog(clusters=[cluster], archiver=DuplicateArchiver(archive_directory=tmp_path))
    qtbot.addWidget(dedup)
    assert bool(dedup.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert dedup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert hasattr(dedup, "container")
    assert isinstance(dedup.container, CustomWindowContainer)
    assert dedup.container.title_bar.btn_close is not None

    # 4. RecordingCompletedDialog
    rec_res = RecordingResult(frames=[img], fps=15, duration_seconds=1.0, window_title="App", width=80, height=80)
    dummy_file = tmp_path / "dummy.mp4"
    dummy_file.write_bytes(b"data")
    rec_dialog = RecordingCompletedDialog(encoded_files={"mp4": dummy_file}, result=rec_res)
    qtbot.addWidget(rec_dialog)
    assert bool(rec_dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert rec_dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert hasattr(rec_dialog, "container")
    assert isinstance(rec_dialog.container, CustomWindowContainer)
    assert rec_dialog.container.title_bar.btn_close is not None
