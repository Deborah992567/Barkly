# BARKLY Phase 4 Integration Report

Live iOS client ↔ FastAPI backend ↔ real machine-learning models.

## System overview

```
iOS app (Swift/SwiftUI)
  ├─ APIClient (HTTP JSON + multipart media upload, Bearer auth, request ids)
  ├─ Repositories: dogs, media, analyses, feedback, history, insights
  ├─ Auth flow (login/register, Keychain-backed session)
  └─ Analysis flows: audio recording, video/photo upload, behavior notes,
       all enriched with optional owner context, then owner-feedback loop
        |
        v
FastAPI (backend/app, /api/v1)
  ├─ auth:      POST /auth/register, /auth/login
  ├─ dogs:      GET/POST /dogs, GET/PATCH /dogs/{id}
  ├─ media:     POST /media/upload (multipart, type + duration)
  ├─ analyses:  POST /analyses (create + run), GET /analyses/{id}
  ├─ feedback:  POST /analyses/{id}/feedback (CONFIRMED | INCORRECT | CORRECTED)
  └─ history:   GET /history (paged, filterable by dog/behavior)
        |
        v
AI provider "barkly-models" (backend/app/ai)
  ├─ audio:      barkly-audio-cnn-v2 (experiments/audio_cnn_v2)
  ├─ vision:     barkly-vision-mobilenet-v3-small (experiments/vision_baseline)
  ├─ fusion:     barkly-fusion-1.0.0
  └─ interpretation: probabilities -> BehaviorState + explanation + safety note
        |
        v
Persistence: results + signals + model lineage (traceability) + owner feedback
```

## Live end-to-end run (proof)

Hermetic run against a throwaway SQLite DB with `BARKLY_AI_PROVIDER=barkly-models`,
served by uvicorn on `127.0.0.1:8765`, exercised exactly the endpoints the iOS
client calls:

| Step | Endpoint | Result |
| --- | --- | --- |
| Register | `POST /api/v1/auth/register` | 200, `access_token` |
| Create dog | `POST /api/v1/dogs` | `Rex` id created |
| Upload audio | `POST /api/v1/media/upload` (multipart WAV, 2.5 s) | media id created |
| Run analysis | `POST /api/v1/analyses` (AUDIO + context) | 201, status `COMPLETED` in ~4.5 s |
| History | `GET /api/v1/history?page=1&page_size=5` | item present |
| Confirm | `POST /analyses/{id}/feedback` verdict `CONFIRMED` | applied |
| Correct | `POST /analyses/{id}/feedback` verdict `CORRECTED` -> `EXCITED` | applied |

Analysis response highlights (real model, not placeholder):

- provider `barkly-models`, model `barkly-multimodal-v1` v1.0.0
- audio model `barkly-audio-cnn-v2`, vision model `barkly-vision-mobilenet-v3-small`
- fusion + interpretation versions and preprocessing/dataset versions recorded
- observation + explanation + disclaimer strings generated
- demo WAV is low quality -> honest `UNKNOWN` result with
  `is_insufficient_evidence: true` and `signals_available.audio_quality: low`
  (the app surfaces this as its "not enough evidence" state)

## Running it

Backend (MariaDB or SQLite for local smoke testing):

```bash
cd backend
.venv/bin/alembic upgrade head
BARKLY_AI_PROVIDER=barkly-models .venv/bin/uvicorn app.main:app --port 8000
```

The app defaults to `http://127.0.0.1:8000` (override with `BARKLY_API_BASE_URL`)
and switches to the live backend whenever it is available.

iOS: generate the project, build, and run on a simulator/device:

```bash
python3 Scripts/generate_project.py
xcodebuild -project Barkly.xcodeproj -scheme Barkly \
  -destination 'platform=iOS Simulator,name=iPhone 17' test
```

## Test status

- Backend pytest: 90 passed (auth, dogs, media, analyses, feedback, history,
  AI/fusion, provider, error contract, migrations), ruff clean.
- iOS XCTest: full suite green (API decoding, flow controller, app container,
  mock repositories, deterministic analysis, time greeting).
- Git history: 7 commits pushed to `origin/master` for the phase.

## Observations / notes

- `inference_latency_ms` reports the fused pipeline timing; it may read 0 in single
  media-type runs where no fusion commit is produced. Cosmetic only.
- Low-confidence/low-quality inputs are reported as `UNKNOWN` +
  `is_insufficient_evidence=true` rather than guessed, and owner feedback
  (`CORRECTED` with `corrected_behavior`) becomes the label used for future
  interpretation, closing the loop.
- Model lineage (provider, model names/versions, preprocessing + dataset + fusion
  versions) is persisted per analysis for auditability.

## Phase 4.1: production polish and integration completion

Live screens that previously leaned on demo data are now fully server-backed:

- **Dogs**: create (`POST /dogs`) and edit (`PATCH /dogs/{id}`) from dedicated
  iOS forms wired into Home's empty state, the dog switcher, and Profile. The
  server-confirmed dog is stored and selected; failures surface inline.
- **History**: `GET /history` drives a paged feed with pull-to-refresh,
  incremental pagination, empty/error/offline states, and status-aware rows.
  Rows open a result only when the server reports `COMPLETED`; queued, running,
  failed, and cancelled runs show a status row instead.
- **Insights**: `DerivedInsightsRepository` aggregates live history. Patterns
  are computed only from completed analyses; `is_insufficient_data` gates
  pattern claims below three usable interpretations, and trend copy hedges
  explicitly ("tendencies in the moments captured, not a diagnosis").
- **Feedback**: submission failures now surface inline with retry instead of a
  false success toast.

Mock/seed data is confined to `AppDependencies.demo`, previews, and tests; see
`docs/mock-data-audit.md`. The shipped path only ever uses the live repositories.

### Test status (end of Phase 4.1)

- Backend pytest: 90 passed, ruff clean (unchanged in 4.1).
- iOS XCTest: full suite green on the simulator, including new coverage for
  `AnalysisStatus` lifecycle mapping, `AppContainer` add/update dog commands,
  paged history (`HistoryPagerTests`), and insights aggregation
  (`DerivedInsightsTests`).
- Git: Phase 4.1 pushed incrementally to `origin/master` (each logical change
  committed and pushed rather than one large dump).