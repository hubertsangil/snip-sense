"""Unit tests for GlobalHotkeyManager, System Tray icon, and background app lifecycle."""

from __future__ import annotations
import pytest
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from PyQt6.QtGui import QCloseEvent
from snipsense.core.hotkey import GlobalHotkeyManager
from snipsense.app import SnipSenseApp, ControlWindow, create_app_icon


def test_hotkey_manager_start_and_stop():
    manager = GlobalHotkeyManager()
    assert not manager.is_running()

    started = manager.start()
    if started:
        assert manager.is_running()
        manager.stop()
        assert not manager.is_running()


def test_hotkey_manager_signal_emission(qtbot):
    manager = GlobalHotkeyManager()
    signals = []
    manager.hotkey_triggered.connect(lambda: signals.append(True))

    manager._on_hotkey()
    assert len(signals) == 1


def test_create_app_icon(qapp):
    icon = create_app_icon()
    assert not icon.isNull()


def test_system_tray_menu_actions(qtbot, qapp, monkeypatch):
    monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", lambda: True)
    app = SnipSenseApp()
    app.setup_system_tray()

    assert app.tray_icon is not None
    assert app.is_tray_available()

    menu = app.tray_icon.contextMenu()
    assert menu is not None

    actions = [act.text() for act in menu.actions() if act.text()]
    assert any("New Snip" in act for act in actions)
    assert any("Search Vault" in act for act in actions)
    assert any("Open Screenshots" in act for act in actions)
    assert any("Show / Hide Studio" in act for act in actions)
    assert any("Exit SnipSense" in act for act in actions)

    # Test clean quit terminates cleanly
    quit_called = []
    monkeypatch.setattr(QApplication, "quit", lambda *args: quit_called.append(True))
    app.quit()
    assert len(quit_called) == 1


def test_control_window_close_minimizes_to_tray(qtbot, qapp, monkeypatch):
    monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", lambda: True)
    app = SnipSenseApp()
    app.setup_system_tray()
    win = ControlWindow(app)
    app.control_win = win
    qtbot.addWidget(win)

    win.show()
    assert win.isVisible()

    # Create close event
    close_event = QCloseEvent()
    win.closeEvent(close_event)

    # Verify event was ignored and window was hidden to tray
    assert not close_event.isAccepted()
    assert not win.isVisible()
    assert app._has_shown_tray_balloon is True


def test_toggle_control_window(qtbot, qapp, monkeypatch):
    monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", lambda: True)
    app = SnipSenseApp()
    win = ControlWindow(app)
    app.control_win = win
    qtbot.addWidget(win)

    win.hide()
    assert not win.isVisible()

    # Toggle to show
    app.toggle_control_window()
    assert win.isVisible()

    # Toggle to hide
    app.toggle_control_window()
    assert not win.isVisible()
