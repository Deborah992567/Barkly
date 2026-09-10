"""Tests for the evaluation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts.evaluate import compute_calibration, compute_ood_detection, evaluate


class TestMetricsCalculation:
    def test_perfect_prediction(self):
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 1, 2])
        labels = ["a", "b", "c"]
        metrics = evaluate(y_true, y_pred, None, labels)
        assert metrics["accuracy"] == 1.0
        assert metrics["macro_f1"] == 1.0

    def test_worst_prediction(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 0, 0, 0])
        labels = ["a", "b"]
        metrics = evaluate(y_true, y_pred, None, labels)
        assert metrics["accuracy"] == 0.0

    def test_per_class_metrics(self):
        y_true = np.array([0, 0, 1, 1, 2, 2])
        y_pred = np.array([0, 0, 1, 2, 2, 1])
        labels = ["a", "b", "c"]
        metrics = evaluate(y_true, y_pred, None, labels)
        assert "per_class" in metrics
        for label in labels:
            assert label in metrics["per_class"]
            assert "precision" in metrics["per_class"][label]
            assert "recall" in metrics["per_class"][label]
            assert "f1-score" in metrics["per_class"][label]


class TestConfusionMatrixShape:
    def test_shape_matches_num_classes(self):
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 1, 0, 2, 2])
        labels = ["a", "b", "c"]
        metrics = evaluate(y_true, y_pred, None, labels)
        cm = np.array(metrics["confusion_matrix"])
        assert cm.shape == (3, 3)

    def test_diagonal_elements(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        labels = ["a", "b"]
        metrics = evaluate(y_true, y_pred, None, labels)
        cm = np.array(metrics["confusion_matrix"])
        assert cm[0, 0] == 2
        assert cm[1, 1] == 2
        assert cm[0, 1] == 0
        assert cm[1, 0] == 0


class TestCalibrationErrorRange:
    def test_ece_in_01(self):
        y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
        probs = np.random.dirichlet([1, 1, 1], 10)
        cal = compute_calibration(y_true, probs)
        assert 0.0 <= cal["ece"] <= 1.0

    def test_perfect_calibration(self):
        y_true = np.array([0, 1, 2])
        probs = np.array([[0.9, 0.05, 0.05], [0.05, 0.9, 0.05], [0.05, 0.05, 0.9]])
        cal = compute_calibration(y_true, probs)
        assert cal["ece"] < 0.1

    def test_bins_count(self):
        y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        probs = np.random.dirichlet([1, 1], 10)
        cal = compute_calibration(y_true, probs, n_bins=5)
        assert isinstance(cal["bins"], list)


class TestOODDetection:
    def test_ood_counts(self):
        probs = np.array([
            [0.9, 0.1],
            [0.3, 0.7],
            [0.4, 0.6],
            [0.1, 0.9],
        ])
        ood = compute_ood_detection(probs, threshold=0.5)
        assert ood["total_samples"] == 4
        assert ood["ood_count"] + ood["id_count"] == 4

    def test_ood_all_high_confidence(self):
        probs = np.array([[0.99, 0.01], [0.95, 0.05]])
        ood = compute_ood_detection(probs, threshold=0.5)
        assert ood["ood_count"] == 0
        assert ood["id_count"] == 2

    def test_ood_all_low_confidence(self):
        probs = np.array([[0.51, 0.49], [0.52, 0.48]])
        ood = compute_ood_detection(probs, threshold=0.8)
        assert ood["ood_count"] == 2
        assert ood["id_count"] == 0

    def test_confidence_distribution(self):
        probs = np.random.dirichlet([1, 1], 100)
        ood = compute_ood_detection(probs, threshold=0.5)
        cd = ood["confidence_distribution"]
        assert cd["p10"] <= cd["p25"] <= cd["p75"] <= cd["p90"]
