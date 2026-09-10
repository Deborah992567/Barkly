from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

import torchvision.models as models


@dataclass
class VisionBaselineConfig:
    model_name: str = "mobilenet_v3"
    num_classes: int = 2
    pretrained: bool = True
    freeze_backbone: bool = False
    fine_tune_layers: int = 0
    lr: float = 0.001
    device: str | None = None


class VisionBaselineModel:
    def __init__(self, config: VisionBaselineConfig | None = None):
        self.config = config or VisionBaselineConfig()
        self.device = torch.device(
            self.config.device
            or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model = self._build_model()
        self.model.to(self.device)
        self.optimizer = self._build_optimizer()
        self.criterion = nn.CrossEntropyLoss()

    def _build_model(self) -> nn.Module:
        weights = "DEFAULT" if self.config.pretrained else None
        if self.config.model_name == "mobilenet_v3":
            model = models.mobilenet_v3_small(weights=weights)
            in_features = model.classifier[3].in_features
            model.classifier[3] = nn.Linear(
                in_features, self.config.num_classes
            )
        elif self.config.model_name == "efficientnet":
            model = models.efficientnet_b0(weights=weights)
            in_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(
                in_features, self.config.num_classes
            )
        else:
            raise ValueError(
                f"Unsupported model: {self.config.model_name}. "
                "Use 'mobilenet_v3' or 'efficientnet'."
            )

        self._apply_freezing(model)
        return model

    def _apply_freezing(self, model: nn.Module) -> None:
        if not self.config.pretrained:
            return

        all_layers = [m for m in model.children() if hasattr(m, "parameters")]
        if self.config.fine_tune_layers > 0:
            for param in model.parameters():
                param.requires_grad = False
            trainable = all_layers[-1 - self.config.fine_tune_layers :]
            for module in trainable:
                for param in module.parameters():
                    param.requires_grad = True
        elif not self.config.freeze_backbone:
            for param in model.parameters():
                param.requires_grad = True

    def _build_optimizer(self) -> torch.optim.Optimizer:
        trainable_params = [
            p for p in self.model.parameters() if p.requires_grad
        ]
        return torch.optim.Adam(trainable_params, lr=self.config.lr)

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader | None = None,
        epochs: int = 30,
    ) -> list[dict[str, float]]:
        history: list[dict[str, float]] = []
        for epoch in range(epochs):
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for images, labels in train_loader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                self.optimizer.zero_grad()
                logits = self.model(images)
                loss = self.criterion(logits, labels)
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item() * images.size(0)
                preds = logits.argmax(dim=1)
                train_correct += (preds == labels).sum().item()
                train_total += labels.size(0)

            record: dict[str, float] = {
                "train_loss": train_loss / max(train_total, 1),
                "train_accuracy": train_correct / max(train_total, 1),
            }

            if val_loader is not None:
                val_metrics = self.evaluate(val_loader)
                record.update(
                    {
                        "val_loss": val_metrics["loss"],
                        "val_accuracy": val_metrics["accuracy"],
                    }
                )
                self.model.train()

            history.append(record)
        return history

    def evaluate(self, data_loader: DataLoader) -> dict[str, float]:
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        all_preds: list[np.ndarray] = []
        all_labels: list[np.ndarray] = []

        with torch.no_grad():
            for images, labels in data_loader:
                images = images.to(self.device)
                labels = labels.to(self.device)
                logits = self.model(images)
                loss = self.criterion(logits, labels)

                total_loss += loss.item() * images.size(0)
                preds = logits.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
                all_preds.append(preds.cpu().numpy())
                all_labels.append(labels.cpu().numpy())

        return {
            "loss": total_loss / max(total, 1),
            "accuracy": correct / max(total, 1),
            "predictions": np.concatenate(all_preds),
            "labels": np.concatenate(all_labels),
        }

    def predict(self, images: torch.Tensor) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            logits = self.model(images.to(self.device))
            return logits.argmax(dim=1).cpu().numpy()

    def predict_proba(self, images: torch.Tensor) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            logits = self.model(images.to(self.device))
            return torch.softmax(logits, dim=1).cpu().numpy()

    def save(self, path: str | Path) -> None:
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "config": {
                    "model_name": self.config.model_name,
                    "num_classes": self.config.num_classes,
                    "pretrained": self.config.pretrained,
                    "lr": self.config.lr,
                },
            },
            path,
        )

    def load(self, path: str | Path) -> None:
        checkpoint = torch.load(path, map_location=self.device)
        config_data = checkpoint.get("config", {})
        self.config = VisionBaselineConfig(**config_data)
        self.model = self._build_model()
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.optimizer = self._build_optimizer()