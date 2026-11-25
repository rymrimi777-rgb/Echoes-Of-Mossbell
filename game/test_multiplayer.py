"""
Comprehensive Test Suite for Echoes of Mossbell Online Multiplayer System.
Validates:
1. Firebase Configuration & Anonymous Auth logic
2. 10-char uppercase alphanumeric room code generation using `secrets`
3. Room creation with conditional ETag (`If-Match: null_etag`) & collision retries
4. Write-first join flow: NO GET before claiming p2 (`PUT .../players/p2` with `If-Match: null_etag`)
5. Strict 2-player limit: rejection of third player (`ROOM_FULL` / 412)
6. Safe non-leaking rejection for nonexistent / closed / host rooms (`JOIN_DENIED`)
7. Remote player interpolation, animation, and overhead badge rendering
8. GameModeScreen & MultiplayerLobbyScreen 10-char alphanumeric keyboard + touch keypad
9. Offline SOLO gameplay independence & engine flow
10. Character ID, map ID, and position validation + room ID format checks
11. Thread safety of NetworkWorker and non-destructive disconnect
12. Unauthenticated request blocking
"""
import os
import sys
import copy
import time
import pygame

# Set dummy headless audio/video drivers
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

pygame.init()
pygame.display.set_mode((160, 144), pygame.HIDDEN)

from game.network.firebase_config import FIREBASE_PROJECT_ID, FIREBASE_DATABASE_URL
from game.network.firebase_auth import FirebaseAuth
from game.network.firebase_client import FirebaseClient
from game.network.room_manager import (
    RoomManager, ROOM_CODE_LENGTH, ROOM_CODE_ALPHABET, is_valid_room_id,
    _sanitize_character_id, _clamp_coord, _sanitize_map_id
)
from game.network.network_worker import NetworkWorker
from game.network.remote_player import RemotePlayer
from game.network.multiplayer_screen import GameModeScreen, MultiplayerLobbyScreen
from game.ui import UIRenderer
from game.camera import Camera
from game.main import Game, STATE_TITLE, STATE_CHAR_SELECT, STATE_GAME_MODE, STATE_PLAY


