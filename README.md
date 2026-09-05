
# Peblo TV Mini

A full-stack streaming catalogue platform with a content management system (CMS) and a public viewer application.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌────────────┐
│     CMS      │─────▶│   FastAPI    │─────▶│ PostgreSQL │
│ React + TS   │      │   Backend    │      │            │
└──────────────┘      └──────┬───────┘      └────────────┘
                             │
                             ▼  POST /admin/catalog/publish
                      catalogue.json
                             │
┌──────────────┐             │
│    Viewer    │◀────────────┘
│ React + TS   │  (reads published file only)
└──────────────┘
```

- **CMS** — React + TypeScript + TanStack Query. Content management dashboard for editors and admins.
- **Backend** — FastAPI + SQLAlchemy + PostgreSQL. REST API with JWT auth, CRUD, validation, and atomic catalogue publishing.
- **Viewer** — React + TypeScript + TanStack Query. Read-only public viewer that consumes the published `catalogue.json`.
- **PostgreSQL** — Persistent data store for all content and users.

## Project Structure

```
peblo-tv-mini/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (auth, shows, seasons, episodes, artwork, admin, catalog)
│   │   ├── core/         # Config and JWT/security utilities
│   │   ├── db/           # SQLAlchemy session and engine
│   │   ├── models/       # ORM models (Show, Season, Episode, Artwork, PublishRun, User)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (catalogue generation, validation, seeding)
│   │   └── storage/      # Storage abstraction (LocalStorage, R2Storage placeholder)
│   ├── tests/            # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── cms/                  # React CMS app
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── viewer/               # React Viewer app
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── data/                 # Seed data (seed_shows.json, reference.json)
├── .github/workflows/    # GitHub Actions CI
├── docker-compose.yml
└── .env.example
```

## Local Setup

### Windows

```bash
# 1. Copy environment file
copy .env.example .env

# 2. Start PostgreSQL (via Docker or local install)
#    Docker: docker run -d --name peblo-db -p 5432:5432 -e POSTGRES_DB=peblo -e POSTGRES_USER=peblo -e POSTGRES_PASSWORD=peblo postgres:17-alpine

# 3. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000  |  Swagger: http://localhost:8000/docs  |  Health: http://localhost:8000/health

# 4. CMS (new terminal)
cd cms
npm install
npm run dev
# → http://localhost:5173

# 5. Viewer (new terminal)
cd viewer
npm install
npm run dev
# → http://localhost:5174
```

### macOS / Linux

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start PostgreSQL (via Docker or local install)
#    Docker: docker run -d --name peblo-db -p 5432:5432 -e POSTGRES_DB=peblo -e POSTGRES_USER=peblo -e POSTGRES_PASSWORD=peblo postgres:17-alpine

# 3. Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000  |  Swagger: http://localhost:8000/docs  |  Health: http://localhost:8000/health

# 4. CMS (new terminal)
cd cms
npm install
npm run dev
# → http://localhost:5173

# 5. Viewer (new terminal)
cd viewer
npm install
npm run dev
# → http://localhost:5174
```

## Docker Compose

```bash
docker compose up --build
```

| Service  | Description           | Host Port |
|----------|-----------------------|-----------|
| `db`     | PostgreSQL 17         | 5432      |
| `api`    | FastAPI backend       | 8000      |
| `cms`    | CMS (nginx)           | 3000      |
| `viewer` | Viewer (nginx)        | 3001      |

The database is seeded automatically on first startup with demo shows and users.

**Note:** In dev mode, Vite serves CMS on `http://localhost:5173` and Viewer on `http://localhost:5174`. Docker Compose uses nginx and maps to ports 3000/3001.

## Demo Accounts

| Username | Password  | Role  | Capabilities          |
|----------|-----------|-------|-----------------------|
| `admin`  | `admin123`  | admin | CRUD + publish        |
| `editor` | `editor123` | editor | CRUD only (no publish) |

## Server-Side Role Enforcement

Every mutating endpoint uses a `require_role()` dependency that checks the JWT token's role claim server-side. Editors are restricted to CRUD operations; publishing is admin-only. Unauthorized requests return `403 Forbidden`.

## Content & Language Model

- **Content groups** group language variants of the same episode under a single logical unit. When the catalogue is generated, episodes sharing a `content_group` collapse into one catalogue entry.
- Each entry's `languages` list contains all available language codes (e.g. `["en", "es"]`).
- The database enforces uniqueness on `(content_group, language)` — you cannot have two episodes with the same content group and language.
- **Season 0** is reserved for trailers and is included in the generated catalogue.

## Artwork Validation

All artwork uploads are validated server-side (not only in the CMS frontend):

| Type       | Aspect Ratio | Target Size   | Max File Size |
|------------|-------------|---------------|---------------|
| Poster     | 2:3         | ~600 × 900    | 200 KB        |
| Banner     | 16:9        | ~1280 × 720   | 200 KB        |
| Thumbnail  | 16:9        | ~640 × 360    | 200 KB        |

Validation checks: file size ≤ 200 KB, valid image format (via Pillow), and aspect ratio within 5% tolerance of the target ratio.

## Storage Abstraction

Artwork storage uses a pluggable `StorageBackend` interface with two implementations:

