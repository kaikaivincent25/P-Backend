"""Skill model — used standalone (/api/skills/) and M2M on Project (stack_tags)."""
import enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SkillCategory(str, enum.Enum):
    frontend = "frontend"
    backend = "backend"
    mobile = "mobile"
    ai_tools = "ai_tools"
    other = "other"


class SkillProficiency(str, enum.Enum):
    learning = "learning"
    comfortable = "comfortable"
    confident = "confident"


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[SkillCategory] = mapped_column(default=SkillCategory.other, index=True)
    proficiency: Mapped[SkillProficiency] = mapped_column(default=SkillProficiency.comfortable)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_order: Mapped[int] = mapped_column(default=0)
