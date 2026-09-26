"""
Public contact endpoint.

Order of operations matters here for both security and UX:
  1. Rate limit check (slowapi) — rejected before we do any work at all.
  2. Honeypot check — if tripped, we return 201 immediately, WITHOUT
     touching the database. Returning a normal-looking success response
     (rather than a 400) is deliberate: a bot that gets a 4xx learns to
     adjust; a bot that gets a 201 has no signal that anything went wrong,
     so it has no reason to change behavior or retry harder.
  3. Save to DB — only real, honeypot-clean submissions are persisted.
  4. Queue the owner-notification email as a BackgroundTask, so the
     visitor's request returns as soon as the DB write succeeds; SMTP
     latency or a transient SMTP outage never affects their experience.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.email import send_contact_notification
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.contact import ContactMessage
from app.schemas.contact import ContactMessageCreate, ContactMessageOut

router = APIRouter(prefix="/api/contact", tags=["contact"])
settings = get_settings()


@router.post("/", response_model=ContactMessageOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.CONTACT_RATE_LIMIT)
async def submit_contact_message(
    request: Request,  # required by slowapi's decorator, even though unused directly
    payload: ContactMessageCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # FIX 1: Match the field name sent by your React frontend ('honeypot' instead of 'website')
    if payload.honeypot:  # honeypot tripped — pretend success, save nothing
        return ContactMessageOut(
            id=uuid.uuid4(),
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            subject=payload.subject,
            message=payload.message,
            intent=payload.intent,
            status="new",
            created_at=datetime.now(timezone.utc),
        )

    message = ContactMessage(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        subject=payload.subject,
        message=payload.message,
        intent=payload.intent,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    # FIX 2: Convert to a plain dictionary so the background task doesn't crash 
    # when the database session closes after returning the 201 response.
    message_data = {
        "id": str(message.id),
        "name": message.name,
        "email": message.email,
        "phone": message.phone,
        "subject": message.subject,
        "message": message.message,
        "intent": message.intent,
    }

    background_tasks.add_task(send_contact_notification, message_data)
    
    return message