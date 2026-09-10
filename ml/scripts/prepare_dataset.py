"""Dataset preparation pipeline.

Creates a manifest from raw data, validates integrity, detects duplicates,
performs train/val/test splits, and saves processed data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.manifest import DatasetManifest, SampleManifest, _normalize_label

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


def discover_files(data_dir: Path, modality: str) -> list[Path]:
    exts = AUDIO_EXTENSIONS if modality == "audio" else IMAGE_EXTENSIONS
    return sorted(p for p in data_dir.rglob("*") if p.suffix.lower() in exts)


def build_manifest(
    data_dir: Path,
    modality: str,
    label_map: dict[str, str] | None = None,
) -> DatasetManifest:
    files = discover_files(data_dir, modality)
    samples: list[SampleManifest] = []

    for i, fpath in enumerate(files):
        parent_label = fpath.parent.name if fpath.parent != data_dir else "unknown"
        raw_label = parent_label
        normalized = _normalize_label(raw_label)

        if label_map and raw_label in label_map:
            normalized = _normalize_label(label_map[raw_label])
            raw_label = label_map[raw_label]

        duration = 0.0
        if modality == "audio":
            try:
                import soundfile as sf
                info = sf.info(str(fpath))
                duration = info.duration
            except Exception:
                pass
        elif modality == "vision":
            try:
                from PIL import Image
                with Image.open(fpath) as img:
                    duration = 0.0
            except Exception:
                pass

        sample = SampleManifest(
            sample_id=fpath.stem,
            source=data_dir.name,
            dog_id=f"dog_{i}",
            modality=modality,
            path=str(fpath),
            label=raw_label,
            normalized_label=normalized,
            duration=duration,
            split="unassigned",
            metadata={"parent_dir": fpath.parent.name},
        )
        sample.compute_file_hash()
        samples.append(sample)

    return DatasetManifest(
        version="1.0.0",
        samples=samples,
        metadata={"data_dir": str(data_dir), "modality": modality},
    )


def validate_manifest(manifest: DatasetManifest) -> list[str]:
    return manifest.validate_integrity()


def detect_duplicates(manifest: DatasetManifest) -> dict[str, list[str]]:
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for sample in manifest.samples:
        fh = sample.file_hash
        if not fh:
            h = hashlib.sha256()
            try:
                with open(sample.path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                fh = h.hexdigest()
            except OSError:
                continue
        hash_groups[fh].append(sample.sample_id)
    return {h: ids for h, ids in hash_groups.items() if len(ids) > 1}


def detect_cross_split_leakage(manifest: DatasetManifest) -> list[tuple[str, str, str, str]]:
    by_hash: dict[str, dict[str, str]] = {}
    leaks: list[tuple[str, str, str, str]] = []
    for sample in manifest.samples:
        fh = sample.file_hash
        if not fh:
            continue
        if fh in by_hash:
            prev = by_hash[fh]
            if prev["split"] != sample.split and prev["split"] != "unassigned" and sample.split != "unassigned":
                leaks.append((prev["id"], sample.sample_id, prev["split"], sample.split))
        by_hash[fh] = {"id": sample.sample_id, "split": sample.split}
    return leaks


def split_dataset(
    manifest: DatasetManifest,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
    stratify_by: str = "normalized_label",
) -> DatasetManifest:
    rng = random.Random(seed)

    groups: dict[str, list[SampleManifest]] = defaultdict(list)
    for sample in manifest.samples:
        key = getattr(sample, stratify_by, "default")
        groups[key].append(sample)

    train, val, test = [], [], []

    for _label, group in groups.items():
        rng.shuffle(group)
        n = len(group)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        train.extend(group[:n_train])
        val.extend(group[n_train : n_train + n_val])
        test.extend(group[n_train + n_val :])

    for s in train:
        s.split = "train"
    for s in val:
        s.split = "val"
    for s in test:
        s.split = "test"

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)

    return DatasetManifest(
        version=manifest.version,
        samples=train + val + test,
        metadata={**manifest.metadata, "split_ratios": {"train": train_ratio, "val": val_ratio, "test": test_ratio}},
    )


def save_processed(manifest: DatasetManifest, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest.save_yaml(output_dir / "manifest.yaml")

    stats = manifest.get_statistics()
    with open(output_dir / "statistics.json", "w") as f:
        json.dump(stats, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a BARKLY dataset")
    parser.add_argument("raw_data_path", help="Path to raw data directory")
    parser.add_argument("output_path", help="Path to save processed dataset")
    parser.add_argument("--config", help="Optional YAML config file")
    parser.add_argument("--modality", choices=["audio", "vision"], default="audio")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    config = {}
    if args.config:
        with open(args.config) as f:
            config = yaml.safe_load(f)

    raw_dir = Path(args.raw_data_path)
    output_dir = Path(args.output_path)
    modality = config.get("modality", args.modality)

    print(f"Building manifest from {raw_dir} ({modality})...")
    manifest = build_manifest(raw_dir, modality)
    print(f"  Found {len(manifest.samples)} samples")

    print("Validating manifest...")
    errors = validate_manifest(manifest)
    if errors:
        print(f"  WARNING: {len(errors)} validation errors")
        for e in errors[:10]:
            print(f"    - {e}")
    else:
        print("  All samples valid")

    print("Detecting duplicates...")
    dupes = detect_duplicates(manifest)
    if dupes:
        print(f"  Found {len(dupes)} duplicate groups")
    else:
        print("  No duplicates found")

    print("Splitting dataset...")
    manifest = split_dataset(
        manifest,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    split_counts = Counter(s.split for s in manifest.samples)
    for sp, cnt in split_counts.items():
        print(f"  {sp}: {cnt}")

    leaks = detect_cross_split_leakage(manifest)
    if leaks:
        print(f"  WARNING: {len(leaks)} cross-split leakage pairs found")

    print(f"Saving processed dataset to {output_dir}...")
    save_processed(manifest, output_dir)
    print("Done.")


if __name__ == "__main__":
    main()
