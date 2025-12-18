from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Kalshi API
    api_key_id: str
    private_key: str
    kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./kalshi_dashboard.db"
    
    # Fal AI (OpenRouter for Claude Sonnet 4.5)
    fal_key: Optional[str] = None
    fal_model: str = "anthropic/claude-sonnet-4.5"
    
    # FinancialDatasets.ai
    fin_dataset_key: Optional[str] = None
    
    # Daytona Sandbox (optional - for code execution)
    daytona_api_key: Optional[str] = None
    daytona_server_url: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
