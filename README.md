# BARKLY

BARKLY is an iOS + backend project for AI-enabled dog-behavior interpretation.
This monorepo contains two workstreams:

| Area | Location | Status |
| --- | --- | --- |
| **Phase 1 — iOS app** | `Barkly/`, `BarklyTests/`, `Scripts/` | Complete. Behavior-analysis UX with typed domain models, repositories behind protocols, and a Swift test suite. |
| **Phase 2 — backend** | `backend/` | API + persistence + AI-abstraction foundation with tests and a documented contract. Real ML inference is Phase 3. |

## Phase 1 — iOS app

- SwiftUI app under `Barkly/` with domain-driven models
  (`BehaviorState`, `VocalizationType`, `Dog`, `BehaviorAnalysis`) and
  repository protocols (`DogRepository`, `AnalysisRepository`,
  `HistoryRepository`, `InsightsRepository`).
- Interactive walkthrough, analysis flow, history, insights, and a
  permission-consented media service.
- Test suite in `BarklyTests/`; regenerate the Xcode project with
  `Scripts/generate_project.py` whenever Swift files change.

## Phase 2 — Backend

A production-oriented API foundation:

- FastAPI (async) + PostgreSQL via async SQLAlchemy + Alembic migrations.
- Ownership-scoped auth (JWT) for dogs, analyses, media, and history.
- Strict analysis lifecycle (`CREATED → QUEUED → PROCESSING → COMPLETED | FAILED`)
  with idempotent creation and first-class failure state.
- **AI provider abstraction** shipping a clearly-labelled development
  placeholder; no fake inference, no fake metrics, no datasets yet.
- Versioned API under `/api/v1`, structured JSON logs with request IDs, and a
  standardized error envelope.
- 78-test suite (SQLite in-memory by default, runnable against PostgreSQL)
  covering auth, dogs, media, analyses, history, feedback, error contract,
  health probes, and migration round-trips.

### Backend quick start

```sh
cd backend
cp .env.example .env          # edit DATABASE_URL / JWT_SECRET
../.venv/bin/pip install -e ".[dev]"
../.venv/bin/alembic upgrade head
../.venv/bin/uvicorn app.main:app --reload --port 8000
```

Docs: `backend/docs/` (API contract, architecture, analysis lifecycle, AI
integration). Full backend README: `backend/README.md`.

## Roadmap

- **Phase 3** — real inference provider(s), feature extraction, dataset and
  metrics tooling, experiment tracking. The provider interface and model
  identity/versioning are already in place so this plugs in without API
  changes.