from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


@dataclass
class SampleManifest:
    sample_id: str
    source: str
    dog_id: str
    modality: str
    path: str
    label: str
    normalized_label: str
    duration: float
    split: str
    metadata: dict[str, Any] = field(default_factory=dict)
    file_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "source": self.source,
            "dog_id": self.dog_id,
            "modality": self.modality,
            "path": self.path,
            "label": self.label,
            "normalized_label": self.normalized_label,
            "duration": self.duration,
            "split": self.split,
            "metadata": self.metadata,
            "file_hash": self.file_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SampleManifest:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def compute_file_hash(self) -> str:
        if self.file_hash:
            return self.file_hash
        try:
            h = hashlib.sha256()
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            self.file_hash = h.hexdigest()
        except (FileNotFoundError, OSError):
            self.file_hash = ""
        return self.file_hash


@dataclass
class DatasetManifest:
    version: str = "1.0.0"
    samples: list[SampleManifest] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> DatasetManifest:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        samples = [SampleManifest.from_dict(s) for s in data.get("samples", [])]
        return cls(
            version=data.get("version", "1.0.0"),
            samples=samples,
            metadata=data.get("metadata", {}),
        )

    def save_yaml(self, path: str | Path) -> None:
        data = {
            "version": self.version,
            "metadata": self.metadata,
            "samples": [s.to_dict() for s in self.samples],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def validate_integrity(self) -> list[str]:
        errors: list[str] = []
        seen_ids: set[str] = set()
        for i, sample in enumerate(self.samples):
            if not sample.sample_id:
                errors.append(f"Sample at index {i} has empty sample_id")
            elif sample.sample_id in seen_ids:
                errors.append(f"Duplicate sample_id: {sample.sample_id}")
            seen_ids.add(sample.sample_id)

            if not sample.path:
                errors.append(f"Sample {sample.sample_id} has empty path")
            if not sample.label:
                errors.append(f"Sample {sample.sample_id} has empty label")
            if sample.duration < 0:
                errors.append(f"Sample {sample.sample_id} has negative duration")
        return errors

    def get_statistics(self) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "total_samples": len(self.samples),
            "samples_per_class": {},
            "samples_per_split": {},
            "samples_per_dog": {},
            "samples_per_source": {},
            "label_mapping": {},
        }

        for sample in self.samples:
            stats["samples_per_class"][sample.normalized_label] = (
                stats["samples_per_class"].get(sample.normalized_label, 0) + 1
            )
            stats["samples_per_split"][sample.split] = (
                stats["samples_per_split"].get(sample.split, 0) + 1
            )
            stats["samples_per_dog"][sample.dog_id] = (
                stats["samples_per_dog"].get(sample.dog_id, 0) + 1
            )
            stats["samples_per_source"][sample.source] = (
                stats["samples_per_source"].get(sample.source, 0) + 1
            )
            if sample.normalized_label not in stats["label_mapping"]:
                stats["label_mapping"][sample.normalized_label] = sample.label

        return stats

    def filter_by_split(self, split: str) -> DatasetManifest:
        return DatasetManifest(
            version=self.version,
            samples=[s for s in self.samples if s.split == split],
            metadata=self.metadata,
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> SampleManifest:
        return self.samples[idx]


def _normalize_label(label: str) -> str:
    return label.strip().lower().replace(" ", "_").replace("-", "_")


def create_manifest(
    audio_dir: str | Path,
    csv_path: str | Path | None = None,
    label_column: str = "label",
    dog_id_column: str = "dog_id",
    source_column: str = "source",
    modality: str = "audio",
) -> DatasetManifest:
    audio_dir = Path(audio_dir)
    samples: list[SampleManifest] = []

    df: pd.DataFrame | None = None
    if csv_path is not None:
        df = pd.read_csv(csv_path)

    audio_extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    audio_files = sorted(
        p for p in audio_dir.rglob("*") if p.suffix.lower() in audio_extensions
    )

    for i, audio_path in enumerate(audio_files):
        sample_id = audio_path.stem
        label = "unknown"
        dog_id = f"dog_{i}"
        source = audio_dir.name

        if df is not None:
            match = df[df.iloc[:, 0].astype(str) == sample_id]
            if not match.empty:
                row = match.iloc[0]
                label = str(row.get(label_column, "unknown"))
                dog_id = str(row.get(dog_id_column, f"dog_{i}"))
                source = str(row.get(source_column, audio_dir.name))

        normalized_label = _normalize_label(label)
        duration = 0.0
        try:
            import soundfile as sf

            info = sf.info(str(audio_path))
            duration = info.duration
        except Exception:
            pass

        sample = SampleManifest(
            sample_id=sample_id,
            source=source,
            dog_id=dog_id,
            modality=modality,
            path=str(audio_path),
            label=label,
            normalized_label=normalized_label,
            duration=duration,
            split="unassigned",
            metadata={},
        )
        sample.compute_file_hash()
        samples.append(sample)

    return DatasetManifest(
        version="1.0.0",
        samples=samples,
        metadata={"audio_dir": str(audio_dir), "csv_path": str(csv_path) if csv_path else None},
    )
