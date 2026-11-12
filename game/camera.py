"""
Camera that follows the player and stays within map bounds.
"""
from game.settings import GAME_W, GAME_H, TILE_SIZE


class Camera:
    def __init__(self, map_w_tiles, map_h_tiles):
        self.x = 0
        self.y = 0
        self.map_pw = map_w_tiles * TILE_SIZE
        self.map_ph = map_h_tiles * TILE_SIZE

    def update(self, target_x, target_y):
        """Centre on the target, clamped to map edges."""
        self.x = target_x - GAME_W // 2 + TILE_SIZE // 2
        self.y = target_y - GAME_H // 2 + TILE_SIZE // 2
        # clamp
        self.x = max(0, min(self.x, self.map_pw - GAME_W))
        self.y = max(0, min(self.y, self.map_ph - GAME_H))

    def apply(self, x, y):
        """Return screen coords for a world position."""
        return x - self.x, y - self.y

    def apply_rect(self, rect):
        import pygame
        return pygame.Rect(rect.x - self.x, rect.y - self.y,
                           rect.width, rect.height)

