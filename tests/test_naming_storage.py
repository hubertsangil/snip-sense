"""Unit tests for NamingEngine, filename sanitization, and StorageManager."""

from pathlib import Path
from PIL import Image
from snipsense.core.models import OCRTextBox
from snipsense.core.naming import (
    sanitize_filename,
    extract_app_name,
    extract_dominant_keyword,
    generate_filename,
)
from snipsense.core.storage import StorageManager


def test_sanitize_filename_removes_illegal_characters():
    assert sanitize_filename('test/file:name*with?illegal"chars<here>|') == "testfilenamewithillegalcharshere"
    assert sanitize_filename("my  cool   screenshot") == "my_cool_screenshot"
    assert sanitize_filename("...___file___...") == "file"
    assert sanitize_filename("") == "Snip"


def test_sanitize_filename_length_clamp():
    very_long = "a" * 100
    cleaned = sanitize_filename(very_long)
    assert len(cleaned) <= 50


def test_extract_app_name_known_applications():
    assert extract_app_name("main.py - snip-sense - Visual Studio Code") == "VSCode"
    assert extract_app_name("Amazon.com: Online Shopping - Google Chrome") == "Chrome"
    assert extract_app_name("Discord | #general | Server") == "Discord"
    assert extract_app_name("Administrator: Windows PowerShell") == "PowerShell"
    assert extract_app_name("Command Prompt - python main.py") == "CommandPrompt"
    assert extract_app_name("") == ""


def test_extract_app_name_generic_window():
    assert extract_app_name("My Document - CustomEditor") == "CustomEditor"
    assert extract_app_name("StandaloneWindow") == "Standalonewindow"


def test_extract_dominant_keyword():
    boxes = [
        OCRTextBox(text="the error in docker container", confidence=0.9, x=10, y=10, width=200, height=30, polygon=[]),
        OCRTextBox(text="code is 137", confidence=0.8, x=10, y=50, width=100, height=20, polygon=[]),
    ]
    keyword = extract_dominant_keyword(boxes)
    assert "Docker" in keyword or "Error" in keyword or "Container" in keyword
    assert "The" not in keyword


def test_generate_filename_synthesis():
    fixed_time = 1791550000.0  # Deterministic timestamp
    boxes = [
        OCRTextBox(text="Payment Successful", confidence=0.95, x=0, y=0, width=100, height=20, polygon=[])
    ]
    name = generate_filename("Chrome - Checkout", boxes, timestamp=fixed_time)
    assert name.startswith("Chrome_Payment_Successful_")
    assert name.endswith(".png")


def test_generate_filename_fallback_on_empty():
    fixed_time = 1791550000.0
    name = generate_filename("", [], timestamp=fixed_time)
    assert name.startswith("Snip_")
    assert name.endswith(".png")


def test_storage_manager_save_and_collision(tmp_path: Path):
    storage = StorageManager(base_directory=tmp_path)
    img = Image.new("RGB", (80, 50), color=(16, 185, 129))

    # 1. First save
    f1 = storage.save_image(img, "TestCapture.png")
    assert f1.exists()
    assert f1.name == "TestCapture.png"

    # 2. Second save with identical name triggers collision avoidance
    f2 = storage.save_image(img, "TestCapture.png")
    assert f2.exists()
    assert f2.name == "TestCapture_1.png"

    # 3. Third save increments again
    f3 = storage.save_image(img, "TestCapture.png")
    assert f3.exists()
    assert f3.name == "TestCapture_2.png"

    # Verify saved image is valid PNG with matching dimensions
    loaded = Image.open(f1)
    assert loaded.size == (80, 50)
    assert loaded.format == "PNG"
