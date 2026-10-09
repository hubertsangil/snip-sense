"""Unit tests for ScreenRegion data models and ScreenGrabber engine."""

from __future__ import annotations
import pytest
from PIL import Image
from snipsense.core.models import ScreenRegion, CaptureResult
from snipsense.core.capture import ScreenGrabber


def test_screen_region_valid():
    region = ScreenRegion(x=10, y=20, width=300, height=200)
    assert region.x == 10
    assert region.y == 20
    assert region.width == 300
    assert region.height == 200
    assert region.as_dict() == {"left": 10, "top": 20, "width": 300, "height": 200}


def test_screen_region_rejects_non_positive_dimensions():
    with pytest.raises(ValueError, match="Region dimensions must be positive"):
        ScreenRegion(x=0, y=0, width=0, height=100)

    with pytest.raises(ValueError, match="Region dimensions must be positive"):
        ScreenRegion(x=0, y=0, width=100, height=-5)


def test_screen_region_from_points_normalized():
    # Dragging top-left to bottom-right
    r1 = ScreenRegion.from_points(10, 20, 110, 120)
    assert (r1.x, r1.y, r1.width, r1.height) == (10, 20, 100, 100)

    # Dragging bottom-right to top-left (reversed)
    r2 = ScreenRegion.from_points(110, 120, 10, 20)
    assert (r2.x, r2.y, r2.width, r2.height) == (10, 20, 100, 100)


def test_screen_grabber_virtual_geometry():
    with ScreenGrabber() as grabber:
        left, top, width, height = grabber.get_virtual_geometry()
        assert width > 0
        assert height > 0


def test_screen_grabber_capture_region():
    with ScreenGrabber() as grabber:
        left, top, _, _ = grabber.get_virtual_geometry()
        # Grab a safe 50x50 patch within bounds
        region = ScreenRegion(x=left + 10, y=top + 10, width=50, height=50)
        result = grabber.capture_region(region, window_title="TestWindow")

        assert isinstance(result, CaptureResult)
        assert isinstance(result.image, Image.Image)
        assert result.width == 50
        assert result.height == 50
        assert result.image.mode == "RGB"
        assert result.window_title == "TestWindow"


def test_screen_grabber_full_screen():
    with ScreenGrabber() as grabber:
        result = grabber.capture_full_screen()
        _, _, w, h = grabber.get_virtual_geometry()
        assert result.width == w
        assert result.height == h
