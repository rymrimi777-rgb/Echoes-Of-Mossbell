"""
Map loader and tile rendering engine with animated tiles (water, flowers),
interior and dungeon tilesets, interactive objects, and warps.
"""
import pygame, os
from game.settings import (TILE_SIZE, TILE_DIR, SPRITE_DIR, COLOR_LIGHTEST, COLOR_DARKEST,
                           ENV_DIR, TREES_DIR, BUILDINGS_DIR)
from game.animation import load_image, TileStripAnimator
from game.collision import CollisionMap

# ---- Global Tile Cache -----------------------------------------------------
_tile_cache = {}

# Animated tile singletons
_anim_water = None
_anim_flowers = None


def init_animators():
    global _anim_water, _anim_flowers
    if _anim_water is None:
        w_path = os.path.join(TILE_DIR, "anim_water_tile_strip4.png")
        _anim_water = TileStripAnimator(w_path, 16, 16, 4, 150)
    if _anim_flowers is None:
        f_path = os.path.join(TILE_DIR, "anim_flowers_strip4.png")
        _anim_flowers = TileStripAnimator(f_path, 16, 16, 4, 150)


def update_tile_animators(dt_ms):
    init_animators()
    _anim_water.update(dt_ms)
    _anim_flowers.update(dt_ms)


def get_tile(name):
    """Return a 16x16 surface for the named tile."""
    # Special animated tiles
    if name == "wt":
        init_animators()
        return _anim_water.get_frame()
    elif name == "fl":
        init_animators()
        return _anim_flowers.get_frame()

    if name in _tile_cache:
        return _tile_cache[name]

    # Ground tiles
    ground_map = {
        "g0": os.path.join(TILE_DIR, "ground", "grass_0.png"),
        "g2": os.path.join(TILE_DIR, "ground", "grass_2.png"),
        "g4": os.path.join(TILE_DIR, "ground", "grass_4.png"),
        "p1": os.path.join(TILE_DIR, "ground", "path_1.png"),
    }
    # Props (16x16)
    prop_map = {
        "bu": os.path.join(TILE_DIR, "props", "bush.png"),
        "ch": os.path.join(TILE_DIR, "props", "chest.png"),
        "rk": os.path.join(TILE_DIR, "props", "rock.png"),
        "bo": os.path.join(TILE_DIR, "props", "bones.png"),
        "gr": os.path.join(TILE_DIR, "props", "grave.png"),
        "fn": os.path.join(TILE_DIR, "props", "fence_v.png"),
        "st": os.path.join(TILE_DIR, "props", "stump.png"),
    }

    path = None
    if name in ground_map:
        path = ground_map[name]
    elif name in prop_map:
        path = prop_map[name]
    elif name.startswith("in_"):
        # Interior tiles (e.g. in_0_0)
        path = os.path.join(TILE_DIR, "interior", f"{name}.png")
    elif name.startswith("ex_"):
        # Exterior tiles (e.g. ex_0_0)
        path = os.path.join(TILE_DIR, "exterior", f"{name}.png")
    elif name.startswith("dg_"):
        # Dungeon tiles (e.g. dg_0_0)
        path = os.path.join(TILE_DIR, "dungeon", f"{name}.png")

    if path and os.path.isfile(path):
        _tile_cache[name] = load_image(path)
    else:
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.fill((139, 172, 15))
        _tile_cache[name] = s

    return _tile_cache[name]


# ---- Big Prop Cache (32x32 trees etc.) -------------------------------------
_big_cache = {}


def get_big_prop(name):
    if name in _big_cache:
        return _big_cache[name]
    files = {
        "tr": os.path.join(TILE_DIR, "trees", "tree_round.png"),
        "td": os.path.join(TILE_DIR, "trees", "tree_dead.png"),
    }
    if name in files and os.path.isfile(files[name]):
        _big_cache[name] = load_image(files[name])
    else: 
        s = pygame.Surface((32, 32))
        s.fill((48, 98, 48))
        _big_cache[name] = s
    return _big_cache[name]


