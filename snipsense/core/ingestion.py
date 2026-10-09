"""Historical screenshot directory scanner, batch ingestion, and background worker."""

from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Set, Tuple
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PIL import Image

from snipsense.core.vault import VaultDatabase
from snipsense.core.dedup import (
    compute_dhash_from_file,
    ScreenshotCandidate,
    DuplicateCluster,
    cluster_duplicates,
)


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def get_default_screenshot_directories() -> List[Path]:
    """Detects standard screenshot folders on the operating system."""
    home = Path.home()
    dirs: List[Path] = []

    # Common cross-platform paths
    snipsense_dir = home / "Pictures" / "SnipSense"
    if snipsense_dir.exists():
        dirs.append(snipsense_dir)

    screenshots_dir = home / "Pictures" / "Screenshots"
    if screenshots_dir.exists():
        dirs.append(screenshots_dir)

    pictures_dir = home / "Pictures"
    if pictures_dir.exists() and pictures_dir not in dirs:
        dirs.append(pictures_dir)

    # macOS default screen capture location is Desktop (scan for Screen Shot / Screenshot files)
    if sys.platform == "darwin":
        desktop_dir = home / "Desktop"
        if desktop_dir.exists() and desktop_dir not in dirs:
            dirs.append(desktop_dir)

    return dirs


class HistoricalScanner:
    """Discovers and parses past screenshots from system directories."""

    def __init__(self, vault: Optional[VaultDatabase] = None, scan_dirs: Optional[List[Path]] = None):
        self.vault = vault or VaultDatabase.get_instance()
        self.scan_dirs = scan_dirs or get_default_screenshot_directories()

    def discover_images(self, recursive: bool = False) -> List[Path]:
        """Discovers all supported image files in scanned directories."""
        discovered: List[Path] = []
        seen: Set[str] = set()

        for directory in self.scan_dirs:
            if not directory.exists():
                continue

            try:
                iterator = directory.rglob("*") if recursive else directory.glob("*")
                for path in iterator:
                    if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        # Avoid scanning archive directories
                        if "archive" in path.parts or ".trash" in path.parts:
                            continue
                        resolved = str(path.resolve())
                        if resolved not in seen:
                            seen.add(resolved)
                            discovered.append(path)
            except Exception:
                continue

        return discovered

    def ingest_images(
        self,
        image_paths: List[Path],
        progress_callback: Optional[callable] = None,
    ) -> Tuple[int, List[DuplicateCluster]]:
        """Ingests images into SQLite database and returns duplicate clusters.
        
        Returns:
            Tuple of (indexed_count, list of DuplicateClusters).
        """
        candidates: List[ScreenshotCandidate] = []
        indexed_count = 0

        total = len(image_paths)
        for i, path in enumerate(image_paths):
            try:
                resolved_path = str(path.resolve())
                stat = path.stat()
                file_size = stat.st_size
                mtime = stat.st_mtime

                # Compute perceptual hash
                p_hash = compute_dhash_from_file(path)

                title = path.stem.replace("_", " ").replace("-", " ")
                
                # Check dimensions
                width, height = 0, 0
                try:
                    with Image.open(path) as img:
                        width, height = img.size
                except Exception:
                    pass

                # Index into SQLite vault
                self.vault.index_capture(
                    file_path=resolved_path,
                    title=title,
                    perceptual_hash=p_hash,
                    created_at=mtime,
                )
                indexed_count += 1

                candidate = ScreenshotCandidate(
                    file_path=resolved_path,
                    created_at=mtime,
                    perceptual_hash=p_hash,
                    file_size_bytes=file_size,
                    width=width,
                    height=height,
                    title=title,
                )
                candidates.append(candidate)

            except Exception:
                continue

            if progress_callback:
                progress_callback(i + 1, total)

        # Detect duplicate clusters
        clusters = cluster_duplicates(candidates)
        return indexed_count, clusters


class IngestionWorker(QObject):
    """Background worker for non-blocking historical screenshot scanning and indexing."""

    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(int, int)  # indexed_count, duplicate_cluster_count

    def __init__(self, scanner: Optional[HistoricalScanner] = None):
        super().__init__()
        self.scanner = scanner or HistoricalScanner()
        self.clusters: List[DuplicateCluster] = []

    def run(self):
        """Executes discovery, hashing, indexing, and duplicate detection."""
        image_paths = self.scanner.discover_images()
        if not image_paths:
            self.clusters = []
            self.finished.emit(0, 0)
            return

        def on_prog(curr, tot):
            self.progress.emit(curr, tot)

        indexed_count, clusters = self.scanner.ingest_images(image_paths, progress_callback=on_prog)
        self.clusters = clusters
        self.finished.emit(indexed_count, len(clusters))

