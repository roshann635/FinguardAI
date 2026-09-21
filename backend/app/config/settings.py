from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://finguard:finguard@localhost:5432/finguard_db"
    gemini_api_key: str = ""
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    environment: str = "development"
    debug: bool = False
    app_name: str = "FinGuard AI"
    app_version: str = "1.0.0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return settings
