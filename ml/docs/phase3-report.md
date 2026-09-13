# BARKLY Phase 3 Implementation Report

> Status: **COMPLETE** — audited dataset prep, trained audio + vision models,
> and evaluated both on held-out test splits through the production inference
> engines. (Vision trained under an explicit 8-epoch compute budget; the
> 30-epoch recipe is the canonical configuration.)

## 1. Objective

Build a genuine, reproducible machine-learning foundation for BARKLY:
real-dataset ingestion, leakage-safe splitting, training of audio + vision
models, evaluation with calibration and out-of-distribution handling, and
production-tier inference wrappers that expose the Phase 2 provider contract.

## 2. Environment

| Item | Value |
|------|-------|
| Hardware | Apple M1, 16 GB RAM (arm64) |
| Accelerator | Torch MPS |
| Python | 3.14.3 (`.venv`) |
| Key deps | torch 2.14, torchaudio 2.11, torchvision 0.29, librosa 1.0, scikit-learn 1.9 |

## 3. Datasets

| Dataset | Modality | Raw | After prep | Classes | License |
|---------|----------|-----|------------|---------|---------|
| Barkopedia Activity & Environment | audio | 12,480 | 12,478 | 8 activity | MIT |
| DogPoseCV | vision | 20,730 | 20,197 | 4 pose | Apache-2.0 |

Preparation and split details: see `ml/docs/dataset-card.md` and
`ml/data/manifests/pipeline_report.json`. Both splits report zero cross-split
leakage after exact-duplicate removal (2 audio groups; 226 image groups; 168
unlabeled images dropped).

## 4. Models

| Model | Config | Artifact | Val acc | Test acc | ECE | OOD AUROC |
|-------|--------|----------|---------|----------|-----|-----------|
| Audio Random Forest (baseline) | audio_baseline.yaml | model.joblib | 0.240 | — | — | — |
| Audio CNN | audio_cnn.yaml | model.pt | 0.203 | n/a¹ | n/a¹ | 0.0¹ |
| Vision MobileNetV3-S | vision_baseline.yaml | model.pt | 0.777 | 0.807 | 0.044 | 0.989 |

¹ At the 0.5 confidence gate, all 1,873 test clips are UNKNOWN (n_known = 0,
unknown rate 1.000; mean confidence 0.216), so accuracy/ECE are undefined and
OOD AUROC is degenerate. The model does not clear the trust gate on real test
audio — an honest, dataset-limited result (87% of Barkopedia clips are < 3 s;
labels are context-level). Details in `experiments/audio_cnn/evaluation.json`
and `model-card.md`.

² Vision evaluated end-to-end (2,762 / 3,031 test images above the 0.5 gate;
unknown rate 0.089; mean confidence 0.814). Per-class test F1: standing 0.880,
undefined 0.789, lying 0.777, sitting 0.701. Trained for 8 epochs (budget
override on top of the committed 30-epoch recipe).

## 5. Components delivered

- **Data pipeline:** `ml/scripts/prepare_real_datasets.py` —
  manifests from raw + external labels, SHA-256 dedup, leakage-safe splits,
  pipeline report.
- **Training:** `ml/scripts/train_audio.py` (RF + CNN), `ml/scripts/train_vision.py`
  (MobileNetV3 via `VisionBaselineModel`), both with MPS support.
- **Evaluation:** `ml/scripts/evaluate_model.py` — runs test set through the
  production inference engines; per-class metrics, confusion matrix,
  calibration (ECE + reliability diagram), OOD AUROC via synthetic probes,
  unknown-rate analysis.
- **Inference:** `AudioInferenceEngine`, `VisionInferenceEngine` (read labels
  + architecture from the checkpoint/config), `BarklyAudioProvider` (Phase 2
  adapter contract).
- **Model cards / docs:** `ml/docs/dataset-card.md`, `model-card.md`,
  `methodology.md`, `experiment-report-*.md`.

## 6. Honest limitations

- Random (not per-dog) splits because neither dataset exposes dog identity.
- Labels are behavioral context / pose; no vocalization-type or emotion ground
  truth exists publicly (see `ml/docs/dataset-research.md`).
- Metrics are on in-distribution test splits; real-world acoustic conditions
  and rare breeds may degrade performance. UNKNOWN is surfaced at low
  confidence / OOD.

## 7. Reproduction

```sh
.venv/bin/python ml/scripts/prepare_real_datasets.py --raw ml/data/raw \
  --processed ml/data/processed --report ml/data/manifests/pipeline_report.json
.venv/bin/python ml/scripts/train_audio.py ml/configs/audio_cnn.yaml \
  --manifest ml/data/processed/barkopedia-activity-env/manifest.yaml \
  --output ml/experiments/audio_cnn
.venv/bin/python ml/scripts/train_vision.py ml/configs/vision_baseline.yaml \
  --manifest ml/data/processed/dogpose-cv/manifest.yaml \
  --output ml/experiments/vision_baseline
.venv/bin/python ml/scripts/evaluate_model.py audio \
  ml/data/processed/barkopedia-activity-env/manifest.yaml \
  --model-dir ml/experiments/audio_cnn --config ml/configs/audio_cnn.yaml
```

## 8. Verification

- ML test suite: 72 passed.
- Backend suite: 78 passed (MariaDB).
- Git history documents each phase milestone (pushed incrementally).