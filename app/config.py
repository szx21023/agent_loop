"""Application settings, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    model: str = "claude-opus-4-8"
    max_loop_steps: int = 6
    log_level: str = "INFO"
    index_path: str = "data/index.json"

    @property
    def is_offline(self) -> bool:
        """True when no API key is set — the agent runs in fallback mode."""
        return not self.anthropic_api_key.strip()


@lru_cache
def get_settings() -> Settings:
    """Settings 單例；透過快取避免重複讀取 .env。"""
    return Settings()


settings = get_settings()
