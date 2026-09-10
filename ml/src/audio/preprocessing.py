from __future__ import annotations

import numpy as np
from dataclasses import dataclass


@dataclass
class AudioPreprocessor:
    target_sr: int = 22050
    target_duration: float = 3.0
    normalize: bool = True
    mono: bool = True

    @property
    def target_length(self) -> int:
        return int(self.target_sr * self.target_duration)


def preprocess_audio(
    path: str,
    preprocessor: AudioPreprocessor | None = None,
) -> np.ndarray:
    import librosa
    import soundfile as sf

    if preprocessor is None:
        preprocessor = AudioPreprocessor()

    y, sr = librosa.load(
        path,
        sr=preprocessor.target_sr,
        mono=preprocessor.mono,
    )

    y = pad_or_truncate(y, preprocessor.target_length)

    if preprocessor.normalize:
        max_val = np.max(np.abs(y))
        if max_val > 0:
            y = y / max_val

    return y


def segment_audio(
    audio: np.ndarray,
    sr: int,
    segment_length: int,
    hop_length: int | None = None,
) -> list[np.ndarray]:
    if hop_length is None:
        hop_length = segment_length

    segments: list[np.ndarray] = []
    start = 0
    while start + segment_length <= len(audio):
        segments.append(audio[start : start + segment_length])
        start += hop_length

    if not segments and len(audio) > 0:
        padded = np.zeros(segment_length)
        padded[: min(len(audio), segment_length)] = audio[: min(len(audio), segment_length)]
        segments.append(padded)

    return segments


def pad_or_truncate(audio: np.ndarray, target_length: int) -> np.ndarray:
    if len(audio) > target_length:
        return audio[:target_length]
    elif len(audio) < target_length:
        padded = np.zeros(target_length, dtype=audio.dtype)
        padded[: len(audio)] = audio
        return padded
    return audio
