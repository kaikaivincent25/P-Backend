from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillOut

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/", response_model=list[SkillOut])
async def list_skills(db: AsyncSession = Depends(get_db)):
    stmt = select(Skill).order_by(Skill.category, Skill.display_order, Skill.name)
    result = await db.execute(stmt)
    return result.scalars().all()
