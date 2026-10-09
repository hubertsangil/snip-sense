"""Interactive image canvas widget supporting OCR text bounding boxes, hover tooltips, and click-to-copy."""

from PyQt6.QtCore import Qt, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap
from PyQt6.QtWidgets import QWidget, QApplication
from snipsense.core.models import OCRTextBox


class InteractiveImageCanvas(QWidget):
    """Custom canvas rendering the captured screenshot with clickable OCR text bounding boxes."""

    text_copied = pyqtSignal(str)

    def __init__(self, pixmap: QPixmap, ocr_boxes: list[OCRTextBox] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.ocr_boxes = ocr_boxes or []
        self.boxes_visible = True
        self.hovered_box: OCRTextBox | None = None
        self.copied_box: OCRTextBox | None = None

        self.setMouseTracking(True)
        self.setFixedSize(self.pixmap.size())

    def set_boxes_visible(self, visible: bool):
        """Toggles rendering of the OCR bounding box outlines."""
        self.boxes_visible = visible
        self.update()

    def _find_box_at(self, x: int, y: int) -> OCRTextBox | None:
        """Finds the first OCR text box containing the point (x, y)."""
        for box in self.ocr_boxes:
            if box.contains_point(x, y):
                return box
        return None

    def mouseMoveEvent(self, event):
        if not self.boxes_visible:
            self.hovered_box = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setToolTip("")
            self.update()
            return

        box = self._find_box_at(event.pos().x(), event.pos().y())
        if box != self.hovered_box:
            self.hovered_box = box
            if box:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                self.setToolTip(f"Click to copy: \"{box.text}\" (Confidence: {box.confidence:.0%})")
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self.setToolTip("")
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.hovered_box:
            # Copy clicked text block to system clipboard
            text = self.hovered_box.text
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

            # Trigger visual feedback on the clicked box
            self.copied_box = self.hovered_box
            self.text_copied.emit(text)
            self.update()

            # Reset copied highlight after 800ms
            QTimer.singleShot(800, self._reset_copied_box)
        else:
            super().mousePressEvent(event)

    def _reset_copied_box(self):
        self.copied_box = None
        self.update()

    def leaveEvent(self, event):
        """Clears hover state when mouse leaves canvas."""
        self.hovered_box = None
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Draw base screenshot pixmap
        painter.drawPixmap(0, 0, self.pixmap)

        if not self.boxes_visible:
            return

        # 2. Draw OCR bounding boxes
        for box in self.ocr_boxes:
            rect = QRect(box.x, box.y, box.width, box.height)

            if box == self.copied_box:
                # Copied confirmation: Vibrant Emerald glow
                pen = QPen(QColor("#10B981"), 1.5)
                brush = QBrush(QColor(16, 185, 129, 60))
            elif box == self.hovered_box:
                # Hovered state: Solid Blue accent with light tint
                pen = QPen(QColor("#3B82F6"), 1.5)
                brush = QBrush(QColor(59, 130, 246, 45))
            else:
                # Inactive state: Subtle dashed border
                pen = QPen(QColor(59, 130, 246, 110), 1, Qt.PenStyle.DashLine)
                brush = QBrush(Qt.BrushStyle.NoBrush)

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRoundedRect(rect, 2, 2)
