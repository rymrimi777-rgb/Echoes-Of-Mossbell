"""
Background Network Worker Thread.
Handles asynchronous bidirectional synchronization with Firebase Realtime Database.
Prevents HTTP network calls from stalling or freezing the 60 FPS Pygame main thread.
"""
import time
import queue
import threading
from game.network.firebase_client import FirebaseClient


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

        self.outgoing_queue = queue.Queue(maxsize=10)
        self.incoming_queue = queue.Queue(maxsize=10)
        self.events_queue = queue.Queue(maxsize=20)

        self.running = False
        self.thread = None

        self._last_send_time = 0.0
        self._last_poll_time = 0.0
        self._last_heartbeat_time = 0.0
        self._last_remote_seen = time.time()
        self._last_local_state = None

    def start(self):
        """Starts the background networking thread."""
        if self.running:
            return
        self.running = True
        self._last_remote_seen = time.time()
        self.thread = threading.Thread(target=self._run, daemon=True, name="NetworkWorker")
        self.thread.start()

    def stop(self):
        """Stops the worker thread cleanly."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)

    def queue_local_update(self, state_dict):
        """Called by Pygame main thread to stage the latest local position."""
        try:
            # Keep only the freshest update
            while not self.outgoing_queue.empty():
                self.outgoing_queue.get_nowait()
            self.outgoing_queue.put_nowait(state_dict)
        except Exception:
            pass

    def get_remote_updates(self):
        """Called by Pygame main thread to fetch all fresh remote updates."""
        updates = []
        while not self.incoming_queue.empty():
            try:
                updates.append(self.incoming_queue.get_nowait())
            except Exception:
                break
        return updates

    def get_events(self):
        """Called by Pygame main thread to read session events."""
        events = []
        while not self.events_queue.empty():
            try:
                events.append(self.events_queue.get_nowait())
            except Exception:
                break
        return events

    def _run(self):
        """Main loop of background networking thread."""
        send_interval = 0.09  # ~11 updates per second
        poll_interval = 0.10  # ~10 polls per second
        heartbeat_interval = 2.0  # Send heartbeat every 2 seconds if idle

        local_path = f"rooms/{self.room_id}/players/{self.local_slot}"
        remote_path = f"rooms/{self.room_id}/players/{self.remote_slot}"

        while self.running:
            now = time.time()

            # 1. Send outgoing updates (Local -> Firebase)
            send_due = (now - self._last_send_time) >= send_interval
            heartbeat_due = (now - self._last_heartbeat_time) >= heartbeat_interval

            pending_update = None
            try:
                pending_update = self.outgoing_queue.get_nowait()
                self._last_local_state = pending_update
            except queue.Empty:
                pass

            if pending_update and send_due:
                payload = dict(pending_update)
                payload["last_seen"] = now
                payload["connected"] = True
                ok, _, _ = self.client.patch(local_path, payload, timeout=3)
                self._last_send_time = now
                self._last_heartbeat_time = now

            elif heartbeat_due and self._last_local_state:
                # Idle heartbeat
                payload = {
                    "last_seen": now,
                    "connected": True
                }
                self.client.patch(local_path, payload, timeout=3)
                self._last_heartbeat_time = now

            # 2. Poll remote updates (Firebase -> Remote Player)
            if (now - self._last_poll_time) >= poll_interval:
                self._last_poll_time = now
                ok, data, _ = self.client.get(remote_path, timeout=3)
                if ok and data:
                    self._last_remote_seen = now
                    try:
                        while not self.incoming_queue.empty():
                            self.incoming_queue.get_nowait()
                        self.incoming_queue.put_nowait(data)
                    except Exception:
                        pass

                    if not data.get("connected", True):
                        self._emit_event(self.EVENT_PLAYER_LEFT, "Remote player disconnected")

                else:
                    # Check for timeout
                    if (now - self._last_remote_seen) > 12.0:
                        self._emit_event(self.EVENT_DISCONNECTED, "Connection to partner timed out")
                        self._last_remote_seen = now  # Reset to prevent spamming

            time.sleep(0.015)

    def _emit_event(self, event_type, data=None):
        try:
            self.events_queue.put_nowait((event_type, data))
        except Exception:
            pass
