from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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


class SocialLinkUpdate(BaseModel):
    platform: SocialPlatform
    value: str = Field(min_length=1, max_length=255)
    display_order: int = 0


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    tagline: str | None = Field(default=None, max_length=255)
    bio: str | None = None
    education: str | None = None
    availability_status: AvailabilityStatus | None = None
    avatar_url: str | None = Field(default=None, max_length=500)
    resume_url: str | None = Field(default=None, max_length=500)
    social_links: list[SocialLinkUpdate] | None = None
