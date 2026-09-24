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
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_admin(api_key: str | None = Security(_api_key_header)) -> None:
    settings = get_settings()
    if not api_key or not secrets.compare_digest(api_key, settings.ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
            headers={"WWW-Authenticate": "API-Key"},
        )
