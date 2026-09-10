# Analysis Lifecycle

This document specifies how an analysis moves from request to terminal state,
how retries stay safe, and how failures become first-class state.

## 1. States

```
               ┌────────────────────────────┐
               │           CREATED          │
               └──────────────┬─────────────┘
                              │ queue
                              ▼
               ┌────────────────────────────┐
               │           QUEUED           │
               └──────────────┬─────────────┘
                              │ processing
                              ▼
                  ┌─────────────────────┐
                  │      PROCESSING     │
                  └────┬───────────┬────┘
                 success │           │ provider failure
                         ▼           ▼
                  ┌─────────────┐ ┌───────────┐
                  │  COMPLETED  │ │  FAILED   │
                  └─────────────┘ └───────────┘
```

State is stored as a string (`AnalysisStatus`). Transitions are one-way:

1. `CREATE` — record created (`CREATED`).
2. `queue` — accepted by the executor (`QUEUED`).
3. `processing` — executor begins (`PROCESSING`).
4. `COMPLETED` — provider returned a valid `InferenceResult`, persisted with
   observations, explanatory text, model identity, and disclaimer.
5. `FAILED` — provider error (unreachable/timeout/unavailable/invalid
   response). `failure.code` and `failure.message` are persisted.

## 2. Ordering and transactional boundaries

The service deliberately does **not** hold a DB transaction while the provider
runs:

```
create+commit (CREATED)
   └─ queue+commit (QUEUED)
       └─ processing+commit (PROCESSING)
           └─ provider inference  ← no locks held here
               ├─ complete+commit (COMPLETED)   ─ result, observations, timestamps
               └─ fail+commit (FAILED)          ─ failure code/message
```

Rationale: inference is the longest, least predictable step. Running it fully
outside transactions prevents long-lived locks, deadlocks with other writes,
and partial state if the process dies mid-inference.

## 3. Idempotent creation

`POST /api/v1/analyses` takes an optional `idempotency_key` (opaque, max 128
chars, scoped **per user**).

On a request with an existing `idempotency_key` for the same user, the service
returns the already-created analysis instead of creating a duplicate. This
makes retries after network failures safe. The key is bound to the user, so
two different users can safely reuse a key without collision.

```
if key and existing = repo.get_by_idempotency(user_id, key):
    return existing            # replay; no new row, no side effects
else:
    create + enqueue + run     # new analysis
```

## 4. Failure semantics

Provider failures don't become HTTP errors — the analysis is a persisted
resource with a terminal state:

```json
{
  "analysis_id": "…",
  "status": "FAILED",
  "failure": { "code": "PROVIDER_UNAVAILABLE", "message": "Inference provider could not be reached." },
  "result": null
}
```

`FailureCode` values: `PROVIDER_UNREACHABLE`, `PROVIDER_TIMEOUT`,
`PROVIDER_UNAVAILABLE`, `PROVIDER_ERROR`, `INVALID_PROVIDER_RESPONSE`.

A `FAILED` analysis still counts toward history and is visible to its owner,
which supports retry UX ("try again with this idempotency key") and telemetry.

## 5. Validation gates at creation

- Dog must exist and be owned by the caller → else `DOG_NOT_FOUND`.
- Referenced media (for `AUDIO`/`VIDEO`/`IMAGE`) must be owned by the caller
  and not already linked to another analysis → else `RESOURCE_NOT_FOUND`.
- `BEHAVIOR` input requires an empty `media_ids`.
- `sound_category` only for `AUDIO`; `duration_ms` only for `AUDIO`/`VIDEO`.

## 6. Response invariants

- `status` is always returned.
- `result` is non-null only when `status == COMPLETED`.
- `failure` is non-null only when `status == FAILED`.
- `media` is always an array (immutable input snapshot).
- `context` is always the snapshot used for the analysis (may be partial).
- A `version` field is present for optimistic concurrency in later phases.