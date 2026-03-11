from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Gen-Friend"
    debug: bool = False
    environment: str = "development"  # development | staging | production

    # Database
    database_url: str = "sqlite+aiosqlite:///./genfriend.db"
    auto_create_tables: bool = True
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # Provider selection
    stt_provider: str = "groq"
    llm_provider: str = "groq"
    tts_provider: str = "openai"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    clerk_secret_key: Optional[str] = None
    clerk_publishable_key: Optional[str] = None

    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    enable_cost_tracking: bool = True

    @property
    def pgvector_available(self) -> bool:
        try:
            from pgvector.sqlalchemy import Vector  # noqa: F401
            return "postgresql" in self.database_url
        except ImportError:
            return False

    enable_advanced_rag: bool = False
    log_level: str = "INFO"

    # Production settings
    allowed_origins: str = "http://localhost:3002,http://127.0.0.1:3002"
    admin_secret_key: str = "dev-admin-secret"

    # Backup settings
    backup_enabled: bool = False
    backup_path: str = "./backups"
    backup_retention_days: int = 30

    @model_validator(mode="after")
    def _validate_production_secrets(self):
        if self.environment == "production":
            if self.jwt_secret == "change-me-in-production":
                raise ValueError("jwt_secret must be set in production (not the default)")
            if self.admin_secret_key == "dev-admin-secret":
                raise ValueError("admin_secret_key must be set in production (not the default)")
            if self.auto_create_tables:
                raise ValueError("auto_create_tables must be False in production — use migrations")
            if self.debug:
                raise ValueError("debug must be False in production")
            if not self.clerk_secret_key:
                raise ValueError("clerk_secret_key is required in production")
            if not self.anthropic_api_key and not self.openai_api_key and not self.groq_api_key:
                raise ValueError("At least one LLM API key must be set in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
