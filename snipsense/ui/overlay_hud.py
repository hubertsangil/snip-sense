"""Surface 4: Frosted-Glass Overlay HUD (Alt + Z) matching DESIGN.md."""

from __future__ import annotations
import time
from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QApplication,
)
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QPainter, QColor, QCursor, QGuiApplication
from snipsense.core.vault import VaultDatabase, SearchResult
from snipsense.core.storage import StorageManager
from snipsense.ui.search_modal import format_relative_time
from snipsense.ui.styles import DARK_THEME_QSS


class RecentCaptureCard(QFrame):
    """Visual card for the horizontal recent captures carousel."""

    def __init__(self, result: SearchResult, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.result = result
        self.setObjectName("carouselCard")
        self.setFixedSize(170, 225)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(154, 92)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet(
            "background-color: #0B0D10; border-radius: 6px; border: 1px solid #1E2530;"
        )
        self._load_thumbnail(result.file_path)
        layout.addWidget(self.thumb_label)

        # 2. Title & Timestamp
        title_text = result.title if len(result.title) <= 18 else result.title[:15] + "..."
        self.title_label = QLabel(title_text)
        self.title_label.setStyleSheet("font-weight: 600; color: #F1F5F9; font-size: 12px;")
        layout.addWidget(self.title_label)

        info_row = QHBoxLayout()
        info_row.setSpacing(4)
        time_str = format_relative_time(result.created_at)
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet("color: #94A3B8; font-size: 10px;")
        info_row.addWidget(self.time_label)

        # Badge
        badge_text = "📋 Text" if result.ocr_text.strip() else "🖼️ Image"
        badge_color = "#34D399"
        badge_bg = "rgba(16, 185, 129, 0.15)"
        if "#masked" in result.tags.lower() or "shield" in result.tags.lower():
            badge_text = "🛡️ Masked"
            badge_color = "#818CF8"
            badge_bg = "rgba(99, 102, 241, 0.15)"
        self.badge_label = QLabel(badge_text)
        self.badge_label.setStyleSheet(
            f"background-color: {badge_bg}; color: {badge_color}; font-size: 9px; padding: 1px 4px; border-radius: 3px;"
        )
        info_row.addWidget(self.badge_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        layout.addStretch()

        # 3. Actions Row
        action_row = QHBoxLayout()
        action_row.setSpacing(4)

        self.copy_img_btn = QPushButton("🖼️")
        self.copy_img_btn.setToolTip("Copy Image to Clipboard")
        self.copy_img_btn.setObjectName("cardActionBtn")
        self.copy_img_btn.setFixedSize(32, 24)
        self.copy_img_btn.clicked.connect(self._copy_image)
        action_row.addWidget(self.copy_img_btn)

        self.copy_text_btn = QPushButton("📋")
        self.copy_text_btn.setToolTip("Copy OCR Text")
        self.copy_text_btn.setObjectName("cardActionBtn")
        self.copy_text_btn.setFixedSize(32, 24)
        self.copy_text_btn.clicked.connect(self._copy_text)
        action_row.addWidget(self.copy_text_btn)

        self.open_btn = QPushButton("📂 Open")
        self.open_btn.setToolTip("Open in File Explorer")
        self.open_btn.setObjectName("cardActionBtn")
        self.open_btn.setFixedHeight(24)
        self.open_btn.clicked.connect(self._open_file)
        action_row.addWidget(self.open_btn)

        layout.addLayout(action_row)

    def _load_thumbnail(self, path_str: str):
        path = Path(path_str)
        if path.exists():
            try:
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        154, 92,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.thumb_label.setPixmap(scaled)
                    return
            except Exception:
                pass
        self.thumb_label.setText("🖼️")

    def _copy_image(self):
        path = Path(self.result.file_path)
        if path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                QApplication.clipboard().setPixmap(pixmap)
                self.copy_img_btn.setText("✓")
                def _reset_img():
                    try:
                        self.copy_img_btn.setText("🖼️")
                    except (RuntimeError, Exception):
                        pass
                QTimer.singleShot(1000, _reset_img)

    def _copy_text(self):
        text = self.result.ocr_text or self.result.title
        QApplication.clipboard().setText(text)
        self.copy_text_btn.setText("✓")
        def _reset_txt():
            try:
                self.copy_text_btn.setText("📋")
            except (RuntimeError, Exception):
                pass
        QTimer.singleShot(1000, _reset_txt)

    def _open_file(self):
        StorageManager.open_in_explorer(Path(self.result.file_path))


class OverlayHUD(QDialog):
    """Frosted-glass modal HUD overlay (Alt + Z) as designed in Surface 4."""

    snip_requested = pyqtSignal()
    record_requested = pyqtSignal()
    search_requested = pyqtSignal()
    clean_duplicates_requested = pyqtSignal()

    _is_active_ready: bool = False

    def __init__(self, vault: Optional[VaultDatabase] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._is_active_ready = False
        self.vault = vault or VaultDatabase.get_instance()
        self.setObjectName("overlayHUD")
        self.setStyleSheet(DARK_THEME_QSS)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        # macOS: ensure tool windows remain visible even when app is not active
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        except Exception:
            pass
        self.setFixedSize(860, 520)
        self._carousel_cards: List[RecentCaptureCard] = []

        # Root layout centering the HUD container
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Centered frosted glass card container
        self.hud_container = QFrame(self)
        self.hud_container.setObjectName("hudContainer")
        self.hud_container.setFixedSize(860, 520)

        container_layout = QVBoxLayout(self.hud_container)
        container_layout.setContentsMargins(24, 20, 24, 20)
        container_layout.setSpacing(14)

        # 1. Header Bar
        header = QHBoxLayout()
        title = QLabel("🔮 SNIPSENSE")
        title.setObjectName("headerTitle")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F1F5F9; letter-spacing: 0.5px;")
        header.addWidget(title)

        offline_badge = QLabel("🟢 100% Offline | Zero Cloud")
        offline_badge.setObjectName("statusBadge")
        offline_badge.setStyleSheet(
            "background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 600;"
        )
        header.addWidget(offline_badge)

        header.addStretch()

        esc_btn = QPushButton("✕ ESC to Close")
        esc_btn.setObjectName("closeBtn")
        esc_btn.clicked.connect(self.close)
        header.addWidget(esc_btn)
        container_layout.addLayout(header)

        # Divider
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("color: #1E2530; background-color: #1E2530; height: 1px; border: none;")
        container_layout.addWidget(line1)

        # 2. Quick Actions Section
        action_sec_title = QLabel("QUICK ACTIONS")
        action_sec_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;")
        container_layout.addWidget(action_sec_title)

        actions_grid = QHBoxLayout()
        actions_grid.setSpacing(12)

        # Action 1: Snip Area
        self.snip_action_btn = self._create_quick_action_btn(
            "✂️ Snip Area", "Ctrl+Shift+S", self._on_snip_clicked
        )
        actions_grid.addWidget(self.snip_action_btn)

        # Action 2: Record Clip
        self.record_action_btn = self._create_quick_action_btn(
            "⏺️ Record Clip", "Up to 30s", self._on_record_clicked
        )
        actions_grid.addWidget(self.record_action_btn)

        # Action 3: Search Vault
        self.search_action_btn = self._create_quick_action_btn(
            "🔍 Search Vault", "Alt + F", self._on_search_clicked
        )
        actions_grid.addWidget(self.search_action_btn)

        # Action 4: Clean Duplicates
        self.clean_dups_btn = self._create_quick_action_btn(
            "🧹 Clean Duplicates", "Perceptual Hash", self._on_clean_dups_clicked
        )
        actions_grid.addWidget(self.clean_dups_btn)

        container_layout.addLayout(actions_grid)

        # 3. Recent Captures Carousel Header
        carousel_header = QHBoxLayout()
        recent_title = QLabel("RECENT CAPTURES")
        recent_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;")
        carousel_header.addWidget(recent_title)
        carousel_header.addStretch()

        self.view_all_btn = QPushButton("View All in Vault →")
        self.view_all_btn.setObjectName("ghostAction")
        self.view_all_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.view_all_btn.clicked.connect(self._on_search_clicked)
        carousel_header.addWidget(self.view_all_btn)
        container_layout.addLayout(carousel_header)

        # Scrollable Carousel
        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedHeight(235)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #1E2530;
                border-radius: 8px;
                background-color: #0E1217;
            }
        """)

        self.carousel_container = QWidget()
        self.carousel_container.setStyleSheet("background-color: transparent;")
        self.carousel_layout = QHBoxLayout(self.carousel_container)
        self.carousel_layout.setContentsMargins(8, 8, 8, 8)
        self.carousel_layout.setSpacing(12)
        self.carousel_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.carousel_container)
        container_layout.addWidget(self.scroll_area)

        # 4. Footer Telemetry
        total_count = self.vault.count_total()
        self.footer_label = QLabel(
            f"STATUS: {total_count} historical screenshots indexed • 100% Zero Cloud Egress"
        )
        self.footer_label.setStyleSheet("color: #64748B; font-size: 11px;")
        container_layout.addWidget(self.footer_label)

        root_layout.addWidget(self.hud_container)

        # Shortcuts & Focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        esc_shortcut.activated.connect(self.close)

        # Populate
        self.refresh_carousel()

    def _create_quick_action_btn(self, title: str, subtitle: str, callback) -> QPushButton:
        btn = QPushButton(f"{title}\n{subtitle}")
        btn.setObjectName("hudActionBtn")
        btn.setFixedHeight(54)
        btn.clicked.connect(callback)
        return btn

    def refresh_carousel(self):
        """Loads the most recent 10 captures from the database into the carousel."""
        while self.carousel_layout.count():
            item = self.carousel_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._carousel_cards.clear()

        recent_items = self.vault.search("", limit=10)
        total_count = self.vault.count_total()
        self.footer_label.setText(
            f"STATUS: {total_count} historical screenshots indexed • 100% Zero Cloud Egress"
        )

        if not recent_items:
            empty_label = QLabel("No captures in visual memory yet. Take a snip with Ctrl+Shift+S!")
            empty_label.setStyleSheet("color: #64748B; font-size: 12px; padding: 20px;")
            self.carousel_layout.addWidget(empty_label)
            return

        for res in recent_items:
            card = RecentCaptureCard(res, parent=self.carousel_container)
            self.carousel_layout.addWidget(card)
            self._carousel_cards.append(card)

    def get_carousel_cards(self) -> List[RecentCaptureCard]:
        """Returns the list of active capture cards in the carousel."""
        return self._carousel_cards

    def showEvent(self, event):
        """Deferred activation so macOS window server grants input focus even from background."""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        # Defer activation pass so event loop completes initial window display
        QTimer.singleShot(30, self._force_activate)

    def _force_activate(self):
        """Forces macOS to bring the app and this window to the foreground."""
        import sys
        if sys.platform == "darwin":
            try:
                from AppKit import (
                    NSApplication,
                    NSRunningApplication,
                    NSApplicationActivateIgnoringOtherApps,
                    NSApplicationActivateAllWindows,
                )
                nsapp = NSApplication.sharedApplication()
                nsapp.activateIgnoringOtherApps_(True)
                cur_app = NSRunningApplication.currentApplication()
                if cur_app:
                    cur_app.activateWithOptions_(
                        NSApplicationActivateIgnoringOtherApps | NSApplicationActivateAllWindows
                    )
            except Exception:
                pass

            try:
                import ctypes, objc
                win_id = int(self.winId())
                if win_id > 65535:
                    nsview = objc.objc_object(c_void_p=ctypes.c_void_p(win_id))
                    nswindow = nsview.window()
                    if nswindow:
                        nswindow.orderFrontRegardless()
                        nswindow.makeKeyAndOrderFront_(None)
                        nswindow.makeKeyWindow()
            except Exception:
                pass

        self._is_active_ready = True
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def changeEvent(self, event):
        """Auto-dismisses HUD when user switches or clicks away to another window/app."""
        from PyQt6.QtCore import QEvent
        if getattr(self, "_is_active_ready", False) and event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.close()
        super().changeEvent(event)

    def paintEvent(self, event):
        """Renders translucent dark frosted-glass backdrop across the display."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(11, 13, 16, 175))

    def mousePressEvent(self, event):
        """Dismisses the HUD when clicking outside the centered HUD card."""
        pos = event.position().toPoint()
        if hasattr(self, "hud_container") and self.hud_container is not None:
            if not self.hud_container.geometry().contains(pos):
                self.close()
                return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        """Dismisses the HUD when Escape is pressed."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def _on_snip_clicked(self):
        self.close()
        self.snip_requested.emit()

    def _on_record_clicked(self):
        self.close()
        self.record_requested.emit()

    def _on_search_clicked(self):
        self.close()
        self.search_requested.emit()

    def _on_clean_dups_clicked(self):
        self.close()
        self.clean_duplicates_requested.emit()
