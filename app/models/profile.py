"""
Profile + SocialLink models.

Profile is designed as a "singleton" table: the app only ever reads/writes
row id=1. We enforce that with a CHECK constraint rather than trusting
application code, so a bug can't accidentally create a second profile row.
"""
import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AvailabilityStatus(str, enum.Enum):
    available = "available"
    open_to_offers = "open_to_offers"
    unavailable = "unavailable"


class SocialPlatform(str, enum.Enum):
    github = "github"
    linkedin = "linkedin"
    twitter = "twitter"
    email = "email"
    website = "website"
    other = "other"


# Base URLs used to build `resolved_url` when the stored value is a bare
# handle (e.g. "yourname") rather than a full URL. Mirrors what the DRF
# serializer's computed field presumably did.
_PLATFORM_URL_PREFIXES = {
    SocialPlatform.github: "https://github.com/",
    SocialPlatform.linkedin: "https://linkedin.com/in/",
    SocialPlatform.twitter: "https://twitter.com/",
    SocialPlatform.email: "mailto:",
}


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (CheckConstraint("id = 1", name="profile_singleton"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False, default=1)
    name: Mapped[str] = mapped_column(String(150))
    tagline: Mapped[str] = mapped_column(String(255), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    education: Mapped[str] = mapped_column(Text, default="")
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        default=AvailabilityStatus.open_to_offers
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    social_links: Mapped[list["SocialLink"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="SocialLink.display_order"
    )


class SocialLink(Base):
    __tablename__ = "social_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    platform: Mapped[SocialPlatform] = mapped_column(default=SocialPlatform.other)
    value: Mapped[str] = mapped_column(String(255))  # handle, email, or full URL
    display_order: Mapped[int] = mapped_column(default=0)

    profile: Mapped["Profile"] = relationship(back_populates="social_links")

    @property
    def resolved_url(self) -> str:
        """Build a clickable URL whether `value` is a bare handle or already a URL."""
        if self.value.startswith(("http://", "https://", "mailto:")):
            return self.value
        prefix = _PLATFORM_URL_PREFIXES.get(self.platform, "")
        return f"{prefix}{self.value}" if prefix else self.value
