"""
Save / Load system – JSON-based, stored in saves/ folder.
"""
import os, json, time, pygame
from game.settings import SAVE_DIR, IS_ANDROID


class SaveSystem:
    def __init__(self):
        save_folder = SAVE_DIR
        if IS_ANDROID:
            android_private = os.environ.get("ANDROID_PRIVATE", "")
            if not android_private and "ANDROID_ARGUMENT" in os.environ:
                android_private = os.environ["ANDROID_ARGUMENT"]
            if android_private:
                save_folder = os.path.join(android_private, "saves")
        try:
            if hasattr(pygame, "system") and hasattr(pygame.system, "get_pref_path"):
                pref = pygame.system.get_pref_path("MossbellGames", "EchoesOfMossbell")
                if pref:
                    save_folder = pref
        except Exception:
            pass
        self.save_dir = save_folder
        try:
            os.makedirs(self.save_dir, exist_ok=True)
        except Exception:
            pass

    def _path(self, slot=0):
        return os.path.join(self.save_dir, f"save_{slot}.json")

    def _char_pref_path(self):
        return os.path.join(self.save_dir, "selected_character.json")

    def get_selected_character(self):
        """Restores previously chosen character ID, persisting across restarts."""
        p = self._char_pref_path()
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    char_id = data.get("character_id")
                    if char_id:
                        return char_id
            except Exception:
                pass
        # Fallback to save_0 if present
        data0 = self.load(0)
        if data0 and "character_id" in data0:
            return data0["character_id"]
        return "actor1_character_01"

    def save_selected_character(self, character_id):
        """Saves player character preference locally (Windows & Android compatible)."""
        p = self._char_pref_path()
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"character_id": str(character_id), "timestamp": time.time()}, f, indent=2)
            return True
        except Exception:
            return False

    def save(self, game_state, slot=0):
        data = {
            "timestamp": time.time(),
            "player_x": game_state.get("player_x", 0),
            "player_y": game_state.get("player_y", 0),
            "player_dir": game_state.get("player_dir", "down"),
            "player_hp": game_state.get("player_hp", 20),
            "character_id": game_state.get("character_id", self.get_selected_character()),
            "variant": game_state.get("variant", "gameboy"),
            "current_map": game_state.get("current_map", "village"),
            "inventory": game_state.get("inventory", {}),
            "quests": game_state.get("quests", {}),
            "flags": game_state.get("flags", {}),
            "play_time": game_state.get("play_time", 0),
        }
        with open(self._path(slot), "w") as f:
            json.dump(data, f, indent=2)
        # Also persist character preference
        self.save_selected_character(data["character_id"])
        return True

    def load(self, slot=0):
        path = self._path(slot)
        if not os.path.isfile(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def exists(self, slot=0):
        return os.path.isfile(self._path(slot))

    def delete(self, slot=0):
        path = self._path(slot)
        if os.path.isfile(path):
            os.remove(path)

    def get_info(self, slot=0):
        data = self.load(slot)
        if data is None:
            return None
        return {
            "slot": slot,
            "map": data.get("current_map", "?"),
            "play_time": data.get("play_time", 0),
        }

