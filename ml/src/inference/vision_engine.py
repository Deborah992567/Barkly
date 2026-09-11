from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import yaml

from .audio_engine import InferenceResult


class VisionInferenceEngine:
    def __init__(
        self,
        model_path: str | Path,
        config_path: str | Path,
        label_encoder_path: str | Path | None = None,
        confidence_threshold: float = 0.5,
        device: str | None = None,
    ):
        from ..vision.preprocessing import ImagePreprocessor

        self.model_path = str(model_path)
        self.config = self._load_config(config_path)
        self.confidence_threshold = confidence_threshold

        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        checkpoint = torch.load(
            self.model_path, map_location="cpu", weights_only=False
        )
        self.class_names: list[str] = list(checkpoint.get("labels", []))
        if not self.class_names and label_encoder_path and Path(label_encoder_path).exists():
            import pickle

            with open(label_encoder_path, "rb") as f:
                encoder = pickle.load(f)
            if hasattr(encoder, "classes_"):
                self.class_names = list(encoder.classes_)
            elif isinstance(encoder, (list, tuple)):
                self.class_names = list(encoder)

        from ..models.vision_baseline import VisionBaselineConfig, VisionBaselineModel

        cfg = VisionBaselineConfig(
            model_name=self.config.get("model", "mobilenet_v3"),
            num_classes=max(len(self.class_names), 2),
            pretrained=False,
            device=str(self.device),
        )
        self.wrapper = VisionBaselineModel(cfg)
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        self.wrapper.model.load_state_dict(state_dict)
        self.wrapper.model.to(self.device)
        self.wrapper.model.eval()

        self.preprocessor = ImagePreprocessor(
            image_size=(
                self.config.get("image_size", 224),
                self.config.get("image_size", 224),
            )
        )

    @staticmethod
    def _load_config(path: str | Path) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def predict(self, image_path: str, sample_id: str = "") -> InferenceResult:
        from ..vision.preprocessing import ImagePreprocessor

        if not self.preprocessor.validate_image(image_path):
            raise FileNotFoundError(f"Invalid or unreadable image: {image_path}")

        tensor = self.preprocessor.preprocess_image(image_path)
        tensor = tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.wrapper.model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])

        is_unknown = confidence < self.confidence_threshold
        class_name = (
            self.class_names[top_idx] if self.class_names else str(top_idx)
        )
        if is_unknown:
            class_name = "UNKNOWN"

        supporting_signals = {
            "top_2_confidence": float(np.sort(probs)[-2] if len(probs) > 1 else 0.0),
            "max_logit": float(logits.max().item()),
            "entropy": float(-np.sum(probs * np.log(probs + 1e-12))),
            "top_k_margin": float(
                np.sort(probs)[-1] - np.sort(probs)[-2]
                if len(probs) > 1
                else 1.0
            ),
        }

        return InferenceResult(
            class_name=class_name,
            confidence=confidence,
            supporting_signals=supporting_signals,
            is_ood=False,
            model_version=self.config.get("version", "unknown"),
            sample_id=sample_id or str(image_path),
            is_unknown=is_unknown,
        )

    def predict_batch(
        self, image_paths: list[str], sample_ids: list[str] | None = None
    ) -> list[InferenceResult]:
        results: list[InferenceResult] = []
        for i, path in enumerate(image_paths):
            sid = sample_ids[i] if sample_ids else str(path)
            results.append(self.predict(path, sample_id=sid))
        return results