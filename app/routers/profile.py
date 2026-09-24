from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/", response_model=ProfileOut)
async def get_profile(db: AsyncSession = Depends(get_db)):
    stmt = select(Profile).options(selectinload(Profile.social_links)).where(Profile.id == 1)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile has not been set up yet.")
    return profile
