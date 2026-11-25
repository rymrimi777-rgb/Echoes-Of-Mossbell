"""
Room Manager for 2-Player Online Multiplayer.
Handles room creation, cryptographically random 10-char alphanumeric room codes,
write-first atomic slot claims, rejection of third players, and room lifecycle management.

Security:
- Generates 10-char uppercase alphanumeric room IDs via Python's `secrets` module.
- Uses ETag conditional writes (If-Match: null_etag) for atomic room creation and slot claims.
- Does NOT read `/rooms/{roomId}` before claiming slot `p2` (prevents unauthorized waiting-room reads).
- Validates character_id against the known character registry and clamps position data.
- Verifies UID ownership before writing to any player slot.
"""
import secrets
import string
import time
from game.network.firebase_client import FirebaseClient

ROOM_CODE_LENGTH = 10
ROOM_CODE_ALPHABET = string.ascii_uppercase + string.digits
_ROOM_CODE_CHARS = frozenset(ROOM_CODE_ALPHABET)


def is_valid_room_id(room_id):
    """Validates a 10-character uppercase alphanumeric room ID."""
    if not isinstance(room_id, str):
        return False
    clean = room_id.strip().upper()
    return len(clean) == ROOM_CODE_LENGTH and all(ch in _ROOM_CODE_CHARS for ch in clean)


# Valid character IDs from the character registry
VALID_CHARACTER_IDS = frozenset([
    "actor1_character_01", "actor1_character_02", "actor1_character_03",
    "actor1_character_04", "actor1_character_05", "actor1_character_06",
    "actor1_character_07", "actor1_character_08",
])

# Valid map IDs matching game/world.py build_all_maps()
VALID_MAP_IDS = frozenset([
    "village", "player_house", "elder_house", "forest",
    "deep_forest", "ruins", "dungeon", "grotto",
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
        """Generates a cryptographically random 10-character uppercase alphanumeric Room ID."""
        return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))

    def create_room(self, character_id, player_name="Player 1"):
        """
        Creates a new room on Firebase Realtime Database using conditional ETag writes
        (If-Match: null_etag). Assigns creator as Player 1 (p1).
        Returns (success: bool, room_id_or_error: str).
        """
        if not self.client.auth.get_valid_token():
            ok, err = self.client.auth.sign_in_anonymously()
            if not ok:
                return False, f"AUTH_ERROR: {err}"

        uid = self.client.auth.uid
        character_id = _sanitize_character_id(character_id)
        last_error = "Could not generate a unique room code after retries"

        for _attempt in range(self.MAX_CREATE_RETRIES):
            room_id = self.generate_room_code()
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

            # Direct conditional PUT with If-Match: null_etag (no prior GET needed)
            success, resp, _ = self.client.put(f"rooms/{room_id}", room_data, if_match="null_etag")
            if not success:
                last_error = str(resp)
                if resp == "PRECONDITION_FAILED" or "Permission denied" in last_error:
                    # Existing room collision (412 from own ETag or 401 hiding another host's room) -> retry
                    continue
                return False, f"CREATE_FAILED: {resp}"

            self.current_room_id = room_id
            self.local_slot = "p1"
            self.local_uid = uid
            self.remote_slot = "p2"
            self.remote_player_info = None
            return True, room_id

        return False, f"CREATE_FAILED: {last_error}"

    def join_room(self, room_id, character_id, player_name="Player 2"):
        """
        Write-first atomic join flow:
        - Does NOT GET /rooms/{roomId} before claiming p2.
        - Directly sends PUT /rooms/{roomId}/players/p2 with If-Match: null_etag.
        - Firebase server rules validate room existence, waiting status, host connectivity,
          host_uid != auth.uid, and empty p2 slot.
        - Only after claiming p2 does it transition status -> playing and GET room data.
        Returns (success: bool, room_data_or_error: str/dict).
        """
        clean_id = str(room_id).strip().upper()
        if not is_valid_room_id(clean_id):
            return False, "INVALID_ROOM_ID"

        if not self.client.auth.get_valid_token():
            ok, err = self.client.auth.sign_in_anonymously()
            if not ok:
                return False, f"AUTH_ERROR: {err}"

        uid = self.client.auth.uid
        character_id = _sanitize_character_id(character_id)

        # Prevent same RoomManager instance from joining its own hosted room
        if self.current_room_id == clean_id and self.local_slot == "p1":
            return False, "CANNOT_JOIN_OWN_ROOM"

        now = time.time()
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

        # 1. Direct conditional PUT on players/p2 with If-Match: null_etag (NO prior GET!)
        claim_ok, claim_resp, _ = self.client.put(
            f"rooms/{clean_id}/players/p2",
            p2_data,
            if_match="null_etag"
        )
        if not claim_ok:
            err_str = str(claim_resp)
            if claim_resp == "PRECONDITION_FAILED":
                return False, "ROOM_FULL"
            if "Permission denied" in err_str:
                # Safe non-leaking rejection (does not expose room existence/status/host)
                return False, "JOIN_DENIED"
            return False, f"CLAIM_FAILED: {err_str}"

        # 2. Transition room status to "playing" directly at /status
        status_ok, status_resp, _ = self.client.put(f"rooms/{clean_id}/status", "playing")
        if not status_ok:
            return False, f"STATUS_FAILED: {status_resp}"

        # 3. Claim succeeded -> now read room data as an authorized member (p2)
        read_ok, room_data, _ = self.client.get(f"rooms/{clean_id}")
        if not read_ok or not room_data:
            return False, f"JOIN_READ_FAILED: {room_data}"

        p1 = room_data.get("players", {}).get("p1")
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
        """Cleanly leaves the room. Only modifies the local player's own slot (never deletes room)."""
        if not self.current_room_id or not self.local_slot:
            return

        rid = self.current_room_id
        slot = self.local_slot
        local_uid = self.local_uid

        try:
            # Verify local UID ownership before updating slot
            if self.client.auth.uid == local_uid:
                self.client.patch(f"rooms/{rid}/players/{slot}", {
                    "connected": False,
                    "last_seen": time.time()
                }, timeout=3)

                # If Host leaves, close the room directly via /status
                if slot == "p1":
                    self.client.put(f"rooms/{rid}/status", "closed", timeout=3)
        except Exception:
            pass
        finally:
            self.current_room_id = None
            self.local_slot = None
            self.local_uid = None
            self.remote_slot = None
            self.remote_player_info = None
