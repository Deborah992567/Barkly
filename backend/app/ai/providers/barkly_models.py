"""Real-model inference provider for BARKLY Phase 4.

Loads the evaluated Phase 3 artifacts (audio activity CNN + vision pose model)
from the shipped model registry, runs them on stored media, and feeds the
evidence through the deterministic fusion/interpretation layer.

This provider NEVER fabricates an interpretation: when the audio model cannot
classify (its documented weakness) and no usable visual signal exists, the
result is UNKNOWN with an explicit "insufficient evidence" flag, exactly as per
the uncertainty policy in docs/multimodal-fusion.md.
"""

from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.ai.evidence import (
    AudioEvidence,
    ContextEvidence,
    EvidenceBundle,
    VisualEvidence,
)
from app.ai.fusion.engine import FusionEngine
from app.ai.fusion.interpretation import interpret
from app.ai.media_loader import (
    pick_media_reference,
    resolve_media,
    sample_video_frames,
)
from app.ai.model_adapters import audio_to_evidence, vision_to_evidence
from app.ai.types import AnalysisInput, InferenceResult, ModelTrace
from app.core.config import get_settings
from app.domain.enums import MediaType
from app.domain.value_objects import ModelIdentity
from app.media.storage import get_storage

_AUDIO_REGISTRY_ID = "barkly-audio-cnn-v2"
_VISION_REGISTRY_ID = "barkly-vision-mobilenet-v3-small"
_REGISTRY_PATH_VALUE = "__registry__"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if value.startswith(".."):
        base = Path(__file__).resolve().parents[3]  # backend/
    else:
        base = _repo_root()
    return (base / path).resolve()


def _ensure_ml_importable() -> None:
    """Make the sibling `ml` package (`src.*`) importable from the backend."""
    ml_root = _repo_root() / "ml"
    if str(ml_root.resolve()) not in sys.path:
        sys.path.insert(0, str(ml_root.resolve()))


@dataclass(frozen=True)
class _RegistryInfo:
    audio_model_version: str
    vision_model_version: str
    audio_dataset_version: str
    audio_preprocessing_version: str
    vision_dataset_version: str
    vision_preprocessing_version: str


@lru_cache
def _load_trace_registry(
    registry_path: Path, audio_model_path: Path, vision_model_path: Path
) -> ModelTrace:
    data = yaml.safe_load(registry_path.read_text())
    models: list[dict] = data.get("models", [])
    by_id = {m.get("id"): m for m in models}

    audio = by_id.get(_AUDIO_REGISTRY_ID) or {}
    vision = by_id.get(_VISION_REGISTRY_ID) or {}

    audio_dataset = audio.get("dataset_version") or "unknown"
    audio_prep = audio.get("preprocessing_version") or "unknown"
    vision_dataset = vision.get("dataset_version") or "unknown"

    return ModelTrace(
        audio_model_name=_AUDIO_REGISTRY_ID,
        audio_model_version=_artifact_version(audio_model_path),
        vision_model_name=_VISION_REGISTRY_ID,
        vision_model_version=_artifact_version(vision_model_path),
        preprocessing_version=audio_prep,
        dataset_version=(
            f"{audio_dataset}/{vision_dataset}" if vision_dataset != "unknown" else audio_dataset
        ),
        fusion_version=get_settings().ai_fusion_version,
        interpretation_version=get_settings().ai_interpretation_version,
    )


def _artifact_version(path: Path) -> str:
    try:
        mtime = path.stat().st_mtime
        import datetime

        return datetime.datetime.fromtimestamp(mtime, tz=datetime.UTC).isoformat()
    except OSError:
        return "unknown"


