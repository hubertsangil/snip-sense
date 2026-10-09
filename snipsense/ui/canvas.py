"""Full-screen multi-monitor transparent selection canvas for capturing regions."""

from __future__ import annotations
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtWidgets import QWidget
from snipsense.core.models import ScreenRegion


class SnipCanvas(QWidget):
    """Full-screen translucent canvas allowing the user to drag-select an area to capture."""

    snip_completed = pyqtSignal(ScreenRegion)
    snip_cancelled = pyqtSignal()

    def __init__(self, virtual_geometry: tuple[int, int, int, int]):
        super().__init__()
        self._vx, self._vy, self._vw, self._vh = virtual_geometry

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Set canvas geometry to exactly cover the entire virtual screen across all monitors
        self.setGeometry(self._vx, self._vy, self._vw, self._vh)

        self._start_pos: QPoint | None = None
        self._current_pos: QPoint | None = None
        self._is_selecting = False

    def get_selected_rect(self) -> QRect | None:
        """Returns the normalized QRect currently selected by the mouse drag."""
        if not self._start_pos or not self._current_pos:
            return None
        x = min(self._start_pos.x(), self._current_pos.x())
        y = min(self._start_pos.y(), self._current_pos.y())
        w = abs(self._current_pos.x() - self._start_pos.x())
        h = abs(self._current_pos.y() - self._start_pos.y())
        return QRect(x, y, w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Fill entire screen with semi-transparent dimming overlay (42% opacity)
        dim_color = QColor(0, 0, 0, 108)
        painter.fillRect(self.rect(), dim_color)

        rect = self.get_selected_rect()
        if rect and rect.width() > 0 and rect.height() > 0:
            # 2. Punch a completely clear hole for the selected area so the screen shines through
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)

            # 3. Draw dashed accent border around the selection cutout
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            border_pen = QPen(QColor("#3B82F6"), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

            # 4. Draw corner grab handles
            handle_size = 5
            handle_color = QColor("#F1F5F9")
            handles = [
                rect.topLeft(),
                rect.topRight(),
                rect.bottomLeft(),
                rect.bottomRight(),
            ]
            for pt in handles:
                painter.fillRect(
                    pt.x() - handle_size // 2,
                    pt.y() - handle_size // 2,
                    handle_size,
                    handle_size,
                    handle_color,
                )

            # 5. Render floating dimension badge next to cursor
            dim_text = f"{rect.width()} × {rect.height()} px"
            badge_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
            painter.setFont(badge_font)

            badge_w = 96
            badge_h = 22
            # Anchor badge slightly offset from bottom-right of selection
            bx = min(rect.right() + 8, self.width() - badge_w - 10)
            by = min(rect.bottom() + 8, self.height() - badge_h - 10)

            # Badge pill background
            painter.setPen(QPen(QColor("#262E3B"), 1))
            painter.setBrush(QBrush(QColor(11, 13, 16, 220)))
            painter.drawRoundedRect(bx, by, badge_w, badge_h, 4, 4)

            # Badge pill text
            painter.setPen(QColor("#F1F5F9"))
            painter.drawText(QRect(bx, by, badge_w, badge_h), Qt.AlignmentFlag.AlignCenter, dim_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self._is_selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancel_snip()

    def mouseMoveEvent(self, event):
        if self._is_selecting:
            self._current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self._is_selecting and event.button() == Qt.MouseButton.LeftButton:
            self._is_selecting = False
            rect = self.get_selected_rect()
            if rect and rect.width() >= 5 and rect.height() >= 5:
                # Map from widget coordinates back to virtual screen coordinates
                vx = self._vx + rect.x()
                vy = self._vy + rect.y()
                region = ScreenRegion(x=vx, y=vy, width=rect.width(), height=rect.height())
                self.hide()
                self.snip_completed.emit(region)
                self.close()
            else:
                # Reset if it was an accidental click without dragging
                self._start_pos = None
                self._current_pos = None
                self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_snip()
        else:
            super().keyPressEvent(event)

    def cancel_snip(self):
        """Cleanly dismisses the selection canvas without side effects."""
        self._is_selecting = False
        self.hide()
        self.snip_cancelled.emit()
        self.close()
