"""Audio model training script.

Supports baseline (Random Forest) and CNN training.  Loads data from a
prepared manifest, extracts features, trains, evaluates, and saves artifacts.
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
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.manifest import DatasetManifest, SampleManifest
from src.audio.preprocessor import preprocess_audio
from src.audio.feature_extractor import extract_features


class AudioManifestDataset(Dataset):
    def __init__(self, samples: list[SampleManifest], config: dict):
        self.samples = samples
        self.config = config
        self.sample_rate = config.get("sample_rate", 22050)
        self.duration = config.get("duration", 3.0)
        self.n_mels = config.get("n_mels", 128)

        self.labels = sorted({s.normalized_label for s in samples})
        self.label_to_idx = {l: i for i, l in enumerate(self.labels)}

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        sample = self.samples[idx]
        waveform = preprocess_audio(
            sample.path,
            target_sr=self.sample_rate,
            target_duration=self.duration,
        )
        features = extract_features(waveform, self.sample_rate, self.config)
        label_idx = self.label_to_idx[sample.normalized_label]
        return torch.tensor(features, dtype=torch.float32), label_idx


class AudioCNN(nn.Module):
    def __init__(self, num_classes: int, config: dict):
        super().__init__()
        conv_channels = config.get("conv_channels", [32, 64, 128])
        fc_dims = config.get("fc_dims", [256, 128])
        dropout = config.get("dropout", 0.3)
        n_mels = config.get("n_mels", 128)

        layers = []
        in_ch = 1
        for out_ch in conv_channels:
            layers.extend([
                nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(),
                nn.MaxPool2d(2),
            ])
            in_ch = out_ch
        self.conv = nn.Sequential(*layers)

        with torch.no_grad():
            dummy = torch.zeros(1, 1, n_mels, n_mels)
            conv_out = self.conv(dummy)
            flat_size = conv_out.view(1, -1).shape[1]

        fc_layers = []
        in_dim = flat_size
        for dim in fc_dims:
            fc_layers.extend([
                nn.Linear(in_dim, dim),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            in_dim = dim
        fc_layers.append(nn.Linear(in_dim, num_classes))
        self.fc = nn.Sequential(*fc_layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            x = x.unsqueeze(1)
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


def train_baseline(config: dict, train_samples, val_samples, output_dir: Path) -> dict:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix

    X_train, y_train = [], []
    for sample in train_samples:
        waveform = preprocess_audio(sample.path, config.get("sample_rate", 22050), config.get("duration", 3.0))
        feats = extract_features(waveform, config.get("sample_rate", 22050), config)
        X_train.append(feats)
        y_train.append(sample.normalized_label)

    X_val, y_val = [], []
    for sample in val_samples:
        waveform = preprocess_audio(sample.path, config.get("sample_rate", 22050), config.get("duration", 3.0))
        feats = extract_features(waveform, config.get("sample_rate", 22050), config)
        X_val.append(feats)
        y_val.append(sample.normalized_label)

    X_train = np.array(X_train)
    X_val = np.array(X_val)

    clf = RandomForestClassifier(
        n_estimators=config.get("n_estimators", 100),
        max_depth=config.get("max_depth"),
        class_weight=config.get("class_weight", "balanced"),
        random_state=config.get("seed", 42),
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_val)
    labels = sorted(set(y_train) | set(y_val))
    report = classification_report(y_val, y_pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_val, y_pred, labels=labels)

    import joblib
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, output_dir / "model.joblib")
    np.save(output_dir / "confusion_matrix.npy", cm)

    metrics = {
        "accuracy": report.get("accuracy", 0),
        "classification_report": report,
        "labels": labels,
    }
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def train_cnn(config: dict, train_samples, val_samples, output_dir: Path) -> dict:
    labels = sorted({s.normalized_label for s in train_samples})
    num_classes = len(labels)
    label_to_idx = {l: i for i, l in enumerate(labels)}

    train_ds = AudioManifestDataset(train_samples, config)
    val_ds = AudioManifestDataset(val_samples, config)
    train_loader = DataLoader(train_ds, batch_size=config.get("batch_size", 32), shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=config.get("batch_size", 32))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AudioCNN(num_classes, config).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=config.get("lr", 0.001),
        weight_decay=config.get("weight_decay", 0.0001),
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=5)

    epochs = config.get("epochs", 50)
    patience = config.get("early_stopping", 10)
    best_val_loss = float("inf")
    wait = 0

    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for features, targets in train_loader:
            features, targets = features.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * features.size(0)

        train_loss /= len(train_ds)

        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for features, targets in val_loader:
                features, targets = features.to(device), targets.to(device)
                outputs = model(features)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * features.size(0)
                _, predicted = outputs.max(1)
                correct += predicted.eq(targets).sum().item()
                total += targets.size(0)
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(targets.cpu().numpy())

        val_loss /= len(val_ds)
        val_acc = correct / total if total else 0
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            wait = 0
            torch.save(model.state_dict(), output_dir / "model.pt")
        else:
            wait += 1
            if wait >= patience:
                break

    from sklearn.metrics import classification_report, confusion_matrix as sklearn_cm

    label_names = [labels[i] for i in range(num_classes)]
    report = classification_report(all_labels, all_preds, labels=list(range(num_classes)), target_names=label_names, output_dict=True, zero_division=0)
    cm = sklearn_cm(all_labels, all_preds, labels=list(range(num_classes)))

    np.save(output_dir / "confusion_matrix.npy", cm)
    metrics = {
        "accuracy": report.get("accuracy", 0),
        "classification_report": report,
        "labels": labels,
        "epochs_trained": epoch + 1,
        "best_val_loss": best_val_loss,
    }
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train BARKLY audio model")
    parser.add_argument("config", help="Path to YAML config file")
    parser.add_argument("--manifest", required=True, help="Path to prepared manifest.yaml")
    parser.add_argument("--output", default="experiments/audio", help="Output directory")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    manifest = DatasetManifest.from_yaml(args.manifest)
    train_manifest = manifest.filter_by_split("train")
    val_manifest = manifest.filter_by_split("val")
    test_manifest = manifest.filter_by_split("test")

    print(f"Train: {len(train_manifest)}  Val: {len(val_manifest)}  Test: {len(test_manifest)}")

    output_dir = Path(args.output)
    model_type = config.get("model", "random_forest")

    if model_type == "random_forest":
        print("Training baseline (Random Forest)...")
        metrics = train_baseline(config, train_manifest.samples, val_manifest.samples, output_dir)
    elif model_type == "audio_cnn":
        print("Training CNN...")
        metrics = train_cnn(config, train_manifest.samples, val_manifest.samples, output_dir)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Artifacts saved to {output_dir}")


if __name__ == "__main__":
    main()
