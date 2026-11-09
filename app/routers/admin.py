import secrets

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import ADMIN_SESSION_TTL, create_admin_session
from app.schemas.admin import AdminLogin, AdminSessionOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/session/", response_model=AdminSessionOut)
@limiter.limit("5/minute")
async def create_session(request: Request, payload: AdminLogin):
    settings = get_settings()
    if not secrets.compare_digest(payload.api_key, settings.ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AdminSessionOut(
        access_token=create_admin_session(),
        expires_in=ADMIN_SESSION_TTL,
    )
