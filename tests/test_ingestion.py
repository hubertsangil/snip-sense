"""Unit tests for historical scanner and background ingestion worker."""

from __future__ import annotations
import time
from pathlib import Path
from PIL import Image

from snipsense.core.vault import VaultDatabase
from snipsense.core.ingestion import HistoricalScanner, IngestionWorker


def test_historical_scanner_discovers_and_ingests(tmp_path):
    shots_dir = tmp_path / "Screenshots"
    shots_dir.mkdir()
    db_path = tmp_path / "vault.db"
    vault = VaultDatabase(db_path=db_path)

    # Create 3 images: img1 & img2 near-identical, img3 distinct
    img1_path = shots_dir / "error_popup_1.png"
    img2_path = shots_dir / "error_popup_2.png"
    img3_path = shots_dir / "sunset.png"

    img_base = Image.new("RGB", (100, 100), color=(200, 100, 50))
    img_base.save(img1_path)
    img_base.save(img2_path)

    img_diff = Image.new("RGB", (100, 100), color=(10, 200, 255))
    img_diff.save(img3_path)

    scanner = HistoricalScanner(vault=vault, scan_dirs=[shots_dir])
    discovered = scanner.discover_images()
    assert len(discovered) == 3

    progress_ticks = []
    def on_prog(curr, tot):
        progress_ticks.append((curr, tot))

    indexed_count, clusters = scanner.ingest_images(discovered, progress_callback=on_prog)
    assert indexed_count == 3
    assert len(clusters) == 1
    assert len(progress_ticks) == 3

    # Check database records
    records = vault.search("")
    assert len(records) == 3


def test_ingestion_worker_signals(qtbot, tmp_path):
    shots_dir = tmp_path / "Screenshots"
    shots_dir.mkdir()
    db_path = tmp_path / "vault.db"
    vault = VaultDatabase(db_path=db_path)

    img_path = shots_dir / "test_shot.png"
    Image.new("RGB", (80, 80), color=(128, 128, 128)).save(img_path)

    scanner = HistoricalScanner(vault=vault, scan_dirs=[shots_dir])
    worker = IngestionWorker(scanner=scanner)

    finished_results = []
    clusters_results = []

    worker.finished.connect(lambda idx, dups: finished_results.append((idx, dups)))
    worker.clusters_ready.connect(lambda cl: clusters_results.append(cl))

    worker.run()

    assert len(finished_results) == 1
    assert finished_results[0][0] == 1  # 1 indexed
    assert len(clusters_results) == 1
