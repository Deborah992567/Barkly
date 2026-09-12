# BARKLY ML Methodology

This document describes the Phase 3 machine-learning methodology: dataset
ingestion, leakage prevention, feature engineering, training, evaluation,
calibration, out-of-distribution handling, and model export.

The guiding priorities, in order: **data quality → leakage prevention →
reproducibility → baseline → model improvement → evaluation → OOD testing →
calibration → model selection → inference integration.**

---

## 1. Data ingestion

### 1.1 Sources

- **Barkopedia Dog Activity & Environment** (audio) — 12,480 WAV clips with
  activity + environment labels from `train_label.csv`. MIT.
- **DogPoseCV** (vision) — 20,730 JPEG images with per-breed `id,label` CSVs
  (4 pose classes). Apache-2.0.

Raw data is downloaded with `huggingface_hub.snapshot_download` and kept under
`ml/data/raw/` (git-ignored). MacOS archive junk (`__MACOSX`) is removed.

Claim verification (advertised vs downloaded vs usable counts), validity
checks, and removal rationale are documented in
`ml/docs/dataset-validation-report.md` + `ml/data/manifests/pipeline_report.json`.

### 1.2 Manifest construction

`ml/scripts/prepare_real_datasets.py` is the single reproducible entry point:

1. **Audio:** iterate all `*.wav`, match `audio_id` in `train_label.csv`, and
   build `SampleManifest` entries with normalized labels and environment
   metadata.
2. **Vision:** load `labels/*.csv`, map `id -> label`, iterate images, keep
   only labeled images, and stamp breed metadata.
3. Every sample gets a deterministic **SHA-256 file hash**.
4. **Exact-duplicate detection** (`detect_exact_duplicates`) groups samples by
   hash; all but one member of each group are dropped.
5. **Leakage-safe splitting** (`split_dataset`) with seed 42.
6. **Cross-split leakage check** (`detect_cross_split_leakage`) verifies no
   hash, id, or dog overlap between train/val/test; the result is recorded.
7. Processed manifests and a pipeline report are written to
   `ml/data/processed/` and `ml/data/manifests/pipeline_report.json`.

### 1.3 Label normalization

Labels are normalized with `_normalize_label` (lowercase, whitespace → `_`),
so case variants (`Rest` vs `rest`, `Alerting to sounds` vs
`Alerting to Sounds`) collapse to one canonical class. The normalization is
stored in `SampleManifest.normalized_label` and is the training target.

---

## 2. Leakage prevention

- **Hashes:** exact-duplicate files are removed before splitting; barking
  duplicates across splits would otherwise inflate accuracy.
- **Identity:** Barkopedia provides no dog identity; DogPoseCV provides no
  per-dog identity. Splits are therefore **random** (documented per dataset),
  and `detect_cross_split_leakage` verifies absent hash/id overlap. Per-dog
  generalization is listed as a limitation in the dataset cards.
- **Determinism:** seed 42 + stable ordering so splits are reproducible.

---

## 3. Audio features

- **Preprocessing:** clips are loaded, resampled to 22.05 kHz, and padded or
  truncated to 3.0 s (`AudioPreprocessor` / `preprocess_audio`).
- **Baseline (Random Forest):** flat features from `AudioFeatureExtractor` —
  MFCCs + spectral descriptors — concatenated per clip (no temporal modeling).
- **CNN:** log-mel spectrogram `(1, n_mels=128, T)`; per-sample z-normalization;
  mel spectrograms are **cached to disk between epochs** so each epoch reuses
  precomputed features (a ~10k-file dataset would otherwise re-decode audio
  every epoch).
- `AudioManifestDataset` yields `(1, n_mels, T)` tensors + label index.

**CNN architecture (`AudioCNN`):** 3× conv blocks (32/64/128 channels) with
batch-norm + ReLU + max-pool, adaptive global pooling, two FC layers
(256, 128) with dropout 0.3, and a linear classifier head. This is the same
architecture the inference engine loads, guaranteeing training/eval consistency.

---

