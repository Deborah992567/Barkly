"""Tests for the data pipeline (manifest, validation, duplicates, splitting)."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from src.data.manifest import DatasetManifest, SampleManifest, _normalize_label, create_manifest
from src.data.leakage import detect_cross_split_leakage, detect_exact_duplicates
from src.data.splitter import SplitManifest, split_dataset
from src.data.validator import validate_audio_file, validate_dataset


def _make_wav(path: Path, data: np.ndarray | None = None, sr: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if data is None:
        data = (np.random.randn(sr).astype(np.float32) * 0.5 * 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())


class TestManifestCreation:
    def test_manifest_from_directory(self, tmp_audio_dir: Path):
        manifest = create_manifest(tmp_audio_dir, modality="audio")
        assert len(manifest.samples) == 15  # 3 label subdirs x 5 files
        for s in manifest.samples:
            assert s.path
            assert s.split == "unassigned"

    def test_manifest_populates_metadata(self, tmp_audio_dir: Path):
        manifest = create_manifest(tmp_audio_dir, modality="audio")
        assert manifest.metadata["audio_dir"] == str(tmp_audio_dir)

    def test_manifest_computes_file_hashes(self, tmp_audio_dir: Path):
        manifest = create_manifest(tmp_audio_dir, modality="audio")
        for s in manifest.samples:
            assert s.file_hash, f"Missing file hash for {s.sample_id}"

    def test_normalize_label(self):
        assert _normalize_label(" Bark ") == "bark"
        assert _normalize_label("Attention Seeking") == "attention_seeking"
        assert _normalize_label("playing-with-toy") == "playing_with_toy"


class TestManifestSaveLoad:
    def test_roundtrip_yaml(self, sample_manifest: DatasetManifest, tmp_path: Path):
        path = tmp_path / "manifest.yaml"
        sample_manifest.save_yaml(path)
        loaded = DatasetManifest.from_yaml(path)
        assert len(loaded) == len(sample_manifest)
        for orig, loaded_s in zip(sample_manifest.samples, loaded.samples):
            assert orig.sample_id == loaded_s.sample_id
            assert orig.normalized_label == loaded_s.normalized_label

    def test_integrity_check(self, sample_manifest: DatasetManifest):
        errors = sample_manifest.validate_integrity()
        assert errors == []


class TestValidatorCatchesMissingFiles:
    def test_missing_file_detected(self, tmp_path: Path):
        sample = SampleManifest(
            sample_id="missing_001",
            source="test",
            dog_id="dog_0",
            modality="audio",
            path=str(tmp_path / "nonexistent.wav"),
            label="bark",
            normalized_label="bark",
            duration=1.0,
            split="train",
        )
        manifest = DatasetManifest(version="1.0.0", samples=[sample])
        report = validate_dataset(manifest)
        assert sample.sample_id in report.missing_files
        assert report.invalid_samples == 1

    def test_validate_audio_file_missing(self, tmp_path: Path):
        assert validate_audio_file(tmp_path / "nope.wav") is False


class TestValidatorCatchesCorruptedFiles:
    def test_empty_file_detected(self, tmp_path: Path):
        empty_file = tmp_path / "empty.wav"
        empty_file.write_bytes(b"")
        assert validate_audio_file(empty_file) is False

        sample = SampleManifest(
            sample_id="corrupt_001",
            source="test",
            dog_id="dog_0",
            modality="audio",
            path=str(empty_file),
            label="bark",
            normalized_label="bark",
            duration=1.0,
            split="train",
        )
        manifest = DatasetManifest(version="1.0.0", samples=[sample])
        report = validate_dataset(manifest)
        assert sample.sample_id in report.corrupted_files


class TestDuplicateDetection:
    def test_exact_duplicates_found(self, tmp_path: Path):
        data = (np.random.randn(16000).astype(np.float32) * 0.5 * 32767).astype(np.int16)
        p1 = tmp_path / "a.wav"
        p2 = tmp_path / "b.wav"
        _make_wav(p1, data)
        _make_wav(p2, data)

        import hashlib

        h = hashlib.sha256(data.tobytes()).hexdigest()
        samples = [
            SampleManifest("s1", "test", "d1", "audio", str(p1), "bark", "bark", 1.0, "train", file_hash=h),
            SampleManifest("s2", "test", "d2", "audio", str(p2), "bark", "bark", 1.0, "test", file_hash=h),
        ]
        manifest = DatasetManifest(version="1.0.0", samples=samples)
        dupes = detect_exact_duplicates(manifest)
        assert len(dupes) == 1
        assert sorted(dupes[0]) == ["s1", "s2"]

    def test_no_duplicates(self, sample_manifest: DatasetManifest):
        dupes = detect_exact_duplicates(sample_manifest)
        assert len(dupes) == 0


class TestSplitLeakageDetection:
    def test_cross_split_leakage_detected(self, tmp_path: Path):
        data = (np.random.randn(16000).astype(np.float32) * 0.5 * 32767).astype(np.int16)
        import hashlib

        h = hashlib.sha256(data.tobytes()).hexdigest()
        p = tmp_path / "shared.wav"
        _make_wav(p, data)

        s1 = SampleManifest("s1", "test", "d1", "audio", str(p), "bark", "bark", 1.0, "train", file_hash=h)
        s2 = SampleManifest("s2", "test", "d2", "audio", str(p), "bark", "bark", 1.0, "test", file_hash=h)
        split_manifest = SplitManifest(
            train=DatasetManifest(version="1.0.0", samples=[s1]),
            val=DatasetManifest(version="1.0.0", samples=[]),
            test=DatasetManifest(version="1.0.0", samples=[s2]),
        )
        report = detect_cross_split_leakage(split_manifest)
        assert report.has_issues

    def test_no_leakage(self, sample_manifest: DatasetManifest):
        split_manifest = split_dataset(sample_manifest, strategy="dog_level", seed=42)
        report = detect_cross_split_leakage(split_manifest)
        assert report.has_issues is False


class TestClassDistribution:
    def test_distribution_counts(self, sample_manifest: DatasetManifest):
        stats = sample_manifest.get_statistics()
        assert stats["total_samples"] == 18
        for cls in ("bark", "whine", "growl"):
            assert stats["samples_per_class"][cls] == 6

    def test_split_distribution(self, sample_manifest: DatasetManifest):
        stats = sample_manifest.get_statistics()
        for sp in ("train", "val", "test"):
            assert stats["samples_per_split"][sp] == 6

    def test_single_dog_not_in_multiple_splits(self, sample_manifest: DatasetManifest):
        split_manifest = split_dataset(
            sample_manifest, strategy="dog_level", seed=42
        )
        dog_splits: dict[str, set[str]] = {}
        for manifest, split_name in [
            (split_manifest.train, "train"),
            (split_manifest.val, "val"),
            (split_manifest.test, "test"),
        ]:
            for s in manifest.samples:
                dog_splits.setdefault(s.dog_id, set()).add(split_name)
        for dog_id, splits in dog_splits.items():
            assert len(splits) == 1, f"Dog {dog_id} appears in multiple splits: {splits}"


class TestSplitDataset:
    def test_split_proportions(self, sample_manifest: DatasetManifest):
        split_manifest = split_dataset(
            sample_manifest, strategy="random", seed=42, train_ratio=0.6, val_ratio=0.2
        )
        n_train = len(split_manifest.train)
        n_val = len(split_manifest.val)
        n_test = len(split_manifest.test)
        assert n_train > 0 and n_val > 0 and n_test > 0
        assert n_train + n_val + n_test == len(sample_manifest)

    def test_strategy_bad(self, sample_manifest: DatasetManifest):
        with pytest.raises(ValueError):
            split_dataset(sample_manifest, strategy="bogus")