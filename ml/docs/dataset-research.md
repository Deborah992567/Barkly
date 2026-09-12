# BARKLY Dataset Research

This document catalogs all candidate datasets evaluated for BARKLY's ML pipeline, documents selection rationale, and provides honest assessments of data limitations.

---

## 1. BARKLY ML Task Definition

### Audio Task
**Objective:** Classify observable dog vocalizations into distinct types.

**Target Classes:**
- BARK
- WHINE
- WHIMPER
- GROWL
- HOWL
- SIGH
- UNKNOWN

These labels represent observable acoustic categories, not emotional interpretations. A growl is an acoustic event; whether it is "aggressive" or "playful" is contextual and should not be baked into the label.

### Vision Task
**Objective:** Classify observable body language signals from video or image frames.

**Target Classes:**
- RELAXED
- ALERT
- PLAYFUL
- EXCITED
- CURIOUS
- ATTENTION_SEEKING
- FEARFUL
- STRESSED
- AGGRESSIVE
- SUBMISSIVE
- RESTLESS
- UNKNOWN

These labels represent observable behavioral states, not emotional diagnoses. "Stressed" describes a pattern of body language (panting, whale eye, tucked tail), not a clinical assessment.

---

## 2. Search Methodology

Datasets were identified through systematic searches across the following platforms and repositories:

| Source | Type | Search Approach |
|--------|------|-----------------|
| Kaggle | Dataset repository | Keyword search: "dog bark", "dog vocalization", "dog emotion", "dog behavior" |
| HuggingFace Datasets | ML dataset hub | Tag search across audio and vision categories, paper-linked datasets |
| Zenodo | Open science repository | Dog audio, animal behavior datasets |
| Figshare | Research data repository | Dog vocalization, canine behavior |
| ACM Digital Library | Academic papers | Dog sound classification, pet monitoring |
| arXiv | Preprint server | Computer vision for dogs, audio classification |
| GitHub | Code repositories | Dog behavior analysis, bark classification |

**Search terms used:** dog bark, dog vocalization, dog emotion, dog behavior, canine audio, dog pose, dog body language, pet sound classification, dog activity recognition.

**Inclusion criteria:** Must contain dog-specific audio or visual data with some form of labeling. No mixed-animal datasets were included.

**Exclusion criteria:** Datasets with fewer than 100 samples, datasets with completely unclear provenance, datasets with proprietary/non-reproducible licensing.

---

## 3. Candidate Datasets

### 3.1 Audio Candidates

#### 3.1.1 DogSpeak

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/ArlingtonCL2/DogSpeak_Dataset |
| **Authors** | Lekhak, Wang, Dang, Zhu (UT Arlington) |
| **Paper** | ACM MM 2025, DOI: 10.1145/3746027.3758298 |
| **Samples** | 77,202 bark sequences |
| **Duration** | 33.162 hours |
| **Dogs** | 156 individual dogs, 5 breeds (Chihuahua, German Shepherd, Husky, Pitbull, Shiba Inu) |
| **Labels** | breed, sex, dog_id — **NO vocalization type labels** |
| **Format** | WAV, 16kHz |
| **License** | CC BY-NC-SA 4.0 (non-commercial) |
| **Dog identity** | YES (dog_id in metadata) |
| **Provenance** | Sourced from online videos |

**Known limitations:**
- Labels are breed/sex/dog_id — NOT vocalization types (bark, whine, growl, etc.)
- Breed-limited: only 5 breeds represented
- Online video sourcing introduces noise variability (background, recording quality)
- Non-commercial license restricts any commercial deployment

**BARKLY suitability:** LOW for vocalization classification. The labels simply do not match BARKLY's vocalization taxonomy. The dataset is well-constructed for its intended purpose (breed and individual dog identification from bark audio), but that is not BARKLY's task.

**Verdict: REJECTED** for BARKLY audio classification task. Labels do not match BARKLY's vocalization taxonomy.

---

