"""Multimodal fusion and interpretation for BARKLY Phase 4."""

from app.ai.fusion.engine import FusionEngine
from app.ai.fusion.interpretation import interpret
from app.ai.fusion.rules import RULES, InterpretationRule, rule_for_interpretation

__all__ = [
    "FusionEngine",
    "interpret",
    "InterpretationRule",
    "RULES",
    "rule_for_interpretation",
]
