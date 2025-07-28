"""Main PyBlasher application for Momentum."""

import sys

from app import run_cli

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-c", "--cli"):
        # Run CLI app
        run_cli()
    else:
        # Run GUI app
        from gui import run_gui

        run_gui()
