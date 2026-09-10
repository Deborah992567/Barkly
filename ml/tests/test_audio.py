"""Tests for the audio preprocessing pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


class TestPreprocessingShapes:
    def test_output_is_ndarray(self, tmp_audio_dir: Path):
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        assert len(audio_files) > 0
        waveform = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=16000, target_duration=1.0),
        )
        assert isinstance(waveform, np.ndarray)
        assert waveform.ndim == 1

    def test_target_duration_respected(self, tmp_audio_dir: Path):
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=16000, target_duration=2.0),
        )
        expected_samples = 16000 * 2
        assert len(waveform) == expected_samples

    def test_different_sample_rates(self, tmp_audio_dir: Path):
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        w1 = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=8000, target_duration=1.0),
        )
        w2 = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=22050, target_duration=1.0),
        )
        assert len(w1) == 8000
        assert len(w2) == 22050


class TestFeatureExtractionShapes:
    def test_mfcc_shape(self, tmp_audio_dir: Path):
        from src.audio.features import AudioFeatureExtractor, FeatureConfig
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=16000, target_duration=1.0),
        )
        extractor = AudioFeatureExtractor(
            FeatureConfig(
                sample_rate=16000,
                n_mfcc=13,
                n_mels=64,
                use_mfcc=True,
                use_mel_spectrogram=False,
                use_spectral=False,
            )
        )
        mfcc = extractor.extract_mfcc(waveform, sr=16000)
        assert isinstance(mfcc, np.ndarray)
        assert mfcc.shape[0] == 13

    def test_combined_features(self, tmp_audio_dir: Path):
        from src.audio.features import AudioFeatureExtractor, FeatureConfig
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=16000, target_duration=1.0),
        )
        extractor = AudioFeatureExtractor(
            FeatureConfig(
                sample_rate=16000,
                n_mfcc=13,
                n_mels=64,
                use_mfcc=True,
                use_mel_spectrogram=True,
                use_spectral=True,
            )
        )
        all_features = extractor.extract_all(waveform, sr=16000)
        flat = extractor.flatten_features(all_features)
        assert flat.ndim == 1
        assert len(flat) > 13  # more than just MFCCs


class TestAugmentationDoesNotCrash:
    def test_augment_preserves_type(self, tmp_audio_dir: Path):
        from src.audio.augmentation import AudioAugmentor
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=16000, target_duration=1.0),
        )
        augmentor = AudioAugmentor(seed=42)
        augmented = augmentor.augment_signal(waveform, sr=16000)
        assert isinstance(augmented, np.ndarray)

    def test_augment_multiple_times(self, tmp_audio_dir: Path):
        from src.audio.augmentation import AudioAugmentor
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=16000, target_duration=1.0),
        )
        augmentor = AudioAugmentor(seed=42)
        for _ in range(5):
            augmented = augmentor.augment_signal(waveform, sr=16000)
            assert len(augmented) == len(waveform)


class TestAugmentationPreservesLength:
    def test_length_unchanged(self, tmp_audio_dir: Path):
        from src.audio.augmentation import AudioAugmentor
        from src.audio.preprocessing import AudioPreprocessor, preprocess_audio

        audio_files = list(tmp_audio_dir.rglob("*.wav"))
        waveform = preprocess_audio(
            str(audio_files[0]),
            AudioPreprocessor(target_sr=16000, target_duration=1.0),
        )
        augmentor = AudioAugmentor(seed=42)
        original_len = len(waveform)
        augmented = augmentor.augment_signal(waveform, sr=16000)
        assert len(augmented) == original_len