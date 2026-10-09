"""Unit and UI integration tests for SearchModal visual memory search."""

import time
from pathlib import Path
import pytest
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from snipsense.core.vault import VaultDatabase
from snipsense.ui.search_modal import SearchModal, format_relative_time


@pytest.fixture
def populated_vault(tmp_path: Path) -> VaultDatabase:
    """Creates a temporary VaultDatabase populated with test screenshot records."""
    db_file = tmp_path / "test_search_vault.db"
    vault = VaultDatabase(db_path=db_file)

    # Create dummy images on disk for thumbnail loading
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    img1 = img_dir / "Docker_OOM_Crash.png"
    Image.new("RGB", (100, 100), color=(255, 0, 0)).save(img1)
    vault.index_capture(
        file_path=img1,
        title="Docker OOM Crash",
        ocr_text="fatal error: container killed with exit code 137 OOMKilled",
        tags="docker,crash",
        created_at=time.time() - 120,  # 2m ago
    )

    img2 = img_dir / "Amazon_Order_Receipt.png"
    Image.new("RGB", (100, 100), color=(0, 255, 0)).save(img2)
    vault.index_capture(
        file_path=img2,
        title="Amazon Order Receipt",
        ocr_text="Order # 114-9283719-281920 Total: $48.99 Shipped with FedEx",
        tags="amazon,receipt",
        created_at=time.time() - 7200,  # 2h ago
    )

    return vault


def test_format_relative_time():
    now = time.time()
    assert format_relative_time(now - 10) == "just now"
    assert format_relative_time(now - 120) == "2m ago"
    assert format_relative_time(now - 7200) == "2h ago"
    assert format_relative_time(now - 86400 * 3) == "3d ago"


def test_search_modal_displays_initial_recent_items(populated_vault, qtbot, qapp):
    modal = SearchModal(vault=populated_vault)
    qtbot.addWidget(modal)
    modal.show()

    # Initial view (empty query) should show all recent records
    assert modal.results_list.count() == 2


def test_search_modal_filters_in_realtime(populated_vault, qtbot, qapp):
    modal = SearchModal(vault=populated_vault)
    qtbot.addWidget(modal)
    modal.show()

    # Type query in search input
    modal.search_input.setText("FedEx")
    assert modal.results_list.count() == 1

    # Filter with non-matching query
    modal.search_input.setText("NonExistentKeywordXYZ")
    assert modal.results_list.count() == 0

    # Clear input restores all recent records
    modal.search_input.setText("")
    assert modal.results_list.count() == 2


def test_search_modal_copy_text_action(populated_vault, qtbot, qapp):
    modal = SearchModal(vault=populated_vault)
    qtbot.addWidget(modal)
    modal.show()

    modal.search_input.setText("OOMKilled")
    assert modal.results_list.count() == 1

    # Get the result card widget
    item = modal.results_list.item(0)
    card = modal.results_list.itemWidget(item)
    assert card is not None

    clipboard = QApplication.clipboard()
    clipboard.clear()

    # Click copy text button on the card
    qtbot.mouseClick(card.copy_text_btn, Qt.MouseButton.LeftButton)
    assert "exit code 137" in clipboard.text()


def test_search_modal_escape_closes(populated_vault, qtbot, qapp):
    modal = SearchModal(vault=populated_vault)
    qtbot.addWidget(modal)
    modal.show()
    assert modal.isVisible()

    qtbot.keyClick(modal, Qt.Key.Key_Escape)
    assert not modal.isVisible()
