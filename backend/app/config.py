"""
ClearMind Configuration Module

Manages all environment variables and application settings using pydantic-settings.
Provides type-safe access to configuration values with sensible defaults.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Google Gemini ---
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 4096

    # --- Database ---
    database_url: str = "postgresql+asyncpg://clearmind:clearmind_secret@localhost:5432/clearmind_db"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- MLflow ---
    mlflow_tracking_uri: str = "http://localhost:5000"

    # --- API Security ---
    api_secret_key: str = "dev-secret-key-change-in-production"

    # --- Model Paths ---
    bias_classifier_path: str = "ml_models/bias_classifier"
    calibration_model_path: str = "ml_models/calibration"

    # --- Application ---
    app_name: str = "ClearMind"
    app_version: str = "1.0.0"
    debug: bool = True
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @property
    def base_dir(self) -> Path:
        """Return the base directory of the backend application."""
        return Path(__file__).parent.parent

    @property
    def ml_models_dir(self) -> Path:
        """Return the path to ML models directory."""
        return self.base_dir / self.bias_classifier_path

    @property
    def calibration_dir(self) -> Path:
        """Return the path to calibration models directory."""
        return self.base_dir / self.calibration_model_path


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance. Use dependency injection in FastAPI routes."""
    return Settings()
