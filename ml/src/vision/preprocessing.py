from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class ImagePreprocessor:
    image_size: tuple[int, int] = (224, 224)
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)
    normalize_pixels: bool = True

    def resize(self, image: Image.Image, size: tuple[int, int]) -> Image.Image:
        return image.resize(size, Image.Resampling.BILINEAR)

    def normalize(
        self,
        array: np.ndarray,
        mean: tuple[float, float, float] | None = None,
        std: tuple[float, float, float] | None = None,
    ) -> np.ndarray:
        mean = mean or self.mean
        std = std or self.std
        arr = array.copy().astype(np.float32)
        if arr.max() > 1.0:
            arr = arr / 255.0
        mean_arr = np.array(mean, dtype=np.float32).reshape(3, 1, 1)
        std_arr = np.array(std, dtype=np.float32).reshape(3, 1, 1)
        return (arr - mean_arr) / std_arr

    def validate_image(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists() or not path.is_file():
            return False
        try:
            with Image.open(path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def preprocess_image(self, path: str | Path) -> "torch.Tensor":
        import torch

        path = Path(path)
        if not self.validate_image(path):
            raise FileNotFoundError(f"Invalid or unreadable image: {path}")

        with Image.open(path) as img:
            img = img.convert("RGB")
            img = self.resize(img, self.image_size)

        arr = np.array(img).astype(np.float32)
        arr = arr.transpose(2, 0, 1)

        if self.normalize_pixels:
            arr = self.normalize(arr)

        return torch.from_numpy(arr)