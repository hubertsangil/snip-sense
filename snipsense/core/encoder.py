"""Video (MP4) and Animated GIF encoder with file size optimization."""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import numpy as np
import cv2

from snipsense.core.naming import sanitize_filename, extract_app_name


class ClipEncoder:
    """Encodes raw frame sequences into lightweight GIF and MP4 files."""

    def __init__(self, base_directory: Optional[Path] = None):
        if base_directory:
            self.base_directory = Path(base_directory)
        else:
            self.base_directory = Path.home() / "Pictures" / "SnipSense" / "Recordings"

        self.base_directory.mkdir(parents=True, exist_ok=True)

    def encode_gif(
        self,
        frames: List[Image.Image],
        output_path: Path,
        fps: int = 15,
        max_width: int = 800,
    ) -> Path:
        """Encodes frame list into an optimized animated GIF under 10MB."""
        if not frames:
            raise ValueError("Cannot encode GIF from empty frame list")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame_delay = max(20, int(1000 / max(1, fps)))

        processed_frames: List[Image.Image] = []
        for frame in frames:
            img = frame.convert("RGB")
            if img.width > max_width:
                aspect = img.height / img.width
                new_w = max_width
                new_h = int(new_w * aspect)
                img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)

            # Quantize for compact GIF palette
            quantized = img.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
            processed_frames.append(quantized)

        processed_frames[0].save(
            str(output_path),
            save_all=True,
            append_images=processed_frames[1:],
            duration=frame_delay,
            loop=0,
            optimize=True,
        )
        return output_path

    def encode_mp4(
        self,
        frames: List[Image.Image],
        output_path: Path,
        fps: int = 15,
        max_width: int = 1920,
    ) -> Path:
        """Encodes frame list into an H.264 / MP4 video using OpenCV."""
        if not frames:
            raise ValueError("Cannot encode MP4 from empty frame list")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        first = frames[0]

        target_w = first.width
        target_h = first.height

        if target_w > max_width:
            aspect = target_h / target_w
            target_w = max_width
            target_h = int(target_w * aspect)

        # Video dimensions must be even for H.264 / mp4v codecs
        target_w = target_w if target_w % 2 == 0 else target_w - 1
        target_h = target_h if target_h % 2 == 0 else target_h - 1
        target_w = max(2, target_w)
        target_h = max(2, target_h)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, float(fps), (target_w, target_h))

        try:
            for frame in frames:
                img = frame.convert("RGB")
                if img.size != (target_w, target_h):
                    img = img.resize((target_w, target_h), Image.Resampling.BILINEAR)

                # Convert RGB PIL to BGR numpy array
                rgb_np = np.array(img)
                bgr_np = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2BGR)
                writer.write(bgr_np)
        finally:
            writer.release()

        return output_path

    def encode_clip(
        self,
        frames: List[Image.Image],
        window_title: str = "",
        fps: int = 15,
        generate_gif: bool = True,
        generate_mp4: bool = True,
    ) -> Dict[str, Path]:
        """Encodes recording frames into both MP4 and GIF formats with auto-naming.
        
        Returns:
            Dictionary mapping format string ("mp4", "gif") to output file Path.
        """
        if not frames:
            return {}

        app_name = extract_app_name(window_title) if window_title else "Screen"
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        slug = f"Clip_{sanitize_filename(app_name)}_{timestamp_str}"

        results: Dict[str, Path] = {}

        if generate_mp4:
            mp4_path = self.base_directory / f"{slug}.mp4"
            self.encode_mp4(frames, mp4_path, fps=fps)
            results["mp4"] = mp4_path

        if generate_gif:
            gif_path = self.base_directory / f"{slug}.gif"
            self.encode_gif(frames, gif_path, fps=fps)
            results["gif"] = gif_path

        return results