class BarklyModelsProvider:
    identity = ModelIdentity(
        provider="barkly-models",
        model_name="barkly-multimodal-v1",
        model_version="1.0.0",
        is_placeholder=False,
    )

    def __init__(self) -> None:
        _ensure_ml_importable()
        settings = get_settings()
        self._settings = settings
        self._audio_engine = None
        self._vision_engine = None
        self._audio_path = _resolve_repo_path(settings.ai_audio_model_path)
        self._audio_config = _resolve_repo_path(settings.ai_audio_config_path)
        self._vision_path = _resolve_repo_path(settings.ai_vision_model_path)
        self._vision_config = _resolve_repo_path(settings.ai_vision_config_path)
        registry_path = _resolve_repo_path(settings.ai_model_registry_path)
        self._trace = _load_trace_registry(registry_path, self._audio_path, self._vision_path)
        self._storage = get_storage(settings.media_storage_provider)
        self._fusion = FusionEngine()

    # --- provider protocol -------------------------------------------------

    async def analyze(self, request: AnalysisInput) -> InferenceResult:
        return await asyncio.wait_for(
            self._analyze_inner(request),
            timeout=self._settings.ai_inference_timeout_seconds,
        )

    async def health(self) -> bool:
        return self._audio_path.is_file() and self._vision_path.is_file()

    # --- internals ---------------------------------------------------------

    async def _analyze_inner(self, request: AnalysisInput) -> InferenceResult:
        audio_path = resolve_media(
            pick_media_reference(MediaType.AUDIO.value, self._refs(request)) or "",
            self._storage,
        )
        image_path = resolve_media(
            pick_media_reference(MediaType.IMAGE.value, self._refs(request)) or "",
            self._storage,
        )
        video_path = resolve_media(
            pick_media_reference(MediaType.VIDEO.value, self._refs(request)) or "",
            self._storage,
        )

        audio_evidence = await self._run_audio(audio_path)
        visual_evidence = await asyncio.to_thread(self._run_visual, video_path, image_path)
        context_evidence = ContextEvidence(
            available=bool(request.context.present()),
            signals=request.context,
        )

        started = time.perf_counter()
        bundle = EvidenceBundle(
            audio=audio_evidence,
            visual=visual_evidence,
            context=context_evidence,
        )
        outcome = await asyncio.to_thread(self._fusion.fuse, bundle)
        latency_ms = int((time.perf_counter() - started) * 1000)

        return interpret(
            outcome=outcome,
            evidence=bundle,
            model=self.identity,
            trace=self._trace,
            latency_ms=latency_ms,
        )

    async def _run_audio(self, audio_path: Path | None) -> AudioEvidence:
        if audio_path is None or not await asyncio.to_thread(audio_path.is_file):
            return AudioEvidence(available=False)

        engine = self._get_audio_engine()
        try:
            raw = await asyncio.to_thread(engine.predict, str(audio_path), str(audio_path))
        except Exception:
            return AudioEvidence(
                available=True,
                is_unknown=True,
                is_weak_model=True,
                supporting_signals={},
            )
        return audio_to_evidence(
            available=True,
            class_name=raw.class_name,
            confidence=raw.confidence,
            is_unknown=raw.is_unknown,
            is_ood=raw.is_ood,
            model_version=raw.model_version,
            supporting_signals=raw.supporting_signals,
        )

    def _run_visual(self, video_path: Path | None, image_path: Path | None) -> VisualEvidence:
        frame_paths: list[Path] = []
        if image_path is not None and image_path.is_file():
            frame_paths = [image_path]
        elif video_path is not None and video_path.is_file():
            frame_paths = sample_video_frames(video_path, self._settings.ai_vision_frames)

        if not frame_paths:
            return VisualEvidence(available=False)

        engine = self._get_vision_engine()
        frame_results: list[tuple[str, float]] = []
        for path in frame_paths:
            try:
                raw = engine.predict(str(path), str(path))
                frame_results.append((raw.class_name, raw.confidence))
            except Exception:
                continue

        return vision_to_evidence(
            available=len(frame_results) > 0,
            frame_results=frame_results,
            model_version=self._trace.vision_model_version or "unknown",
        )

    def _get_audio_engine(self):
        if self._audio_engine is None:
            from src.inference.audio_engine import AudioInferenceEngine

            self._audio_engine = AudioInferenceEngine(
                model_path=self._audio_path,
                config_path=self._audio_config,
                confidence_threshold=self._settings.ai_audio_confidence_threshold,
                ood_threshold=self._settings.ai_audio_ood_threshold,
            )
        return self._audio_engine

    def _get_vision_engine(self):
        if self._vision_engine is None:
            from src.inference.vision_engine import VisionInferenceEngine

            self._vision_engine = VisionInferenceEngine(
                model_path=self._vision_path,
                config_path=self._vision_config,
                confidence_threshold=self._settings.ai_vision_confidence_threshold,
            )
        return self._vision_engine

    @staticmethod
    def _refs(request: AnalysisInput) -> tuple[tuple[str, str], ...]:
        return tuple((ref.media_type, ref.storage_reference) for ref in request.media_refs)
