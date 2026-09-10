"""Tests for model construction, forward passes, and serialization."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from src.models.audio_baseline import AudioBaselineModel
from src.models.audio_cnn import AudioCNN, AudioCNNConfig, count_parameters, model_size_mb


class TestBaselineModelTrainPredict:
    def test_random_forest_train_predict(self):
        X = np.random.randn(100, 20)
        y = np.random.choice(["a", "b", "c"], 100)
        model = AudioBaselineModel(n_estimators=10, random_state=42)
        model.train(X, y)
        preds = model.predict(X[:10])
        assert len(preds) == 10
        assert all(p in ("a", "b", "c") for p in preds)

    def test_baseline_probabilities(self):
        X = np.random.randn(100, 20)
        y = np.random.choice(["a", "b", "c"], 100)
        model = AudioBaselineModel(n_estimators=10, random_state=42)
        model.train(X, y)
        proba = model.predict_proba(X[:5])
        assert proba.shape == (5, 3)
        assert np.allclose(proba.sum(axis=1), 1.0)

    def test_classes_property(self):
        X = np.random.randn(50, 20)
        y = np.random.choice(["x", "y"], 50)
        model = AudioBaselineModel(n_estimators=10, random_state=42)
        model.train(X, y)
        assert set(model.classes_) == {"x", "y"}

    def test_train_raises_before_fit(self):
        model = AudioBaselineModel()
        with np.testing.assert_raises(ValueError):
            model.predict(np.zeros((1, 20)))


class TestBaselineModelSaveLoad:
    def test_save_load_roundtrip(self, tmp_path: Path):
        X = np.random.randn(100, 20)
        y = np.random.choice(["a", "b", "c"], 100)
        model = AudioBaselineModel(n_estimators=10, random_state=42)
        model.train(X, y)

        model_path = tmp_path / "model.pkl"
        model.save(model_path)
        loaded = AudioBaselineModel.load(model_path)

        preds_orig = model.predict(X[:5])
        preds_loaded = loaded.predict(X[:5])
        np.testing.assert_array_equal(preds_orig, preds_loaded)


class TestCNNModelForwardPass:
    def test_cnn_forward(self):
        config = AudioCNNConfig(conv_channels=[16, 32], fc_dims=[64], dropout=0.3, num_classes=5)
        model = AudioCNN(config)
        x = torch.randn(4, 1, 64, 64)
        out = model(x)
        assert out.shape == (4, 5)

    def test_cnn_single_sample(self):
        config = AudioCNNConfig(conv_channels=[16], fc_dims=[32], dropout=0.1, num_classes=3)
        model = AudioCNN(config)
        x = torch.randn(1, 1, 64, 64)
        out = model(x)
        assert out.shape == (1, 3)

    def test_cnn_default_config(self):
        model = AudioCNN()
        x = torch.randn(2, 1, 128, 128)
        out = model(x)
        assert out.shape == (2, 2)

    def test_cnn_accepts_3d_input(self):
        config = AudioCNNConfig(conv_channels=[16], fc_dims=[32], dropout=0.1, num_classes=3)
        model = AudioCNN(config)
        x = torch.randn(1, 64, 64)
        out = model(x)
        assert out.shape == (1, 3)


class TestCNNOutputShape:
    def test_output_matches_num_classes(self):
        for n_classes in [2, 5, 10, 20]:
            config = AudioCNNConfig(conv_channels=[16, 32], fc_dims=[64], dropout=0.2, num_classes=n_classes)
            model = AudioCNN(config)
            x = torch.randn(8, 1, 64, 64)
            out = model(x)
            assert out.shape[1] == n_classes


class TestConfidenceRange:
    def test_softmax_in_01(self):
        config = AudioCNNConfig(conv_channels=[16], fc_dims=[32], dropout=0.0, num_classes=5)
        model = AudioCNN(config)
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
        subset = ["relaxed", "alert", "playful", "excited", "curious", "attention_seeking"]
        X = np.random.randn(100, 20)
        y = np.random.choice(subset, 100)
        model = AudioBaselineModel(n_estimators=10, random_state=42)
        model.train(X, y)
        preds = model.predict(X[:10])
        assert all(p in subset for p in preds)


class TestParamCountHelpers:
    def test_count_parameters(self):
        config = AudioCNNConfig(conv_channels=[16], fc_dims=[32], num_classes=4)
        model = AudioCNN(config)
        assert count_parameters(model) > 0

    def test_model_size_mb(self):
        config = AudioCNNConfig(conv_channels=[16], fc_dims=[32], num_classes=4)
        model = AudioCNN(config)
        assert model_size_mb(model) > 0.0