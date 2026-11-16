"""
Collision helpers – axis-aligned bounding-box checks against map solids and boundaries.
"""
import pygame
from game.settings import TILE_SIZE


class CollisionMap:
    """
    Stores a 2-D boolean grid: True = solid tile.
    Also keeps a list of rects for prop-level colliders.
    """

    def __init__(self, w_tiles, h_tiles):
        self.w = w_tiles
        self.h = h_tiles
        self.grid = [[False] * w_tiles for _ in range(h_tiles)]
        self.extra_rects = []  # list[pygame.Rect]

    def set_solid(self, tx, ty, solid=True):
        if 0 <= tx < self.w and 0 <= ty < self.h:
            self.grid[ty][tx] = solid

    def is_solid(self, tx, ty):
        if tx < 0 or ty < 0 or tx >= self.w or ty >= self.h:
            return True  # out-of-bounds = solid
        return self.grid[ty][tx]

    def add_rect(self, rect):
        self.extra_rects.append(rect)

    def can_move(self, rect, dx, dy):
        """
        Check if *rect* moved by (dx, dy) would collide.
        Resolves X and Y axes independently to allow sliding along walls.
        """
        # Check X axis
        if dx != 0:
            test_x = pygame.Rect(rect.x + dx, rect.y, rect.width, rect.height)
            if self._collides(test_x):
                dx = 0

        # Check Y axis
        if dy != 0:
            test_y = pygame.Rect(rect.x + dx, rect.y + dy, rect.width, rect.height)
            if self._collides(test_y):
                dy = 0

        return dx, dy

    def _collides(self, rect):
        # Strict boundary check: out of map bounds is strictly solid
        if rect.left < 0 or rect.top < 0 or rect.right > self.w * TILE_SIZE or rect.bottom > self.h * TILE_SIZE:
            return True

        # Tile grid check
        left   = max(0, rect.left   // TILE_SIZE)
        right  = min(self.w - 1, (rect.right - 1) // TILE_SIZE)
        top    = max(0, rect.top    // TILE_SIZE)
        bottom = min(self.h - 1, (rect.bottom - 1) // TILE_SIZE)

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if self.grid[ty][tx]:
                    tile_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(tile_rect):
                        return True

        # Extra prop/furniture rects
        for er in self.extra_rects:
            if rect.colliderect(er):
                return True

        return False
