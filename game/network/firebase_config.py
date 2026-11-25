"""
Firebase Configuration for Echoes of Mossbell Online Multiplayer.
Supports Windows desktop, Android APK, and offline testing environments.
"""
import os
import json
from game.settings import BASE_DIR, SAVE_DIR

# Firebase Project Configuration
FIREBASE_PROJECT_ID = "echoes-of-mossbell"
FIREBASE_DATABASE_URL = "https://echoes-of-mossbell-default-rtdb.firebaseio.com"

# Web API Key for Identity Toolkit (Anonymous Auth)
# Public client identifier for Firebase project 'echoes-of-mossbell';
# can still be overridden via FIREBASE_API_KEY env var or saves/firebase_config.json.
_DEFAULT_API_KEY = os.environ.get("FIREBASE_API_KEY", "AIzaSyA9T1e9noxiazIRtvnp4eSU5yiFlhRFHmA")


def get_config_file_path():
    candidates = [
        os.path.join(SAVE_DIR, "firebase_config.json"),
        os.path.join(BASE_DIR, "firebase_config.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[0]


def load_api_key():
    """Retrieves Web API key from environment, config file, or cache."""
    env_key = os.environ.get("FIREBASE_API_KEY")
    if env_key:
        return env_key.strip()

    cfg_path = get_config_file_path()
    if os.path.isfile(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                key = data.get("api_key") or data.get("apiKey") or data.get("web_api_key")
                if key:
                    return key.strip()
        except Exception:
            pass

    return _DEFAULT_API_KEY.strip()


def save_api_key(api_key):
    """Saves Web API key to local storage so user only has to provide it once."""
    cfg_path = get_config_file_path()
    try:
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({
                "project_id": FIREBASE_PROJECT_ID,
                "database_url": FIREBASE_DATABASE_URL,
                "api_key": api_key.strip()
            }, f, indent=2)
        return True
    except Exception:
        return False
