"""File storage management and operating system explorer integration."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image
from snipsense.core.naming import sanitize_filename


class StorageManager:
    """Manages disk saving, collision handling, and native file manager interaction."""

    def __init__(self, base_directory: Optional[Path] = None):
        if base_directory:
            self.base_directory = Path(base_directory)
        else:
            # Default to Pictures/SnipSense under user home directory
            self.base_directory = Path.home() / "Pictures" / "SnipSense"

        self.ensure_directory()

    def ensure_directory(self) -> Path:
        """Ensures the target save directory exists on disk."""
        self.base_directory.mkdir(parents=True, exist_ok=True)
        return self.base_directory

    def save_image(self, image: Image.Image, filename: str, directory: Optional[Path] = None) -> Path:
        """Saves a PIL image as a lossless PNG to disk with collision avoidance.
        
        Args:
            image: PIL Image instance.
            filename: Target filename (e.g., 'VSCode_Error.png').
            directory: Optional override directory. Defaults to base_directory.

        Returns:
            The Path of the newly saved file.
        """
        save_dir = Path(directory) if directory else self.ensure_directory()
        save_dir.mkdir(parents=True, exist_ok=True)

        # Ensure .png extension and sanitize
        raw_name = filename[:-4] if filename.lower().endswith(".png") else filename
        clean_name = sanitize_filename(raw_name)
        if not clean_name:
            clean_name = "Snip"

        target_file = save_dir / f"{clean_name}.png"

        # Handle filename collisions with incremental suffixes
        counter = 1
        while target_file.exists():
            target_file = save_dir / f"{clean_name}_{counter}.png"
            counter += 1

        # Save image as PNG
        image.save(target_file, format="PNG", optimize=True)
        return target_file

    @staticmethod
    def open_in_explorer(path: Path):
        """Opens the system file manager and selects the target file/folder."""
        target = Path(path).resolve()
        if not target.exists():
            return

        if sys.platform == "win32":
            if target.is_file():
                # Select the specific file in Windows Explorer
                subprocess.Popen(["explorer", f"/select,{str(target)}"])
            else:
                os.startfile(str(target))
        elif sys.platform == "darwin":
            if target.is_file():
                subprocess.Popen(["open", "-R", str(target)])
            else:
                subprocess.Popen(["open", str(target)])
        else:
            # Linux / X11
            parent_dir = target.parent if target.is_file() else target
            subprocess.Popen(["xdg-open", str(parent_dir)])
