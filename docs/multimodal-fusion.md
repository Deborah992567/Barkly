# Multimodal Fusion Policy (Phase 4)

This document is the source of truth for how BARKLY turns model outputs and
context into a behavioral interpretation. It exists so the uncertainty policy
is reviewable by people, not just encoded in code.

## Signals and their meaning

| Signal | Source | Meaning |
| ------ | ------ | ------- |
| Audio activity | Phase 3 CNN (`barkly-audio-cnn-v2`) | Activity context (playing, rest, attention, …), **not** vocalization type, **not** emotion |
| Vision pose | Phase 3 vision (`barkly-vision-mobilenet-v3-small`) | Posture only (standing / sitting / lying / undefined) |
| Context | Owner-provided fields | Circumstances at capture time (owner home/away, recent play/walk/stress, strangers, other animals, …) |

## Honesty constraints

1. **No signal alone claims a behavior.** Every interpretation requires at
   least one *known* (non-UNKNOWN) model output.
2. **No rule emits AGGRESSIVE, FEARFUL, or STRESSED.** BARKLY's models cannot
   read emotional states, and none of the supported evidence implies them.
   These states are out of scope and are never synthesized.
3. **Context never drives a decision.** Context signals are *supports*. An
   interpretation without a confident model signal is UNKNOWN + "insufficient
   evidence".
4. **`taking_shower` audio has no behavioral meaning.** It is recorded as an
   observation only and never becomes an interpretation.
5. **`detected_audio_category` stays UNKNOWN.** The audio model outputs activity
   classes, not vocalization types (bark/whine/…), so BARKLY never claims which
   vocalization type was detected.
6. **The weak audio model is not hidden.** On real clips the model is below the
   0.30 confidence gate essentially always, so results fall to UNKNOWN instead
   of guessing. This is a feature of the policy, not a bug.

## Rules

Rules are ordered; the first rule whose required hints are satisfied wins.

| Rule id | Requires (≥1) | Supports | Contradicts (cross-modal) | Interpretation |
| ------- | -------------- | -------- | ------------------------- | -------------- |
| `play-from-activity` | `AUDIO_PLAYING` | `CONTEXT_PLAYING`, `RECENT_PLAY`, `OTHER_ANIMALS_PRESENT` | `AUDIO_REST`, `VISION_LYING` | PLAYFUL |
| `attention-from-activity` | `AUDIO_ATTENTION`, `AUDIO_FOOD` | `OWNER_PRESENT`, `RECENT_FEEDING` | `AUDIO_REST` | ATTENTION_SEEKING |
| `alert-from-activity` | `AUDIO_ALERTING` | `STRANGERS_PRESENT`, `OTHER_ANIMALS_PRESENT`, `RECENT_STRESS`, `OWNER_AWAY`, `VISION_STANDING` | `AUDIO_REST`, `VISION_LYING` | ALERT |
| `relaxed-from-rest-or-pose` | `AUDIO_REST`, `VISION_LYING` | `CONTEXT_RESTING` | `AUDIO_ALERTING`, `AUDIO_PLAYING`, `AUDIO_ATTENTION`, `VISION_STANDING` | RELAXED |

"Contradicts" is evaluated **cross-modality only**: a known hint from the other
modality listed as a contradiction.

## Confidence formula

```
base            = confidence of the driving (required) model evidence
contradiction   = number of known cross-modal contradictions (see above)
support_bonus   = min(0.12, 0.04 × number of supporting hints)
confidence      = clamp(base × (1 − 0.25 × contradictions) + support_bonus,
                       0.0, min(0.95, base + 0.12))
```

## Conflict handling

When the driving model evidence contradicts known evidence from the other
modality (e.g. confident play audio + confident lying posture), BARKLY does
**not** silently pick the louder signal:

- primary interpretation = **UNKNOWN**
- confidence = `min(driving_conf, 0.40)`
- both observations are preserved, and the rule's interpretation is listed as
  an **alternative** (`secondary_behaviors`)
- the explanation names both signals

## Safety advisories

BARKLY is a monitoring aid, not a diagnosis. Precautionary notes (never
"dangerous" claims) are attached when:

- primary = ALERT (a stress/defensive reaction is plausible → give space), or
- signals were insufficient but alerting audio coincided with strangers /
  other animals / a recent stressful event, or
- interpretation was inconclusive alongside recent stress / strangers.

## Traceability

Every completed analysis persists:

- audio / vision model ids and artifact versions (artifact mtime UTC)
- dataset + preprocessing versions (from `ml/model_registry.yaml`)
- fusion + interpretation system versions (`ai_fusion_version`,
  `ai_interpretation_version`)
- inference latency, the insufficient-evidence flag, and the full
  signal-availability snapshot (`signals_available` JSON).

## Thresholds

| Setting | Value | Meaning |
| ------- | ----- | ------- |
| `ai_audio_confidence_threshold` | 0.30 | below this, audio is UNKNOWN (weak model gate) |
| `ai_vision_confidence_threshold` | 0.50 | below this, vision pose is UNKNOWN |
| `ai_fusion_contradiction_penalty` | 0.25 | per-contradiction multiplier on base confidence |

These are exposed as settings in `backend/app/core/config.py` and are never
silently overridden in code.