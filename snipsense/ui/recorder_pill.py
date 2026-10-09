"""Floating draggable recording pill widget (Surface 6) with pulsing indicator and timer."""

from __future__ import annotations
from typing import Optional
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
)
from snipsense.ui.styles import DARK_THEME_QSS
from snipsense.ui.motion import start_breathing_pulse, stop_breathing_pulse


class RecorderPill(QWidget):
    """Floating draggable on-screen recording HUD with elapsed timer and stop action."""

    stop_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, max_duration_seconds: float = 30.0, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.max_duration = max_duration_seconds
        self._drag_pos: Optional[QPoint] = None
        self._pulse_state = False

        # Window Flags: Frameless, Floating on top, Tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("recorderPillContainer")
        self.setStyleSheet(DARK_THEME_QSS)

        self._init_ui()
        self._init_timer()
        self._center_top_screen()

    def _init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Main pill frame
        self.pill_frame = QFrame()
        self.pill_frame.setObjectName("pillFrame")
        self.pill_frame.setStyleSheet("""
            QFrame#pillFrame {
                background-color: rgba(32, 32, 32, 0.95);
                border: 1px solid #383838;
                border-radius: 18px;
                padding: 4px 12px;
            }
        """)

        layout = QHBoxLayout(self.pill_frame)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        # Pulsing REC indicator with purposeful breathing motion
        self.rec_indicator = QLabel("🔴 REC")
        self.rec_indicator.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.rec_indicator)
        start_breathing_pulse(self.rec_indicator, min_opacity=0.35, max_opacity=1.0, duration_ms=850)

        # Timer label
        self.timer_label = QLabel(f"00:00 / {int(self.max_duration):02d}:00")
        self.timer_label.setStyleSheet("color: #F3F3F3; font-weight: 600; font-family: monospace; font-size: 13px;")
        layout.addWidget(self.timer_label)

        # Stop button
        self.stop_btn = QPushButton("Stop & Save")
        self.stop_btn.setObjectName("primaryAction")
        self.stop_btn.setStyleSheet("""
            QPushButton#primaryAction {
                background-color: #0067C0;
                color: #FFFFFF;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton#primaryAction:hover {
                background-color: #1170CF;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        layout.addWidget(self.stop_btn)

        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setObjectName("closeBtn")
        self.cancel_btn.setStyleSheet("""
            QPushButton#closeBtn {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 2px 6px;
            }
            QPushButton#closeBtn:hover {
                color: #F43F5E;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(self.cancel_btn)

        root_layout.addWidget(self.pill_frame)
        self.adjustSize()

    def _init_timer(self):
        self.pulse_timer = QTimer(self)
        self.pulse_timer.setInterval(500)
        self.pulse_timer.timeout.connect(self._toggle_pulse)
        self.pulse_timer.start()

    def _toggle_pulse(self):
        self._pulse_state = not self._pulse_state
        if self._pulse_state:
            self.rec_indicator.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 12px;")
        else:
            self.rec_indicator.setStyleSheet("color: #7F1D1D; font-weight: bold; font-size: 12px;")

    def update_time(self, elapsed: float, max_duration: Optional[float] = None):
        """Updates the elapsed and total time text."""
        limit = max_duration if max_duration is not None else self.max_duration
        elapsed_clamped = min(elapsed, limit)

        el_min = int(elapsed_clamped // 60)
        el_sec = int(elapsed_clamped % 60)

        max_min = int(limit // 60)
        max_sec = int(limit % 60)

        self.timer_label.setText(f"{el_min:02d}:{el_sec:02d} / {max_min:02d}:{max_sec:02d}")

    def _center_top_screen(self):
        """Positions the pill horizontally centered near the top of the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            pill_width = self.width() or 280
            x = geom.x() + (geom.width() - pill_width) // 2
            y = geom.y() + 40
            self.move(x, y)

    # Mouse drag events
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def closeEvent(self, event):
        stop_breathing_pulse(self.rec_indicator)
        if hasattr(self, "pulse_timer") and self.pulse_timer.isActive():
            self.pulse_timer.stop()
        super().closeEvent(event)
