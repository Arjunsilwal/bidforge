"""
API Configuration and Settings Management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "BidForge"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    # NOTE: v1 intentionally ships no authentication (deferred to v2 per the plan), so
    # there is no SECRET_KEY here. A signing key with an insecure default would imply a
    # protection the app does not actually provide. Reintroduce it with the auth layer.

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    # Browser origins permitted by CORS. Empty means "no cross-origin browser access",
    # which is the safe default — this is never widened to "*".
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8501,http://localhost:8000"

    DATABASE_URL: str = "sqlite:///./bidforge.db"  # Default local fallback; overrides with PostgreSQL in docker/prod

    FRED_API_KEY: str = ""
    FRED_SERIES_ID: str = "WPUSI012011"

    ANTHROPIC_API_KEY: str = ""
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    MODELS_DIR: str = "./models"
    DATA_RAW_DIR: str = "./data/raw"
    DATA_PROCESSED_DIR: str = "./data/processed"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
