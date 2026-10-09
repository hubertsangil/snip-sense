"""Unit and UI tests for RecorderPill and RecordingCompletedDialog."""

from __future__ import annotations
from pathlib import Path
from PIL import Image
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent

from snipsense.core.recorder import RecordingResult
from snipsense.ui.recorder_pill import RecorderPill
from snipsense.ui.recording_dialog import RecordingCompletedDialog


def test_recorder_pill_ui_and_signals(qtbot):
    pill = RecorderPill(max_duration_seconds=30.0)
    qtbot.addWidget(pill)

    # Test initial state
    assert "00:00 / 30:00" in pill.timer_label.text()
    assert pill.stop_btn.isEnabled() is True
    assert pill.cancel_btn.isEnabled() is True

    # Test update time
    pill.update_time(14.5, 30.0)
    assert pill.timer_label.text() == "00:14 / 00:30"

    # Test pulse toggle
    pill._toggle_pulse()
    assert pill.rec_indicator.text() == "🔴 REC"

    # Test stop signal
    stop_signals = []
    pill.stop_requested.connect(lambda: stop_signals.append(True))
    qtbot.mouseClick(pill.stop_btn, Qt.MouseButton.LeftButton)
    assert len(stop_signals) == 1

    # Test cancel signal
    cancel_signals = []
    pill.cancel_requested.connect(lambda: cancel_signals.append(True))
    qtbot.mouseClick(pill.cancel_btn, Qt.MouseButton.LeftButton)
    assert len(cancel_signals) == 1


def test_recording_completed_dialog(qtbot, tmp_path):
    img = Image.new("RGB", (100, 100), color=(50, 100, 150))
    mp4_file = tmp_path / "clip.mp4"
    gif_file = tmp_path / "clip.gif"
    mp4_file.write_bytes(b"dummy mp4 content")
    gif_file.write_bytes(b"dummy gif content")

    result = RecordingResult(
        frames=[img],
        fps=15,
        duration_seconds=2.5,
        window_title="VSCode",
        width=100,
        height=100,
    )

    encoded_files = {"mp4": mp4_file, "gif": gif_file}
    dialog = RecordingCompletedDialog(encoded_files, result)
    qtbot.addWidget(dialog)

    assert dialog.copy_btn.isEnabled() is True
    assert dialog.folder_btn.isEnabled() is True

    # Test copy button click
    qtbot.mouseClick(dialog.copy_btn, Qt.MouseButton.LeftButton)
    assert dialog.copy_btn.text() == "Copied!"
