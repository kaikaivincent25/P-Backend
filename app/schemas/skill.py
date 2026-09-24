from pydantic import BaseModel, ConfigDict

from app.models.skill import SkillCategory, SkillProficiency


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: SkillCategory
    proficiency: SkillProficiency
    icon: str | None
    display_order: int
