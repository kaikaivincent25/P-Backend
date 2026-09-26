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


from pydantic import BaseModel
from typing import Optional

class ContactMessageCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str
    intent: str
    honeypot: Optional[str] = None  # Replaced 'website' with 'honeypot'

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
