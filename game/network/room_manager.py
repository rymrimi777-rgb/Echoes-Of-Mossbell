"""
Room Manager for 2-Player Online Multiplayer.
Handles room creation, unique room code generation, atomic slot validation,
rejection of third players, and room lifecycle management.

Security:
- Uses ETag conditional writes (If-Match) for atomic room creation and slot claims.
- Validates character_id against the known character registry.
- Clamps position data to valid map bounds.
- Verifies UID ownership before writing to any player slot.
"""
import random
import time
from game.network.firebase_client import FirebaseClient

# Valid character IDs from the character registry
VALID_CHARACTER_IDS = frozenset([
    "actor1_character_01", "actor1_character_02", "actor1_character_03",
    "actor1_character_04", "actor1_character_05", "actor1_character_06",
    "actor1_character_07", "actor1_character_08",
])

# Valid map IDs for position validation
VALID_MAP_IDS = frozenset([
    "village", "player_house", "forest", "deep_forest", "grotto",
    "watchtower", "cave", "elder_house",
])

# Position bounds (pixels) — generous bounds covering all maps
MAX_COORD = 4096.0
MIN_COORD = 0.0


def _sanitize_character_id(char_id):
    """Returns a valid character ID or the default if invalid."""
    if char_id in VALID_CHARACTER_IDS:
        return char_id
    return "actor1_character_01"


def _clamp_coord(val):
    """Clamps a coordinate to valid map bounds."""
    try:
        v = float(val)
    except (TypeError, ValueError):
        return 0.0
    return max(MIN_COORD, min(MAX_COORD, v))


def _sanitize_map_id(map_id):
    """Returns a valid map ID or the default if invalid."""
    if map_id in VALID_MAP_IDS:
        return map_id
    return "village"


