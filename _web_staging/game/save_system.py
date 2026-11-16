"""
Save / Load system – JSON-based, stored in saves/ folder.
"""
import os, json, time, pygame
from game.settings import SAVE_DIR


class SaveSystem:
    def __init__(self):
        save_folder = SAVE_DIR
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

    def save(self, game_state, slot=0):
        data = {
            "timestamp": time.time(),
            "player_x": game_state.get("player_x", 0),
            "player_y": game_state.get("player_y", 0),
            "player_dir": game_state.get("player_dir", "down"),
            "current_map": game_state.get("current_map", "village"),
            "inventory": game_state.get("inventory", {}),
            "quests": game_state.get("quests", {}),
            "flags": game_state.get("flags", {}),
            "play_time": game_state.get("play_time", 0),
        }
        with open(self._path(slot), "w") as f:
            json.dump(data, f, indent=2)
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