#### 3.1.2 Barkopedia Dog Emotion Classification

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/ArlingtonCL2/BarkopediaDogEmotionClassification_Data |
| **Authors** | UT Arlington ACL2 Lab |
| **Paper** | IJCAI 2025 Challenge |
| **Samples** | 1,400 clips (1,000 train + 400 test) |
| **Dogs** | 2 breeds (Husky, Shiba Inu) |
| **Labels** | arousal (Low/Medium/High), valence (Negative/Neutral/Positive) |
| **License** | MIT |
| **Dog identity** | NO |
| **Provenance** | Derived from Barkopedia source data |

**Known limitations:**
- Very small (1,400 total clips)
- Only 2 breeds — severely limits generalizability
- Arousal/valence labels are dimensional emotion constructs, not vocalization types
- Emotion labels are inherently subjective
- Pre-defined train/test split

**BARKLY suitability:** MEDIUM. Arousal/valence could map to behavioral states but is not vocalization classification. Useful as supplementary emotional state signal alongside primary behavioral labels.

**Verdict: USEFUL** for supplementary emotional state analysis but not primary vocalization task.

---

#### 3.1.3 Barkopedia Dog Activity & Environment

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/ArlingtonCL2/Barkopedia_Dog_Act_Env |
| **Authors** | UT Arlington ACL2 Lab |
| **Paper** | IJCAI 2025 Challenge |
| **Samples** | 12,480 training clips |
| **Labels** | Activity: rest, alerting to sounds, seeking attention, playing with human, playing with other animals, playing with toy, begging for food, taking shower |
| | Environment: indoor, near window, near door, on grass, near other animals, vehicle interior |
| **License** | MIT |
| **Dog identity** | NO |
| **Provenance** | Labels generated by VLM, manually verified |

**Known limitations:**
- Activity labels are behavioral context, not vocalization type
- Labels initially generated by a Vision-Language Model then manually verified — introduces VLM bias
- Activity taxonomy is a fixed set that does not perfectly map to BARKLY's behavioral signals
- No breed or individual dog metadata
- Source videos are online (variable quality, noise)

**BARKLY suitability:** HIGH for behavioral context classification. Activity labels (alerting, seeking attention, playing, resting) map reasonably well to BARKLY's observable behavioral taxonomy. Environment labels provide useful context.

**Verdict: SELECTED** as primary audio behavioral dataset.

---

#### 3.1.4 ESC-50

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/ashraq/esc50 |
| **Author** | Karol J. Piczak |
| **Paper** | ACM MM 2015 |
| **Samples** | 2,000 total (40 per class, 50 classes) |
| **Dog samples** | 40 clips (single "dog" class) |
| **License** | CC BY-NC (non-commercial) |

**Known limitations:**
- Only 40 dog vocalization clips in entire dataset
- Single "dog" class — no differentiation between bark/whine/growl
- Non-commercial license
- Old dataset (2015), audio quality varies

**BARKLY suitability:** VERY LOW. Only 40 dog samples with no sub-classification.

**Verdict: REJECTED.**

---

#### 3.1.5 437aewuh/dog-dataset

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/437aewuh/dog-dataset |
| **Samples** | 300 |
| **Labels** | Unclear / undocumented |
| **License** | Unclear (redistribution of mixed sources) |

**Known limitations:**
- Only 300 samples
- Labels are poorly documented
- License provenance unclear
- Appears to be a redistribution of mixed-source data

**BARKLY suitability:** VERY LOW.

**Verdict: REJECTED.**

---

#### 3.1.6 Dog-Vocal-Separation

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/ArlingtonCL2/Dog-Vocal-Separation |
| **Size** | 180 GB, 281K pairs |
| **Task** | Source separation (not classification) |
| **License** | MIT |

**Known limitations:**
- Task is source separation, not classification
- Massive size (180 GB) impractical for current pipeline
- Useful only if source separation is needed pre-classification

**BARKLY suitability:** LOW for classification. Could be useful for preprocessing if dog audio needs to be separated from background noise.

