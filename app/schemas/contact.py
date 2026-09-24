"""
Contact form schemas.

Security notes:
- The honeypot field is declared as an ordinary optional string on the
  *input* schema, styled off-screen by the frontend. Real users never see
  or fill it; bots that auto-fill every field do. We check it in the
  router, not here, because "field is non-empty" should silently succeed
  (return 201, save nothing) rather than raise a validation error that
  would tip off a bot that it was detected.
- The input schema never exposes `status` or `id` — those are server-
  assigned. The output/admin schema is a separate model so a client can
  never set its own status via the create endpoint.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.contact import MessageStatus


class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    subject: str = Field(default="", max_length=200)
    message: str = Field(min_length=1, max_length=5000)
    intent: str | None = Field(default=None, max_length=100)

    # Honeypot: real users leave this blank. Name deliberately generic/
    # innocuous-looking on the frontend (e.g. "website"), configurable via
    # settings.HONEYPOT_FIELD_NAME so it's not hardcoded to one obvious name.
    website: str | None = Field(default=None, max_length=200)

    @field_validator("name", "subject", "message", "intent")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v


class ContactMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    subject: str
    message: str
    intent: str | None
    status: MessageStatus
    created_at: datetime


class ContactMessageStatusUpdate(BaseModel):
    """PATCH body — the only field an admin can change on a message."""
    status: MessageStatus
