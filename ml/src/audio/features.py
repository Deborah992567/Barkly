from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class FeatureConfig:
    n_mfcc: int = 13
    n_mels: int = 128
    hop_length: int = 512
    n_fft: int = 2048
    sample_rate: int = 22050
    use_mfcc: bool = True
    use_mel_spectrogram: bool = True
    use_spectral: bool = True


class AudioFeatureExtractor:
    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()

    def extract_mfcc(
        self, audio: np.ndarray, sr: int | None = None, n_mfcc: int | None = None
    ) -> np.ndarray:
        import librosa

        sr = sr or self.config.sample_rate
        n_mfcc = n_mfcc or self.config.n_mfcc
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=sr,
            n_mfcc=n_mfcc,
            hop_length=self.config.hop_length,
            n_fft=self.config.n_fft,
        )
        return mfcc

    def extract_mel_spectrogram(
        self, audio: np.ndarray, sr: int | None = None, n_mels: int | None = None
    ) -> np.ndarray:
        import librosa

        sr = sr or self.config.sample_rate
        n_mels = n_mels or self.config.n_mels
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=sr,
            n_mels=n_mels,
            hop_length=self.config.hop_length,
            n_fft=self.config.n_fft,
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        return mel_spec_db

    def extract_spectral_features(
        self, audio: np.ndarray, sr: int | None = None
    ) -> dict[str, float]:
        import librosa

        sr = sr or self.config.sample_rate

        centroid = librosa.feature.spectral_centroid(
            y=audio, sr=sr, hop_length=self.config.hop_length
        )
        bandwidth = librosa.feature.spectral_bandwidth(
            y=audio, sr=sr, hop_length=self.config.hop_length
        )
        rolloff = librosa.feature.spectral_rolloff(
            y=audio, sr=sr, hop_length=self.config.hop_length
        )
        zcr = librosa.feature.zero_crossing_rate(
            y=audio, hop_length=self.config.hop_length
        )
        rms = librosa.feature.rms(
            y=audio, hop_length=self.config.hop_length
        )

        return {
            "spectral_centroid_mean": float(np.mean(centroid)),
            "spectral_centroid_std": float(np.std(centroid)),
            "spectral_bandwidth_mean": float(np.mean(bandwidth)),
            "spectral_bandwidth_std": float(np.std(bandwidth)),
            "spectral_rolloff_mean": float(np.mean(rolloff)),
            "spectral_rolloff_std": float(np.std(rolloff)),
            "zcr_mean": float(np.mean(zcr)),
            "zcr_std": float(np.std(zcr)),
            "rms_mean": float(np.mean(rms)),
            "rms_std": float(np.std(rms)),
        }

    def extract_all(
        self, audio: np.ndarray, sr: int | None = None
    ) -> dict[str, np.ndarray | float]:
        sr = sr or self.config.sample_rate
        features: dict[str, np.ndarray | float] = {}

        if self.config.use_mfcc:
            features["mfcc"] = self.extract_mfcc(audio, sr)

        if self.config.use_mel_spectrogram:
            features["mel_spectrogram"] = self.extract_mel_spectrogram(audio, sr)

        if self.config.use_spectral:
            spectral = self.extract_spectral_features(audio, sr)
            features.update(spectral)

        return features

    def flatten_features(self, features: dict[str, np.ndarray | float]) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for key, val in sorted(features.items()):
            if isinstance(val, np.ndarray):
                vectors.append(val.flatten())
            else:
                vectors.append(np.array([val]))
        return np.concatenate(vectors)
