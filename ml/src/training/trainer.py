from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader


@dataclass
class TrainingConfig:
    lr: float = 0.001
    batch_size: int = 32
    epochs: int = 50
    optimizer: str = "adam"
    scheduler: str = "reduce_on_plateau"
    seed: int = 42
    early_stopping_patience: int = 10
    weight_decay: float = 0.0001


@dataclass
class TrainingHistory:
    train_losses: list[float] = field(default_factory=list)
    val_losses: list[float] = field(default_factory=list)
    metrics: dict[str, list[float]] = field(default_factory=dict)
    best_epoch: int = -1
    best_val_score: float | None = None

    def record_epoch(
        self,
        train_loss: float,
        val_loss: float | None = None,
        extra_metrics: dict[str, float] | None = None,
    ) -> None:
        self.train_losses.append(train_loss)
        if val_loss is not None:
            self.val_losses.append(val_loss)
        if extra_metrics:
            for key, val in extra_metrics.items():
                if key not in self.metrics:
                    self.metrics[key] = []
                self.metrics[key].append(val)

    def to_dict(self) -> dict[str, list[float] | int | float | None]:
        return {
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "metrics": self.metrics,
            "best_epoch": self.best_epoch,
            "best_val_score": self.best_val_score,
        }

    def __len__(self) -> int:
        return len(self.train_losses)


@dataclass
class EvaluationMetrics:
    loss: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    confusion_matrix: np.ndarray | None = None
    predictions: list[int] = field(default_factory=list)
    labels: list[int] = field(default_factory=list)
    probabilities: np.ndarray | None = None

    def to_dict(self) -> dict[str, float | np.ndarray | None | list[int]]:
        cm = self.confusion_matrix
        if cm is not None:
            cm = cm.tolist()
        return {
            "loss": self.loss,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "confusion_matrix": cm,
            "predictions": self.predictions,
            "labels": self.labels,
            "probabilities": self.probabilities,
        }


class AudioTrainer:
    def __init__(
        self,
        model: nn.Module,
        config: TrainingConfig | None = None,
        device: str | None = None,
    ):
        self.model = model
        self.config = config or TrainingConfig()
        self.device = torch.device(
            device
            or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model.to(self.device)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = self._build_optimizer()
        self.scheduler = self._build_scheduler()
        self.history = TrainingHistory()

    def _build_optimizer(self) -> torch.optim.Optimizer:
        if self.config.optimizer == "adam":
            return torch.optim.Adam(
                self.model.parameters(),
                lr=self.config.lr,
                weight_decay=self.config.weight_decay,
            )
        elif self.config.optimizer == "sgd":
            return torch.optim.SGD(
                self.model.parameters(),
                lr=self.config.lr,
                momentum=0.9,
                weight_decay=self.config.weight_decay,
            )
        elif self.config.optimizer == "adamw":
            return torch.optim.AdamW(
                self.model.parameters(),
                lr=self.config.lr,
                weight_decay=self.config.weight_decay,
            )
        raise ValueError(f"Unsupported optimizer: {self.config.optimizer}")

    def _build_scheduler(self) -> torch.optim.lr_scheduler.LRScheduler | None:
        if self.config.scheduler == "reduce_on_plateau":
            return torch.optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer, mode="min", factor=0.5, patience=3
            )
        elif self.config.scheduler == "cosine":
            return torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=self.config.epochs
            )
        elif self.config.scheduler in (None, "none"):
            return None
        raise ValueError(f"Unsupported scheduler: {self.config.scheduler}")

    def _run_epoch(
        self,
        data_loader: DataLoader,
        training: bool,
    ) -> tuple[float, float]:
        if training:
            self.model.train()
        else:
            self.model.eval()

        total_loss = 0.0
        correct = 0
        total = 0

        for inputs, labels in data_loader:
            inputs = inputs.to(self.device)
            labels = labels.to(self.device)

            if training:
                self.optimizer.zero_grad()

            with torch.set_grad_enabled(training):
                logits = self.model(inputs)
                if logits.shape[1] != len(torch.unique(labels)) and labels.max() >= logits.shape[1]:
                    labels = labels - labels.min()
                loss = self.criterion(logits, labels)
                if training:
                    loss.backward()
                    self.optimizer.step()

            total_loss += loss.item() * inputs.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        return total_loss / max(total, 1), correct / max(total, 1)

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader | None = None,
    ) -> TrainingHistory:
        best_val_loss = float("inf")
        epochs_no_improve = 0
        best_state = None

        for epoch in range(self.config.epochs):
            train_loss, train_acc = self._run_epoch(train_loader, training=True)

            record: dict[str, float] = {"train_accuracy": train_acc}
            if val_loader is not None:
                val_loss, val_acc = self._run_epoch(val_loader, training=False)
                record["val_accuracy"] = val_acc
            else:
                val_loss = None

            self.history.record_epoch(train_loss, val_loss, record)

            if isinstance(self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                self.scheduler.step(val_loss if val_loss is not None else train_loss)
            elif self.scheduler is not None:
                self.scheduler.step()

            if val_loss is not None and val_loss < best_val_loss:
                best_val_loss = val_loss
                epochs_no_improve = 0
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                self.history.best_epoch = epoch
                self.history.best_val_score = val_loss
            elif val_loss is not None:
                epochs_no_improve += 1

            if (
                self.config.early_stopping_patience > 0
                and epochs_no_improve >= self.config.early_stopping_patience
            ):
                break

        if best_state is not None:
            self.model.load_state_dict(best_state)

        return self.history

    def evaluate(self, test_loader: DataLoader) -> EvaluationMetrics:
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

        self.model.eval()
        total_loss = 0.0
        all_preds: list[np.ndarray] = []
        all_labels: list[np.ndarray] = []
        all_probs: list[np.ndarray] = []

        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs = inputs.to(self.device)
                labels = labels.to(self.device)

                logits = self.model(inputs)
                loss = self.criterion(logits, labels)
                total_loss += loss.item() * inputs.size(0)

                probs = torch.softmax(logits, dim=1)
                preds = logits.argmax(dim=1)

                all_preds.append(preds.cpu().numpy())
                all_labels.append(labels.cpu().numpy())
                all_probs.append(probs.cpu().numpy())

        preds = np.concatenate(all_preds)
        labels = np.concatenate(all_labels)
        probs = np.concatenate(all_probs)

        return EvaluationMetrics(
            loss=total_loss / max(len(labels), 1),
            accuracy=accuracy_score(labels, preds),
            precision=precision_score(labels, preds, average="macro", zero_division=0),
            recall=recall_score(labels, preds, average="macro", zero_division=0),
            f1=f1_score(labels, preds, average="macro", zero_division=0),
            confusion_matrix=torch.zeros(
                self.model.config.num_classes, self.model.config.num_classes, dtype=torch.int64
            ).numpy(),
            predictions=preds.tolist(),
            labels=labels.tolist(),
            probabilities=probs,
        )

    def save_checkpoint(self, path: str | Path) -> None:
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "config": asdict(self.config),
                "history": self.history.to_dict(),
            },
            path,
        )

    def load_checkpoint(self, path: str | Path) -> None:
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "config" in checkpoint:
            self.config = TrainingConfig(**checkpoint["config"])
        if "history" in checkpoint:
            hist = checkpoint["history"]
            self.history = TrainingHistory(
                train_losses=hist.get("train_losses", []),
                val_losses=hist.get("val_losses", []),
                metrics=hist.get("metrics", {}),
                best_epoch=hist.get("best_epoch", -1),
                best_val_score=hist.get("best_val_score"),
            )