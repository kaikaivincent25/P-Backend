"""
ContactMessage model.

Uses a UUID primary key (rather than an auto-increment int) so message IDs
in emails/links can't be enumerated to guess how many contact submissions
the site has received, and can't be trivially incremented by a bot probing
`/api/messages/{id}/`.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessageStatus(str, enum.Enum):
    new = "new"
    read = "read"
    replied = "replied"
    archived = "archived"


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    subject: Mapped[str] = mapped_column(String(200), default="")
    message: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[MessageStatus] = mapped_column(default=MessageStatus.new, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    # Note: the honeypot field is deliberately NOT a column here — a
    # submission that trips the honeypot is never persisted at all (see
    # routers/contact.py). Storing it would mean spam bots' junk lives in
    # your DB right alongside real messages.
