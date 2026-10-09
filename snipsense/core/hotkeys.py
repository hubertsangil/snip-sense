"""Cross-platform system-wide global hotkey listener supporting macOS Cocoa and Windows/Linux."""

from __future__ import annotations
import sys
import threading
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class GlobalHotkeyListener(QObject):
    """Listens for system-wide global hotkeys (Alt+Z, Ctrl+Shift+S / Cmd+Shift+S, Alt+F).
    
    - On macOS: Uses native Cocoa NSEvent.addGlobalMonitorForEventsMatchingMask (0 thread collision, 100% safe).
    - On Windows / Linux: Uses pynput GlobalHotKeys background listener.
    """

    snip_triggered = pyqtSignal()
    hud_triggered = pyqtSignal()
    search_triggered = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._listener = None
        self._mac_monitor = None
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> bool:
        """Starts the global hotkey listener."""
        with self._lock:
            if self._running:
                return True

            if sys.platform == "darwin":
                try:
                    from AppKit import (
                        NSEvent,
                        NSEventMaskKeyDown,
                        NSEventModifierFlagOption,
                        NSEventModifierFlagCommand,
                        NSEventModifierFlagShift,
                        NSEventModifierFlagControl,
                    )

                    def _mac_key_handler(event):
                        try:
                            flags = event.modifierFlags()
                            chars = event.charactersIgnoringModifiers()
                            char_lower = chars.lower() if chars else ""

                            is_option = bool(flags & NSEventModifierFlagOption)
                            is_cmd = bool(flags & NSEventModifierFlagCommand)
                            is_shift = bool(flags & NSEventModifierFlagShift)
                            is_ctrl = bool(flags & NSEventModifierFlagControl)

                            # Option + Z (Alt + Z) -> HUD
                            if is_option and char_lower == "z":
                                self.hud_triggered.emit()
                            # Cmd + Shift + S or Ctrl + Shift + S -> Region Snip
                            elif (is_cmd or is_ctrl) and is_shift and char_lower == "s":
                                self.snip_triggered.emit()
                            # Option + F (Alt + F) -> Search Vault
                            elif is_option and char_lower == "f":
                                self.search_triggered.emit()
                        except Exception:
                            pass

                    self._mac_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                        NSEventMaskKeyDown, _mac_key_handler
                    )
                    self._running = self._mac_monitor is not None
                    return self._running
                except Exception:
                    self._running = False
                    return False

            # Windows / Linux fallback via pynput
            try:
                from pynput import keyboard

                hotkey_map = {
                    "<alt>+z": self._on_hud,
                    "<alt>+Z": self._on_hud,
                    "<ctrl>+<shift>+s": self._on_snip,
                    "<ctrl>+<shift>+S": self._on_snip,
                    "<alt>+f": self._on_search,
                    "<alt>+F": self._on_search,
                }

                self._listener = keyboard.GlobalHotKeys(hotkey_map)
                self._listener.daemon = True
                self._listener.start()
                self._running = True
                return True
            except Exception:
                self._running = False
                return False

    def stop(self):
        """Stops the global listener."""
        with self._lock:
            if sys.platform == "darwin" and self._mac_monitor:
                try:
                    from AppKit import NSEvent
                    NSEvent.removeMonitor_(self._mac_monitor)
                except Exception:
                    pass
                self._mac_monitor = None

            if self._listener:
                try:
                    self._listener.stop()
                except Exception:
                    pass
                self._listener = None

            self._running = False

    def is_running(self) -> bool:
        """Returns True if the global listener is currently active."""
        return self._running

    def _on_snip(self):
        self.snip_triggered.emit()

    def _on_hud(self):
        self.hud_triggered.emit()

    def _on_search(self):
        self.search_triggered.emit()
