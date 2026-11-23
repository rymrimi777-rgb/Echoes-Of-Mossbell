"""
World definition – 8 connected maps with interiors, dungeons, animated water & flowers,
integrated 48x48 Game Boy environmental structures (buildings, cottages, towers, fountains),
Free_1.1 decorations (bridges, cave entrances/stairs, lampposts, benches, pickets, tall grass, reeds),
NPCs with animated portraits, interactive furniture, secrets, and SGQ Action-RPG enemies.
Carefully handcrafted, organized, and uncluttered with natural spacing.
"""
from game.map_loader import (GameMap, NPCDef, WarpDef, ItemPickup,
                             InteractiveObject, StructureDef)
from game.monsters import Monster
from game.placement_validator import PlacementValidator


def _fill(w, h, val):
    return [[val] * w for _ in range(h)]


# -----------------------------------------------------------------------------
# 1. MOSSBELL VILLAGE (22 x 18 tiles)
# -----------------------------------------------------------------------------
def build_village():
    W, H = 22, 18
    ground = _fill(W, H, "g0")
    solids = _fill(W, H, 0)

    # Perimeter boundaries
    for tx in range(W):
        solids[0][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    # Main crossroads:
    # East-West thoroughfare (y=9, 10) connecting west farms to east forest exit
    for tx in range(1, W):
        ground[9][tx] = "p1"
        ground[10][tx] = "p1"
    # North-South main avenue (x=10, 11) connecting northern gate to southern park
    for ty in range(1, H - 1):
        ground[ty][10] = "p1"
        ground[ty][11] = "p1"

    # Lane branch up to Player House (x=4) and Elder House (x=16)
    for ty in range(4, 10):
        ground[ty][4] = "p1"
        ground[ty][16] = "p1"

    # Natural grass variations (subtle textures)
    for ty in range(H):
        for tx in range(W):
            if ground[ty][tx] == "g0":
                if (tx * 3 + ty * 7) % 7 == 0:
                    ground[ty][tx] = "g2"
                elif (tx + ty * 5) % 11 == 0:
                    ground[ty][tx] = "g4"

    # Animated Flower garden in southern civic park (x=3..5, y=13..14)
    flower_coords = [(3, 13), (4, 13), (5, 13), (3, 14), (4, 14), (5, 14)]
    for fx, fy in flower_coords:
        ground[fy][fx] = "fl"

    # Village Millpond with Animated Water (south-east: x=16..18, y=13..16)
    for py in range(13, 17):
        for px in range(16, 19):
            ground[py][px] = "wt"
            solids[py][px] = 1

    # Water inlet crossing at north edge of pond (x=16..17, y=12)
    ground[12][16] = "wt"
    ground[12][17] = "wt"
    solids[12][16] = 1
    solids[12][17] = 1
    # Walkable banks connecting the bridge: West landing at (15, 12), East landing at (18, 12)
    ground[12][15] = "p1"
    ground[12][18] = "p1"

    # Doorstep walkability
    solids[4][4] = 0   # Player house doorstep
    solids[4][16] = 0  # Elder house doorstep

    # East exit open to forest
    solids[9][W - 1] = 0
    solids[10][W - 1] = 0

    # North and South avenue endpoints (clear of invisible blockers, framed by landmarks)
    solids[1][10] = 0
    solids[1][11] = 0
    solids[H - 2][10] = 0
    solids[H - 2][11] = 0

    # -------------------------------------------------------------------------
    # Handcrafted, Uncluttered Structure & Decoration Placements
    # -------------------------------------------------------------------------
    structures = [
        # --- NORTHERN RESIDENTIAL SECTOR (y=16) ---
        # 1. Player's Stone Cottage (px=48, py=16) [tiles x=3..5, y=1..3]
        StructureDef("bldg_11", 48, 16, col_boxes=[(4, 20, 14, 24), (30, 20, 14, 24)]),

        # 2. Elder Orin's Archive Residence (px=240, py=16) [tiles x=15..17, y=1..3]
        StructureDef("bldg_06", 240, 16, col_boxes=[(4, 20, 14, 24), (30, 20, 14, 24)]),

        # 3. Northeast Guard Bastion (px=288, py=16) [tiles x=18..20, y=1..3]
        StructureDef("bldg_03", 288, 16, col_boxes=[(12, 24, 24, 22)]),

        # --- WESTERN FARM & MARKET SECTOR (aligned along western lane) ---
        # 4. Village Barn & Stable (px=16, py=72) [tiles x=1..3, y=4.5..7.5]
        StructureDef("bldg_02", 16, 72, col_boxes=[(4, 20, 40, 22)]),

        # 5. Woodcutter's Cart / Shed (px=16, py=128) [tiles x=1..3, y=8..10.5]
        StructureDef("bldg_10", 16, 128, col_boxes=[(12, 18, 24, 20)]),

        # 6. Healer Fern's Fenced Herb Garden (px=16, py=192) [tiles x=1..3, y=12..14.5]
        StructureDef("bldg_01", 16, 192, col_boxes=[(4, 16, 40, 26)]),

        # 7. Martha's Market Stall (px=64, py=80) [tiles x=4..6, y=5..7]
        StructureDef("bldg_07", 64, 80, col_boxes=[(6, 18, 36, 18)]),

        # --- CENTRAL CIVIC PARK (south-west of crossroads, y=12..16) ---
        # 8. Mossbell Village Fountain (px=96, py=192) [tiles x=6..8, y=12..14]
        StructureDef("bldg_04", 96, 192, col_boxes=[(8, 18, 32, 22)]),

        # --- EASTERN RESIDENTIAL & MILLPOND SECTOR ---
        # 9. Stone Well (px=272, py=72) [tiles x=17..19, y=4.5..7]
        StructureDef("bldg_09", 272, 72, col_boxes=[(8, 16, 32, 22)]),

        # 10. Timmy's Small Cottage (px=208, py=72) [tiles x=13..15, y=4.5..7]
        StructureDef("bldg_14", 208, 72, col_boxes=[(6, 22, 36, 22)]),

        # 11. Village Watermill (px=208, py=192) [tiles x=13..15, y=12..14] - wheel turns by pond
        StructureDef("bldg_12", 208, 192, col_boxes=[(4, 18, 40, 26)]),

        # 12. Validated Horizontal Footbridge over pond inlet (px=256, py=192) [tiles x=16..17, y=12]
        StructureDef("bridge_h", 16 * 16, 12 * 16, col_boxes=False, is_ground=True),

        # 13. Weathered Perimeter Stone Wall (px=288, py=128) [tiles x=18..20, y=8..10]
        StructureDef("bldg_05", 288, 128, col_boxes=[(6, 18, 36, 18)]),

        # --- ORGANIZED TREES (clustered with proper spacing, zero overlaps) ---
        StructureDef("tree_02", 0, 0),        # NW corner oak (px=0..48, py=0..48)
        StructureDef("tree_02", 112, 0),      # North avenue oak (px=112..160, py=0..48)
        StructureDef("tree_11", 104, 32),     # Cottage yard blossom tree
        StructureDef("tree_10", 48, 208),     # Grand canopy oak in southern park
        StructureDef("tree_06", 288, 192),    # Weeping willow beside millpond
        StructureDef("tree_08", 0, 144),      # Twin oaks along western boundary

        # --- LOGICAL DECORATIONS (comfortably spaced, non-cluttered) ---
        # Lampposts along the street junctions
        StructureDef("lampost", 144, 48),     # Framing north gate avenue
        StructureDef("lampost", 144, 128),    # Central crossroads lamp
        StructureDef("lampost", 208, 128),    # East residential lane lamp
        # Benches for resting
        StructureDef("bench_h", 112, 244),    # Park bench south of fountain
        StructureDef("bench_h", 48, 128),     # Plaza bench near market
        # Picket fence neatly framing player cottage
        StructureDef("fence_picket", 16, 16),
        # Natural reeds along pond edge
        StructureDef("reeds", 15 * 16, 13 * 16, is_ground=True),
        StructureDef("reeds", 19 * 16, 15 * 16, is_ground=True),
    ]

    # Validate bridge placement
    v_ok, _ = PlacementValidator.validate_bridge(W, H, ground, solids, 16, 12, "horizontal")
    if not v_ok:
        solids[12][16] = 0
        solids[12][17] = 0

    # Minimal, well-placed environmental props (no collision clutter)
    props = [
        ("bu", 7, 3), ("bu", 13, 3),
        ("rk", 14, 16), ("rk", 19, 13),
        ("st", 9, 6),
    ]

    # Interactive Village Objects (all placed with clear player access)
    interactives = [
        InteractiveObject(4 * 16, 4 * 16, 16, 8, [
            "Your home. A cozy stone cottage."
        ]),
        InteractiveObject(16 * 16, 4 * 16, 16, 8, [
            "Elder Orin's residence and village archive."
        ]),
        InteractiveObject(10 * 16, 7 * 16, 16, 16, [
            "Village Notice Board:",
            "'Beware of Whispering Woods after dusk.'",
            "'Report any strange sightings to Elder Orin.'"
        ]),
        InteractiveObject(6 * 16, 12 * 16, 16, 16, [
            "Mossbell Village Fountain:",
            "Pure mountain spring water ripples gently in the stone basin."
        ]),
        InteractiveObject(17 * 16 + 8, 5 * 16, 16, 16, [
            "The Village Well:",
            "Deep, crystal-clear water drawn from beneath the old moss."
        ]),
        InteractiveObject(5 * 16, 5 * 16 + 8, 16, 16, [
            "Market Stall:",
            "Fresh forest apples, hearth loaves, and travelers' supplies."
        ]),
        InteractiveObject(10 * 16, 1 * 16, 2 * 16, 16, [
            "Northern Mountain Gate:",
            "'Dragon's Ridge Pass - Closed by decree of Elder Orin.'"
        ]),
    ]

    # NPCs (positioned cleanly in open walkable spaces)
    npcs = [
        NPCDef("elder", "Elder Orin", "old_man.png", 16 * 16, 6 * 16,
               "down", portrait="old_man", ocean_char_id="actor1_character_05",
               dialogues=[
                   {"text": "Welcome, young one. A heavy shadow has fallen over Mossbell.", "portrait": "old_man"},
                   {"text": "Three villagers have vanished into Whispering Woods.", "portrait": "old_man"},
                   {"text": "Please search the woods east of the village and uncover the truth.", "portrait": "old_man"}
               ]),
        NPCDef("healer", "Healer Fern", "king.png", 5 * 16, 13 * 16,
               "right", portrait="king", ocean_char_id="actor1_character_03",
               dialogues=[
                   {"text": "Greetings, traveler. I tend to the ailing of our village.", "portrait": "king"},
                   {"text": "My medicine chest is nearly bare. If you find Forest Herbs, bring them to me.", "portrait": "king"}
               ]),
        NPCDef("boy", "Timmy", "boy.png", 13 * 16, 6 * 16,
               "down", portrait="boy", ocean_char_id="actor1_character_02",
               dialogues=[
                   {"text": "I lost my mother's silver ring near the old watchtower ruins...", "portrait": "boy"},
                   {"text": "She went missing last full moon... I hope she is still safe.", "portrait": "boy"}
               ]),
        NPCDef("villager1", "Martha", "old_man.png", 5 * 16, 6 * 16,
               "right", portrait="old_man", ocean_char_id="actor2_character_03",
               dialogues=[
                   {"text": "The wind carries strange whispers at night.", "portrait": "old_man"},
                   {"text": "Lock your door tight before sunset!", "portrait": "old_man"}
               ]),
    ]

    # Warps
    warps = [
        WarpDef(4 * 16, 3 * 16 + 8, 16, 12, "player_house", 5 * 16, 8 * 16),
        WarpDef(16 * 16, 3 * 16 + 8, 16, 12, "elder_house", 5 * 16, 8 * 16),
        WarpDef((W - 1) * 16, 9 * 16, 16, 2 * 16, "forest", 16, 9 * 16),
    ]

    items = []

    return GameMap("village", W, H, ground, solids, props, [],
                   npcs, warps, items, interactives, music="bpag02 - Game Theme.mp3",
                   structures=structures)


# -----------------------------------------------------------------------------
# 2. PLAYER HOUSE INTERIOR (12 x 10 tiles)
# -----------------------------------------------------------------------------
def build_player_house():
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

    for rx in range(4, 8):
        for ry in range(4, 7):
            ground[ry][rx] = "p1"

    props = [
        ("in_2_1", 2, 2), ("in_2_2", 3, 2),
        ("in_0_4", 8, 2), ("in_1_4", 8, 3),
        ("in_0_6", 5, 1), ("in_1_6", 5, 2),
        ("in_4_3", 5, 5), ("in_4_4", 6, 5),
        ("ch", 10, 2),
    ]

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

    items = [
        ItemPickup("apple", 10 * 16, 2 * 16, "house_apple"),
    ]

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
        ("in_0_4", 2, 2), ("in_1_4", 2, 3),
        ("in_0_4", 3, 2), ("in_1_4", 3, 3),
        ("in_0_4", 8, 2), ("in_1_4", 8, 3),
        ("in_0_4", 9, 2), ("in_1_4", 9, 3),
        ("in_4_3", 5, 4), ("in_4_4", 6, 4),
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

    # Winding paths:
    # East-West trail (y=9)
    for tx in range(W):
        ground[9][tx] = "p1"
    # South path to Ruins (x=10, y=9..17)
    for ty in range(9, 18):
        ground[ty][10] = "p1"

    # Grass variants
    for ty in range(H):
        for tx in range(W):
            if ground[ty][tx] == "g0":
                if (tx * 7 + ty * 3) % 5 == 0:
                    ground[ty][tx] = "g2"
                elif (tx + ty * 4) % 9 == 0:
                    ground[ty][tx] = "g4"

    # Flower patches in natural clearings
    for fx, fy in [(4, 5), (5, 5), (14, 5), (5, 13)]:
        ground[fy][fx] = "fl"

    # Forest brook with animated water on east side (x=15..16, y=2..15)
    for sy in range(2, 16):
        ground[sy][15] = "wt"
        ground[sy][16] = "wt"
        solids[sy][15] = 1
        solids[sy][16] = 1

    # Bridge crossing brook at y=9
    ground[9][14] = "p1"
    ground[9][17] = "p1"

    # Exits:
    solids[9][0] = 0         # West -> Village
    solids[9][W - 1] = 0     # East -> Deep Forest
    solids[H - 1][10] = 0    # South -> Ruins

    # Validate bridge placement
    v_ok, _ = PlacementValidator.validate_bridge(W, H, ground, solids, 15, 9, "horizontal")
    if not v_ok:
        solids[9][15] = 0
        solids[9][16] = 0

    # -------------------------------------------------------------------------
    # Natural Forest Tree Clusters (spaced gracefully, zero overlaps)
    # -------------------------------------------------------------------------
    structures = [
        # 1. Validated horizontal footbridge across the brook
        StructureDef("bridge_h", 15 * 16, 9 * 16, col_boxes=False, is_ground=True),

        # 2. Woodsman's Camp Cart (px=80, py=64) [tiles x=5..7, y=4..6]
        StructureDef("bldg_10", 80, 64, col_boxes=[(12, 18, 24, 20)]),

        # 3. Ancient Overgrown Wall segment (px=192, py=208) [tiles x=12..14, y=13..15]
        StructureDef("bldg_05", 192, 208, col_boxes=[(6, 18, 36, 18)]),

        # --- NORTH-WEST CANOPY CLUSTER (x=1..8, y=1..4) ---
        StructureDef("tree_02", 16, 16),      # Lush round oak (px=16..64, py=16..64)
        StructureDef("tree_10", 80, 16),      # Grand canopy oak (px=80..128, py=16..64)
        StructureDef("tree_08", 48, 64),      # Twin trees creating depth

        # --- NORTH-EAST WOODS CLUSTER (x=11..14, y=1..4) ---
        StructureDef("tree_04", 176, 16),     # Twisted oak
        StructureDef("tree_06", 240, 16),     # Willow by brook (px=240..288, py=16..64)
        StructureDef("tree_12", 272, 32),     # Alpine pine east of brook

        # --- SOUTH-WEST DENSE WOODS (x=1..7, y=11..16) ---
        StructureDef("tree_09", 16, 192),     # Dense bush tree
        StructureDef("tree_12", 64, 192),     # Border pine
        StructureDef("tree_08", 32, 144),     # Twin trees near clearing

        # --- SOUTH-EAST WATER WILLOWS (x=13..15, y=12..16) ---
        StructureDef("tree_06", 240, 192),    # Willow along stream
        StructureDef("tree_03", 272, 176),    # Weeping vines east bank

        # --- NATURAL DECORATIONS (comfortably placed, clear pathways) ---
        StructureDef("pine_tall", 288, 80),   # Tall pine along eastern path
        StructureDef("reeds", 14 * 16, 4 * 16, is_ground=True),
        StructureDef("reeds", 14 * 16, 13 * 16, is_ground=True),
        StructureDef("reeds", 17 * 16, 5 * 16, is_ground=True),
        StructureDef("tall_grass", 3 * 16, 12 * 16, is_ground=True),
        StructureDef("tall_grass", 12 * 16, 4 * 16, is_ground=True),
    ]

    # Props
    props = [
        ("bu", 8, 7), ("bu", 12, 7),
        ("rk", 9, 6), ("rk", 12, 13),
        ("st", 11, 8),
    ]

    # Old Woodsman NPC by his campfire
    npcs = [
        NPCDef("woodsman", "Old Woodsman", "old_man.png", 6 * 16, 6 * 16,
               "down", portrait="old_man", ocean_char_id="actor2_character_01",
               dialogues=[
                   {"text": "Beware... deep in the forest, the shadows take physical form.", "portrait": "old_man"},
                   {"text": "I heard an unearthly wail from the watchtower to the south.", "portrait": "old_man"}
               ]),
    ]

    interactives = [
        InteractiveObject(9 * 16, 11 * 16, 16, 16, [
            "Signpost: 'South -> Watchtower Ruins. East -> Deep Woods (Dangerous).'"
        ]),
    ]

    items = [
        ItemPickup("herb", 4 * 16, 6 * 16, "herb_1"),
        ItemPickup("herb", 14 * 16, 6 * 16, "herb_2"),
        ItemPickup("herb", 6 * 16, 14 * 16, "herb_3"),
    ]

    # SGQ Enemies (preserved exactly as defined)
    enemies = [
        Monster("slime", 5 * 16, 12 * 16, patrol_radius=32),
        Monster("slime", 13 * 16, 6 * 16, patrol_radius=24),
        Monster("slime", 12 * 16, 14 * 16, patrol_radius=32),
        Monster("rat", 7 * 16, 4 * 16, patrol_radius=40),
        Monster("goblin", 17 * 16, 12 * 16, patrol_radius=30),
    ]

    warps = [
        WarpDef(0, 9 * 16, 16, 16, "village", 20 * 16, 9 * 16),
        WarpDef((W - 1) * 16, 9 * 16, 16, 16, "deep_forest", 16, 9 * 16),
        WarpDef(10 * 16, (H - 1) * 16, 16, 16, "ruins", 10 * 16, 16),
    ]

    return GameMap("forest", W, H, ground, solids, props, [],
                   npcs, warps, items, interactives, music="cag04 - Game Theme-B.mp3",
                   structures=structures, enemies=enemies)


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
    solids[14][16] = 0       # South-east passage inside cave entrance
    solids[15][16] = 0

    # -------------------------------------------------------------------------
    # Natural Dark Forest Clusters & Landmarks
    # -------------------------------------------------------------------------
    structures = [
        # 1. Mystical Mushroom Tower in northeast clearing (px=224, py=16) [tiles x=14..16, y=1..3]
        StructureDef("bldg_08", 224, 16, col_boxes=[(14, 28, 20, 18)]),

        # 2. Sunken Overgrown Ruin Wall (px=80, py=112) [tiles x=5..7, y=7..9]
        StructureDef("bldg_05", 80, 112, col_boxes=[(6, 18, 36, 18)]),

        # 3. Cave Entrance leading down into the Shadow Grotto (px=240, py=224)
        StructureDef("cave_entrance", 240, 224),

        # --- DEAD & GNARLED FOREST CANOPY (clean spacing, zero overlaps) ---
        StructureDef("tree_01", 16, 16),      # NW dead hanging tree
        StructureDef("tree_05", 96, 16),      # Ancient twisted tree
        StructureDef("tree_07", 160, 16),     # Dead branch tree
        StructureDef("tree_03", 16, 144),     # Weeping vines on west border
        StructureDef("tree_04", 144, 96),     # Twisted oak in central grove
        StructureDef("tree_01", 32, 208),     # SW dead hanging tree
        StructureDef("tree_05", 144, 192),    # Ancient twisted tree south
        StructureDef("tree_07", 256, 128),    # East border dead tree

        # --- ATMOSPHERIC DECORATIONS ---
        StructureDef("cave_boulder", 48, 80),
        StructureDef("cave_boulder", 192, 144),
        StructureDef("tall_grass", 7 * 16, 4 * 16, is_ground=True),
        StructureDef("tall_grass", 11 * 16, 14 * 16, is_ground=True),
    ]

    props = [
        ("bo", 3, 9), ("bo", 15, 9),
        ("rk", 8, 6), ("rk", 13, 11),
    ]

    items = [
        ItemPickup("glow_herb", 3 * 16, 6 * 16, "herb_glow"),
        ItemPickup("mushroom", 7 * 16, 14 * 16, "deep_mush"),
        ItemPickup("crystal", 17 * 16, 4 * 16, "shadow_crystal"),
    ]

    interactives = [
        InteractiveObject(15 * 16, 14 * 16, 2 * 16, 16, [
            "A dark cavern mouth leads down into the subterranean Shadow Grotto..."
        ]),
    ]

    # SGQ Enemies (preserved exactly as defined)
    enemies = [
        Monster("spider", 5 * 16, 7 * 16, patrol_radius=36),
        Monster("spider", 12 * 16, 8 * 16, patrol_radius=30),
        Monster("bat", 9 * 16, 12 * 16, patrol_radius=45),
        Monster("bat", 4 * 16, 14 * 16, patrol_radius=45),
        Monster("cube_slime", 16 * 16, 6 * 16, patrol_radius=28),
    ]

    warps = [
        WarpDef(0, 9 * 16, 16, 16, "forest", 18 * 16, 9 * 16),
        WarpDef(16 * 16, 15 * 16, 16, 16, "grotto", 10 * 16, 2 * 16),
    ]

    return GameMap("deep_forest", W, H, ground, solids, props, [],
                   [], warps, items, interactives, music="cag07 - Game Theme-A+B.mp3",
                   structures=structures, enemies=enemies)


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

    # Crypt stairway at back of ruins (x=9..10, y=5)
    solids[5][9] = 0
    solids[5][10] = 0

    structures = [
        # 1. The Great Stone Watchtower (px=128, py=16) [tiles x=8..10, y=1..3]
        StructureDef("bldg_03", 128, 16, col_boxes=[(12, 24, 24, 22)]),

        # 2. Ruined fortress rampart walls
        StructureDef("bldg_05", 32, 96, col_boxes=[(6, 18, 36, 18)]),
        StructureDef("bldg_05", 224, 96, col_boxes=[(6, 18, 36, 18)]),

        # 3. Cave stairs descending into dungeon (px=144, py=80) [tile 9, y=5]
        StructureDef("cave_stairs_down", 9 * 16, 5 * 16, is_ground=True),

        # 4. Courtyard boulders and tall grass
        StructureDef("tall_grass", 7 * 16, 8 * 16, is_ground=True),
        StructureDef("tall_grass", 12 * 16, 8 * 16, is_ground=True),
        StructureDef("cave_boulder", 4 * 16, 11 * 16),
        StructureDef("cave_boulder", 15 * 16, 11 * 16),

        # 5. Fortress perimeter alpine trees (spaced around walls)
        StructureDef("tree_07", 0, 0),
        StructureDef("tree_07", 256, 0),
        StructureDef("tree_01", 0, 208),
        StructureDef("tree_01", 256, 208),
        StructureDef("tree_12", 48, 16),
        StructureDef("tree_12", 208, 16),
    ]

    props = [
        ("gr", 3, 6), ("gr", 3, 8),
        ("gr", 16, 6), ("gr", 16, 8),
        ("bo", 8, 7), ("bo", 11, 7),
        ("rk", 4, 3), ("rk", 15, 3),
    ]

    npcs = [
        NPCDef("ghost", "Phantom Knight", "king.png", 9 * 16, 9 * 16,
               "down", portrait="king", ocean_char_id="actor3_character_01",
               dialogues=[
                   {"text": "Halt, living soul... I was captain of the king's guard.", "portrait": "king"},
                   {"text": "The crypt below holds our armory and our curse.", "portrait": "king"},
                   {"text": "Enter if you have the courage to break the darkness.", "portrait": "king"}
               ]),
    ]

    items = [
        ItemPickup("ring", 11 * 16, 9 * 16, "timmy_ring"),
        ItemPickup("map_piece", 8 * 16, 9 * 16, "dungeon_map"),
    ]

    interactives = [
        InteractiveObject(9 * 16, 5 * 16, 2 * 16, 16, [
            "Stone stairway descending into the subterranean dungeon."
        ]),
    ]

    # SGQ Enemies (preserved exactly as defined)
    enemies = [
        Monster("skeleton", 7 * 16, 11 * 16, patrol_radius=25),
        Monster("skeleton", 12 * 16, 11 * 16, patrol_radius=25),
        Monster("ghost", 4 * 16, 9 * 16, patrol_radius=35),
    ]

    warps = [
        WarpDef(10 * 16, 0, 16, 16, "forest", 10 * 16, (H - 2) * 16),
        WarpDef(9 * 16, 5 * 16, 2 * 16, 16, "dungeon", 8 * 16, 11 * 16),
    ]

    return GameMap("ruins", W, H, ground, solids, props, [],
                   npcs, warps, items, interactives, music="stg02 - Game Start.mp3",
                   structures=structures, enemies=enemies)


# -----------------------------------------------------------------------------
# 7. DUNGEON / UNDERGROUND VAULT (16 x 14 tiles)
# -----------------------------------------------------------------------------
def build_dungeon():
    W, H = 16, 14
    ground = _fill(W, H, "dg_5_2")
    solids = _fill(W, H, 0)

    for tx in range(W):
        solids[0][tx] = 1
        solids[1][tx] = 1
        solids[H - 1][tx] = 1
    for ty in range(H):
        solids[ty][0] = 1
        solids[ty][W - 1] = 1

    for tx in range(1, W - 1):
        ground[0][tx] = "dg_0_2"
        ground[1][tx] = "dg_1_2"

    # Prison cell dividers
    for ty in range(3, 8):
        solids[ty][5] = 1
        solids[ty][10] = 1

    # Stairs up to ruins at south (x=8, y=12)
    solids[12][8] = 0

    # Secret east passage to Grotto at (x=W-2, y=5)
    solids[5][W - 1] = 0

    structures = [
        # Cave stairs leading up back to the ruins
        StructureDef("cave_stairs_up", 8 * 16, 12 * 16, is_ground=True),

        # Cave exit fissure on east wall opening to Shadow Grotto
        StructureDef("cave_exit", 13 * 16, 5 * 16),

        # Boulders inside corner cells
        StructureDef("cave_boulder", 2 * 16, 7 * 16),
        StructureDef("cave_boulder", 13 * 16, 7 * 16),
    ]

    props = [
        ("bo", 3, 5), ("bo", 12, 5),
        ("rk", 4, 9), ("rk", 11, 9),
        ("ch", 3, 3), ("ch", 12, 3),
        ("ch", 8, 4),
    ]

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
        InteractiveObject(13 * 16, 5 * 16, 2 * 16, 16, [
            "A cracked stone fissure opens into a subterranean cave channel..."
        ]),
    ]

    # SGQ Enemies (preserved exactly as defined)
    enemies = [
        Monster("flying_skull", 5 * 16, 6 * 16, patrol_radius=30),
        Monster("flying_skull", 10 * 16, 6 * 16, patrol_radius=30),
        Monster("rat", 8 * 16, 9 * 16, patrol_radius=25),
        Monster("medium_slime", 7 * 16, 5 * 16, patrol_radius=20),
    ]

    warps = [
        WarpDef(8 * 16, 12 * 16, 16, 16, "ruins", 9 * 16, 6 * 16),
        WarpDef((W - 1) * 16, 5 * 16, 16, 16, "grotto", 2 * 16, 9 * 16),
    ]

    return GameMap("dungeon", W, H, ground, solids, props, [],
                   [], warps, items, interactives, music="bpag03 - Game Over.mp3",
                   structures=structures, enemies=enemies)


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

    # North exit to Deep Forest (x=10, y=0..1)
    solids[0][10] = 0
    solids[1][10] = 0

    # West passage back to Dungeon (x=0, y=9)
    solids[9][0] = 0

    # Underground cavern lake on west side (x=3..5, y=11..14)
    for ly in range(11, 15):
        for lx in range(3, 6):
            ground[ly][lx] = "wt"
            solids[ly][lx] = 1

    # Stepping stone across pool
    ground[13][4] = "wt"

    # Stone pillars
    pillars = [(5, 5), (14, 5), (14, 12), (8, 8), (11, 8)]
    for px, py in pillars:
        solids[py][px] = 1

    structures = [
        # Petrified underground roots framing cavern perimeter
        StructureDef("tree_05", 16, 16),
        StructureDef("tree_05", 256, 16),
        StructureDef("tree_05", 16, 208),
        StructureDef("tree_05", 256, 208),
        StructureDef("tree_07", 112, 16),

        # Cavern decorations
        StructureDef("cave_stairs_up", 10 * 16, 1 * 16, is_ground=True),
        StructureDef("cave_exit", 1 * 16, 9 * 16),
        StructureDef("rock_water_big", 3 * 16, 11 * 16),
        StructureDef("stepping_stones", 4 * 16, 13 * 16, is_ground=True),
        StructureDef("cave_boulder", 6 * 16, 12 * 16),
        StructureDef("cave_boulder", 13 * 16, 6 * 16),
    ]

    props = [
        ("rk", 5, 5), ("rk", 14, 5), ("rk", 14, 12),
        ("rk", 8, 8), ("rk", 11, 8),
        ("bo", 9, 7), ("bo", 10, 7),
    ]

    npcs = [
        NPCDef("shadow", "Shadow King", "king.png", 10 * 16, 4 * 16,
               "down", portrait="king", ocean_char_id="actor3_character_08",
               dialogues=[
                   {"text": "Who disturbs the eternal dusk?", "portrait": "king"},
                   {"text": "I am the shade of King Aldous... bound to this cavern.", "portrait": "king"},
                   {"text": "Vanquish the Slime Sovereign and break the ancient curse!", "portrait": "king"}
               ]),
    ]

    items = [
        ItemPickup("amulet", 6 * 16, 9 * 16, "sun_amulet"),
    ]

    # Boss encounter: Slime Sovereign + Guardian Bats (preserved exactly as defined)
    enemies = [
        Monster("slime_king", 8 * 16, 6 * 16, patrol_radius=50),
        Monster("bat", 5 * 16, 4 * 16, patrol_radius=40),
        Monster("bat", 14 * 16, 4 * 16, patrol_radius=40),
    ]

    warps = [
        WarpDef(10 * 16, 0, 16, 16, "deep_forest", 15 * 16, 15 * 16),
        WarpDef(0, 9 * 16, 16, 16, "dungeon", 14 * 16, 5 * 16),
    ]

    return GameMap("grotto", W, H, ground, solids, props, [],
                   npcs, warps, items, [], music="stg05 - Game Over.mp3",
                   structures=structures, enemies=enemies)


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
