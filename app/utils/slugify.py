"""Slug generation for Project.slug, with DB-level uniqueness enforcement."""
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


async def generate_unique_slug(db: AsyncSession, title: str, *, exclude_id: int | None = None) -> str:
    """
    Appends -2, -3, ... on collision, matching typical Django slugify()
    + uniqueness-loop behavior. Checked against the DB, not an in-memory
    set, so it's correct even across concurrent requests up to the point
    of the final INSERT (which still has a unique constraint as the real
    safety net — see models/project.py).
    """
    base = slugify(title) or "project"
    candidate = base
    suffix = 2
    while True:
        stmt = select(Project.id).where(Project.slug == candidate)
        if exclude_id is not None:
            stmt = stmt.where(Project.id != exclude_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1
