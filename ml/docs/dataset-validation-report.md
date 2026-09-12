# BARKLY Dataset Validation Report

Companion to [`dataset-research.md`](./dataset-research.md) and
[`dataset-card.md`](./dataset-card.md). This report documents the **dataset
verification** (gate §6) and **quality gate** (gate §8) findings for every
dataset actually ingested by the pipeline. It records what was claimed,
what was found, and what was removed and why.

> Verification was performed on the downloaded copies under
> `ml/data/raw/`. Counts below are from inspecting the actual files and label
> files, not from dataset descriptions.

---

## 1. Barkopedia Dog Activity & Environment (`barkopedia-activity-env`)

### 1.1 Claim verification

| Claim | Advertised | Verified |
|-------|-----------|----------|
| Training clips | 12,480 | 12,480 WAV files present (100% match) |
| Label rows | 12,480 | 12,480 rows in `train_label.csv` (100% match) |
| 1:1 label/clip correspondence | — | 0 clips missing a label; 0 label rows without a clip |
| Format | — | WAV, 16 kHz, mono, 16-bit (all 12,480) |
| License | MIT | MIT |

**Advertised = downloaded = valid = usable for this field:** 12,480.

### 1.2 Format & duration distribution

- Sample rate: 16,000 Hz mono (uniform).
- Duration: 0.064 s – 93.4 s. Distribution is heavily short-tailed:

| Duration bucket | Clips | Share |
|-----------------|-------|-------|
| < 1 s | 6,249 | 50.1% |
| 1 – < 3 s | 4,602 | 36.9% |
| >= 3 s | 1,629 | 13.0% |

**Implication:** ~50% of clips are under 1 second and ~87% under 3 seconds.
The training preprocessor pads/truncates to a fixed 3.0 s window, so for the
majority of clips the window is mostly padding/silence. This is a material
quality issue for the task and is one reason model accuracy is moderate.

### 1.3 Label consistency

`train_label.csv` uses 21 distinct raw strings for the same 8 categories due
to inconsistent capitalization (`rest`/`Rest`, `Seeking attention`/
`Seeking Attention`, etc.). `_normalize_label` collapses these to 8 canonical
labels. The environment column is misspelled `environement` (sic) in both the
CSV and the consuming code.

Canonical class distribution (post-normalization, post-dedup):

| Label | Count | Share |
|-------|-------|-------|
| seeking_attention | 1,818 | 14.6% |
| playing_with_human | 1,797 | 14.4% |
| playing_with_toy | 1,779 | 14.3% |
| playing_with_other_animals | 1,774 | 14.2% |
| rest | 1,770 | 14.2% |
| alerting_to_sounds | 1,754 | 14.1% |
| taking_shower | 1,245 | 10.0% |
| begging_for_food | 541 | 4.3% |

Six of eight classes are near-balanced; `taking_shower` (~10%) and
`begging_for_food` (~4%) are undersampled.

### 1.4 Validity checks

- Corrupt/unreadable WAV files: **0 / 12,480**
- Zero-byte files: **0**
- Fully silent clips (zero peak in first 2 s): **0**

### 1.5 Removals

| Step | Removed | Reason |
|------|---------|--------|
| Exact-duplicate (SHA-256) | 2 clips (`audio_06189`, `audio_08541`) | Same bytes; one representative kept |
| Label inconsistencies | 0 (normalized in place) | Case variants collapsed, not dropped |

**Usable after prep:** 12,478. Split (seed 42, random): train 8,734 / val
1,871 / test 1,873.

### 1.6 Remaining quality risks

- **Regime mismatch:** labels are behavioral *context* produced by a VLM
  (Janus-Pro-7B) then manually verified; systematic VLM bias cannot be
  measured from the data.
- **Short clips:** ~87% under 3 s means training windows carry real signal
  for only a minority of clips.
- **No dog identity / breed metadata:** per-dog generalization and per-dog
  splits are impossible; random split is the only option (documented in the
  pipeline report).
- Background-noise variability from online video sources.

---

## 2. DogPoseCV (`dogpose-cv`)

### 2.1 Claim verification

The HF README advertises 20,578 images with a specific class distribution;
the actual downloaded package differs in both total count and distribution.

| Claim | Advertised (README) | Verified (actual files) |
|-------|--------------------|------------------------|
| Total images | 20,578 | 20,730 on disk (20,580 breed folders + 150 in `validation/`) |
| Label rows (CSV) | — | 20,423 rows across 119 per-breed CSVs (`id,label`) |
| standing | 4,143 | 7,047 |
| sitting | 3,038 | 3,008 |
| lying down | 7,090 | 4,110 (`lying`) |
| undefined | 6,307 | 6,258 |

**Verified counts therefore replace the README numbers.** The README's
distribution does not match the shipped label files; the label CSVs are
treated as the source of truth.

Note discrepancies with the advertised figure:
- The package ships a `validation/` sub-directory (150 images) inside
  `data/images/` that has no labels included in the per-breed CSVs and is
  **not** part of the labeled training population.
