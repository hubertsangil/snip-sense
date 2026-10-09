"""Background screen frame capture engine for short GIF/MP4 clips."""

from __future__ import annotations
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import mss
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

from snipsense.core.models import ScreenRegion
from snipsense.core.naming import get_foreground_window_title


@dataclass
class RecordedFrame:
    """Represents a single captured video frame."""
    image: Image.Image
    timestamp: float


@dataclass
class RecordingResult:
    """Represents the output of a completed screen recording session."""
    frames: List[Image.Image]
    fps: int
    duration_seconds: float
    window_title: str
    width: int
    height: int


class FrameCaptureWorker(QObject):
    """Background worker thread capturing screen frames at a fixed frame rate."""

    frame_captured = pyqtSignal(object)  # Image.Image
    tick = pyqtSignal(float, float)  # elapsed_seconds, max_seconds
    finished = pyqtSignal(object)  # RecordingResult
    cancelled = pyqtSignal()

    def __init__(
        self,
        region: Optional[ScreenRegion] = None,
        target_fps: int = 15,
        max_duration_seconds: float = 30.0,
        window_title: str = "",
    ):
        super().__init__()
        self.region = region
        self.target_fps = max(1, min(30, target_fps))
        self.max_duration = max_duration_seconds
        self.window_title = window_title
        self._is_running = False
        self._is_cancelled = False
        self._frames: List[Image.Image] = []
        self._start_time: float = 0.0

    def stop(self):
        """Signals the capture loop to stop and finalize."""
        self._is_running = False

    def cancel(self):
        """Signals the capture loop to abort and discard."""
        self._is_cancelled = True
        self._is_running = False

    def run(self):
        """Executes the high-speed frame capture loop."""
        self._is_running = True
        self._is_cancelled = False
        self._frames.clear()
        self._start_time = time.time()
        frame_interval = 1.0 / self.target_fps

        try:
            if hasattr(mss, "MSS"):
                sct = mss.MSS()
            else:
                sct = mss.mss()
        except Exception:
            sct = None

        while self._is_running:
            loop_start = time.time()
            elapsed = loop_start - self._start_time

            # Check 30s hard cap
            if elapsed >= self.max_duration:
                break

            # Capture frame
            img = None
            try:
                if sct is not None:
                    if self.region:
                        monitor = {
                            "left": self.region.x,
                            "top": self.region.y,
                            "width": self.region.width,
                            "height": self.region.height,
                        }
                    else:
                        monitor = sct.monitors[0]  # All monitors combined

                    sct_img = sct.grab(monitor)
                    # Convert BGRA to RGB PIL Image
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            except Exception:
                img = None

            # Robust fallback for locked session or headless test environment
            if img is None:
                w = self.region.width if self.region else 640
                h = self.region.height if self.region else 480
                img = Image.new("RGB", (w, h), color=(30, 35, 45))

            self._frames.append(img)
            self.frame_captured.emit(img)

            self.tick.emit(elapsed, self.max_duration)

            # Precise frame pacing
            compute_time = time.time() - loop_start
            sleep_duration = frame_interval - compute_time
            if sleep_duration > 0:
                time.sleep(sleep_duration)

        if sct is not None:
            try:
                sct.close()
            except Exception:
                pass

        if self._is_cancelled:
            self._frames.clear()
            self.cancelled.emit()
            return

        final_duration = max(0.01, time.time() - self._start_time)
        actual_fps = max(1, int(round(len(self._frames) / final_duration))) if self._frames else self.target_fps
        width, height = self._frames[0].size if self._frames else (0, 0)

        result = RecordingResult(
            frames=self._frames,
            fps=actual_fps,
            duration_seconds=final_duration,
            window_title=self.window_title,
            width=width,
            height=height,
        )
        self.finished.emit(result)


class ScreenRecorder(QObject):
    """Manages recording lifecycle, threading, and events."""

    tick = pyqtSignal(float, float)  # elapsed, max
    recording_finished = pyqtSignal(object)  # RecordingResult
    recording_cancelled = pyqtSignal()

    def __init__(
        self,
        target_fps: int = 15,
        max_duration_seconds: float = 30.0,
    ):
        super().__init__()
        self.target_fps = target_fps
        self.max_duration_seconds = max_duration_seconds
        self._thread: Optional[QThread] = None
        self._worker: Optional[FrameCaptureWorker] = None
        self._is_recording = False

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self, region: Optional[ScreenRegion] = None, window_title: Optional[str] = None):
        """Starts recording frames in a background thread."""
        if self._is_recording:
            return

        active_title = window_title if window_title is not None else get_foreground_window_title()

        self._thread = QThread()
        self._worker = FrameCaptureWorker(
            region=region,
            target_fps=self.target_fps,
            max_duration_seconds=self.max_duration_seconds,
            window_title=active_title,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.tick.connect(self.tick.emit)
        self._worker.finished.connect(self._on_finished)
        self._worker.cancelled.connect(self._on_cancelled)

        self._is_recording = True
        self._thread.start()

    def stop(self):
        """Stops active recording and triggers encoding."""
        if self._worker and self._is_recording:
            self._worker.stop()

    def cancel(self):
        """Aborts active recording and discards frames."""
        if self._worker and self._is_recording:
            self._worker.cancel()

    def _on_finished(self, result: RecordingResult):
        self._is_recording = False
        if self._thread:
            self._thread.quit()
            self._thread.wait()
        self.recording_finished.emit(result)

    def _on_cancelled(self):
        self._is_recording = False
        if self._thread:
            self._thread.quit()
            self._thread.wait()
        self.recording_cancelled.emit()
