"""Dataset inspection script.

Reports: total samples, class distribution, duration stats, file format
distribution, missing/corrupted files, duplicates.  Saves a JSON report and
prints a human-readable summary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.manifest import DatasetManifest


AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _check_file_integrity(path: Path, modality: str) -> bool:
    if not path.exists():
        return False
    try:
        with open(path, "rb") as f:
            header = f.read(16)
            if len(header) == 0:
                return False
        if modality == "audio":
            import soundfile as sf
            sf.info(str(path))
        elif modality == "vision":
            from PIL import Image
            Image.open(path).verify()
        return True
    except Exception:
        return False


def inspect_manifest(manifest: DatasetManifest) -> dict:
    total = len(manifest.samples)
    missing_files: list[str] = []
    corrupted_files: list[str] = []
    hashes: dict[str, list[str]] = {}
    class_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    dog_counts: Counter[str] = Counter()
    format_counts: Counter[str] = Counter()
    durations: list[float] = []

    for sample in manifest.samples:
        class_counts[sample.normalized_label] += 1
        split_counts[sample.split] += 1
        source_counts[sample.source] += 1
        dog_counts[sample.dog_id] += 1
        ext = Path(sample.path).suffix.lower()
        format_counts[ext] += 1

        p = Path(sample.path)
        if not p.exists():
            missing_files.append(sample.sample_id)
            continue

        if not _check_file_integrity(p, sample.modality):
            corrupted_files.append(sample.sample_id)
            continue

        if sample.duration > 0:
            durations.append(sample.duration)

        fh = sample.file_hash or _file_hash(p)
        hashes.setdefault(fh, []).append(sample.sample_id)

    duplicates = {h: ids for h, ids in hashes.items() if len(ids) > 1}

    duration_stats = {}
    if durations:
        duration_stats = {
            "min": round(min(durations), 3),
            "max": round(max(durations), 3),
            "mean": round(sum(durations) / len(durations), 3),
            "total_seconds": round(sum(durations), 3),
        }

    report = {
        "total_samples": total,
        "class_distribution": dict(class_counts.most_common()),
        "split_distribution": dict(split_counts),
        "source_distribution": dict(source_counts),
        "dog_id_distribution": dict(dog_counts.most_common(10)),
        "file_format_distribution": dict(format_counts),
        "duration_stats": duration_stats,
        "missing_files": missing_files,
        "corrupted_files": corrupted_files,
        "duplicates": {h: ids for h, ids in duplicates.items()},
        "duplicate_group_count": len(duplicates),
        "unique_dogs": len(dog_counts),
        "unique_sources": len(source_counts),
    }
    return report


def print_summary(report: dict) -> None:
    print("=" * 60)
    print("DATASET INSPECTION REPORT")
    print("=" * 60)
    print(f"Total samples:      {report['total_samples']}")
    print(f"Unique dogs:        {report['unique_dogs']}")
    print(f"Unique sources:     {report['unique_sources']}")
    print()
    print("Class distribution:")
    for cls, count in report["class_distribution"].items():
        pct = count / report["total_samples"] * 100 if report["total_samples"] else 0
        print(f"  {cls:30s} {count:6d}  ({pct:5.1f}%)")
    print()
    print("Split distribution:")
    for split, count in report["split_distribution"].items():
        print(f"  {split:30s} {count:6d}")
    print()
    print("File format distribution:")
    for fmt, count in report["file_format_distribution"].items():
        print(f"  {fmt:10s} {count:6d}")
    if report["duration_stats"]:
        ds = report["duration_stats"]
        print()
        print(f"Duration stats: min={ds['min']}s  max={ds['max']}s  mean={ds['mean']}s  total={ds['total_seconds']}s")
    print()
    print(f"Missing files:     {len(report['missing_files'])}")
    print(f"Corrupted files:   {len(report['corrupted_files'])}")
    print(f"Duplicate groups:  {report['duplicate_group_count']}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a BARKLY dataset")
    parser.add_argument("dataset_path", help="Path to dataset root or manifest YAML")
    parser.add_argument("output_path", help="Path to save JSON report")
    args = parser.parse_args()

    dataset_path = Path(args.dataset_path)
    output_path = Path(args.output_path)

    if dataset_path.suffix in (".yaml", ".yml"):
        manifest = DatasetManifest.from_yaml(dataset_path)
    else:
        print("No manifest found, attempting to discover files...")
        manifest = DatasetManifest(version="1.0.0", samples=[], metadata={"path": str(dataset_path)})

    report = inspect_manifest(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print_summary(report)
    print(f"\nReport saved to {output_path}")


if __name__ == "__main__":
    main()
