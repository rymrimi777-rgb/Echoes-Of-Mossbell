"""
Shared strict SSL/TLS context helper for Firebase HTTPS requests.

On desktop OSes, OpenSSL uses system root certificates automatically.
On Android (python-for-android / Buildozer), compiled OpenSSL has no default
CA trust store path, which causes CERTIFICATE_VERIFY_FAILED unless certifi or
Android CA directories are loaded explicitly while keeping full verification.
"""
import os
import ssl
from typing import Optional

_ANDROID_CA_DIRS = (
    "/apex/com.android.conscrypt/cacerts",
    "/system/etc/security/cacerts",
    "/etc/ssl/certs",
)


def get_ssl_context() -> Optional[ssl.SSLContext]:
    """Return a strict TLS context configured with certifi and system CA paths."""
    try:
        ctx = ssl.create_default_context()
    except Exception:
        return None

    try:
        import certifi
        cafile = certifi.where()
        if cafile and os.path.isfile(cafile):
            ctx.load_verify_locations(cafile=cafile)
    except Exception:
        pass

    for capath in _ANDROID_CA_DIRS:
        if os.path.isdir(capath):
            try:
                ctx.load_verify_locations(capath=capath)
            except Exception:
                pass

    return ctx
