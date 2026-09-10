# AI Integration

## 1. What Phase 2 does — and doesn't — do

Phase 2 builds the **contract and plumbing** for AI inference. It ships **no** ML
model, no dataset, no metrics, and no dataset-engineering tooling. Those are
explicitly deferred to Phase 3. What exists today:

- A provider interface (`app/ai/base.py`) that real models will implement.
- A registry (`app/ai/providers/__init__.py`) selecting an active provider by
  `BARKLY_AI_PROVIDER`.
- A clearly-labelled **development placeholder** provider that produces
  deterministic, conservative estimates so the full pipeline (create → infer →
  persist → history → feedback) is testable end to end **without pretending to
  be an AI system**.

### Placeholder labelling (anti-fake guardrail)

Everything emitted by the placeholder is transparently marked:

- `provider = "development-placeholder"`
- `model_name = "barkly-placeholder"`
- `model_version = "0.0.0-development"`
- `is_placeholder = true`
- Explanations use tentative language ("may be consistent with…") and every
  result carries the product disclaimer.

No consumer can mistake placeholder output for a trained inference.

## 2. Provider interface

```python
class InferenceProvider(Protocol):
    identity: ModelIdentity              # provider, model_name, model_version, is_placeholder
    async def analyze(self, request: AnalysisInput) -> InferenceResult: ...
    async def health(self) -> bool: ...
```

`InferenceResult` carries: `primary_behavior`, `confidence` (0..1),
`secondary_behaviors`, optional `detected_audio_category`, `observations[]`,
`explanation`, `model`. The service layer normalizes: confidence is clamped
and rounded, behaviors are validated against the canonical taxonomy, and the
disclaimer is attached at the response boundary.

### Inputs

`AnalysisInput` groups:

- `DogContext` — age, breed, sex (for models that use demographics).
- `AudioSignal` — duration, detected `sound_category` (feature flags that a
  Phase 3 model can replace with derived features).
- `VisualSignal` — placeholder for frame/posture features.
- `ContextSignals` — owner presence, activity state, time of day, recent
  feeding/walk/play, strangers/animals, stressful event, location, notes.

Phase 3 feature engineering plugs in here: the interface already carries the
signal types the pipeline will consume; nothing in the API needs to change to
swap `DevelopmentPlaceholderProvider` for a real one.

## 3. Provider errors

The interface allows the provider to raise, and the service maps them:

| Exception | Analysis terminal state | failure.code |
| --- | --- | --- |
| `ProviderUnreachableError` | `FAILED` | `PROVIDER_UNREACHABLE` |
| `ProviderTimeoutError` | `FAILED` | `PROVIDER_TIMEOUT` |
| `ProviderUnavailableError` | `FAILED` | `PROVIDER_UNAVAILABLE` |
| `ProviderError` | `FAILED` | `PROVIDER_ERROR` |
| malformed result (validation) | `FAILED` | `INVALID_PROVIDER_RESPONSE` |

The HTTP response for a terminal analysis is still `200/201` with
`status: "FAILED"` and the failure details — never a server error, because the
resource itself was created successfully and its outcome is known.

## 4. Model versioning

`ModelIdentity` is persisted on every completed analysis (`provider`,
`model_name`, `model_version`, `is_placeholder`). This gives:

- History that is reproducible (results are interpretable knowing which model
  produced them).
- Safe rollout: a new `model_version` is just a new `ModelIdentity`; old rows
  keep their provenance.
- Feedback correctness: corrections snapshot the predicted behavior at the
  time, independent of later model changes.

## 5. Adding a real provider (Phase 3 checklist)

1. Implement `InferenceProvider` (analysis + health) in
   `app/ai/providers/<name>.py` with an accurate `ModelIdentity`.
2. Register it in `app/ai/providers/__init__.py` (or a config-driven registry).
3. Set `BARKLY_AI_PROVIDER` to the new id in the target environment.
4. Add a provider test in `tests/test_ai.py` and, if the model needs assets,
   extend `app/media`/feature extraction.
5. Keep the development placeholder available for offline/dev/testing.

Deferred to Phase 3 (out of scope now): model files/weights, feature
pipelines, GPU/serving infra, dataset versioning, evaluation metrics, and
ML experiment tracking. None of these are required for the API contract to be
complete and stable.