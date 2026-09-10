from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .audio_engine import AudioInferenceEngine, InferenceResult


@dataclass
class ProviderResult:
    class_name: str = "UNKNOWN"
    confidence: float = 0.0
    supporting_signals: dict[str, float] = field(default_factory=dict)
    is_unknown: bool = False
    is_ood: bool = False
    model_version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_name": self.class_name,
            "confidence": self.confidence,
            "supporting_signals": self.supporting_signals,
            "is_unknown": self.is_unknown,
            "is_ood": self.is_ood,
            "model_version": self.model_version,
            "metadata": self.metadata,
        }


class BehaviorInferenceProvider(Protocol):
    name: str
    modality: str

    def predict(self, input_path: str) -> ProviderResult:
        ...

    def predict_batch(self, input_paths: list[str]) -> list[ProviderResult]:
        ...


class BarklyAudioProvider:
    """Phase 2 adapter wrapping the AudioInferenceEngine."""

    name: str = "barkly_audio"
    modality: str = "audio"

    def __init__(
        self,
        model_path: str | Path,
        config_path: str | Path,
        label_encoder_path: str | Path | None = None,
        **kwargs: Any,
    ):
        self.engine = AudioInferenceEngine(
            model_path=model_path,
            config_path=config_path,
            label_encoder_path=label_encoder_path,
            **kwargs,
        )

    def _map_result(self, result: InferenceResult) -> ProviderResult:
        return ProviderResult(
            class_name=result.class_name,
            confidence=result.confidence,
            supporting_signals=result.supporting_signals,
            is_unknown=result.is_unknown,
            is_ood=result.is_ood,
            model_version=result.model_version,
            metadata={"sample_id": result.sample_id},
        )

    def predict(self, input_path: str) -> ProviderResult:
        try:
            result = self.engine.predict(input_path)
            return self._map_result(result)
        except FileNotFoundError as e:
            raise ValueError(f"Input file not found: {input_path}") from e
        except Exception as e:
            raise RuntimeError(f"Audio inference failed for {input_path}: {e}") from e

    def predict_batch(self, input_paths: list[str]) -> list[ProviderResult]:
        results: list[ProviderResult] = []
        for path in input_paths:
            try:
                results.append(self.predict(path))
            except (ValueError, RuntimeError):
                results.append(
                    ProviderResult(
                        class_name="UNKNOWN",
                        confidence=0.0,
                        is_unknown=True,
                        metadata={"error": f"inference failed for {path}"},
                    )
                )
        return results