"""Tests for data leakage detection."""

from __future__ import annotations

import hashlib
import wave
from pathlib import Path

import numpy as np
import pytest

from src.data.manifest import DatasetManifest, SampleManifest
from src.data.leakage import (
    detect_cross_split_leakage,
    detect_exact_duplicates,
)
from src.data.splitter import SplitManifest, split_dataset


def _make_wav(path: Path, sr: int = 16000, data: np.ndarray | None = None) -> str:
    if data is None:
        data = np.random.randn(sr).astype(np.float32) * 0.5
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((data * 32767).astype(np.int16).tobytes())
    return hashlib.sha256((data * 32767).astype(np.int16).tobytes()).hexdigest()


class TestExactDuplicateDetection:
    def test_identical_files_detected(self, tmp_path: Path):
        data = np.random.randn(16000).astype(np.float32) * 0.5
        h1 = _make_wav(tmp_path / "a.wav", data=data)
        h2 = _make_wav(tmp_path / "b.wav", data=data)

        samples = [
            SampleManifest("s1", "test", "d1", "audio", str(tmp_path / "a.wav"), "bark", "bark", 1.0, "train", file_hash=h1),
            SampleManifest("s2", "test", "d2", "audio", str(tmp_path / "b.wav"), "bark", "bark", 1.0, "test", file_hash=h2),
        ]
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        dupes = detect_exact_duplicates(manifest)
        assert len(dupes) == 1
        assert sorted(dupes[0]) == ["s1", "s2"]

    def test_no_duplicates_unique_files(self, tmp_path: Path):
        samples = []
        for i in range(5):
            p = tmp_path / f"f{i}.wav"
            h = _make_wav(p)
            samples.append(SampleManifest(
                f"s{i}", "test", "d0", "audio", str(p), "bark", "bark", 1.0, "train", file_hash=h,
            ))
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        dupes = detect_exact_duplicates(manifest)
        assert len(dupes) == 0


class TestCrossSplitLeakage:
    def test_same_file_in_train_and_test(self, tmp_path: Path):
        data = np.random.randn(16000).astype(np.float32) * 0.5
        h = _make_wav(tmp_path / "shared.wav", data=data)

        s1 = SampleManifest("s1", "test", "d1", "audio", str(tmp_path / "shared.wav"), "bark", "bark", 1.0, "train", file_hash=h)
        s2 = SampleManifest("s2", "test", "d2", "audio", str(tmp_path / "shared.wav"), "bark", "bark", 1.0, "test", file_hash=h)
        split_manifest = SplitManifest(
            train=DatasetManifest(version="1.0.0", samples=[s1]),
            val=DatasetManifest(version="1.0.0", samples=[]),
            test=DatasetManifest(version="1.0.0", samples=[s2]),
        )
        report = detect_cross_split_leakage(split_manifest)
        assert report.has_issues
        assert "train_test_hash_overlap" in report.cross_split_issues

    def test_no_leakage_when_all_train(self, tmp_path: Path):
        samples = []
        for i in range(5):
            p = tmp_path / f"f{i}.wav"
            h = _make_wav(p)
            samples.append(SampleManifest(
                f"s{i}", "test", "d0", "audio", str(p), "bark", "bark", 1.0, "train", file_hash=h,
            ))
        split_manifest = SplitManifest(
            train=DatasetManifest(version="1.0.0", samples=samples),
            val=DatasetManifest(version="1.0.0", samples=[]),
            test=DatasetManifest(version="1.0.0", samples=[]),
        )
        report = detect_cross_split_leakage(split_manifest)
        assert report.has_issues is False


class TestDogLevelSplitNoLeakage:
    def test_same_dog_in_one_split(self, tmp_path: Path):
        samples = []
        for i in range(20):
            p = tmp_path / f"f{i}.wav"
            h = _make_wav(p)
            samples.append(SampleManifest(
                f"s{i}", "test", "dog_A", "audio", str(p), "bark", "bark", 1.0, "unassigned", file_hash=h,
            ))
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        split_manifest = split_dataset(manifest, seed=42, strategy="dog_level")

        dog_splits = {}
        for split_name, split_manifest_item in [
            ("train", split_manifest.train),
            ("val", split_manifest.val),
            ("test", split_manifest.test),
        ]:
            for s in split_manifest_item.samples:
                dog_splits.setdefault(s.dog_id, set()).add(split_name)

        for dog_id, splits in dog_splits.items():
            assert len(splits) == 1, f"Dog {dog_id} appears in multiple splits: {splits}"
        assert split_manifest.leakage_checks["has_leakage"] is False

    def test_multiple_dogs_each_in_single_split(self, tmp_path: Path):
        samples = []
        for i in range(20):
            p = tmp_path / f"f{i}.wav"
            h = _make_wav(p)
            samples.append(SampleManifest(
                f"s{i}", "test", f"dog_{i % 5}", "audio", str(p), "bark", "bark", 1.0, "unassigned", file_hash=h,
            ))
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        split_manifest = split_dataset(manifest, seed=42, strategy="dog_level")
        assert split_manifest.leakage_checks["has_leakage"] is False