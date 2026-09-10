from __future__ import annotations

import numpy as np


class OODDetector:
    def __init__(self, method: str = "max_softmax"):
        if method not in ("max_softmax", "energy"):
            raise ValueError(
                f"Unsupported OOD method: {method}. Use 'max_softmax' or 'energy'."
            )
        self.method = method

    def energy_score(self, logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        logits = np.asarray(logits, dtype=np.float64)
        logits = logits / temperature
        return temperature * np.log(np.sum(np.exp(logits), axis=1))

    def max_softmax_probability(self, logits: np.ndarray) -> np.ndarray:
        logits = np.asarray(logits, dtype=np.float64)
        logits_max = logits.max(axis=1, keepdims=True)
        exp_logits = np.exp(logits - logits_max)
        probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
        return probs.max(axis=1)

    def score(self, logits: np.ndarray) -> np.ndarray:
        if self.method == "energy":
            return self.energy_score(logits)
        return self.max_softmax_probability(logits)

    def detect_ood(
        self,
        scores: np.ndarray,
        threshold: float | None = None,
    ) -> np.ndarray:
        scores = np.asarray(scores)
        if threshold is None:
            threshold = np.median(scores)
        if self.method == "energy":
            # For energy scores, higher = more in-distribution
            return scores < threshold
        # For max softmax, higher = more in-distribution
        return scores < threshold

    def find_threshold(
        self,
        scores: np.ndarray,
        labels: np.ndarray,
        target_fpr: float = 0.05,
    ) -> float:
        scores = np.asarray(scores)
        labels = np.asarray(labels)
        binary = labels == 1
        in_scores = scores[binary]
        ood_scores = scores[~binary]

        if len(ood_scores) == 0:
            return float(np.min(scores))

        thresholds = np.unique(np.concatenate([in_scores, ood_scores]))
        thresholds = np.sort(thresholds)
        best_threshold = thresholds[0]
        best_fpr_diff = float("inf")

        for t in thresholds:
            if self.method == "energy":
                # Energy: score < threshold => OOD
                fpr = np.mean(in_scores < t)
            else:
                # Max softmax: score < threshold => OOD
                fpr = np.mean(in_scores < t)
            if abs(fpr - target_fpr) < best_fpr_diff:
                best_fpr_diff = abs(fpr - target_fpr)
                best_threshold = t

        return float(best_threshold)