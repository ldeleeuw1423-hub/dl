# InfraEstimator — Netbeheer Projectramingssysteem

Professioneel SaaS-platform voor projectkostenraming bij ondergrondse infrastructuur (gas & elektra netbeheer) in Nederland. Gericht op projectmanagers, engineers en omgevingsmanagers bij bedrijven als Liander, Stedin en Enexis.

## Functionaliteiten

- **AI-ondersteunde raming** — uren en kosten op basis van projectparameters, met GPT-4o + fallback naar regelgebaseerde berekening
- **Risicobeheer (RISMAN)** — 5×5 risicomatrix, auto-detectie van risico's per discipline
- **Vergunningenbeheer** — timeline-overzicht, auto-detectie per discipline en locatietype
- **GIS-kaartweergave** — Leaflet met PDOK-kaartlagen (BGT, BAG), tracé tekenen en omgevingsanalyse
- **Historische data** — referentieprojecten voor vergelijkingen en AI-training
- **Dashboard** — KPI-overzicht, budget vergelijking, project timeline

## Stack

| Laag | Technologie |
|------|-------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python FastAPI |
| Database | PostgreSQL + PostGIS + pgvector |
| AI | OpenAI GPT-4o (optioneel) |
| GIS | Leaflet.js + PDOK WMS |
| Auth | JWT (jose + passlib bcrypt) |

## Snel starten

```bash
# 1. Kopieer environment variabelen
cp .env.example .env

# 2. Vul in: POSTGRES_PASSWORD, SECRET_KEY, OPENAI_API_KEY (optioneel)
nano .env

# 3. Start alle services
docker compose up -d

# 4. Wacht tot database klaar is en voer migraties uit
docker compose exec backend alembic upgrade head

# 5. Open de applicatie
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/api/v1/docs
```

## Eerste gebruiker aanmaken

Registreer via `/register` of gebruik de API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bedrijf.nl","password":"geheim123","name":"Beheerder","role":"admin","organization":"Liander"}'
```

## Disciplines

- **Gas** — gasdistributie en transportleidingen
- **Elektra** — laagspanning (LS) aansluitingen
- **LS/MS** — laag- en middenspanning kabels
- **Stations** — schakelstations en transformatorhuisjes

## Projectfasen

- **VO** — Voorlopig Ontwerp (bandbreedte ~±35%)
- **DO** — Definitief Ontwerp (bandbreedte ~±25%)
- **UO** — Uitvoeringsontwerp (bandbreedte ~±15%)
- **Realisatie** — Uitvoering (bandbreedte ~±10%)

## Omgeving variabelen

| Variabele | Omschrijving |
|-----------|--------------|
| `POSTGRES_DB` | Database naam |
| `POSTGRES_USER` | Database gebruiker |
| `POSTGRES_PASSWORD` | Database wachtwoord |
| `SECRET_KEY` | JWT signing secret (minimaal 32 tekens) |
| `OPENAI_API_KEY` | OpenAI API sleutel (optioneel) |
| `OPENAI_MODEL` | OpenAI model (standaard: gpt-4o) |
| `NEXT_PUBLIC_API_URL` | Backend URL voor frontend |

## Ontwikkeling

```bash
# Backend apart starten
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend apart starten
cd frontend
npm install
npm run dev
```

## Architectuur

```
InfraEstimator
├── backend/           FastAPI applicatie
│   ├── app/
│   │   ├── models/    SQLAlchemy ORM modellen
│   │   ├── schemas/   Pydantic validatie schemas
│   │   ├── routers/   API endpoints
│   │   ├── services/  Business logic (AI, GIS, files)
│   │   └── core/      Auth + dependencies
│   └── alembic/       Database migraties
└── frontend/          Next.js 14 applicatie
    └── src/
        ├── app/       App Router pagina's
        ├── components/ React componenten
        ├── hooks/     Data hooks
        ├── lib/       API client + utilities
        └── types/     TypeScript types
```
