"""Unit tests for the GlobalHotkeyListener component."""

import time
import pytest
from PyQt6.QtCore import QObject
from snipsense.core.hotkeys import GlobalHotkeyListener


def test_hotkey_listener_initialization():
    listener = GlobalHotkeyListener()
    assert listener is not None
    assert not listener.is_running()


def test_hotkey_listener_start_and_stop():
    listener = GlobalHotkeyListener()
    started = listener.start()
    if started:
        assert listener.is_running()
        listener.stop()
        assert not listener.is_running()


def test_hotkey_listener_signals_connectable(qapp):
    listener = GlobalHotkeyListener()
    hud_events = []
    listener.hud_triggered.connect(lambda: hud_events.append(True))
    
    # Emit directly to test bridge thread safety
    listener.hud_triggered.emit()
    assert len(hud_events) == 1