- **LocalStorage** (default) — saves files to disk under `./storage/uploads/`. Configured via `STORAGE_BACKEND=local`.
- **R2Storage** (placeholder) — same interface, designed for Cloudflare R2. To migrate:
  1. Implement the `save()`, `delete()`, and `get_url()` methods using `boto3` for R2.
  2. Set `STORAGE_BACKEND=r2` in your environment.
  3. Configure R2 credentials (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`).
  No business logic changes needed — the rest of the app is storage-agnostic.

## Atomic Publishing

Publishing is triggered via `POST /admin/catalog/publish` (admin only):

1. The full catalogue is generated in memory from all published shows and episodes.
2. Written to a temporary file in the same filesystem directory.
3. `os.replace()` atomically swaps the temp file to the live `catalogue.json` path.

**Crash safety:** If publishing crashes at any point before the atomic rename, the previous `catalogue.json` remains intact and valid. The viewer always reads the last successfully written file. Temp files are cleaned up on failure.

### Why a Pre-Published Catalogue?

The viewer reads a pre-generated `catalogue.json` rather than querying PostgreSQL per request because:

- **Performance:** Single file read vs. N database queries with JOINs across shows, seasons, episodes, and artwork.
- **Consistency:** Every viewer sees the exact same snapshot at any point in time.
- **Simplicity:** No caching layer, connection pooling, or read replicas needed.
- **Cost:** Zero database load from read traffic.

The trade-off is that updates require a publish step, which is appropriate for a content catalogue that changes infrequently.

## Search Endpoint

```
GET /catalog/search?q=&category=&language=&section=
```

| Parameter  | Description                                                  |
|------------|--------------------------------------------------------------|
| `q`        | Substring match against show title and episode titles (case-insensitive) |
| `section`  | Filter by section name                                       |
| `language` | Filter episodes by language code                             |
| `category` | Declared as a query parameter (reserved for future use)      |

Filters compose with AND logic. The endpoint loads the published `catalogue.json` into memory and filters inline.

### Current Scale Limitation

All filtering happens in Python against the in-memory JSON. This is suitable for hundreds to low thousands of shows. **Next scaling step:** For 10k+ shows, add PostgreSQL full-text search using `tsvector`/`tsquery` or a dedicated search engine (Elasticsearch / Meilisearch) for the search endpoint, while keeping the pre-published file for the main catalogue view.

## Validation Report & Publish Endpoints

| Endpoint                      | Method | Auth        | Description                                        |
|-------------------------------|--------|-------------|----------------------------------------------------|
| `/admin/validation-report`    | GET    | editor/admin | Checks all published entities for blocking issues (missing section, duration, artwork) |
| `/admin/catalog/publish`      | POST   | admin only  | Atomically generates and publishes the catalogue    |
| `/admin/publish-runs`         | GET    | editor/admin | Lists the last 50 publish runs with status and metadata |

## Testing

Tests use **pytest** with an in-memory SQLite database (no PostgreSQL required for test runs) and `starlette.testclient`.

```bash
cd backend
pytest tests -v
```

**What is tested:**

- **Authentication** (`test_auth.py`) — login success/failure, token retrieval, unauthorized access
- **CRUD operations** (`test_crud.py`) — show/season/episode create, read, update, delete; slug uniqueness; season number uniqueness; content_group+language uniqueness; editor cannot publish
- **Health check** (`test_health.py`) — `/health` endpoint returns `{"status": "ok"}`
- **Publishing** (`test_publish.py`) — validation report (missing section/duration/artwork), publishable check, language variant grouping, deterministic ordering, atomic publish success, search filters, role enforcement
- **Artwork** (`test_artwork.py`) — valid poster/banner/thumbnail upload, wrong aspect ratio rejection, oversized file rejection, invalid artwork type rejection

## GitHub Actions / CI

`.github/workflows/ci.yml` runs on every push and pull request:

1. **Backend job** — Installs Python 3.13, installs dependencies, runs `pytest backend/tests -v`.
2. **Frontend job** — Matrix build for `cms` and `viewer`. Installs Node 22, runs `npm install` and `npm run build` for each.
3. **Docker job** — Depends on backend and frontend. Builds Docker images for all three services (`api`, `cms`, `viewer`) to verify Dockerfiles are valid.

## What Was Intentionally Left Out

- **OAuth2/OIDC** — Used simple JWT with seeded demo users. Production would use a proper identity provider.
- **Image resizing / CDN** — Artwork is stored at original resolution. Production would use Cloudflare Images or similar.
- **Full-text search index** — Current in-memory search is sufficient for the challenge dataset.
- **Rate limiting** — Not critical for a take-home challenge.
- **Soft deletes** — Hard deletes are simpler and sufficient here.
- **Pagination cursors** — Offset pagination is used for simplicity.

## Production Secret Management

Secrets (database credentials, JWT signing keys, storage credentials) should be stored in environment variables or a managed secret storage service (e.g. AWS Secrets Manager, Vault). Never commit secrets to Git. The `.env.example` file provides a template with placeholder values.

## AI Tools Used

AI coding assistance was used during the development of this project. All generated code was **reviewed, tested, modified, and accepted** only when it matched the challenge requirements. Architecture decisions — including atomic publishing with `os.replace()`, the storage abstraction layer, server-side role/permission enforcement, content group language collapse logic, and catalogue generation — were **reviewed rather than blindly accepting** generated output. Generated implementations that did not meet requirements were rewritten or discarded.


