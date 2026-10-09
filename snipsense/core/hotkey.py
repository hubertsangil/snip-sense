"""Global system-wide hotkey listener using pynput and Qt signal dispatch."""

from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard


class GlobalHotkeyManager(QObject):
    """Listens for global key combinations across all applications and dispatches Qt signals."""

    hotkey_triggered = pyqtSignal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._listener: keyboard.GlobalHotKeys | None = None

    def _on_hotkey(self):
        """Callback invoked on pynput background thread."""
        self.hotkey_triggered.emit()

    def start(self):
        """Starts the global hotkey listener in a daemon background thread."""
        if self._listener is None:
            try:
                self._listener = keyboard.GlobalHotKeys({
                    "<ctrl>+<shift>+s": self._on_hotkey,
                })
                self._listener.daemon = True
                self._listener.start()
            except Exception:
                self._listener = None

    def stop(self):
        """Stops and cleans up the hotkey listener."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def is_running(self) -> bool:
        """Checks if the hotkey listener thread is active."""
        return self._listener is not None and self._listener.is_alive()
