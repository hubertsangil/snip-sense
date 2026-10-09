"""Pytest fixtures and Qt initialization for headless test execution."""

import os
import pytest
from PyQt6.QtWidgets import QApplication

# Set offscreen platform if running headless or CI
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

@pytest.fixture(scope="session")
def qapp():
    """Provides a shared QApplication instance across tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
