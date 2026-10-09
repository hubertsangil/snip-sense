"""Entry point for SnipSense application."""

import sys

# Explicitly register Windows AppUserModelID so system tray notifications, toasts,
# and taskbar entries display 'SnipSense' rather than generic 'python'.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SnipSense.Desktop.CaptureStudio.1.0")
    except Exception:
        pass

from snipsense.app import SnipSenseApp

def main():
    app = SnipSenseApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
