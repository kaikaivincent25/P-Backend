"""
Centralized application configuration.

Everything that varies between environments (local, Render staging, Render
production) is read from environment variables here and nowhere else. This
keeps secrets out of source control and gives us one place to reason about
what the app depends on.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False

    # --- Database (Neon Postgres) ---
    # Neon gives you a `postgresql://` URL. We rewrite it to the asyncpg
    # driver at runtime (see database.py) rather than asking the user to
    # remember the right prefix.
    DATABASE_URL: str

    # --- Security ---
    # SECRET_KEY is reserved for anything needing signing (e.g. future JWTs,
    # signed cookies). Not required for the API-key admin auth used today,
    # but kept so we don't have to redeploy to add signed sessions later.
    SECRET_KEY: str
    ADMIN_API_KEY: str  # long random string, sent as `X-API-Key` header

    # --- CORS ---
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    # --- Email (contact form notifications) ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    OWNER_NOTIFICATION_EMAIL: EmailStr = "owner@example.com"
    CONTACT_FROM_EMAIL: EmailStr = "no-reply@example.com"
    EMAIL_ENABLED: bool = True  # set False in tests / local dev without SMTP creds

    # --- Rate limiting ---
    CONTACT_RATE_LIMIT: str = "5/hour"  # slowapi rate-limit string, per IP

    # --- Honeypot ---
    HONEYPOT_FIELD_NAME: str = "website"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> "Settings":
    """Cached so we parse the environment once per process, not per request."""
    return Settings()
