"""Global system-wide hotkey listener using macOS Cocoa and Windows/Linux support."""

from __future__ import annotations
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from snipsense.core.hotkeys import GlobalHotkeyListener


class GlobalHotkeyManager(GlobalHotkeyListener):
    """Compatibility wrapper providing hotkey_triggered alias for snip_triggered."""

    hotkey_triggered = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.snip_triggered.connect(self.hotkey_triggered.emit)

    def _on_hotkey(self):
        """Manually triggers the snip signal for testing."""
        self.snip_triggered.emit()