**Verdict: DEFERRED** — not needed for Phase 3 classification task. Revisit if source separation becomes a pipeline requirement.

---

### 3.2 Vision Candidates

#### 3.2.1 DogPoseCV

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/stockeh/dog-pose-cv |
| **Authors** | Jason Stock, Tom Cavey (Colorado State) |
| **Paper** | arXiv:2101.02380 |
| **Samples** | 20,578 advertised; verified 20,730 files on disk, 20,197 usable after prep |
| **Dogs** | 120 breeds advertised; 119 per-breed label CSVs found |
| **Labels** | README claims standing (4,143), sitting (3,038), lying down (7,090), undefined (6,307); **verified label CSVs say** standing (7,047), undefined (6,258), lying (4,110), sitting (3,008) |
| **License** | Apache 2.0 |
| **Dog identity** | NO |
| **Provenance** | Web-scraped, curated |

> Verification note (2026-09-12): the advertised README class distribution
> does **not** match the shipped label files; the label CSVs are treated as
> the source of truth. See `dataset-validation-report.md`.

**Known limitations:**
- Class imbalance: "lying down" has more than double the samples of "sitting"
- Large "undefined" class (6,307 images) — 30.6% of data
- Pose labels (standing/sitting/lying) are not behavioral states
- No temporal information (static images, not video)
- Web-sourced images may have inconsistent lighting, angles, backgrounds

**BARKLY suitability:** MEDIUM. Pose is an observable physical signal but not a behavioral state directly. However, pose is a useful input feature for inferring behavioral state. Apache 2.0 license is permissive.

**Verdict: SELECTED** as primary vision dataset for pose estimation.

---

#### 3.2.2 Dog Emotion Dataset v2

| Field | Detail |
|-------|--------|
| **URL** | https://huggingface.co/datasets/Dewa/Dog_Emotion_Dataset_v2 |
| **Samples** | 4,000 images |
| **Labels** | sad (0), angry (1), relaxed (2), happy (3) |
| **License** | creativeml-openrail-m |

**Known limitations:**
- Only 4,000 images
- Emotion labels (sad, angry, relaxed, happy) are subjective interpretations, not observable signals
- No breed, age, or identity metadata
- Unknown data collection methodology
- Limited license (OpenRAIL-M) has use restrictions

**BARKLY suitability:** MEDIUM. Emotion labels could serve as soft labels for behavioral state prediction, but must be handled carefully to avoid baking subjective interpretations into the model.

**Verdict: USEFUL** supplementary but labels need careful handling.

---

#### 3.2.3 DEBIw

| Field | Detail |
|-------|--------|
| **URL** | Academic paper (ACI 2022) |
| **Samples** | 15,599 images |
| **Labels** | Emotion: anger, fear, happiness, relaxation |
| **License** | Unclear (web-scraped) |

**Known limitations:**
- Licensing unclear — web-scraped images may have copyright issues
- Emotion labels are subjective interpretations
- No provenance chain documented
- Reproducibility concerns

**BARKLY suitability:** LOW due to licensing uncertainty.

**Verdict: REJECTED** due to licensing uncertainty.

---

#### 3.2.4 CREMD

| Field | Detail |
|-------|--------|
| **URL** | arXiv:2602.15349 |
| **Samples** | 923 video clips |
| **Labels** | Emotion (crowd-sourced) |
| **License** | TBD (research release) |

**Known limitations:**
- Very small (923 clips)
- Crowd-sourced emotion labels — high inter-annotator variability expected
- Multimodal (audio + video) but insufficient data for training
- License not finalized

**BARKLY suitability:** LOW. Too small for training; license unclear.

**Verdict: REJECTED** for training. Useful for evaluation reference if license resolves.

---

#### 3.2.5 DECADE

| Field | Detail |
|-------|--------|
| **URL** | CVPR 2018 |
| **Samples** | 380 video clips, 24,500 frames |
| **Labels** | Ego-centric dog movements |
| **License** | Research use |

