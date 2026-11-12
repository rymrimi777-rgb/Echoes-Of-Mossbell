import pygame

from .buttons import (
    AButton, BButton, DownButton, LeftButton, RightButton,
    SelectButton, StartButton, UpButton, XButton, YButton,
)


class TouchController:
    """Routes touch / mouse input to buttons. Supports multi-touch and sliding
    a finger from one button to another (handy for the D-pad)."""

    def __init__(self, buttons):
        self.buttons = list(buttons)
        self._pointers = {}  # pointer_id -> button currently held (or None)

    # ---- input -------------------------------------------------------
    def handle_event(self, event, surface_size):
        w, h = surface_size
        t = event.type
        if t == pygame.FINGERDOWN:
            self._down(event.finger_id, (event.x * w, event.y * h))
        elif t == pygame.FINGERMOTION:
            self._move(event.finger_id, (event.x * w, event.y * h))
        elif t == pygame.FINGERUP:
            self._up(event.finger_id)
        # mouse = desktop testing. Skip mouse events synthesized from touch.
        elif t == pygame.MOUSEBUTTONDOWN and event.button == 1 and not getattr(event, "touch", False):
            self._down("mouse", event.pos)
        elif t == pygame.MOUSEMOTION and "mouse" in self._pointers:
            self._move("mouse", event.pos)
        elif t == pygame.MOUSEBUTTONUP and event.button == 1 and not getattr(event, "touch", False):
            self._up("mouse")

    def _button_at(self, pos):
        return next((b for b in self.buttons if b.hit(pos)), None)

    def _down(self, pid, pos):
        btn = self._button_at(pos)
        self._pointers[pid] = btn
        if btn:
            btn.press(pid)

    def _move(self, pid, pos):
        if pid not in self._pointers:
            return
        old, new = self._pointers[pid], self._button_at(pos)
        if new is old:
            return
        if old:
            old.release(pid)
        if new:
            new.press(pid)
        self._pointers[pid] = new

    def _up(self, pid):
        btn = self._pointers.pop(pid, None)
        if btn:
            btn.release(pid)

    # ---- loop --------------------------------------------------------
    def update(self, dt_ms):
        for b in self.buttons:
            b.update(dt_ms)

    def draw(self, surface):
        for b in self.buttons:
            b.draw(surface)

    def is_pressed(self, action):
        return any(b.action == action and b.pressed for b in self.buttons)


def build_default_controller(screen_size, scale=3, margin=16, with_xy=False):
    """Classic Game Boy layout: D-pad bottom-left, A/B bottom-right,
    Select/Start bottom-center. Move or resize buttons freely - each one only
    needs a position."""
    w, h = screen_size
    cell = 16 * scale
    gap = 2 * scale
    step = cell + gap

    # D-pad
    ox, oy = margin, h - margin - 2 * cell - gap
    up = UpButton((ox + step, oy), scale)
    left = LeftButton((ox, oy + step), scale)
    down = DownButton((ox + step, oy + step), scale)
    right = RightButton((ox + 2 * step, oy + step), scale)

    # A / B (A slightly higher, like the real thing)
    a = AButton((w - margin - cell, h - margin - cell - step // 2), scale)
    b = BButton((w - margin - 2 * cell - gap, h - margin - cell), scale)

    # Select / Start
    sw = 32 * scale
    sy = h - margin - cell
    select = SelectButton((w // 2 - sw - gap, sy), scale)
    start = StartButton((w // 2 + gap, sy), scale)

    buttons = [up, down, left, right, a, b, select, start]
    if with_xy:
        buttons += [
            XButton((a.rect.x - step, a.rect.y - step), scale),
            YButton((b.rect.x - step, b.rect.y - step), scale),
        ]
    return TouchController(buttons)
