from __future__ import annotations

from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class AudioCNNConfig:
    n_mels: int = 128
    n_mfcc: int = 13
    n_mels_feature: int = 128
    conv_channels: list[int] = field(default_factory=lambda: [32, 64, 128])
    fc_dims: list[int] = field(default_factory=lambda: [256, 128])
    dropout: float = 0.3
    num_classes: int = 2
    kernel_size: int = 3
    pooling: str = "adaptive"


class AudioCNN(nn.Module):
    def __init__(self, config: AudioCNNConfig | None = None):
        super().__init__()
        if config is None:
            config = AudioCNNConfig()
        self.config = config

        conv_layers: list[nn.Module] = []
        in_channels = 1
        for channels in config.conv_channels:
            conv_layers.append(
                nn.Conv2d(in_channels, channels, kernel_size=config.kernel_size, padding=1)
            )
            conv_layers.append(nn.BatchNorm2d(channels))
            conv_layers.append(nn.ReLU(inplace=True))
            conv_layers.append(nn.MaxPool2d(kernel_size=2, stride=2))
            in_channels = channels
        self.conv_stack = nn.Sequential(*conv_layers)

        self.adaptive_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.flatten = nn.Flatten()

        n_features = config.conv_channels[-1]
        fc_layers: list[nn.Module] = []
        for dim in config.fc_dims:
            fc_layers.append(nn.Linear(n_features, dim))
            fc_layers.append(nn.ReLU(inplace=True))
            fc_layers.append(nn.Dropout(config.dropout))
            n_features = dim
        self.fc_stack = nn.Sequential(*fc_layers)

        self.classifier = nn.Linear(n_features, config.num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, 1, n_mels, time_steps)
        if x.dim() == 3:
            x = x.unsqueeze(1)
        x = self.conv_stack(x)
        x = self.adaptive_pool(x)
        x = self.flatten(x)
        x = self.fc_stack(x)
        return self.classifier(x)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def model_size_mb(model: nn.Module) -> float:
    total_bytes = 0
    for p in model.parameters():
        total_bytes += p.numel() * p.element_size()
    buffer_bytes = sum(b.numel() * b.element_size() for b in model.buffers())
    return (total_bytes + buffer_bytes) / (1024 * 1024)