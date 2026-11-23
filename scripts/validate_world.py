"""
Script: scripts/validate_world.py
Runs the 10-point automated map validation suite for Echoes of Mossbell.
"""
import sys
import os

# Ensure project root is in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
pygame.init()
try:
    pygame.display.set_mode((160, 144), pygame.HIDDEN)
except Exception:
    pass

from game.map_validator import MapValidator


def main():
    print("=" * 70)
    print("ECHOES OF MOSSBELL — 10-POINT AUTOMATED MAP & WORLD VALIDATION SUITE")
    print("=" * 70)

    validator = MapValidator()
    all_passed, results = validator.run_all_checks()

    for check_name, res in sorted(results.items()):
        status_tag = "[PASS]" if res["passed"] else "[FAIL]"
        print(f"\n{status_tag} {check_name.upper()}:")
        for note in res.get("notes", []):
            print(f"   * {note}")

    print("\n" + "=" * 70)
    if all_passed:
        print("OVERALL RESULT: ALL 10 WORLD VALIDATION CHECKS PASSED SUCCESSFULLY!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("OVERALL RESULT: ONE OR MORE VALIDATION CHECKS FAILED.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
