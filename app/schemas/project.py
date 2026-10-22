from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.skill import SkillOut


class ProjectImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    caption: str
    display_order: int


class ProjectListItem(BaseModel):
    """Card data for GET /api/projects/, including the project's overview."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    summary: str
    description: str
    cover_image_url: str | None
    repo_url: str | None
    live_url: str | None
    featured: bool
    created_at: datetime
    stack_tags: list[SkillOut] = []


class ProjectDetail(ProjectListItem):
    """Full shape for GET /api/projects/{slug}/ — adds description + gallery."""
    description: str
    images: list[ProjectImageOut] = []
