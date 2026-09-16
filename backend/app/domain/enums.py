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


class BehavioralHints(StrEnum):
    """Canonical evidence hints used by the fusion/interpretation layer.

    These are *support* indicators, never certainty. They combine model outputs
    and context for the evidence-based interpretation rules.
    """

    AUDIO_ALERTING = "AUDIO_ALERTING"
    AUDIO_PLAYING = "AUDIO_PLAYING"
    AUDIO_ATTENTION = "AUDIO_ATTENTION"
    AUDIO_REST = "AUDIO_REST"
    AUDIO_FOOD = "AUDIO_FOOD"
    AUDIO_SHOWER = "AUDIO_SHOWER"
    VISION_STANDING = "VISION_STANDING"
    VISION_SITTING = "VISION_SITTING"
    VISION_LYING = "VISION_LYING"
    OWNER_PRESENT = "OWNER_PRESENT"
    OWNER_AWAY = "OWNER_AWAY"
    RECENT_PLAY = "RECENT_PLAY"
    RECENT_WALK = "RECENT_WALK"
    RECENT_FEEDING = "RECENT_FEEDING"
    RECENT_STRESS = "RECENT_STRESS"
    STRANGERS_PRESENT = "STRANGERS_PRESENT"
    OTHER_ANIMALS_PRESENT = "OTHER_ANIMALS_PRESENT"
    CONTEXT_PLAYING = "CONTEXT_PLAYING"
    CONTEXT_RESTING = "CONTEXT_RESTING"
    NIGHTTIME = "NIGHTTIME"
