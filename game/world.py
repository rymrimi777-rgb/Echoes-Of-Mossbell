"""
World definition – 8 connected maps with interiors, dungeons, animated water & flowers,
NPCs with animated portraits, interactive furniture, and secrets.
"""
from game.map_loader import GameMap, NPCDef, WarpDef, ItemPickup, InteractiveObject


def _fill(w, h, val):
    return [[val] * w for _ in range(h)]


# -----------------------------------------------------------------------------
# 1. MOSSBELL VILLAGE (22 x 18 tiles)
# -----------------------------------------------------------------------------
def build_village():
    W, H = 22, 18
    # Ground pattern
    ground = _fill(W, H, "g0")
    solids = _fill(W, H, 0)

    # Borders
    for tx in range(W):
        solids[0][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    # Main stone path through center
    for tx in range(3, 19):
        ground[9][tx] = "p1"
        ground[10][tx] = "p1"
    for ty in range(4, 15):
        ground[ty][10] = "p1"
        ground[ty][11] = "p1"
    # Path branches to player house (x=4) and elder house (x=16)
    for ty in range(5, 10):
        ground[ty][4] = "p1"
        ground[ty][16] = "p1"

    # Grass variants
    for ty in range(H):
        for tx in range(W):
            if ground[ty][tx] == "g0":
                if (tx * 3 + ty * 7) % 7 == 0:
                    ground[ty][tx] = "g2"
                elif (tx + ty * 5) % 11 == 0:
                    ground[ty][tx] = "g4"

    # Animated Flower garden (south-west)
    flower_coords = [(3, 13), (4, 13), (5, 13), (3, 14), (4, 14), (5, 14)]
    for fx, fy in flower_coords:
        ground[fy][fx] = "fl"

    # Village Pond with Animated Water (south-east: x=14..17, y=12..15)
    for py in range(12, 16):
        for px in range(14, 18):
            ground[py][px] = "wt"
            solids[py][px] = 1  # water is solid to walk on

    # Player House structure (top-left: x=2..6, y=1..4)
    for hy in range(1, 5):
        for hx in range(2, 7):
            solids[hy][hx] = 1
    # Elder House structure (top-right: x=14..18, y=1..4)
    for hy in range(1, 5):
        for hx in range(14, 19):
            solids[hy][hx] = 1
    # Village Storehouse (bottom-left: x=2..6, y=12..15)
    for hy in range(12, 16):
        for hx in range(2, 7):
            solids[hy][hx] = 1

    # Doors are open for entering!
    solids[4][4] = 0   # Player house door
    solids[4][16] = 0  # Elder house door

    # East exit open to forest
    solids[9][W - 1] = 0
    solids[10][W - 1] = 0

    # Trees along top and edges
    big_props = [
        ("tr", 0 * 16, 0 * 16),
        ("tr", 8 * 16, 0 * 16),
        ("tr", 19 * 16, 0 * 16),
        ("tr", 0 * 16, 6 * 16),
        ("tr", 19 * 16, 6 * 16),
        ("tr", 8 * 16, 14 * 16),
        ("tr", 19 * 16, 14 * 16),
    ]

    # Props: fences around garden, well, bushes, rocks
    props = [
        ("fn", 2, 13), ("fn", 2, 14), ("fn", 6, 13), ("fn", 6, 14),
        ("bu", 7, 3), ("bu", 13, 3), ("bu", 7, 12), ("bu", 13, 12),
        ("rk", 13, 15), ("rk", 18, 12),
        ("st", 9, 6),
    ]

    # Interactive Village Objects
    interactives = [
        InteractiveObject(4 * 16, 4 * 16, 16, 8, [
            "Your home. A cozy thatched cottage."
        ]),
        InteractiveObject(16 * 16, 4 * 16, 16, 8, [
            "Elder Orin's residence and village archive."
        ]),
        InteractiveObject(10 * 16, 7 * 16, 16, 16, [
            "Village Notice Board:",
            "'Beware of Whispering Woods after dusk.'",
            "'Report any strange sightings to Elder Orin.'"
        ]),
    ]

    # NPCs
    npcs = [
        NPCDef("elder", "Elder Orin", "old_man.png", 16 * 16, 6 * 16,
               "down", portrait="old_man", ocean_char_id="actor1_character_05",
               dialogues=[
                   {"text": "Welcome, young one. A heavy shadow has fallen over Mossbell.", "portrait": "old_man"},
                   {"text": "Three villagers have vanished into Whispering Woods.", "portrait": "old_man"},
                   {"text": "Please search the woods east of the village and uncover the truth.", "portrait": "old_man"}
               ]),
        NPCDef("healer", "Healer Fern", "king.png", 7 * 16, 13 * 16,
               "right", portrait="king", ocean_char_id="actor1_character_03",
               dialogues=[
                   {"text": "Greetings, traveler. I tend to the ailing of our village.", "portrait": "king"},
                   {"text": "My medicine chest is nearly bare. If you find Forest Herbs, bring them to me.", "portrait": "king"}
               ]),
        NPCDef("boy", "Timmy", "boy.png", 13 * 16, 11 * 16,
               "down", portrait="boy", ocean_char_id="actor1_character_02",
               dialogues=[
                   {"text": "I lost my mother's silver ring near the old watchtower ruins...", "portrait": "boy"},
                   {"text": "She went missing last full moon... I hope she is still safe.", "portrait": "boy"}
               ]),
        NPCDef("villager1", "Martha", "old_man.png", 6 * 16, 8 * 16,
               "right", portrait="old_man", ocean_char_id="actor2_character_03",
               dialogues=[
                   {"text": "The wind carries strange whispers at night.", "portrait": "old_man"},
                   {"text": "Lock your door tight before sunset!", "portrait": "old_man"}
               ]),
    ]

    # Warps:
    # 1. Door into Player House
    # 2. Door into Elder House
    # 3. East path into Forest
    warps = [
        WarpDef(4 * 16, 3 * 16 + 8, 16, 12, "player_house", 5 * 16, 8 * 16),
        WarpDef(16 * 16, 3 * 16 + 8, 16, 12, "elder_house", 5 * 16, 8 * 16),
        WarpDef((W - 1) * 16, 9 * 16, 16, 2 * 16, "forest", 16, 9 * 16),
    ]

    items = []

    return GameMap("village", W, H, ground, solids, props, big_props,
                   npcs, warps, items, interactives, music="bpag02 - Game Theme.mp3")


# -----------------------------------------------------------------------------
# 2. PLAYER HOUSE INTERIOR (12 x 10 tiles)
# -----------------------------------------------------------------------------
def build_player_house():
    W, H = 12, 10
    ground = _fill(W, H, "in_3_0")  # wooden floor
    solids = _fill(W, H, 0)

    # Perimeter walls
    for tx in range(W):
        solids[0][tx] = 1
        solids[1][tx] = 1  # top wall 2 tiles high
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    # Leave south doorway open
    solids[H - 1][5] = 0

    # Back wall tiles
    for tx in range(1, W - 1):
        ground[0][tx] = "in_0_0"
        ground[1][tx] = "in_1_0"

    # Carpet / Rug in center
    for rx in range(4, 8):
        for ry in range(4, 7):
            ground[ry][rx] = "p1"

    # Props in house:
    # Bed at top-left (x=2, y=2)
    props = [
        ("in_2_1", 2, 2), ("in_2_2", 3, 2),
        # Bookshelf (x=8, y=2)
        ("in_0_4", 8, 2), ("in_1_4", 8, 3),
        # Fireplace / Stove (x=5, y=1)
        ("in_0_6", 5, 1), ("in_1_6", 5, 2),
        # Table & Chairs (center)
        ("in_4_3", 5, 5), ("in_4_4", 6, 5),
        # Dresser / Chest (x=10, y=3)
        ("ch", 10, 2),
    ]

    # Interactive objects: Bed, Bookshelf, Fireplace, Dresser
    interactives = [
        InteractiveObject(2 * 16, 2 * 16, 2 * 16, 16, [
            "Your comfortable bed.",
            "You rest and recover your stamina. HP fully restored!"
        ], on_interact="heal_player"),
        InteractiveObject(8 * 16, 2 * 16, 16, 2 * 16, [
            "Bookshelf:",
            "'Tales of the Ancient Seal - Chapter 3:'",
            "'The Shadow Grotto lies hidden where the dead trees meet the eastern mists.'"
        ]),
        InteractiveObject(5 * 16, 1 * 16, 16, 2 * 16, [
            "The hearth fire burns warmly, filling the room with cedar aroma."
        ]),
    ]

    # Dresser contains an apple!
    items = [
        ItemPickup("apple", 10 * 16, 2 * 16, "house_apple"),
    ]

    # Exit warp to village
    warps = [
        WarpDef(5 * 16, (H - 1) * 16, 16, 16, "village", 4 * 16, 5 * 16),
    ]

    return GameMap("player_house", W, H, ground, solids, props, [],
                   [], warps, items, interactives, music="cag01 - Title Screen.mp3")


# -----------------------------------------------------------------------------
# 3. ELDER'S ARCHIVE INTERIOR (12 x 10 tiles)
# -----------------------------------------------------------------------------
def build_elder_house():
    W, H = 12, 10
    ground = _fill(W, H, "in_3_0")
    solids = _fill(W, H, 0)

    for tx in range(W):
        solids[0][tx] = 1
        solids[1][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    solids[H - 1][5] = 0

    for tx in range(1, W - 1):
        ground[0][tx] = "in_0_0"
        ground[1][tx] = "in_1_0"

    props = [
        # Multiple bookshelves
        ("in_0_4", 2, 2), ("in_1_4", 2, 3),
        ("in_0_4", 3, 2), ("in_1_4", 3, 3),
        ("in_0_4", 8, 2), ("in_1_4", 8, 3),
        ("in_0_4", 9, 2), ("in_1_4", 9, 3),
        # Desk and chair
        ("in_4_3", 5, 4), ("in_4_4", 6, 4),
        # Archive chest
        ("ch", 9, 6),
    ]

    interactives = [
        InteractiveObject(2 * 16, 2 * 16, 2 * 16, 2 * 16, [
            "Elder's Records: '100 years ago, a king succumbed to shadow.'",
            "'The seal was placed inside the watchtower crypt.'"
        ]),
        InteractiveObject(5 * 16, 4 * 16, 2 * 16, 16, [
            "The study desk is covered in maps of Whispering Woods."
        ]),
    ]

    items = [
        ItemPickup("gold_key", 9 * 16, 6 * 16, "elder_key"),
    ]

    warps = [
        WarpDef(5 * 16, (H - 1) * 16, 16, 16, "village", 16 * 16, 5 * 16),
    ]

    return GameMap("elder_house", W, H, ground, solids, props, [],
                   [], warps, items, interactives, music="cag02 - Game Theme-A.mp3")


# -----------------------------------------------------------------------------
# 4. WHISPERING WOODS (20 x 18 tiles)
# -----------------------------------------------------------------------------
def build_forest():
    W, H = 20, 18
    ground = _fill(W, H, "g0")
    solids = _fill(W, H, 0)

    for tx in range(W):
        solids[0][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    # Winding path
    for tx in range(W):
        ground[9][tx] = "p1"
    for ty in range(4, 15):
        ground[ty][10] = "p1"

    # Variety
    for ty in range(H):
        for tx in range(W):
            if ground[ty][tx] == "g0":
                if (tx * 7 + ty * 3) % 5 == 0:
                    ground[ty][tx] = "g2"
                elif (tx + ty * 4) % 9 == 0:
                    ground[ty][tx] = "g4"

    # Animated Flower patches in forest clearings
    for fx, fy in [(4, 5), (5, 5), (14, 5), (15, 5), (5, 13), (14, 13)]:
        ground[fy][fx] = "fl"

    # Forest stream with animated water (vertical brook on east side)
    for sy in range(2, 7):
        ground[sy][16] = "wt"
        solids[sy][16] = 1
    for sy in range(12, 16):
        ground[sy][16] = "wt"
        solids[sy][16] = 1

    # Exits:
    solids[9][0] = 0         # West -> Village
    solids[9][W - 1] = 0     # East -> Deep Forest
    solids[H - 1][10] = 0    # South -> Ruins

    # Dense trees
    big_props = []
    tree_coords = [
        (1, 1), (3, 1), (5, 1), (12, 1), (14, 1), (17, 1),
        (1, 3), (7, 3), (12, 3),
        (1, 11), (7, 11), (12, 11), (17, 11),
        (1, 14), (3, 15), (7, 15), (12, 15), (15, 15), (17, 14),
    ]
    for tx, ty in tree_coords:
        big_props.append(("tr", tx * 16, ty * 16))
        for dy in range(2):
            for dx in range(2):
                stx, sty = tx + dx, ty + dy
                if 0 <= stx < W and 0 <= sty < H:
                    solids[sty][stx] = 1

    # Re-open exits
    solids[9][0] = 0
    solids[9][W - 1] = 0
    solids[H - 1][10] = 0

    props = [
        ("bu", 8, 7), ("bu", 12, 7), ("bu", 8, 12),
        ("rk", 9, 6), ("rk", 11, 13),
        ("st", 11, 8),
    ]

    npcs = [
        NPCDef("woodsman", "Old Woodsman", "old_man.png", 9 * 16, 8 * 16,
               "down", portrait="old_man", ocean_char_id="actor2_character_01",
               dialogues=[
                   {"text": "Beware... deep in the forest, the shadows take physical form.", "portrait": "old_man"},
                   {"text": "I heard an unearthly wail from the watchtower to the south.", "portrait": "old_man"}
               ]),
    ]

    interactives = [
        InteractiveObject(10 * 16, 12 * 16, 16, 16, [
            "Signpost: 'South -> Watchtower Ruins. East -> Deep Woods (Dangerous).'"
        ]),
    ]

    items = [
        ItemPickup("herb", 4 * 16, 6 * 16, "herb_1"),
        ItemPickup("herb", 15 * 16, 6 * 16, "herb_2"),
        ItemPickup("herb", 6 * 16, 14 * 16, "herb_3"),
    ]

    warps = [
        WarpDef(0, 9 * 16, 16, 16, "village", 20 * 16, 9 * 16),
        WarpDef((W - 1) * 16, 9 * 16, 16, 16, "deep_forest", 16, 9 * 16),
        WarpDef(10 * 16, (H - 1) * 16, 16, 16, "ruins", 10 * 16, 16),
    ]

    return GameMap("forest", W, H, ground, solids, props, big_props,
                   npcs, warps, items, interactives, music="cag04 - Game Theme-B.mp3")


# -----------------------------------------------------------------------------
# 5. DEEP FOREST (20 x 18 tiles)
# -----------------------------------------------------------------------------
def build_deep_forest():
    W, H = 20, 18
    ground = _fill(W, H, "g4")
    solids = _fill(W, H, 0)

    for tx in range(W):
        solids[0][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    # Exits:
    solids[9][0] = 0         # West -> Forest
    solids[H - 1][16] = 0    # Secret south passage -> Grotto

    # Dead trees maze
    big_props = []
    dead_tree_coords = [
        (0, 0), (2, 0), (4, 0), (6, 0), (12, 0), (14, 0), (16, 0), (18, 0),
        (2, 4), (6, 4), (10, 4), (14, 4),
        (4, 8), (8, 8), (12, 8), (16, 8),
        (2, 12), (6, 12), (10, 12), (14, 12),
        (0, 15), (4, 15), (8, 15), (12, 15), (18, 15),
    ]
    for tx, ty in dead_tree_coords:
        big_props.append(("td", tx * 16, ty * 16))
        for dy in range(2):
            for dx in range(2):
                stx, sty = tx + dx, ty + dy
                if 0 <= stx < W and 0 <= sty < H:
                    solids[sty][stx] = 1

    solids[9][0] = 0
    solids[H - 1][16] = 0

    props = [
        ("bo", 3, 9), ("bo", 15, 9), ("bo", 11, 14),
        ("rk", 8, 6), ("rk", 13, 11),
    ]

    items = [
        ItemPickup("glow_herb", 3 * 16, 6 * 16, "herb_glow"),
        ItemPickup("mushroom", 7 * 16, 14 * 16, "deep_mush"),
        ItemPickup("crystal", 17 * 16, 4 * 16, "shadow_crystal"),
    ]

    interactives = [
        InteractiveObject(16 * 16, 16 * 16, 16, 16, [
            "A dark fissure between twisted dead roots leads into an abyssal cavern..."
        ]),
    ]

    warps = [
        WarpDef(0, 9 * 16, 16, 16, "forest", 18 * 16, 9 * 16),
        WarpDef(16 * 16, (H - 1) * 16, 16, 16, "grotto", 10 * 16, 16),
    ]

    return GameMap("deep_forest", W, H, ground, solids, props, big_props,
                   [], warps, items, interactives, music="cag07 - Game Theme-A+B.mp3")


# -----------------------------------------------------------------------------
# 6. WATCHTOWER RUINS (20 x 18 tiles)
# -----------------------------------------------------------------------------
def build_ruins():
    W, H = 20, 18
    ground = _fill(W, H, "g2")
    solids = _fill(W, H, 0)

    for tx in range(W):
        solids[0][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    solids[0][10] = 0  # North exit back to forest

    # Watchtower stone perimeter (x=6..13, y=5..13)
    for ty in range(5, 14):
        for tx in range(6, 14):
            ground[ty][tx] = "p1"
            if ty in (5, 13) or tx in (6, 13):
                solids[ty][tx] = 1

    # Entrance to dungeon inside ruins (door at x=9, y=13)
    solids[13][9] = 0
    solids[13][10] = 0

    # Crypt entrance doorway at back of ruins (x=9..10, y=5)
    solids[5][9] = 0
    solids[5][10] = 0

    props = [
        ("gr", 3, 6), ("gr", 3, 8), ("gr", 3, 10),
        ("gr", 16, 6), ("gr", 16, 8), ("gr", 16, 10),
        ("bo", 8, 7), ("bo", 11, 7), ("bo", 8, 11), ("bo", 11, 11),
        ("rk", 4, 3), ("rk", 15, 3),
    ]

    big_props = [
        ("td", 0, 0), ("td", 18 * 16, 0),
        ("td", 0, 16 * 16), ("td", 18 * 16, 16 * 16),
    ]

    # Ghost NPC inside the ruins
    npcs = [
        NPCDef("ghost", "Phantom Knight", "king.png", 9 * 16, 9 * 16,
               "down", portrait="king", ocean_char_id="actor3_character_01",
               dialogues=[
                   {"text": "Halt, living soul... I was captain of the king's guard.", "portrait": "king"},
                   {"text": "The crypt below holds our armory and our curse.", "portrait": "king"},
                   {"text": "Enter if you have the courage to break the darkness.", "portrait": "king"}
               ]),
    ]

    # Mother's lost ring and map piece in the ruins
    items = [
        ItemPickup("ring", 11 * 16, 9 * 16, "timmy_ring"),
        ItemPickup("map_piece", 8 * 16, 9 * 16, "dungeon_map"),
    ]

    interactives = [
        InteractiveObject(9 * 16, 5 * 16, 2 * 16, 16, [
            "Stone stairway descending into the subterranean dungeon."
        ]),
    ]

    warps = [
        WarpDef(10 * 16, 0, 16, 16, "forest", 10 * 16, (H - 2) * 16),
        WarpDef(9 * 16, 5 * 16, 2 * 16, 16, "dungeon", 8 * 16, 12 * 16),
    ]

    return GameMap("ruins", W, H, ground, solids, props, big_props,
                   npcs, warps, items, interactives, music="stg02 - Game Start.mp3")


# -----------------------------------------------------------------------------
# 7. DUNGEON / UNDERGROUND VAULT (16 x 14 tiles)
# -----------------------------------------------------------------------------
def build_dungeon():
    W, H = 16, 14
    ground = _fill(W, H, "dg_5_2")  # dungeon flagstone floor
    solids = _fill(W, H, 0)

    # Outer dungeon walls
    for tx in range(W):
        solids[0][tx] = 1
        solids[1][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    # North back wall
    for tx in range(1, W - 1):
        ground[0][tx] = "dg_0_2"
        ground[1][tx] = "dg_1_2"

    # Prison cell dividers
    for ty in range(3, 8):
        solids[ty][5] = 1
        solids[ty][10] = 1

    props = [
        ("bo", 3, 5), ("bo", 12, 5), ("bo", 8, 8),
        ("rk", 4, 9), ("rk", 11, 9),
        ("ch", 3, 3), ("ch", 12, 3),
        ("ch", 8, 4),
    ]

    # Dungeon treasure chests: Iron Sword, Shield, Elixir, Gold Coins!
    items = [
        ItemPickup("sword", 3 * 16, 3 * 16, "dungeon_sword"),
        ItemPickup("shield", 12 * 16, 3 * 16, "dungeon_shield"),
        ItemPickup("elixir", 8 * 16, 4 * 16, "dungeon_elixir"),
        ItemPickup("coins", 7 * 16, 8 * 16, "dungeon_coins"),
    ]

    interactives = [
        InteractiveObject(7 * 16, 3 * 16, 2 * 16, 16, [
            "An ancient stone altar glowing faintly.",
            "Inscribed: 'The Shadow King awaits in the deep grotto.'"
        ]),
    ]

    # Stairs back to ruins (south)
    warps = [
        WarpDef(8 * 16, (H - 1) * 16, 16, 16, "ruins", 9 * 16, 6 * 16),
    ]

    return GameMap("dungeon", W, H, ground, solids, props, [],
                   [], warps, items, interactives, music="bpag03 - Game Over.mp3")


# -----------------------------------------------------------------------------
# 8. SHADOW GROTTO (20 x 18 tiles)
# -----------------------------------------------------------------------------
def build_grotto():
    W, H = 20, 18
    ground = _fill(W, H, "g4")
    solids = _fill(W, H, 0)

    for tx in range(W):
        solids[0][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    solids[0][10] = 0  # North exit back to Deep Forest

    # Mysterious columns
    pillars = [(5, 5), (14, 5), (5, 12), (14, 12), (8, 8), (11, 8)]
    for px, py in pillars:
        solids[py][px] = 1

    props = [
        ("rk", 5, 5), ("rk", 14, 5), ("rk", 5, 12), ("rk", 14, 12),
        ("rk", 8, 8), ("rk", 11, 8),
        ("bo", 9, 7), ("bo", 10, 7),
    ]

    # Shadow King Boss NPC
    npcs = [
        NPCDef("shadow", "Shadow King", "king.png", 10 * 16, 5 * 16,
               "down", portrait="king", ocean_char_id="actor3_character_08",
               dialogues=[
                   {"text": "Who disturbs the eternal dusk?", "portrait": "king"},
                   {"text": "I am the shade of King Aldous... bound to this cavern.", "portrait": "king"},
                   {"text": "Use the Shadow Crystal... break the seal and free us all!", "portrait": "king"}
               ]),
    ]

    items = [
        ItemPickup("amulet", 6 * 16, 9 * 16, "sun_amulet"),
    ]

    warps = [
        WarpDef(10 * 16, 0, 16, 16, "deep_forest", 16 * 16, 16 * 16),
    ]

    return GameMap("grotto", W, H, ground, solids, props, [],
                   npcs, warps, items, [], music="stg05 - Game Over.mp3")


# -----------------------------------------------------------------------------
# Master Map Registry
# -----------------------------------------------------------------------------
def build_all_maps():
    return {
        "village":      build_village(),
        "player_house": build_player_house(),
        "elder_house":  build_elder_house(),
        "forest":       build_forest(),
        "deep_forest":  build_deep_forest(),
        "ruins":        build_ruins(),
        "dungeon":      build_dungeon(),
        "grotto":       build_grotto(),
    }
