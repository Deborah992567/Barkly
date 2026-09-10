from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from .manifest import DatasetManifest, SampleManifest


@dataclass
class LeakageReport:
    exact_duplicates: list[list[str]] = field(default_factory=list)
    near_duplicates: list[list[str]] = field(default_factory=list)
    cross_split_issues: dict[str, list[str]] = field(default_factory=dict)
    source_leakage: list[dict[str, str]] = field(default_factory=list)
    has_issues: bool = False

    def summary(self) -> str:
        lines: list[str] = []
        if self.exact_duplicates:
            lines.append(f"Exact duplicate groups: {len(self.exact_duplicates)}")
        if self.near_duplicates:
            lines.append(f"Near-duplicate groups: {len(self.near_duplicates)}")
        if self.cross_split_issues:
            lines.append(
                f"Cross-split issues: {len(self.cross_split_issues)} categories"
            )
        if self.source_leakage:
            lines.append(f"Source leakage entries: {len(self.source_leakage)}")
        if not lines:
            return "No leakage detected."
        return "\n".join(lines)


def _compute_file_hash(path: str) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, OSError):
        return ""


def detect_exact_duplicates(manifest: DatasetManifest) -> list[list[str]]:
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for sample in manifest.samples:
        if sample.file_hash:
            hash_groups[sample.file_hash].append(sample.sample_id)
        else:
            file_hash = _compute_file_hash(sample.path)
            if file_hash:
                hash_groups[file_hash].append(sample.sample_id)
    return [ids for ids in hash_groups.values() if len(ids) > 1]


def detect_near_duplicates(
    manifest: DatasetManifest,
    threshold: float = 0.95,
) -> list[list[str]]:
    import librosa

    embeddings: dict[str, np.ndarray] = {}
    for sample in manifest.samples:
        try:
            y, sr = librosa.load(sample.path, sr=22050, duration=3.0)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            embedding = np.mean(mfcc, axis=1)
            embeddings[sample.sample_id] = embedding
        except Exception:
            continue

    ids = list(embeddings.keys())
    n = len(ids)
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            a = embeddings[ids[i]]
            b = embeddings[ids[j]]
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a > 0 and norm_b > 0:
                cos_sim = float(np.dot(a, b) / (norm_a * norm_b))
                sim_matrix[i, j] = cos_sim
                sim_matrix[j, i] = cos_sim

    visited: set[int] = set()
    groups: list[list[str]] = []
    for i in range(n):
        if i in visited:
            continue
        group = [ids[i]]
        visited.add(i)
        for j in range(i + 1, n):
            if j in visited:
                continue
            if sim_matrix[i, j] >= threshold:
                group.append(ids[j])
                visited.add(j)
        if len(group) > 1:
            groups.append(group)

    return groups


def detect_cross_split_leakage(split_manifest: "SplitManifest") -> LeakageReport:
    report = LeakageReport()

    from .splitter import SplitManifest

    train_hashes = {s.file_hash for s in split_manifest.train.samples if s.file_hash}
    val_hashes = {s.file_hash for s in split_manifest.val.samples if s.file_hash}
    test_hashes = {s.file_hash for s in split_manifest.test.samples if s.file_hash}

    train_ids = {s.sample_id for s in split_manifest.train.samples}
    val_ids = {s.sample_id for s in split_manifest.val.samples}
    test_ids = {s.sample_id for s in split_manifest.test.samples}

    train_dogs = {s.dog_id for s in split_manifest.train.samples}
    val_dogs = {s.dog_id for s in split_manifest.val.samples}
    test_dogs = {s.dog_id for s in split_manifest.test.samples}

    issues: dict[str, list[str]] = {}
    if train_dogs & val_dogs:
        issues["train_val_dog_overlap"] = sorted(train_dogs & val_dogs)
    if train_dogs & test_dogs:
        issues["train_test_dog_overlap"] = sorted(train_dogs & test_dogs)
    if val_dogs & test_dogs:
        issues["val_test_dog_overlap"] = sorted(val_dogs & test_dogs)

    if train_hashes & val_hashes:
        issues["train_val_hash_overlap"] = sorted(train_hashes & val_hashes)
    if train_hashes & test_hashes:
        issues["train_test_hash_overlap"] = sorted(train_hashes & test_hashes)
    if val_hashes & test_hashes:
        issues["val_test_hash_overlap"] = sorted(val_hashes & test_hashes)

    if train_ids & val_ids:
        issues["train_val_id_overlap"] = sorted(train_ids & val_ids)
    if train_ids & test_ids:
        issues["train_test_id_overlap"] = sorted(train_ids & test_ids)
    if val_ids & test_ids:
        issues["val_test_id_overlap"] = sorted(val_ids & test_ids)

    report.cross_split_issues = issues
    report.has_issues = bool(issues)
    return report


def detect_source_leakage(manifest: DatasetManifest) -> list[dict[str, str]]:
    dog_sources: dict[str, set[str]] = defaultdict(set)
    for sample in manifest.samples:
        dog_sources[sample.dog_id].add(sample.source)

    overlaps: list[dict[str, str]] = []
    for dog_id, sources in dog_sources.items():
        if len(sources) > 1:
            overlaps.append(
                {"dog_id": dog_id, "sources": ", ".join(sorted(sources))}
            )
    return overlaps
