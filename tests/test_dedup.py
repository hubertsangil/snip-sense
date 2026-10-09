"""Unit tests for perceptual image hashing, Hamming distance, clustering, and safe archival."""

from __future__ import annotations
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from snipsense.core.dedup import (
    compute_dhash,
    compute_dhash_from_file,
    hamming_distance,
    ScreenshotCandidate,
    DuplicateCluster,
    cluster_duplicates,
    DuplicateArchiver,
)


def test_dhash_identical_images():
    img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img2 = Image.new("RGB", (100, 100), color=(255, 0, 0))

    hash1 = compute_dhash(img1)
    hash2 = compute_dhash(img2)

    assert hash1 == hash2
    assert hamming_distance(hash1, hash2) == 0


def test_dhash_near_duplicate_images():
    # Base image
    img1 = Image.new("RGB", (200, 200), color=(200, 200, 200))
    draw1 = ImageDraw.Draw(img1)
    draw1.rectangle([20, 20, 180, 180], fill=(50, 50, 50))

    # Slightly modified image (e.g. tiny 1px artifact)
    img2 = img1.copy()
    draw2 = ImageDraw.Draw(img2)
    draw2.point((21, 21), fill=(55, 55, 55))

    # Completely different image
    img3 = Image.new("RGB", (200, 200), color=(10, 10, 10))
    draw3 = ImageDraw.Draw(img3)
    draw3.ellipse([10, 10, 190, 190], fill=(250, 250, 250))

    hash1 = compute_dhash(img1)
    hash2 = compute_dhash(img2)
    hash3 = compute_dhash(img3)

    # Near duplicates have Hamming distance <= 4
    assert hamming_distance(hash1, hash2) <= 4
    # Distinct images have large Hamming distance
    assert hamming_distance(hash1, hash3) > 10


def test_cluster_duplicates_grouping():
    candidates = [
        ScreenshotCandidate(
            file_path="/path/to/img1.png",
            created_at=1000.0,
            perceptual_hash="ffff0000ffff0000",
            file_size_bytes=50000,
            title="Image 1",
        ),
        ScreenshotCandidate(
            file_path="/path/to/img2.png",
            created_at=1005.0,
            perceptual_hash="ffff0000ffff0001",  # 1 bit difference
            file_size_bytes=49000,
            title="Image 2",
        ),
        ScreenshotCandidate(
            file_path="/path/to/img3.png",
            created_at=2000.0,
            perceptual_hash="0000ffff0000ffff",  # completely different
            file_size_bytes=60000,
            title="Image 3",
        ),
    ]

    clusters = cluster_duplicates(candidates, max_hamming_distance=4)

    assert len(clusters) == 1
    assert clusters[0].primary.file_path == "/path/to/img1.png"
    assert len(clusters[0].duplicates) == 1
    assert clusters[0].duplicates[0].file_path == "/path/to/img2.png"
    assert clusters[0].total_reclaimable_bytes == 49000


def test_duplicate_archiver_and_undo(tmp_path):
    src_dir = tmp_path / "screenshots"
    src_dir.mkdir()
    archive_dir = tmp_path / "archive"

    file1 = src_dir / "shot1.png"
    file2 = src_dir / "shot2.png"

    img = Image.new("RGB", (50, 50), color=(100, 100, 100))
    img.save(file1)
    img.save(file2)

    archiver = DuplicateArchiver(archive_directory=archive_dir)

    # Archive file2
    count, batch_id = archiver.archive_files([file2])
    assert count == 1
    assert not file2.exists()
    assert file1.exists()

    # Undo archival
    restored = archiver.undo_archive(batch_id)
    assert restored == 1
    assert file2.exists()
