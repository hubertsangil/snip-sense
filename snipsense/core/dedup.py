"""Perceptual image hashing, Hamming distance, duplicate clustering, and safe archiving."""

from __future__ import annotations
import os
import shutil
import time
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image


def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
    """Computes a 64-bit difference hash (dHash) for a PIL Image.
    
    Args:
        image: PIL Image instance.
        hash_size: Grid width (default 8 yields 8x8 comparison = 64-bit hash).
        
    Returns:
        16-character hexadecimal hash string.
    """
    try:
        # 1. Resize to (hash_size + 1, hash_size) in grayscale
        resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = list(resized.getdata())
        width = hash_size + 1

        # 2. Compare adjacent horizontal pixels
        difference = []
        for row in range(hash_size):
            for col in range(hash_size):
                pixel_left = pixels[row * width + col]
                pixel_right = pixels[row * width + col + 1]
                difference.append(pixel_left > pixel_right)

        # 3. Convert boolean array into 64-bit integer then hex string
        decimal_val = 0
        for bit in difference:
            decimal_val = (decimal_val << 1) | int(bit)

        return f"{decimal_val:0{hash_size * hash_size // 4}x}"
    except Exception:
        return "0" * (hash_size * hash_size // 4)


def compute_dhash_from_file(file_path: str | Path) -> str:
    """Opens an image file and computes its perceptual dHash."""
    try:
        with Image.open(file_path) as img:
            return compute_dhash(img)
    except Exception:
        return "0" * 16


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculates bitwise Hamming distance between two hexadecimal hashes.
    
    Returns:
        Number of differing bits (0 = exact match).
    """
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 64
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        xor_val = val1 ^ val2
        return bin(xor_val).count("1")
    except ValueError:
        return 64


@dataclass
class ScreenshotCandidate:
    """Metadata for an image candidate evaluated for deduplication."""
    file_path: str
    created_at: float
    perceptual_hash: str
    file_size_bytes: int = 0
    width: int = 0
    height: int = 0
    title: str = ""
    ocr_text: str = ""


@dataclass
class DuplicateCluster:
    """Represents a set of near-duplicate screenshots (Hamming distance <= 4)."""
    cluster_id: str
    primary: ScreenshotCandidate
    duplicates: List[ScreenshotCandidate] = field(default_factory=list)

    @property
    def total_reclaimable_bytes(self) -> int:
        return sum(d.file_size_bytes for d in self.duplicates)


def cluster_duplicates(
    candidates: List[ScreenshotCandidate],
    max_hamming_distance: int = 10
) -> List[DuplicateCluster]:
    """Groups screenshots into duplicate clusters based on perceptual hash similarity.
    
    Images with Hamming distance <= max_hamming_distance are grouped together.
    The primary version is chosen as the earliest capture (or largest file size).
    
    Note: A threshold of 10 captures real-world near-duplicates like rapid bursts,
    same-page screenshots with slight scrolling, or timing differences. Lower values
    (e.g. 4) only catch pixel-identical copies.
    """
    if not candidates:
        return []

    # Sort candidates chronologically (earliest first)
    sorted_candidates = sorted(candidates, key=lambda c: (c.created_at, -c.file_size_bytes))
    clusters: List[DuplicateCluster] = []
    assigned: set[str] = set()

    for i, candidate in enumerate(sorted_candidates):
        if candidate.file_path in assigned or not candidate.perceptual_hash:
            continue

        matching_dups: List[ScreenshotCandidate] = []

        for j in range(i + 1, len(sorted_candidates)):
            other = sorted_candidates[j]
            if other.file_path in assigned or not other.perceptual_hash:
                continue

            dist = hamming_distance(candidate.perceptual_hash, other.perceptual_hash)
            if dist <= max_hamming_distance:
                matching_dups.append(other)
                assigned.add(other.file_path)

        if matching_dups:
            assigned.add(candidate.file_path)
            clusters.append(DuplicateCluster(
                cluster_id=f"cluster_{len(clusters) + 1}",
                primary=candidate,
                duplicates=matching_dups,
            ))

    return clusters


class DuplicateArchiver:
    """Safely archives duplicate screenshots to a designated folder with undo support."""

    def __init__(self, archive_directory: Optional[Path] = None):
        if archive_directory:
            self.archive_dir = Path(archive_directory)
        else:
            self.archive_dir = Path.home() / "Pictures" / "SnipSense" / "Archive"

        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.archive_dir / "archive_manifest.json"

    def _load_manifest(self) -> Dict[str, Dict]:
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_manifest(self, data: Dict[str, Dict]):
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def archive_files(self, file_paths: List[str | Path]) -> Tuple[int, str]:
        """Moves duplicate files to the archive directory and records manifest.
        
        Returns:
            Tuple of (number of files archived, batch_id string).
        """
        batch_id = f"batch_{int(time.time() * 1000)}"
        manifest = self._load_manifest()
        batch_records = []
        count = 0

        batch_folder = self.archive_dir / batch_id
        batch_folder.mkdir(parents=True, exist_ok=True)

        for item in file_paths:
            src = Path(item).resolve()
            if not src.exists():
                continue

            dest = batch_folder / src.name
            # Handle potential name collisions inside batch folder
            counter = 1
            while dest.exists():
                dest = batch_folder / f"{src.stem}_{counter}{src.suffix}"
                counter += 1

            try:
                shutil.move(str(src), str(dest))
                batch_records.append({
                    "original_path": str(src),
                    "archived_path": str(dest),
                })
                count += 1
            except Exception:
                continue

        if batch_records:
            manifest[batch_id] = {
                "timestamp": time.time(),
                "records": batch_records,
            }
            self._save_manifest(manifest)

        return count, batch_id

    def undo_archive(self, batch_id: Optional[str] = None) -> int:
        """Restores archived files back to their original locations.
        
        If batch_id is None, undos the latest batch.
        
        Returns:
            Number of files restored.
        """
        manifest = self._load_manifest()
        if not manifest:
            return 0

        target_batch = batch_id
        if not target_batch:
            # Pick latest timestamp batch
            sorted_batches = sorted(
                manifest.items(),
                key=lambda x: x[1].get("timestamp", 0),
                reverse=True
            )
            if not sorted_batches:
                return 0
            target_batch = sorted_batches[0][0]

        if target_batch not in manifest:
            return 0

        batch_info = manifest[target_batch]
        restored_count = 0

        for record in batch_info.get("records", []):
            orig = Path(record["original_path"])
            arch = Path(record["archived_path"])

            if arch.exists():
                orig.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(arch), str(orig))
                    restored_count += 1
                except Exception:
                    pass

        # Cleanup empty batch folder
        batch_folder = self.archive_dir / target_batch
        if batch_folder.exists() and not any(batch_folder.iterdir()):
            try:
                batch_folder.rmdir()
            except Exception:
                pass

        del manifest[target_batch]
        self._save_manifest(manifest)
        return restored_count
