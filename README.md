# AI CareerGuide

AI-powered career guidance for students and job seekers: career match scores, skill-gap analysis, a phased learning roadmap,
course recommendations, resume and job-description analysis, a profile-aware chat assistant (CareerAI) and progress tracking.

**Stack:** React + Vite + TypeScript + Tailwind + Recharts + Framer Motion + Lucide | FastAPI + Pydantic + SQLAlchemy | PostgreSQL (Supabase-ready; SQLite for local dev) | bcrypt + JWT.

## How the "AI" works (read this first)
The recommendation features are **transparent, rule-based scoring over curated data**, not trained models:

| Feature | Method |
|---|---|
| Career match | Weighted score (skills 40, interests 20, education 15, projects 15, experience 10; configurable per request) over `data/careers.json` |
| Courses | Gap-weighted ranking over `data/courses.json`, boosted when prerequisites are met; every result carries a reason |
| Roadmap | Skill gaps ordered by learning stage, grouped into phases, with course hours converted to weeks |
| Resume / job analysis | Keyword and pattern extraction (`skill_extraction.py`), heuristic section parsing, fixed scoring formulas |
| CareerAI | Intent rules grounded in your own stored data; optional OpenAI-compatible LLM via `LLM_*` env vars |

There are no embeddings or trained scikit-learn models yet. Semantic matching with sentence-transformers is the natural next step
and would slot into `skill_extraction.py`. All outputs are guidance, not guaranteed outcomes, and the UI says so.

## Features
Landing page | register/login (bcrypt, JWT) | 5-step onboarding | dashboard | career analysis with explanations | skill gaps |
roadmap with completion tracking | courses with status tracking | resume analyzer (PDF) | job description match | CareerAI chat with history |
progress and career-readiness score with charts | dark/light mode | responsive layout.

## Project structure
```
ai-careerguide/
  backend/app/{api,core,database,models,schemas,services}, tests/, requirements.txt, .env.example
  frontend/src/{pages,layouts,lib}, package.json, vercel.json
  data/{careers,skills,courses,project_ideas}.json
  scripts/{smoke_test.py,gen_api_docs.py}
  docs/{API.md,DEPLOYMENT.md,screenshots/}
  Dockerfile  render.yaml
```

## Local development
Requirements: Python 3.12+, Node 20+.
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then set JWT_SECRET (see below)
python -c "import secrets; print(secrets.token_urlsafe(48))"    # paste into JWT_SECRET
uvicorn app.main:app --reload   # http://localhost:8000/docs

# frontend (new terminal)
cd frontend
npm install
cp .env.example .env            # VITE_API_URL=http://localhost:8000
npm run dev                     # http://localhost:5173
```
Without `DATABASE_URL` the API uses a local SQLite file (development only). Tables and the skills catalog are created on startup.
To use Postgres locally set `DATABASE_URL=postgresql://user:pass@localhost:5432/careerguide`.

### Environment variables (backend)
| Variable | Purpose |
|---|---|
| `JWT_SECRET` | **Required**, 16+ random characters. The server refuses to start without it |
| `DATABASE_URL` | Postgres URL (`postgres://` and `postgresql://` both accepted) |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `JWT_EXPIRE_HOURS`, `AI_RATE_LIMIT_PER_MIN`, `AUTH_RATE_LIMIT_PER_MIN`, `RESUME_MAX_MB` | Tuning |
| `LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL` | Optional OpenAI-compatible chat endpoint for CareerAI. All three must be set |
| `DB_PGBOUNCER=1` | Disable prepared statements for PgBouncer transaction pooling (auto-enabled for hosts containing "pooler") |

Frontend: `VITE_API_URL` (build-time). Never put secrets in frontend variables.

## Testing
```bash
cd backend && python -m pytest -q                                   # 61 tests, in-memory SQLite
TEST_DATABASE_URL=postgresql://... python -m pytest -q              # same suite on Postgres
cd frontend && npm run build                                        # type-check + production build
python scripts/smoke_test.py http://localhost:8000                  # 16-step end-to-end flow against a running API
```
The smoke test walks: register, login, profile, career analysis, courses, roadmap, resume (generated PDF), job match, CareerAI, progress.
The frontend has no automated UI tests yet.

## API
29 endpoints, documented in [docs/API.md](docs/API.md) and interactively at `/docs` on a running server.
Errors share one shape: `{"error": {"code", "message", "details"}}`. Regenerate the table with `python scripts/gen_api_docs.py`.

## Database
`backend/app/database/schema.sql` is the reference schema (UUID keys, foreign keys with cascades, check constraints, indexes). The ORM
models create the same layout on startup; the full test suite passes against a database built purely from `schema.sql`.
There are no migrations yet (add Alembic before changing the schema in production). The `courses`, `career_courses`,
`career_skills`, `careers`, `projects` and `certifications` tables exist in the schema but are not used yet: the catalog lives in `data/*.json`
and projects/certifications are stored on the profile.

## Deployment
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): Supabase (database), Render or Railway (API, via the Dockerfile), Vercel (frontend).

## Security notes
bcrypt password hashing | JWT with expiry | generic login errors and constant-time-style comparison | Pydantic validation everywhere |
SQLAlchemy parameterized queries | PDF upload checks (extension, content type, magic bytes, size, page count) | CORS allow-list |
per-IP rate limits on AI and auth endpoints | no secrets in the frontend | resume PDFs and pasted job text are never stored.
Known trade-offs: the JWT lives in `localStorage` (consider httpOnly cookies before a public launch); rate limiting is in-memory (use Redis for several workers).

## Known limitations
Rule-based matching (see above) | course ratings are intentionally empty (unverified) and durations/URLs are approximate: check them |
resume parsing assumes conventional headings and text-based PDFs | no email verification or password reset | no screenshots are included
(see `docs/screenshots/README.md`).
