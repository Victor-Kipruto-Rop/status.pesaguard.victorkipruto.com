"""
Application configuration.

All settings are read from environment variables (see .env.example at the
repo root). Nothing here should be hardcoded for a specific environment —
docker-compose, CI, and production should all just set different env vars.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_name: str = "PesaGuard Status API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- CORS ---
    # Comma-separated origins in the env var, e.g.
    # CORS_ORIGINS=https://status.pesaguard.victorkipruto.com,http://localhost:5500
    cors_origins: str = "*"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://pesaguard:pesaguard@localhost:5432/pesaguard_status"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 15

    # --- Uptime aggregation ---
    uptime_history_days: int = 90

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
