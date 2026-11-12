"""
Typography system for Echoes of Mossbell.
Consistent retro pixel-art fonts:
- Press Start 2P: Titles, headers, buttons, and status indicators.
- Pixel Operator: Dialogue, readable body text, and descriptions.
Stored locally in assets/fonts/ for 100% offline gameplay.
"""
import os, pygame
from game.settings import FONT_DIR

_fonts = {}

def get_font_path(filename):
    return os.path.join(FONT_DIR, filename)

def load_font(filename, size):
    """Load a TrueType font with caching, falling back to pygame default if unavailable."""
    key = (filename, size)
    if key in _fonts:
        return _fonts[key]

    path = get_font_path(filename)
    if os.path.isfile(path):
        try:
            font = pygame.font.Font(path, size)
            _fonts[key] = font
            return font
        except Exception:
            pass

    font = pygame.font.Font(None, size)
    _fonts[key] = font
    return font

# ---- Standard Typography Scale ---------------------------------------------
# Headings & Titles (Press Start 2P)
def font_title():
    """Main menu game title (Press Start 2P, 10px)."""
    return load_font("PressStart2P-Regular.ttf", 10)

def font_heading():
    """Section banners, menu headers, dialog speaker (Press Start 2P, 8px)."""
    return load_font("PressStart2P-Regular.ttf", 8)

def font_subheading():
    """Menu options, inventory tabs, quest titles (Press Start 2P, 7px)."""
    return load_font("PressStart2P-Regular.ttf", 7)

def font_tag():
    """Status indicators, prompt pills, button hints (Press Start 2P, 6px)."""
    return load_font("PressStart2P-Regular.ttf", 6)

# Body & Dialogue (Pixel Operator)
def font_dialogue():
    """In-game NPC conversations and reading (Pixel Operator, 15px)."""
    return load_font("PixelOperator.ttf", 15)

def font_body():
    """Item descriptions, lore, objective text (Pixel Operator, 14px)."""
    return load_font("PixelOperator.ttf", 14)

def font_body_small():
    """Compact secondary details (Pixel Operator, 12px)."""
    return load_font("PixelOperator.ttf", 12)

