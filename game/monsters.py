"""
Monster and Combat System for Echoes of Mossbell.
Real-time retro Action-RPG combat (Zelda: Link's Awakening style).
Supports 12 monster types (SGQ Enemies + Slime King boss), patrol/chase/flutter/boss AI,
directional animation frames, knockback physics, hurt flashing, and loot drops.
"""
import os
import math
import random
import pygame
from game.settings import (
    TILE_SIZE, COLOR_DARKEST, COLOR_DARK, COLOR_LIGHT, COLOR_LIGHTEST,
    MONSTERS_DIR, BOSSES_DIR
)
from game.asset_registry import MONSTER_CATALOG


# Frame slicing cache: monster_type -> dict of directional frame lists
_monster_sheet_cache = {}


def get_monster_frames(monster_type):
    """Slice and cache frames from the monster spritesheet."""
    if monster_type in _monster_sheet_cache:
        return _monster_sheet_cache[monster_type]

    info = MONSTER_CATALOG.get(monster_type)
    if not info:
        return None

    path = os.path.join(info["dir"], info["file"])
    if not os.path.isfile(path):
        return None

    sheet = pygame.image.load(path)
    if pygame.display.get_surface() is not None:
        try:
            sheet = sheet.convert_alpha()
        except Exception:
            pass
    fw, fh = info["frame_w"], info["frame_h"]
    cols, rows = info["cols"], info["rows"]

    frames_by_row = []
    for r in range(rows):
        row_frames = []
        for c in range(cols):
            rect = pygame.Rect(c * fw, r * fh, fw, fh)
            frame = pygame.Surface((fw, fh), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), rect)
            row_frames.append(frame)
        frames_by_row.append(row_frames)

    # Direction mappings according to SGQ sheet standards:
    # Row 0 = Down, Row 1 = Left, Row 2 = Right, Row 3 = Up
    # Row 4 = Action/Attack, Row 5 = Hurt/Death (if rows >= 6)
    dirs = {
        "down": frames_by_row[0] if rows > 0 else [],
        "left": frames_by_row[1] if rows > 1 else frames_by_row[0],
        "right": frames_by_row[2] if rows > 2 else frames_by_row[0],
        "up": frames_by_row[3] if rows > 3 else frames_by_row[0],
        "action": frames_by_row[4] if rows > 4 else frames_by_row[0],
        "hurt": frames_by_row[5] if rows > 5 else frames_by_row[0],
    }

    _monster_sheet_cache[monster_type] = {
        "dirs": dirs,
        "fw": fw,
        "fh": fh,
        "info": info
    }
    return _monster_sheet_cache[monster_type]


