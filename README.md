# Portfolio API (FastAPI + Neon + Render)

A FastAPI rewrite of a Django REST Framework portfolio backend.

## Stack
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async, `asyncpg`) + Alembic
- Neon Serverless Postgres
- `aiosmtplib` for contact-form email, `slowapi` for rate limiting
- API-key auth (`X-API-Key`) for admin endpoints

## How this was built — phases

**Phase 1 — Project setup & config**
`app/config.py`, `app/database.py`, `requirements.txt`, `.env.example`.
Environment-driven settings via `pydantic-settings`; a single async engine
pointed at Neon (auto-rewrites `postgresql://` → `postgresql+asyncpg://`).

**Phase 2 — Models & migrations**
`app/models/*.py` mirror the Django models 1:1 (`Profile`, `SocialLink`,
`Skill`, `Project`, `ProjectImage`, `ContactMessage`), plus the
`project_skills` M2M table. Alembic (`alembic/`) is wired to the same async
engine and settings, so `alembic upgrade head` works against Neon out of
the box.

**Phase 3 — Schemas**
`app/schemas/*.py`: separate `*Create` / `*Out` / `*Update` Pydantic models
per resource, so a client can never write fields it shouldn't (e.g. a
contact submission can't set its own `status`).

**Phase 4 — Security, rate limiting, email**
`app/core/security.py` (constant-time API key check), `app/core/rate_limit.py`
(slowapi, IP-keyed), `app/core/email.py` (async SMTP, fire-and-forget via
BackgroundTasks, never fails the visitor's request).

**Phase 5 — Routers**
`app/routers/*.py`: one router per resource, matching the original DRF URL
structure and query-param filters (`?featured=`, `?stack=`, `?status=`).

**Phase 6 — Wiring & deployment**
`app/main.py` ties it together: CORS locked to explicit origins, security
headers, docs disabled in production, `/health` for Render's health check.

## Security decisions worth knowing about
- **Admin auth**: `X-API-Key` header, compared with `secrets.compare_digest`
  (timing-safe). Swap for OAuth2/JWT later without touching route logic —
  just change `require_admin`.
- **Honeypot**: a `website` field on the contact form that real users never
  see. If it's filled in, the API returns `201` and *does not touch the
  database* — no error message that would tip off a bot.
- **Rate limiting**: `POST /api/contact/` only, 5/hour per IP by default
  (`CONTACT_RATE_LIMIT` in `.env`).
- **UUID PKs** on `ContactMessage` so message IDs can't be enumerated.
- **CORS**: explicit origin allowlist, no wildcard, no credentials.
- **Prod hardening**: `/docs`, `/redoc`, `/openapi.json` are disabled when
  `ENVIRONMENT=production`.

## Local development
```bash
cp .env.example .env        # fill in your Neon URL, keys, SMTP creds
pip install -r requirements.txt
alembic revision --autogenerate -m "init"
alembic upgrade head
python seed.py               # optional: creates a starter Profile + 2 Skills
uvicorn app.main:app --reload
```
Visit `http://localhost:8000/docs`.

## Deploying to Render

1. **Push this repo to GitHub** (it includes a `.gitignore` — don't commit `.env`).
2. **Create a Neon project** at neon.tech, copy the pooled connection string.
3. **Create a new Web Service on Render**, pointing at your repo:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11+
4. **Set environment variables** on the Render service (Settings → Environment)
   using `.env.example` as the checklist — especially `DATABASE_URL`,
   `SECRET_KEY`, `ADMIN_API_KEY`, `CORS_ALLOWED_ORIGINS` (your frontend's
   Render URL), and SMTP settings. Set `ENVIRONMENT=production`.
5. **Run migrations** once the service is up, via Render's Shell tab:
   ```bash
   alembic upgrade head
   python seed.py   # optional
   ```
6. **Point your frontend** at the Render service URL and confirm
   `CORS_ALLOWED_ORIGINS` includes it exactly (scheme + host, no trailing slash).
7. **Health check**: set Render's health check path to `/health`.

## API summary
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/profile/` | public | profile + nested social links |
| GET | `/api/skills/` | public | ordered by category, display_order |
| GET | `/api/projects/` | public | `?featured=true`, `?stack=<skill>` |
| GET | `/api/projects/{slug}/` | public | full detail + gallery |
| POST | `/api/contact/` | public, rate-limited | honeypot-protected |
| GET | `/api/messages/` | `X-API-Key` | `?status=new\|read\|replied\|archived` |
| PATCH | `/api/messages/{id}/` | `X-API-Key` | update status only |

## What's intentionally left for you to fill in
- Actual avatar/resume/project-image **file uploads** — models store URLs
  (`avatar_url`, `cover_image_url`, `image_url`); wire these to S3/Cloudinary/
  Render disk depending on where you want assets to live.
- A first Alembic migration (`alembic revision --autogenerate`) — not
  committed, since it should be generated once you confirm the schema fits
  your data.