- 139 `validation/` files duplicate labeled breed-folder files **by
  filename** and are byte-identical to them; the other 11 validation images
  have no label rows at all.

### 2.2 Label consistency

Pose labels are objectively checkable (unlike emotion labels). Canonical
post-normalization class distribution (post-dedup, n=20,197):

| Label | Count | Share |
|-------|-------|-------|
| standing | 6,983 | 34.6% |
| undefined | 6,190 | 30.6% |
| lying | 4,055 | 20.1% |
| sitting | 2,969 | 14.7% |

Imbalanced: `standing` is 2.4x more frequent than `sitting`, and `undefined`
(~31%) reflects images the annotators could not confidently label.

### 2.3 Validity checks

- Corrupt/unreadable JPEG files: **0 / 20,730**
- Zero-byte files: **0**

### 2.4 Removals

| Step | Removed | Reason |
|------|---------|--------|
| Unlabeled (no CSV row) | 168 image files (20,730 – 20,562) | `validation/` files and breed-folder images without a label row; they carry no supervision signal |
| Exact-duplicate (SHA-256) | 226 duplicate groups; 365 sample instances | Byte-identical images appear in multiple breeds/folders (incl. the 139 `validation/` copies sharing a name with labeled breed images) |

**Usable after prep:** 20,197. Split (seed 42, random): train 14,137 / val
3,029 / test 3,031.

### 2.5 Remaining quality risks

- **Identity leak unaddressed:** no verified per-dog identity. Several
  byte-identical duplicates across breeds suggest the same dog/screenshot may
  recur under different filenames; we removed exact duplicates but not
  near-duplicates (perceptual), which is documented as a limitation.
- **`undefined` class** is large and contributes limited behavioral signal.
- Static frames only — pose, not body-language state.
- Web-scraped: variable lighting/angles/backgrounds; breed labels retained as
  ImageNet-style folder names (metadata only).

---

## 3. Duplicate / near-duplicate and leakage summary

| Dataset | Duplicate check | Near-duplicate check | Cross-split leakage after prep |
|---------|-----------------|----------------------|--------------------------------|
| Barkopedia | yes (SHA-256, 2 groups) | no (not practical at this size; documented) | none (hash/id/dog) |
| DogPoseCV | yes (SHA-256, 226 groups) | no (not run; documented) | none (hash id only; no dog identity) |

Dog identity is **not available** for either dataset. Per-gate §9, the
pipeline therefore:
- splits by random seed 42 (documented in
  `ml/data/manifests/pipeline_report.json`), and
- explicitly documents that identity-based train/test separation cannot be
  guaranteed.

---

## 4. Advertised vs downloaded vs usable counts (gate §6)

### Barkopedia (`barkopedia-activity-env`)

| Stage | Count |
|-------|-------|
| Advertised (README) | 12,480 |
| Downloaded (files present) | 12,480 |
| Valid (readable WAV) | 12,480 |
| Usable labeled | 12,480 |
| After exact-dup removal | 12,478 |
| After split (train/val/test) | 8,734 / 1,871 / 1,873 |

### DogPoseCV (`dogpose-cv`)

| Stage | Count |
|-------|-------|
| Advertised (README) | 20,578 |
| Downloaded (files present) | 20,730 |
| Valid (readable JPEG) | 20,730 |
| Labeled (CSV rows)** | 20,423 unique IDs; 20,562 file matches incl. duplicate-name `validation/` copies |
| Removed: unlabeled | 168 |
| Usable labeled, pre-dedup | 20,562 |
| Removed: exact duplicates | 365 sample instances (226 groups) |
| Usable after prep | 20,197 |
| After split (train/val/test) | 14,137 / 3,029 / 3,031 |

** The 20,423 unique label rows all correspond to breed-folder images; the
extra 139 matched files are the `validation/`-folder copies sharing those
filenames.

---

## 5. Reproducibility

Data preparation is fully reproducible:

```sh
cd ml
# re-derives processed splits + pipeline report from the raw download
.venv/bin/python scripts/prepare_real_datasets.py \
  --raw data/raw --processed data/processed \
  --report data/manifests/pipeline_report.json
```

Split sizes and class distributions are deterministic (seed 42) and match the
committed `ml/data/manifests/pipeline_report.json`.

---

## 6. Tooling

| Check | Where |
|-------|-------|
| Exact-duplicate detection | `ml/src/data/leakage.py` (`detect_exact_duplicates`) |
| Cross-split leakage check | `ml/src/data/leakage.py` (`detect_cross_split_leakage`) |
| Splitting | `ml/src/data/splitter.py` |
| Label normalization | `ml/src/data/manifest.py` (`_normalize_label`) |
| Pipeline orchestrator | `ml/scripts/prepare_real_datasets.py` |
| Per-dataset inspection | `ml/scripts/inspect_dataset.py` |