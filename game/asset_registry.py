"""
Centralized Asset Registry for Echoes of Mossbell.
Catalogues all environmental structures, decorations, monsters, and items
with dimensions, frame specifications, collision defaults, and palette verification.
"""
import os
import pygame
from game.settings import (
    ASSET_DIR, ENV_DIR, TREES_DIR, BUILDINGS_DIR, DECOR_DIR,
    MONSTERS_DIR, BOSSES_DIR, TILE_DIR, ITEM_DIR, AUDIO_DIR
)

# -----------------------------------------------------------------------------
# 1. Environmental Structures (48x48 Trees & Buildings)
# -----------------------------------------------------------------------------
STRUCTURE_CATALOG = {
    # 12 Trees
    "tree_01": {"file": "tree_01_dead_hanging.png",    "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_02": {"file": "tree_02_round_oak.png",       "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_03": {"file": "tree_03_weeping_vines.png",   "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_04": {"file": "tree_04_twisted_oak.png",     "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_05": {"file": "tree_05_ancient_twisted.png", "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_06": {"file": "tree_06_willow.png",          "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_07": {"file": "tree_07_dead_branch.png",     "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_08": {"file": "tree_08_twin_trees.png",      "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_09": {"file": "tree_09_dense_bush_tree.png", "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_10": {"file": "tree_10_large_canopy.png",    "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_11": {"file": "tree_11_small_blossom.png",   "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},
    "tree_12": {"file": "tree_12_pine.png",            "dir": TREES_DIR, "w": 48, "h": 48, "type": "tree"},

    # 14 Village Buildings
    "bldg_01": {"file": "building_01_fenced_garden.png",  "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_02": {"file": "building_02_barn.png",           "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_03": {"file": "building_03_castle_tower.png",   "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_04": {"file": "building_04_fountain.png",       "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_05": {"file": "building_05_ruined_wall.png",    "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_06": {"file": "building_06_village_house.png",  "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_07": {"file": "building_07_market_stall.png",   "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_08": {"file": "building_08_mushroom_tower.png", "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_09": {"file": "building_09_well.png",           "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_10": {"file": "building_10_cart_or_shed.png",   "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_11": {"file": "building_11_stone_cottage.png",  "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_12": {"file": "building_12_watermill.png",      "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
    "bldg_13": {"file": "building_13_bridge.png",         "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "bridge"},
    "bldg_14": {"file": "building_14_small_cottage.png",  "dir": BUILDINGS_DIR, "w": 48, "h": 48, "type": "building"},
}

# -----------------------------------------------------------------------------
# 2. Environmental Decorations & Bridges (from Free_1.1)
# -----------------------------------------------------------------------------
DECORATION_CATALOG = {
    "bridge_h":         {"file": "bridge_horizontal.png",     "w": 32, "h": 16, "is_ground": True,  "type": "bridge"},
    "bridge_v":         {"file": "bridge_vertical.png",       "w": 16, "h": 32, "is_ground": True,  "type": "bridge"},
    "cave_entrance":    {"file": "cave_entrance.png",         "w": 48, "h": 32, "is_ground": False, "type": "cave"},
    "cave_exit":        {"file": "cave_exit.png",             "w": 32, "h": 16, "is_ground": False, "type": "cave"},
    "cave_boulder":     {"file": "cave_boulder.png",          "w": 16, "h": 16, "is_ground": False, "type": "rock"},
    "cave_stairs_up":   {"file": "cave_stairs_up.png",        "w": 16, "h": 16, "is_ground": True,  "type": "stairs"},
    "cave_stairs_down": {"file": "cave_stairs_down.png",      "w": 16, "h": 16, "is_ground": True,  "type": "stairs"},
    "stepping_stones":  {"file": "stepping_stones_water.png", "w": 16, "h": 16, "is_ground": True,  "type": "crossing"},
    "rock_water_big":   {"file": "rock_water_big.png",        "w": 32, "h": 32, "is_ground": False, "type": "rock"},
    "tall_grass":       {"file": "tall_grass.png",            "w": 32, "h": 16, "is_ground": True,  "type": "flora"},
    "reeds":            {"file": "reeds.png",                 "w": 16, "h": 16, "is_ground": True,  "type": "flora"},
    "pine_tall":        {"file": "pine_tall.png",             "w": 16, "h": 32, "is_ground": False, "type": "tree"},
    "bench_h":          {"file": "bench_horizontal.png",      "w": 32, "h": 16, "is_ground": False, "type": "furniture"},
    "lampost":          {"file": "lampost.png",               "w": 16, "h": 48, "is_ground": False, "type": "landmark"},
    "fence_picket":     {"file": "fence_picket.png",          "w": 24, "h": 48, "is_ground": False, "type": "fence"},
    "signpost_wood":    {"file": "signpost.png",              "w": 32, "h": 16, "is_ground": False, "type": "sign"},
}

# -----------------------------------------------------------------------------
# 3. Monster & Boss Catalog (from SGQ_Enemies)
# -----------------------------------------------------------------------------
MONSTER_CATALOG = {
    # Small 16x16 nominal frames
    "slime": {
        "name": "Green Slime",
        "file": "slime.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 6,
        "max_hp": 4, "atk": 2, "speed": 0.5, "ai": "patrol",
        "exp": 5, "loot": "coins",
    },
    "rat": {
        "name": "Giant Rat",
        "file": "rat.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 6,
        "max_hp": 6, "atk": 2, "speed": 0.9, "ai": "chase",
        "exp": 8, "loot": "bread",
    },
    "bat": {
        "name": "Shadow Bat",
        "file": "bat.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 6,
        "max_hp": 8, "atk": 3, "speed": 1.1, "ai": "flutter",
        "exp": 10, "loot": None,
    },
    "fly": {
        "name": "Swarm Fly",
        "file": "fly.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 4,
        "max_hp": 6, "atk": 2, "speed": 1.0, "ai": "flutter",
        "exp": 8, "loot": None,
    },
    "goblin": {
        "name": "Forest Goblin",
        "file": "goblin.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 6,
        "max_hp": 12, "atk": 3, "speed": 0.7, "ai": "chase",
        "exp": 15, "loot": "herb",
    },
    "spider": {
        "name": "Cave Spider",
        "file": "spider.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 6,
        "max_hp": 12, "atk": 3, "speed": 0.8, "ai": "patrol",
        "exp": 14, "loot": None,
    },
    "skeleton": {
        "name": "Crypt Skeleton",
        "file": "skeleton.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 6,
        "max_hp": 16, "atk": 4, "speed": 0.6, "ai": "chase",
        "exp": 20, "loot": "coins",
    },
    "ghost": {
        "name": "Ruins Phantom",
        "file": "ghost.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 4,
        "max_hp": 14, "atk": 3, "speed": 0.7, "ai": "patrol",
        "exp": 18, "loot": "crystal",
    },
    "flying_skull": {
        "name": "Cursed Skull",
        "file": "flying_skull.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 16,
        "cols": 4, "rows": 4,
        "max_hp": 14, "atk": 4, "speed": 1.0, "ai": "chase",
        "exp": 18, "loot": None,
    },
    # Tall 16x32 nominal frames
    "cube_slime": {
        "name": "Gelatinous Cube",
        "file": "cube_slime.png",
        "dir": MONSTERS_DIR,
        "frame_w": 16, "frame_h": 32,
        "cols": 4, "rows": 6,
        "max_hp": 18, "atk": 4, "speed": 0.4, "ai": "patrol",
        "exp": 22, "loot": "mushroom",
    },
    # Medium 32x32 nominal frames
    "medium_slime": {
        "name": "Great Slime",
        "file": "medium_slime.png",
        "dir": MONSTERS_DIR,
        "frame_w": 32, "frame_h": 32,
        "cols": 4, "rows": 6,
        "max_hp": 24, "atk": 4, "speed": 0.5, "ai": "chase",
        "exp": 30, "loot": "elixir",
    },
    # Boss
    "slime_king": {
        "name": "Slime Sovereign",
        "file": "slime_king.png",
        "dir": BOSSES_DIR,
        "frame_w": 60, "frame_h": 64,
        "cols": 4, "rows": 6,
        "max_hp": 60, "atk": 6, "speed": 0.5, "ai": "boss",
        "exp": 100, "loot": "sun_amulet",
    },
}

_cache = {}


def get_asset_surface(asset_id):
    """Retrieve cached Pygame Surface for any registered asset."""
    if asset_id in _cache:
        return _cache[asset_id]

    path = None
    if asset_id in STRUCTURE_CATALOG:
        entry = STRUCTURE_CATALOG[asset_id]
        path = os.path.join(entry["dir"], entry["file"])
    elif asset_id in DECORATION_CATALOG:
        entry = DECORATION_CATALOG[asset_id]
        path = os.path.join(DECOR_DIR, entry["file"])
    elif asset_id in MONSTER_CATALOG:
        entry = MONSTER_CATALOG[asset_id]
        path = os.path.join(entry["dir"], entry["file"])

    if path and os.path.isfile(path):
        surf = pygame.image.load(path)
        if pygame.display.get_surface() is not None:
            try:
                surf = surf.convert_alpha()
            except Exception:
                pass
        _cache[asset_id] = surf
        return surf

    return None
