from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings parsed from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    PORT: int = 8000

    # Supabase PostgreSQL connection string
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/edtech_crm?sslmode=prefer"
    DB_POOL_MIN_SIZE: int = 1
    DB_POOL_MAX_SIZE: int = 10

    # JWT Authentication configuration
    JWT_SECRET: str = "dev-insecure-secret-key-change-this-in-production-1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # CORS configuration
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Optional provisioning variables for scripts/create_admin.py
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
