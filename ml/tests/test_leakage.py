"""Tests for data leakage detection."""

from __future__ import annotations

import hashlib
import wave
from pathlib import Path

import numpy as np
import pytest

from src.data.manifest import DatasetManifest, SampleManifest
from scripts.prepare_dataset import (
    detect_cross_split_leakage,
    detect_duplicates,
    split_dataset,
)


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
        dupes = detect_duplicates(manifest)
        assert len(dupes) == 1
        assert len(list(dupes.values())[0]) == 2

    def test_no_duplicates_unique_files(self, tmp_path: Path):
        samples = []
        for i in range(5):
            p = tmp_path / f"f{i}.wav"
            h = _make_wav(p)
            samples.append(SampleManifest(
                f"s{i}", "test", "d0", "audio", str(p), "bark", "bark", 1.0, "train", file_hash=h,
            ))
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        dupes = detect_duplicates(manifest)
        assert len(dupes) == 0


class TestCrossSplitLeakage:
    def test_same_file_in_train_and_test(self, tmp_path: Path):
        data = np.random.randn(16000).astype(np.float32) * 0.5
        h = _make_wav(tmp_path / "shared.wav", data=data)

        samples = [
            SampleManifest("s1", "test", "d1", "audio", str(tmp_path / "shared.wav"), "bark", "bark", 1.0, "train", file_hash=h),
            SampleManifest("s2", "test", "d2", "audio", str(tmp_path / "shared.wav"), "bark", "bark", 1.0, "test", file_hash=h),
        ]
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        leaks = detect_cross_split_leakage(manifest)
        assert len(leaks) == 1
        assert ("train", "test") == tuple(sorted([leaks[0][2], leaks[0][3]]))

    def test_no_leakage_when_all_train(self, tmp_path: Path):
        samples = []
        for i in range(5):
            p = tmp_path / f"f{i}.wav"
            h = _make_wav(p)
            samples.append(SampleManifest(
                f"s{i}", "test", "d0", "audio", str(p), "bark", "bark", 1.0, "train", file_hash=h,
            ))
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        leaks = detect_cross_split_leakage(manifest)
        assert len(leaks) == 0


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
        split_manifest = split_dataset(manifest, seed=42, stratify_by="dog_id")

        dog_splits = {}
        for s in split_manifest.samples:
            dog_splits.setdefault(s.dog_id, set()).add(s.split)

        for dog_id, splits in dog_splits.items():
            assert len(splits) == 1, f"Dog {dog_id} appears in multiple splits: {splits}"
