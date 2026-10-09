"""Core capture, OCR, privacy, naming, and storage engines for SnipSense."""

from snipsense.core.models import ScreenRegion, OCRTextBox, CaptureResult
from snipsense.core.capture import ScreenGrabber
from snipsense.core.ocr_engine import OCREngine
from snipsense.core.naming import generate_filename, sanitize_filename
from snipsense.core.storage import StorageManager
from snipsense.core.vault import VaultDatabase, VaultRecord, SearchResult
from snipsense.core.dedup import (
    compute_dhash,
    compute_dhash_from_file,
    hamming_distance,
    ScreenshotCandidate,
    DuplicateCluster,
    cluster_duplicates,
    DuplicateArchiver,
)
from snipsense.core.ingestion import HistoricalScanner, IngestionWorker

__all__ = [
    "ScreenRegion",
    "OCRTextBox",
    "CaptureResult",
    "ScreenGrabber",
    "OCREngine",
    "generate_filename",
    "sanitize_filename",
    "StorageManager",
    "VaultDatabase",
    "VaultRecord",
    "SearchResult",
    "compute_dhash",
    "compute_dhash_from_file",
    "hamming_distance",
    "ScreenshotCandidate",
    "DuplicateCluster",
    "cluster_duplicates",
    "DuplicateArchiver",
    "HistoricalScanner",
    "IngestionWorker",
]