**Known limitations:**
- Ego-centric perspective (camera on dog) — not useful for observing dog behavior from outside
- Only 380 clips
- Movement labels, not behavioral interpretation
- Research-only license

**BARKLY suitability:** LOW. Wrong perspective for behavior interpretation.

**Verdict: REJECTED.**

---

## 4. Dataset Comparison Table

### Audio Datasets

| Criterion | DogSpeak | Barkopedia Emotion | Barkopedia Activity | ESC-50 | 437aewuh | Dog-Vocal-Sep |
|-----------|----------|--------------------|---------------------|--------|----------|---------------|
| **Modality** | Audio | Audio | Audio | Audio | Audio | Audio |
| **Samples** | 77,202 | 1,400 | 12,480 | 40 (dog) | 300 | 281K pairs |
| **Duration** | 33.16 hrs | N/A | N/A | ~40s | N/A | 180 GB |
| **Dogs** | 156 | Unknown | Unknown | N/A | Unknown | Unknown |
| **Labels** | breed, sex, dog_id | arousal, valence | activity, environment | dog (1 class) | unclear | source pairs |
| **Label quality** | High (for task) | Moderate (subjective) | Moderate (VLM + verify) | High | Poor | N/A |
| **Class balance** | N/A | 3 arousal x 3 valence | 8 activity classes | Balanced | Unknown | N/A |
| **Dog identity** | YES | NO | NO | NO | NO | NO |
| **Breed diversity** | 5 breeds | 2 breeds | Unknown | N/A | Unknown | N/A |
| **Size** | Large | Small | Medium | Tiny | Tiny | Large |
| **License** | CC BY-NC-SA | MIT | MIT | CC BY-NC | Unknown | MIT |
| **Commercial OK** | NO | YES | YES | NO | Unknown | YES |
| **Provenance** | Online videos | Derived | Online videos | Curated | Mixed | Online videos |
| **Leakage risk** | Medium | Medium | Medium | Low | Unknown | Low |
| **BARKLY fit** | LOW | MEDIUM | **HIGH** | VERY LOW | VERY LOW | LOW |

### Vision Datasets

| Criterion | DogPoseCV | Dog Emotion v2 | DEBIw | CREMD | DECADE |
|-----------|-----------|----------------|-------|-------|--------|
| **Modality** | Image | Image | Image | Video | Video |
| **Samples** | 20,578 advertised / 20,197 usable | 4,000 | 15,599 | 923 | 24,500 frames |
| **Breeds** | 120 (adv.) / 119 CSV | Unknown | Unknown | Unknown | Unknown |
| **Labels** | pose (4 classes) | emotion (4 classes) | emotion (4 classes) | emotion | movement |
| **Label quality** | Moderate (CSV verified) | Subjective | Subjective | Crowd-sourced | Movement-based |
| **Class balance** | Imbalanced | Unknown | Unknown | Unknown | N/A |
| **Dog identity** | NO | NO | NO | NO | NO |
| **Size** | Large | Small | Medium | Small | Medium |
| **License** | Apache 2.0 | OpenRAIL-M | Unclear | TBD | Research |
| **Commercial OK** | YES | Conditional | Unknown | Unknown | NO |
| **Provenance** | Web-scraped | Unknown | Web-scraped | Collected | Collected |
| **Leakage risk** | Low | Low | High | Low | Low |
| **BARKLY fit** | **HIGH** | MEDIUM | LOW | LOW | LOW |

---

## 5. Dataset Selection Justification

### Primary Datasets (SELECTED)

#### Audio: Barkopedia Dog Activity & Environment
- **Why selected:** 12,480 clips is the largest usable dog-specific labeled dataset with behavioral context labels. MIT license permits commercial use. Activity labels (rest, alerting, seeking attention, playing) map reasonably to BARKLY's behavioral taxonomy. Environment labels provide useful context for behavior interpretation.
- **Why not others:** DogSpeak has 77K samples but labels are breed/sex, not vocalization type. ESC-50 has only 40 dog samples. No dataset with vocalization type labels (bark vs. whine vs. growl) was found.

