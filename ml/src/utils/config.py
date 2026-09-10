from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_config(config: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


@dataclass
class MLConfig:
    model_type: str = "audio_cnn"
    sample_rate: int = 22050
    duration: float = 3.0
    n_mfcc: int = 13
    n_mels: int = 128
    batch_size: int = 32
    lr: float = 0.001
    epochs: int = 50
    early_stopping_patience: int = 10
    seed: int = 42
    split_strategy: str = "dog_level"
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    confidence_threshold: float = 0.5
    ood_threshold: float | None = None
    class_weight: str | dict | None = "balanced"
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MLConfig:
        known_fields = {
            k: v for k, v in data.items() if k in cls.__dataclass_fields__
            and k not in ("extra",)
        }
        extra_keys = set(data.keys()) - set(known_fields.keys())
        extra = {k: data[k] for k in extra_keys}
        return cls(**known_fields, extra=extra)

    @classmethod
    def from_yaml(cls, path: str | Path) -> MLConfig:
        return cls.from_dict(load_config(path))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(d.pop("extra"))
        return d

    def to_yaml(self, path: str | Path) -> None:
        save_config(self.to_dict(), path)