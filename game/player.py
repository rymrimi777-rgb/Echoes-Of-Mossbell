"""
Player entity – fluid subpixel movement, sprint/dash, responsive interaction box, and collision.
"""
import pygame, os
from game.settings import (TILE_SIZE, PLAYER_WALK_SPEED, PLAYER_RUN_SPEED, SPRITE_DIR,
                           KEYS_UP, KEYS_DOWN, KEYS_LEFT, KEYS_RIGHT, KEYS_RUN)
from game.ocean_animator import OceanCharacterAnimator


class Player:
    def __init__(self, x, y, character_id="actor1_character_01", variant="gameboy"):
        self.fx = float(x)
        self.fy = float(y)
        self.x = int(self.fx)
        self.y = int(self.fy)
        self.w = 16
        self.h = 16
        self.direction = "down"
        self.moving = False

        # Health & Combat
        self.max_hp = 20
        self.hp = 20
        self.attack_timer = 0
        self.invulnerable_timer = 0
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0

        # Collision rect at feet (10x6)
        self.col_offset_x = 3
        self.col_offset_y = 10
        self.col_w = 10
        self.col_h = 6

        # Ocean Character Animator (Actor1 slot 1 hero)
        self.character_id = character_id
        self.variant = variant
        self.animator = OceanCharacterAnimator(self.character_id, variant=self.variant,
                                              target_size=(24, 32), fps=8)
        self.step_timer = 0
        self.was_running = False

    def set_character(self, character_id, variant="gameboy"):
        self.character_id = character_id
        self.variant = variant
        self.animator = OceanCharacterAnimator(self.character_id, variant=self.variant,
                                              target_size=(24, 32), fps=8)
        self.animator.face(self.direction)

    @property
    def col_rect(self):
        return pygame.Rect(self.x + self.col_offset_x,
                           self.y + self.col_offset_y,
                           self.col_w, self.col_h)

    @property
    def center_x(self):
        return self.x + self.w // 2

    @property
    def center_y(self):
        return self.y + self.h // 2

    def heal(self, amount):
        prev = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - prev

    def attack(self):
        """Triggers real-time sword slash attack."""
        if self.attack_timer <= 0:
            self.attack_timer = 180  # 180ms sword swing
            return True
        return False

    def get_attack_rect(self):
        """Returns 18x18 sword hitbox in front of player."""
        if self.direction == "up":
            return pygame.Rect(self.x - 2, self.y - 14, 20, 16)
        elif self.direction == "down":
            return pygame.Rect(self.x - 2, self.y + 14, 20, 16)
        elif self.direction == "left":
            return pygame.Rect(self.x - 14, self.y - 2, 16, 20)
        else:
            return pygame.Rect(self.x + 14, self.y - 2, 16, 20)

    def take_damage(self, amount, knock_dir=None):
        """Takes damage from enemy contact with invulnerability frames and knockback."""
        if self.invulnerable_timer > 0:
            return False

        self.hp = max(0, self.hp - amount)
        self.invulnerable_timer = 600  # 600ms invulnerability

        if knock_dir:
            self.knockback_vx = knock_dir[0] * 3.0
            self.knockback_vy = knock_dir[1] * 3.0

        return True

    def get_interact_box(self):
        """
        Returns a generous 22x20 pixel bounding box in front of the player,
        ensuring interactions trigger effortlessly without exact alignment.
        """
        if self.direction == "up":
            return pygame.Rect(self.x - 3, self.y - 14, 22, 16)
        elif self.direction == "down":
            return pygame.Rect(self.x - 3, self.y + 12, 22, 16)
        elif self.direction == "left":
            return pygame.Rect(self.x - 14, self.y - 3, 16, 22)
        else:
            return pygame.Rect(self.x + 12, self.y - 3, 16, 22)

    def is_near_target(self, target_rect):
        """Checks if target is inside the interact box OR within close proximity."""
        # Check facing box
        if self.get_interact_box().colliderect(target_rect):
            return True
        # Proximity check (player center within 22 pixels of target center)
        tcx, tcy = target_rect.center
        dist_sq = (self.center_x - tcx) ** 2 + (self.center_y - tcy) ** 2
        return dist_sq <= (22 ** 2)

    def update(self, dt_ms, collision_map, touch_ctrl=None, audio_mgr=None):
        if self.attack_timer > 0:
            self.attack_timer -= dt_ms

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt_ms

        # Apply knockback if active
        if abs(self.knockback_vx) > 0.05 or abs(self.knockback_vy) > 0.05:
            self.fx += self.knockback_vx
            self.fy += self.knockback_vy
            self.knockback_vx *= 0.80
            self.knockback_vy *= 0.80
            self.x = int(self.fx)
            self.y = int(self.fy)
            return

        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0

        # Running / Dash speed
        is_running = any(keys[k] for k in KEYS_RUN)

        up = any(keys[k] for k in KEYS_UP)
        down = any(keys[k] for k in KEYS_DOWN)
        left = any(keys[k] for k in KEYS_LEFT)
        right = any(keys[k] for k in KEYS_RIGHT)

        # Merge touch controller inputs
        if touch_ctrl and getattr(touch_ctrl, "enabled", False):
            if touch_ctrl.up:
                up = True
            if touch_ctrl.down:
                down = True
            if touch_ctrl.left:
                left = True
            if touch_ctrl.right:
                right = True
            if touch_ctrl.btn_b:
                is_running = True

        speed = PLAYER_RUN_SPEED if is_running else PLAYER_WALK_SPEED

        # Cancel opposing directions
        if up and not down:
            dy = -speed
        elif down and not up:
            dy = speed

        if left and not right:
            dx = -speed
        elif right and not left:
            dx = speed

        # Normalize diagonal speed so diagonal isn't 1.41x faster
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.moving = (dx != 0 or dy != 0)

        # Update facing direction
        if dy < 0:
            self.direction = "up"
        elif dy > 0:
            self.direction = "down"
        elif dx < 0:
            self.direction = "left"
        elif dx > 0:
            self.direction = "right"

        # Separate X and Y collision checking for smooth sliding
        if collision_map and self.moving:
            # Check X movement
            int_dx = int(dx) if abs(dx) >= 1.0 else (1 if dx > 0 else (-1 if dx < 0 else 0))
            if int_dx != 0:
                allowed_dx, _ = collision_map.can_move(self.col_rect, int_dx, 0)
                if allowed_dx == 0:
                    dx = 0.0

            # Check Y movement
            int_dy = int(dy) if abs(dy) >= 1.0 else (1 if dy > 0 else (-1 if dy < 0 else 0))
            if int_dy != 0:
                _, allowed_dy = collision_map.can_move(self.col_rect, 0, int_dy)
                if allowed_dy == 0:
                    dy = 0.0

        self.fx += dx
        self.fy += dy
        self.x = int(self.fx)
        self.y = int(self.fy)

        # Footstep and sprint sounds
        if self.moving:
            if is_running and not self.was_running and audio_mgr:
                audio_mgr.play_sfx("dash", "player")
            self.was_running = is_running

            self.step_timer += dt_ms
            step_interval = 220 if is_running else 330
            if self.step_timer >= step_interval:
                self.step_timer = 0
                if audio_mgr:
                    audio_mgr.play_sfx("step_grass", "player")
        else:
            self.step_timer = 200
            self.was_running = False

        self.animator.update(dt_ms, self.moving, self.direction if self.moving else None)

    def draw(self, surface, camera):
        # Invulnerability flicker (flash every 60ms)
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 60) % 2 == 1:
            pass  # skip blitting for flicker effect
        else:
            frame = self.animator.get_frame()
            fw, fh = frame.get_size()
            draw_x = self.x - (fw - self.w) // 2
            draw_y = self.y - (fh - self.h)
            sx, sy = camera.apply(draw_x, draw_y)
            surface.blit(frame, (sx, sy))

        # Sword slash arc effect
        if self.attack_timer > 0:
            from game.settings import COLOR_LIGHTEST, COLOR_DARKEST
            atk_rect = self.get_attack_rect()
            asx, asy = camera.apply(atk_rect.x, atk_rect.y)
            slash_surf = pygame.Surface((atk_rect.w, atk_rect.h), pygame.SRCALPHA)
            if self.direction == "up":
                pygame.draw.arc(slash_surf, COLOR_LIGHTEST, (1, 1, atk_rect.w - 2, atk_rect.h + 6), 0.2, 2.9, 3)
                pygame.draw.arc(slash_surf, COLOR_DARKEST, (0, 0, atk_rect.w, atk_rect.h + 8), 0.2, 2.9, 1)
            elif self.direction == "down":
                pygame.draw.arc(slash_surf, COLOR_LIGHTEST, (1, -6, atk_rect.w - 2, atk_rect.h + 4), 3.3, 6.0, 3)
                pygame.draw.arc(slash_surf, COLOR_DARKEST, (0, -8, atk_rect.w, atk_rect.h + 8), 3.3, 6.0, 1)
            elif self.direction == "left":
                pygame.draw.arc(slash_surf, COLOR_LIGHTEST, (1, 1, atk_rect.w + 6, atk_rect.h - 2), 1.7, 4.5, 3)
                pygame.draw.arc(slash_surf, COLOR_DARKEST, (0, 0, atk_rect.w + 8, atk_rect.h), 1.7, 4.5, 1)
            else:
                pygame.draw.arc(slash_surf, COLOR_LIGHTEST, (-6, 1, atk_rect.w + 4, atk_rect.h - 2), 4.9, 1.4, 3)
                pygame.draw.arc(slash_surf, COLOR_DARKEST, (-8, 0, atk_rect.w + 8, atk_rect.h), 4.9, 1.4, 1)
            surface.blit(slash_surf, (asx, asy))
