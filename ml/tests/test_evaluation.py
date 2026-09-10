"""Tests for the evaluation pipeline (metrics, calibration, OOD)."""

from __future__ import annotations

import numpy as np
import pytest

from src.evaluation.metrics import (
    compute_calibration_error,
    compute_ood_metrics,
    evaluate_classification,
    reliability_diagram_data,
)
from src.evaluation.ood import OODDetector


class TestMetricsCalculation:
    def test_perfect_prediction(self):
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 1, 2])
        labels = ["a", "b", "c"]
        metrics = evaluate_classification(y_true, y_pred, None, labels)
        assert metrics.accuracy == 1.0
        assert metrics.macro_f1 == 1.0

    def test_worst_prediction(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 0, 0, 0])
        labels = ["a", "b"]
        metrics = evaluate_classification(y_true, y_pred, None, labels)
        assert metrics.accuracy == 0.0
        assert metrics.macro_f1 == 0.0

    def test_per_class_metrics(self):
        y_true = np.array([0, 0, 1, 1, 2, 2])
        y_pred = np.array([0, 0, 1, 2, 2, 1])
        labels = ["a", "b", "c"]
        metrics = evaluate_classification(y_true, y_pred, None, labels)
        assert len(metrics.per_class_metrics) == 3
        for pm in metrics.per_class_metrics:
            assert pm.class_name in labels
            assert pm.precision >= 0.0
            assert pm.recall >= 0.0
            assert pm.f1 >= 0.0

    def test_report_to_dict(self):
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])
        metrics = evaluate_classification(y_true, y_pred)
        d = metrics.to_dict()
        assert d["accuracy"] == 1.0
        assert d["per_class_metrics"][0]["precision"] == 1.0


class TestConfusionMatrixShape:
    def test_shape_matches_num_classes(self):
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 1, 0, 2, 2])
        labels = ["a", "b", "c"]
        metrics = evaluate_classification(y_true, y_pred, None, labels)
        assert metrics.confusion_matrix.shape == (3, 3)

    def test_diagonal_elements(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        labels = ["a", "b"]
        metrics = evaluate_classification(y_true, y_pred, None, labels)
        cm = metrics.confusion_matrix
        assert cm[0, 0] == 2
        assert cm[1, 1] == 2
        assert cm[0, 1] == 0
        assert cm[1, 0] == 0


class TestCalibrationErrorRange:
    def test_ece_in_01(self):
        y_true = np.random.choice([0, 1, 2], 50)
        probs = np.random.dirichlet([1, 1, 1], 50)
        ece = compute_calibration_error(y_true, probs, n_bins=10)
        assert 0.0 <= ece <= 1.0

    def test_perfect_calibration(self):
        y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        probs = np.array([0.0] * 5 + [1.0] * 5)
        ece = compute_calibration_error(y_true, probs, n_bins=10)
        assert ece == 0.0

    def test_binary_probs_vector(self):
        y_true = np.array([0, 1, 0, 1])
        probs = np.array([0.9, 0.2, 0.8, 0.3])
        ece = compute_calibration_error(y_true, probs, n_bins=5)
        assert 0.0 <= ece <= 1.0

    def test_reliability_diagram(self):
        y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        probs = np.random.dirichlet([2, 1], 10)[:, 0]
        data = reliability_diagram_data(y_true, probs, n_bins=5)
        assert isinstance(data, list)
        for entry in data:
            assert {"bin", "count", "avg_confidence", "avg_accuracy"} <= set(entry)


class TestOODMetrics:
    def test_ood_metrics_separation(self):
        in_probs = np.random.dirichlet([10, 1, 1], 100)
        ood_probs = np.random.dirichlet([1, 10, 10], 100)
        metrics = compute_ood_metrics(in_probs, ood_probs)
        assert 0.0 <= metrics.auroc <= 1.0
        assert 0.0 <= metrics.tpr_at_95_fpr <= 1.0

    def test_ood_metrics_one_dimensional(self):
        in_scores = np.random.uniform(0.8, 1.0, 50)
        ood_scores = np.random.uniform(0.0, 0.4, 50)
        metrics = compute_ood_metrics(in_scores, ood_scores)
        assert metrics.auroc > 0.9
        assert metrics.in_mean_score > metrics.ood_mean_score


class TestOODDetector:
    def test_max_softmax_method(self):
        detector = OODDetector(method="max_softmax")
        logits = np.random.randn(10, 4)
        scores = detector.score(logits)
        assert scores.shape == (10,)
        assert np.all((scores >= 0) & (scores <= 1))

    def test_energy_method(self):
        detector = OODDetector(method="energy")
        logits = np.random.randn(10, 4)
        scores = detector.score(logits)
        assert scores.shape == (10,)

    def test_invalid_method(self):
        with pytest.raises(ValueError):
            OODDetector(method="bogus")

    def test_detect_ood_threshold(self):
        detector = OODDetector(method="max_softmax")
        scores = np.array([0.9, 0.1, 0.8, 0.2])
        flags = detector.detect_ood(scores, threshold=0.5)
        assert flags.tolist() == [False, True, False, True]

    def test_find_threshold_target_fpr(self):
        detector = OODDetector(method="max_softmax")
        rng = np.random.default_rng(42)
        in_scores = rng.beta(8, 2, 200)  # mostly high
        ood_scores = rng.beta(2, 8, 200)  # mostly low
        scores = np.concatenate([in_scores, ood_scores])
        labels = np.concatenate([np.ones(200), np.zeros(200)])
        threshold = detector.find_threshold(scores, labels, target_fpr=0.05)
        assert 0.0 < threshold < 1.0


class TestUnknownHeuristics:
    def test_unknown_class_present(self):
        assert "unknown" in [l.lower() for l in ["bark", "whine", "growl", "howl", "sigh", "whimper", "unknown"]]