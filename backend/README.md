# BARKLY Backend

Production-oriented foundation and AI-ready contract for BARKLY's
dog-behavior interpretation service. Built with FastAPI, async SQLAlchemy,
PostgreSQL, and Alembic. Ships an **AI-provider abstraction** with a clearly
labelled development placeholder — no inference is faked as real ML.

- API contract: [`docs/api-contract.md`](docs/api-contract.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Analysis lifecycle: [`docs/analysis-lifecycle.md`](docs/analysis-lifecycle.md)
- AI integration: [`docs/ai-integration.md`](docs/ai-integration.md)

## Prerequisites

- macOS with Homebrew (the commands below are for a fresh macOS machine)
- Python 3.11+ (developed on 3.14)
- PostgreSQL 15+ (optional for development; **required** for production)

## 1. Virtual environment

```sh
cd backend
python3 -m venv .venv          # or reuse the repo-root venv: ../.venv
source .venv/bin/activate
pip install -e ".[dev]"
```

A repo-root venv is used in this project: `../.venv/bin/python`, `../.venv/bin/pip`.

## 2. Configuration

```sh
cp .env.example .env
```

Edit `.env` (or export `BARKLY_` variables). Everything defaults to a local
developer setup; the only required value in production is `JWT_SECRET` (≥32
chars). See `docs/architecture.md → §8` for the full surface.

## 3. PostgreSQL (local development)

On macOS with Homebrew:

```sh
brew install postgresql@17
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /tmp/barkly-pg -l /tmp/barkly-pg.log \
  -o "-p 5455" start
/opt/homebrew/opt/postgresql@17/bin/createdb -p 5455 -U barkly barkly_dev
/opt/homebrew/opt/postgresql@17/bin/createdb -p 5455 -U barkly barkly_test
```

Point `.env` at it:

```sh
DATABASE_URL=postgresql+asyncpg://barkly@127.0.0.1:5455/barkly_dev
```

Any PostgreSQL instance works; the port/credentials are just the ones used
during development on this machine.

## 4. Migrations

```sh
cd backend
../.venv/bin/alembic upgrade head       # apply pending migrations
../.venv/bin/alembic current            # show applied revision
../.venv/bin/alembic history            # show revision history (downgrade: base)
```

The URL is read from `BARKLY_DATABASE_URL` (env) or `.env` — never duplicated
in `alembic.ini`. Migrations are portable (no PostgreSQL-only constructs) and
verified against both SQLite and PostgreSQL.

## 5. Running the API

```sh
cd backend
../.venv/bin/uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Liveness: http://localhost:8000/health
- Readiness: http://localhost:8000/ready

## 6. Testing

The suite runs hermetically on in-memory SQLite by default:

```sh
cd backend
BARKLY_ENVIRONMENT=test ../.venv/bin/pytest
```

Run against real PostgreSQL (also verifies the migration path there):

```sh
BARKLY_ENVIRONMENT=test \
BARKLY_DATABASE_URL=postgresql+asyncpg://barkly@127.0.0.1:5455/barkly_test \
TEST_POSTGRES_URL=postgresql+psycopg://barkly@127.0.0.1:5455/barkly_test \
../.venv/bin/pytest
```

The same `pytest` invocation exercises Alembic upgrade/downgrade automatically.

### Lint & format

```sh
../.venv/bin/ruff check app tests migrations
../.venv/bin/ruff format --check app tests
```

## 7. Project layout

```
app/
├── main.py                 # create_app(): middleware, error handlers, routers
├── core/                   # config, logging, request context, security, errors
├── db/                     # engine, Base, ORM models
├── domain/                 # string taxonomies (enums), value objects
├── schemas/                # Pydantic request/response models
├── repositories/           # ownership-scoped data access
├── services/               # analysis lifecycle, dogs, media, feedback
├── ai/                     # provider interface + registry + placeholder
├── media/                  # content validation + storage abstraction
├── dependencies/           # bearer-token auth dependency
└── api/v1/                 # routers + serializers
```

## 8. Quick smoke check

Register a user, create a dog, upload an audio file, and run an analysis:

```sh
BASE=http://localhost:8000/api/v1
TOKEN=$(curl -s -X POST $BASE/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"a-strong-password!"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

DOG=$(curl -s -X POST $BASE/dogs -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"Max"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')

MEDIA=$(curl -s -X POST $BASE/media/upload -H "Authorization: Bearer $TOKEN" \
  -F 'media_type=AUDIO' -F 'file=@/path/to/bark.mp3' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["media_id"])')

curl -s -X POST $BASE/analyses -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"dog_id\":\"$DOG\",\"input_type\":\"AUDIO\",\"media_ids\":[\"$MEDIA\"],\"idempotency_key\":\"demo-1\"}"
```