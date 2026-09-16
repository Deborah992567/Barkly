"""Mapping of raw model outputs to the evidence contract.

Keeps `providers/barkly_models.py` thin: it loads artifacts and calls models;
this module turns what the models emit into `AudioEvidence` / `VisualEvidence`
that the fusion rules understand — applying the documented uncertainty policy
(thresholds, OOD gating, weak-model handling).
"""

from __future__ import annotations

from app.ai.evidence import AudioEvidence, PoseSignal, VisualEvidence
from app.core.config import get_settings


def audio_to_evidence(
    *,
    available: bool,
    class_name: str,
    confidence: float,
    is_unknown: bool,
    is_ood: bool,
    model_version: str,
    supporting_signals: dict[str, float],
) -> AudioEvidence:
    return AudioEvidence(
        available=available,
        label=None if is_unknown or class_name == "UNKNOWN" else class_name,
        confidence=confidence,
        raw_confidence=confidence,
        is_unknown=bool(is_unknown or class_name == "UNKNOWN"),
        is_ood=is_ood,
        is_weak_model=True,
        model_version=model_version,
        supporting_signals=dict(supporting_signals),
    )


def vision_to_evidence(
    *,
    available: bool,
    frame_results: list[tuple[str, float]],  # (class_name, confidence) per frame
    model_version: str,
) -> VisualEvidence:
    """Aggregate per-frame pose predictions into a single posture decision.

    The dominant class across frames wins; confidence is the mean confidence of
    the frames that voted for it. Empty or all-UNKNOWN results yield an unknown
    visual signal. `undefined` is treated as no usable posture info.
    """
    settings = get_settings()
    poses: list[PoseSignal] = []
    for class_name, confidence in frame_results:
        if class_name == "UNKNOWN":
            continue
        poses.append(PoseSignal(pose=class_name, confidence=confidence))

    votes: dict[str, list[float]] = {}
    for pose in poses:
        if pose.confidence >= settings.ai_vision_confidence_threshold:
            votes.setdefault(pose.pose, []).append(pose.confidence)

    aggregated_pose: str | None = None
    confidence = 0.0
    if votes:
        aggregated_pose = max(
            votes, key=lambda pose: (len(votes[pose]), sum(votes[pose]) / len(votes[pose]))
        )
        confidence = sum(votes[aggregated_pose]) / len(votes[aggregated_pose])

    is_unknown = aggregated_pose is None or aggregated_pose == "undefined"

    return VisualEvidence(
        available=available,
        aggregated_pose=None if is_unknown else aggregated_pose,
        confidence=confidence,
        is_unknown=is_unknown,
        model_version=model_version,
        frames_sampled=len(frame_results),
        poses=poses,
    )
