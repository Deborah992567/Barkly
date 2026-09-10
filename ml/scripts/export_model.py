"""Model export script.

Loads trained model artifacts and exports them alongside metadata and a model
card describing the model's capabilities, limitations, and usage.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_model_card(metrics: dict, config: dict, modality: str) -> str:
    labels = metrics.get("labels", [])
    accuracy = metrics.get("accuracy", 0)
    model_type = config.get("model", "unknown")

    limitations = []
    if accuracy < 0.8:
        limitations.append("Moderate accuracy - predictions should not be used as sole decision basis")
    if len(labels) < 3:
        limitations.append("Limited number of output classes")
    limitations.append("Model outputs represent behavioral observations, not clinical diagnoses")
    limitations.append("Performance may vary across dog breeds and environments")

    card = f"""# BARKLY {modality.title()} Model Card

## Model Information
- **Model type:** {model_type}
- **Modality:** {modality}
- **Task:** Behavioral classification
- **Version:** {config.get("version", "0.1.0")}
- **Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}

## Performance
- **Accuracy:** {accuracy:.4f}
- **Output classes:** {", ".join(labels)}

## Intended Use
This model is intended for observing and classifying observable dog behavioral
signals from {modality} data. It is NOT intended for clinical diagnosis or
emotional assessment.

## Limitations
"""
    for lim in limitations:
        card += f"- {lim}\n"

    card += """
## Ethical Considerations
- Model predictions should always be interpreted by a human
- Cultural and breed-specific behavioral differences may affect accuracy
- This model does not replace professional veterinary or behavioral advice
"""
    return card


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a BARKLY model")
    parser.add_argument("--model-dir", required=True, help="Directory with trained model artifacts")
    parser.add_argument("--output-dir", required=True, help="Output directory for exported model")
    parser.add_argument("--config", help="Model config YAML")
    parser.add_argument("--modality", choices=["audio", "vision"], default="audio")
    parser.add_argument("--version", default="0.1.0", help="Model version string")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = {}
    if args.config:
        with open(args.config) as f:
            config = yaml.safe_load(f)

    metrics = {}
    metrics_path = model_dir / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

    artifact_files = ["model.pt", "model.joblib", "confusion_matrix.npy"]
    for name in artifact_files:
        src = model_dir / name
        if src.exists():
            shutil.copy2(src, output_dir / name)

    export_meta = {
        "model_version": args.version,
        "modality": args.modality,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "metrics_summary": {
            "accuracy": metrics.get("accuracy"),
            "labels": metrics.get("labels"),
        },
    }
    with open(output_dir / "export_metadata.json", "w") as f:
        json.dump(export_meta, f, indent=2)

    card = generate_model_card(metrics, config, args.modality)
    with open(output_dir / "MODEL_CARD.md", "w") as f:
        f.write(card)

    print(f"Model exported to {output_dir}")
    print(f"  Artifacts: {', '.join(a for a in artifact_files if (model_dir / a).exists())}")
    print(f"  Model card: MODEL_CARD.md")


if __name__ == "__main__":
    main()
