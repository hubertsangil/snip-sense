"""Purposeful motion and interaction design helpers for SnipSense.

Adheres to Windows 11 Fluent and Interaction Design guidelines:
- 100-150ms: Micro-feedback (hovers, clicks, badge transitions)
- 150-250ms: Window entrances and exits with OutCubic/InQuad deceleration
- Continuous: Subtle breathing pulses for live recording indicators
- Respects reduced motion settings and headless test environments
"""

from __future__ import annotations

import os
from typing import Callable, Optional
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QEasingCurve,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QTimer,
)
from PyQt6.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect


def is_reduced_motion() -> bool:
    """Returns True if the system or user requested reduced motion or in automated test suite."""
    return (
        os.environ.get("SNIPSENSE_REDUCED_MOTION") == "1"
        or os.environ.get("PYTEST_CURRENT_TEST") is not None
    )


def animate_window_entrance(
    window: QWidget,
    duration_ms: int = 180,
    slide_px: int = 6,
    force: bool = False,
) -> Optional[QParallelAnimationGroup]:
    """Gracefully introduces a window with decelerated fade-in and subtle upward settle.
    
    Communicates orientation and focus without delaying user interaction.
    """
    if (not force and is_reduced_motion()) or duration_ms <= 0:
        window.setWindowOpacity(1.0)
        return None

    # Set starting opacity
    window.setWindowOpacity(0.0)

    group = QParallelAnimationGroup(window)

    # 1. Opacity fade-in (0.0 -> 1.0)
    fade_anim = QPropertyAnimation(window, b"windowOpacity", group)
    fade_anim.setDuration(duration_ms)
    fade_anim.setStartValue(0.0)
    fade_anim.setEndValue(1.0)
    fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    group.addAnimation(fade_anim)

    # 2. Subtle vertical settle (y + slide_px -> y)
    if slide_px > 0:
        target_pos = window.pos()
        start_pos = QPoint(target_pos.x(), target_pos.y() + slide_px)
        window.move(start_pos)

        pos_anim = QPropertyAnimation(window, b"pos", group)
        pos_anim.setDuration(duration_ms)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(target_pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(pos_anim)

    setattr(window, "_entrance_animation", group)

    def _cleanup():
        try:
            window.setWindowOpacity(1.0)
        except RuntimeError:
            pass

    group.finished.connect(_cleanup)
    try:
        window.destroyed.connect(group.stop)
    except Exception:
        pass

    group.start()
    return group


def animate_window_exit(
    window: QWidget,
    on_finished: Optional[Callable[[], None]] = None,
    duration_ms: int = 130,
    force: bool = False,
) -> Optional[QPropertyAnimation]:
    """Gracefully exits a window with accelerated fade-out before hiding/closing.
    
    Provides continuity and prevents harsh visual pops when dismissing.
    """
    if (not force and is_reduced_motion()) or duration_ms <= 0 or not window.isVisible():
        if on_finished:
            on_finished()
        return None

    fade_anim = QPropertyAnimation(window, b"windowOpacity", window)
    fade_anim.setDuration(duration_ms)
    fade_anim.setStartValue(window.windowOpacity())
    fade_anim.setEndValue(0.0)
    fade_anim.setEasingCurve(QEasingCurve.Type.InQuad)

    setattr(window, "_exit_animation", fade_anim)

    def _on_done():
        if on_finished:
            on_finished()

    fade_anim.finished.connect(_on_done)
    try:
        window.destroyed.connect(fade_anim.stop)
    except Exception:
        pass

    fade_anim.start()
    return fade_anim


def start_breathing_pulse(
    widget: QWidget,
    min_opacity: float = 0.35,
    max_opacity: float = 1.0,
    duration_ms: int = 850,
    force: bool = False,
) -> Optional[QPropertyAnimation]:
    """Applies a smooth continuous breathing opacity oscillation to widget.
    
    Communicates ongoing background activity (such as active screen recording)
    with calm, organic rhythm instead of harsh, sudden binary blinking.
    """
    if not force and is_reduced_motion():
        return None

    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration_ms)
    anim.setKeyValueAt(0.0, max_opacity)
    anim.setKeyValueAt(0.5, min_opacity)
    anim.setKeyValueAt(1.0, max_opacity)
    anim.setEasingCurve(QEasingCurve.Type.InOutSine)
    anim.setLoopCount(-1)

    setattr(widget, "_pulse_animation", anim)
    try:
        widget.destroyed.connect(anim.stop)
    except Exception:
        pass

    anim.start()
    return anim


def stop_breathing_pulse(widget: QWidget) -> None:
    """Stops the breathing pulse and restores full widget opacity."""
    anim = getattr(widget, "_pulse_animation", None)
    if anim:
        anim.stop()
        setattr(widget, "_pulse_animation", None)

    try:
        effect = widget.graphicsEffect()
        if isinstance(effect, QGraphicsOpacityEffect):
            effect.setOpacity(1.0)
    except RuntimeError:
        pass


def animate_badge_toast(
    badge: QLabel,
    message: str,
    original_text: Optional[str] = None,
    original_style: str = "",
    toast_style: str = "",
    fade_duration_ms: int = 140,
    hold_ms: int = 2000,
    force: bool = False,
) -> None:
    """Animates a transient status confirmation on a badge label.
    
    Applies text immediately for test/screen-reader reliability, animates a brief
    decelerating pulse, holds, then smoothly restores original text.
    """
    if original_text is None:
        original_text = badge.text()

    badge.setText(message)
    if toast_style:
        badge.setStyleSheet(toast_style)

    if (not force and is_reduced_motion()) or fade_duration_ms <= 0:
        def _simple_restore():
            try:
                badge.setText(original_text)
                badge.setStyleSheet(original_style)
            except (RuntimeError, Exception):
                pass
        QTimer.singleShot(hold_ms, _simple_restore)
        return

    effect = badge.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(badge)
        badge.setGraphicsEffect(effect)

    # Decelerated entrance pulse from 0.4 -> 1.0
    pulse_in = QPropertyAnimation(effect, b"opacity", badge)
    pulse_in.setDuration(fade_duration_ms)
    pulse_in.setStartValue(0.4)
    pulse_in.setEndValue(1.0)
    pulse_in.setEasingCurve(QEasingCurve.Type.OutCubic)
    pulse_in.start()
    setattr(badge, "_toast_pulse_in", pulse_in)

    def _start_restore():
        try:
            fade_out = QPropertyAnimation(effect, b"opacity", badge)
            fade_out.setDuration(fade_duration_ms)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.2)
            fade_out.setEasingCurve(QEasingCurve.Type.InQuad)

            def _finish_restore():
                try:
                    badge.setText(original_text)
                    badge.setStyleSheet(original_style)
                    fade_back = QPropertyAnimation(effect, b"opacity", badge)
                    fade_back.setDuration(fade_duration_ms)
                    fade_back.setStartValue(0.2)
                    fade_back.setEndValue(1.0)
                    fade_back.setEasingCurve(QEasingCurve.Type.OutCubic)
                    fade_back.start()
                    setattr(badge, "_toast_fade_back", fade_back)
                except (RuntimeError, Exception):
                    pass

            fade_out.finished.connect(_finish_restore)
            fade_out.start()
            setattr(badge, "_toast_fade_out", fade_out)
        except (RuntimeError, Exception):
            pass

    QTimer.singleShot(hold_ms, _start_restore)
