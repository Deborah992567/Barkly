from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class AudioAugmentor:
    def __init__(self, seed: int | None = None):
        self.rng = np.random.RandomState(seed)

    def add_noise(
        self, signal: np.ndarray, noise_level: float = 0.005
    ) -> np.ndarray:
        noise = self.rng.randn(len(signal)) * noise_level
        return signal + noise

    def time_shift(
        self, signal: np.ndarray, shift_range: float = 0.2
    ) -> np.ndarray:
        max_shift = int(len(signal) * shift_range)
        shift = self.rng.randint(-max_shift, max_shift + 1)
        return np.roll(signal, shift)

    def pitch_shift(
        self, signal: np.ndarray, sr: int, n_steps: float = 2.0
    ) -> np.ndarray:
        import librosa

        steps = self.rng.uniform(-n_steps, n_steps)
        return librosa.effects.pitch_shift(y=signal, sr=sr, n_steps=steps)

    def time_stretch(
        self, signal: np.ndarray, rate_range: tuple[float, float] = (0.8, 1.2)
    ) -> np.ndarray:
        import librosa

        rate = self.rng.uniform(rate_range[0], rate_range[1])
        stretched = librosa.effects.time_stretch(signal, rate=rate)
        if len(stretched) > len(signal):
            stretched = stretched[: len(signal)]
        elif len(stretched) < len(signal):
            stretched = np.pad(stretched, (0, len(signal) - len(stretched)))
        return stretched

    def volume_scale(
        self, signal: np.ndarray, factor_range: tuple[float, float] = (0.7, 1.3)
    ) -> np.ndarray:
        factor = self.rng.uniform(factor_range[0], factor_range[1])
        return signal * factor

    def apply_spec_augment(
        self,
        mel_spec: np.ndarray,
        num_masks: int = 2,
        freq_mask_param: int = 10,
        time_mask_param: int = 20,
    ) -> np.ndarray:
        augmented = mel_spec.copy()
        n_freq, n_time = augmented.shape

        for _ in range(num_masks):
            # Frequency masking
            f = self.rng.randint(0, min(freq_mask_param, n_freq // 2) + 1)
            f0 = self.rng.randint(0, max(1, n_freq - f))
            augmented[f0 : f0 + f, :] = 0

            # Time masking
            t = self.rng.randint(0, min(time_mask_param, n_time // 2) + 1)
            t0 = self.rng.randint(0, max(1, n_time - t))
            augmented[:, t0 : t0 + t] = 0

        return augmented

    def augment_signal(
        self,
        signal: np.ndarray,
        sr: int = 22050,
        augmentations: list[str] | None = None,
    ) -> np.ndarray:
        if augmentations is None:
            augmentations = ["noise", "shift", "volume"]

        augmented = signal.copy()
        for aug_name in augmentations:
            if aug_name == "noise":
                augmented = self.add_noise(augmented)
            elif aug_name == "shift":
                augmented = self.time_shift(augmented)
            elif aug_name == "pitch":
                augmented = self.pitch_shift(augmented, sr)
            elif aug_name == "stretch":
                augmented = self.time_stretch(augmented)
            elif aug_name == "volume":
                augmented = self.volume_scale(augmented)
        return augmented