# ---- Environment Assets & Structures (Trees & Village Buildings 48x48) ------
_env_cache = {}

ENV_ASSET_MAP = {
    # 12 Trees
    "tree_01": os.path.join(TREES_DIR, "tree_01_dead_hanging.png"),
    "tree_02": os.path.join(TREES_DIR, "tree_02_round_oak.png"),
    "tree_03": os.path.join(TREES_DIR, "tree_03_weeping_vines.png"),
    "tree_04": os.path.join(TREES_DIR, "tree_04_twisted_oak.png"),
    "tree_05": os.path.join(TREES_DIR, "tree_05_ancient_twisted.png"),
    "tree_06": os.path.join(TREES_DIR, "tree_06_willow.png"),
    "tree_07": os.path.join(TREES_DIR, "tree_07_dead_branch.png"),
    "tree_08": os.path.join(TREES_DIR, "tree_08_twin_trees.png"),
    "tree_09": os.path.join(TREES_DIR, "tree_09_dense_bush_tree.png"),
    "tree_10": os.path.join(TREES_DIR, "tree_10_large_canopy.png"),
    "tree_11": os.path.join(TREES_DIR, "tree_11_small_blossom.png"),
    "tree_12": os.path.join(TREES_DIR, "tree_12_pine.png"),
    # 14 Village Buildings
    "bldg_01": os.path.join(BUILDINGS_DIR, "building_01_fenced_garden.png"),
    "bldg_02": os.path.join(BUILDINGS_DIR, "building_02_barn.png"),
    "bldg_03": os.path.join(BUILDINGS_DIR, "building_03_castle_tower.png"),
    "bldg_04": os.path.join(BUILDINGS_DIR, "building_04_fountain.png"),
    "bldg_05": os.path.join(BUILDINGS_DIR, "building_05_ruined_wall.png"),
    "bldg_06": os.path.join(BUILDINGS_DIR, "building_06_village_house.png"),
    "bldg_07": os.path.join(BUILDINGS_DIR, "building_07_market_stall.png"),
    "bldg_08": os.path.join(BUILDINGS_DIR, "building_08_mushroom_tower.png"),
    "bldg_09": os.path.join(BUILDINGS_DIR, "building_09_well.png"),
    "bldg_10": os.path.join(BUILDINGS_DIR, "building_10_cart_or_shed.png"),
    "bldg_11": os.path.join(BUILDINGS_DIR, "building_11_stone_cottage.png"),
    "bldg_12": os.path.join(BUILDINGS_DIR, "building_12_watermill.png"),
    "bldg_13": os.path.join(BUILDINGS_DIR, "building_13_bridge.png"),
    "bldg_14": os.path.join(BUILDINGS_DIR, "building_14_small_cottage.png"),
}

# Register alternate naming aliases
for _k, _p in list(ENV_ASSET_MAP.items()):
    _base = os.path.splitext(os.path.basename(_p))[0]
    ENV_ASSET_MAP[_base] = _p
    if _k.startswith("bldg_"):
        ENV_ASSET_MAP["building_" + _k[5:]] = _p


def get_env_prop(asset_id):
    """Retrieve 48x48 transparent surface for tree or building."""
    if asset_id in _env_cache:
        return _env_cache[asset_id]

    path = ENV_ASSET_MAP.get(asset_id)
    if not path or not os.path.isfile(path):
        for d in (TREES_DIR, BUILDINGS_DIR):
            cand = os.path.join(d, f"{asset_id}.png")
            if os.path.isfile(cand):
                path = cand
                break

    if path and os.path.isfile(path):
        _env_cache[asset_id] = load_image(path)
    else:
        if asset_id in ("tr", "td"):
            return get_big_prop(asset_id)
        s = pygame.Surface((48, 48), pygame.SRCALPHA)
        s.fill((48, 98, 48, 255))
        _env_cache[asset_id] = s

    return _env_cache[asset_id]


