"""Audio model training script.

Supports baseline (Random Forest) and CNN training.  Loads data from a
prepared manifest, extracts features, trains, evaluates, and saves artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
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
from src.audio.preprocessing import AudioPreprocessor, preprocess_audio
from src.audio.features import AudioFeatureExtractor, FeatureConfig
from src.models.audio_cnn import AudioCNN, AudioCNNConfig


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _preprocess(path: str, config: dict) -> np.ndarray:
    return preprocess_audio(
        path,
        AudioPreprocessor(
            target_sr=config.get("sample_rate", 22050),
            target_duration=config.get("duration", 3.0),
        ),
    )


def _extract_flat_features(waveform: np.ndarray, config: dict) -> np.ndarray:
    sr = config.get("sample_rate", 22050)
    extractor = AudioFeatureExtractor(
        FeatureConfig(
            sample_rate=sr,
            n_mfcc=config.get("n_mfcc", 13),
            n_mels=config.get("n_mels", 128),
            use_mfcc=True,
            use_mel_spectrogram=False,
            use_spectral=True,
        )
    )
    feats = extractor.extract_all(waveform, sr)
    return extractor.flatten_features(feats)


class AudioManifestDataset(Dataset):
    def __init__(self, samples: list[SampleManifest], config: dict, cache_dir: Path | None = None):
        self.samples = samples
        self.config = config
        self.sample_rate = config.get("sample_rate", 22050)
        self.duration = config.get("duration", 3.0)
        self.n_mels = config.get("n_mels", 128)
        self.cache_dir = cache_dir

        self.labels = sorted({s.normalized_label for s in samples})
        self.label_to_idx = {l: i for i, l in enumerate(self.labels)}

    def __len__(self) -> int:
        return len(self.samples)

    def _cache_path(self, sample: SampleManifest) -> Path | None:
        if self.cache_dir is None:
            return None
        key = (
            f"{sample.sample_id}_{self.sample_rate}_{self.duration}_{self.n_mels}"
        )
        return self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.npy"

    def __getitem__(self, idx: int):
        sample = self.samples[idx]

        cache_path = self._cache_path(sample)
        if cache_path is not None and cache_path.exists():
            mel = np.load(cache_path).astype(np.float32)
        else:
            waveform = _preprocess(sample.path, self.config)
            extractor = AudioFeatureExtractor(
                FeatureConfig(
                    sample_rate=self.sample_rate,
                    n_mels=self.n_mels,
                    use_mfcc=False,
                    use_mel_spectrogram=True,
                    use_spectral=False,
                )
            )
            mel = extractor.extract_mel_spectrogram(waveform, self.sample_rate, self.n_mels)
            mel = (mel - np.mean(mel)) / (np.std(mel) + 1e-8)
            mel = mel.astype(np.float32)
            if cache_path is not None:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                np.save(cache_path, mel)

        feature = torch.from_numpy(mel).unsqueeze(0)  # (1, n_mels, T)
        label_idx = self.label_to_idx[sample.normalized_label]
        return feature, label_idx


def train_baseline(config: dict, train_samples, val_samples, output_dir: Path) -> dict:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix

    X_train, y_train = [], []
    for sample in train_samples:
        waveform = _preprocess(sample.path, config)
        X_train.append(_extract_flat_features(waveform, config))
        y_train.append(sample.normalized_label)

    X_val, y_val = [], []
    for sample in val_samples:
        waveform = _preprocess(sample.path, config)
        X_val.append(_extract_flat_features(waveform, config))
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

    cache_dir = output_dir / "feature_cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    train_ds = AudioManifestDataset(train_samples, config, cache_dir=cache_dir)
    val_ds = AudioManifestDataset(val_samples, config, cache_dir=cache_dir)
    train_loader = DataLoader(train_ds, batch_size=config.get("batch_size", 32), shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=config.get("batch_size", 32))

    device = get_device()
    cnn_config = AudioCNNConfig(
        n_mels=config.get("n_mels", 128),
        n_mfcc=config.get("n_mfcc", 13),
        conv_channels=config.get("conv_channels", [32, 64, 128]),
        fc_dims=config.get("fc_dims", [256, 128]),
        dropout=config.get("dropout", 0.3),
        num_classes=len(labels),
    )
    model = AudioCNN(cnn_config).to(device)
    print(f"Device: {device} | Params: {sum(p.numel() for p in model.parameters()):,}")

    criterion = nn.CrossEntropyLoss(label_smoothing=config.get("label_smoothing", 0.0))
    optimizer = optim.Adam(
        model.parameters(),
        lr=config.get("lr", 0.001),
        weight_decay=config.get("weight_decay", 0.0001),
    )
    if config.get("scheduler", "reduce_on_plateau") == "cosine":
        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=config.get("epochs", 50), eta_min=1e-5
        )
    else:
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=5)

    epochs = config.get("epochs", 50)
    patience = config.get("early_stopping", 10)
    best_val_loss = float("inf")
    wait = 0

    output_dir.mkdir(parents=True, exist_ok=True)

    all_labels, all_preds = [], []

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
        epoch_preds, epoch_labels = [], []
        with torch.no_grad():
            for features, targets in val_loader:
                features, targets = features.to(device), targets.to(device)
                outputs = model(features)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * features.size(0)
                _, predicted = outputs.max(1)
                correct += predicted.eq(targets).sum().item()
                total += targets.size(0)
                epoch_preds.extend(predicted.cpu().numpy())
                epoch_labels.extend(targets.cpu().numpy())

        val_loss /= len(val_ds)
        val_acc = correct / total if total else 0
        scheduler.step(val_loss) if not isinstance(scheduler, optim.lr_scheduler.CosineAnnealingLR) else scheduler.step()

        print(f"Epoch {epoch + 1}/{epochs} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | val_acc={val_acc:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            wait = 0
            all_preds, all_labels = epoch_preds, epoch_labels
            torch.save({"model_state_dict": model.state_dict(), "labels": labels},
                       output_dir / "model.pt")
        else:
            wait += 1
            if wait >= patience:
                break

    from sklearn.metrics import classification_report, confusion_matrix as sklearn_cm

    label_names = labels
    report = classification_report(all_labels, all_preds, labels=list(range(len(labels))),
                                   target_names=label_names, output_dict=True, zero_division=0)
    cm = sklearn_cm(all_labels, all_preds, labels=list(range(len(labels))))

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