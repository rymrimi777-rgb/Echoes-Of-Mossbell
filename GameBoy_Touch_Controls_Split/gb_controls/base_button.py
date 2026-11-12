from pathlib import Path

import pygame

from .animation import ButtonAnimation
from .events import GB_BUTTON_DOWN, GB_BUTTON_UP

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "buttons"
FRAME_FILES = ("idle.png", "mid.png", "pressed.png")


class TouchButton:
    """One on-screen button. Subclasses (see buttons/) only set group / name / action.

    NOTE: create the display (pygame.display.set_mode) BEFORE building buttons,
    because frames are loaded with convert_alpha().
    """

    group = ""   # dpad / action / extra / system
    name = ""    # folder name inside the group
    action = ""  # what the game receives

    def __init__(self, pos=(0, 0), scale=4):
        folder = ASSETS_DIR / self.group / self.name
        self.frames = [self._load(folder / f, scale) for f in FRAME_FILES]
        self.rect = self.frames[0].get_rect(topleft=pos)
        self.anim = ButtonAnimation()
        self._holders = set()  # fingers / mouse currently holding this button

    @staticmethod
    def _load(path, scale):
        img = pygame.image.load(str(path)).convert_alpha()
        # nearest-neighbor on purpose: keeps pixel art crisp
        return pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))

    @property
    def pressed(self):
        return bool(self._holders)

    def hit(self, point):
        return self.rect.collidepoint(point)

    def press(self, pointer_id):
        first = not self._holders
        self._holders.add(pointer_id)
        if first:
            self.anim.press()
            pygame.event.post(pygame.event.Event(GB_BUTTON_DOWN, action=self.action))

    def release(self, pointer_id):
        if pointer_id not in self._holders:
            return
        self._holders.discard(pointer_id)
        if not self._holders:
            self.anim.release()
            pygame.event.post(pygame.event.Event(GB_BUTTON_UP, action=self.action))

    def update(self, dt_ms):
        self.anim.update(dt_ms)

    def draw(self, surface):
        surface.blit(self.frames[self.anim.frame_index], self.rect)