class Monster:
    """
    Live enemy instance roaming the map.
    Handles AI, movement, contact collision, sword hitboxes, knockback, and loot.
    """

    def __init__(self, monster_type, x, y, patrol_radius=40):
        self.monster_type = monster_type
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.fx = float(x)
        self.fy = float(y)
        self.x = int(self.fx)
        self.y = int(self.fy)

        data = get_monster_frames(monster_type)
        if data:
            self.fw = data["fw"]
            self.fh = data["fh"]
            self.frames = data["dirs"]
            info = data["info"]
            self.name = info["name"]
            self.max_hp = info["max_hp"]
            self.hp = self.max_hp
            self.atk = info["atk"]
            self.base_speed = info["speed"]
            self.ai_type = info["ai"]
            self.exp = info["exp"]
            self.loot = info["loot"]
        else:
            self.fw = 16
            self.fh = 16
            self.frames = {}
            self.name = monster_type
            self.max_hp = 6
            self.hp = 6
            self.atk = 2
            self.base_speed = 0.6
            self.ai_type = "patrol"
            self.exp = 8
            self.loot = "coins"

        self.direction = "down"
        self.is_alive = True
        self.death_timer = 0
        self.hurt_timer = 0
        self.contact_cooldown = 0
        self.anim_timer = 0
        self.frame_index = 0

        # AI state
        self.patrol_radius = patrol_radius
        self.patrol_timer = random.uniform(800, 2000)
        self.patrol_dir = (0.0, 0.0)
        self.is_chasing = False

        # Boss special state
        self.boss_timer = 0
        self.is_charging = False

        # Knockback velocity
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0

    @property
    def col_rect(self):
        """Collision bounding box for movement and collision."""
        cw = min(14, self.fw)
        ch = min(10, self.fh // 2)
        ox = (self.fw - cw) // 2
        oy = self.fh - ch
        return pygame.Rect(self.x + ox, self.y + oy, cw, ch)

    @property
    def hit_rect(self):
        """Generous bounding box for sword strike detection."""
        return pygame.Rect(self.x, self.y, self.fw, self.fh)

    def take_damage(self, amount, knock_dir=None):
        """
        Applies sword damage, triggers hurt animation and knockback.
        Returns True if this hit defeats the monster.
        """
        if not self.is_alive or self.hurt_timer > 0:
            return False

        self.hp = max(0, self.hp - amount)
        self.hurt_timer = 220  # flash for 220ms

        # Knockback push
        if knock_dir:
            k_speed = 2.4 if self.ai_type != "boss" else 0.8
            self.knockback_vx = knock_dir[0] * k_speed
            self.knockback_vy = knock_dir[1] * k_speed

        if self.hp <= 0:
            self.is_alive = False
            self.death_timer = 300  # death dissolve
            return True

        return False

    def update(self, dt_ms, player, collision_map, new_spawns=None):
        if not self.is_alive:
            if self.death_timer > 0:
                self.death_timer -= dt_ms
            return

        if self.hurt_timer > 0:
            self.hurt_timer -= dt_ms

        if self.contact_cooldown > 0:
            self.contact_cooldown -= dt_ms

        # Apply knockback decay
        if abs(self.knockback_vx) > 0.05 or abs(self.knockback_vy) > 0.05:
            self.fx += self.knockback_vx
            self.fy += self.knockback_vy
            self.knockback_vx *= 0.80
            self.knockback_vy *= 0.80
            self.x = int(self.fx)
            self.y = int(self.fy)
            return

        # AI Movement
        dx, dy = 0.0, 0.0
        dist_to_player = math.hypot(player.center_x - (self.x + self.fw // 2),
                                    player.center_y - (self.y + self.fh // 2))

        aggro_range = 80 if self.ai_type == "chase" else (120 if self.ai_type == "boss" else 55)

        if self.ai_type == "boss":
            self.boss_timer += dt_ms
            if self.boss_timer > 3000:
                self.boss_timer = 0
                self.is_charging = not self.is_charging

            speed = self.base_speed * (2.2 if self.is_charging else 1.0)
            if dist_to_player < 180:
                ang = math.atan2(player.center_y - (self.y + self.fh // 2),
                                 player.center_x - (self.x + self.fw // 2))
                dx = math.cos(ang) * speed
                dy = math.sin(ang) * speed

        elif self.ai_type == "chase" and dist_to_player <= aggro_range:
            self.is_chasing = True
            ang = math.atan2(player.center_y - (self.y + self.fh // 2),
                             player.center_x - (self.x + self.fw // 2))
            dx = math.cos(ang) * self.base_speed
            dy = math.sin(ang) * self.base_speed

        elif self.ai_type == "flutter":
            # Erratic darting movement
            self.patrol_timer -= dt_ms
            if self.patrol_timer <= 0:
                self.patrol_timer = random.uniform(300, 700)
                angle = random.uniform(0, 2 * math.pi)
                self.patrol_dir = (math.cos(angle), math.sin(angle))
            dx = self.patrol_dir[0] * self.base_speed
            dy = self.patrol_dir[1] * self.base_speed

        else:
            # Standard patrol wander
            self.is_chasing = False
            self.patrol_timer -= dt_ms
            if self.patrol_timer <= 0:
                self.patrol_timer = random.uniform(1000, 2500)
                if random.random() < 0.4:
                    self.patrol_dir = (0.0, 0.0)  # Pause
                else:
                    angle = random.uniform(0, 2 * math.pi)
                    self.patrol_dir = (math.cos(angle), math.sin(angle))

            # Return toward spawn point if strayed too far
            dist_from_spawn = math.hypot(self.fx - self.spawn_x, self.fy - self.spawn_y)
            if dist_from_spawn > self.patrol_radius:
                ang = math.atan2(self.spawn_y - self.fy, self.spawn_x - self.fx)
                self.patrol_dir = (math.cos(ang), math.sin(ang))

            dx = self.patrol_dir[0] * self.base_speed
            dy = self.patrol_dir[1] * self.base_speed

        # Update facing direction
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        elif abs(dy) > 0.05:
            self.direction = "down" if dy > 0 else "up"

        # Separate X/Y collision handling with map
        if collision_map:
            if dx != 0:
                int_dx = 1 if dx > 0 else -1
                adx, _ = collision_map.can_move(self.col_rect, int_dx, 0)
                if adx == 0:
                    dx = 0
            if dy != 0:
                int_dy = 1 if dy > 0 else -1
                _, ady = collision_map.can_move(self.col_rect, 0, int_dy)
                if ady == 0:
                    dy = 0

        self.fx += dx
        self.fy += dy
        self.x = int(self.fx)
        self.y = int(self.fy)

        # Animation timing
        self.anim_timer += dt_ms
        if self.anim_timer >= 150:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % 4

    def draw(self, surface, camera):
        if not self.is_alive and self.death_timer <= 0:
            return

        # Frame selection
        row_key = self.direction
        if self.hurt_timer > 0 and "hurt" in self.frames and self.frames["hurt"]:
            # Flash hurt frame
            flist = self.frames["hurt"]
            frame = flist[min(self.frame_index, len(flist) - 1)]
        elif row_key in self.frames and self.frames[row_key]:
            flist = self.frames[row_key]
            frame = flist[self.frame_index % len(flist)]
        else:
            # Fallback placeholder
            frame = pygame.Surface((self.fw, self.fh))
            frame.fill(COLOR_DARK)

        sx, sy = camera.apply(self.x, self.y)

        # Flashing effect when hurt (flicker visibility)
        if self.hurt_timer > 0 and (self.hurt_timer // 40) % 2 == 0:
            flash_surf = frame.copy()
            flash_surf.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(flash_surf, (sx, sy))
        else:
            surface.blit(frame, (sx, sy))

        # Health bar for Boss or damaged monsters
        if self.ai_type == "boss" and self.is_alive:
            # Draw Boss HUD health bar at top of screen
            bar_w = 80
            bar_h = 6
            bar_x = (surface.get_width() - bar_w) // 2
            bar_y = 14
            pygame.draw.rect(surface, COLOR_DARKEST, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
            pygame.draw.rect(surface, COLOR_DARK, (bar_x, bar_y, bar_w, bar_h))
            fill_w = int((self.hp / self.max_hp) * bar_w)
            if fill_w > 0:
                pygame.draw.rect(surface, COLOR_LIGHTEST, (bar_x, bar_y, fill_w, bar_h))
        elif self.hp < self.max_hp and self.is_alive:
            # Mini floating health bar above monster
            bar_w = max(12, self.fw)
            bar_x = sx
            bar_y = sy - 4
            pygame.draw.rect(surface, COLOR_DARKEST, (bar_x - 1, bar_y - 1, bar_w + 2, 4))
            pygame.draw.rect(surface, COLOR_DARK, (bar_x, bar_y, bar_w, 2))
            fill_w = int((self.hp / self.max_hp) * bar_w)
            if fill_w > 0:
                pygame.draw.rect(surface, COLOR_LIGHTEST, (bar_x, bar_y, fill_w, 2))
