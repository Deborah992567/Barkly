"""End-to-end model evaluation on a held-out test split.

Loads the trained model through the production inference engine, runs
predictions on the test split, and produces a full report: per-class metrics,
confusion matrix, ROC-AUC, calibration (ECE + reliability diagram), and OOD /
UNKNOWN analysis using synthetic out-of-distribution inputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.manifest import DatasetManifest
from src.evaluation.metrics import (
    compute_calibration_error,
    compute_ood_metrics,
    evaluate_classification,
    reliability_diagram_data,
)


def _make_audio_ood_samples(config: dict, n: int = 100) -> list[str]:
    """Write short synthetic noise/silence clips as OOD audio."""
    from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

    sr = config.get("sample_rate", 22050)
    duration = config.get("duration", 3.0)
    n_samples = int(sr * duration)
    tmp = Path("/tmp/barkly_ood_audio")
    tmp.mkdir(parents=True, exist_ok=True)

    paths = []
    rng = np.random.default_rng(0)
    for i in range(n):
        kind = i % 2
        if kind == 0:
            signal = rng.standard_normal(n_samples).astype(np.float32)
        else:
            signal = np.zeros(n_samples, dtype=np.float32)
        path = tmp / f"ood_{i}.wav"
        import soundfile as sf

        sf.write(path, signal, sr)
        paths.append(str(path))
    return paths


def _make_vision_ood_samples(config: dict, n: int = 100) -> list[str]:
    """Write solid-color and noise images as OOD vision inputs."""
    from PIL import Image

    size = config.get("image_size", 224)
    tmp = Path("/tmp/barkly_ood_vision")
    tmp.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(1)
    paths = []
    for i in range(n):
        kind = i % 2
        if kind == 0:
            arr = rng.integers(0, 255, (size, size, 3), dtype=np.uint8)
        else:
            arr = np.full((size, size, 3), 128, dtype=np.uint8)
        path = tmp / f"ood_{i}.png"
        Image.fromarray(arr).save(path)
        paths.append(str(path))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a BARKLY model end-to-end")
    parser.add_argument("modality", choices=["audio", "vision"])
    parser.add_argument("manifest", help="Path to prepared manifest.yaml")
    parser.add_argument("--model-dir", required=True, help="Trained model directory")
    parser.add_argument("--config", required=True, help="Model config YAML")
    parser.add_argument("--output", default=None, help="Report output path")
    parser.add_argument("--split", default="test", help="Split to evaluate")
    parser.add_argument("--confidence-threshold", type=float, default=0.5)
    parser.add_argument("--ood-n", type=int, default=100)
    args = parser.parse_args()

    import yaml

    with open(args.config) as f:
        config = yaml.safe_load(f)

    manifest = DatasetManifest.from_yaml(args.manifest)
    eval_manifest = manifest.filter_by_split(args.split)
    print(f"Evaluating {len(eval_manifest)} samples from '{args.split}' split")

    from src.inference.audio_engine import AudioInferenceEngine
    from src.inference.vision_engine import VisionInferenceEngine

    model_dir = Path(args.model_dir)
    if args.modality == "audio":
        engine = AudioInferenceEngine(
            model_path=model_dir / "model.pt",
            config_path=args.config,
            confidence_threshold=args.confidence_threshold,
        )
        ood_paths = _make_audio_ood_samples(config, args.ood_n)
    else:
        engine = VisionInferenceEngine(
            model_path=model_dir / "model.pt",
            config_path=args.config,
            confidence_threshold=args.confidence_threshold,
        )
        ood_paths = _make_vision_ood_samples(config, args.ood_n)

    class_names = engine.class_names
    label_to_idx = {lbl: i for i, lbl in enumerate(class_names)}
    print(f"Classes ({len(class_names)}): {', '.join(class_names)}")

    y_true, y_pred, max_conf, ood_flags, unknown_flags = [], [], [], [], []
    for sample in eval_manifest.samples:
        try:
            res = engine.predict(sample.path, sample_id=sample.sample_id)
        except Exception as e:  # noqa: BLE001 - treat failed samples as unknown
            y_true.append(-1)
            y_pred.append(-1)
            max_conf.append(0.0)
            ood_flags.append(True)
            unknown_flags.append(True)
            continue
        y_true.append(label_to_idx.get(sample.normalized_label, -1))
        cls = res.class_name
        if cls == "UNKNOWN":
            y_pred.append(-1)
            max_conf.append(float(res.confidence))
            ood_flags.append(res.is_ood)
            unknown_flags.append(True)
        else:
            y_pred.append(label_to_idx.get(cls, -1))
            max_conf.append(float(res.confidence))
            ood_flags.append(res.is_ood)
            unknown_flags.append(False)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    max_conf = np.array(max_conf)
    known = (y_true >= 0) & (y_pred >= 0)
    y_true_known = y_true[known]
    y_pred_known = y_pred[known]

    report = evaluate_classification(
        y_true_known,
        y_pred_known,
        class_names=class_names,
    )
    full = report.to_dict()
    full["n_samples"] = int(len(y_true))
    full["n_known"] = int(known.sum())
    full["unknown_rate"] = float((~known).mean()) if len(y_true) else 0.0
    full["confidence_threshold"] = args.confidence_threshold
    full["mean_confidence"] = float(np.mean(max_conf))
    full["median_confidence"] = float(np.median(max_conf))
    full["ood_flag_rate"] = float(np.mean(ood_flags)) if len(ood_flags) else 0.0
    full["confidence_percentiles"] = {
        "p10": float(np.percentile(max_conf, 10)),
        "p25": float(np.percentile(max_conf, 25)),
        "p75": float(np.percentile(max_conf, 75)),
        "p90": float(np.percentile(max_conf, 90)),
    }

    if len(y_true_known):
        conf_known = max_conf[known]
        bin_true = (y_pred_known == y_true_known).astype(int)
        full["calibration"] = {
            "ece": compute_calibration_error(bin_true, conf_known),
            "reliability_diagram": reliability_diagram_data(bin_true, conf_known),
        }

    in_scores = max_conf[known] if known.sum() else np.array([0.0])
    ood_results = []
    for path in ood_paths:
        try:
            res = engine.predict(path)
            ood_results.append(float(res.confidence))
        except Exception:  # noqa: BLE001
            ood_results.append(0.0)
    ood_scores = np.array(ood_results)
    full["ood_analysis"] = compute_ood_metrics(in_scores, ood_scores).to_dict()
    full["ood_probe_count"] = int(len(ood_scores))

    full["classes"] = class_names
    full["config"] = {k: v for k, v in config.items() if k != "model"}

    output_path = Path(args.output) if args.output else model_dir / "evaluation.json"
    with open(output_path, "w") as f:
        json.dump(full, f, indent=2)

    print(f"\nAccuracy (known): {full['accuracy']:.4f}  Unknown rate: {full['unknown_rate']:.4f}")
    print(f"ECE: {full.get('calibration', {}).get('ece', float('nan')):.4f}")
    print(f"OOD AUROC: {full['ood_analysis']['auroc']:.4f}  FPR@95TPR: {full['ood_analysis']['fpr_at_95_tpr']:.4f}")
    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    main()