#### Vision: DogPoseCV
- **Why selected:** 20,197 usable images (verified) across ~120 breeds provides the largest and most diverse dog body pose dataset. Apache 2.0 license is fully permissive. Pose (standing/sitting/lying) is an observable physical feature that serves as useful input for behavioral state inference.
- **Why not others:** Dog Emotion v2 has subjective labels and limited license. DEBIw has licensing uncertainty. CREMD is too small. DECADE uses wrong perspective.

### Supplementary Datasets (AUXILIARY)

#### Audio: Barkopedia Dog Emotion Classification
- **Role:** Provides arousal/valence dimensional labels that can supplement activity labels for emotional state context.
- **Limitations:** Small (1,400 clips), only 2 breeds.

#### Vision: Dog Emotion Dataset v2
- **Role:** Provides soft emotion labels (sad/angry/relaxed/happy) that can supplement pose features.
- **Limitations:** Subjective labels, OpenRAIL-M license restrictions.

### Rejected Datasets

| Dataset | Reason for Rejection |
|---------|---------------------|
| **DogSpeak** | Wrong labels (breed/sex, not vocalization type), non-commercial license |
| **ESC-50** | Only 40 dog samples, non-commercial license |
| **437aewuh/dog-dataset** | 300 samples, unclear labels, unclear license |
| **Dog-Vocal-Separation** | Task mismatch (separation not classification), deferred |
| **DEBIw** | Licensing uncertainty, web-scraped images |
| **CREMD** | Too small (923), license TBD |
| **DECADE** | Wrong perspective (ego-centric), research-only license |

---

## 6. Label Mapping

### Barkopedia Activity Labels → BARKLY Audio Taxonomy

| Barkopedia Label | BARKLY Mapping | Confidence | Notes |
|------------------|----------------|------------|-------|
| rest | UNKNOWN / behavioral context | Low | Resting dogs may sigh, whine softly. No direct vocalization mapping. |
| alerting to sounds | ALERT | High | Alert barking is observable. May map to BARK in alert context. |
| seeking attention | ATTENTION_SEEKING | High | Attention-seeking vocalizations (whining, barking) are well-defined. |
| playing with human | PLAYFUL | Medium | Play vocalizations are distinct (play growl, playful bark). |
| playing with other animals | PLAYFUL | Medium | Play behavior context. Vocalizations during play are observable. |
| playing with toy | PLAYFUL | Medium | Solo play vocalizations less studied but observable. |
| begging for food | ATTENTION_SEEKING | Medium | Food-begging involves whining, pawing — partially observable. |
| taking shower | UNKNOWN | Low | Edge case. Vocalizations during bathing are stress-related. |

**Key insight:** Barkopedia labels describe *behavioral context*, not vocalization type. BARKLY must map context to expected vocalization patterns rather than directly mapping labels. This is an indirect mapping and introduces uncertainty.

### Barkopedia Environment Labels → BARKLY Context

| Barkopedia Label | BARKLY Mapping | Notes |
|------------------|----------------|-------|
| indoor | Environment: indoor | Provides recording context |
| near window | Environment: boundary | Window-related alerting behavior |
| near door | Environment: boundary | Door-related alerting behavior |
| on grass | Environment: outdoor | Outdoor context |
| near other animals | Environment: social | Multi-animal context |
| vehicle interior | Environment: vehicle | Confinement context |

### DogPoseCV Pose Labels → BARKLY Visual Signals

| DogPoseCV Label | BARKLY Mapping | Confidence | Notes |
|-----------------|----------------|------------|-------|
| standing | RELAXED, ALERT, PLAYFUL, EXCITED, CURIOUS | Low | Standing is a baseline; behavioral state depends on additional features (ear position, tail, etc.) |
| sitting | RELAXED, ATTENTION_SEEKING | Low | Sitting is a common posture; limited behavioral specificity. |
| lying down | RELAXED, RESTLESS | Low | Lying down could be relaxation or stress-related. |
| undefined | UNKNOWN | N/A | Cannot map — insufficient visual information. |

