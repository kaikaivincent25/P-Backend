"""
Admin-only endpoints for triaging contact messages.

Every route here depends on `require_admin`, which validates the
`X-API-Key` header (see core/security.py). There is no public read access
to contact messages at all — not even a "your message was received" lookup
by ID — since messages can contain PII (email, phone) volunteered by
strangers on the internet.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin
from app.database import get_db
from app.models.contact import ContactMessage, MessageStatus
from app.schemas.contact import ContactMessageOut, ContactMessageStatusUpdate

router = APIRouter(
    prefix="/api/messages",
    tags=["messages (admin)"],
    dependencies=[Depends(require_admin)],
)


@router.get("/", response_model=list[ContactMessageOut])
async def list_messages(
    status_filter: MessageStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ContactMessage).order_by(ContactMessage.created_at.desc())
    if status_filter is not None:
        stmt = stmt.where(ContactMessage.status == status_filter)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{message_id}/", response_model=ContactMessageOut)
async def update_message_status(
    message_id: uuid.UUID,
    payload: ContactMessageStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    message = await db.get(ContactMessage, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    message.status = payload.status
    await db.commit()
    await db.refresh(message)
    return message
