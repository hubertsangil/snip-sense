"""Unit tests for the VaultDatabase SQLite FTS5 search index."""

import time
import pytest
from pathlib import Path
from PIL import Image
from snipsense.core.vault import VaultDatabase, VaultRecord, SearchResult


@pytest.fixture
def temp_vault(tmp_path: Path) -> VaultDatabase:
    """Provides an isolated in-memory or temporary file-based VaultDatabase."""
    db_path = tmp_path / "test_vault.db"
    vault = VaultDatabase(db_path=db_path)
    return vault


def test_vault_initializes_schema(temp_vault: VaultDatabase):
    """Verifies tables and FTS5 indexes are properly initialized."""
    with temp_vault.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "captures" in tables
        assert "fts_captures" in tables


def test_vault_insert_and_retrieve(temp_vault: VaultDatabase):
    """Verifies adding a capture stores fields and returns a valid ID."""
    record_id = temp_vault.index_capture(
        file_path="/tmp/screens/VSCode_Docker_Exit137.png",
        title="VSCode Docker Crash",
        ocr_text="fatal error: container killed with exit code 137 OOMKilled",
        tags="docker,vscode,error",
        window_title="Visual Studio Code - server.py",
        created_at=time.time(),
    )
    assert record_id > 0

    record = temp_vault.get_capture(record_id)
    assert record is not None
    assert record.title == "VSCode Docker Crash"
    assert "exit code 137" in record.ocr_text
    assert record.tags == "docker,vscode,error"


def test_vault_fts_exact_and_prefix_search(temp_vault: VaultDatabase):
    """Verifies FTS5 lexical full-text search with exact words and prefix wildcards."""
    temp_vault.index_capture(
        file_path="/tmp/screens/receipt_amazon.png",
        title="Amazon Order Receipt",
        ocr_text="Order # 114-9283719-281920 Total: $48.99 Shipped with FedEx",
        tags="amazon,receipt",
    )
    temp_vault.index_capture(
        file_path="/tmp/screens/wifi_creds.png",
        title="Guest Wifi Password",
        ocr_text="SSID: OfficeGuest Password: SuperSecretKey2026",
        tags="wifi,credentials",
    )

    # Search for exact token in OCR text
    results_receipt = temp_vault.search("FedEx")
    assert len(results_receipt) == 1
    assert results_receipt[0].title == "Amazon Order Receipt"
    assert "FedEx" in results_receipt[0].snippet

    # Search for prefix token (e.g. 'Offi*' or 'Office')
    results_wifi = temp_vault.search("Office")
    assert len(results_wifi) == 1
    assert results_wifi[0].title == "Guest Wifi Password"

    # Search for title keyword
    results_title = temp_vault.search("Amazon")
    assert len(results_title) == 1
    assert Path(results_title[0].file_path) == Path("/tmp/screens/receipt_amazon.png").resolve()


def test_vault_search_special_characters_graceful(temp_vault: VaultDatabase):
    """Verifies search handles quotes, asterisks, punctuation without SQLite syntax errors."""
    temp_vault.index_capture(
        file_path="/tmp/screens/code.png",
        title="Python Error",
        ocr_text="SyntaxError: unexpected EOF while parsing () : []",
    )

    # Query with punctuation and unbalanced quotes
    results = temp_vault.search('SyntaxError: ("EOF"')
    assert len(results) >= 0  # Does not raise sqlite3.OperationalError


def test_vault_search_empty_query_returns_recent(temp_vault: VaultDatabase):
    """Empty query should return recent captures ordered by created_at DESC."""
    temp_vault.index_capture(
        file_path="/tmp/screens/1.png",
        title="First",
        ocr_text="First screenshot",
        created_at=100.0,
    )
    temp_vault.index_capture(
        file_path="/tmp/screens/2.png",
        title="Second",
        ocr_text="Second screenshot",
        created_at=200.0,
    )

    results = temp_vault.search("")
    assert len(results) == 2
    assert results[0].title == "Second"
    assert results[1].title == "First"


def test_vault_upsert_on_same_path(temp_vault: VaultDatabase):
    """Verifies that re-indexing the same file path updates the existing entry."""
    path = "/tmp/screens/same_file.png"
    id1 = temp_vault.index_capture(file_path=path, title="Old Title", ocr_text="Old Text")
    id2 = temp_vault.index_capture(file_path=path, title="New Title", ocr_text="New Text")

    assert id1 == id2
    record = temp_vault.get_capture(id1)
    assert record.title == "New Title"
    assert record.ocr_text == "New Text"

    # FTS search should now match new text and not match old text
    assert len(temp_vault.search("New")) == 1
    assert len(temp_vault.search("Old")) == 0
