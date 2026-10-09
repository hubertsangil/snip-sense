"""Entry point for SnipSense application."""

import sys
from snipsense.app import SnipSenseApp

def main():
    app = SnipSenseApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
