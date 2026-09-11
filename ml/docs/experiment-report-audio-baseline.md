# BARKLY Experiment Report — Audio Baseline (Random Forest)

- **Dataset:** Barkopedia Dog Activity & Environment (`barkopedia-activity-env`)
- **Modality:** Audio
- **Model:** Random Forest (flat MFCC + spectral features)
- **Config:** `ml/configs/audio_baseline.yaml`
- **Run command:**
  `train_audio.py configs/audio_baseline.yaml --manifest data/processed/barkopedia-activity-env/manifest.yaml --output experiments/audio_baseline`
- **Seed:** 42
- **Date:** 2026-09-11

## Setup

| Setting | Value |
|---------|-------|
| Train / Val / Test | 8,734 / 1,871 / 1,873 |
| Classes | 8 |
| Features | MFCC (13) + spectral descriptors, flattened per clip |
| n_estimators | 100 |
| Class weight | balanced |

Metrics reported below are on the **validation** split (the training script's
held-out set for early model selection).

## Results (validation)

- **Accuracy:** 0.2400
- **Macro precision / recall / F1:** 0.239 / 0.235 / 0.234
- **Weighted F1:** 0.237

Per-class (P / R / F1 / support):

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| alerting_to_sounds | 0.312 | 0.349 | 0.329 | 278 |
| taking_shower | 0.258 | 0.359 | 0.300 | 184 |
| seeking_attention | 0.267 | 0.270 | 0.268 | 282 |
| playing_with_human | 0.198 | 0.202 | 0.200 | 247 |
| playing_with_toy | 0.249 | 0.190 | 0.215 | 290 |
| playing_with_other_animals | 0.205 | 0.193 | 0.199 | 254 |
| begging_for_food | 0.250 | 0.149 | 0.186 | 74 |
| rest | 0.171 | 0.172 | 0.171 | 262 |

## Interpretation

0.24 balanced accuracy is only slightly above the 0.125 random baseline — the
flat (orderless) hand-crafted features carry little separable signal for these
8 activity contexts, and several classes overlap acoustically. This is the
**baseline ceiling**; the audio CNN (mel spectrogram + temporal conv structure)
is expected to substantially exceed it.

## Artifacts

- `ml/experiments/audio_baseline/model.joblib`
- `ml/experiments/audio_baseline/confusion_matrix.npy`
- `ml/experiments/audio_baseline/metrics.json`
- `ml/experiments/audio_baseline/train.log`