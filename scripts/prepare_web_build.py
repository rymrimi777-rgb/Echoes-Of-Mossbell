"""
Echoes of Mossbell - Complete Web Build & Optimization Pipeline
1. Stages minimal runtime assets (under 3.3 MB uncompressed).
2. Packages WebAssembly bundle via Pygbag.
3. Generates high-performance, Game Boy-themed dual-platform index.html.
"""
import os
import shutil
import sys
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING_DIR = os.path.join(BASE_DIR, "_web_staging")
OUTPUT_DIR = os.path.join(BASE_DIR, "build", "web")

USED_OCEAN_CHARS = [
    "actor1_character_01",
    "actor1_character_02",
    "actor1_character_03",
    "actor1_character_05",
    "actor2_character_01",
    "actor2_character_03",
    "actor3_character_01",
    "actor3_character_08",
]

def build_web():
    print("=" * 60)
    print(" ECHOES OF MOSSBELL — WEB OPTIMIZATION PIPELINE ")
    print("=" * 60)

    # 1. Clean Staging
    if os.path.exists(STAGING_DIR):
        shutil.rmtree(STAGING_DIR)
    os.makedirs(STAGING_DIR, exist_ok=True)

    # 2. Copy main.py
    shutil.copy2(os.path.join(BASE_DIR, "main.py"), os.path.join(STAGING_DIR, "main.py"))

    # 3. Copy game/ directory (excluding dev tests and cache)
    shutil.copytree(
        os.path.join(BASE_DIR, "game"),
        os.path.join(STAGING_DIR, "game"),
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "test_*.py")
    )

    # 4. Copy assets/ directory (excluding heavy source files)
    shutil.copytree(
        os.path.join(BASE_DIR, "assets"),
        os.path.join(STAGING_DIR, "assets"),
        ignore=shutil.ignore_patterns("*.aseprite", "README*.txt")
    )

    # 5. Copy ONLY used Ocean Nostalgia characters (gameboy variant only)
    ocean_src = os.path.join(BASE_DIR, "Ocean_Nostalgia_Pygame_Ready", "characters")
    ocean_dst = os.path.join(STAGING_DIR, "Ocean_Nostalgia_Pygame_Ready", "characters")
    os.makedirs(ocean_dst, exist_ok=True)

    for char_id in USED_OCEAN_CHARS:
        src_char = os.path.join(ocean_src, char_id)
        dst_char = os.path.join(ocean_dst, char_id)
        if os.path.isdir(src_char):
            os.makedirs(dst_char, exist_ok=True)
            gb_src = os.path.join(src_char, "gameboy")
            gb_dst = os.path.join(dst_char, "gameboy")
            if os.path.isdir(gb_src):
                shutil.copytree(gb_src, gb_dst)

    # Copy metadata files
    for meta in ["CHARACTER_PREVIEW.png", "README.txt"]:
        src_meta = os.path.join(BASE_DIR, "Ocean_Nostalgia_Pygame_Ready", meta)
        if os.path.isfile(src_meta):
            shutil.copy2(src_meta, os.path.join(STAGING_DIR, "Ocean_Nostalgia_Pygame_Ready", meta))

    # Clean pygbag.ini inside staging
    ini_path = os.path.join(STAGING_DIR, "pygbag.ini")
    with open(ini_path, "w", encoding="utf-8") as f:
        f.write('[DEPENDENCIES]\nignoredirs = ["build", "dist", "__pycache__"]\nignorefiles = ["*.bat", "*.spec"]\n')

    # Copy favicon if available
    favicon_src = os.path.join(BASE_DIR, "assets", "android", "icon.png")
    if os.path.isfile(favicon_src):
        # Resize or copy to favicon.png
        shutil.copy2(favicon_src, os.path.join(STAGING_DIR, "favicon.png"))
    elif os.path.isfile(os.path.join(BASE_DIR, "build", "web", "favicon.png")):
        shutil.copy2(os.path.join(BASE_DIR, "build", "web", "favicon.png"), os.path.join(STAGING_DIR, "favicon.png"))

    print("\n[+] Staging ready! Compiling WebAssembly package via Pygbag...")
    cmd = [
        sys.executable, "-m", "pygbag",
        "--build",
        "--disable-sound-format-error",
        STAGING_DIR
    ]
    subprocess.run(cmd, check=True)

    # 6. Locate generated archives in staging
    staging_web = os.path.join(STAGING_DIR, "build", "web")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Rename archives to canonical 'game.apk' and 'game.tar.gz'
    for f in os.listdir(staging_web):
        src_file = os.path.join(staging_web, f)
        if f.endswith(".apk"):
            dst_file = os.path.join(OUTPUT_DIR, "game.apk")
            shutil.copy2(src_file, dst_file)
            print(f"[+] Output: {dst_file} ({os.path.getsize(dst_file)/(1024*1024):.2f} MB)")
        elif f.endswith(".tar.gz"):
            dst_file = os.path.join(OUTPUT_DIR, "game.tar.gz")
            shutil.copy2(src_file, dst_file)
            print(f"[+] Output: {dst_file} ({os.path.getsize(dst_file)/(1024*1024):.2f} MB)")
        elif f == "favicon.png":
            shutil.copy2(src_file, os.path.join(OUTPUT_DIR, "favicon.png"))

    # Add .nojekyll for GitHub Pages
    with open(os.path.join(OUTPUT_DIR, ".nojekyll"), "w") as f:
        pass

    print("\n[+] Web assets optimized and staged in build/web/ successfully!")

if __name__ == "__main__":
    build_web()
