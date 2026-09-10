# BARKLY

BARKLY is an iOS + backend + ML project for AI-enabled dog-behavior interpretation.
This monorepo contains three workstreams:

| Area | Location | Status |
| --- | --- | --- |
| **Phase 1 — iOS app** | `Barkly/`, `BarklyTests/`, `Scripts/` | Complete. Behavior-analysis UX with typed domain models, repositories behind protocols, and a Swift test suite. |
| **Phase 2 — backend** | `backend/` | Complete. FastAPI API + persistence + AI-abstraction foundation with tests and a documented contract. |
| **Phase 3 — ML foundation** | `ml/` | In progress. Dataset research, ingestion tooling, ML pipelines, models, evaluation, inference engine. |

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

- FastAPI (async) + **MariaDB** via async SQLAlchemy + Alembic migrations.
- Ownership-scoped auth (JWT) for dogs, analyses, media, and history.
- Strict analysis lifecycle (`CREATED → QUEUED → PROCESSING → COMPLETED | FAILED`)
  with idempotent creation and first-class failure state.
- **AI provider abstraction** shipping a clearly-labelled development
  placeholder; no fake inference, no fake metrics.
- Versioned API under `/api/v1`, structured JSON logs with request IDs, and a
  standardized error envelope.
- 78-test suite (SQLite in-memory by default, runnable against MariaDB)
  covering auth, dogs, media, analyses, history, feedback, error contract,
  health probes, and migration round-trips.

### Database: MariaDB

BARKLY uses **MariaDB** in production. Development runs SQLite in-memory for
hermetic tests; the async driver is `aiomysql` (with `PyMySQL` for
migrations). Set `BARKLY_DATABASE_URL=mysql+aiomysql://...` to point the API
at a real MariaDB instance. See `backend/README.md → §3` for local setup.

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

## Phase 3 — ML foundation

A genuine machine-learning engineering phase built on real, legally usable
datasets. Priority order: **data quality → leakage prevention →
reproducibility → baseline → model improvement → evaluation → OOD testing →
calibration → model selection → inference integration**.

### Dataset research & selection

Before training, all candidate datasets are documented with provenance,
licensing, sample counts, label taxonomies, and limitations in
[`ml/docs/dataset-research.md`](ml/docs/dataset-research.md). A machine-readable
registry lives in [`ml/data/manifests/dataset_registry.yaml`](ml/data/manifests/dataset_registry.yaml).

Selected primary datasets:

- **Barkopedia Dog Activity & Environment** — 12,480 audio clips, behavioral
  context labels, MIT license.
- **DogPoseCV** — 20,578 dog images, pose/position labels, Apache-2.0.

Selected supplementary datasets:

- **Barkopedia Dog Emotion Classification** — 1,400 audio clips, arousal/valence, MIT.
- **Dog Emotion Dataset v2** — 4,000 images, OpenRAIL-M.

Rejected datasets (with documented reasons) include DogSpeak
(non-commercial license, no vocalization-type labels), ESC-50 (only 40 dog
samples), DEBIw (unclear licensing), CREMD (too small), and DECADE (wrong
perspective).

### What BARKLY CAN and CANNOT claim

- **CAN**: classify observable signals (vocalization patterns, activity,
  pose) using models trained and evaluated on documented datasets.
- **CANNOT**: translate dog "language", diagnose emotions, or make veterinary
  claims. No currently available public dataset provides aligned
  audio+video behavioral labels with dog identity, so multimodal fusion is
  deferred to Phase 4.

### ML quick start

```sh
cd ml
../.venv/bin/pip install -e ".[dev]"
# dataset inspection:
../.venv/bin/python scripts/inspect_dataset.py --help
# prepare a dataset (manifest + validation + split):
../.venv/bin/python scripts/prepare_dataset.py --help
# train audio baseline / CNN:
../.venv/bin/python scripts/train_audio.py --config configs/audio_baseline.yaml
# evaluate + OOD + calibration:
../.venv/bin/python scripts/evaluate.py --help
# run the ML test suite:
cd .. && .venv/bin/pytest ml/tests -q
```

> Datasets and model artifacts are git-ignored; manifests, configs, code, and
> reports are version-controlled. See `ml/README.md` for full details.

## Roadmap

- **Phase 4** — multimodal inference (aligned audio+video), context-aware
  interpretation engine, per-dog personalization, provider hardening.

## Repository layout

```
Barkly/          iOS app (SwiftUI)
BarklyTests/     iOS test suite
Scripts/         Xcode project generation + icon tooling
backend/         FastAPI API, MariaDB persistence, AI provider abstraction
ml/              dataset tooling, models, evaluation, inference engines
```