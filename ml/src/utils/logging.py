from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MLLogger:
    def __init__(self, log_dir: str | Path = "logs", experiment_name: str = "default"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.experiment_name = experiment_name
        self.exp_dir = self.log_dir / experiment_name
        self.exp_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"ml.{experiment_name}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            fh = logging.FileHandler(self.exp_dir / "training.log")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._history: dict[str, Any] = {}

    def log_config(self, config: Any) -> None:
        cfg = asdict(config) if is_dataclass(config) else config
        self.dump_artifact("config.json", cfg)

    def log_metric(self, name: str, value: float, step: int | None = None) -> None:
        entry: dict[str, Any] = {"value": value, "timestamp": datetime.now(timezone.utc).isoformat()}
        if step is not None:
            entry["step"] = step
        self._history.setdefault("metrics", {}).setdefault(name, []).append(entry)
        self.logger.info(f"metric {name}={value}" + (f" step={step}" if step is not None else ""))

    def log_metrics_batch(self, metrics: dict[str, float], step: int | None = None) -> None:
        for name, value in metrics.items():
            self.log_metric(name, value, step)

    def log_artifact(self, name: str, artifact_path: str | Path) -> None:
        import shutil

        artifact_path = Path(artifact_path)
        if not artifact_path.exists():
            self.logger.warning(f"Artifact not found: {artifact_path}")
            return
        dest = self.exp_dir / "artifacts" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact_path, dest)
        self.logger.info(f"logged artifact {name}")

    def dump_artifact(self, name: str, data: Any) -> None:
        dest = self.exp_dir / "artifacts"
        dest.mkdir(parents=True, exist_ok=True)
        if name.endswith(".json") or data is dict:
            with open(dest / name, "w") as f:
                json.dump(data, f, indent=2, default=str)
        else:
            with open(dest / name, "w") as f:
                f.write(str(data))
        self.logger.info(f"dumped artifact {name}")

    def save_history(self) -> None:
        with open(self.exp_dir / "history.json", "w") as f:
            json.dump(self._history, f, indent=2, default=str)
        self.logger.info(f"saved history to {self.exp_dir / 'history.json'}")

    def get_run_dir(self) -> Path:
        return self.exp_dir / self.run_id


def log_experiment(
    config: dict,
    metrics: dict[str, float],
    artifacts: dict[str, str] | None = None,
    log_dir: str | Path = "logs",
    experiment_name: str = "experiment",
) -> str:
    logger = MLLogger(log_dir=log_dir, experiment_name=experiment_name)
    logger.log_config(config)
    logger.log_metrics_batch(metrics)
    if artifacts:
        for name, path in artifacts.items():
            logger.log_artifact(name, path)
    logger.save_history()
    return logger.exp_dir.as_posix()