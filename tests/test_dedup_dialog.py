"""Unit and UI tests for DedupDialog and ClusterItemWidget components."""

from __future__ import annotations
from pathlib import Path
from PIL import Image

from PyQt6.QtCore import Qt

from snipsense.core.dedup import (
    ScreenshotCandidate,
    DuplicateCluster,
    DuplicateArchiver,
)
from snipsense.ui.dedup_dialog import DedupDialog, ClusterItemWidget


def test_dedup_dialog_ui_and_clean_action(qtbot, tmp_path):
    src_dir = tmp_path / "screens"
    src_dir.mkdir()
    archive_dir = tmp_path / "archive"

    file1 = src_dir / "orig.png"
    file2 = src_dir / "dup.png"

    img = Image.new("RGB", (60, 60), color=(80, 80, 80))
    img.save(file1)
    img.save(file2)

    primary = ScreenshotCandidate(
        file_path=str(file1),
        created_at=100.0,
        perceptual_hash="1111222233334444",
        file_size_bytes=1024,
        title="Original",
    )
    dup = ScreenshotCandidate(
        file_path=str(file2),
        created_at=105.0,
        perceptual_hash="1111222233334444",
        file_size_bytes=1024,
        title="Duplicate",
    )

    cluster = DuplicateCluster(
        cluster_id="cluster_1",
        primary=primary,
        duplicates=[dup],
    )

    archiver = DuplicateArchiver(archive_directory=archive_dir)
    dialog = DedupDialog(clusters=[cluster], archiver=archiver)
    qtbot.addWidget(dialog)

    assert len(dialog.item_widgets) == 1
    assert dialog.clean_btn.isEnabled() is True
    assert dialog.undo_btn.isEnabled() is False

    cleaned_events = []
    dialog.cleaning_completed.connect(lambda count, bytes_reclaimed: cleaned_events.append((count, bytes_reclaimed)))

    # Click clean button
    qtbot.mouseClick(dialog.clean_btn, Qt.MouseButton.LeftButton)

    assert not file2.exists()
    assert file1.exists()
    assert dialog.undo_btn.isEnabled() is True
    assert len(cleaned_events) == 1

    # Click undo
    dialog._handle_undo()
    assert file2.exists()
    assert dialog.undo_btn.isEnabled() is False
