"""
Firebase Realtime Database Security Rules & Client Integration Test Suite
Runs against the official Firebase Auth + Realtime Database Local Emulator Suite.

Verifies all 10 security criteria under live RTDB rule evaluation:
1. Non-member cannot read a waiting room
2. Non-member cannot list rooms
3. Valid second player can claim p2 without reading the room first (write-first join)
4. Third player cannot claim p2 or write p3
5. Host cannot join their own room (blocked both client-side and by RTDB rules)
6. Two simultaneous join attempts result in strictly 1 success, 1 rejection
7. Player cannot overwrite or delete another player's slot or the entire room
8. Existing host and player synchronization (poll_waiting_room, NetworkWorker, leave_room) works
9. Invalid room codes are rejected (client-side & RTDB rules)
10. Production Auth/ETag checks (`X-Firebase-ETag`, `null_etag`, HTTP `412`)

Usage:
    firebase emulators:exec --only auth,database --project echoes-of-mossbell "python scripts/test_firebase_rules_emulator.py"
"""
import os
import sys
import json
import time
import tempfile
import urllib.request
import urllib.error
import concurrent.futures

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from game.network.firebase_auth import FirebaseAuth
from game.network.firebase_client import FirebaseClient
from game.network.room_manager import RoomManager, ROOM_CODE_LENGTH, is_valid_room_id
from game.network.network_worker import NetworkWorker

AUTH_HOST = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
DB_HOST = os.environ.get("FIREBASE_DATABASE_EMULATOR_HOST", "127.0.0.1:9000")
AUTH_SIGNUP = f"http://{AUTH_HOST}/identitytoolkit.googleapis.com/v1/accounts:signUp?key=emulator-key"
AUTH_REFRESH = f"http://{AUTH_HOST}/securetoken.googleapis.com/v1/token?key=emulator-key"
DB_URL = f"http://{DB_HOST}"
NS = "echoes-of-mossbell-default-rtdb"


class EmuFirebaseAuth(FirebaseAuth):
    """Points Identity Toolkit REST endpoints to the local Auth Emulator."""
    AUTH_URL = AUTH_SIGNUP
    REFRESH_URL = AUTH_REFRESH

    def __init__(self, tmp_dir, idx):
        self.api_key = "emulator-key"
        self.uid = None
        self.id_token = None
        self.refresh_token = None
        self.expires_at = 0.0
        self.token_file = os.path.join(tmp_dir, f"emu_auth_{idx}.json")


class SpyEmuFirebaseClient(FirebaseClient):
    """Routes REST requests to the local RTDB Emulator namespace and logs method/path sequence."""
    def __init__(self, auth_manager, base_url=None):
        super().__init__(auth_manager, base_url=base_url)
        self.history = []

    def _build_url(self, path, params=None):
        p = dict(params) if params else {}
        p["ns"] = NS
        return super()._build_url(path, params=p)

    def _send_request(self, method, path, data=None, headers=None, if_match=None, timeout=6, retry_on_401=True):
        self.history.append((method, path.strip("/"), if_match))
        return super()._send_request(method, path, data, headers, if_match, timeout, retry_on_401)


def raw_req(method, path, token=None, data=None, headers=None):
    clean = path.strip("/")
    url = f"{DB_URL}/{clean}.json?ns={NS}"
    if token:
        url += f"&auth={token}"
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else None), dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else None
        except Exception:
            parsed = raw
        return e.code, parsed, dict(e.headers)


