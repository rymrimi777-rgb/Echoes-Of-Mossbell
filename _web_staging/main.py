"""
Root launcher for Echoes of Mossbell.
Compatible with Desktop (Windows), Mobile (Android), and WebAssembly (Pygbag HTML5).
"""
import os
import sys
import asyncio

# Ensure project root is in sys.path
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from game.main import Game


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
