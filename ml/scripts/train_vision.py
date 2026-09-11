"""Vision model training script.

Trains a vision model (MobileNetV3 or custom CNN) for dog body language
classification from images.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.manifest import DatasetManifest, SampleManifest


class VisionManifestDataset(Dataset):
    def __init__(self, samples: list[SampleManifest], config: dict, augment: bool = False):
        self.samples = samples
        self.image_size = config.get("image_size", 224)

        if augment:
            self.transform = transforms.Compose([
                transforms.Resize((self.image_size, self.image_size)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(10),
                transforms.ColorJitter(brightness=0.2, contrast=0.2),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((self.image_size, self.image_size)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])

        self.labels = sorted({s.normalized_label for s in samples})
        self.label_to_idx = {l: i for i, l in enumerate(self.labels)}

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        from PIL import Image

        sample = self.samples[idx]
        image = Image.open(sample.path).convert("RGB")
        image = self.transform(image)
        label_idx = self.label_to_idx[sample.normalized_label]
        return image, label_idx


class VisionCNN(nn.Module):
    def __init__(self, num_classes: int, config: dict):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


def get_model(num_classes: int, config: dict) -> nn.Module:
    model_type = config.get("model", "mobilenet_v3")

    if model_type == "mobilenet_v3" or model_type == "efficientnet":
        from src.models.vision_baseline import VisionBaselineConfig, VisionBaselineModel

        wrapper = VisionBaselineModel(VisionBaselineConfig(
            model_name=model_type,
            num_classes=num_classes,
            pretrained=config.get("pretrained", True),
            freeze_backbone=config.get("freeze_backbone", False),
            fine_tune_layers=config.get("fine_tune_layers", 0),
        ))
        return wrapper
    else:
        return VisionCNN(num_classes, config)


def train(config: dict, train_samples, val_samples, output_dir: Path) -> dict:
    train_ds = VisionManifestDataset(train_samples, config, augment=True)
    val_ds = VisionManifestDataset(val_samples, config, augment=False)
    train_loader = DataLoader(train_ds, batch_size=config.get("batch_size", 32), shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=config.get("batch_size", 32))

    labels = train_ds.labels
    num_classes = len(labels)

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    wrapper = get_model(num_classes, config)
    model = wrapper.model if hasattr(wrapper, "model") else wrapper
    model.to(device)
    print(f"Device: {device} | Params: {sum(p.numel() for p in model.parameters()):,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=config.get("lr", 0.001))

    epochs = config.get("epochs", 30)
    best_val_acc = 0.0
    wait = 0
    patience = config.get("early_stopping", 10)

    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(epochs):
        model.train()
        for images, targets in train_loader:
            images, targets = images.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = 0
        total = 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for images, targets in val_loader:
                images, targets = images.to(device), targets.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                correct += predicted.eq(targets).sum().item()
                total += targets.size(0)
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(targets.cpu().numpy())

        val_acc = correct / total if total else 0
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            wait = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "labels": labels,
                },
                output_dir / "model.pt",
            )
        else:
            wait += 1
            if wait >= patience:
                break

    from sklearn.metrics import classification_report, confusion_matrix

    label_names = labels
    report = classification_report(all_labels, all_preds, labels=list(range(num_classes)), target_names=label_names, output_dict=True, zero_division=0)
    cm = confusion_matrix(all_labels, all_preds, labels=list(range(num_classes)))

    np.save(output_dir / "confusion_matrix.npy", cm)
    metrics = {
        "accuracy": report.get("accuracy", 0),
        "classification_report": report,
        "labels": labels,
        "epochs_trained": epoch + 1,
        "best_val_accuracy": best_val_acc,
    }
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train BARKLY vision model")
    parser.add_argument("config", help="Path to YAML config file")
    parser.add_argument("--manifest", required=True, help="Path to prepared manifest.yaml")
    parser.add_argument("--output", default="experiments/vision", help="Output directory")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    manifest = DatasetManifest.from_yaml(args.manifest)
    train_manifest = manifest.filter_by_split("train")
    val_manifest = manifest.filter_by_split("val")

    print(f"Train: {len(train_manifest)}  Val: {len(val_manifest)}")

    output_dir = Path(args.output)
    print("Training vision model...")
    metrics = train(config, train_manifest.samples, val_manifest.samples, output_dir)
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Artifacts saved to {output_dir}")


if __name__ == "__main__":
    main()
