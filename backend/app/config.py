from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    api_key_id: str
    private_key: str
    kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    database_url: str = "sqlite+aiosqlite:///./kalshi_dashboard.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