**Key insight:** Pose alone is insufficient for behavioral state classification. A standing dog could be relaxed, alert, playful, or fearful. Pose must be combined with other features (ear position, tail position, mouth state, gaze direction) for meaningful behavioral classification. BARKLY should use pose as one input feature among many, not as the sole behavioral indicator.

---

## 7. Licensing Analysis

### Barkopedia Dog Activity & Environment
- **License:** MIT
- **Restrictions:** Minimal. Must include copyright notice and license in copies.
- **Commercial use:** YES
- **Attribution required:** YES (must credit original authors)
- **Viral/share-alike:** NO
- **Patent grant:** MIT includes patent grant
- **Risk:** Low. MIT is well-understood and permissive.

### Barkopedia Dog Emotion Classification
- **License:** MIT
- **Restrictions:** Same as above
- **Commercial use:** YES
- **Attribution required:** YES
- **Risk:** Low.

### DogPoseCV
- **License:** Apache 2.0
- **Restrictions:** Must include license, state changes, include copyright notice. Includes explicit patent grant.
- **Commercial use:** YES
- **Attribution required:** YES
- **Viral/share-alike:** NO
- **Patent grant:** YES (explicit)
- **Risk:** Low. Apache 2.0 is permissive and well-established.

### Dog Emotion Dataset v2
- **License:** creativeml-openrail-m
- **Restrictions:** OpenRAIL-M licenses have use restrictions — must not be used for harmful purposes. Specific restrictions vary by implementation.
- **Commercial use:** CONDITIONAL (depends on specific restrictions)
- **Risk:** Medium. Need to review specific license terms for any restrictions beyond standard open-source.

---

## 8. Known Limitations

### Critical Limitations

1. **No dataset directly provides vocalization type classification.** No existing public dataset labels dog audio as bark vs. whine vs. growl vs. howl vs. sigh. This is the single most significant gap. BARKLY cannot train a vocalization classifier from existing public data alone.

2. **Activity labels are behavioral context, not vocalization type.** Barkopedia labels describe what the dog is *doing* (playing, resting, alerting), not what vocalization the dog is *producing*. Mapping context to vocalization is indirect and uncertain.

3. **Vision datasets have subjective emotion labels.** Dog Emotion Dataset v2 labels images as "sad", "happy", "angry", "relaxed" — these are human interpretations, not objective features. A model trained on these labels learns to replicate human bias, not observable body language.

4. **No multimodal aligned dataset exists.** No public dataset provides synchronized audio + video + behavioral labels for dogs. BARKLY's vision and audio models must be trained separately and fused at inference.

### Moderate Limitations

5. **Pose is insufficient for behavioral classification.** DogPoseCV provides standing/sitting/lying — these are necessary but not sufficient features. A standing dog can be alert, playful, or fearful. Additional features (ears, tail, mouth, eyes) are needed but not available in current datasets.

6. **Both primary datasets are sourced from online videos.** This introduces selection bias (people upload interesting/unusual clips), recording quality variability, and potential label noise.

7. **Barkopedia labels were initially generated by a VLM.** The activity labels were machine-generated then manually verified. This introduces systematic bias — the labels reflect what the VLM "thinks" is happening, which may not match ground truth. Manual verification helps but does not eliminate this bias.

8. **Breed diversity is limited in audio datasets.** Barkopedia Emotion covers only 2 breeds. Barkopedia Activity does not document breed coverage. A model trained on limited breeds may not generalize.

