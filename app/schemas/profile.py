from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.profile import AvailabilityStatus, SocialPlatform


class SocialLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: SocialPlatform
    value: str
    resolved_url: str
    display_order: int


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tagline: str
    bio: str
    education: str
    availability_status: AvailabilityStatus
    avatar_url: str | None
    resume_url: str | None
    updated_at: datetime
    social_links: list[SocialLinkOut] = []
