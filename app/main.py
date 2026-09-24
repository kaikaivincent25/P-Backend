"""
Application entrypoint.

Wiring order matters:
  1. Create the app.
  2. Attach the rate limiter to app.state (slowapi's requirement) and
     register its exception handler, so a throttled request returns a
     clean 429 instead of an unhandled exception.
  3. CORS middleware — restricted to the exact origins in
     CORS_ALLOWED_ORIGINS (your deployed frontend + local dev), never "*",
     since the API accepts credentialless but PII-bearing POSTs.
  4. Include routers.
  5. A couple of small hardening touches: hide docs in production, add a
     baseline set of security response headers.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.core.rate_limit import limiter
from app.routers import contact, messages, profile, projects, skills

settings = get_settings()

app = FastAPI(
    title="Portfolio API",
    version="1.0.0",
    # Swagger/ReDoc are handy in dev but needlessly expose your schema
    # (including the shape of admin endpoints) to the public in prod.
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,   # no cookies/sessions in play — keep this False
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(profile.router)
app.include_router(skills.router)
app.include_router(projects.router)
app.include_router(contact.router)
app.include_router(messages.router)


@app.get("/health", tags=["health"])
async def health_check():
    """Simple liveness check for Render's health check / uptime monitors."""
    return {"status": "ok"}
