from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .manifest import DatasetManifest, SampleManifest


@dataclass
class ValidationReport:
    total_samples: int = 0
    valid_samples: int = 0
    invalid_samples: int = 0
    missing_files: list[str] = field(default_factory=list)
    corrupted_files: list[str] = field(default_factory=list)
    duplicates: list[list[str]] = field(default_factory=list)
    label_distribution: dict[str, int] = field(default_factory=dict)
    duration_distribution: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_audio_file(path: str | Path) -> bool:
    path = Path(path)
    if not path.exists():
        return False
    if not path.is_file():
        return False
    if path.stat().st_size == 0:
        return False
    try:
        import soundfile as sf

        info = sf.info(str(path))
        if info.duration <= 0:
            return False
        return True
    except Exception:
        pass
    try:
        import librosa

        librosa.load(str(path), sr=None, duration=0.1)
        return True
    except Exception:
        return False


def validate_dataset(manifest: DatasetManifest) -> ValidationReport:
    report = ValidationReport()
    report.total_samples = len(manifest.samples)

    seen_ids: dict[str, list[str]] = {}
    seen_hashes: dict[str, list[str]] = {}
    durations: list[float] = []
    valid_count = 0

    for sample in manifest.samples:
        is_valid = True

        # Check for missing files
        if not Path(sample.path).exists():
            report.missing_files.append(sample.sample_id)
            is_valid = False

        # Check for corrupted files
        elif not validate_audio_file(sample.path):
            report.corrupted_files.append(sample.sample_id)
            is_valid = False

        # Check duplicate IDs
        if sample.sample_id not in seen_ids:
            seen_ids[sample.sample_id] = []
        seen_ids[sample.sample_id].append(sample.path)

        # Check duplicate hashes
        if sample.file_hash:
            if sample.file_hash not in seen_hashes:
                seen_hashes[sample.file_hash] = []
            seen_hashes[sample.file_hash].append(sample.sample_id)

        # Collect label distribution
        report.label_distribution[sample.normalized_label] = (
            report.label_distribution.get(sample.normalized_label, 0) + 1
        )

        # Collect duration
        if sample.duration > 0:
            durations.append(sample.duration)

        if is_valid:
            valid_count += 1

    report.valid_samples = valid_count
    report.invalid_samples = report.total_samples - valid_count

    # Find duplicate IDs
    for sid, paths in seen_ids.items():
        if len(paths) > 1:
            report.duplicates.append([sid] + paths)

    # Find duplicate hashes
    for fhash, sids in seen_hashes.items():
        if len(sids) > 1:
            report.duplicates.append(sids)

    # Duration distribution
    if durations:
        dur_arr = np.array(durations)
        report.duration_distribution = {
            "mean": float(np.mean(dur_arr)),
            "std": float(np.std(dur_arr)),
            "min": float(np.min(dur_arr)),
            "max": float(np.max(dur_arr)),
            "median": float(np.median(dur_arr)),
        }

    # Generate warnings
    for label, count in report.label_distribution.items():
        if count < 10:
            report.warnings.append(
                f"Class '{label}' has only {count} samples (recommend >= 10)"
            )

    if report.missing_files:
        report.warnings.append(
            f"{len(report.missing_files)} samples reference missing files"
        )
    if report.corrupted_files:
        report.warnings.append(
            f"{len(report.corrupted_files)} samples reference corrupted/unreadable files"
        )
    if report.duplicates:
        report.warnings.append(
            f"{len(report.duplicates)} groups of duplicate samples found"
        )

    return report
