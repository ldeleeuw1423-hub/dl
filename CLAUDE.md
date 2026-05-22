# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

InfraEstimator is a SaaS platform for project estimation in Dutch underground infrastructure (gas & electricity network management). Target users are projectmanagers, engineers and omgevingsmanagers at network operators (Liander/Stedin/Enexis). The platform generates hour estimations, risk registers (RISMAN), permit analyses, and GIS analyses from project data and KML/GeoJSON uploads.

There are **two runnable versions**:
- **Full-stack** (`backend/` + `frontend/`): FastAPI + Next.js + PostgreSQL/PostGIS, requires Docker
- **Standalone demo** (`docs/index.html`): single-file HTML/CSS/JS app served via GitHub Pages at `https://ldeleeuw1423-hub.github.io/dl/` — no build step, no backend needed

## Running the full stack

```bash
cp .env.example .env          # fill in POSTGRES_PASSWORD, SECRET_KEY, OPENAI_API_KEY
docker compose up -d          # starts db (pgvector/pgvector:pg15), backend :8000, frontend :3000
docker compose exec backend alembic upgrade head   # run both migrations
```

**Without Docker** (demo mode, SQLite, no PostGIS/pgvector):
```bash
cd backend && pip install -r requirements-demo.txt && python3 demo_server.py  # :8000
cd frontend && npm install --legacy-peer-deps && npm run dev                   # :3000
```
The demo server (`backend/demo_server.py`) uses in-memory data and requires none of the PostgreSQL-specific types.

## Frontend commands

All run from `frontend/`:

```bash
npm run dev          # dev server on :3000 (uses next.config.mjs, NOT next.config.ts)
npm run build        # production build
npm run lint         # ESLint
npm run type-check   # tsc --noEmit (no emitted files)
```

`next.config.mjs` is the active config (rewrites `/api/v1/*` → `NEXT_PUBLIC_API_URL`). The `.ts` variant is kept for reference but ignored.

## Backend commands

All run from `backend/`:

```bash
uvicorn app.main:app --reload --port 8000   # dev server
alembic upgrade head                         # apply all migrations
alembic revision --autogenerate -m "desc"    # generate new migration
```

Interactive API docs: `http://localhost:8000/api/v1/docs`

## Architecture

### Backend (`backend/app/`)

Layer structure: `routers/` → `services/` → `models/` + `schemas/`

- **`models/`** — SQLAlchemy ORM. `Project` has a PostGIS `geometry` column. `HistoricalProject` has a `pgvector` `Vector(1536)` column for similarity search. `Risk.score` is auto-calculated by SQLAlchemy event listener. All multi-tenant models carry `organization_id` FK.
- **`schemas/`** — Pydantic v2 with Dutch domain enums: `phase` (VO/DO/UO/Realisatie), `discipline` (Gas/Elektra/LS_MS/Stations), `authority` (gemeente/waterschap/prorail/rws).
- **`routers/`** — All routes prefixed `/api/v1/`. Estimation, risk, permit, file, and export routers all mount under `/api/v1/projects/{id}/...`. Auth uses JWT Bearer via `core/deps.py:get_current_user`. Organization-scoped queries use `get_current_organization`.
- **`services/`** — Business logic:
  - `estimation_service.py` — rule tables `DISCIPLINE_PARAMS` (hours/100m per discipline) + location multipliers (binnenstedelijk ×1.35). `find_similar_projects()` uses pgvector `<=>` cosine operator.
  - `risk_service.py` — `STANDARD_RISKS` catalog per discipline (Gas/Elektra/LS_MS/Stations) + 4 universal risks. Auto-detect calls AI service for extra risks.
  - `permit_service.py` — Dutch permit catalog per authority and discipline (instemmingsbesluit, BABW, watervergunning, spoorvergunning, etc.).
  - `gis_service.py` — Async PDOK WFS calls (BAG, BGT, bestuurlijkegrenzen, Natura2000, NWB). `analyze_with_pdok()` combines all checks.
  - `ai_service.py` — OpenAI async client with Dutch-language structured prompts. Graceful fallback to rule-based logic when `OPENAI_API_KEY` is absent.
  - `export_service.py` — `openpyxl` (Excel, 4 sheets) + `reportlab` (PDF A4).

### Frontend (`frontend/src/`)

Next.js 14 App Router with two route groups:
- `(auth)/` — login, register (no layout wrapper)
- `(dashboard)/` — all protected pages wrapped in `DashboardLayout` with `Sidebar` + `Header`

Project detail lives under `(dashboard)/projects/[id]/` with sub-pages: `estimation/`, `risks/`, `permits/`, `gis/`.

**Data flow:** `hooks/` (useProjects, useEstimation, useRisks) call `lib/api.ts` which is a singleton `APIClient` (axios). JWT token stored in a cookie; 401 responses auto-redirect to `/login`.

**GIS:** `components/gis/MapView.tsx` uses `react-leaflet`. PDOK WMS layers toggled via `LayerControl`. Drawing tools via `leaflet-draw`.

**Key shared state:** no global state manager — each page fetches its own data via hooks. Types in `src/types/index.ts` are the single source of truth for all API shapes.

### Standalone demo (`docs/index.html`)

A ~92 KB self-contained single-page app using Tailwind CDN + Chart.js + FontAwesome. All data is in JS variables. The **Project Intake wizard** (5-step) and all other pages are vanilla JS `showPage()` navigation. When updating the live GitHub Pages site, changes to `docs/index.html` must also be copied to the `gh-pages` branch root:

```bash
git checkout gh-pages
cp docs/index.html index.html
git add index.html && git commit -m "..." && git push origin gh-pages
git checkout claude/infrastructure-estimation-app-Tm8bQ
```

## Key domain concepts

- **RISMAN risk scoring** — `score = kans (1-5) × impact (1-5)`. High ≥ 10, medium 5–9, low 1–4.
- **Project phases** — VO (Voorontwerp) → DO (Definitief Ontwerp) → UO (Uitvoeringsontwerp) → Realisatie. Confidence scores decrease from Realisatie to VO.
- **Hour estimation structure** — Engineering / Projectmanagement / Omgevingsmanagement / Werkvoorbereiding / Uitvoering (regie). Each has sub-disciplines with fixed rates in `HOURLY_RATES`.
- **Multi-tenant** — every query against Project/Risk/Permit/Estimation must filter on `organization_id`. Use `get_current_organization` dependency in new routers.
- **PDOK** — Dutch national open geodata APIs (WFS). All calls are async with 15s timeout and silent fallback. No API key required.

## Database migrations

Two migrations exist:
- `001_initial_schema.py` — all core tables
- `002_pgvector_multitenant.py` — enables `vector` extension, adds `organizations` table, adds `organization_id` FKs, replaces text `embedding` with `vector(1536)`, adds IVFFlat cosine index

Always run both: `alembic upgrade head`.

## Deployment

- **GitHub Pages** (demo): `gh-pages` branch, `index.html` at root. Auto-deployed on push.
- **Vercel** (frontend): `frontend/vercel.json` present. Set `NEXT_PUBLIC_API_URL` env var to backend URL.
- **Render** (backend): `render.yaml` at repo root. Uses `requirements-demo.txt` and `python3 demo_server.py`.
- **Full production**: `docker-compose.yml` with `pgvector/pgvector:pg15` image (not plain `postgres:15`).
