"""Full-screen multi-monitor transparent selection canvas for capturing regions."""

from __future__ import annotations
import io
from PIL import Image
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QImage, QRegion
from PyQt6.QtWidgets import QWidget
from snipsense.core.models import ScreenRegion


def qpixmap_to_pil(pixmap: QPixmap) -> Image.Image:
    """Converts a QPixmap into a PIL Image RGB buffer with sub-5ms latency."""
    try:
        qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        raw_bytes = qimg.bits().asstring(qimg.bytesPerLine() * qimg.height())
        return Image.frombuffer(
            "RGBA",
            (qimg.width(), qimg.height()),
            raw_bytes,
            "raw",
            "RGBA",
            qimg.bytesPerLine(),
            1,
        ).convert("RGB")
    except Exception:
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.ReadWrite)
        pixmap.save(buffer, "PNG")
        return Image.open(io.BytesIO(buffer.data().data())).convert("RGB")


class SnipCanvas(QWidget):
    """Full-screen canvas displaying frozen desktop buffer and allowing drag-selection capture."""

    snip_completed = pyqtSignal([ScreenRegion, object], [ScreenRegion])
    snip_cancelled = pyqtSignal()

    def __init__(
        self,
        virtual_geometry: tuple[int, int, int, int],
        frozen_pixmap: QPixmap | None = None,
        dpr: float = 1.0,
    ):
        super().__init__()
        self._vx, self._vy, self._vw, self._vh = virtual_geometry
        self._frozen_pixmap: QPixmap | None = frozen_pixmap
        self._dpr: float = dpr if dpr > 0 else 1.0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Cover the entire virtual screen across all monitors in logical coordinates
        self.setGeometry(self._vx, self._vy, self._vw, self._vh)

        self._start_pos: QPoint | None = None
        self._current_pos: QPoint | None = None
        self._is_selecting = False

    def _clamp_pos(self, pos: QPoint) -> QPoint:
        """Clamps mouse coordinates to canvas boundaries to ensure edge and corner clicks register."""
        cx = max(0, min(pos.x(), max(0, self.width() - 1)))
        cy = max(0, min(pos.y(), max(0, self.height() - 1)))
        return QPoint(cx, cy)

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

        rect = self.get_selected_rect()

        # 1. Background rendering
        if self._frozen_pixmap and not self._frozen_pixmap.isNull():
            # Draw frozen desktop snapshot
            painter.drawPixmap(self.rect(), self._frozen_pixmap)
            # Dim regions outside the current selection cutout
            if rect and rect.width() > 0 and rect.height() > 0:
                dim_region = QRegion(self.rect()).subtracted(QRegion(rect))
                painter.setClipRegion(dim_region)
                painter.fillRect(self.rect(), QColor(0, 0, 0, 108))
                painter.setClipping(False)
            else:
                painter.fillRect(self.rect(), QColor(0, 0, 0, 108))
        else:
            # Translucent fallback when no frozen pixmap is provided
            dim_color = QColor(0, 0, 0, 108)
            painter.fillRect(self.rect(), dim_color)
            if rect and rect.width() > 0 and rect.height() > 0:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # 2. Render selection styling if active
        if rect and rect.width() > 0 and rect.height() > 0:
            border_pen = QPen(QColor("#3B82F6"), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

            # Grab handles
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

            # Dimension badge
            dim_text = f"{rect.width()} × {rect.height()} px"
            badge_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
            painter.setFont(badge_font)

            badge_w = 96
            badge_h = 22
            bx = min(rect.right() + 8, self.width() - badge_w - 10)
            by = min(rect.bottom() + 8, self.height() - badge_h - 10)

            painter.setPen(QPen(QColor("#262E3B"), 1))
            painter.setBrush(QBrush(QColor(11, 13, 16, 220)))
            painter.drawRoundedRect(bx, by, badge_w, badge_h, 4, 4)

            painter.setPen(QColor("#F1F5F9"))
            painter.drawText(QRect(bx, by, badge_w, badge_h), Qt.AlignmentFlag.AlignCenter, dim_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self._clamp_pos(event.pos())
            self._start_pos = pos
            self._current_pos = pos
            self._is_selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancel_snip()

    def mouseMoveEvent(self, event):
        if self._is_selecting:
            self._current_pos = self._clamp_pos(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if self._is_selecting and event.button() == Qt.MouseButton.LeftButton:
            self._is_selecting = False
            self._current_pos = self._clamp_pos(event.pos())
            rect = self.get_selected_rect()
            if rect and rect.width() >= 5 and rect.height() >= 5:
                # Map from widget coordinates back to virtual screen coordinates
                vx = self._vx + rect.x()
                vy = self._vy + rect.y()
                region = ScreenRegion(x=vx, y=vy, width=rect.width(), height=rect.height())

                # Slice directly from frozen pixmap using precise scale ratio
                cropped_img = None
                if self._frozen_pixmap and not self._frozen_pixmap.isNull():
                    scale_x = self._frozen_pixmap.width() / max(1, self.width())
                    scale_y = self._frozen_pixmap.height() / max(1, self.height())
                    px = max(0, int(round(rect.x() * scale_x)))
                    py = max(0, int(round(rect.y() * scale_y)))
                    pw = max(1, int(round(rect.width() * scale_x)))
                    ph = max(1, int(round(rect.height() * scale_y)))

                    if px + pw > self._frozen_pixmap.width():
                        pw = max(1, self._frozen_pixmap.width() - px)
                    if py + ph > self._frozen_pixmap.height():
                        ph = max(1, self._frozen_pixmap.height() - py)

                    cropped_pixmap = self._frozen_pixmap.copy(px, py, pw, ph)
                    cropped_img = qpixmap_to_pil(cropped_pixmap)

                self.hide()
                self.snip_completed.emit(region, cropped_img)
                self.close()
            else:
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
