"""
Remote Player Entity for Online Multiplayer.
Renders the partner player using their chosen Ocean Nostalgia character sprite and animations.
Implements subpixel linear interpolation (lerp) to ensure smooth, jitter-free movement.
"""
import math
import pygame
from game.ocean_animator import OceanCharacterAnimator
from game.fonts import font_tag
from game.settings import COLOR_DARKEST, COLOR_LIGHTEST, COLOR_LIGHT


class RemotePlayer:
    """
    Synchronized remote player entity.
    - Controlled exclusively by incoming network packets.
    - Smooths movement with interpolation.
    - Renders authentic 24x32 Game Boy character with overhead player badge.
    """

    def __init__(self, character_id="actor1_character_02", name="Player 2", slot="p2", x=176.0, y=144.0):
        self.character_id = character_id
        self.name = name
        self.slot = slot

        self.fx = float(x)
        self.fy = float(y)
        self.x = int(self.fx)
        self.y = int(self.fy)
        self.w = 16
        self.h = 16

        self.target_x = float(x)
        self.target_y = float(y)
        self.direction = "down"
        self.moving = False
        self.current_map = "village"
        self.connected = True

        # Ocean Character Animator for the remote player's chosen character
        self.animator = OceanCharacterAnimator(self.character_id, variant="gameboy",
                                              target_size=(24, 32), fps=8)
        self.animator.face(self.direction)

    def set_character(self, character_id):
        if self.character_id != character_id:
            self.character_id = character_id
            self.animator = OceanCharacterAnimator(self.character_id, variant="gameboy",
                                                  target_size=(24, 32), fps=8)
            self.animator.face(self.direction)

    def apply_network_state(self, state_dict):
        """Updates target position, animation, and map from incoming network packet."""
        if not state_dict:
            return

        tx = state_dict.get("x")
        ty = state_dict.get("y")
        if tx is not None and ty is not None:
            self.target_x = float(tx)
            self.target_y = float(ty)

            # Snap position if distance is huge (e.g. map change, teleport, spawn)
            dist = math.hypot(self.target_x - self.fx, self.target_y - self.fy)
            if dist > 48.0:
                self.fx = self.target_x
                self.fy = self.target_y
                self.x = int(self.fx)
                self.y = int(self.fy)

        new_dir = state_dict.get("direction")
        if new_dir in ("down", "left", "right", "up"):
            self.direction = new_dir

        self.moving = bool(state_dict.get("moving", False))
        self.current_map = state_dict.get("map", self.current_map)
        self.connected = bool(state_dict.get("connected", True))

        remote_char = state_dict.get("character_id")
        if remote_char:
            self.set_character(remote_char)

    def update(self, dt_ms):
        """Interpolates towards target position and advances 8 FPS walk animation."""
        if not self.connected:
            return

        # Linear interpolation (lerp) towards target position
        dx = self.target_x - self.fx
        dy = self.target_y - self.fy
        dist = math.hypot(dx, dy)

        if dist > 0.3:
            # Smooth step towards target
            step = min(dist, max(1.2, dist * 0.28))
            self.fx += (dx / dist) * step
            self.fy += (dy / dist) * step
            self.x = int(self.fx)
            self.y = int(self.fy)
        else:
            self.fx = self.target_x
            self.fy = self.target_y
            self.x = int(self.fx)
            self.y = int(self.fy)

        # Drive 8 FPS character animator
        self.animator.update(dt_ms, moving=self.moving, direction=self.direction)

    def draw(self, surface, camera):
        """Draws the remote character and overhead multiplayer badge."""
        if not self.connected:
            return

        # Render 24x32 character centered on 16x16 footprint
        frame = self.animator.get_frame()
        fw, fh = frame.get_size()
        draw_x = self.x - (fw - self.w) // 2
        draw_y = self.y - (fh - self.h)
        sx, sy = camera.apply(draw_x, draw_y)
        surface.blit(frame, (sx, sy))

        # Overhead player badge (e.g. "2P" or "P1")
        badge_text = "2P" if self.slot == "p2" else "1P"
        f = font_tag()
        tw, th = f.size(badge_text)
        bx = sx + (fw - tw) // 2
        by = sy - 7

        pygame.draw.rect(surface, COLOR_DARKEST, (bx - 2, by - 1, tw + 4, th + 2))
        pygame.draw.rect(surface, COLOR_LIGHT, (bx - 2, by - 1, tw + 4, th + 2), 1)
        badge_surf = f.render(badge_text, False, COLOR_LIGHTEST)
        surface.blit(badge_surf, (bx, by))
