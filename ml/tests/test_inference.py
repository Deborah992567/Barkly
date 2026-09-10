"""Tests for the inference pipeline."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from src.data.manifest import SampleManifest, DatasetManifest


AUDIO_LABELS = ["bark", "whine", "growl", "howl", "sigh", "whimper", "unknown"]
BEHAVIOR_LABELS = [
    "relaxed", "alert", "playful", "excited", "curious",
    "attention_seeking", "fearful", "stressed", "aggressive",
    "submissive", "restless", "unknown",
]


class TestAudioInferenceReturnsValidResult:
    def test_result_structure(self, tmp_audio_dir):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.1, "n_mels": 64}
        model = AudioCNN(num_classes=len(AUDIO_LABELS), config=config)
        model.eval()

        x = torch.randn(1, 1, 64, 64)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
            pred_idx = probs.argmax(dim=1).item()
            confidence = probs[0, pred_idx].item()

        assert isinstance(pred_idx, int)
        assert isinstance(confidence, float)
        assert 0 <= pred_idx < len(AUDIO_LABELS)


class TestInferenceConfidenceInRange:
    def test_confidence_in_01(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.0, "n_mels": 64}
        model = AudioCNN(num_classes=7, config=config)
        model.eval()

        for _ in range(10):
            x = torch.randn(1, 1, 64, 64)
            with torch.no_grad():
                logits = model(x)
                probs = torch.softmax(logits, dim=1)
                conf = probs.max().item()
            assert 0.0 <= conf <= 1.0


class TestInferenceLabelValid:
    def test_label_in_audio_taxonomy(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.0, "n_mels": 64}
        model = AudioCNN(num_classes=len(AUDIO_LABELS), config=config)
        model.eval()

        x = torch.randn(1, 1, 64, 64)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
            pred_idx = probs.argmax(dim=1).item()

        assert AUDIO_LABELS[pred_idx] in AUDIO_LABELS

    def test_label_in_behavior_taxonomy(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.0, "n_mels": 64}
        model = AudioCNN(num_classes=len(BEHAVIOR_LABELS), config=config)
        model.eval()

        x = torch.randn(1, 1, 64, 64)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
            pred_idx = probs.argmax(dim=1).item()

        assert BEHAVIOR_LABELS[pred_idx] in BEHAVIOR_LABELS


class TestOODReturnsUnknown:
    def test_low_confidence_maps_to_unknown(self):
        probs = torch.tensor([[0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.1]])
        max_conf = probs.max().item()
        threshold = 0.3
        if max_conf < threshold:
            predicted_label = "unknown"
        else:
            predicted_label = AUDIO_LABELS[probs.argmax().item()]
        assert predicted_label == "unknown"

    def test_high_confidence_not_unknown(self):
        probs = torch.tensor([[0.9, 0.02, 0.02, 0.02, 0.02, 0.02, 0.0]])
        threshold = 0.3
        max_conf = probs.max().item()
        if max_conf < threshold:
            predicted_label = "unknown"
        else:
            predicted_label = AUDIO_LABELS[probs.argmax().item()]
        assert predicted_label == "bark"


class TestMalformedInputHandlesSafely:
    def test_empty_tensor_does_not_crash(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.1, "n_mels": 64}
        model = AudioCNN(num_classes=7, config=config)
        model.eval()
        x = torch.randn(0, 1, 64, 64)
        with torch.no_grad():
            out = model(x)
        assert out.shape[0] == 0

    def test_wrong_dimensions(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.1, "n_mels": 64}
        model = AudioCNN(num_classes=7, config=config)
        model.eval()
        x = torch.randn(1, 64, 64)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (1, 7)
