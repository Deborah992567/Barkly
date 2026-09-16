"""Safety advisories for analysis results.

BARKLY is a monitoring aid, not a diagnosis or a safety guarantee. This module
produces precautionary, plain-language notes that accompany results where a
defensive or stress-related reaction is plausible. It never claims a dog is
dangerous: an alerting signal with strangers present is not aggression.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import BehaviorState, BehavioralHints


@dataclass(frozen=True)
class SafetyAdvisory:
    note: str | None
    is_precautionary: bool = True


def evaluate_safety(
    *,
    primary_state: BehaviorState,
    hints: frozenset[BehavioralHints],
    is_insufficient_evidence: bool,
) -> SafetyAdvisory:
    if primary_state is BehaviorState.ALERT:
        return SafetyAdvisory(
            note=(
                "BARKLY detected signs of alerting in a setting where a stress or "
                "defensive reaction is plausible. Give the dog space and avoid "
                "forcing interaction until the signals settle."
            )
        )

    if (
        is_insufficient_evidence
        and BehavioralHints.AUDIO_ALERTING in hints
        and (
            BehavioralHints.STRANGERS_PRESENT in hints
            or BehavioralHints.OTHER_ANIMALS_PRESENT in hints
            or BehavioralHints.RECENT_STRESS in hints
        )
    ):
        return SafetyAdvisory(
            note=(
                "Signals were unclear but included alerting sounds alongside a "
                "potentially unsettling situation. BARKLY suggests watching from a "
                "distance and not forcing interaction."
            )
        )

    if (
        primary_state is BehaviorState.UNKNOWN
        and not is_insufficient_evidence
        and (
            BehavioralHints.RECENT_STRESS in hints
            or BehavioralHints.STRANGERS_PRESENT in hints
        )
    ):
        return SafetyAdvisory(
            note=(
                "The signals did not resolve into one interpretation, and recent "
                "context suggests possible stress. Consider giving the dog space and "
                "checking in from a distance."
            )
        )

    return SafetyAdvisory(note=None)


SILENT = SafetyAdvisory(note=None)