from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import yaml


@dataclass
class InferenceResult:
    class_name: str
    confidence: float
    supporting_signals: dict[str, float] = field(default_factory=dict)
    is_ood: bool = False
    model_version: str = ""
    sample_id: str = ""
    is_unknown: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "class_name": self.class_name,
            "confidence": self.confidence,
            "supporting_signals": self.supporting_signals,
            "is_ood": self.is_ood,
            "model_version": self.model_version,
            "sample_id": self.sample_id,
            "is_unknown": self.is_unknown,
        }


class AudioInferenceEngine:
    def __init__(
        self,
        model_path: str | Path,
        config_path: str | Path,
        label_encoder_path: str | Path | None = None,
        confidence_threshold: float = 0.5,
        ood_threshold: float | None = None,
        device: str | None = None,
    ):
        self.model_path = str(model_path)
        self.config = load_yaml(config_path)
        self.confidence_threshold = confidence_threshold
        self.ood_threshold = ood_threshold

        self.label_encoder_path = label_encoder_path

        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.model_type = self.config.get("model", "audio_cnn")
        self.class_names, self.checkpoint = self._load_checkpoint()
        self.model = self._load_model()
        self.model.to(self.device)
        self.model.eval()

        from ..audio.preprocessing import AudioPreprocessor
        from ..audio.features import AudioFeatureExtractor

        self.preprocessor = AudioPreprocessor(
            target_sr=self.config.get("sample_rate", 22050),
            target_duration=self.config.get("duration", 3.0),
        )
        self.feature_extractor = AudioFeatureExtractor()

        self._init_ood()

    def _init_ood(self) -> None:
        from ..evaluation.ood import OODDetector

        self.ood_detector = OODDetector(method="energy")

    def _load_checkpoint(self) -> tuple[list[str], dict]:
        checkpoint = torch.load(
            self.model_path, map_location="cpu", weights_only=False
        )
        labels = checkpoint.get("labels", [])
        if labels:
            return list(labels), checkpoint
        if self.label_encoder_path and Path(self.label_encoder_path).exists():
            import pickle

            with open(self.label_encoder_path, "rb") as f:
                encoder = pickle.load(f)
            if hasattr(encoder, "classes_"):
                return list(encoder.classes_), checkpoint
            if isinstance(encoder, (list, tuple)):
                return list(encoder), checkpoint
        return [], checkpoint

    def _load_model(self) -> torch.nn.Module:
        from ..models.audio_cnn import AudioCNN, AudioCNNConfig

        cfg = AudioCNNConfig(
            n_mels=self.config.get("n_mels", 128),
            n_mfcc=self.config.get("n_mfcc", 13),
            conv_channels=self.config.get("conv_channels", [32, 64, 128]),
            fc_dims=self.config.get("fc_dims", [256, 128]),
            dropout=self.config.get("dropout", 0.3),
            num_classes=max(len(self.class_names), 2),
        )
        model = AudioCNN(cfg)
        state_dict = self.checkpoint.get("model_state_dict", self.checkpoint)
        model.load_state_dict(state_dict)
        return model

    def _extract_features(self, audio: np.ndarray, sr: int) -> tuple[np.ndarray, torch.Tensor]:
        audio = np.asarray(audio, dtype=np.float32)
        if self.model_type == "audio_cnn":
            mel_spec = self.feature_extractor.extract_mel_spectrogram(
                audio, sr, n_mels=self.config.get("n_mels", 128)
            )
            mel_spec = (mel_spec - np.mean(mel_spec)) / (np.std(mel_spec) + 1e-8)
            tensor = torch.from_numpy(mel_spec.astype(np.float32)).unsqueeze(0).unsqueeze(0)
            return mel_spec, tensor
        elif self.model_type == "random_forest":
            features = self.feature_extractor.extract_all(audio, sr)
            flat = self.feature_extractor.flatten_features(features)
            tensor = torch.from_numpy(flat.astype(np.float32)).unsqueeze(0)
            return flat, tensor
        raise ValueError(f"Unsupported model type: {self.model_type}")

    def _post_process(
        self,
        logits: torch.Tensor,
        preprocessed: np.ndarray,
        sample_id: str = "",
    ) -> InferenceResult:
        import torch.nn.functional as F

        with torch.no_grad():
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]

        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])

        from ..evaluation.ood import OODDetector

        detector = OODDetector(method="energy")
        ood_scores = detector.energy_score(logits.cpu().numpy())
        in_domain_score = float(np.sum(ood_scores))

        is_ood = False
        if self.ood_threshold is not None:
            ood_probs = probs.max()
            is_ood = ood_probs < self.ood_threshold

        is_unknown = confidence < self.confidence_threshold or is_ood
        class_name = (
            self.class_names[top_idx] if self.class_names else str(top_idx)
        )
        if is_unknown:
            class_name = "UNKNOWN"

        supporting_signals = {
            "top_2_confidence": float(
                np.sort(probs)[-2] if len(probs) > 1 else 0.0
            ),
            "max_logit": float(logits.max().item()),
            "entropy": float(
                -np.sum(probs * np.log(probs + 1e-12))
            ),
            "ood_score": float(ood_scores[0]),
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
            is_ood=is_ood,
            model_version=self.config.get("version", "unknown"),
            sample_id=sample_id,
            is_unknown=is_unknown,
        )

    def predict(self, audio_path: str, sample_id: str = "") -> InferenceResult:
        from ..audio.preprocessing import preprocess_audio

        audio = preprocess_audio(audio_path, self.preprocessor)
        sr = self.config.get("sample_rate", 22050)

        _, tensor = self._extract_features(audio, sr)
        tensor = tensor.to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)

        return self._post_process(logits, audio, sample_id or str(audio_path))

    def predict_batch(
        self, audio_paths: list[str], sample_ids: list[str] | None = None
    ) -> list[InferenceResult]:
        results: list[InferenceResult] = []
        for i, path in enumerate(audio_paths):
            sid = sample_ids[i] if sample_ids else str(path)
            results.append(self.predict(path, sample_id=sid))
        return results


def load_yaml(path: str | Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)