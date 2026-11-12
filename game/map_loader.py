"""
Map loader and tile rendering engine with animated tiles (water, flowers),
interior and dungeon tilesets, interactive objects, and warps.
"""
import pygame, os
from game.settings import TILE_SIZE, TILE_DIR, SPRITE_DIR, COLOR_LIGHTEST, COLOR_DARKEST
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
                 items=None, interactives=None, music=None):
        self.map_id = map_id
        self.width = width
        self.height = height
        self.ground = ground
        self.props = props or []              # list of (tile_id, tx, ty)
        self.big_props = big_props or []       # list of (id, px, py)
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
