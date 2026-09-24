"""
Project routers.

GET /api/projects/ supports:
  - ?featured=true      filter to featured projects only
  - ?stack=skill_name   filter to projects whose stack_tags include a skill
                        with this name (case-insensitive exact match)

Both are optional and combine with AND when both are present.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project import Project
from app.models.skill import Skill
from app.schemas.project import ProjectDetail, ProjectListItem

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectListItem])
async def list_projects(
    featured: bool | None = Query(default=None),
    stack: str | None = Query(default=None, description="Skill name to filter by"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Project).options(selectinload(Project.stack_tags)).order_by(Project.created_at.desc())

    if featured is not None:
        stmt = stmt.where(Project.featured == featured)

    if stack:
        stmt = stmt.join(Project.stack_tags).where(func.lower(Skill.name) == stack.lower())

    result = await db.execute(stmt)
    return result.unique().scalars().all()


@router.get("/{slug}/", response_model=ProjectDetail)
async def get_project(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Project)
        .options(selectinload(Project.stack_tags), selectinload(Project.images))
        .where(Project.slug == slug)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project
