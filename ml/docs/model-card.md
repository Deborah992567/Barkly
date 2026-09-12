# BARKLY Model Cards

Aggregated model cards for BARKLY Phase 3 models. Individual machine-generated
cards ship beside each exported artifact (`experiments/*/MODEL_CARD.md`); this
document is the committed, human-maintained summary.

Every BARKLY model returns observable behavioral signals and an UNKNOWN / OOD
flag when uncertain. Predictions are **observations, not diagnoses**.

---

## 1. Audio Random Forest (baseline)

| Field | Value |
|-------|-------|
| Model version | `barkly-audio-baseline-v0.1.0` |
| Modality | Audio |
| Task | Behavioral context classification (8 Barkopedia activity classes) |
| Architecture | Random Forest (100 trees, class-weighted) |
| Input | Flat MFCC + spectral features per 3.0 s clip @ 22.05 kHz |
| Dataset | Barkopedia Activity & Environment (train 8,734 / val 1,871 / test 1,873) |
| License (data) | MIT |

**Validation performance:** accuracy 0.240; macro F1 0.234; weighted F1 0.237.

**Intended use:** reference ceiling for the hand-crafted-feature approach;
diagnostics and feature sanity checks.

**Limitations:** flat (orderless) features discard temporal structure; several
activity classes are acoustically confusable; below the trust threshold for
standalone deployment.

---

## 2. Audio CNN

| Field | Value |
|-------|-------|
| Model version | `barkly-audio-v0.1.0` (audio_cnn.yaml artifact; v2 config training) |
| Modality | Audio |
| Task | Behavioral context classification (8 classes) |
| Architecture | `AudioCNN` — 3 conv blocks + adaptive pooling + 2 FC layers |
| Input | Log-mel spectrogram `(1, 128, T)` of 3.0 s clip @ 22.05 kHz |
| Training | MPS, Adam+cosine, label smoothing 0.1, seed 42 |
| Dataset | Barkopedia Activity & Environment |
| License (data) | MIT |

**Validation performance (best of 50 epochs):** accuracy 0.203 (chance ≈ 0.125).

**Test-set performance (1,873 clips, confidence gate 0.5):** none of the test
clips cleared the gate — classification accuracy is undefined, unknown rate
1.000. Mean confidence 0.216 (median 0.204, p90 0.288); confidence is flat
across classes. ECE not computable (no gated predictions); OOD AUROC 0.0
(degenerate — the model assigns ≈0.2 max-confidence to both real and
synthetic-noise inputs, so it does not separate them).

**Interpretation:** the CNN is only marginally better than chance and never
rises above the `UNKNOWN` trust threshold for real test audio, so BARKLY
correctly surfaces UNKNOWN rather than an arbitrary class. This is a real,
dataset-limited outcome: 87% of Barkopedia clips are under 3 s (mostly 0.1–1 s)
and were labelled at the *context* level, so the log-mel of a 3 s window is
mostly useless padding. The Random Forest baseline (0.240) tells the same
story. The audio signal is not deployment-ready for `BarklyAudioProvider` as
the sole behavioral signal; see `dataset-validation-report.md`.

**Intended use:** production audio behavioral-context signal for the Phase 2
`BarklyAudioProvider`, with confidence → UNKNOWN gating.

**Limitations:** labels are behavioral context (VLM-generated + verified), not
vocalization types; random split (no dog identity); expected moderate
accuracy; generalization to rare breeds/unseen environments unverified.

---

## 3. Vision MobileNetV3-Small

| Field | Value |
|-------|-------|
| Model version | `barkly-vision-v0.1.0` |
| Modality | Image |
| Task | Dog pose classification (4 classes: standing / sitting / lying / undefined) |
| Architecture | MobileNetV3-Small (ImageNet init) + linear head |
| Input | 224×224 RGB image |
| Training | MPS, Adam; frozen-backbone (linear probe) and/or fine-tune variants |
| Dataset | DogPoseCV (train 14,137 / val 3,029 / test 3,031) |
| License (data) | Apache-2.0 |

**Performance:** to be completed after the vision training + test-set
evaluation finishes (training in progress on this machine).

**Intended use:** per-frame pose observation used as a visual behavioral
signal; supports future multimodal fusion (Phase 4).

**Limitations:** pose is a physical signal, not a behavioral state; the large
`undefined` class reflects ambiguous images; static frames only; web-scraped
images vary in quality.

---

## 4. Shared ethical & usage notes

- Predictions must be interpreted by a human; models do not replace
  veterinary or behavioral-consultant advice.
- Low-confidence (`< 0.5`) and OOD inputs are surfaced as UNKNOWN rather than
  forced into a class.
- Training/evaluation data are documented and leakage-checked (see
  `dataset-card.md`, `methodology.md`).