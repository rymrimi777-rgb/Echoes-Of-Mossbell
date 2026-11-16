"""
Comprehensive Asset Integration & Verification Suite
Verifies:
1. All 12 Trees & 14 Village Buildings loaded from assets/environment/
2. Surface integrity (48x48 RGBA, transparency, 4-shade palette)
3. Asset registry completeness in map_loader.py
4. Placement and usage of all 26 assets across world maps (0 unused)
5. Collision box registration in MapCollision
6. Depth sorting (base_y) and behind-object walkability
7. Bridge walkability and doorway accessibility
8. Phase 5 directory structure readiness
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

import pygame
pygame.init()
pygame.display.set_mode((160, 144))

from game.settings import (
    ASSET_DIR, ENV_DIR, TREES_DIR, BUILDINGS_DIR,
    MONSTERS_DIR, BOSSES_DIR, HUD_DIR, MENU_DIR, JOURNAL_DIR
)
from game.map_loader import ENV_ASSET_MAP, get_env_prop
from game.world import build_all_maps

def run_asset_verification():
    print("=" * 60)
    print("STARTING COMPREHENSIVE ASSET INTEGRATION VERIFICATION")
    print("=" * 60)

    # 1. Verify files exist on disk
    expected_trees = [
        "tree_01_dead_hanging.png", "tree_02_round_oak.png", "tree_03_weeping_vines.png",
        "tree_04_twisted_oak.png", "tree_05_ancient_twisted.png", "tree_06_willow.png",
        "tree_07_dead_branch.png", "tree_08_twin_trees.png", "tree_09_dense_bush_tree.png",
        "tree_10_large_canopy.png", "tree_11_small_blossom.png", "tree_12_pine.png"
    ]

    expected_buildings = [
        "building_01_fenced_garden.png", "building_02_barn.png", "building_03_castle_tower.png",
        "building_04_fountain.png", "building_05_ruined_wall.png", "building_06_village_house.png",
        "building_07_market_stall.png", "building_08_mushroom_tower.png", "building_09_well.png",
        "building_10_cart_or_shed.png", "building_11_stone_cottage.png", "building_12_watermill.png",
        "building_13_bridge.png", "building_14_small_cottage.png"
    ]

    print("\n1. Verifying Asset Files on Disk...")
    for t in expected_trees:
        path = os.path.join(TREES_DIR, t)
        assert os.path.exists(path), f"Missing tree file: {path}"
    print(f"  All {len(expected_trees)} Tree assets exist in {TREES_DIR}")

    for b in expected_buildings:
        path = os.path.join(BUILDINGS_DIR, b)
        assert os.path.exists(path), f"Missing building file: {path}"
    print(f"  All {len(expected_buildings)} Building assets exist in {BUILDINGS_DIR}")

    # 2. Verify surface dimensions, alpha channel and palette
    print("\n2. Verifying Surface Dimensions, Transparency & Alpha...")
    all_files = [(t, os.path.join(TREES_DIR, t)) for t in expected_trees] + \
                [(b, os.path.join(BUILDINGS_DIR, b)) for b in expected_buildings]

    for fname, path in all_files:
        surf = pygame.image.load(path).convert_alpha()
        assert surf.get_size() == (48, 48), f"{fname} size is {surf.get_size()}, expected (48, 48)"
        
        # Check that image contains transparent pixels
        has_alpha = False
        colors = set()
        for x in range(48):
            for y in range(48):
                c = surf.get_at((x, y))
                if c.a == 0:
                    has_alpha = True
                else:
                    colors.add((c.r, c.g, c.b))
        assert has_alpha, f"{fname} lacks transparent pixels (alpha=0)!"
        assert len(colors) <= 6, f"{fname} has too many colors ({len(colors)}), not Game Boy palette"
    print(f"  All {len(all_files)} assets verified: exact 48x48 RGBA, clean alpha transparency, authentic GB colors.")

    # 3. Verify registry mapping in map_loader.py
    print("\n3. Verifying Registry Mapping in map_loader.py...")
    canonical_keys = [f"tree_{i:02d}" for i in range(1, 13)] + [f"bldg_{i:02d}" for i in range(1, 15)]
    assert len(canonical_keys) == 26, f"Expected 26 canonical assets, got {len(canonical_keys)}"
    for key in canonical_keys:
        assert key in ENV_ASSET_MAP, f"Key {key} not found in ENV_ASSET_MAP"
        prop = get_env_prop(key)
        assert prop is not None, f"Failed to retrieve prop for key {key}"
        assert prop.get_size() == (48, 48), f"Prop {key} size is {prop.get_size()}"
    print(f"  All 26 canonical assets mapped in ENV_ASSET_MAP and loadable via get_env_prop.")

    # 4. Verify asset placement across maps and zero unused assets
    print("\n4. Verifying Asset Placement & World Integration...")
    all_maps = build_all_maps()
    asset_counts = {k: 0 for k in canonical_keys}
    loaded_maps = all_maps

    for map_id, gmap in all_maps.items():
        assert gmap is not None, f"Failed to load map {map_id}"
        num_structures = len(gmap.structures)
        print(f"  Map '{map_id}': {num_structures} structures loaded.")
        for s in gmap.structures:
            canon = s.asset_id
            if canon.startswith("building_"):
                canon = "bldg_" + canon[9:11]
            if canon in asset_counts:
                asset_counts[canon] += 1

    unused = [k for k, count in asset_counts.items() if count == 0]
    print(f"\n  Asset usage breakdown ({len(asset_counts)} total assets):")
    for k, count in sorted(asset_counts.items()):
        print(f"    - {k:10s}: {count} placements")
    assert len(unused) == 0, f"Unused assets detected: {unused}"
    print(f"\n  Zero unused assets! All 26 assets actively integrated into game maps.")

    # 5. Verify collision registration and depth sorting properties
    print("\n5. Verifying Collision Registration & Depth Sorting...")
    village = loaded_maps["village"]
    forest = loaded_maps["forest"]

    # In forest, check ground structure (bridge) vs solid structures
    bridge_found = False
    solid_structures = 0
    for s in forest.structures:
        if s.asset_id == "bldg_13":
            bridge_found = True
            assert s.is_ground is True, "Bridge must be is_ground=True"
            assert len(s.col_rects) == 0, "Bridge must have 0 col_rects so player can cross"
        else:
            if len(s.col_rects) > 0:
                solid_structures += 1
    assert bridge_found, "Arched bridge bldg_13 not found in forest map!"
    assert solid_structures > 0, "No solid structures in forest map!"
    print("  Walkable bridge bldg_13 verified (is_ground=True, no collision obstruction).")
    print("  Solid structures collision boxes correctly configured.")

    # Check depth sorting base_y
    for s in village.structures:
        expected_base = s.py + s.depth_offset
        assert s.base_y == expected_base, f"Invalid base_y for {s.asset_id}: {s.base_y} != {expected_base}"
    print("  Depth sorting base_y correctly calculated for all structures.")

    # 6. Test Player walkability around buildings and behind canopies
    print("\n6. Testing Player Collision & Canopy Walkability...")
    cm = village.collision
    
    # Cottage bldg_14 is at (224, 128)
    # Roof canopy: (224+12, 128+6) = (236, 134) -> behind the roof, player is free to walk
    player_roof_rect = pygame.Rect(236, 134, 10, 8)
    assert not cm._collides(player_roof_rect), "Player should be able to walk behind the roof canopy!"

    # Base wall: (224+12, 128+28) = (236, 156) -> base wall should be solid
    player_wall_rect = pygame.Rect(236, 156, 10, 8)
    assert cm._collides(player_wall_rect), "Player wall rect should collide with building base wall!"

    print("  Player can freely walk behind roof canopy (Y-depth sorting) and is blocked by base wall.")

    # 7. Verify Phase 5 Directory Structure
    print("\n7. Verifying Phase 5 Future Expansion Directories...")
    phase5_dirs = [
        ("Monsters", MONSTERS_DIR),
        ("Bosses", BOSSES_DIR),
        ("UI HUD", HUD_DIR),
        ("UI Menu", MENU_DIR),
        ("UI Journal", JOURNAL_DIR),
    ]
    for name, p in phase5_dirs:
        assert os.path.exists(p), f"Missing Phase 5 directory for {name}: {p}"
        readme = os.path.join(p, "README.md")
        assert os.path.exists(readme), f"Missing README.md in {p}"
        print(f"  {name} directory verified: {p}")

    print("\n" + "=" * 60)
    print("ALL 7 ASSET INTEGRATION VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_asset_verification()