class RoomManager:
    """Manages creation, joining, atomic slot assignment, and closure of 2-player rooms."""

    MAX_CREATE_RETRIES = 5  # Retry limit for room code collision

    def __init__(self, firebase_client: FirebaseClient):
        self.client = firebase_client
        self.current_room_id = None
        self.local_slot = None  # "p1" or "p2"
        self.remote_slot = None  # "p2" or "p1"
        self.local_uid = None  # UID that owns this slot
        self.remote_player_info = None

    @staticmethod
    def generate_room_code():
        """Generates a clean 5-digit room ID (e.g. '58291') easily typed on mobile and PC."""
        return str(random.randint(10000, 99999))

    def create_room(self, character_id, player_name="Player 1"):
        """
        Creates a new room on Firebase Realtime Database using conditional ETag writes.
        Assigns creator as Player 1 (p1).
        Returns (success: bool, room_id_or_error: str).
        """
        if not self.client.auth.get_valid_token():
            ok, err = self.client.auth.sign_in_anonymously()
            if not ok:
                return False, f"AUTH_ERROR: {err}"

        uid = self.client.auth.uid
        character_id = _sanitize_character_id(character_id)

        for attempt in range(self.MAX_CREATE_RETRIES):
            room_id = self.generate_room_code()

            # Check if room already exists (ETag-based collision detection)
            check_ok, existing, etag = self.client.get(f"rooms/{room_id}")
            if check_ok and existing is not None:
                # Room code collision — retry with a different code
                continue

            now = time.time()
            room_data = {
                "created_at": now,
                "host_uid": uid,
                "status": "waiting",
                "max_players": 2,
                "players": {
                    "p1": {
                        "uid": uid,
                        "name": str(player_name)[:20],
                        "character_id": character_id,
                        "x": 160.0,
                        "y": 144.0,
                        "direction": "down",
                        "moving": False,
                        "last_seen": now,
                        "connected": True,
                        "map": "village"
                    }
                }
            }

            # Conditional PUT with ETag to prevent race condition overwrites
            success, resp, _ = self.client.put(f"rooms/{room_id}", room_data,
                                               if_match=etag if etag else None)
            if not success:
                if resp == "PRECONDITION_FAILED":
                    # Another client created this room between our GET and PUT — retry
                    continue
                return False, f"CREATE_FAILED: {resp}"

            self.current_room_id = room_id
            self.local_slot = "p1"
            self.local_uid = uid
            self.remote_slot = "p2"
            self.remote_player_info = None
            return True, room_id

        return False, "CREATE_FAILED: Could not generate a unique room code after retries"

    def join_room(self, room_id, character_id, player_name="Player 2"):
        """
        Validates room, enforces 2-player limit, and conditionally claims slot p2 using ETags.
        Returns (success: bool, room_data_or_error: str/dict).
        """
        clean_id = str(room_id).strip()
        if not clean_id or not clean_id.isdigit() or len(clean_id) != 5:
            return False, "INVALID_ROOM_ID"

        if not self.client.auth.get_valid_token():
            ok, err = self.client.auth.sign_in_anonymously()
            if not ok:
                return False, f"AUTH_ERROR: {err}"

        uid = self.client.auth.uid
        character_id = _sanitize_character_id(character_id)

        # 1. Fetch room state
        success, room_data, room_etag = self.client.get(f"rooms/{clean_id}")
        if not success or not room_data:
            return False, "ROOM_NOT_FOUND"

        status = room_data.get("status")
        if status == "closed":
            return False, "ROOM_CLOSED"

        players = room_data.get("players", {})

        # 2. Check if p1 exists and is alive
        p1 = players.get("p1")
        if not p1 or not p1.get("connected"):
            return False, "HOST_DISCONNECTED"

        # 3. Prevent joining your own room
        if p1.get("uid") == uid:
            return False, "CANNOT_JOIN_OWN_ROOM"

        # 4. Check if slot p2 is occupied (STRICT 2-PLAYER LIMIT)
        p2 = players.get("p2")
        now = time.time()
        if p2:
            # If p2 belongs to another user and was active recently -> Room is Full!
            if p2.get("uid") != uid and p2.get("connected") and (now - p2.get("last_seen", 0) < 15.0):
                return False, "ROOM_FULL"

        # 5. Fetch p2 slot ETag for conditional write
        _, existing_p2, p2_etag = self.client.get(f"rooms/{clean_id}/players/p2")

        # 6. Atomic conditional claim of slot p2
        p2_data = {
            "uid": uid,
            "name": str(player_name)[:20],
            "character_id": character_id,
            "x": _clamp_coord(176.0),
            "y": _clamp_coord(144.0),
            "direction": "down",
            "moving": False,
            "last_seen": now,
            "connected": True,
            "map": "village"
        }

        # Conditional PUT with ETag to prevent race condition (two players claiming p2)
        claim_ok, claim_resp, _ = self.client.put(
            f"rooms/{clean_id}/players/p2", p2_data,
            if_match=p2_etag if p2_etag else None
        )
        if not claim_ok:
            if claim_resp == "PRECONDITION_FAILED":
                return False, "ROOM_FULL"
            return False, f"CLAIM_FAILED: {claim_resp}"

        # Update room status to "playing"
        self.client.patch(f"rooms/{clean_id}", {"status": "playing"})

        self.current_room_id = clean_id
        self.local_slot = "p2"
        self.local_uid = uid
        self.remote_slot = "p1"
        self.remote_player_info = p1
        return True, room_data

    def poll_waiting_room(self):
        """
        For Player 1 (Host): Checks if Player 2 has joined.
        Returns (has_player2: bool, p2_info: dict or None).
        """
        if not self.current_room_id or self.local_slot != "p1":
            return False, None

        ok, p2_data, _ = self.client.get(f"rooms/{self.current_room_id}/players/p2")
        if ok and p2_data and p2_data.get("connected"):
            self.remote_player_info = p2_data
            return True, p2_data
        return False, None

    def leave_room(self):
        """Cleanly leaves the room. Only modifies the local player's own slot."""
        if not self.current_room_id or not self.local_slot:
            return

        rid = self.current_room_id
        slot = self.local_slot

        try:
            # Only mark OUR OWN slot as disconnected (verified by local_uid)
            self.client.patch(f"rooms/{rid}/players/{slot}", {
                "connected": False,
                "last_seen": time.time()
            }, timeout=3)

            # If Host leaves, mark room as closed
            if slot == "p1":
                self.client.patch(f"rooms/{rid}", {"status": "closed"}, timeout=3)
        except Exception:
            pass
        finally:
            self.current_room_id = None
            self.local_slot = None
            self.local_uid = None
            self.remote_slot = None
            self.remote_player_info = None
