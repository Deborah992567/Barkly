"""Tests for model training, inference, and serialization."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch


TAXONOMY_LABELS = [
    "relaxed", "alert", "playful", "excited", "curious",
    "attention_seeking", "fearful", "stressed", "aggressive",
    "submissive", "restless", "unknown",
]

AUDIO_LABELS = ["bark", "whine", "growl", "howl", "sigh", "whimper", "unknown"]


class TestBaselineModelTrainPredict:
    def test_random_forest_train_predict(self):
        from sklearn.ensemble import RandomForestClassifier

        X = np.random.randn(100, 20)
        y = np.random.choice(["a", "b", "c"], 100)
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)
        preds = clf.predict(X[:10])
        assert len(preds) == 10
        assert all(p in ("a", "b", "c") for p in preds)

    def test_baseline_probabilities(self):
        from sklearn.ensemble import RandomForestClassifier

        X = np.random.randn(100, 20)
        y = np.random.choice(["a", "b", "c"], 100)
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)
        proba = clf.predict_proba(X[:5])
        assert proba.shape == (5, 3)
        assert np.allclose(proba.sum(axis=1), 1.0)


class TestBaselineModelSaveLoad:
    def test_save_load_roundtrip(self, tmp_path: Path):
        import joblib
        from sklearn.ensemble import RandomForestClassifier

        X = np.random.randn(100, 20)
        y = np.random.choice(["a", "b", "c"], 100)
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)

        model_path = tmp_path / "model.joblib"
        joblib.dump(clf, model_path)
        loaded = joblib.load(model_path)

        preds_orig = clf.predict(X[:5])
        preds_loaded = loaded.predict(X[:5])
        np.testing.assert_array_equal(preds_orig, preds_loaded)


class TestCNNModelForwardPass:
    def test_cnn_forward(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16, 32], "fc_dims": [64], "dropout": 0.3, "n_mels": 64}
        model = AudioCNN(num_classes=5, config=config)
        x = torch.randn(4, 1, 64, 64)
        out = model(x)
        assert out.shape == (4, 5)

    def test_cnn_single_sample(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.1, "n_mels": 64}
        model = AudioCNN(num_classes=3, config=config)
        x = torch.randn(1, 1, 64, 64)
        out = model(x)
        assert out.shape == (1, 3)


class TestCNNOutputShape:
    def test_output_matches_num_classes(self):
        from scripts.train_audio import AudioCNN

        for n_classes in [2, 5, 10, 20]:
            config = {"conv_channels": [16, 32], "fc_dims": [64], "dropout": 0.2, "n_mels": 64}
            model = AudioCNN(num_classes=n_classes, config=config)
            x = torch.randn(8, 1, 64, 64)
            out = model(x)
            assert out.shape[1] == n_classes


class TestConfidenceRange:
    def test_softmax_in_01(self):
        from scripts.train_audio import AudioCNN

        config = {"conv_channels": [16], "fc_dims": [32], "dropout": 0.0, "n_mels": 64}
        model = AudioCNN(num_classes=5, config=config)
        model.eval()
        x = torch.randn(10, 1, 64, 64)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
        assert probs.min() >= 0.0
        assert probs.max() <= 1.0
        assert torch.allclose(probs.sum(dim=1), torch.ones(10), atol=1e-5)


class TestPredictionLabelInTaxonomy:
    def test_baseline_labels_in_tax(self):
        from sklearn.ensemble import RandomForestClassifier

        subset = TAXONOMY_LABELS[:6]
        X = np.random.randn(100, 20)
        y = np.random.choice(subset, 100)
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)
        preds = clf.predict(X[:10])
        assert all(p in subset for p in preds)


class TestUnknownHandling:
    def test_unknown_class_present(self):
        assert "unknown" in [l.lower() for l in AUDIO_LABELS]
        assert "unknown" in [l.lower() for l in TAXONOMY_LABELS]
