"""Review and Clean Duplicates dialog displaying side-by-side comparisons and safe batch archival."""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QCheckBox,
    QFrame,
    QMessageBox,
)
from PIL import Image

from snipsense.core.dedup import DuplicateCluster, DuplicateArchiver, hamming_distance
from snipsense.ui.styles import DARK_THEME_QSS


def format_bytes(bytes_count: int) -> str:
    """Formats raw byte counts into human-readable string (KB/MB)."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    else:
        return f"{bytes_count / (1024 * 1024):.1f} MB"


def format_time_ago(timestamp: float) -> str:
    """Formats Unix timestamp into relative human-readable string."""
    diff = max(0, time.time() - timestamp)
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        return f"{int(diff // 60)}m ago"
    elif diff < 86400:
        return f"{int(diff // 3600)}h ago"
    else:
        return f"{int(diff // 86400)}d ago"


class ClusterItemWidget(QFrame):
    """Widget displaying a single duplicate cluster with side-by-side thumbnail comparisons."""

    def __init__(self, cluster: DuplicateCluster, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cluster = cluster
        self.setObjectName("clusterCard")
        self.setStyleSheet("""
            QFrame#clusterCard {
                background-color: #1A202C;
                border: 1px solid #2D3748;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header with checkbox and reclaimable size
        header_layout = QHBoxLayout()
        self.checkbox = QCheckBox(f"Cluster: {cluster.primary.title or Path(cluster.primary.file_path).name}")
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("font-weight: 600; color: #F1F5F9;")
        header_layout.addWidget(self.checkbox)

        size_label = QLabel(f"Reclaimable: {format_bytes(cluster.total_reclaimable_bytes)}")
        size_label.setStyleSheet("color: #10B981; font-weight: 600; font-size: 12px;")
        header_layout.addWidget(size_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Side-by-side comparison horizontal row
        comparison_layout = QHBoxLayout()
        comparison_layout.setSpacing(12)

        # Primary Version Card
        primary_col = self._create_version_card(
            title="Primary (Keep)",
            file_path=cluster.primary.file_path,
            timestamp=cluster.primary.created_at,
            file_size=cluster.primary.file_size_bytes,
            is_primary=True,
        )
        comparison_layout.addWidget(primary_col)

        # Duplicate Versions Cards
        for dup in cluster.duplicates:
            dist = hamming_distance(cluster.primary.perceptual_hash, dup.perceptual_hash)
            similarity = max(0, int((1 - dist / 64) * 100))
            dup_col = self._create_version_card(
                title=f"Duplicate ({similarity}% match)",
                file_path=dup.file_path,
                timestamp=dup.created_at,
                file_size=dup.file_size_bytes,
                is_primary=False,
            )
            comparison_layout.addWidget(dup_col)

        comparison_layout.addStretch()
        layout.addLayout(comparison_layout)

    def _create_version_card(
        self,
        title: str,
        file_path: str,
        timestamp: float,
        file_size: int,
        is_primary: bool,
    ) -> QWidget:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {'#14181F' if is_primary else '#1F2937'};
                border: 1px solid {'#10B981' if is_primary else '#E11D48'};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(4)

        tag = QLabel(title)
        tag.setStyleSheet(f"color: {'#10B981' if is_primary else '#FB7185'}; font-weight: bold; font-size: 11px;")
        vbox.addWidget(tag)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(140, 90)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("background-color: #0B0D10; border-radius: 4px;")

        if os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(136, 86, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumb_label.setPixmap(scaled)
        vbox.addWidget(thumb_label)

        # Meta info
        meta = QLabel(f"{format_time_ago(timestamp)} • {format_bytes(file_size)}")
        meta.setStyleSheet("color: #94A3B8; font-size: 10px;")
        vbox.addWidget(meta)

        return card

    def is_selected(self) -> bool:
        return self.checkbox.isChecked()

    def get_duplicate_paths(self) -> List[str]:
        return [d.file_path for d in self.cluster.duplicates]


class DedupDialog(QDialog):
    """Review & Clean Duplicates modal window."""

    cleaning_completed = pyqtSignal(int, int)  # cleaned_files_count, bytes_reclaimed

    def __init__(
        self,
        clusters: List[DuplicateCluster],
        archiver: Optional[DuplicateArchiver] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.clusters = clusters
        self.archiver = archiver or DuplicateArchiver()
        self.item_widgets: List[ClusterItemWidget] = []
        self.last_batch_id: Optional[str] = None

        self.setWindowTitle("Review & Clean Screenshot Duplicates")
        self.setObjectName("previewWindow")
        self.setStyleSheet(DARK_THEME_QSS)
        self.resize(750, 520)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_label = QLabel("🧹 Duplicate Screenshot Cleaner")
        title_label.setObjectName("headerTitle")
        header.addWidget(title_label)

        total_bytes = sum(c.total_reclaimable_bytes for c in self.clusters)
        self.stats_badge = QLabel(f"{len(self.clusters)} Duplicate Clusters • Reclaimable: {format_bytes(total_bytes)}")
        self.stats_badge.setObjectName("statusBadge")
        header.addWidget(self.stats_badge)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        main_layout.addLayout(header)

        # Description
        desc = QLabel("Identified near-identical screenshot bursts (Hamming distance ≤ 4). Redundant files will be safely moved to the SnipSense Archive folder.")
        desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Scroll area for clusters
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(6, 6, 6, 6)

        if not self.clusters:
            empty_label = QLabel("✨ No duplicate screenshots found! Your vault is clean.")
            empty_label.setStyleSheet("color: #94A3B8; font-size: 13px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
        else:
            for cluster in self.clusters:
                item_widget = ClusterItemWidget(cluster)
                self.item_widgets.append(item_widget)
                self.scroll_layout.addWidget(item_widget)

        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.undo_btn = QPushButton("↩️ Undo Last Cleanup")
        self.undo_btn.setObjectName("ghostAction")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self._handle_undo)
        btn_layout.addWidget(self.undo_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Close")
        cancel_btn.setObjectName("ghostAction")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.clean_btn = QPushButton("🧹 Clean Selected Duplicates")
        self.clean_btn.setObjectName("primaryAction")
        self.clean_btn.setEnabled(len(self.clusters) > 0)
        self.clean_btn.clicked.connect(self._handle_clean)
        btn_layout.addWidget(self.clean_btn)

        main_layout.addLayout(btn_layout)

    def _handle_clean(self):
        """Archives all selected duplicate items."""
        to_archive: List[str] = []
        reclaimed_bytes = 0

        for widget in self.item_widgets:
            if widget.is_selected():
                paths = widget.get_duplicate_paths()
                to_archive.extend(paths)
                reclaimed_bytes += widget.cluster.total_reclaimable_bytes

        if not to_archive:
            QMessageBox.information(self, "Notice", "No duplicate items selected for cleanup.")
            return

        count, batch_id = self.archiver.archive_files(to_archive)
        self.last_batch_id = batch_id
        self.undo_btn.setEnabled(True)
        self.clean_btn.setEnabled(False)

        self.stats_badge.setText(f"Cleaned {count} duplicates ({format_bytes(reclaimed_bytes)} reclaimed)")
        self.stats_badge.setStyleSheet("background-color: rgba(16, 185, 129, 0.2); color: #10B981;")

        self.cleaning_completed.emit(count, reclaimed_bytes)

    def _handle_undo(self):
        """Reverts the last archival batch."""
        if not self.last_batch_id:
            return

        restored = self.archiver.undo_archive(self.last_batch_id)
        self.undo_btn.setEnabled(False)
        self.clean_btn.setEnabled(True)
        self.stats_badge.setText(f"Restored {restored} files from archive")
        self.stats_badge.setStyleSheet("background-color: rgba(59, 130, 246, 0.2); color: #60A5FA;")