9. **Class imbalance exists in vision data.** Verified distribution: `standing` (34.6%) is ~2.4x `sitting` (14.7%) and the `undefined` class (30.6%) contributes nothing useful. (This differs from the README's advertised distribution; see `dataset-validation-report.md`.)

10. **Non-commercial licenses exclude DogSpeak and ESC-50.** The two largest audio datasets (77K and 2K samples) are non-commercial, limiting BARKLY's deployment options.

---

## 9. Dataset Quality Concerns

### Label Reliability

- **Barkopedia Activity:** Labels generated by VLM, manually verified. VLM bias is systematic — the model may consistently misclassify certain activities (e.g., confusing "alerting to sounds" with "seeking attention"). Manual verification reduces but does not eliminate this. Inter-annotator agreement is not reported.

- **DogPoseCV:** Labels are more objective (pose is visually verifiable) but "undefined" class suggests labeling difficulty. The dataset was web-scraped and relabeled, introducing potential annotation errors.

- **Dog Emotion Dataset v2:** Subjective labels with no reported inter-annotator agreement. Different annotators may classify the same image differently.

### Data Provenance

- Both Barkopedia datasets and DogPoseCV are derived from online video content. This creates several concerns:
  - **Selection bias:** Viral/interesting dog videos are overrepresented
  - **Recording quality:** Highly variable (phone cameras, different environments)
  - **Background noise:** Audio recordings contain environmental sounds
  - **Re-uploaded content:** Some videos may be re-uploads with quality degradation

### Reproducibility

- Barkopedia datasets do not provide source video URLs, making independent verification difficult
- DogPoseCV provides image URLs but video sources vary
- Pre-defined train/test splits may not be documented as stratified by breed or recording source

### Statistical Power

- Barkopedia Emotion (1,400 clips) is too small for reliable training — results will be high-variance
- Barkopedia Activity (12,480 clips) is adequate for fine-tuning but may be insufficient for training from scratch
- DogPoseCV (20,578 images) is adequate for fine-tuning a pre-trained vision model

---

## 10. Decision

### What BARKLY CAN Claim (Based on Available Data)

- **Behavioral context classification from audio:** Using Barkopedia Activity labels, BARKLY can classify what context a dog is in (resting, playing, alerting, seeking attention) based on audio patterns. This is behavioral context, not vocalization type.

- **Pose estimation from images:** Using DogPoseCV, BARKLY can classify dog body posture (standing, sitting, lying) from camera input. This is a physical feature, not a behavioral state.

- **Emotional dimension estimation:** Using Barkopedia Emotion, BARKLY can estimate arousal/valence from audio as supplementary signals.

- **Context-aware behavioral interpretation:** Combining pose + activity context + arousal/valence, BARKLY can provide *contextual behavioral interpretation* — but this is a composite inference, not a direct classification.

### What BARKLY CANNOT Claim (Based on Available Data)

- **Vocalization type classification:** BARKLY cannot reliably classify whether a sound is a bark, whine, growl, howl, or sigh. No training data exists for this task. Any such claims would be misleading.

- **Emotional diagnosis:** BARKLY cannot diagnose a dog's emotional state. Emotion labels in available datasets are subjective interpretations, not clinical assessments. BARKLY provides behavioral observation, not veterinary diagnosis.

- **Breed-agnostic performance:** BARKLY's audio models are trained on limited breed data. Performance on underrepresented breeds is unknown and likely degraded.

- **Production-ready accuracy:** Available datasets are small-to-medium in size, sourced from online videos with variable quality, and contain label noise. Models trained on these data will have moderate accuracy at best and should be validated thoroughly before deployment.

### Recommendation

BARKLY should position itself as providing **behavioral context observation** based on available data, not as providing **vocalization classification** or **emotional diagnosis**. The datasets support a system that observes what a dog is likely doing and in what context, but cannot reliably identify specific vocalization types or clinical emotional states.

Future work should prioritize:
1. Creating a custom labeled dataset with vocalization type annotations (bark/whine/growl/howl/sigh)
2. Expanding pose datasets to include fine-grained body language features (ears, tail, mouth, eyes)
3. Establishing inter-annotator agreement protocols for behavioral labels
4. Collecting multimodal aligned data (synchronized audio + video + behavioral labels)
