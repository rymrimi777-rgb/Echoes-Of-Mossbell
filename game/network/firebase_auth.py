"""
Firebase Anonymous Authentication REST Client.
Uses the Google Identity Toolkit REST API to authenticate anonymously,
securely store tokens, and automatically refresh expired ID tokens.
100% standard-library Python compatible with Windows and Android (no third-party dependencies).
"""
import os
import json
import time
import ssl
import urllib.request
import urllib.error
from game.network.firebase_config import load_api_key, save_api_key
from game.settings import SAVE_DIR

# SSL context for cross-platform HTTPS (works on Windows, Linux, Android)
try:
    _SSL_CTX = ssl.create_default_context()
except Exception:
    _SSL_CTX = None


class FirebaseAuth:
    """Manages Firebase Anonymous Authentication state, token caching, and refreshes."""

    AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={key}"
    REFRESH_URL = "https://securetoken.googleapis.com/v1/token?key={key}"

    def __init__(self, api_key=None):
        self.api_key = api_key or load_api_key()
        self.uid = None
        self.id_token = None
        self.refresh_token = None
        self.expires_at = 0.0
        self.token_file = os.path.join(SAVE_DIR, "auth_cache.json")
        self._load_cached_tokens()

    def _load_cached_tokens(self):
        if os.path.isfile(self.token_file):
            try:
                with open(self.token_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.uid = data.get("uid")
                    self.id_token = data.get("id_token")
                    self.refresh_token = data.get("refresh_token")
                    self.expires_at = data.get("expires_at", 0.0)
            except Exception:
                pass

    def _save_cached_tokens(self):
        try:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, "w", encoding="utf-8") as f:
                json.dump({
                    "uid": self.uid,
                    "id_token": self.id_token,
                    "refresh_token": self.refresh_token,
                    "expires_at": self.expires_at
                }, f, indent=2)
        except Exception:
            pass

    def is_authenticated(self):
        return bool(self.uid and self.id_token and time.time() < self.expires_at)

    def sign_in_anonymously(self, api_key=None, timeout=8):
        """
        Signs in anonymously using Firebase Identity Toolkit REST API.
        Returns (success: bool, uid_or_error: str).
        """
        key = api_key or self.api_key or load_api_key()
        if not key:
            return False, "API_KEY_REQUIRED"

        self.api_key = key
        url = self.AUTH_URL.format(key=key)
        payload = json.dumps({"returnSecureToken": True}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as response:
                body = json.loads(response.read().decode("utf-8"))
                self.id_token = body.get("idToken")
                self.refresh_token = body.get("refreshToken")
                self.uid = body.get("localId")
                expires_in = float(body.get("expiresIn", 3600))
                self.expires_at = time.time() + expires_in - 120.0  # 2 minute safety margin
                self._save_cached_tokens()
                return True, self.uid
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode("utf-8"))
                msg = err_data.get("error", {}).get("message", str(e))
            except Exception:
                msg = str(e)
            return False, msg
        except Exception as ex:
            return False, str(ex)

    def refresh_id_token(self, timeout=8):
        """Refreshes the Firebase ID token using the saved refresh token."""
        if not self.refresh_token:
            return self.sign_in_anonymously(timeout=timeout)

        key = self.api_key or load_api_key()
        if not key:
            return False, "API_KEY_REQUIRED"

        url = self.REFRESH_URL.format(key=key)
        form_data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as response:
                body = json.loads(response.read().decode("utf-8"))
                self.id_token = body.get("id_token")
                self.refresh_token = body.get("refresh_token", self.refresh_token)
                self.uid = body.get("user_id", self.uid)
                expires_in = float(body.get("expires_in", 3600))
                self.expires_at = time.time() + expires_in - 120.0
                self._save_cached_tokens()
                return True, self.id_token
        except Exception:
            # Fall back to re-signing in anonymously
            return self.sign_in_anonymously(timeout=timeout)

    def get_valid_token(self, timeout=8):
        """Returns a valid ID token, refreshing or authenticating if necessary."""
        now = time.time()
        if self.id_token and now < self.expires_at:
            return self.id_token

        if self.refresh_token:
            success, _ = self.refresh_id_token(timeout=timeout)
            if success:
                return self.id_token

        success, _ = self.sign_in_anonymously(timeout=timeout)
        if success:
            return self.id_token

        return None
