"""Unit tests for GIF and MP4 ClipEncoder."""

from __future__ import annotations
import os
from pathlib import Path
from PIL import Image, ImageDraw

from snipsense.core.encoder import ClipEncoder


def _create_sample_frames(count: int = 5, size: tuple[int, int] = (120, 80)) -> list[Image.Image]:
    frames = []
    for i in range(count):
        img = Image.new("RGB", size, color=(i * 40, 100, 150))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"Frame {i}", fill=(255, 255, 255))
        frames.append(img)
    return frames


def test_encode_gif(tmp_path):
    encoder = ClipEncoder(base_directory=tmp_path)
    frames = _create_sample_frames(5)
    gif_path = tmp_path / "test.gif"

    output = encoder.encode_gif(frames, gif_path, fps=10)
    assert output.exists()
    assert output.stat().st_size > 0

    # Verify GIF properties
    with Image.open(output) as img:
        assert getattr(img, "is_animated", False)
        assert img.n_frames == 5


def test_encode_mp4(tmp_path):
    encoder = ClipEncoder(base_directory=tmp_path)
    frames = _create_sample_frames(6)
    mp4_path = tmp_path / "test.mp4"

    output = encoder.encode_mp4(frames, mp4_path, fps=15)
    assert output.exists()
    assert output.stat().st_size > 0


def test_encode_clip_dual_outputs(tmp_path):
    encoder = ClipEncoder(base_directory=tmp_path)
    frames = _create_sample_frames(4)

    results = encoder.encode_clip(
        frames=frames,
        window_title="Google Chrome - Dashboard",
        fps=12,
        generate_gif=True,
        generate_mp4=True,
    )

    assert "mp4" in results
    assert "gif" in results
    assert results["mp4"].exists()
    assert results["gif"].exists()
    assert "Chrome" in results["mp4"].name
    assert "Chrome" in results["gif"].name
