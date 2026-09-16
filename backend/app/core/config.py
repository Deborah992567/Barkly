"""Application configuration loaded from environment variables.

Precedence: environment variables > backend/.env > defaults.
Defaults are only safe for development. Production requires an explicit
`JWT_SECRET`; startup fails fast otherwise rather than silently generating one.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BARKLY_",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "mysql+aiomysql://barkly:barkly@127.0.0.1:3306/barkly_dev"

    # --- Authentication / security ---
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    bcrypt_rounds: int = 12

    # --- CORS ---
    allowed_origins: list[str] = ["http://localhost:3000"]

    # --- AI provider ---
    ai_provider: str = "development-placeholder"

    # --- Phase 4 real-model inference configuration ---
    # Paths to the Phase 3 artifacts (see ml/model_registry.yaml for provenance).
    # Paths are resolved relative to the repository root when given as relative.
    ai_ml_package_path: str = "../ml/src"
    ai_model_registry_path: str = "../ml/model_registry.yaml"
    ai_audio_model_path: str = "ml/experiments/audio_cnn_v2/model.pt"
    ai_audio_config_path: str = "ml/configs/audio_cnn_v2.yaml"
    ai_vision_model_path: str = "ml/experiments/vision_baseline/model.pt"
    ai_vision_config_path: str = "ml/configs/vision_baseline.yaml"

    # Thresholds and system versions. These settings ARE the documentation of
    # the uncertainty policy; they are never silently overridden elsewhere.
    ai_audio_confidence_threshold: float = 0.30
    ai_vision_confidence_threshold: float = 0.50
    ai_audio_ood_threshold: float | None = None
    ai_fusion_version: str = "barkly-fusion-1.0.0"
    ai_interpretation_version: str = "barkly-interpretation-1.0.0"
    ai_inference_timeout_seconds: float = 60.0

    # Video sampling: frames evenly sampled across the clip are run through the
    # vision model and aggregated. 0 disables video frame extraction.
    ai_vision_frames: int = 3
    ai_vision_frame_ffmpeg_binary: str = "ffmpeg"

    # Fusion weights (documented in docs/multimodal-fusion.md).
    ai_fusion_audio_weight: float = 0.35
    ai_fusion_vision_weight: float = 0.45
    ai_fusion_context_weight: float = 0.20
    ai_fusion_contradiction_penalty: float = 0.25

    # --- Media ---
    media_storage_provider: str = "local"
    media_storage_root: str = "./media_storage"
    max_upload_size_bytes: int = 25_000_000
    media_retention_days: int = 30

    # --- Pagination ---
    default_page_size: int = 20
    max_page_size: int = 100

    # --- Product language ---
    disclaimer: str = (
        "BARKLY provides AI-based behavioral estimates from available signals and "
        "context. Results are not guaranteed interpretations and are not veterinary "
        "diagnoses."
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _validate_secret(self) -> "Settings":
        if self.environment == "prod" and len(self.jwt_secret) < 32:
            raise ValueError(
                "BARKLY_JWT_SECRET must be set to a value of at least 32 characters "
                "when ENVIRONMENT=production. Current value is empty or too short."
            )
        if self.environment == "prod" and "mysql+aiomysql" not in self.database_url:
            raise ValueError("Production configuration requires an explicit MariaDB DATABASE_URL.")
        return self

    @property
    def dev_secret(self) -> str:
        """Clearly labelled development-only secret."""
        return "development-only-insecure-secret-do-not-use-in-prod!"

    @property
    def effective_jwt_secret(self) -> str:
        if self.jwt_secret:
            return self.jwt_secret
        if self.environment == "dev":
            return self.dev_secret
        raise RuntimeError("JWT secret missing in a non-dev environment.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