## 4. Vision pipeline

- **Preprocessing:** resize to 224×224, ImageNet normalization
  (`ImagePreprocessor`). Training uses augmentation — random horizontal flip,
  rotation (±10°), color jitter.
- **Model:** MobileNetV3-Small initialized with ImageNet weights; the final
  classifier is replaced with a 4-way head. The canonical wrapper
  (`VisionBaselineModel`) builds, trains, and saves the model so the inference
  engine can deserialize it exactly.
- Checkpoints save `{"model_state_dict": ..., "labels": [...]}`.

---

## 5. Training

| Setting | Audio RF | Audio CNN | Vision |
|---------|----------|-----------|--------|
| Optimizer | — (RF) | Adam, lr 1e-3, wd 1e-4 | Adam, lr 1e-3 |
| Epochs | — | up to 50 | up to 30 |
| Early stopping | — | 10 (val loss) | 10 (val acc) |
| Scheduler | — | ReduceLROnPlateau(5) | — |
| Batch size | — | 32 | 32 |
| Class weighting | balanced | none | none |
| Device | CPU | MPS/CUDA/CPU | MPS/CUDA/CPU |

Baseline RF establishes the hand-crafted-feature ceiling; the CNN is expected
to exceed it on the same train/val split.

---

## 6. Evaluation

The test split is held out from all training decisions. `evaluate_model.py`
runs the test set **through the production inference engine** (the same code
path served at inference time), then reports:

- overall accuracy, macro/weighted precision-recall-F1;
- per-class precision/recall/F1/support and confusion matrix;
- **calibration:** binned ECE (`compute_calibration_error`) with a
  reliability-diagram table (`reliability_diagram_data`). ECE uses clamped bin
  indexing so values stay in [0, 1];
- **uncertainty/OOD:** max-confidence distribution (percentiles), unknown rate
  at the deployed confidence threshold, and synthetic OOD probes (white-noise /
  silence for audio, noise / flat-color for vision) scored with
  `compute_ood_metrics` → AUROC, FPR@95%TPR, and mean score gap;
- ROC-AUC (macro, one-vs-rest) when probabilities are available.

### 6.1 UNKNOWN handling at inference

The inference engine returns `UNKNOWN` when the maximum class probability falls
below the confidence threshold (default 0.5) or exceeds the OOD threshold
(audio only, energy-based by default). `is_unknown` and `is_ood` flags are
surfaced in `InferenceResult` (and the provider's `ProviderResult`), so
downstream consumers never need to trust low-confidence predictions.

---

## 7. Model export & versioning

`export_model.py` packages trained artifacts with:

- `export_metadata.json` (version, modality, config, metrics summary, export
  time);
- the model weights (`model.pt` / `model.joblib`) and `confusion_matrix.npy`;
- a generated `MODEL_CARD.md`.

Versions follow `barkly-{modality}-v{major}.{minor}.{patch}`
(e.g. `barkly-audio-v0.1.0`). Artifacts live under `ml/experiments/`
(git-ignored); code, configs, and reports are version-controlled.

---

## 8. Reproducibility

- Data prep: `prepare_real_datasets.py`. Seed 42 everywhere.
- Training: `train_audio.py`, `train_vision.py` with committed YAML configs.
- Evaluation: `evaluate_model.py` (production engine path).
- Raw data and artifacts are git-ignored; manifests of split membership,
  pipeline report, code, configs, and docs are committed.
- ML test suite (`ml/tests`, 72 tests) pins the public API of the data,
  models, evaluation, leakage, and inference modules.

---

## 9. Scope & honest limitations

- Labels are **behavioral context / pose**, not vocalization types or emotion
  diagnoses (see `dataset-card.md` and `dataset-research.md`).
- Random rather than per-dog splits because no dataset provides dog identity.
- Online-sourced audio/image data: label noise and quality variance are
  expected; reported metrics are on in-distribution test splits.
- Accuracy expectations are moderate (baseline RF ≈ 0.24 balanced accuracy);
  models are meant to be interpreted by humans, not to stand alone.