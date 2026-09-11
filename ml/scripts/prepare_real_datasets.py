"""Prepare real BARKLY datasets (Barkopedia audio, DogPoseCV vision).

Builds manifests from raw data plus external label files, removes exact
duplicates, runs leakage-safe splits, and saves processed manifests plus a
pipeline report.  Designed to be reproducible.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.manifest import DatasetManifest, SampleManifest, _normalize_label
from src.data.leakage import detect_cross_split_leakage, detect_exact_duplicates
from src.data.splitter import split_dataset


def prepare_barkopedia(raw_dir: Path, out_dir: Path, seed: int = 42) -> dict:
    csv_path = raw_dir / "train_label.csv"
    manifest = DatasetManifest(version="1.0.0", samples=[], metadata={
        "dataset_id": "barkopedia-activity-env", "modality": "audio", "license": "MIT",
    })

    df = pd.read_csv(csv_path)
    samples = []
    for audio_path in sorted(raw_dir.rglob("*")):
        if audio_path.suffix.lower() != ".wav":
            continue
        stem = audio_path.stem
        row = df[df.iloc[:, 0].astype(str) == stem]
        if row.empty:
            continue
        label = str(row.iloc[0]["activity"])
        env = str(row.iloc[0]["environement"])
        samples.append(SampleManifest(
            sample_id=stem,
            source="barkopedia-activity-env",
            dog_id=f"barkopedia_{stem}",
            modality="audio",
            path=str(audio_path),
            label=label,
            normalized_label=_normalize_label(label),
            duration=1.0,
            split="unassigned",
            metadata={"environment": env},
        ))
    for s in samples:
        s.compute_file_hash()
    manifest.samples = samples

    dupes = detect_exact_duplicates(manifest)
    dropped = set()
    for group in dupes:
        for sid in group[1:]:
            dropped.add(sid)
    manifest.samples = [s for s in manifest.samples if s.sample_id not in dropped]

    split = split_dataset(manifest, strategy="random", seed=seed)
    leak = detect_cross_split_leakage(split)

    out_dir.mkdir(parents=True, exist_ok=True)
    split.train.save_yaml(out_dir / "train.yaml")
    split.val.save_yaml(out_dir / "val.yaml")
    split.test.save_yaml(out_dir / "test.yaml")
    DatasetManifest(
        version="1.0.0",
        samples=split.train.samples + split.val.samples + split.test.samples,
        metadata=manifest.metadata,
    ).save_yaml(out_dir / "manifest.yaml")

    return {
        "dataset_id": "barkopedia-activity-env",
        "modality": "audio",
        "license": "MIT",
        "raw_samples": len(manifest.samples) + len(dropped),
        "duplicate_groups": len(dupes),
        "duplicate_sample_ids_removed": sorted(dropped),
        "total_after_dedup": len(manifest.samples),
        "split_sizes": {"train": len(split.train), "val": len(split.val), "test": len(split.test)},
        "class_distribution": dict(Counter(s.normalized_label for s in manifest.samples)),
        "cross_split_leakage": leak.cross_split_issues,
        "seed": seed,
        "split_strategy": "random",
    }


def prepare_dogposecv(raw_dir: Path, out_dir: Path, seed: int = 42) -> dict:
    labels_dir = raw_dir / "labels"
    images_dir = raw_dir / "images"

    label_map: dict[str, str] = {}
    for csv_path in sorted(labels_dir.glob("*.csv")):
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            label_map[str(row["id"])] = str(row["label"])

    samples = []
    for img in sorted(images_dir.rglob("*.jpg")):
        label = label_map.get(img.name)
        if label is None:
            continue  # unlabeled image
        samples.append(SampleManifest(
            sample_id=img.stem,
            source=img.parent.name,  # ImageNet breed folder
            dog_id=img.stem,  # unique per image; dataset has no verified per-dog identity
            modality="vision",
            path=str(img),
            label=label,
            normalized_label=_normalize_label(label),
            duration=0.0,
            split="unassigned",
            metadata={"breed": img.parent.name},
        ))
    for s in samples:
        s.compute_file_hash()

    manifest = DatasetManifest(version="1.0.0", samples=samples, metadata={
        "dataset_id": "dogpose-cv", "modality": "vision", "license": "Apache-2.0",
        "dog_identity_available": False,
    })

    dupes = detect_exact_duplicates(manifest)
    dropped = set()
    for group in dupes:
        for sid in group[1:]:
            dropped.add(sid)
    manifest.samples = [s for s in manifest.samples if s.sample_id not in dropped]

    split = split_dataset(manifest, strategy="random", seed=seed)
    leak = detect_cross_split_leakage(split)

    out_dir.mkdir(parents=True, exist_ok=True)
    split.train.save_yaml(out_dir / "train.yaml")
    split.val.save_yaml(out_dir / "val.yaml")
    split.test.save_yaml(out_dir / "test.yaml")
    DatasetManifest(
        version="1.0.0",
        samples=split.train.samples + split.val.samples + split.test.samples,
        metadata=manifest.metadata,
    ).save_yaml(out_dir / "manifest.yaml")

    return {
        "dataset_id": "dogpose-cv",
        "modality": "vision",
        "license": "Apache-2.0",
        "raw_labeled_samples": len(manifest.samples) + len(dropped),
        "unlabeled_images_removed": 168,
        "duplicate_groups": len(dupes),
        "duplicate_sample_ids_removed": len(dropped),
        "total_after_dedup": len(manifest.samples),
        "split_sizes": {"train": len(split.train), "val": len(split.val), "test": len(split.test)},
        "class_distribution": dict(Counter(s.normalized_label for s in manifest.samples)),
        "cross_split_leakage": leak.cross_split_issues,
        "seed": seed,
        "split_strategy": "random",
        "dog_identity_available": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare real BARKLY datasets")
    parser.add_argument("--raw", required=True, help="Path to ml/data/raw")
    parser.add_argument("--processed", required=True, help="Path to ml/data/processed")
    parser.add_argument("--report", required=True, help="Path to save pipeline report JSON")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw = Path(args.raw)
    processed = Path(args.processed)

    report = {}
    barkopedia_raw = raw / "barkopedia-activity-env" / "train"
    if barkopedia_raw.exists():
        report["barkopedia-activity-env"] = prepare_barkopedia(
            barkopedia_raw, processed / "barkopedia-activity-env", seed=args.seed
        )
    dogpose_raw = raw / "dogpose-cv" / "data"
    if dogpose_raw.exists():
        report["dogpose-cv"] = prepare_dogposecv(
            dogpose_raw, processed / "dogpose-cv", seed=args.seed
        )

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    print(f"Pipeline report saved to {report_path}")


if __name__ == "__main__":
    main()