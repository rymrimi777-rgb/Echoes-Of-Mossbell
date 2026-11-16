"""
Game Boy-Style Touch Controls System for Mobile / Android & Desktop Emulation.
Uses authentic 4-shade pixel-art button assets with 3-frame press animations
(idle, mid, pressed), multi-touch pointer tracking, directional D-pad sliding,
expanded touch hitboxes, and adaptive landscape/portrait layouts.

Assets: GBStudio Keyboard Buttons by Luna Desuwa (https://okutasan.itch.io)
"""
import os
import pygame
from game.settings import (
    BUTTON_DIR, COLOR_DARKEST, COLOR_DARK, COLOR_LIGHT, COLOR_LIGHTEST, IS_ANDROID
)

# Animation state constants
ANIM_IDLE = "idle"
ANIM_PRESSING = "pressing"
ANIM_PRESSED = "pressed"
ANIM_RELEASING = "releasing"
FRAME_FOR_STATE = {
    ANIM_IDLE: 0,
    ANIM_PRESSING: 1,
    ANIM_PRESSED: 2,
    ANIM_RELEASING: 1,
}
FRAME_FILES = ("idle.png", "mid.png", "pressed.png")


class ButtonAnimation:
    """Handles 3-frame button press/release animation timing."""

    def __init__(self, step_ms=40):
        self.step_ms = step_ms
        self.state = ANIM_IDLE
        self._timer = 0
        self._release_queued = False

    def press(self):
        if self.state in (ANIM_IDLE, ANIM_RELEASING):
            self.state = ANIM_PRESSING
            self._timer = 0
        self._release_queued = False

    def release(self):
        if self.state == ANIM_PRESSED:
            self.state = ANIM_RELEASING
            self._timer = 0
        elif self.state == ANIM_PRESSING:
            # Quick tap: ensure pressed frame displays before returning to idle
            self._release_queued = True

    def update(self, dt_ms):
        if self.state in (ANIM_PRESSING, ANIM_RELEASING) or (
            self.state == ANIM_PRESSED and self._release_queued
        ):
            self._timer += dt_ms
            if self._timer >= self.step_ms:
                self._timer = 0
                if self.state == ANIM_PRESSING:
                    self.state = ANIM_PRESSED
                elif self.state == ANIM_PRESSED:
                    self.state = ANIM_RELEASING
                    self._release_queued = False
                else:
                    self.state = ANIM_IDLE

    @property
    def frame_index(self):
        return FRAME_FOR_STATE[self.state]


class GBTouchButton:
    """Individual Game Boy pixel-art touch button with 3-frame animation."""

    def __init__(self, group, name, action, pos=(0, 0), scale=3, padding=10, opacity=1.0):
        self.group = group
        self.name = name
        self.action = action
        self.scale = scale
        self.padding = padding
        self.opacity = opacity
        self.anim = ButtonAnimation()
        self._holders = set()

        self.frames = self._load_frames()
        self.rect = self.frames[0].get_rect(topleft=pos)
        self.touch_rect = self.rect.inflate(padding * 2, padding * 2)

    def _load_frames(self):
        folder = os.path.join(BUTTON_DIR, self.group, self.name)
        loaded = []
        for filename in FRAME_FILES:
            filepath = os.path.join(folder, filename)
            if os.path.exists(filepath):
                try:
                    img = pygame.image.load(filepath).convert_alpha()
                    sw = int(img.get_width() * self.scale)
                    sh = int(img.get_height() * self.scale)
                    scaled = pygame.transform.scale(img, (sw, sh))
                    loaded.append(scaled)
                except Exception:
                    loaded.append(self._create_fallback_frame(filename))
            else:
                loaded.append(self._create_fallback_frame(filename))

        # Apply opacity if specified
        if self.opacity < 0.99:
            alpha = max(30, min(255, int(self.opacity * 255)))
            for frame in loaded:
                frame.set_alpha(alpha)

        return loaded

    def _create_fallback_frame(self, filename):
        w = int(32 * self.scale if self.group == "system" else 16 * self.scale)
        h = int(16 * self.scale)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color = COLOR_DARKEST if filename == "pressed.png" else COLOR_DARK
        pygame.draw.rect(surf, color, (0, 0, w, h), border_radius=4)
        pygame.draw.rect(surf, COLOR_LIGHTEST, (0, 0, w, h), width=2, border_radius=4)
        return surf

    def set_position(self, pos):
        self.rect.topleft = pos
        self.touch_rect = self.rect.inflate(self.padding * 2, self.padding * 2)

    def set_opacity(self, opacity):
        self.opacity = max(0.2, min(1.0, opacity))
        alpha = int(self.opacity * 255)
        for frame in self.frames:
            frame.set_alpha(alpha)

    @property
    def pressed(self):
        return bool(self._holders)

    def hit(self, point):
        return self.touch_rect.collidepoint(point)

    def press(self, pointer_id):
        was_empty = not self._holders
        self._holders.add(pointer_id)
        if was_empty:
            self.anim.press()
            return True
        return False

    def release(self, pointer_id):
        if pointer_id not in self._holders:
            return False
        self._holders.discard(pointer_id)
        if not self._holders:
            self.anim.release()
            return True
        return False

    def update(self, dt_ms):
        self.anim.update(dt_ms)

    def draw(self, surface):
        surface.blit(self.frames[self.anim.frame_index], self.rect)

    # Compatibility helpers
    def contains(self, px, py):
        return self.hit((px, py))

    @property
    def label(self):
        return self.action.upper()


