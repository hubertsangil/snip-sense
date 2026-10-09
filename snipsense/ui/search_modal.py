"""Visual Memory Search Modal (Surface 5) utilizing SQLite FTS5 index."""

from __future__ import annotations
import time
from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QApplication,
    QFrame,
)
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut
from PIL import Image
from snipsense.core.vault import VaultDatabase, SearchResult
from snipsense.core.storage import StorageManager
from snipsense.ui.styles import DARK_THEME_QSS


def format_relative_time(timestamp: float) -> str:
    """Formats a unix timestamp into human-readable relative time (e.g. '10m ago')."""
    diff = max(0, time.time() - timestamp)
    if diff < 60:
        return "just now"
    elif diff < 3600:
        return f"{int(diff // 60)}m ago"
    elif diff < 86400:
        return f"{int(diff // 3600)}h ago"
    else:
        return f"{int(diff // 86400)}d ago"


class SearchResultCard(QFrame):
    """Custom widget card presenting a single search match with thumbnail and quick actions."""

    def __init__(self, result: SearchResult, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.result = result
        self.setObjectName("resultCard")
        self.setStyleSheet("""
            #resultCard {
                background-color: #121721;
                border: 1px solid #1E2736;
                border-radius: 10px;
                padding: 6px;
            }
            #resultCard:hover {
                background-color: #18202D;
                border-color: #3B82F6;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # 1. Image Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(64, 46)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #0A0D13; border-radius: 6px; border: 1px solid #1E2633;")
        self._load_thumbnail(result.file_path)
        layout.addWidget(self.thumb_label)

        # 2. Text Details
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        header_row = QHBoxLayout()
        self.title_label = QLabel(result.title)
        self.title_label.setStyleSheet("font-weight: 600; color: #F8FAFC; font-size: 13px;")
        header_row.addWidget(self.title_label)

        time_str = format_relative_time(result.created_at)
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 500;")
        header_row.addWidget(self.time_label)
        header_row.addStretch()
        text_layout.addLayout(header_row)

        # Snippet with highlight formatting
        snippet_html = self._format_snippet_html(result.snippet)
        self.snippet_label = QLabel(snippet_html)
        self.snippet_label.setTextFormat(Qt.TextFormat.RichText)
        self.snippet_label.setWordWrap(True)
        self.snippet_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        text_layout.addWidget(self.snippet_label)

        layout.addLayout(text_layout, stretch=1)

        # 3. Action Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.copy_text_btn = QPushButton("📋 Copy Text")
        self.copy_text_btn.setObjectName("ghostAction")
        self.copy_text_btn.setFixedHeight(26)
        self.copy_text_btn.setStyleSheet("font-size: 11px; padding: 2px 8px; border-radius: 6px;")
        self.copy_text_btn.clicked.connect(self._copy_text)
        btn_layout.addWidget(self.copy_text_btn)

        self.open_file_btn = QPushButton("📂 Open")
        self.open_file_btn.setObjectName("ghostAction")
        self.open_file_btn.setFixedHeight(26)
        self.open_file_btn.setStyleSheet("font-size: 11px; padding: 2px 8px; border-radius: 6px;")
        self.open_file_btn.clicked.connect(self._open_file)
        btn_layout.addWidget(self.open_file_btn)

        layout.addLayout(btn_layout)

    def _format_snippet_html(self, raw_snippet: str) -> str:
        """Converts <mark> tags to styled HTML spans for rich text display."""
        # Replace <mark> with glowing green/emerald styling
        styled = raw_snippet.replace("<mark>", "<span style='color: #34D399; font-weight: bold; background-color: rgba(16, 185, 129, 0.2); border-radius: 2px;'>")
        styled = styled.replace("</mark>", "</span>")
        return f"<span>{styled}</span>"

    def _load_thumbnail(self, path_str: str):
        """Loads and scales a thumbnail from the image file on disk."""
        path = Path(path_str)
        if path.exists():
            try:
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        64, 48,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.thumb_label.setPixmap(scaled)
                    return
            except Exception:
                pass
        self.thumb_label.setText("🖼️")

    def _copy_text(self):
        clipboard = QApplication.clipboard()
        text_to_copy = self.result.ocr_text or self.result.title
        clipboard.setText(text_to_copy)

        self.copy_text_btn.setText("✓ Copied!")
        self.copy_text_btn.setStyleSheet("background-color: #059669; color: #FFFFFF; font-size: 11px; padding: 2px 8px;")
        QTimer.singleShot(1200, lambda: self.copy_text_btn.setText("📋 Copy Text"))
        QTimer.singleShot(1200, lambda: self.copy_text_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;"))

    def _open_file(self):
        path = Path(self.result.file_path)
        StorageManager.open_in_explorer(path)


class SearchModal(QDialog):
    """Visual Memory Search launcher (Alt + F) with real-time FTS5 query dispatch."""

    def __init__(self, vault: Optional[VaultDatabase] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.vault = vault or VaultDatabase.get_instance()
        self.setObjectName("searchModal")
        self.setStyleSheet(DARK_THEME_QSS)
        self.setWindowTitle("Visual Memory Search — SnipSense")
        self.resize(680, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Search Bar
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("🔍 Search screenshot text, titles, or tags... (Press Esc to close)")
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self._on_search_query_changed)
        search_row.addWidget(self.search_input)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("ghostAction")
        close_btn.setFixedSize(38, 38)
        close_btn.clicked.connect(self.close)
        search_row.addWidget(close_btn)

        layout.addLayout(search_row)

        # Results Count Status
        self.status_label = QLabel("Recent Captures")
        self.status_label.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.status_label)

        # Results List Widget
        self.results_list = QListWidget()
        self.results_list.setObjectName("resultsList")
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #0A0D13;
                border: 1px solid #1E2633;
                border-radius: 10px;
                padding: 6px;
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
                margin-bottom: 6px;
            }
        """)
        self.results_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.results_list)

        # Footer Hint
        footer = QHBoxLayout()
        hint = QLabel("↑ ↓ navigate  •  ↵ open  •  Esc close")
        hint.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 500;")
        footer.addWidget(hint)
        footer.addStretch()
        layout.addLayout(footer)

        # Keyboard shortcuts
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self.close)

        # Initial populate
        self.perform_search("")

    def _on_search_query_changed(self, text: str):
        self.perform_search(text)

    def perform_search(self, query: str):
        """Executes the search and updates the result cards in the list."""
        self.results_list.clear()
        results = self.vault.search(query, limit=50)

        if query.strip():
            self.status_label.setText(f"{len(results)} match{'es' if len(results) != 1 else ''} for \"{query.strip()}\"")
        else:
            self.status_label.setText(f"Recent Captures ({len(results)})")

        for res in results:
            item = QListWidgetItem()
            card = SearchResultCard(res, parent=self.results_list)
            item.setSizeHint(QSize(self.results_list.width() - 20, 72))
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, card)

    def keyPressEvent(self, event):
        """Handles Escape to close and Enter to trigger selection."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
