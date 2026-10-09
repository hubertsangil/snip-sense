"""Unit tests for ScreenRecorder and FrameCaptureWorker."""

from __future__ import annotations
import time
from PIL import Image
from PyQt6.QtCore import QThread

from snipsense.core.models import ScreenRegion
from snipsense.core.recorder import FrameCaptureWorker, ScreenRecorder, RecordingResult


def test_frame_capture_worker_basic(qtbot):
    thread = QThread()
    worker = FrameCaptureWorker(target_fps=20, max_duration_seconds=1.0, window_title="TestWindow")
    worker.moveToThread(thread)

    results = []
    ticks = []

    thread.started.connect(worker.run)
    worker.finished.connect(lambda res: results.append(res))
    worker.tick.connect(lambda el, mx: ticks.append((el, mx)))

    thread.start()

    qtbot.waitUntil(lambda: len(ticks) > 0, timeout=1500)
    worker.stop()
    qtbot.waitUntil(lambda: len(results) > 0, timeout=2500)

    thread.quit()
    thread.wait()

    assert len(results) == 1
    res = results[0]
    assert isinstance(res, RecordingResult)
    assert res.window_title == "TestWindow"
    assert len(res.frames) > 0
    assert len(ticks) > 0


def test_frame_capture_worker_cancel(qtbot):
    thread = QThread()
    worker = FrameCaptureWorker(target_fps=20, max_duration_seconds=2.0)
    worker.moveToThread(thread)

    cancelled_events = []
    thread.started.connect(worker.run)
    worker.cancelled.connect(lambda: cancelled_events.append(True))

    thread.start()
    qtbot.wait(100)
    worker.cancel()
    qtbot.waitUntil(lambda: len(cancelled_events) > 0, timeout=2500)

    thread.quit()
    thread.wait()

    assert len(cancelled_events) == 1
    assert len(worker._frames) == 0


def test_screen_recorder_lifecycle(qtbot):
    recorder = ScreenRecorder(target_fps=15, max_duration_seconds=0.5)

    finished_results = []
    ticks = []

    recorder.tick.connect(lambda el, mx: ticks.append((el, mx)))
    recorder.recording_finished.connect(lambda res: finished_results.append(res))

    recorder.start(window_title="ActiveApp")
    assert recorder.is_recording is True

    # Wait for auto-cap
    qtbot.waitUntil(lambda: len(finished_results) > 0, timeout=3000)

    assert recorder.is_recording is False
    assert len(finished_results) == 1
    assert finished_results[0].window_title == "ActiveApp"
