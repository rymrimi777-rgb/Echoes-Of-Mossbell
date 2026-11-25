"""
Background Network Worker Thread.
Handles asynchronous bidirectional synchronization with Firebase Realtime Database.
Prevents HTTP network calls from stalling or freezing the 60 FPS Pygame main thread.

Thread safety:
- Uses a threading.Lock to protect the latest-state slot from concurrent access.
- Outgoing state is stored in a single-slot variable (not a queue) to guarantee
  only the latest position is sent, eliminating stale-frame races.
- The stop() method uses an Event for clean, immediate shutdown.
"""
import time
import queue
import threading
from game.network.firebase_client import FirebaseClient
from game.network.room_manager import _sanitize_character_id, _clamp_coord, _sanitize_map_id


class NetworkWorker:
    """
    Background worker thread for asynchronous movement and state sync.
    - Sends local player position updates (~10-12 updates/sec).
    - Polls remote player state (~10 updates/sec).
    - Sends heartbeats when idle.
    - Detects remote player disconnects.
    """

    EVENT_PLAYER_JOINED = "player_joined"
    EVENT_PLAYER_LEFT = "player_left"
    EVENT_ROOM_CLOSED = "room_closed"
    EVENT_DISCONNECTED = "disconnected"
    EVENT_ERROR = "error"

    def __init__(self, firebase_client: FirebaseClient, room_id, local_slot, remote_slot):
        self.client = firebase_client
        self.room_id = room_id
        self.local_slot = local_slot
        self.remote_slot = remote_slot

        # Thread-safe single-slot for the latest outgoing state (replaces Queue)
        self._outgoing_lock = threading.Lock()
        self._outgoing_state = None

        self.incoming_queue = queue.Queue(maxsize=10)
        self.events_queue = queue.Queue(maxsize=20)

        self._stop_event = threading.Event()
        self._stop_event.set()  # Initially stopped; start() clears this
        self.thread = None

        self._last_send_time = 0.0
        self._last_poll_time = 0.0
        self._last_heartbeat_time = 0.0
        self._last_remote_seen = time.time()
        self._last_sent_state = None
        self._remote_left_emitted = False

    @property
    def running(self):
        return not self._stop_event.is_set()

    def start(self):
        """Starts the background networking thread."""
        if self.thread and self.thread.is_alive():
            return
        self._stop_event.clear()
        self._last_remote_seen = time.time()
        self._remote_left_emitted = False
        self.thread = threading.Thread(target=self._run, daemon=True, name="NetworkWorker")
        self.thread.start()

    def stop(self):
        """Stops the worker thread cleanly (waits longer than HTTP timeout)."""
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.5)
        self.thread = None

    def queue_local_update(self, state_dict):
        """Called by Pygame main thread to stage the latest local position (thread-safe)."""
        with self._outgoing_lock:
            self._outgoing_state = state_dict

    def _consume_outgoing(self):
        """Called by worker thread to atomically grab and clear the latest state."""
        with self._outgoing_lock:
            state = self._outgoing_state
            self._outgoing_state = None
            return state

    def get_remote_updates(self):
        """Called by Pygame main thread to fetch all fresh remote updates."""
        updates = []
        while not self.incoming_queue.empty():
            try:
                updates.append(self.incoming_queue.get_nowait())
            except queue.Empty:
                break
        return updates

    def get_events(self):
        """Called by Pygame main thread to read session events."""
        events = []
        while not self.events_queue.empty():
            try:
                events.append(self.events_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def _run(self):
        """Main loop of background networking thread."""
        send_interval = 0.09  # ~11 updates per second
        poll_interval = 0.10  # ~10 polls per second
        heartbeat_interval = 2.0  # Send heartbeat every 2 seconds if idle

        local_path = f"rooms/{self.room_id}/players/{self.local_slot}"
        remote_path = f"rooms/{self.room_id}/players/{self.remote_slot}"

        while not self._stop_event.is_set():
            now = time.time()

            # 1. Send outgoing updates (Local -> Firebase)
            send_due = (now - self._last_send_time) >= send_interval
            heartbeat_due = (now - self._last_heartbeat_time) >= heartbeat_interval

            pending_update = self._consume_outgoing()
            if pending_update:
                self._last_sent_state = pending_update

            if pending_update and send_due:
                payload = dict(pending_update)
                if "character_id" in payload:
                    payload["character_id"] = _sanitize_character_id(payload["character_id"])
                if "x" in payload:
                    payload["x"] = _clamp_coord(payload["x"])
                if "y" in payload:
                    payload["y"] = _clamp_coord(payload["y"])
                if "map" in payload:
                    payload["map"] = _sanitize_map_id(payload["map"])
                if "direction" in payload and payload["direction"] not in ("up", "down", "left", "right"):
                    payload["direction"] = "down"
                payload["last_seen"] = now
                payload["connected"] = True
                try:
                    ok, _, _ = self.client.patch(local_path, payload, timeout=3)
                except Exception:
                    pass
                self._last_send_time = now
                self._last_heartbeat_time = now

            elif heartbeat_due and self._last_sent_state:
                # Idle heartbeat
                payload = {
                    "last_seen": now,
                    "connected": True
                }
                try:
                    self.client.patch(local_path, payload, timeout=3)
                except Exception:
                    pass
                self._last_heartbeat_time = now

            # 2. Poll remote updates (Firebase -> Remote Player)
            if (now - self._last_poll_time) >= poll_interval:
                self._last_poll_time = now
                try:
                    ok, data, _ = self.client.get(remote_path, timeout=3)
                except Exception:
                    ok, data = False, None

                if ok and data:
                    self._last_remote_seen = now
                    try:
                        # Drain stale entries before inserting fresh data
                        while not self.incoming_queue.empty():
                            self.incoming_queue.get_nowait()
                        self.incoming_queue.put_nowait(data)
                    except queue.Full:
                        pass

                    if not data.get("connected", True) and not self._remote_left_emitted:
                        self._remote_left_emitted = True
                        self._emit_event(self.EVENT_PLAYER_LEFT, "Remote player disconnected")
                    elif data.get("connected", True):
                        self._remote_left_emitted = False

                elif ok and data is None:
                    # Remote slot removed cleanly
                    if not self._remote_left_emitted:
                        self._remote_left_emitted = True
                        self._emit_event(self.EVENT_PLAYER_LEFT, "Remote player disconnected")

                else:
                    # Check for timeout
                    if (now - self._last_remote_seen) > 12.0:
                        self._emit_event(self.EVENT_DISCONNECTED, "Connection to partner timed out")
                        self._last_remote_seen = now  # Reset to prevent spamming

            # Use Event.wait() for interruptible sleep (stops immediately when stop() is called)
            self._stop_event.wait(timeout=0.015)

    def _emit_event(self, event_type, data=None):
        try:
            self.events_queue.put_nowait((event_type, data))
        except queue.Full:
            pass
