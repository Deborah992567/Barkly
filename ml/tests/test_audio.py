"""Tests for the audio preprocessing pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch


class TestPreprocessingShapes:
    def test_output_is_tensor(self, tmp_audio_dir: Path):
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        assert len(audio_files) > 0
        waveform = preprocess_audio(str(audio_files[0]), target_sr=16000, target_duration=1.0)
        assert isinstance(waveform, np.ndarray) or isinstance(waveform, torch.Tensor)

    def test_target_duration_respected(self, tmp_audio_dir: Path):
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(str(audio_files[0]), target_sr=16000, target_duration=2.0)
        expected_samples = 16000 * 2
        assert len(waveform) == expected_samples

    def test_different_sample_rates(self, tmp_audio_dir: Path):
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        w1 = preprocess_audio(str(audio_files[0]), target_sr=8000, target_duration=1.0)
        w2 = preprocess_audio(str(audio_files[0]), target_sr=22050, target_duration=1.0)
        assert len(w1) == 8000
        assert len(w2) == 22050


class TestFeatureExtractionShapes:
    def test_mfcc_shape(self, tmp_audio_dir: Path):
        from src.audio.feature_extractor import extract_features
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(str(audio_files[0]), target_sr=16000, target_duration=1.0)
        config = {"features": ["mfcc"], "n_mfcc": 13, "n_mels": 64, "sample_rate": 16000}
        features = extract_features(waveform, 16000, config)
        assert isinstance(features, np.ndarray)
        assert features.ndim == 1

    def test_combined_features(self, tmp_audio_dir: Path):
        from src.audio.feature_extractor import extract_features
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(str(audio_files[0]), target_sr=16000, target_duration=1.0)
        config = {"features": ["mfcc", "mel_spectrogram", "spectral"], "n_mfcc": 13, "n_mels": 64, "sample_rate": 16000}
        features = extract_features(waveform, 16000, config)
        assert features.ndim == 1
        assert len(features) > 13  # more than just MFCCs


class TestAugmentationDoesNotCrash:
    def test_augment_preserves_type(self, tmp_audio_dir: Path):
        from src.audio.augment import augment_audio
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(str(audio_files[0]), target_sr=16000, target_duration=1.0)
        augmented = augment_audio(waveform, sr=16000)
        assert isinstance(augmented, np.ndarray) or isinstance(augmented, torch.Tensor)

    def test_augment_multiple_times(self, tmp_audio_dir: Path):
        from src.audio.augment import augment_audio
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(str(audio_files[0]), target_sr=16000, target_duration=1.0)
        for _ in range(5):
            augmented = augment_audio(waveform, sr=16000)
            assert len(augmented) > 0


class TestAugmentationPreservesLength:
    def test_length_unchanged(self, tmp_audio_dir: Path):
        from src.audio.augment import augment_audio
        from src.audio.preprocessor import preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(str(audio_files[0]), target_sr=16000, target_duration=1.0)
        original_len = len(waveform)
        augmented = augment_audio(waveform, sr=16000)
        assert len(augmented) == original_len
