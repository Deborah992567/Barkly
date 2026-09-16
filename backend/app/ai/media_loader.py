"""Loading of stored media into paths the ML engines can consume.

Media stays inside the storage layer until this module resolves a reference to
a readable local path (already supported by LocalStorage.resolve()). Video clips
are sampled into a small set of evenly-spaced JPEG frames with ffmpeg.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.core.config import get_settings
from app.media.storage import StorageProvider

_AUDIO_TYPES = ("AUDIO", "audio", "WAV", "wav", "audio/mpeg", "audio/wav", "audio/x-wav")
_VIDEO_TYPES = ("VIDEO", "video", "MP4", "mp4", "video/mp4", "video/quicktime", "MOV", "mov")
_IMAGE_TYPES = ("IMAGE", "image", "JPG", "jpg", "JPEG", "jpeg", "PNG", "png")


def resolve_media(reference: str, storage: StorageProvider) -> Path | None:
    if not reference:
        return None
    return storage.resolve(reference)


def pick_media_reference(
    media_type: str, references: tuple[tuple[str, str], ...]
) -> str | None:
    """Return the first storage reference matching a media type.

    `references` is a tuple of (media_type, storage_reference).
    """
    for candidate_type, reference in references:
        if media_type.lower() in _AUDIO_TYPES and candidate_type in _AUDIO_TYPES:
            return reference
        if media_type.lower() in _VIDEO_TYPES and candidate_type in _VIDEO_TYPES:
            return reference
        if media_type.lower() in _IMAGE_TYPES and candidate_type in _IMAGE_TYPES:
            return reference
    return None


def sample_video_frames(video_path: Path, count: int) -> list[Path]:
    """Evenly sample `count` frames from a video clip into a temp directory."""
    if count <= 0:
        return []
    settings = get_settings()
    ffmpeg = settings.ai_vision_frame_ffmpeg_binary

    duration = _probe_duration(video_path, ffmpeg)
    if duration is None or duration <= 0.0:
        return _early_frames(video_path, count, ffmpeg)

    out_dir_parts: list[Path] = []
    for index in range(count):
        timestamp = (duration * index / max(count - 1, 1)) if count > 1 else 0.0
        out = Path(
            tempfile.mkdtemp(prefix="barkly_frame_") if not out_dir_parts else out_dir_parts[0]
        )
        if not out_dir_parts:
            out_dir_parts.append(out)
        frame_path = out / f"frame_{index}.jpg"
        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            "-y",
            str(frame_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        except (subprocess.CalledProcessError, OSError, TimeoutError):
            continue
    if not out_dir_parts:
        return []
    return sorted(out_dir_parts[0].glob("frame_*.jpg"))


def _probe_duration(video_path: Path, ffmpeg: str) -> float | None:
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-i",
                str(video_path),
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, TimeoutError):
        return None
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            token = line.split("Duration:")[1].split(",")[0].strip()
            try:
                parts = token.split(":")
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            except (IndexError, ValueError):
                return None
    return None


def _early_frames(video_path: Path, count: int, ffmpeg: str) -> list[Path]:
    out_dir = Path(tempfile.mkdtemp(prefix="barkly_frame_"))
    try:
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(video_path),
                "-frames:v",
                str(count),
                "-q:v",
                "2",
                "-y",
                str(out_dir / "frame_%d.jpg"),
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except (subprocess.CalledProcessError, OSError, TimeoutError):
        pass
    return sorted(out_dir.glob("frame_*.jpg"))