class StructureDef:
    """
    Environmental structure (tree, building, landmark) in the world.
    Native resolution: 48x48 (3x3 tiles).
    Supports custom collision boxes and depth-sorting base_y.
    """
    def __init__(self, asset_id, px, py, col_boxes=None, depth_offset=38, is_ground=False):
        self.asset_id = asset_id
        self.px = px
        self.py = py
        self.w = 48
        self.h = 48
        self.is_ground = is_ground
        self.depth_offset = depth_offset
        self.base_y = py + depth_offset

        # Build collision rects
        if col_boxes is False:
            self.col_rects = []
        elif col_boxes is not None:
            if isinstance(col_boxes, tuple):
                col_boxes = [col_boxes]
            self.col_rects = [pygame.Rect(px + ox, py + oy, cw, ch) for (ox, oy, cw, ch) in col_boxes]
        else:
            # Default collision box according to asset category
            if self.is_ground or asset_id in ("bldg_13", "building_13", "building_13_bridge"):
                # Bridges and ground overlays are walkable
                self.col_rects = []
            elif asset_id.startswith("tree_") or asset_id.startswith("t_"):
                # Tree trunk collision: player can walk around trunk and behind canopy
                self.col_rects = [pygame.Rect(px + 18, py + 32, 12, 12)]
            elif asset_id in ("bldg_04", "building_04", "building_04_fountain"):
                # Fountain stone basin
                self.col_rects = [pygame.Rect(px + 8, py + 18, 32, 22)]
            elif asset_id in ("bldg_09", "building_09", "building_09_well"):
                # Water well
                self.col_rects = [pygame.Rect(px + 8, py + 16, 32, 22)]
            elif asset_id in ("bldg_03", "building_03", "building_03_castle_tower"):
                # Tower stone base
                self.col_rects = [pygame.Rect(px + 12, py + 26, 24, 20)]
            elif asset_id in ("bldg_08", "building_08", "building_08_mushroom_tower"):
                # Mushroom stalk
                self.col_rects = [pygame.Rect(px + 14, py + 28, 20, 18)]
            elif asset_id in ("bldg_10", "building_10", "building_10_cart_or_shed"):
                # Wooden cart
                self.col_rects = [pygame.Rect(px + 12, py + 18, 24, 20)]
            elif asset_id in ("bldg_07", "building_07", "building_07_market_stall"):
                # Market counter
                self.col_rects = [pygame.Rect(px + 6, py + 20, 36, 18)]
            elif asset_id in ("bldg_01", "building_01", "building_01_fenced_garden"):
                # Garden fence
                self.col_rects = [pygame.Rect(px + 6, py + 16, 36, 26)]
            elif asset_id in ("bldg_05", "building_05", "building_05_ruined_wall"):
                # Ruined stone wall
                self.col_rects = [pygame.Rect(px + 6, py + 18, 36, 18)]
            else:
                # Standard cottage / house / barn (solid base, open for walk-behind roof)
                self.col_rects = [pygame.Rect(px + 6, py + 22, 36, 22)]

    def get_surface(self):
        return get_env_prop(self.asset_id)


# ---- Definitions -----------------------------------------------------------
class NPCDef:
    def __init__(self, npc_id, name, sprite_file=None, x=0, y=0, direction="down",
                 dialogues=None, portrait=None, ocean_char_id=None, variant="gameboy"):
        self.npc_id = npc_id
        self.name = name
        self.sprite_file = sprite_file
        self.x = x
        self.y = y
        self.direction = direction
        self.dialogues = dialogues or []
        self.portrait = portrait
        self.ocean_char_id = ocean_char_id
        self.variant = variant

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, 16, 16)


class WarpDef:
    def __init__(self, x, y, w, h, target_map, target_x, target_y):
        self.rect = pygame.Rect(x, y, w, h)
        self.target_map = target_map
        self.target_x = target_x
        self.target_y = target_y