def run_emulator_security_tests():
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        assert cond, f"FAILED: {name} -> {detail}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        a1 = EmuFirebaseAuth(tmp_dir, 1)
        a2 = EmuFirebaseAuth(tmp_dir, 2)
        a3 = EmuFirebaseAuth(tmp_dir, 3)
        ok1, uid1 = a1.sign_in_anonymously()
        ok2, uid2 = a2.sign_in_anonymously()
        ok3, uid3 = a3.sign_in_anonymously()
        check("T1. 3 real Anonymous Auth sessions via Auth Emulator", ok1 and ok2 and ok3, f"uids=({uid1}, {uid2}, {uid3})")

        c1 = SpyEmuFirebaseClient(a1, base_url=DB_URL)
        c2 = SpyEmuFirebaseClient(a2, base_url=DB_URL)
        c3 = SpyEmuFirebaseClient(a3, base_url=DB_URL)

        rm1 = RoomManager(c1)
        rm2 = RoomManager(c2)
        rm3 = RoomManager(c3)

        # Unauthenticated read/write blocked
        st_ua_r, _, _ = raw_req("GET", "rooms/ABCD123456")
        st_ua_w, _, _ = raw_req("PUT", "rooms/ABCD123456", data={"status": "waiting"})
        check("T2. Unauthenticated read & write rejected (401)", st_ua_r == 401 and st_ua_w == 401, f"r={st_ua_r}, w={st_ua_w}")

        # Host creates 10-char alphanumeric room atomically via If-Match: null_etag
        c_ok, rid = rm1.create_room("actor1_character_01", player_name="Ralph")
        check("T3. Creator creates 10-char room via RoomManager.create_room",
              c_ok and len(rid) == ROOM_CODE_LENGTH and is_valid_room_id(rid), f"rid={rid}")

        # Requirement 2: Non-member cannot list /rooms
        st_list_p2, _, _ = raw_req("GET", "rooms", token=a2.id_token)
        st_list_p3, _, _ = raw_req("GET", "rooms", token=a3.id_token)
        check("T4. Non-member cannot list /rooms (401)", st_list_p2 == 401 and st_list_p3 == 401)

        # Requirement 1: Non-member CANNOT read waiting room (before P2 joins!)
        st_wait_read_p2, _, _ = raw_req("GET", f"rooms/{rid}", token=a2.id_token)
        st_wait_read_p3, _, _ = raw_req("GET", f"rooms/{rid}", token=a3.id_token)
        st_wait_read_p1_node, _, _ = raw_req("GET", f"rooms/{rid}/players/p1", token=a2.id_token)
        check("T5. Non-member CANNOT read waiting room or waiting p1 (401)",
              st_wait_read_p2 == 401 and st_wait_read_p3 == 401 and st_wait_read_p1_node == 401,
              f"p2={st_wait_read_p2}, p3={st_wait_read_p3}, p1node={st_wait_read_p1_node}")

        # Host can read own waiting room via poll_waiting_room
        has_p2_early, _ = rm1.poll_waiting_room()
        check("T6. Host can poll own waiting room cleanly (has_p2=False)", has_p2_early is False)

        # Existing room overwrite/collision blocked: non-owner gets 401 (no data leak); owner gets 412 (ETag mismatch)
        st_dup_other, _, _ = raw_req("PUT", f"rooms/{rid}", token=a2.id_token, data={"status": "waiting"}, headers={"If-Match": "null_etag"})
        st_dup_self, _, _ = raw_req("PUT", f"rooms/{rid}", token=a1.id_token, data={"status": "waiting"}, headers={"If-Match": "null_etag"})
        check("T7. Conditional PUT on existing room rejected (other=401, owner ETag=412)",
              st_dup_other == 401 and st_dup_self == 412,
              f"other={st_dup_other}, self={st_dup_self}")

        # Requirement 5: Host cannot join their own room (client + separate instance hitting RTDB rules)
        self_ok, self_err = rm1.join_room(rid, "actor1_character_02", "RalphClone")
        rm1_clone = RoomManager(SpyEmuFirebaseClient(a1, base_url=DB_URL))
        self2_ok, self2_err = rm1_clone.join_room(rid, "actor1_character_02", "RalphClone2")
        check("T8. Host cannot join own room (client CANNOT_JOIN_OWN_ROOM + server 401 JOIN_DENIED)",
              (not self_ok) and self_err == "CANNOT_JOIN_OWN_ROOM" and (not self2_ok) and self2_err == "JOIN_DENIED",
              f"err1={self_err}, err2={self2_err}")

        # Requirement 9: Invalid room codes rejected both client-side and by Firebase RTDB rules
        bad_client_results = [rm2.join_room(b, "actor1_character_02") for b in ("12345", "SHORT", "A1B2C3D4E!", "TOOLONG1234")]
        st_bad_id1, _, _ = raw_req("PUT", "rooms/12345", token=a2.id_token, data={"status": "waiting"})
        st_bad_id2, _, _ = raw_req("PUT", "rooms/lowercase1", token=a2.id_token, data={"status": "waiting"})
        check("T9. Invalid room codes rejected client-side (INVALID_ROOM_ID) and server-side (401)",
              all((not ok and err == "INVALID_ROOM_ID") for ok, err in bad_client_results)
              and st_bad_id1 == 401 and st_bad_id2 == 401)

        # Nonexistent room returns safe JOIN_DENIED without leaking existence
        ghost_ok, ghost_err = rm2.join_room("ZZZZZ99999", "actor1_character_02")
        check("T10. Nonexistent 10-char room returns safe JOIN_DENIED", (not ghost_ok) and ghost_err == "JOIN_DENIED", f"err={ghost_err}")

        # Requirement 3: Valid P2 claims p2 WITHOUT reading room first (write-first flow!)
        c2.history.clear()
        j2_ok, j2_data = rm2.join_room(rid, "actor1_character_02", player_name="Ulrika")
        check("T11. Write-first join succeeds for P2 and order is [PUT p2(null_etag), PUT status, GET room]",
              j2_ok
              and rm2.local_slot == "p2"
              and c2.history[0] == ("PUT", f"rooms/{rid}/players/p2", "null_etag")
              and c2.history[1] == ("PUT", f"rooms/{rid}/status", None)
              and c2.history[2] == ("GET", f"rooms/{rid}", None)
              and j2_data.get("players", {}).get("p1", {}).get("uid") == uid1,
              f"seq={c2.history}")

        # Requirement 4: Third player CANNOT claim p2 or write p3 or read active room
        j3_ok, j3_err = rm3.join_room(rid, "actor1_character_03", "Intruder")
        st_p3_read, _, _ = raw_req("GET", f"rooms/{rid}", token=a3.id_token)
        st_p3_slot, _, _ = raw_req("PUT", f"rooms/{rid}/players/p3", token=a3.id_token, data={
            "uid": uid3, "character_id": "actor1_character_03", "x": 10, "y": 10, "connected": True
        })
        check("T12. Third player blocked from joining, reading active room, or writing p3",
              (not j3_ok) and j3_err in ("ROOM_FULL", "JOIN_DENIED") and st_p3_read == 401 and st_p3_slot == 401,
              f"j3_err={j3_err}, read={st_p3_read}, p3_slot={st_p3_slot}")

        # Requirement 7: Player cannot overwrite/delete another player's slot or entire room
        st_p1_over_p2, _, _ = raw_req("PUT", f"rooms/{rid}/players/p2", token=a1.id_token, data={"uid": uid1})
        st_p2_over_p1, _, _ = raw_req("PUT", f"rooms/{rid}/players/p1", token=a2.id_token, data={"uid": uid2})
        st_p2_patch_p1, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p1", token=a2.id_token, data={"x": 99.0})
        st_p1_patch_p2, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p2", token=a1.id_token, data={"x": 99.0})
        st_del_p1_by_p2, _, _ = raw_req("DELETE", f"rooms/{rid}/players/p1", token=a2.id_token)
        st_del_p2_by_p1, _, _ = raw_req("DELETE", f"rooms/{rid}/players/p2", token=a1.id_token)
        st_del_room_p1, _, _ = raw_req("DELETE", f"rooms/{rid}", token=a1.id_token)
        st_del_room_p2, _, _ = raw_req("DELETE", f"rooms/{rid}", token=a2.id_token)
        st_del_active_p1, _, _ = raw_req("DELETE", f"rooms/{rid}/players/p1", token=a1.id_token)
        st_status_p3, _, _ = raw_req("PUT", f"rooms/{rid}/status", token=a3.id_token, data="closed")
        check("T13. Cross-slot overwrites, deletions, active/room deletions & non-member status all rejected (401)",
              all(s == 401 for s in (
                  st_p1_over_p2, st_p2_over_p1, st_p2_patch_p1, st_p1_patch_p2,
                  st_del_p1_by_p2, st_del_p2_by_p1, st_del_room_p1, st_del_room_p2,
                  st_del_active_p1, st_status_p3
              )))

        # Requirement 6: Two simultaneous join attempts result in strictly 1 success & 1 failure
        rm_race_host = RoomManager(SpyEmuFirebaseClient(a1, base_url=DB_URL))
        ok_race, rid_race = rm_race_host.create_room("actor1_character_01", "RaceHost")
        assert ok_race
        rm_r2 = RoomManager(SpyEmuFirebaseClient(a2, base_url=DB_URL))
        rm_r3 = RoomManager(SpyEmuFirebaseClient(a3, base_url=DB_URL))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fa = ex.submit(rm_r2.join_room, rid_race, "actor1_character_02", "P2")
            fb = ex.submit(rm_r3.join_room, rid_race, "actor1_character_03", "P3")
            ra = fa.result()
            rb = fb.result()
        wins = sum(1 for r in (ra, rb) if r[0] is True)
        losses = sum(1 for r in (ra, rb) if r[0] is False and r[1] in ("ROOM_FULL", "JOIN_DENIED"))
        check("T14. Simultaneous p2 claims: strictly 1 succeeds and 1 rejected safely",
              wins == 1 and losses == 1, f"ra={ra[0]}({ra[1] if not ra[0] else 'OK'}), rb={rb[0]}({rb[1] if not rb[0] else 'OK'})")

        # Requirement 8: Existing host & player sync works (poll_waiting_room, NetworkWorker, leave_room)
        has_p2, p2_info = rm1.poll_waiting_room()
        check("T15a. Host poll_waiting_room sees joined P2", has_p2 and p2_info.get("uid") == uid2)

        nw1 = NetworkWorker(c1, rid, "p1", "p2")
        nw2 = NetworkWorker(c2, rid, "p2", "p1")
        nw1.start()
        nw2.start()
        nw1.queue_local_update({"character_id": "actor1_character_01", "x": 208.0, "y": 144.0, "direction": "right", "moving": True, "map": "forest"})
        nw2.queue_local_update({"character_id": "actor1_character_02", "x": 192.0, "y": 160.0, "direction": "left", "moving": True, "map": "village"})
        got1, got2 = False, False
        deadline = time.time() + 4.0
        while time.time() < deadline and not (got1 and got2):
            for u in nw2.get_remote_updates():
                if u.get("x") == 208.0 and u.get("map") == "forest":
                    got1 = True
            for u in nw1.get_remote_updates():
                if u.get("x") == 192.0 and u.get("map") == "village":
                    got2 = True
            time.sleep(0.05)
        nw1.stop()
        nw2.stop()
        check("T15b. Bidirectional NetworkWorker sync works under updated rules", got1 and got2)

        rm2.leave_room()
        rm1.leave_room()
        _, closed_data, _ = raw_req("GET", f"rooms/{rid}", token=a1.id_token)
        st_p3_closed, _, _ = raw_req("GET", f"rooms/{rid}", token=a3.id_token)
        check("T15c. Clean disconnect sets status=closed, preserves slots, blocks non-member reads",
              closed_data.get("status") == "closed" and closed_data["players"]["p2"]["uid"] == uid2 and st_p3_closed == 401)

    print(f"\n=== ALL {len(results)} LIVE FIREBASE EMULATOR SECURITY TESTS PASSED ===")


if __name__ == "__main__":
    run_emulator_security_tests()
