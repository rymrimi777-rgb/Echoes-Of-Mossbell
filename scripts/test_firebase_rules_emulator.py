"""
Firebase Realtime Database Security Rules & Client Integration Test Suite
Runs against the official Firebase Auth + Realtime Database Local Emulator Suite.

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
from game.network.room_manager import RoomManager
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


class EmuFirebaseClient(FirebaseClient):
    """Routes REST requests to the local RTDB Emulator namespace."""
    def _build_url(self, path, params=None):
        p = dict(params) if params else {}
        p["ns"] = NS
        return super()._build_url(path, params=p)


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
        check("1. FirebaseAuth anonymous sign-in (3 clients)", ok1 and ok2 and ok3, f"uids=({uid1}, {uid2}, {uid3})")

        c1 = EmuFirebaseClient(a1, base_url=DB_URL)
        c2 = EmuFirebaseClient(a2, base_url=DB_URL)
        c3 = EmuFirebaseClient(a3, base_url=DB_URL)

        rm1 = RoomManager(c1)
        rm2 = RoomManager(c2)
        rm3 = RoomManager(c3)

        # Unauthenticated access rejected
        st_ua_r, _, _ = raw_req("GET", "rooms/12345")
        st_ua_w, _, _ = raw_req("PUT", "rooms/12345", data={"status": "waiting"})
        check("2. Unauthenticated read & write rejected (401)", st_ua_r == 401 and st_ua_w == 401, f"r={st_ua_r}, w={st_ua_w}")

        # ETag null_etag check
        g_ok, g_val, g_etag = c1.get("rooms/77777", with_etag=True)
        check("3. GET empty path with X-Firebase-ETag returns null_etag", g_ok and g_val is None and g_etag == "null_etag", f"etag={g_etag}")

        # Creator claims p1 via RoomManager
        c_ok, rid = rm1.create_room("actor1_character_01", player_name="Ralph")
        check("4. Creator claims p1 via RoomManager.create_room", c_ok and len(rid) == 5, f"rid={rid}")

        # Conditional ETag overwrite returns 412
        st_dup, _, _ = raw_req("PUT", f"rooms/{rid}", token=a2.id_token, data={"status": "waiting"}, headers={"If-Match": "null_etag"})
        check("5. Conditional create PUT on existing room rejected with 412", st_dup == 412, f"st={st_dup}")

        # Another user attempting to claim/overwrite p1
        st_p1_hijack, _, _ = raw_req("PUT", f"rooms/{rid}/players/p1", token=a2.id_token, data={
            "uid": uid2, "character_id": "actor1_character_02", "x": 100, "y": 100, "connected": True
        })
        check("6. Another user claiming/overwriting p1 rejected (401)", st_p1_hijack == 401, f"st={st_p1_hijack}")

        # Host claiming both slots (self-join) blocked both client-side and rule-side
        self_ok, self_err = rm1.join_room(rid, "actor1_character_02", "RalphClone")
        st_host_p2, _, _ = raw_req("PUT", f"rooms/{rid}/players/p2", token=a1.id_token, data={
            "uid": uid1, "character_id": "actor1_character_02", "x": 176, "y": 144, "connected": True
        })
        check("7. Host claiming both slots rejected (client + rule 401)", (not self_ok) and self_err == "CANNOT_JOIN_OWN_ROOM" and st_host_p2 == 401, f"err={self_err}, st={st_host_p2}")

        # Non-member changing status waiting->playing before joining
        st_nonmember_stat, _, _ = raw_req("PUT", f"rooms/{rid}/status", token=a3.id_token, data="playing")
        # Host prematurely flipping waiting->playing before p2 exists
        st_host_premature, _, _ = raw_req("PUT", f"rooms/{rid}/status", token=a1.id_token, data="playing")
        check("8. Non-member & premature host status transitions rejected (401)", st_nonmember_stat == 401 and st_host_premature == 401, f"nonmember={st_nonmember_stat}, host={st_host_premature}")

        # Second player claiming p2 via RoomManager
        j2_ok, _ = rm2.join_room(rid, "actor1_character_02", player_name="Ulrika")
        check("9. Second player claims p2 & transitions status -> playing", j2_ok and rm2.local_slot == "p2")

        # Third player attempting to join & non-member reading active room & /rooms listing
        st_list, _, _ = raw_req("GET", "rooms", token=a3.id_token)
        st_read_active, _, _ = raw_req("GET", f"rooms/{rid}", token=a3.id_token)
        j3_ok, j3_err = rm3.join_room(rid, "actor1_character_03", "Intruder")
        st_p3_overwrite, _, _ = raw_req("PUT", f"rooms/{rid}/players/p2", token=a3.id_token, data={"uid": uid3, "character_id": "actor1_character_03", "x": 10, "y": 10, "connected": True})
        st_p3_slot, _, _ = raw_req("PUT", f"rooms/{rid}/players/p3", token=a3.id_token, data={"uid": uid3, "character_id": "actor1_character_03", "x": 10, "y": 10, "connected": True})
        check("10. Non-member read, /rooms listing, 3rd player join & p3 slot rejected",
              st_list == 401 and st_read_active == 401 and (not j3_ok) and j3_err == "ROOM_FULL" and st_p3_overwrite == 401 and st_p3_slot == 401,
              f"list={st_list}, read={st_read_active}, j3={j3_err}, p2_over={st_p3_overwrite}, p3={st_p3_slot}")

        # Player 2 modifying p1 & Player 1 modifying p2
        st_p2_mod_p1, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p1", token=a2.id_token, data={"x": 50.0})
        st_p1_mod_p2, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p2", token=a1.id_token, data={"x": 50.0})
        check("11. Cross-slot modification (P2->p1, P1->p2) rejected (401)", st_p2_mod_p1 == 401 and st_p1_mod_p2 == 401, f"p2->p1={st_p2_mod_p1}, p1->p2={st_p1_mod_p2}")

        # Player deleting another player's slot or entire room (and host deleting active p1)
        st_del_p1_by_p2, _, _ = raw_req("DELETE", f"rooms/{rid}/players/p1", token=a2.id_token)
        st_del_p2_by_p1, _, _ = raw_req("DELETE", f"rooms/{rid}/players/p2", token=a1.id_token)
        st_del_room_p1, _, _ = raw_req("DELETE", f"rooms/{rid}", token=a1.id_token)
        st_del_room_p2, _, _ = raw_req("DELETE", f"rooms/{rid}", token=a2.id_token)
        st_del_active_p1, _, _ = raw_req("DELETE", f"rooms/{rid}/players/p1", token=a1.id_token)
        check("12. Slot cross-deletes & active/entire room deletions rejected (401)",
              all(s == 401 for s in (st_del_p1_by_p2, st_del_p2_by_p1, st_del_room_p1, st_del_room_p2, st_del_active_p1)),
              f"statuses={(st_del_p1_by_p2, st_del_p2_by_p1, st_del_room_p1, st_del_room_p2, st_del_active_p1)}")

        # Simultaneous p2 claims
        rm_race_host = RoomManager(RoomManager(c1).client)
        ok_race, rid_race = rm_race_host.create_room("actor1_character_01", "HostRace")
        assert ok_race
        rm_r2 = RoomManager(EmuFirebaseClient(a2, base_url=DB_URL))
        rm_r3 = RoomManager(EmuFirebaseClient(a3, base_url=DB_URL))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fa = ex.submit(rm_r2.join_room, rid_race, "actor1_character_02", "P2")
            fb = ex.submit(rm_r3.join_room, rid_race, "actor1_character_03", "P3")
            ra = fa.result()
            rb = fb.result()
        wins = sum(1 for r in (ra, rb) if r[0] is True)
        losses = sum(1 for r in (ra, rb) if r[0] is False)
        check("13. Simultaneous p2 claims: exactly 1 succeeds, 1 fails", wins == 1 and losses == 1)

        # Schema validations (char ID, coords, map, direction, extra field)
        st_char, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p1", token=a1.id_token, data={"character_id": "boss"})
        st_pos, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p1", token=a1.id_token, data={"x": -10})
        st_map, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p1", token=a1.id_token, data={"map": "bad_map"})
        st_extra, _, _ = raw_req("PATCH", f"rooms/{rid}/players/p1", token=a1.id_token, data={"cheat": 999})
        check("14. Schema rules reject bad character_id, negative coord, bad map, extra key (401)",
              all(s == 401 for s in (st_char, st_pos, st_map, st_extra)))

        # Bidirectional NetworkWorker + Clean Disconnect
        nw1 = NetworkWorker(c1, rid, "p1", "p2")
        nw2 = NetworkWorker(c2, rid, "p2", "p1")
        nw1.start()
        nw2.start()
        nw1.queue_local_update({"character_id": "actor1_character_01", "x": 192.0, "y": 160.0, "direction": "right", "moving": True, "map": "ruins"})
        got = False
        deadline = time.time() + 3.5
        while time.time() < deadline and not got:
            for u in nw2.get_remote_updates():
                if u.get("x") == 192.0 and u.get("map") == "ruins":
                    got = True
            time.sleep(0.05)
        nw1.stop()
        nw2.stop()
        check("15. NetworkWorker live sync (including valid map 'ruins')", got)

        rm2.leave_room()
        rm1.leave_room()
        _, closed_room, _ = raw_req("GET", f"rooms/{rid}", token=a1.id_token)
        st_p3_closed, _, _ = raw_req("GET", f"rooms/{rid}", token=a3.id_token)
        check("16. Clean leave closes room & preserves slots; non-member blocked on closed room",
              closed_room.get("status") == "closed" and closed_room["players"]["p2"]["uid"] == uid2 and st_p3_closed == 401)

    print(f"\n=== ALL {len(results)} LIVE FIREBASE EMULATOR SECURITY TESTS PASSED ===")


if __name__ == "__main__":
    run_emulator_security_tests()
