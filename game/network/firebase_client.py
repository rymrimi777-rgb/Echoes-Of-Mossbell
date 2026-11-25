"""
Firebase Realtime Database REST Client.
Implements authenticated GET, PUT, PATCH, DELETE, and conditional requests (ETags).
Handles automatic token expiration recovery (HTTP 401) and atomic conditional operations.
100% standard library (urllib.request).
"""
import json
import ssl
import urllib.request
import urllib.error
import urllib.parse
from game.network.firebase_config import FIREBASE_DATABASE_URL

try:
    _SSL_CTX = ssl.create_default_context()
except Exception:
    _SSL_CTX = None


class FirebaseClient:
    """REST client for Firebase Realtime Database with auth token injection and ETag support."""

    def __init__(self, auth_manager, base_url=None):
        self.auth = auth_manager
        self.base_url = (base_url or FIREBASE_DATABASE_URL).rstrip("/")

    def _build_url(self, path, params=None):
        clean_path = path.strip("/")
        url = f"{self.base_url}/{clean_path}.json"
        query = {}
        token = self.auth.get_valid_token()
        if not token:
            raise ConnectionError("AUTHENTICATION_REQUIRED: No valid Firebase token available.")
        query["auth"] = token
        if params:
            query.update(params)
        if query:
            url += "?" + urllib.parse.urlencode(query)
        return url

    def _send_request(self, method, path, data=None, headers=None, if_match=None, timeout=6, retry_on_401=True):
        try:
            url = self._build_url(path)
        except ConnectionError as ce:
            return False, str(ce), None
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        if if_match:
            req_headers["If-Match"] = str(if_match)

        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                resp_bytes = resp.read()
                resp_text = resp_bytes.decode("utf-8") if resp_bytes else ""
                parsed = json.loads(resp_text) if resp_text else None
                etag = resp.headers.get("ETag")
                return True, parsed, etag
        except urllib.error.HTTPError as e:
            # Handle token expiration (HTTP 401)
            if e.code == 401 and retry_on_401:
                token_refreshed, _ = self.auth.refresh_id_token()
                if token_refreshed:
                    return self._send_request(method, path, data, headers, if_match, timeout, retry_on_401=False)

            # Precondition failed (ETag mismatch)
            if e.code == 412:
                return False, "PRECONDITION_FAILED", None

            try:
                err_body = json.loads(e.read().decode("utf-8"))
                err_msg = err_body.get("error", str(e))
            except Exception:
                err_msg = str(e)
            return False, err_msg, None
        except Exception as ex:
            return False, str(ex), None

    def get(self, path, timeout=6):
        """GET request. Returns (success: bool, data: any, etag: str)."""
        return self._send_request("GET", path, timeout=timeout)

    def put(self, path, data, if_match=None, timeout=6):
        """PUT request (replaces data at path). Supports conditional If-Match."""
        return self._send_request("PUT", path, data=data, if_match=if_match, timeout=timeout)

    def patch(self, path, data, timeout=6):
        """PATCH request (updates specified fields without overwriting siblings)."""
        return self._send_request("PATCH", path, data=data, timeout=timeout)

    def delete(self, path, timeout=6):
        """DELETE request. Removes data at path."""
        return self._send_request("DELETE", path, timeout=timeout)
