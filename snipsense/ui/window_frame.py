"""Custom borderless window container with dedicated modern control buttons (minimize, expand, exit)."""

from __future__ import annotations
from typing import Optional
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMainWindow,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtGui import QColor, QMouseEvent


class CustomTitleBar(QWidget):
    """Modern borderless titlebar with window dragging and dedicated minimize, expand, exit buttons."""

    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(
        self,
        parent_window: QWidget,
        title: str = "SnipSense",
        badge_text: Optional[str] = None,
        can_maximize: bool = True,
        can_minimize: bool = True,
    ):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.can_maximize = can_maximize
        self.can_minimize = can_minimize
        self._drag_pos: Optional[QPoint] = None

        self.setObjectName("customTitleBar")
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 10, 4)
        layout.setSpacing(10)

        # 1. Left Side: Brand Icon & Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleBarTitle")
        self.title_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #F8FAFC; letter-spacing: -0.2px;")
        layout.addWidget(self.title_label)

        if badge_text:
            self.badge_label = QLabel(badge_text)
            self.badge_label.setObjectName("statusBadge")
            layout.addWidget(self.badge_label)
        else:
            self.badge_label = None

        layout.addStretch()

        # 2. Right Side: Dedicated Control Buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Minimize Button
        if self.can_minimize:
            self.btn_minimize = QPushButton("—")
            self.btn_minimize.setObjectName("winBtnMinimize")
            self.btn_minimize.setToolTip("Minimize to tray / taskbar")
            self.btn_minimize.setFixedSize(28, 26)
            self.btn_minimize.clicked.connect(self._on_minimize)
            controls_layout.addWidget(self.btn_minimize)
        else:
            self.btn_minimize = None

        # Expand / Maximize Button
        if self.can_maximize:
            self.btn_maximize = QPushButton("□")
            self.btn_maximize.setObjectName("winBtnMaximize")
            self.btn_maximize.setToolTip("Expand / Restore window")
            self.btn_maximize.setFixedSize(28, 26)
            self.btn_maximize.clicked.connect(self._on_maximize)
            controls_layout.addWidget(self.btn_maximize)
        else:
            self.btn_maximize = None

        # Exit / Close Button
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("winBtnClose")
        self.btn_close.setToolTip("Close")
        self.btn_close.setFixedSize(28, 26)
        self.btn_close.clicked.connect(self._on_close)
        controls_layout.addWidget(self.btn_close)

        layout.addLayout(controls_layout)

    def set_title(self, title: str):
        """Updates title label text."""
        self.title_label.setText(title)

    def set_badge_text(self, text: str):
        """Updates badge text if present."""
        if self.badge_label:
            self.badge_label.setText(text)

    def update_maximize_icon(self):
        """Updates icon between maximize (□) and restore (❐)."""
        if self.btn_maximize and self.parent_window:
            if self.parent_window.isMaximized():
                self.btn_maximize.setText("❐")
                self.btn_maximize.setToolTip("Restore window")
            else:
                self.btn_maximize.setText("□")
                self.btn_maximize.setToolTip("Expand / Maximize")

    def _on_minimize(self):
        self.minimize_clicked.emit()
        if self.parent_window:
            self.parent_window.showMinimized()

    def _on_maximize(self):
        self.maximize_clicked.emit()
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
            else:
                self.parent_window.showMaximized()
            self.update_maximize_icon()

    def _on_close(self):
        self.close_clicked.emit()
        if self.parent_window:
            self.parent_window.close()

    # Window Dragging & Double Click Maximize Handling
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_window:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton and self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
                self.update_maximize_icon()
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.can_maximize:
            self._on_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class CustomWindowContainer(QFrame):
    """Frameless modern window container frame with drop shadow and custom titlebar."""

    def __init__(
        self,
        parent_window: QWidget,
        title: str = "SnipSense",
        badge_text: Optional[str] = None,
        can_maximize: bool = True,
        can_minimize: bool = True,
    ):
        super().__init__(parent_window)
        self.setObjectName("windowFrame")

        # Container layout
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # Title bar
        self.title_bar = CustomTitleBar(
            parent_window=parent_window,
            title=title,
            badge_text=badge_text,
            can_maximize=can_maximize,
            can_minimize=can_minimize,
        )
        self.root_layout.addWidget(self.title_bar)

        # Client content body
        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("windowContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(18, 14, 18, 16)
        self.content_layout.setSpacing(12)
        self.root_layout.addWidget(self.content_widget, stretch=1)

    def add_content_widget(self, widget: QWidget, stretch: int = 0):
        """Adds a widget to the central client area."""
        self.content_layout.addWidget(widget, stretch)

    def add_content_layout(self, layout, stretch: int = 0):
        """Adds a sub-layout to the central client area."""
        self.content_layout.addLayout(layout, stretch)