class TouchController:
    """Full Game Boy virtual touch controller managing multi-touch, sliding, and layout."""

    def __init__(self, screen_w=640, screen_h=576):
        self.screen_w = max(160, screen_w)
        self.screen_h = max(144, screen_h)
        self.enabled = True
        self.mode = "always" if IS_ANDROID else "auto"
        self.visible = (self.mode == "always" or IS_ANDROID)

        # Settings
        self.size_preset = "normal"  # "small", "normal", "large"
        self.opacity = 0.90          # 0.5, 0.75, 1.0

        # State flags (held)
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        self.btn_a = False
        self.btn_b = False
        self.btn_start = False
        self.btn_select = False

        # One-shot triggers (rising edge)
        self.btn_up_pressed = False
        self.btn_down_pressed = False
        self.btn_left_pressed = False
        self.btn_right_pressed = False
        self.btn_a_pressed = False
        self.btn_b_pressed = False
        self.btn_start_pressed = False
        self.btn_select_pressed = False
        self.btn_inv_pressed = False
        self.btn_menu_pressed = False

        self.buttons = {}
        self._pointers = {}  # pointer_id -> button currently held

        self.update_layout(self.screen_w, self.screen_h)

    def set_size_preset(self, preset):
        if preset in ("small", "normal", "large"):
            self.size_preset = preset
            self.update_layout(self.screen_w, self.screen_h)

    def set_opacity(self, opacity):
        self.opacity = max(0.2, min(1.0, opacity))
        for btn in self.buttons.values():
            btn.set_opacity(self.opacity)

    def _calc_scale(self):
        factor = 1.0
        if self.size_preset == "small":
            factor = 0.80
        elif self.size_preset == "large":
            factor = 1.25

        # Base scale according to screen resolution
        base_scale = max(2.0, min(5.0, (self.screen_h / 190.0)))
        return max(1.8, round(base_scale * factor, 1))

    def update_layout(self, screen_w, screen_h):
        """Recalculates positions and scales for landscape or portrait."""
        self.screen_w = max(160, screen_w)
        self.screen_h = max(144, screen_h)
        is_portrait = self.screen_h > (self.screen_w * 1.1)

        scale = self._calc_scale()
        cell = int(16 * scale)
        gap = max(2, int(2 * scale))
        padding = max(8, int(cell * 0.35))

        # Clear existing button references but preserve state holders
        old_pointers = dict(self._pointers)
        self.buttons.clear()

        if is_portrait:
            # ================= PORTRAIT CONSOLE LAYOUT =================
            # Game screen sits on upper 50%, controls fill lower half like a real Game Boy
            ctl_top = int(self.screen_h * 0.54)
            ctl_h = self.screen_h - ctl_top

            # D-pad bottom-left
            ox = int(self.screen_w * 0.10)
            oy = ctl_top + int(ctl_h * 0.40)

            step = cell + gap
            up_pos = (ox + step, oy)
            left_pos = (ox, oy + step)
            down_pos = (ox + step, oy + 2 * step)
            right_pos = (ox + 2 * step, oy + step)

            # A & B Action Buttons bottom-right (angled, A higher than B)
            b_pos = (int(self.screen_w * 0.64), ctl_top + int(ctl_h * 0.52))
            a_pos = (int(self.screen_w * 0.82), ctl_top + int(ctl_h * 0.40))

            # Select & Start buttons centered below display
            sw = int(32 * scale)
            sys_y = ctl_top + int(ctl_h * 0.12)
            sel_x = int(self.screen_w * 0.50 - sw - gap * 2)
            start_x = int(self.screen_w * 0.50 + gap * 2)

        else:
            # ================= LANDSCAPE MOBILE / DESKTOP LAYOUT =================
            margin_x = max(12, int(self.screen_w * 0.03))
            margin_y = max(12, int(self.screen_h * 0.04))

            # D-pad on bottom-left
            step = cell + gap
            dpad_w = 3 * cell + 2 * gap
            ox = margin_x
            oy = self.screen_h - margin_y - dpad_w

            up_pos = (ox + step, oy)
            left_pos = (ox, oy + step)
            down_pos = (ox + step, oy + 2 * step)
            right_pos = (ox + 2 * step, oy + step)

            # A & B Action Buttons on bottom-right (A higher than B)
            a_pos = (self.screen_w - margin_x - cell, self.screen_h - margin_y - int(cell * 2.2))
            b_pos = (self.screen_w - margin_x - int(cell * 2.2), self.screen_h - margin_y - cell)

            # Select & Start buttons near center bottom
            sw = int(32 * scale)
            sys_y = self.screen_h - margin_y - int(cell * 0.8)
            sel_x = int(self.screen_w * 0.50 - sw - gap * 3)
            start_x = int(self.screen_w * 0.50 + gap * 3)

        # Build button objects
        self.buttons["up"] = GBTouchButton("dpad", "up", "up", up_pos, scale, padding, self.opacity)
        self.buttons["down"] = GBTouchButton("dpad", "down", "down", down_pos, scale, padding, self.opacity)
        self.buttons["left"] = GBTouchButton("dpad", "left", "left", left_pos, scale, padding, self.opacity)
        self.buttons["right"] = GBTouchButton("dpad", "right", "right", right_pos, scale, padding, self.opacity)

        self.buttons["a"] = GBTouchButton("action", "a", "a", a_pos, scale, padding, self.opacity)
        self.buttons["b"] = GBTouchButton("action", "b", "b", b_pos, scale, padding, self.opacity)

        self.buttons["select"] = GBTouchButton("system", "select", "select", (sel_x, sys_y), scale, padding, self.opacity)
        self.buttons["start"] = GBTouchButton("system", "start", "start", (start_x, sys_y), scale, padding, self.opacity)

        # Backwards compatibility aliases for inv/menu
        self.buttons["inv"] = self.buttons["select"]
        self.buttons["menu"] = self.buttons["start"]

        # Re-attach pointers if any were active
        self._pointers.clear()
        for pid, old_btn in old_pointers.items():
            if old_btn and old_btn.action in self.buttons:
                btn = self.buttons[old_btn.action]
                btn.press(pid)
                self._pointers[pid] = btn

    def _button_at(self, pos):
        """Returns the best matching button for a screen coordinate with distance fallback."""
        direct = [b for b in self.buttons.values() if b.hit(pos)]
        if not direct:
            return None
        if len(direct) == 1:
            return direct[0]
        # If overlapping hitboxes, pick the one closest to its visual center
        px, py = pos
        return min(direct, key=lambda b: (b.rect.centerx - px) ** 2 + (b.rect.centery - py) ** 2)

    def handle_event(self, event):
        """Processes real touch events and mouse emulation."""
        if not self.enabled:
            return

        t = event.type
        if t == pygame.FINGERDOWN:
            if self.mode == "auto":
                self.visible = True
            pos = (event.x * self.screen_w, event.y * self.screen_h)
            self._down(event.finger_id, pos)

        elif t == pygame.FINGERMOTION:
            pos = (event.x * self.screen_w, event.y * self.screen_h)
            self._move(event.finger_id, pos)

        elif t == pygame.FINGERUP:
            self._up(event.finger_id)

        # Mouse fallback for desktop testing
        elif t == pygame.MOUSEBUTTONDOWN and event.button == 1 and not getattr(event, "touch", False):
            if self.mode == "auto":
                self.visible = True
            self._down("mouse", event.pos)

        elif t == pygame.MOUSEMOTION and "mouse" in self._pointers:
            self._move("mouse", event.pos)

        elif t == pygame.MOUSEBUTTONUP and event.button == 1 and not getattr(event, "touch", False):
            self._up("mouse")

    def _down(self, pid, pos):
        btn = self._button_at(pos)
        self._pointers[pid] = btn
        if btn:
            newly_pressed = btn.press(pid)
            if newly_pressed:
                self._trigger_edge(btn.action)
        self._sync_states()

    def _move(self, pid, pos):
        if pid not in self._pointers:
            return
        old_btn = self._pointers[pid]
        new_btn = self._button_at(pos)
        if new_btn is old_btn:
            return
        if old_btn:
            old_btn.release(pid)
        if new_btn:
            newly_pressed = new_btn.press(pid)
            if newly_pressed:
                self._trigger_edge(new_btn.action)
        self._pointers[pid] = new_btn
        self._sync_states()

    def _up(self, pid):
        btn = self._pointers.pop(pid, None)
        if btn:
            btn.release(pid)
        self._sync_states()

    def _trigger_edge(self, action):
        if action == "up":
            self.btn_up_pressed = True
        elif action == "down":
            self.btn_down_pressed = True
        elif action == "left":
            self.btn_left_pressed = True
        elif action == "right":
            self.btn_right_pressed = True
        elif action == "a":
            self.btn_a_pressed = True
        elif action == "b":
            self.btn_b_pressed = True
        elif action in ("start", "menu"):
            self.btn_start_pressed = True
            self.btn_menu_pressed = True
        elif action in ("select", "inv"):
            self.btn_select_pressed = True
            self.btn_inv_pressed = True

    def _sync_states(self):
        self.up = self.buttons["up"].pressed
        self.down = self.buttons["down"].pressed
        self.left = self.buttons["left"].pressed
        self.right = self.buttons["right"].pressed
        self.btn_a = self.buttons["a"].pressed
        self.btn_b = self.buttons["b"].pressed
        self.btn_start = self.buttons["start"].pressed
        self.btn_select = self.buttons["select"].pressed

    # One-shot trigger consumers
    def consume_up(self):
        val = self.btn_up_pressed
        self.btn_up_pressed = False
        return val

    def consume_down(self):
        val = self.btn_down_pressed
        self.btn_down_pressed = False
        return val

    def consume_left(self):
        val = self.btn_left_pressed
        self.btn_left_pressed = False
        return val

    def consume_right(self):
        val = self.btn_right_pressed
        self.btn_right_pressed = False
        return val

    def consume_a(self):
        val = self.btn_a_pressed
        self.btn_a_pressed = False
        return val

    def consume_b(self):
        val = self.btn_b_pressed
        self.btn_b_pressed = False
        return val

    def consume_start(self):
        val = self.btn_start_pressed or self.btn_menu_pressed
        self.btn_start_pressed = False
        self.btn_menu_pressed = False
        return val

    def consume_select(self):
        val = self.btn_select_pressed or self.btn_inv_pressed
        self.btn_select_pressed = False
        self.btn_inv_pressed = False
        return val

    # Compatibility aliases
    def consume_menu(self):
        return self.consume_start()

    def consume_inv(self):
        return self.consume_select()

    def update(self, dt_ms):
        """Updates animation state for all buttons."""
        # Unique instances to avoid updating duplicates
        unique = {id(b): b for b in self.buttons.values()}
        for b in unique.values():
            b.update(dt_ms)

    def draw(self, surface):
        """Draws the pixel-art Game Boy button overlay."""
        if not self.enabled or not self.visible:
            return

        unique = {id(b): b for b in self.buttons.values()}
        for b in unique.values():
            b.draw(surface)
