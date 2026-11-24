"""
Character Registry & Metadata System
Defines all 8 playable characters, their stable IDs, portraits, class titles,
and matching Ocean Nostalgia Game Boy walking sprites.
Prepares the architecture for local persistence and future multiplayer.
"""
import os
import pygame
from game.settings import BASE_DIR, ASSET_DIR, COLOR_LIGHT, COLOR_DARKEST

# 8 Playable Characters from Actor 1 (Ralph, Ulrika, Bennett, Yva, Lawrence, Natasha, Rick, Isabelle)
PLAYABLE_CHARACTERS = [
    {
        "id": "actor1_character_01",
        "name": "Ralph",
        "class_name": "Swordsman",
        "title": "Blade Knight",
        "portrait_file": "character_01.png",
        "sprite_id": "actor1_character_01",
        "variant": "gameboy",
        "description": "Courageous blade fighter of Mossbell.",
        "stats": "HP: 20 | ATK: Balanced",
    },
    {
        "id": "actor1_character_02",
        "name": "Ulrika",
        "class_name": "Mage",
        "title": "Mystic Adept",
        "portrait_file": "character_02.png",
        "sprite_id": "actor1_character_02",
        "variant": "gameboy",
        "description": "Clever elemental mystic with keen insight.",
        "stats": "HP: 20 | ATK: Arcane",
    },
    {
        "id": "actor1_character_03",
        "name": "Bennett",
        "class_name": "Fighter",
        "title": "Martial Monk",
        "portrait_file": "character_03.png",
        "sprite_id": "actor1_character_03",
        "variant": "gameboy",
        "description": "Fierce martial brawler seasoned by battle.",
        "stats": "HP: 20 | ATK: Unarmed",
    },
    {
        "id": "actor1_character_04",
        "name": "Yva",
        "class_name": "Cleric",
        "title": "Holy Priestess",
        "portrait_file": "character_04.png",
        "sprite_id": "actor1_character_04",
        "variant": "gameboy",
        "description": "Devoted sanctuary healer bearing sacred light.",
        "stats": "HP: 20 | ATK: Holy",
    },
    {
        "id": "actor1_character_05",
        "name": "Lawrence",
        "class_name": "Paladin",
        "title": "Royal Sentinel",
        "portrait_file": "character_05.png",
        "sprite_id": "actor1_character_05",
        "variant": "gameboy",
        "description": "Stalwart shieldbearer defending the realm.",
        "stats": "HP: 20 | ATK: Defend",
    },
    {
        "id": "actor1_character_06",
        "name": "Natasha",
        "class_name": "Rogue",
        "title": "Shadow Scout",
        "portrait_file": "character_06.png",
        "sprite_id": "actor1_character_06",
        "variant": "gameboy",
        "description": "Swift shadow tracker navigating the dark.",
        "stats": "HP: 20 | ATK: Agility",
    },
    {
        "id": "actor1_character_07",
        "name": "Rick",
        "class_name": "Ranger",
        "title": "Forest Archer",
        "portrait_file": "character_07.png",
        "sprite_id": "actor1_character_07",
        "variant": "gameboy",
        "description": "Keen-eyed hunter roaming the deep canopy.",
        "stats": "HP: 20 | ATK: Ranged",
    },
    {
        "id": "actor1_character_08",
        "name": "Isabelle",
        "class_name": "Witch",
        "title": "Moon Sorceress",
        "portrait_file": "character_08.png",
        "sprite_id": "actor1_character_08",
        "variant": "gameboy",
        "description": "Enigmatic spellweaver steeped in ancient lore.",
        "stats": "HP: 20 | ATK: Occult",
    },
]

CHARACTERS_BY_ID = {c["id"]: c for c in PLAYABLE_CHARACTERS}
DEFAULT_CHARACTER_ID = "actor1_character_01"

_PORTRAIT_CACHE = {}


def get_default_character_id():
    return DEFAULT_CHARACTER_ID


def get_all_characters():
    return list(PLAYABLE_CHARACTERS)


def get_character(character_id):
    if character_id in CHARACTERS_BY_ID:
        return CHARACTERS_BY_ID[character_id]
    return CHARACTERS_BY_ID[DEFAULT_CHARACTER_ID]


def _find_portrait_path(filename):
    """Searches across multiple standard directories for portrait files."""
    candidates = [
        os.path.join(ASSET_DIR, "characters", "portraits", filename),
        os.path.join(BASE_DIR, "Echoes_Of_Mossbell_Individual_Characters", filename),
        os.path.join(BASE_DIR, "_internal", "Echoes_Of_Mossbell_Individual_Characters", filename),
        os.path.join(BASE_DIR, "_internal", "assets", "characters", "portraits", filename),
        os.path.join(ASSET_DIR, "portraits", filename),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def load_portrait(char_or_id, size=None):
    """
    Loads and caches a character portrait Surface.
    size: optional (w, h) tuple for nearest-neighbor scaling.
    """
    if isinstance(char_or_id, dict):
        char_def = char_or_id
    else:
        char_def = get_character(char_or_id)

    filename = char_def.get("portrait_file", "character_01.png")
    cache_key = (filename, size)

    if cache_key in _PORTRAIT_CACHE:
        return _PORTRAIT_CACHE[cache_key]

    path = _find_portrait_path(filename)
    if path and os.path.isfile(path):
        try:
            img = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                img = img.convert_alpha()
            if size is not None and img.get_size() != size:
                img = pygame.transform.scale(img, size)
            _PORTRAIT_CACHE[cache_key] = img
            return img
        except Exception:
            pass

    # Fallback placeholder if file not found
    fallback_w, fallback_h = size if size else (32, 32)
    fb = pygame.Surface((fallback_w, fallback_h), pygame.SRCALPHA)
    fb.fill(COLOR_LIGHT)
    pygame.draw.rect(fb, COLOR_DARKEST, (0, 0, fallback_w, fallback_h), 1)
    _PORTRAIT_CACHE[cache_key] = fb
    return fb
