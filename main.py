"""
Root launcher for Echoes of Mossbell.
Enables standard packaging tools (Buildozer, python-for-android, PyInstaller) to run out of the box.
"""
import os
import sys

# Ensure project root is in sys.path
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from game.main import main

if __name__ == "__main__":
    main()

