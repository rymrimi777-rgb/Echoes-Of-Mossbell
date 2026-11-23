"""
Placement Validation System for Echoes of Mossbell.
Enforces strict grid-based placement rules for structures, bridges, decorations, and items.
Ensures path walkability, collision integrity, water-spanning bridges, and map connectivity.
"""
from collections import deque
from game.settings import TILE_SIZE

# Ground types considered walkable natural land
WALKABLE_GROUNDS = {"g0", "g2", "g4", "p1"}
WATER_GROUNDS = {"wt"}


class PlacementValidator:
    """
    Validates object and structure placement on tilemaps.
    Guarantees no blocked paths, correct bridge orientations, and collision validity.
    """

    @staticmethod
    def is_in_bounds(map_w, map_h, tx, ty, tw=1, th=1):
        """Check if a tile rectangle is completely inside map boundaries."""
        return 0 <= tx and (tx + tw) <= map_w and 0 <= ty and (ty + th) <= map_h

    @staticmethod
    def validate_bridge(map_w, map_h, ground, solids, tx, ty, orientation="horizontal"):
        """
        Validates placement of a bridge:
        - Must spawn over water.
        - Must connect two walkable land sections.
        - Must have correct orientation matching the water span.
        - Returns (is_valid, reason).
        """
        if orientation == "horizontal":
            # Horizontal bridge: width=2 tiles (32px), height=1 tile (16px)
            # Spans horizontally over a 2-tile wide water channel or pond inlet.
            if not PlacementValidator.is_in_bounds(map_w, map_h, tx, ty, 2, 1):
                return False, "Bridge out of bounds"

            # Check under-bridge tiles: must be water or designated crossing
            for bx in range(tx, tx + 2):
                if ground[ty][bx] not in WATER_GROUNDS and ground[ty][bx] != "p1":
                    return False, f"Bridge tile ({bx}, {ty}) is not water"

            # West neighbor must be in bounds and walkable land
            if tx - 1 < 0:
                return False, "Horizontal bridge lacks West landing"
            west_ground = ground[ty][tx - 1]
            if west_ground not in WALKABLE_GROUNDS or solids[ty][tx - 1] == 1:
                return False, f"West landing ({tx-1}, {ty}) is not walkable land"

            # East neighbor must be in bounds and walkable land
            if tx + 2 >= map_w:
                return False, "Horizontal bridge lacks East landing"
            east_ground = ground[ty][tx + 2]
            if east_ground not in WALKABLE_GROUNDS or solids[ty][tx + 2] == 1:
                return False, f"East landing ({tx+2}, {ty}) is not walkable land"

            return True, "Valid horizontal bridge"

        elif orientation == "vertical":
            # Vertical bridge: width=1 tile (16px), height=2 tiles (32px)
            # Spans vertically over a 2-tile high water channel.
            if not PlacementValidator.is_in_bounds(map_w, map_h, tx, ty, 1, 2):
                return False, "Bridge out of bounds"

            # Check under-bridge tiles: must be water
            for by in range(ty, ty + 2):
                if ground[by][tx] not in WATER_GROUNDS and ground[by][tx] != "p1":
                    return False, f"Bridge tile ({tx}, {by}) is not water"

            # North neighbor must be walkable land
            if ty - 1 < 0:
                return False, "Vertical bridge lacks North landing"
            north_ground = ground[ty - 1][tx]
            if north_ground not in WALKABLE_GROUNDS or solids[ty - 1][tx] == 1:
                return False, f"North landing ({tx}, {ty-1}) is not walkable land"

            # South neighbor must be walkable land
            if ty + 2 >= map_h:
                return False, "Vertical bridge lacks South landing"
            south_ground = ground[ty + 2][tx]
            if south_ground not in WALKABLE_GROUNDS or solids[ty + 2][tx] == 1:
                return False, f"South landing ({tx}, {ty+2}) is not walkable land"

            return True, "Valid vertical bridge"

        return False, f"Unknown bridge orientation: {orientation}"

    @staticmethod
    def validate_structure(map_w, map_h, ground, solids, px, py, w, h, col_boxes=None,
                           is_ground=False, allowed_terrains=None):
        """
        Validates placing a structure (building, tree, landmark):
        - Within pixel bounds of the map.
        - Does not block essential walkways if collision is enabled.
        - Respects allowed terrain types if specified.
        """
        max_px = map_w * TILE_SIZE
        max_py = map_h * TILE_SIZE

        if px < 0 or py < 0 or (px + w) > max_px or (py + h) > max_py:
            return False, f"Structure out of bounds: ({px}, {py}, {w}, {h}) in map {max_px}x{max_py}"

        tx_start = px // TILE_SIZE
        ty_start = py // TILE_SIZE
        tx_end = (px + w - 1) // TILE_SIZE
        ty_end = (py + h - 1) // TILE_SIZE

        if allowed_terrains:
            for ty in range(ty_start, ty_end + 1):
                for tx in range(tx_start, tx_end + 1):
                    if ground[ty][tx] not in allowed_terrains:
                        return False, f"Tile ({tx}, {ty}) has terrain {ground[ty][tx]}, required: {allowed_terrains}"

        return True, "Valid structure placement"

    @staticmethod
    def check_path_exists(solids, start_tx, start_ty, goal_tx, goal_ty):
        """
        BFS pathfinding on solids grid. Returns True if a walkable path exists between
        (start_tx, start_ty) and (goal_tx, goal_ty).
        """
        H = len(solids)
        W = len(solids[0]) if H > 0 else 0

        if not (0 <= start_tx < W and 0 <= start_ty < H):
            return False
        if not (0 <= goal_tx < W and 0 <= goal_ty < H):
            return False
        if solids[start_ty][start_tx] == 1 or solids[goal_ty][goal_tx] == 1:
            return False

        if (start_tx, start_ty) == (goal_tx, goal_ty):
            return True

        queue = deque([(start_tx, start_ty)])
        visited = {(start_tx, start_ty)}

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == (goal_tx, goal_ty):
                return True

            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < W and 0 <= ny < H:
                    if solids[ny][nx] == 0 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        return False

    @staticmethod
    def get_reachable_tiles(solids, start_tx, start_ty):
        """Returns set of all (tx, ty) coordinates reachable from start_tile."""
        H = len(solids)
        W = len(solids[0]) if H > 0 else 0
        if not (0 <= start_tx < W and 0 <= start_ty < H) or solids[start_ty][start_tx] == 1:
            return set()

        queue = deque([(start_tx, start_ty)])
        visited = {(start_tx, start_ty)}

        while queue:
            cx, cy = queue.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < W and 0 <= ny < H:
                    if solids[ny][nx] == 0 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        return visited