class ItemPickup:
    def __init__(self, item_id, x, y, flag_id=None):
        self.item_id = item_id
        self.x = x
        self.y = y
        self.flag_id = flag_id
        self.rect = pygame.Rect(x, y, 16, 16)


class InteractiveObject:
    """Furniture, signs, bookshelves, beds, and chests with examine dialogues."""
    def __init__(self, x, y, w, h, dialogues, on_interact=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.dialogues = dialogues
        self.on_interact = on_interact


# ---- GameMap ---------------------------------------------------------------
class GameMap:
    def __init__(self, map_id, width, height, ground, solids,
                 props=None, big_props=None, npcs=None, warps=None,
                 items=None, interactives=None, music=None, structures=None):
        self.map_id = map_id
        self.width = width
        self.height = height
        self.ground = ground
        self.props = props or []              # list of (tile_id, tx, ty)
        self.big_props = big_props or []       # list of (id, px, py)
        self.structures = structures or []     # list of StructureDef
        self.npcs = npcs or []
        self.warps = warps or []
        self.items = items or []
        self.interactives = interactives or []
        self.music = music

        # Build collision grid
        self.collision = CollisionMap(width, height)
        for ty, row in enumerate(solids):
            for tx, val in enumerate(row):
                if val:
                    self.collision.set_solid(tx, ty)

        # Big props collision (lower half)
        for pid, px, py in self.big_props:
            self.collision.add_rect(pygame.Rect(px, py + 16, 32, 16))

        # Structure collisions
        for st in self.structures:
            for cr in st.col_rects:
                self.collision.add_rect(cr)

        # Prop collisions
        for pid, tx, ty in self.props:
            if pid in ("bu", "rk", "fn", "st") or pid.startswith("in_") or pid.startswith("dg_"):
                # mark solid unless specified
                self.collision.set_solid(tx, ty)

        # Interactive objects collision
        for obj in self.interactives:
            self.collision.add_rect(obj.rect)

    def draw_ground(self, surface, camera):
        cam_left = max(0, camera.x // TILE_SIZE)
        cam_top = max(0, camera.y // TILE_SIZE)
        cam_right = min(self.width, cam_left + (surface.get_width() // TILE_SIZE) + 2)
        cam_bottom = min(self.height, cam_top + (surface.get_height() // TILE_SIZE) + 2)

        for ty in range(cam_top, cam_bottom):
            for tx in range(cam_left, cam_right):
                tile_id = self.ground[ty][tx]
                tile_surf = get_tile(tile_id)
                sx, sy = camera.apply(tx * TILE_SIZE, ty * TILE_SIZE)
                surface.blit(tile_surf, (sx, sy))

    def draw_ground_structures(self, surface, camera):
        """Draw flat ground structures such as bridges under entities' feet."""
        for st in self.structures:
            if st.is_ground:
                surf = st.get_surface()
                sx, sy = camera.apply(st.px, st.py)
                surface.blit(surf, (sx, sy))

    def draw_props(self, surface, camera):
        for pid, tx, ty in self.props:
            tile_surf = get_tile(pid)
            sx, sy = camera.apply(tx * TILE_SIZE, ty * TILE_SIZE)
            surface.blit(tile_surf, (sx, sy))

        for pid, px, py in self.big_props:
            prop_surf = get_big_prop(pid)
            sx, sy = camera.apply(px, py)
            surface.blit(prop_surf, (sx, sy))

    def draw_items(self, surface, camera, flags):
        from game.inventory import ITEMS
        for item in self.items:
            if item.flag_id and flags.get(item.flag_id):
                continue
            # Draw real item icon or chest
            if item.item_id in ITEMS:
                icon = ITEMS[item.item_id].get_icon()
            else:
                icon = get_tile("ch")
            sx, sy = camera.apply(item.x, item.y)
            surface.blit(icon, (sx, sy))
