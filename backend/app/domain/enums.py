"""Controlled vocabularies for BARKLY.

These labels are model output categories / observed signal classes. They are
*not* guaranteed emotional truth. Stored as stable uppercase string codes so the
taxonomy can evolve without a database rewrite.
"""

from __future__ import annotations

from enum import StrEnum


class BehaviorState(StrEnum):
    RELAXED = "RELAXED"
    ALERT = "ALERT"
    PLAYFUL = "PLAYFUL"
    EXCITED = "EXCITED"
    CURIOUS = "CURIOUS"
    ATTENTION_SEEKING = "ATTENTION_SEEKING"
    FEARFUL = "FEARFUL"
    STRESSED = "STRESSED"
    AGGRESSIVE = "AGGRESSIVE"
    SUBMISSIVE = "SUBMISSIVE"
    RESTLESS = "RESTLESS"
    UNKNOWN = "UNKNOWN"


class AudioCategory(StrEnum):
    BARK = "BARK"
    WHINE = "WHINE"
    WHIMPER = "WHIMPER"
    GROWL = "GROWL"
    HOWL = "HOWL"
    SIGH = "SIGH"
    UNKNOWN = "UNKNOWN"


class AnalysisStatus(StrEnum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MediaType(StrEnum):
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"


class AnalysisInputType(StrEnum):
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    BEHAVIOR = "BEHAVIOR"


class Sex(StrEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    UNKNOWN = "UNKNOWN"


class OwnerPresence(StrEnum):
    HOME = "HOME"
    AWAY = "AWAY"
    UNKNOWN = "UNKNOWN"


class ActivityState(StrEnum):
    RESTING = "RESTING"
    WALKING = "WALKING"
    PLAYING = "PLAYING"
    EATING = "EATING"
    TRAINING = "TRAINING"
    UNKNOWN = "UNKNOWN"


class TimeOfDayCategory(StrEnum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    NIGHT = "NIGHT"
    UNKNOWN = "UNKNOWN"


class FeedbackVerdict(StrEnum):
    CONFIRMED = "CONFIRMED"
    CORRECTED = "CORRECTED"


class ObservationCategory(StrEnum):
    AUDIO = "AUDIO"
    VISUAL = "VISUAL"
    CONTEXT = "CONTEXT"
    ENVIRONMENTAL = "ENVIRONMENTAL"


class FailureCode(StrEnum):
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    INTERNAL = "INTERNAL"
    CANCELLED = "CANCELLED"
