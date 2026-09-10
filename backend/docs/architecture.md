# BARKLY Backend Architecture

## 1. Overview

The backend is a layered async Python/FastAPI service that will host BARKLY's
AI-enabled dog-behavior interpretation. Phase 2 establishes the production
foundation: ownership-scoped persistence, a documented API contract, a strict
analysis lifecycle, an **AI provider abstraction** (ships with a clearly
labelled development placeholder only — no inference is faked as real ML), and
media handling that never exposes internal storage.

Design constraints honored throughout:

- Async I/O end to end (SQLAlchemy 2.x async + aiomysql).
- SQLite is used **only** in tests (in-memory, hermetic); production targets
  MariaDB via Alembic migrations.
- No Redis, no Celery, no Kubernetes, no Nginx — a single FastAPI process is
  deliberately kept deployable as one unit for this phase.
- No fake metrics, datasets, or model training; the provider interface is the
  explicit boundary where real Phase 3 inference will plug in.

## 2. Repository layout

```
backend/
├── pyproject.toml              # deps, pytest + ruff config
├── alembic.ini                 # migration config
├── migrations/
│   ├── env.py                  # async env; URL from BARKLY_DATABASE_URL
│   └── versions/               # initial_schema (  portable, 0 MariaDB-only SQL)
├── app/
│   ├── main.py                 # create_app(): middleware, handlers, routers
│   ├── core/                   # config, logging, context, security, errors
│   ├── db/                     # engine/session factory, Base, ORM models
│   ├── domain/                 # enums (string taxonomy), value objects
│   ├── schemas/                # Pydantic request/response contracts
│   ├── repositories/           # data-access layer (ownership queries)
│   ├── services/               # business logic (lifecycle, media, feedback)
│   ├── ai/                     # provider protocol + registry + placeholder
│   ├── media/                  # validation tables + storage abstraction
│   ├── dependencies/           # auth dependency
│   └── api/v1/                 # routers + serializers
└── tests/                      # pytest suite (sqlite default, PG optional)
```

## 3. Request flow

```
client ─▶ middleware (request/correlation id, JSON request logging)
       ─▶ auth dependency (JWT → user)
       ─▶ router → service (business rules)
       ─▶ repository (ownership-scoped SQL)
       ─▶ MariaDB
       ─▶ serializer → response model
```

Every response flowing back through the middleware carries `X-Request-Id`; the
error envelope always includes `request_id` so clients can correlate problems.

## 4. Domain model

String-typed enums (see `docs/api-contract.md → §5`) so the behavior taxonomy
can evolve in place. Entities:

- **User** — auth identity; owner of dogs, analyses, media, feedback.
- **Dog** — pet profile owned by a user. Architectural rule: **no cross-user
  access** — every dog/analysis/media/feedback lookup filters by owner.
- **Analysis** — one interpretation request; status machine
  `CREATED → QUEUED → PROCESSING → COMPLETED | FAILED`; optional
  `idempotency_key` (unique per user).
- **AnalysisContext** — 1:1 snapshot of the signal context at analysis time.
- **AnalysisMedia** — immutable snapshot of the inputs used (owns a nullable
  `asset_id → media_assets`).
- **AnalysisObservation** — provider-returned evidence lines (audio/visual/
  context), 1:N.
- **AnalysisResult** — 1:1 finished interpretation (behavior, confidence,
  model identity, disclaimer).
- **AnalysisFeedback** — 1:N confirm/correct records; snapshots predicted +
  corrected behavior.
- **MediaAsset** — uploaded owned file metadata; internal storage reference
  kept private.

## 5. Layering rules

- **API layer** (`api/v1/`) — routing, HTTP concerns, serialization; thin.
- **Service layer** (`services/`) — orchestration, validation policies,
  lifecycle transitions, error mapping.
- **Repository layer** (`repositories/`) — all SQL, always owner-filtered.
- **Domain layer** (`domain/`) — shared vocabulary with no I/O.
- **Schema layer** (`schemas/`) — request/response contracts; transport only.

Dependencies point inward (API → service → repository). Models never leak into
schemas; serializers translate ORM → response.

## 6. Key decisions

| Decision | Rationale |
| --- | --- |
| Inference runs outside DB transactions | A slow/failed model must not hold locks or poison writes; create → commit → infer → commit |
| Provider failure ⇒ `FAILED` status, not an HTTP 5xx | The analysis is a persisted resource; its terminal state carries failure info via `failure.code/message` |
| Media identity is `media_id`, storage refs are opaque | Storage backend is swappable; clients never touch paths |
| `idempotency_key` server-side lookup | Retry-safe creation without client coupon tokens |
| Pagination at the DB with stable ordering | No unbounded scans; `page/page_size/total/has_next` |
| Feedback snapshots the prediction | Corrections stay interpretable after model upgrades |
| Structured JSON logs with request_id | Correlation across requests and future tracing |
| String enums in the DB | Taxonomy evolves without destructive migrations |
| `metadata` column renamed `media_metadata` | Avoids the reserved JSON `metadata` name on both PostgreSQL and SQLite |

## 7. Dependencies (vendored version family)

- FastAPI / Uvicorn, Pydantic v2 + pydantic-settings
- SQLAlchemy 2.x (async), Alembic, aiomysql, aiosqlite (tests), PyMySQL (migrations/tests)
- PyJWT (HS256), bcrypt
- pytest + pytest-asyncio + httpx (tests), ruff (lint/format)

See `backend/pyproject.toml` for exact pins.

## 8. Configuration surface

All settings are read from environment variables with the `BARKLY_` prefix
(precedence: env > `backend/.env` > defaults). Key values:

| Setting | Default | Notes |
| --- | --- | --- |
| `BARKLY_DATABASE_URL` | local MariaDB (aiomysql) | prod must be MariaDB |
| `BARKLY_JWT_SECRET` | dev-only fallback | ≥32 chars required in prod |
| `BARKLY_AI_PROVIDER` | `development-placeholder` | future: real model ids |
| `BARKLY_MEDIA_STORAGE_PROVIDER` | `local` | storage abstraction |
| `BARKLY_MAX_UPLOAD_SIZE_BYTES` | 25 MB | upload rejection |
| `BARKLY_DISCLAIMER` | standard | attached to every result |
| `BARKLY_ALLOWED_ORIGINS` | localhost:3000 | CORS; never `*` |

## 9. Observability & security

- Middleware logs `request_started` / `request_completed` with
  `request_id`, `correlation_id`, endpoint, status, and duration.
- JWT access tokens: 30-minute lifetime, `HS256`, signed with the configured
  secret; production refuses to boot without an explicit strong secret.
- Passwords: bcrypt, 12 rounds.
- CORS origins explicit; media files validated by content type + extension +
  size; storage references never serialized.