"""
Optional convenience script: populate a fresh DB with a starter Profile row
and a couple of skills, so /api/profile/ and /api/skills/ don't 404 right
after your first migration. Run once after `alembic upgrade head`:

    python seed.py
"""
import asyncio

from app.database import AsyncSessionLocal
from app.models.profile import Profile
from app.models.skill import Skill, SkillCategory, SkillProficiency


async def main():
    async with AsyncSessionLocal() as db:
        existing = await db.get(Profile, 1)
        if existing is None:
            db.add(Profile(id=1, name="Your Name", tagline="Full-stack developer"))
        for name, category in [("Python", SkillCategory.backend), ("React", SkillCategory.frontend)]:
            db.add(Skill(name=name, category=category, proficiency=SkillProficiency.confident))
        await db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
