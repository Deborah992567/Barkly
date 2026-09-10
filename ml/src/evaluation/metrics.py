from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class PerClassMetrics:
    class_name: str
    precision: float
    recall: float
    f1: float
    support: int
    accuracy: float


@dataclass
class EvaluationReport:
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    macro_f1: float = 0.0
    weighted_f1: float = 0.0
    per_class_metrics: list[PerClassMetrics] = field(default_factory=list)
    confusion_matrix: np.ndarray | None = None
    roc_auc: float = 0.0
    n_samples: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "macro_f1": self.macro_f1,
            "weighted_f1": self.weighted_f1,
            "per_class_metrics": [
                {
                    "class_name": m.class_name,
                    "precision": m.precision,
                    "recall": m.recall,
                    "f1": m.f1,
                    "support": m.support,
                    "accuracy": m.accuracy,
                }
                for m in self.per_class_metrics
            ],
            "confusion_matrix": (
                self.confusion_matrix.tolist()
                if self.confusion_matrix is not None
                else None
            ),
            "roc_auc": self.roc_auc,
            "n_samples": self.n_samples,
        }


def evaluate_classification(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None = None,
    class_names: list[str] | None = None,
) -> EvaluationReport:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n_samples = len(y_true)

    # Remap labels to contiguous range if needed
    unique_labels = np.unique(np.concatenate([y_true, y_pred]))
    label_to_idx = {label: i for i, label in enumerate(unique_labels)}
    y_true_map = np.array([label_to_idx[l] for l in y_true])
    y_pred_map = np.array([label_to_idx[l] for l in y_pred])
    n_classes = len(unique_labels)

    if class_names is None:
        class_names = [str(l) for l in unique_labels]

    report = EvaluationReport()
    report.accuracy = accuracy_score(y_true_map, y_pred_map)
    report.precision = precision_score(
        y_true_map, y_pred_map, average="macro", zero_division=0
    )
    report.recall = recall_score(
        y_true_map, y_pred_map, average="macro", zero_division=0
    )
    report.f1 = f1_score(y_true_map, y_pred_map, average="macro", zero_division=0)
    report.macro_f1 = report.f1
    report.weighted_f1 = f1_score(
        y_true_map, y_pred_map, average="weighted", zero_division=0
    )
    report.n_samples = n_samples

    cm = confusion_matrix(y_true_map, y_pred_map, labels=list(range(n_classes)))
    report.confusion_matrix = cm

    report.per_class_metrics = []
    for i in range(n_classes):
        class_mask_true = y_true.map if hasattr(y_true, "map") else None
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = int(cm[i, :].sum())

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

        report.per_class_metrics.append(
            PerClassMetrics(
                class_name=class_names[i] if i < len(class_names) else str(i),
                precision=prec,
                recall=rec,
                f1=f1,
                support=support,
                accuracy=tp / support if support > 0 else 0.0,
            )
        )

    if y_prob is not None and n_classes == 2:
        pos_probs = np.asarray(y_prob)[:, 1] if np.asarray(y_prob).ndim > 1 else y_prob
        try:
            report.roc_auc = roc_auc_score(y_true_map, pos_probs)
        except ValueError:
            report.roc_auc = 0.0
    elif y_prob is not None and n_classes > 2:
        try:
            report.roc_auc = roc_auc_score(
                y_true_map, np.asarray(y_prob), multi_class="ovr", average="macro"
            )
        except ValueError:
            report.roc_auc = 0.0

    return report


def compute_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> float:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    if y_true.ndim > 1:
        raise ValueError("y_true must be a 1D array of binary labels")
    if y_prob.ndim > 1:
        y_prob = y_prob[:, 1]

    if len(y_true) == 0:
        return 0.0

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    if np.issubdtype(y_true.dtype, np.integer) or y_true.max() > 1:
        y_true = (y_true == y_true.max()).astype(int)

    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_prob >= lo) & (y_prob <= hi)
        if i == n_bins - 1:
            mask = (y_prob >= lo) & (y_prob <= hi + 1e-12)
        n_bin = mask.sum()
        if n_bin == 0:
            continue
        avg_conf = float(y_prob[mask].mean())
        avg_acc = float(y_true[mask].mean())
        ece += (n_bin / n) * abs(avg_conf - avg_acc)
    return ece


def reliability_diagram_data(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> list[dict[str, float]]:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    if y_prob.ndim > 1:
        y_prob = y_prob[:, 1]
    if np.issubdtype(y_true.dtype, np.integer) and y_true.max() > 1:
        y_true = (y_true == y_true.max()).astype(int)

    if len(y_true) == 0:
        return []

    data: list[dict[str, float]] = []
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        if i == n_bins - 1:
            hi += 1e-12
        mask = (y_prob >= lo) & (y_prob <= hi)
        n_bin = int(mask.sum())
        if n_bin == 0:
            continue
        data.append(
            {
                "bin": i,
                "count": n_bin,
                "avg_confidence": float(y_prob[mask].mean()),
                "avg_accuracy": float(y_true[mask].mean()),
                "bin_low": lo,
                "bin_high": hi,
            }
        )
    return data


@dataclass
class OODMetrics:
    auroc: float = 0.0
    fpr_at_95_tpr: float = 1.0
    in_mean_score: float = 0.0
    ood_mean_score: float = 0.0
    tpr_at_95_fpr: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "auroc": self.auroc,
            "fpr_at_95_tpr": self.fpr_at_95_tpr,
            "in_mean_score": self.in_mean_score,
            "ood_mean_score": self.ood_mean_score,
            "tpr_at_95_fpr": self.tpr_at_95_fpr,
        }


def compute_ood_metrics(
    in_domain_probs: np.ndarray,
    ood_probs: np.ndarray,
) -> OODMetrics:
    from sklearn.metrics import roc_auc_score

    in_domain_probs = np.asarray(in_domain_probs)
    ood_probs = np.asarray(ood_probs)

    if in_domain_probs.ndim > 1:
        in_scores = in_domain_probs.max(axis=1)
        ood_scores = ood_probs.max(axis=1)
    else:
        in_scores = in_domain_probs
        ood_scores = ood_probs

    y_true = np.concatenate(
        [np.ones(len(in_scores)), np.zeros(len(ood_scores))]
    )
    y_scores = np.concatenate([in_scores, ood_scores])

    metrics = OODMetrics(
        in_mean_score=float(np.mean(in_scores)),
        ood_mean_score=float(np.mean(ood_scores)),
    )

    if len(np.unique(y_true)) == 2:
        try:
            metrics.auroc = roc_auc_score(y_true, y_scores)
        except ValueError:
            metrics.auroc = 0.0

        thresholds = np.sort(y_scores)
        tpr_at_95_fpr = 0.0
        for t in thresholds:
            fpr = np.mean(ood_scores >= t)
            tpr = np.mean(in_scores >= t)
            if fpr <= 0.05:
                tpr_at_95_fpr = tpr
                metrics.fpr_at_95_tpr = 0.05
        metrics.tpr_at_95_fpr = tpr_at_95_fpr

    return metrics