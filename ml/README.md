# BARKLY ML

Machine learning module for BARKLY dog behavioral classification.

## Structure

```
ml/
  configs/          Training configuration YAML files
  data/
    external/       Downloaded raw datasets
    interim/        Intermediate processed data
    manifests/      Dataset registry and manifest files
    processed/      Cleaned, split datasets ready for training
    raw/            Unprocessed source data
  docs/             Dataset research and documentation
  experiments/      Saved model artifacts, metrics, and reports
  scripts/          Runnable CLI scripts
  src/              Core ML library code
    audio/          Audio preprocessing, feature extraction, augmentation
    data/           Manifest handling, validation, dataset utilities
    evaluation/     Model evaluation and metrics
    inference/      Inference pipeline
    models/         Model definitions
    training/       Training loops and utilities
    utils/          Shared helpers
    vision/         Vision preprocessing and augmentation
  tests/            Pytest test suite
  pyproject.toml    Package metadata and dependencies
```

## Quick Start

### Install

```sh
cd ml
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Inspect a Dataset

```sh
python scripts/inspect_dataset.py data/raw/barkopedia-activity data/manifests/inspection_report.json
```

### Prepare a Dataset

The real-data pipeline ingests Barkopedia (audio) and DogPoseCV (vision),
dedupes exact duplicates, runs leakage-safe splits, and writes processed
manifests plus a report:

```sh
python scripts/prepare_real_datasets.py \
  --raw data/raw --processed data/processed \
  --report data/manifests/pipeline_report.json
```

### Train Audio Model

```sh
# Baseline (Random Forest)
python scripts/train_audio.py configs/audio_baseline.yaml \
  --manifest data/processed/barkopedia-activity/manifest.yaml \
  --output experiments/audio_baseline

# CNN
python scripts/train_audio.py configs/audio_cnn.yaml \
  --manifest data/processed/barkopedia-activity/manifest.yaml \
  --output experiments/audio_cnn
```

### Train Vision Model

```sh
python scripts/train_vision.py configs/vision_baseline.yaml \
  --manifest data/processed/dogpose-cv/manifest.yaml \
  --output experiments/vision_baseline
```

### Evaluate

End-to-end evaluation runs the test split through the **production inference
engine** and reports per-class metrics, confusion matrix, calibration (ECE),
and OOD/UNKNOWN analysis:

```sh
python scripts/evaluate_model.py audio \
  data/processed/barkopedia-activity-env/manifest.yaml \
  --model-dir experiments/audio_cnn --config configs/audio_cnn.yaml \
  --output experiments/audio_cnn/evaluation.json

python scripts/evaluate_model.py vision \
  data/processed/dogpose-cv/manifest.yaml \
  --model-dir experiments/vision_baseline --config configs/vision_baseline.yaml \
  --output experiments/vision_baseline/evaluation.json
```

### Export Model

```sh
python scripts/export_model.py \
  --model-dir experiments/audio_baseline \
  --output-dir experiments/audio_baseline/exported \
  --config configs/audio_baseline.yaml \
  --modality audio --version 0.1.0
```

## Run Tests

```sh
cd ml
pytest tests/ -v
```

## Dataset Registry

All candidate datasets are documented in `data/manifests/dataset_registry.yaml` with licensing, limitations, and BARKLY suitability assessments.

### Selected Datasets

| Dataset | Modality | Task | Samples | License |
|---------|----------|------|---------|---------|
| Barkopedia Activity & Environment | Audio | Behavioral context | 12,480 (12,478 after dedup) | MIT |
| DogPoseCV | Vision | Pose classification | 20,730 (20,197 after dedup) | Apache 2.0 |

### Supplementary Datasets

| Dataset | Modality | Task | Samples | License |
|---------|----------|------|---------|---------|
| Barkopedia Emotion | Audio | Arousal/valence | 1,400 | MIT |
| Dog Emotion Dataset v2 | Vision | Emotion classification | 4,000 | OpenRAIL-M |

## Key Design Decisions

- **Observable labels only.** Model outputs are behavioral observations, not emotional diagnoses. UNKNOWN is a valid class.
- **Dog-level splitting.** When dog identity is available, samples from the same dog stay in the same split to prevent data leakage.
- **File hash deduplication.** SHA-256 hashes detect exact duplicates across splits before training.
- **Manifest-driven.** All data flows through YAML manifests for reproducibility and auditability.
- **Model cards.** Every exported model includes a MODEL_CARD.md documenting capabilities and limitations.

## Configuration

Training configs live in `configs/` as YAML files:

| Config | Model | Use Case |
|--------|-------|----------|
| `audio_baseline.yaml` | Random Forest | Quick baseline, feature-based |
| `audio_cnn.yaml` | CNN | End-to-end mel spectrogram |
| `vision_baseline.yaml` | MobileNetV3 | Transfer learning for images |
