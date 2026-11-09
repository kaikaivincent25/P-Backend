"""
Admin auth via API key.

Why API key over HTTP Basic for this use case: this is a single-admin
portfolio backend with no user accounts to manage, so there's no real
username/password pair to check — Basic Auth would just mean comparing a
hardcoded username against a hardcoded password, which is API-key auth
with extra steps and a browser login-prompt UX we don't want on a JSON API.
An `X-API-Key` header is simpler to rotate, doesn't get cached by browsers,
and is what tools like Postman/curl/your own admin UI expect.

Security details that matter here:
- `secrets.compare_digest` for a constant-time comparison, so response
  timing can't be used to brute-force the key character by character.
- The key is never logged, never echoed back in error messages.
- 401 (not 403) on a missing/invalid key, matching HTTP semantics for
  "you didn't authenticate" vs "you're authenticated but not allowed".
"""
import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer_scheme = HTTPBearer(auto_error=False)
ADMIN_SESSION_TTL = 60 * 60 * 8


def create_admin_session() -> str:
    """Create an eight-hour signed bearer token for the dashboard."""
    settings = get_settings()
    payload = json.dumps(
        {"sub": "admin", "exp": int(time.time()) + ADMIN_SESSION_TTL},
        separators=(",", ":"),
    ).encode()
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode()
    signature = hmac.new(
        settings.SECRET_KEY.encode(), encoded_payload.encode(), hashlib.sha256
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{encoded_payload}.{encoded_signature}"


def _valid_admin_session(token: str) -> bool:
    settings = get_settings()
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode(), encoded_payload.encode(), hashlib.sha256
        ).digest()
        supplied_signature = base64.urlsafe_b64decode(
            encoded_signature + "=" * (-len(encoded_signature) % 4)
        )
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return False
        payload_bytes = base64.urlsafe_b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4)
        )
        payload = json.loads(payload_bytes)
        return (
            isinstance(payload, dict)
            and payload.get("sub") == "admin"
            and isinstance(payload.get("exp"), int)
            and payload["exp"] > int(time.time())
        )
    except (ValueError, TypeError, json.JSONDecodeError):
        return False


def require_admin(
    api_key: str | None = Security(_api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> None:
    settings = get_settings()
    api_key_valid = bool(
        api_key and secrets.compare_digest(api_key, settings.ADMIN_API_KEY)
    )
    session_valid = bool(
        credentials
        and credentials.scheme.lower() == "bearer"
        and _valid_admin_session(credentials.credentials)
    )
    if not (api_key_valid or session_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid admin credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