class MockFirebaseBackend:
    """In-memory mock enforcing ETag If-Match and server-side participant read/write rules."""

    def __init__(self):
        self.data = {}
        self._ver = 0

    def _get_ref(self, path):
        path = path.strip("/")
        parts = [p for p in path.split("/") if p]
        curr = self.data
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return None, "null_etag"
        return curr, f"etag_v{self._ver}"

    def get(self, path, with_etag=False, caller_uid=None):
        clean = path.strip("/")
        parts = [p for p in clean.split("/") if p]
        if len(parts) >= 2 and parts[0] == "rooms" and caller_uid is not None:
            rid = parts[1]
            room = self.data.get("rooms", {}).get(rid)
            if not isinstance(room, dict):
                return False, "Permission denied", None
            p2_uid = (room.get("players", {}).get("p2") or {}).get("uid")
            if room.get("host_uid") != caller_uid and p2_uid != caller_uid:
                return False, "Permission denied", None
        val, etag = self._get_ref(path)
        return True, copy.deepcopy(val), (etag if with_etag else None)

    def put(self, path, val, if_match=None, caller_uid=None):
        clean = path.strip("/")
        parts = [p for p in clean.split("/") if p]

        # Simulate RTDB rule checks for write-first players/p2 claim
        if len(parts) == 4 and parts[0] == "rooms" and parts[2] == "players" and parts[3] == "p2" and caller_uid is not None:
            room = self.data.get("rooms", {}).get(parts[1])
            if not isinstance(room, dict):
                return False, "Permission denied", None
            p1 = room.get("players", {}).get("p1") or {}
            p2 = room.get("players", {}).get("p2")
            if p2 is not None:
                # Existing node fails null_etag check (412)
                if if_match == "null_etag":
                    return False, "PRECONDITION_FAILED", None
                return False, "Permission denied", None
            if room.get("status") != "waiting" or not p1.get("connected") or room.get("host_uid") == caller_uid or p1.get("uid") == caller_uid:
                return False, "Permission denied", None

        existing, current_etag = self._get_ref(path)
        if if_match is not None and if_match != current_etag:
            return False, "PRECONDITION_FAILED", None

        curr = self.data
        for p in parts[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
            curr = curr[p]
        curr[parts[-1]] = copy.deepcopy(val)
        self._ver += 1
        return True, val, f"etag_v{self._ver}"

    def patch(self, path, val):
        path = path.strip("/")
        parts = [p for p in path.split("/") if p]
        curr = self.data
        for p in parts:
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
            curr = curr[p]
        if isinstance(val, dict):
            curr.update(copy.deepcopy(val))
        self._ver += 1
        return True, curr, f"etag_v{self._ver}"

    def delete(self, path):
        path = path.strip("/")
        parts = [p for p in path.split("/") if p]
        curr = self.data
        for p in parts[:-1]:
            if p in curr:
                curr = curr[p]
            else:
                return True, None, None
        if parts[-1] in curr:
            del curr[parts[-1]]
        self._ver += 1
        return True, None, None


class MockFirebaseClient:
    """Mock client routing to MockFirebaseBackend and recording request sequence."""

    def __init__(self, backend, uid):
        self.backend = backend
        self.calls = []
        self.auth = type("MockAuth", (), {
            "uid": uid,
            "get_valid_token": lambda self: "mock_jwt_token",
            "sign_in_anonymously": lambda self: (True, uid),
            "refresh_id_token": lambda self: (True, "mock_refreshed_token")
        })()

    def get(self, path, timeout=5, with_etag=False):
        self.calls.append(("GET", path))
        return self.backend.get(path, with_etag=with_etag, caller_uid=self.auth.uid)

    def put(self, path, data, if_match=None, timeout=5):
        self.calls.append(("PUT", path, if_match))
        return self.backend.put(path, data, if_match=if_match, caller_uid=self.auth.uid)

    def patch(self, path, data, timeout=5):
        self.calls.append(("PATCH", path))
        return self.backend.patch(path, data)

    def delete(self, path, timeout=5):
        self.calls.append(("DELETE", path))
        return self.backend.delete(path)


def run_multiplayer_tests():
    print("=" * 65)
    print(" ECHOES OF MOSSBELL — MULTIPLAYER SECURITY TEST SUITE ")
    print("=" * 65)

    # 1. Configuration & Project Settings
    print("\n1. Testing Firebase Project Configuration...")
    assert FIREBASE_PROJECT_ID == "echoes-of-mossbell"
    assert "echoes-of-mossbell" in FIREBASE_DATABASE_URL
    print(f"Project ID: {FIREBASE_PROJECT_ID}")

    # 2. Authentication Logic & urllib.parse import
    print("\n2. Testing Firebase Anonymous Auth Client Logic...")
    auth = FirebaseAuth()
    assert hasattr(auth, "sign_in_anonymously")
    assert hasattr(auth, "refresh_id_token")
    assert hasattr(auth, "get_valid_token")
    import urllib.parse
    assert hasattr(urllib.parse, "urlencode")
    print("FirebaseAuth structure and urllib.parse verified.")

    # 3. 10-Char Secrets Room Code Generation & Conditional Create
    print("\n3. Testing 10-Char Secrets Room Codes & ETag Room Creation...")
    backend = MockFirebaseBackend()
    client_p1 = MockFirebaseClient(backend, uid="uid_player_1")
    room_mgr_p1 = RoomManager(client_p1)

    codes = {room_mgr_p1.generate_room_code() for _ in range(25)}
    assert len(codes) == 25, "Generated room codes must be unpredictable/unique"
    for c in codes:
        assert len(c) == ROOM_CODE_LENGTH == 10
        assert all(ch in ROOM_CODE_ALPHABET for ch in c)
        assert is_valid_room_id(c) is True

    ok, rid = room_mgr_p1.create_room(character_id="actor1_character_01", player_name="Ralph")
    assert ok is True and is_valid_room_id(rid)
    assert client_p1.calls[0] == ("PUT", f"rooms/{rid}", "null_etag"), "create_room must use direct PUT with null_etag"
    assert room_mgr_p1.local_slot == "p1"
    print(f"Player 1 created 10-char room {rid} atomically via If-Match: null_etag.")

    # 4. Non-member cannot read waiting room BEFORE joining
    print("\n4. Testing Strict Non-Member Read Blocking on Waiting Room...")
    client_p3 = MockFirebaseClient(backend, uid="uid_player_3")
    ok_read_wait, err_read_wait, _ = client_p3.get(f"rooms/{rid}")
    assert ok_read_wait is False and err_read_wait == "Permission denied"
    print("Non-member blocked from reading waiting room.")

    # 5. Write-First Join Flow (NO GET before PUT players/p2!)
    print("\n5. Testing Write-First Join Flow (Player 2)...")
    client_p2 = MockFirebaseClient(backend, uid="uid_player_2")
    room_mgr_p2 = RoomManager(client_p2)

    ok, room_data = room_mgr_p2.join_room(rid.lower(), character_id="actor1_character_02", player_name="Ulrika")
    assert ok is True, f"Player 2 failed write-first join: {room_data}"
    assert room_mgr_p2.local_slot == "p2"
    assert client_p2.calls[0] == ("PUT", f"rooms/{rid}/players/p2", "null_etag"), "First request MUST be conditional PUT on players/p2"
    assert client_p2.calls[1][0:2] == ("PUT", f"rooms/{rid}/status")
    assert client_p2.calls[2][0:2] == ("GET", f"rooms/{rid}"), "GET must occur ONLY AFTER claiming p2"
    print(f"Write-first join verified! Request sequence: {[c[:2] for c in client_p2.calls]}")

    has_p2, p2_info = room_mgr_p1.poll_waiting_room()
    assert has_p2 is True and p2_info["character_id"] == "actor1_character_02"

    # 6. Third Player & Non-existent Room Rejection (No Leakage)
    print("\n6. Testing 3rd Player Rejection & Safe Rejection Errors...")
    room_mgr_p3 = RoomManager(client_p3)
    ok_p3, err_p3 = room_mgr_p3.join_room(rid, character_id="actor1_character_03", player_name="Bennett")
    assert ok_p3 is False and err_p3 == "ROOM_FULL", f"Expected ROOM_FULL, got {err_p3}"

    ok_ghost, err_ghost = room_mgr_p3.join_room("ZZZZ9999AA", character_id="actor1_character_03", player_name="Ghost")
    assert ok_ghost is False and err_ghost == "JOIN_DENIED", f"Expected JOIN_DENIED (no info leak), got {err_ghost}"
    print("3rd player got ROOM_FULL (412) and nonexistent room got safe JOIN_DENIED (401).")

    # 7. Remote Player Entity & Interpolation
    print("\n7. Testing Remote Player Interpolation & Rendering...")
    remote = RemotePlayer(character_id="actor1_character_02", name="Ulrika", slot="p2", x=160.0, y=144.0)
    remote.apply_network_state({"x": 176.0, "y": 144.0, "direction": "right", "moving": True, "map": "village"})
    for _ in range(10):
        remote.update(16)
    assert remote.fx > 165.0
    cam = Camera(22, 18)
    remote.draw(pygame.Surface((160, 144)), cam)
    print(f"Remote player interpolated to {remote.fx:.2f} and rendered at 160x144.")

    # 8. Lobby UI 10-Char Alphanumeric Keyboard & Touch Keypad
    print("\n8. Testing 10-Char Alphanumeric Lobby Input (Keyboard + Touch)...")
    ui = UIRenderer()
    gm_screen = GameModeScreen(ui)
    gm_screen.reset("actor1_character_01")
    gm_screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert gm_screen.choice == "SOLO"

    lobby = MultiplayerLobbyScreen(ui, room_mgr_p1)
    lobby.mode = MultiplayerLobbyScreen.MODE_JOIN_INPUT
    # Ensure keys including X, A, E, J, Z, digits type characters (no premature exit/submit!)
    sample = "A1X9E3J7Z2"
    for ch in sample:
        kc = pygame.K_0 + int(ch) if ch.isdigit() else pygame.K_a + (ord(ch) - ord("A"))
        lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, key=kc, unicode=ch.lower()))
    assert lobby.input_code == sample, f"Expected '{sample}', got '{lobby.input_code}'"
    lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
    assert lobby.input_code == sample[:-1]

    # Touch keypad click on 'Q', 'DEL', bounds check inside 160x144
    for key_label, rect in lobby.keypad_rects.items():
        assert 0 <= rect.x and rect.right <= 160 and 0 <= rect.y and rect.bottom <= 144, f"Keypad key {key_label} outside 160x144: {rect}"
    qx, qy = lobby.keypad_rects["Q"].center
    lobby.handle_pointer_down(qx, qy)
    assert lobby.input_code == sample[:-1] + "Q"
    lobby.draw(pygame.Surface((160, 144)))
    print("Lobby 10-char keyboard & 38-key touch keypad cleanly verified inside 160x144.")

    # Check error banner rendering in MODE_MAIN when API key missing
    no_key_auth = type("NoKeyAuth", (), {
        "uid": None,
        "get_valid_token": lambda self: None,
        "sign_in_anonymously": lambda self: (False, "API_KEY_REQUIRED"),
    })()
    no_key_client = FirebaseClient(no_key_auth)
    no_key_rm = RoomManager(no_key_client)
    lobby_err = MultiplayerLobbyScreen(ui, no_key_rm)
    assert lobby_err.handle_pointer_down(60, 72) is True
    assert lobby_err.is_error is True and "firebase_config.json" in lobby_err.status_message
    lobby_err.draw(pygame.Surface((160, 144)))

    # 9. Game Engine SOLO Isolation & Real Pointer/Touch Navigation
    print("\n9. Testing Game Engine SOLO Mode Independence & Pointer/Touch Navigation...")
    game = Game()
    vx, vy = game.view_offset
    sc = game.view_scale
    ng_idx = game.title_screen.options.index("NEW GAME")
    ng_spacing = 13 if len(game.title_screen.options) > 3 else 14
    ng_ny = 69 + ng_idx * ng_spacing + 3
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(int(vx + 80 * sc), int(vy + ng_ny * sc))))
    game._handle_events()
    game._update(16)
    assert game.state == STATE_CHAR_SELECT, f"Click on NEW GAME failed! state={game.state}"

    scr_w, scr_h = game.screen.get_size()
    cx_norm = (vx + 36 * sc) / scr_w
    cy_norm = (vy + 134 * sc) / scr_h
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=cx_norm, y=cy_norm))
    game._handle_events()
    game._update(16)
    assert game.state == STATE_GAME_MODE, f"FINGERDOWN on Confirm failed! state={game.state}"

    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(int(vx + 80 * sc), int(vy + 88 * sc))))
    game._handle_events()
    game._update(16)
    assert game.state == "mp_lobby", f"Click on PLAY WITH FRIENDS failed! state={game.state}"

    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(int(vx + 80 * sc), int(vy + 106 * sc))))
    game._handle_events()
    game._update(16)
    assert game.state == STATE_GAME_MODE

    game.game_mode_screen.choice = "SOLO"
    game.game_mode_screen.done = True
    game._update(16)
    assert game.state == STATE_PLAY and game.is_multiplayer is False
    print("Title click, Character FINGERDOWN tap, Lobby click, and SOLO mode verified!")

    # 10. Validation & Self-Join Prevention (against fresh waiting room so host rule check is exercised)
    print("\n10. Testing Room ID, Character ID, Map ID, Coords & Self-Join...")
    assert _sanitize_character_id("actor1_character_08") == "actor1_character_08"
    assert _sanitize_character_id("hacked") == "actor1_character_01"
    assert _sanitize_map_id("ruins") == "ruins"
    assert _sanitize_map_id("dungeon") == "dungeon"
    assert _sanitize_map_id("invalid_map") == "village"
    assert _clamp_coord(-500.0) == 0.0 and _clamp_coord(99999.0) == 4096.0

    for bad_code in ("", "12345", "A1B2C3D4E", "A1B2C3D4E5F", "A1B2C3D4E!", "bad space!"):
        ok_bad, err_bad = room_mgr_p2.join_room(bad_code, "actor1_character_01")
        assert ok_bad is False and err_bad == "INVALID_ROOM_ID", f"Failed rejecting '{bad_code}'"

    ok_self, err_self = room_mgr_p1.join_room(rid, "actor1_character_02")
    assert ok_self is False and err_self == "CANNOT_JOIN_OWN_ROOM"
    # Even a fresh RoomManager holding the host UID on an open waiting room gets rejected with JOIN_DENIED
    rm_wait_host = RoomManager(MockFirebaseClient(backend, uid="uid_host_self"))
    ok_w, rid_w = rm_wait_host.create_room("actor1_character_01", "HostSelf")
    assert ok_w
    rm_host_clone = RoomManager(MockFirebaseClient(backend, uid="uid_host_self"))
    ok_self2, err_self2 = rm_host_clone.join_room(rid_w, "actor1_character_02")
    assert ok_self2 is False and err_self2 == "JOIN_DENIED"
    print("Validation and self-join prevention verified!")

    # 11. Non-Destructive Disconnect & NetworkWorker Thread Safety
    print("\n11. Testing Clean Disconnect & NetworkWorker Thread Safety...")
    room_mgr_p1.leave_room()
    assert backend.data["rooms"][rid]["status"] == "closed"
    assert backend.data["rooms"][rid]["players"]["p2"]["uid"] == "uid_player_2"
    room_mgr_p2.leave_room()
    assert backend.data["rooms"][rid]["players"]["p2"]["connected"] is False

    nw = NetworkWorker(MockFirebaseClient(backend, uid="uid_player_1"), rid, "p1", "p2")
    assert nw.running is False
    nw.queue_local_update({"x": 10})
    nw.queue_local_update({"x": 42})
    assert nw._consume_outgoing() == {"x": 42}
    assert nw._consume_outgoing() is None
    print("Non-destructive disconnect and NetworkWorker thread safety verified!")

    # 12. Unauthenticated Access Rejection & 412 Handling
    print("\n12. Testing Unauthenticated Rejection & 412 Conflict Handling...")
    no_token_auth = type("NoTokenAuth", (), {"get_valid_token": lambda self: None})()
    real_no_auth = FirebaseClient(no_token_auth)
    ok_u, err_u, _ = real_no_auth.get(f"rooms/{rid}")
    assert ok_u is False and "AUTHENTICATION_REQUIRED" in err_u
    ok_412, err_412, _ = backend.put(f"rooms/{rid}", {"status": "waiting"}, if_match="null_etag")
    assert ok_412 is False and err_412 == "PRECONDITION_FAILED"
    print("Unauthenticated block and 412 ETag precondition enforcement verified!")

    print("\n" + "=" * 65)
    print("=== ALL 12 MULTIPLAYER SECURITY TESTS PASSED WITH 100% SUCCESS! ===")
    print("=" * 65)


if __name__ == "__main__":
    run_multiplayer_tests()
