"""Shared test fixtures for BARKLY ML tests."""

from __future__ import annotations

import random
import struct
import wave
from pathlib import Path

import numpy as np
import pytest
import yaml

from src.data.manifest import DatasetManifest, SampleManifest


@pytest.fixture(autouse=True)
def _set_seeds():
    random.seed(42)
    np.random.seed(42)
    try:
        import torch
        torch.manual_seed(42)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(42)
    except ImportError:
        pass


@pytest.fixture
def tmp_audio_dir(tmp_path: Path) -> Path:
    """Create a temp directory with synthetic WAV files organized by label."""
    audio_dir = tmp_path / "audio_data"
    audio_dir.mkdir()
    sr = 16000
    duration_samples = sr  # 1 second

    labels = ["bark", "whine", "growl"]
    for label in labels:
        label_dir = audio_dir / label
        label_dir.mkdir()
        for i in range(5):
            fname = label_dir / f"{label}_{i:03d}.wav"
            samples = np.random.randn(duration_samples).astype(np.float32) * 0.5
            with wave.open(str(fname), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes((samples * 32767).astype(np.int16).tobytes())
    return audio_dir


@pytest.fixture
def tmp_image_dir(tmp_path: Path) -> Path:
    """Create a temp directory with synthetic images organized by label."""
    from PIL import Image

    image_dir = tmp_path / "image_data"
    image_dir.mkdir()
    labels = ["sitting", "standing", "lying_down"]

    for label in labels:
        label_dir = image_dir / label
        label_dir.mkdir()
        for i in range(5):
            fname = label_dir / f"{label}_{i:03d}.png"
            arr = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
            Image.fromarray(arr).save(fname)
    return image_dir


@pytest.fixture
def sample_manifest(tmp_path: Path) -> DatasetManifest:
    """Create a small test manifest with 18 samples (3 classes x 3 splits x 2)."""
    samples = []
    labels = ["bark", "whine", "growl"]
    splits = ["train", "val", "test"]

    idx = 0
    for label in labels:
        for split in splits:
            for j in range(2):
                p = tmp_path / "data" / f"{label}_{split}_{j:03d}.wav"
                p.parent.mkdir(parents=True, exist_ok=True)
                sr = 16000
                with wave.open(str(p), "w") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sr)
                    data = np.random.randn(sr).astype(np.float32) * 0.5
                    wf.writeframes((data * 32767).astype(np.int16).tobytes())
                samples.append(SampleManifest(
                    sample_id=f"s_{idx:04d}",
                    source="test_source",
                    dog_id=f"dog_{j}",
                    modality="audio",
                    path=str(p),
                    label=label,
                    normalized_label=label,
                    duration=1.0,
                    split=split,
                ))
                idx += 1

    return DatasetManifest(version="1.0.0", samples=samples, metadata={"test": True})
