"""Unit tests for purposeful motion and interaction design module."""

import os
import pytest
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt

from snipsense.ui.motion import (
    is_reduced_motion,
    animate_window_entrance,
    animate_window_exit,
    start_breathing_pulse,
    stop_breathing_pulse,
    animate_badge_toast,
)


def test_is_reduced_motion(monkeypatch):
    monkeypatch.delenv("SNIPSENSE_REDUCED_MOTION", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert is_reduced_motion() is False

    monkeypatch.setenv("SNIPSENSE_REDUCED_MOTION", "1")
    assert is_reduced_motion() is True


def test_animate_window_entrance(qtbot):
    win = QWidget()
    qtbot.addWidget(win)
    win.resize(200, 200)

    group = animate_window_entrance(win, duration_ms=50, slide_px=4, force=True)
    assert group is not None
    assert getattr(win, "_entrance_animation", None) is not None
    group.stop()


def test_animate_window_entrance_reduced_motion(qtbot, monkeypatch):
    monkeypatch.setenv("SNIPSENSE_REDUCED_MOTION", "1")
    win = QWidget()
    qtbot.addWidget(win)

    result = animate_window_entrance(win, duration_ms=50)
    assert result is None
    assert win.windowOpacity() == 1.0


def test_animate_window_exit(qtbot):
    win = QWidget()
    qtbot.addWidget(win)
    win.show()
    assert win.isVisible()

    callback_called = []
    anim = animate_window_exit(
        win,
        on_finished=lambda: callback_called.append(True),
        duration_ms=50,
        force=True,
    )
    assert anim is not None
    qtbot.waitUntil(lambda: len(callback_called) == 1, timeout=1000)


def test_breathing_pulse_lifecycle(qtbot):
    label = QLabel("🔴 REC")
    qtbot.addWidget(label)

    anim = start_breathing_pulse(label, min_opacity=0.3, max_opacity=1.0, duration_ms=100, force=True)
    assert anim is not None
    assert getattr(label, "_pulse_animation", None) is not None

    stop_breathing_pulse(label)
    assert getattr(label, "_pulse_animation", None) is None


def test_animate_badge_toast(qtbot):
    badge = QLabel("Initial Text")
    qtbot.addWidget(badge)

    animate_badge_toast(
        badge,
        message="Saved!",
        original_text="Initial Text",
        toast_style="color: #10B981;",
        fade_duration_ms=40,
        hold_ms=100,
        force=True,
    )

    # Immediately text should reflect toast message
    assert badge.text() == "Saved!"
