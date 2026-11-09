from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_admin
from app.database import get_db
from app.models.profile import Profile, SocialLink
from app.schemas.profile import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/", response_model=ProfileOut)
async def get_profile(db: AsyncSession = Depends(get_db)):
    stmt = select(Profile).options(selectinload(Profile.social_links)).where(Profile.id == 1)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile has not been set up yet.")
    return profile


@router.patch("/", response_model=ProfileOut, dependencies=[Depends(require_admin)])
async def update_profile(payload: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Profile).options(selectinload(Profile.social_links)).where(Profile.id == 1)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile has not been set up yet.")

    updates = payload.model_dump(exclude_unset=True)
    social_links = updates.pop("social_links", None)
    if "social_links" in payload.model_fields_set and social_links is None:
        raise HTTPException(status_code=422, detail="social_links must be a list.")

    for field, value in updates.items():
        if value is None and field not in {"avatar_url", "resume_url"}:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null.")
        setattr(profile, field, value)

    if social_links is not None:
        profile.social_links = [SocialLink(**link) for link in social_links]

    await db.commit()
    await db.refresh(profile, attribute_names=["social_links"])
    return profile
