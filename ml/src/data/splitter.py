from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field

from .manifest import DatasetManifest, SampleManifest


@dataclass
class SplitManifest:
    train: DatasetManifest
    val: DatasetManifest
    test: DatasetManifest
    leakage_checks: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "train_size": len(self.train),
            "val_size": len(self.val),
            "test_size": len(self.test),
            "train_samples": [s.to_dict() for s in self.train.samples],
            "val_samples": [s.to_dict() for s in self.val.samples],
            "test_samples": [s.to_dict() for s in self.test.samples],
        }

    def get_statistics(self) -> dict[str, dict[str, int]]:
        stats: dict[str, dict[str, int]] = {}
        for split_name, manifest in [
            ("train", self.train),
            ("val", self.val),
            ("test", self.test),
        ]:
            dist: dict[str, int] = {}
            for s in manifest.samples:
                dist[s.normalized_label] = dist.get(s.normalized_label, 0) + 1
            stats[split_name] = dist
        return stats


from typing import Any


def _assign_splits_random(
    samples: list[SampleManifest],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[SampleManifest], list[SampleManifest], list[SampleManifest]]:
    rng = random.Random(seed)
    shuffled = list(samples)
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train = shuffled[:n_train]
    val = shuffled[n_train : n_train + n_val]
    test = shuffled[n_train + n_val :]
    return train, val, test


def _assign_splits_dog_level(
    samples: list[SampleManifest],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[SampleManifest], list[SampleManifest], list[SampleManifest]]:
    dog_groups: dict[str, list[SampleManifest]] = defaultdict(list)
    for s in samples:
        dog_groups[s.dog_id].append(s)

    rng = random.Random(seed)
    dog_ids = list(dog_groups.keys())
    rng.shuffle(dog_ids)

    n_dogs = len(dog_ids)
    n_train_dogs = max(1, int(n_dogs * train_ratio))
    n_val_dogs = max(1, int(n_dogs * val_ratio))

    train_dogs = dog_ids[:n_train_dogs]
    val_dogs = dog_ids[n_train_dogs : n_train_dogs + n_val_dogs]
    test_dogs = dog_ids[n_train_dogs + n_val_dogs :]

    train = [s for d in train_dogs for s in dog_groups[d]]
    val = [s for d in val_dogs for s in dog_groups[d]]
    test = [s for d in test_dogs for s in dog_groups[d]]
    return train, val, test


def _assign_splits_source_level(
    samples: list[SampleManifest],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[SampleManifest], list[SampleManifest], list[SampleManifest]]:
    source_groups: dict[str, list[SampleManifest]] = defaultdict(list)
    for s in samples:
        source_groups[s.source].append(s)

    rng = random.Random(seed)
    source_ids = list(source_groups.keys())
    rng.shuffle(source_ids)

    n_src = len(source_ids)
    n_train_src = max(1, int(n_src * train_ratio))
    n_val_src = max(1, int(n_src * val_ratio))

    train_sources = source_ids[:n_train_src]
    val_sources = source_ids[n_train_src : n_train_src + n_val_src]
    test_sources = source_ids[n_train_src + n_val_src :]

    train = [s for src in train_sources for s in source_groups[src]]
    val = [s for src in val_sources for s in source_groups[src]]
    test = [s for src in test_sources for s in source_groups[src]]
    return train, val, test


def _check_leakage(
    train: list[SampleManifest],
    val: list[SampleManifest],
    test: list[SampleManifest],
) -> dict[str, Any]:
    train_dogs = {s.dog_id for s in train}
    val_dogs = {s.dog_id for s in val}
    test_dogs = {s.dog_id for s in test}

    train_val_overlap = train_dogs & val_dogs
    train_test_overlap = train_dogs & test_dogs
    val_test_overlap = val_dogs & test_dogs

    train_ids = {s.sample_id for s in train}
    val_ids = {s.sample_id for s in val}
    test_ids = {s.sample_id for s in test}

    train_val_dup = train_ids & val_ids
    train_test_dup = train_ids & test_ids
    val_test_dup = val_ids & test_ids

    train_hashes = {s.file_hash for s in train if s.file_hash}
    val_hashes = {s.file_hash for s in val if s.file_hash}
    test_hashes = {s.file_hash for s in test if s.file_hash}

    train_val_hash = train_hashes & val_hashes
    train_test_hash = train_hashes & test_hashes
    val_test_hash = val_hashes & test_hashes

    return {
        "dog_leakage": {
            "train_val": list(train_val_overlap),
            "train_test": list(train_test_overlap),
            "val_test": list(val_test_overlap),
        },
        "id_leakage": {
            "train_val": list(train_val_dup),
            "train_test": list(train_test_dup),
            "val_test": list(val_test_dup),
        },
        "hash_leakage": {
            "train_val": list(train_val_hash),
            "train_test": list(train_test_hash),
            "val_test": list(val_test_hash),
        },
        "has_leakage": bool(
            train_val_overlap or train_test_overlap or val_test_overlap
            or train_val_dup or train_test_dup or val_test_dup
            or train_val_hash or train_test_hash or val_test_hash
        ),
    }


def split_dataset(
    manifest: DatasetManifest,
    strategy: str = "dog_level",
    seed: int = 42,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> SplitManifest:
    samples = manifest.samples

    if strategy == "random":
        train, val, test = _assign_splits_random(samples, train_ratio, val_ratio, seed)
    elif strategy == "dog_level":
        train, val, test = _assign_splits_dog_level(samples, train_ratio, val_ratio, seed)
    elif strategy == "source_level":
        train, val, test = _assign_splits_source_level(
            samples, train_ratio, val_ratio, seed
        )
    else:
        raise ValueError(f"Unknown split strategy: {strategy}")

    def _make_split(split_samples: list[SampleManifest], split_name: str) -> DatasetManifest:
        for s in split_samples:
            s.split = split_name
        return DatasetManifest(
            version=manifest.version,
            samples=split_samples,
            metadata={**manifest.metadata, "split_strategy": strategy, "seed": seed},
        )

    train_manifest = _make_split(train, "train")
    val_manifest = _make_split(val, "val")
    test_manifest = _make_split(test, "test")

    leakage_checks = _check_leakage(train, val, test)

    return SplitManifest(
        train=train_manifest,
        val=val_manifest,
        test=test_manifest,
        leakage_checks=leakage_checks,
    )
