"""Unit and UI integration tests for the OverlayHUD component (Surface 4)."""

import time
from pathlib import Path
import pytest
from PIL import Image
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication
from snipsense.core.vault import VaultDatabase
from snipsense.ui.overlay_hud import OverlayHUD, RecentCaptureCard


@pytest.fixture
def populated_vault(tmp_path: Path) -> VaultDatabase:
    """Provides a temporary VaultDatabase pre-populated with test records."""
    db_file = tmp_path / "hud_test_vault.db"
    vault = VaultDatabase(db_path=db_file)

    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    img1 = img_dir / "VSCode_Crash.png"
    Image.new("RGB", (120, 80), color=(30, 41, 59)).save(img1)
    vault.index_capture(
        file_path=img1,
        title="VSCode_Crash",
        ocr_text="SIGSEGV address 0x0000",
        tags="#dev,#bug",
        created_at=time.time() - 60,
    )

    img2 = img_dir / "Amazon_Order.png"
    Image.new("RGB", (120, 80), color=(15, 23, 42)).save(img2)
    vault.index_capture(
        file_path=img2,
        title="Amazon_Order",
        ocr_text="Order total $99.00",
        tags="#receipt",
        created_at=time.time() - 3600,
    )

    return vault


def test_overlay_hud_initializes_with_carousel_items(populated_vault, qtbot, qapp):
    hud = OverlayHUD(vault=populated_vault)
    qtbot.addWidget(hud)
    hud.show()

    assert hud.isVisible()
    # Check that the 2 items from vault are populated in the carousel layout
    cards = hud.get_carousel_cards()
    assert len(cards) == 2
    assert cards[0].result.title == "VSCode_Crash"
    assert cards[1].result.title == "Amazon_Order"


def test_overlay_hud_actions_signals(populated_vault, qtbot, qapp):
    hud = OverlayHUD(vault=populated_vault)
    qtbot.addWidget(hud)
    hud.show()

    snip_triggered = []
    search_triggered = []

    hud.snip_requested.connect(lambda: snip_triggered.append(True))
    hud.search_requested.connect(lambda: search_triggered.append(True))

    # Click Quick Action: Snip Area
    qtbot.mouseClick(hud.snip_action_btn, Qt.MouseButton.LeftButton)
    assert len(snip_triggered) == 1
    assert not hud.isVisible()  # Should close when initiating snip

    hud.show()
    # Click Quick Action: Search Vault
    qtbot.mouseClick(hud.search_action_btn, Qt.MouseButton.LeftButton)
    assert len(search_triggered) == 1


def test_recent_capture_card_copy_actions(populated_vault, qtbot, qapp):
    hud = OverlayHUD(vault=populated_vault)
    qtbot.addWidget(hud)
    hud.show()

    cards = hud.get_carousel_cards()
    assert len(cards) >= 1
    card = cards[0]

    clipboard = QApplication.clipboard()
    clipboard.clear()

    # Test copy text from card
    qtbot.mouseClick(card.copy_text_btn, Qt.MouseButton.LeftButton)
    assert "SIGSEGV" in clipboard.text()

    # Test copy image from card
    clipboard.clear()
    qtbot.mouseClick(card.copy_img_btn, Qt.MouseButton.LeftButton)
    assert not clipboard.pixmap().isNull()


def test_overlay_hud_escape_dismisses(populated_vault, qtbot, qapp):
    hud = OverlayHUD(vault=populated_vault)
    qtbot.addWidget(hud)
    hud.show()
    assert hud.isVisible()

    qtbot.keyClick(hud, Qt.Key.Key_Escape)
    assert not hud.isVisible()
