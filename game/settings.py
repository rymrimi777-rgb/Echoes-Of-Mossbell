"""
Global settings for the retro RPG game.
Configured for maximum keyboard compatibility (AZERTY + QWERTY + Arrow keys).
"""
import os, sys, pygame

# ---------- paths ----------------------------------------------------------
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(sys.executable)
    meipass = getattr(sys, "_MEIPASS", exe_dir)
    if os.path.exists(os.path.join(meipass, "assets")):
        BASE_DIR = meipass
    elif os.path.exists(os.path.join(exe_dir, "assets")):
        BASE_DIR = exe_dir
    else:
        BASE_DIR = exe_dir
    SAVE_DIR = os.path.join(exe_dir, "saves")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SAVE_DIR = os.path.join(BASE_DIR, "saves")

ASSET_DIR   = os.path.join(BASE_DIR, "assets")
SPRITE_DIR  = os.path.join(ASSET_DIR, "sprites")
TILE_DIR    = os.path.join(ASSET_DIR, "tilesets")
ITEM_DIR    = os.path.join(ASSET_DIR, "items")
AUDIO_DIR   = os.path.join(ASSET_DIR, "audio")
MUSIC_DIR   = os.path.join(AUDIO_DIR, "music")
SFX_DIR     = os.path.join(AUDIO_DIR, "sfx")
AUDIO_PLAYER_DIR = os.path.join(AUDIO_DIR, "player")
AUDIO_NPC_DIR    = os.path.join(AUDIO_DIR, "npc")
AUDIO_ENV_DIR    = os.path.join(AUDIO_DIR, "environment")
AUDIO_COMBAT_DIR = os.path.join(AUDIO_DIR, "combat")
AUDIO_UI_DIR     = os.path.join(AUDIO_DIR, "ui")
AUDIO_ITEMS_DIR  = os.path.join(AUDIO_DIR, "items")
MAP_DIR     = os.path.join(ASSET_DIR, "maps")
FONT_DIR    = os.path.join(ASSET_DIR, "fonts")
UI_DIR      = os.path.join(ASSET_DIR, "ui")
BUTTON_DIR  = os.path.join(UI_DIR, "buttons")
if not os.path.isdir(BUTTON_DIR):
    _alt_btn = os.path.join(BASE_DIR, "GameBoy_Touch_Controls_Split", "assets", "buttons")
    if os.path.isdir(_alt_btn):
        BUTTON_DIR = _alt_btn
OCEAN_DIR   = os.path.join(BASE_DIR, "Ocean_Nostalgia_Pygame_Ready")
if not os.path.isdir(OCEAN_DIR):
    _alt = os.path.join(ASSET_DIR, "Ocean_Nostalgia_Pygame_Ready")
    if os.path.isdir(_alt):
        OCEAN_DIR = _alt
OCEAN_CHAR_DIR = os.path.join(OCEAN_DIR, "characters")

# ---------- display --------------------------------------------------------
GAME_W, GAME_H = 160, 144          # native Game Boy resolution
SCALE          = 4                  # window = 640 x 576
WINDOW_W       = GAME_W * SCALE
WINDOW_H       = GAME_H * SCALE
FPS            = 60
TILE_SIZE      = 16

# ---------- Game Boy 4-shade palette ---------------------------------------
PALETTE = [
    (15,  56,  15),    # darkest  – shade 1
    (48,  98,  48),    # dark     – shade 2
    (139, 172, 15),    # light    – shade 3
    (155, 188, 15),    # lightest – shade 4
]
COLOR_DARKEST  = PALETTE[0]
COLOR_DARK     = PALETTE[1]
COLOR_LIGHT    = PALETTE[2]
COLOR_LIGHTEST = PALETTE[3]

# ---------- gameplay speeds ------------------------------------------------
PLAYER_WALK_SPEED = 1.5     # pixels per frame (smooth & responsive)
PLAYER_RUN_SPEED  = 2.2     # holding Shift / Run key
WALK_ANIM_SPEED   = 100     # ms per walk frame
IDLE_ANIM_SPEED   = 250     # ms per idle frame
INTERACT_RANGE    = 22      # pixels (generous hitbox)

# ---------- universal controls (QWERTY + AZERTY + Arrows) -----------------
# Movement: Arrows, WASD (QWERTY), ZQSD (AZERTY)
KEYS_UP        = (pygame.K_UP, pygame.K_w, pygame.K_z)
KEYS_DOWN      = (pygame.K_DOWN, pygame.K_s)
KEYS_LEFT      = (pygame.K_LEFT, pygame.K_a, pygame.K_q)
KEYS_RIGHT     = (pygame.K_RIGHT, pygame.K_d)

# Interaction: Spacebar (Universal!), Enter, E, J, C, and also Z & A
KEYS_INTERACT  = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e,
                  pygame.K_j, pygame.K_c, pygame.K_z, pygame.K_a)

# Cancel / Back
KEYS_CANCEL    = (pygame.K_x, pygame.K_k, pygame.K_ESCAPE, pygame.K_BACKSPACE)

# Confirm in menus
KEYS_CONFIRM   = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e, pygame.K_j)

# Run / Dash (hold to sprint)
KEYS_RUN       = (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_x)

# Inventory Toggle
KEYS_INVENTORY = (pygame.K_i, pygame.K_b)

# Pause
KEYS_PAUSE     = (pygame.K_ESCAPE, pygame.K_p, pygame.K_TAB)

# Android / Mobile platform flag
IS_ANDROID     = hasattr(pygame, "android") or ("ANDROID_ROOT" in os.environ) or ("ANDROID_ARGUMENT" in os.environ)
