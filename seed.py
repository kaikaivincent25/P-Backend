"""
Database seeding script.

Populates a fresh database with:
  1. A complete singleton Profile row + Social Links.
  2. Baseline Skills across Frontend, Backend, AI Tools, and Mobile.
  3. A sample Project tagged with relevant stack skills.

Usage:
    python seed.py
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.profile import AvailabilityStatus, Profile, SocialLink, SocialPlatform
from app.models.project import Project, ProjectImage
from app.models.skill import Skill, SkillCategory, SkillProficiency


async def seed_profile(db) -> Profile:
    profile = await db.get(Profile, 1)
    if profile is None:
        profile = Profile(
            id=1,
            name="Vincent Kaikai",
            tagline="Full-stack & mobile developer building technology for East Africa",
            bio=(
                "I'm a software developer and final-year Business Information Technology "
                "student at The Co-operative University of Kenya (graduating December 2026). "
                "I work independently across product and engineering: design, architecture "
                "and implementation, shipping React and React Native (Expo) front ends "
                "backed by Django REST Framework, FastAPI and PostgreSQL. "
                "I'm especially interested in problems specific to the East African context, "
                "such as fighting misinformation and making verified expert knowledge easier "
                "to reach. I care about clean architecture, performance, and interfaces "
                "that feel intentional rather than templated."
            ),
            education="BBIT, The Co-operative University of Kenya (expected December 2026)",
            availability_status=AvailabilityStatus.open_to_offers,
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=500",
            resume_url="https://example.com/resume.pdf",
        )
        db.add(profile)
        await db.flush()  # Ensure profile.id is available for FKs

        socials = [
            SocialLink(
                profile_id=1,
                platform=SocialPlatform.github,
                value="https://github.com/kaikaivincent25",
                display_order=1,
            ),
            SocialLink(
                profile_id=1,
                platform=SocialPlatform.linkedin,
                value="https://linkedin.com/in/vincent-kaikai",
                display_order=2,
            ),
            SocialLink(
                profile_id=1,
                platform=SocialPlatform.twitter,
                value="https://twitter.com/kaikaivincent",
                display_order=3,
            ),
            SocialLink(
                profile_id=1,
                platform=SocialPlatform.email,
                value="mailto:kaikaivincent24@gmail.com",
                display_order=4,
            ),
        ]
        db.add_all(socials)
        print("✓ Created singleton Profile and Social Links.")
    else:
        print("i Profile row already exists, skipping...")
    return profile


async def seed_skills(db) -> dict[str, Skill]:
    skills_data = [
        # Frontend
        ("React", SkillCategory.frontend, SkillProficiency.confident, "react", 1),
        ("Vite", SkillCategory.frontend, SkillProficiency.confident, "vite", 2),
        ("TypeScript", SkillCategory.frontend, SkillProficiency.comfortable, "typescript", 3),
        ("Tailwind CSS", SkillCategory.frontend, SkillProficiency.confident, "tailwindcss", 4),
        # Backend
        ("Django REST Framework", SkillCategory.backend, SkillProficiency.confident, "django", 1),
        ("FastAPI", SkillCategory.backend, SkillProficiency.confident, "fastapi", 2),
        ("Python", SkillCategory.backend, SkillProficiency.confident, "python", 3),
        ("PostgreSQL", SkillCategory.backend, SkillProficiency.confident, "postgresql", 4),
        # Mobile & AI Tools
        ("React Native (Expo)", SkillCategory.mobile, SkillProficiency.confident, "react", 1),
        ("OpenAI API", SkillCategory.ai_tools, SkillProficiency.comfortable, "openai", 1),
    ]

    skill_map = {}
    for name, category, proficiency, icon, order in skills_data:
        stmt = select(Skill).where(Skill.name == name)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing is None:
            skill = Skill(
                name=name,
                category=category,
                proficiency=proficiency,
                icon=icon,
                display_order=order,
            )
            db.add(skill)
            await db.flush()
            skill_map[name] = skill
        else:
            skill_map[name] = existing

    print(f"✓ Ensured {len(skills_data)} core Skills exist.")
    return skill_map


async def seed_projects(db, skill_map: dict[str, Skill]):
    slug = "personal-portfolio-api"
    stmt = select(Project).where(Project.slug == slug)
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing is None:
        project = Project(
            title="Personal Portfolio API",
            slug=slug,
            summary="Async FastAPI backend paired with a Neon PostgreSQL database and React frontend.",
            description=(
                "A full-stack portfolio application built to showcase project case studies, "
                "manage contact messages securely with honeypot validation and rate limiting, "
                "and present dynamic developer profile metrics."
            ),
            cover_image_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=1000",
            repo_url="https://github.com/kaikaivincent25/P-Backend",
            live_url="https://kaikaivincentwebsite-pi.vercel.app",
            featured=True,
        )

        # Attach skill tags dynamically
        tagged_skills = ["FastAPI", "Python", "PostgreSQL", "React", "Tailwind CSS"]
        project.stack_tags = [skill_map[s] for s in tagged_skills if s in skill_map]

        db.add(project)
        await db.flush()

        # Add sample gallery images
        images = [
            ProjectImage(
                project_id=project.id,
                image_url="https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&q=80&w=800",
                caption="API Endpoint Architecture",
                display_order=1,
            ),
        ]
        db.add_all(images)
        print("✓ Created starter Project case study.")
    else:
        print("i Sample project already exists, skipping...")


async def main():
    async with AsyncSessionLocal() as db:
        await seed_profile(db)
        skill_map = await seed_skills(db)
        await seed_projects(db, skill_map)
        await db.commit()
    print("\n🚀 Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())