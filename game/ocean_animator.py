"""
Ocean Character Animator
Loads and manages 8 FPS 4-directional sprite animations from the Ocean_Nostalgia_Pygame_Ready package.
Supports all 24 characters across Game Boy, Color, and Gray variants.
Preserves transparency, original 72x96 native frames, and nearest-neighbor scaled 24x32 in-game frames.
"""
import os
import json
import pygame
from game.settings import OCEAN_CHAR_DIR, COLOR_LIGHT, COLOR_DARKEST

_CACHE = {}  # (character_id, variant, target_size) -> (native_frames, scaled_frames, meta)


def get_available_characters(base_dir=None):
    """Returns a sorted list of all available character IDs."""
    directory = base_dir or OCEAN_CHAR_DIR
    if not os.path.isdir(directory):
        return []
    return sorted([d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))])


class OceanCharacterAnimator:
    """
    Animator for Ocean's Nostalgia character package.
    - Native frame size: 72x96 pixels (RPG Maker MV format, 3x integer scaling of 24x32 pixel art).
    - In-game target size: 24x32 pixels (crisp 1:1 pixel art at Game Boy resolution).
    - 3 frames per direction: down (0), left (1), right (2), up (3).
    - Walk cycle: [0, 1, 2, 1] at 8 FPS (125 ms per frame).
    - Idle frame: frame index 1 (middle frame).
    """

    DIRECTIONS = ["down", "left", "right", "up"]
    DIR_ROW_MAP = {"down": 0, "left": 1, "right": 2, "up": 3}
    WALK_CYCLE = [0, 1, 2, 1]

    def __init__(self, character_id="actor1_character_01", variant="gameboy",
                 target_size=(24, 32), fps=8, base_dir=None):
        self.character_id = character_id
        self.variant = variant
        self.target_size = target_size
        self.base_dir = base_dir or OCEAN_CHAR_DIR

        self.direction = "down"
        self.moving = False
        self.timer = 0.0
        self.cycle_index = 1
        self.current_frame_index = 1
        self.fps = fps
        self.ms_per_frame = 1000.0 / self.fps if self.fps > 0 else 125.0
        self.idle_frame_index = 1

        self.native_frames = {}
        self.scaled_frames = {}

        self._load_assets()

    def _load_assets(self):
        cache_key = (self.character_id, self.variant, self.target_size)
        if cache_key in _CACHE:
            self.native_frames, self.scaled_frames, meta = _CACHE[cache_key]
            self.fps = meta.get("fps", self.fps)
            self.ms_per_frame = 1000.0 / self.fps
            self.idle_frame_index = meta.get("idle_frame_index", 1)
            self.current_frame_index = self.idle_frame_index
            return

        char_variant_dir = os.path.join(self.base_dir, self.character_id, self.variant)

        # Fallback if specific character directory is missing
        if not os.path.isdir(char_variant_dir):
            fallback_char = "actor1_character_01"
            char_variant_dir = os.path.join(self.base_dir, fallback_char, self.variant)
            if not os.path.isdir(char_variant_dir):
                char_variant_dir = os.path.join(self.base_dir, fallback_char, "gameboy")

        # Load animation.json if present
        json_path = os.path.join(char_variant_dir, "animation.json")
        if os.path.isfile(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rec = data.get("animation_recommendation", {})
                    self.fps = rec.get("fps", self.fps)
                    self.ms_per_frame = 1000.0 / self.fps
                    self.idle_frame_index = rec.get("idle_frame_index", 1)
            except Exception:
                pass

        self.native_frames = {d: [] for d in self.DIRECTIONS}
        self.scaled_frames = {d: [] for d in self.DIRECTIONS}

        frames_dir = os.path.join(char_variant_dir, "frames")
        loaded_successfully = False

        # Attempt 1: Individual frame files (frames/<dir>/frame_0X.png)
        if os.path.isdir(frames_dir):
            try:
                all_found = True
                temp_native = {}
                temp_scaled = {}
                for d in self.DIRECTIONS:
                    temp_native[d] = []
                    temp_scaled[d] = []
                    for idx in range(3):
                        p = os.path.join(frames_dir, d, f"frame_{idx:02d}.png")
                        if not os.path.isfile(p):
                            all_found = False
                            break
                        surf = pygame.image.load(p).convert_alpha()
                        temp_native[d].append(surf)
                        if self.target_size:
                            sc = pygame.transform.scale(surf, self.target_size)
                            temp_scaled[d].append(sc)
                        else:
                            temp_scaled[d].append(surf)
                    if not all_found:
                        break

                if all_found:
                    self.native_frames = temp_native
                    self.scaled_frames = temp_scaled
                    loaded_successfully = True
            except Exception:
                loaded_successfully = False

        # Attempt 2: Direction strip files (*_walk_<dir>.png)
        if not loaded_successfully:
            try:
                all_strips = True
                temp_native = {}
                temp_scaled = {}
                for d in self.DIRECTIONS:
                    strip_name = f"{self.character_id}_{self.variant}_walk_{d}.png"
                    strip_path = os.path.join(char_variant_dir, strip_name)
                    if not os.path.isfile(strip_path):
                        all_strips = False
                        break
                    strip = pygame.image.load(strip_path).convert_alpha()
                    sw = strip.get_width() // 3
                    sh = strip.get_height()
                    frames_n = []
                    frames_s = []
                    for i in range(3):
                        sub = strip.subsurface(pygame.Rect(i * sw, 0, sw, sh)).copy()
                        frames_n.append(sub)
                        if self.target_size:
                            frames_s.append(pygame.transform.scale(sub, self.target_size))
                        else:
                            frames_s.append(sub)
                    temp_native[d] = frames_n
                    temp_scaled[d] = frames_s

                if all_strips:
                    self.native_frames = temp_native
                    self.scaled_frames = temp_scaled
                    loaded_successfully = True
            except Exception:
                loaded_successfully = False

        # Attempt 3: Sheet file (*_sheet.png)
        if not loaded_successfully:
            sheet_name = f"{self.character_id}_{self.variant}_sheet.png"
            sheet_path = os.path.join(char_variant_dir, sheet_name)
            if os.path.isfile(sheet_path):
                try:
                    sheet = pygame.image.load(sheet_path).convert_alpha()
                    fw = sheet.get_width() // 3
                    fh = sheet.get_height() // 4
                    for row_idx, d in enumerate(self.DIRECTIONS):
                        frames_n = []
                        frames_s = []
                        for col_idx in range(3):
                            sub = sheet.subsurface(pygame.Rect(col_idx * fw, row_idx * fh, fw, fh)).copy()
                            frames_n.append(sub)
                            if self.target_size:
                                frames_s.append(pygame.transform.scale(sub, self.target_size))
                            else:
                                frames_s.append(sub)
                        self.native_frames[d] = frames_n
                        self.scaled_frames[d] = frames_s
                    loaded_successfully = True
                except Exception:
                    loaded_successfully = False

        # Fallback placeholder if missing
        if not loaded_successfully:
            tw, th = self.target_size if self.target_size else (24, 32)
            for d in self.DIRECTIONS:
                self.native_frames[d] = []
                self.scaled_frames[d] = []
                for _ in range(3):
                    s_nat = pygame.Surface((72, 96), pygame.SRCALPHA)
                    s_nat.fill((0, 0, 0, 0))
                    pygame.draw.rect(s_nat, COLOR_LIGHT, (12, 16, 48, 64))
                    pygame.draw.rect(s_nat, COLOR_DARKEST, (12, 16, 48, 64), 2)
                    self.native_frames[d].append(s_nat)

                    s_sc = pygame.Surface((tw, th), pygame.SRCALPHA)
                    s_sc.fill((0, 0, 0, 0))
                    pygame.draw.rect(s_sc, COLOR_LIGHT, (4, 4, tw - 8, th - 8))
                    pygame.draw.rect(s_sc, COLOR_DARKEST, (4, 4, tw - 8, th - 8), 1)
                    self.scaled_frames[d].append(s_sc)

        meta = {
            "fps": self.fps,
            "idle_frame_index": self.idle_frame_index,
        }
        _CACHE[cache_key] = (self.native_frames, self.scaled_frames, meta)
        self.current_frame_index = self.idle_frame_index

    def update(self, dt_ms, moving, direction=None):
        """
        Updates the animation state.
        Frame timing is independent of movement speed (strictly 8 FPS).
        When standing still, immediately rests on the idle frame (frame 1).
        """
        if direction in self.DIRECTIONS:
            self.direction = direction

        self.moving = bool(moving)

        if self.moving:
            self.timer += dt_ms
            while self.timer >= self.ms_per_frame:
                self.timer -= self.ms_per_frame
                self.cycle_index = (self.cycle_index + 1) % len(self.WALK_CYCLE)
            self.current_frame_index = self.WALK_CYCLE[self.cycle_index]
        else:
            # Idle frame
            self.current_frame_index = self.idle_frame_index
            self.timer = 0.0
            self.cycle_index = 1

    def get_frame(self):
        """Returns the current scaled frame (target_size) for rendering on the Game Boy screen."""
        frames = self.scaled_frames.get(self.direction) or self.scaled_frames["down"]
        idx = min(self.current_frame_index, len(frames) - 1)
        return frames[idx]

    def get_native_frame(self):
        """Returns the native 72x96 frame."""
        frames = self.native_frames.get(self.direction) or self.native_frames["down"]
        idx = min(self.current_frame_index, len(frames) - 1)
        return frames[idx]

    def get_idle_frame(self, direction=None):
        """Returns the idle frame for the current or specified direction."""
        d = direction if direction in self.DIRECTIONS else self.direction
        frames = self.scaled_frames.get(d) or self.scaled_frames["down"]
        idx = min(self.idle_frame_index, len(frames) - 1)
        return frames[idx]

    def face(self, direction):
        """Makes the character face a direction without walking."""
        if direction in self.DIRECTIONS:
            self.direction = direction
        self.moving = False
        self.current_frame_index = self.idle_frame_index
        self.timer = 0.0
        self.cycle_index = 1

