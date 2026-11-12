"""
Sprite-sheet slicer, character animation, animated tiles, and portrait animation.
"""
import pygame, os
from game.settings import SPRITE_DIR, TILE_DIR, WALK_ANIM_SPEED, IDLE_ANIM_SPEED
from game.ocean_animator import OceanCharacterAnimator


def load_image(path, colorkey=None):
    """Load a PNG and convert for fast blitting."""
    img = pygame.image.load(path).convert_alpha()
    if colorkey is not None:
        img.set_colorkey(colorkey)
    return img


def slice_sheet(surface, frame_w, frame_h):
    """Cut a sprite-sheet into a 2D list of sub-surfaces [row][col]."""
    cols = surface.get_width()  // frame_w
    rows = surface.get_height() // frame_h
    frames = []
    for r in range(rows):
        row = []
        for c in range(cols):
            rect = pygame.Rect(c * frame_w, r * frame_h, frame_w, frame_h)
            row.append(surface.subsurface(rect).copy())
        frames.append(row)
    return frames


def slice_strip(surface, frame_w, frame_h, count):
    """Slice a horizontal strip into *count* frames."""
    frames = []
    for i in range(count):
        rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
        frames.append(surface.subsurface(rect).copy())
    return frames


class CharacterAnimator:
    """
    Drives 8-directional/4-directional walk and idle animations for characters.
    128x128 sheet = 8 rows x 8 cols of 16x16 frames:
        Row 0: walk-down   (8 frames)
        Row 1: walk-up     (8 frames)
        Row 2: walk-left   (8 frames)
        Row 3: walk-right  (8 frames)
        Row 4: idle-down   (4 frames)
        Row 5: idle-up     (4 frames)
        Row 6: idle-left   (4 frames)
        Row 7: idle-right  (4 frames)
    """

    DIR_MAP = {"down": 0, "up": 1, "left": 2, "right": 3}

    def __init__(self, sheet_path):
        sheet = load_image(sheet_path)
        self.frames = slice_sheet(sheet, 16, 16)
        self.direction = "down"
        self.moving = False
        self.frame_index = 0
        self.timer = 0

    def update(self, dt_ms, moving, direction=None):
        self.moving = moving
        if direction:
            self.direction = direction

        if self.moving:
            speed = WALK_ANIM_SPEED
            row = self.DIR_MAP[self.direction]
            max_frames = 8
        else:
            speed = IDLE_ANIM_SPEED
            row = self.DIR_MAP[self.direction] + 4
            max_frames = 4

        self.timer += dt_ms
        if self.timer >= speed:
            self.timer -= speed
            self.frame_index = (self.frame_index + 1) % max_frames

        if self.frame_index >= len(self.frames[row]):
            self.frame_index = 0

    def get_frame(self):
        if self.moving:
            row = self.DIR_MAP[self.direction]
        else:
            row = self.DIR_MAP[self.direction] + 4

        row = min(row, len(self.frames) - 1)
        idx = min(self.frame_index, len(self.frames[row]) - 1)
        return self.frames[row][idx]


class TileStripAnimator:
    """Animates strip-based tiles (flowers, water) per JSON metadata (150ms)."""

    def __init__(self, strip_path, frame_w=16, frame_h=16, count=4, ms_per_frame=150):
        if os.path.isfile(strip_path):
            sheet = load_image(strip_path)
            self.frames = slice_strip(sheet, frame_w, frame_h, count)
        else:
            s = pygame.Surface((frame_w, frame_h))
            s.fill((48, 98, 48))
            self.frames = [s]
        self.ms_per_frame = ms_per_frame
        self.index = 0
        self.timer = 0

    def update(self, dt_ms):
        self.timer += dt_ms
        if self.timer >= self.ms_per_frame:
            self.timer -= self.ms_per_frame
            self.index = (self.index + 1) % len(self.frames)

    def get_frame(self):
        return self.frames[self.index]


class PortraitAnimator:
    """
    Animates 3-frame talking portraits (32x32):
    Frame 0: Neutral / Mouth closed
    Frame 1: Mouth open / Talking
    Frame 2: Blink
    """

    def __init__(self, strip_path):
        if os.path.isfile(strip_path):
            sheet = load_image(strip_path)
            self.frames = slice_strip(sheet, 32, 32, 3)
        else:
            s = pygame.Surface((32, 32))
            s.fill((139, 172, 15))
            self.frames = [s, s, s]

        self.current_frame = 0
        self.talk_timer = 0
        self.blink_timer = 0
        self.is_blinking = False

    def update(self, dt_ms, is_typing):
        if is_typing:
            self.is_blinking = False
            self.talk_timer += dt_ms
            if self.talk_timer >= 120:
                self.talk_timer -= 120
                self.current_frame = 1 if self.current_frame == 0 else 0
        else:
            self.talk_timer = 0
            # Natural blink occasionally
            self.blink_timer += dt_ms
            if not self.is_blinking and self.blink_timer >= 2400:
                self.is_blinking = True
                self.blink_timer = 0
                self.current_frame = 2
            elif self.is_blinking and self.blink_timer >= 150:
                self.is_blinking = False
                self.blink_timer = 0
                self.current_frame = 0
            elif not self.is_blinking:
                self.current_frame = 0

    def get_frame(self):
        idx = min(self.current_frame, len(self.frames) - 1)
        return self.frames[idx]
