"""
Room Manager for 2-Player Online Multiplayer.
Handles room creation, unique room code generation, atomic slot validation,
rejection of third players, and room lifecycle management.
"""
import random
import time
from game.network.firebase_client import FirebaseClient


class RoomManager:
    """Manages creation, joining, atomic slot assignment, and closure of 2-player rooms."""

    def __init__(self, firebase_client: FirebaseClient):
        self.client = firebase_client
        self.current_room_id = None
        self.local_slot = None  # "p1" or "p2"
        self.remote_slot = None  # "p2" or "p1"
        self.remote_player_info = None

    @staticmethod
    def generate_room_code():
        """Generates a clean 5-digit room ID (e.g. '58291') easily typed on mobile and PC."""
        return str(random.randint(10000, 99999))

    def create_room(self, character_id, player_name="Player 1"):
        """
        Creates a new room on Firebase Realtime Database.
        Assigns creator as Player 1 (p1).
        Returns (success: bool, room_id_or_error: str).
        """
        if not self.client.auth.get_valid_token():
            ok, err = self.client.auth.sign_in_anonymously()
            if not ok:
                return False, f"AUTH_ERROR: {err}"

        uid = self.client.auth.uid
        room_id = self.generate_room_code()

        room_data = {
            "created_at": time.time(),
            "host_uid": uid,
            "status": "waiting",
            "max_players": 2,
            "players": {
                "p1": {
                    "uid": uid,
                    "name": player_name,
                    "character_id": character_id,
                    "x": 160.0,
                    "y": 144.0,
                    "direction": "down",
                    "moving": False,
                    "last_seen": time.time(),
                    "connected": True,
                    "map": "village"
                }
            }
        }

        # PUT rooms/{room_id}.json
        success, resp, _ = self.client.put(f"rooms/{room_id}", room_data)
        if not success:
            return False, f"CREATE_FAILED: {resp}"

        self.current_room_id = room_id
        self.local_slot = "p1"
        self.remote_slot = "p2"
        self.remote_player_info = None
        return True, room_id

    def join_room(self, room_id, character_id, player_name="Player 2"):
        """
        Validates room, enforces 2-player limit, and atomically claims slot p2.
        Returns (success: bool, room_data_or_error: str/dict).
        """
        clean_id = str(room_id).strip()
        if not clean_id:
            return False, "INVALID_ROOM_ID"

        if not self.client.auth.get_valid_token():
            ok, err = self.client.auth.sign_in_anonymously()
            if not ok:
                return False, f"AUTH_ERROR: {err}"

        uid = self.client.auth.uid

        # 1. Fetch room state
        success, room_data, etag = self.client.get(f"rooms/{clean_id}")
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

        # 3. Check if slot p2 is occupied (STRICT 2-PLAYER LIMIT)
        p2 = players.get("p2")
        now = time.time()
        if p2:
            # If p2 belongs to another user and was active recently -> Room is Full!
            if p2.get("uid") != uid and p2.get("connected") and (now - p2.get("last_seen", 0) < 15.0):
                return False, "ROOM_FULL"

        # 4. Atomic conditional claim of slot p2
        p2_data = {
            "uid": uid,
            "name": player_name,
            "character_id": character_id,
            "x": 176.0,
            "y": 144.0,
            "direction": "down",
            "moving": False,
            "last_seen": now,
            "connected": True,
            "map": "village"
        }

        # Safe slot PUT
        claim_ok, claim_resp, _ = self.client.put(f"rooms/{clean_id}/players/p2", p2_data)
        if not claim_ok:
            return False, f"CLAIM_FAILED: {claim_resp}"

        # Update room status to "playing"
        self.client.patch(f"rooms/{clean_id}", {"status": "playing"})

        self.current_room_id = clean_id
        self.local_slot = "p2"
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
        """Cleanly leaves the room and notifies the session."""
        if not self.current_room_id or not self.local_slot:
            return

        rid = self.current_room_id
        slot = self.local_slot

        try:
            # Mark self as disconnected
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
            self.remote_slot = None
            self.remote_player_info = None
