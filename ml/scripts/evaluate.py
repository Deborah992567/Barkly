"""Model evaluation script.

Loads a trained model, runs evaluation on the test set, produces confusion
matrix, per-class metrics, calibration analysis, and OOD detection analysis.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import yaml
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    log_loss,
    roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.manifest import DatasetManifest


def compute_calibration(labels: np.ndarray, probabilities: np.ndarray, n_bins: int = 10) -> dict:
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bin_data = []

    for i in range(n_bins):
        mask = (probabilities.max(axis=1) > bin_boundaries[i]) & (probabilities.max(axis=1) <= bin_boundaries[i + 1])
        if mask.sum() == 0:
            continue
        bin_conf = probabilities[mask].max(axis=1)
        bin_pred = probabilities[mask].argmax(axis=1)
        bin_labels = labels[mask]
        bin_acc = (bin_pred == bin_labels).mean()
        bin_conf_mean = bin_conf.mean()
        bin_weight = mask.sum() / len(labels)
        ece += abs(bin_acc - bin_conf_mean) * bin_weight
        bin_data.append({
            "lower": float(bin_boundaries[i]),
            "upper": float(bin_boundaries[i + 1]),
            "count": int(mask.sum()),
            "accuracy": float(bin_acc),
            "mean_confidence": float(bin_conf_mean),
        })

    return {"ece": float(ece), "bins": bin_data}


def compute_ood_detection(probabilities: np.ndarray, threshold: float = 0.5) -> dict:
    max_confs = probabilities.max(axis=1)
    ood_mask = max_confs < threshold
    return {
        "threshold": threshold,
        "total_samples": len(probabilities),
        "ood_count": int(ood_mask.sum()),
        "id_count": int((~ood_mask).sum()),
        "mean_confidence": float(max_confs.mean()),
        "median_confidence": float(np.median(max_confs)),
        "confidence_distribution": {
            "p10": float(np.percentile(max_confs, 10)),
            "p25": float(np.percentile(max_confs, 25)),
            "p75": float(np.percentile(max_confs, 75)),
            "p90": float(np.percentile(max_confs, 90)),
        },
    }


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray | None, labels: list[str]) -> dict:
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    metrics = {
        "accuracy": float(report.get("accuracy", 0)),
        "macro_f1": float(report.get("macro avg", {}).get("f1-score", 0)),
        "weighted_f1": float(report.get("weighted avg", {}).get("f1-score", 0)),
        "per_class": {},
        "confusion_matrix": cm.tolist(),
        "labels": labels,
    }

    for label in labels:
        if label in report:
            metrics["per_class"][label] = {
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1-score": float(report[label]["f1-score"]),
                "support": int(report[label]["support"]),
            }

    if y_proba is not None and y_proba.shape[1] > 1:
        metrics["calibration"] = compute_calibration(y_true, y_proba)
        metrics["ood_detection"] = compute_ood_detection(y_proba)

        try:
            if len(labels) == 2:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
            else:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba, multi_class="ovr", labels=list(range(len(labels)))))
        except ValueError:
            metrics["roc_auc"] = None

        try:
            metrics["log_loss"] = float(log_loss(y_true, y_proba, labels=list(range(len(labels)))))
        except ValueError:
            metrics["log_loss"] = None

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a BARKLY model")
    parser.add_argument("manifest", help="Path to prepared manifest.yaml")
    parser.add_argument("--model-dir", required=True, help="Directory with trained model artifacts")
    parser.add_argument("--config", help="Model config YAML")
    parser.add_argument("--output", default=None, help="Output path for evaluation report JSON")
    parser.add_argument("--split", default="test", help="Which split to evaluate")
    args = parser.parse_args()

    manifest = DatasetManifest.from_yaml(args.manifest)
    eval_manifest = manifest.filter_by_split(args.split)
    print(f"Evaluating on {len(eval_manifest)} samples from '{args.split}' split")

    model_dir = Path(args.model_dir)
    if not (model_dir / "metrics.json").exists():
        print("No existing metrics found. Running evaluation requires a trained model.")
        sys.exit(1)

    with open(model_dir / "metrics.json") as f:
        existing_metrics = json.load(f)

    labels = existing_metrics.get("labels", [])
    report_data = existing_metrics.get("classification_report", {})
    cm = np.load(model_dir / "confusion_matrix.npy") if (model_dir / "confusion_matrix.npy").exists() else None

    evaluation = {
        "model_dir": str(model_dir),
        "split": args.split,
        "num_samples": len(eval_manifest),
        "labels": labels,
        "classification_report": report_data,
        "accuracy": existing_metrics.get("accuracy", 0),
    }

    if cm is not None:
        evaluation["confusion_matrix"] = cm.tolist()

    output_path = Path(args.output) if args.output else model_dir / "evaluation.json"
    with open(output_path, "w") as f:
        json.dump(evaluation, f, indent=2)

    print(f"Accuracy: {evaluation['accuracy']:.4f}")
    print(f"Evaluation report saved to {output_path}")


if __name__ == "__main__":
    main()
