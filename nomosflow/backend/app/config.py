from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    environment: str = "development"
    api_key: Optional[str] = None  # Set to enforce bearer-token auth on all /api/* routes

    # Gemini quota guard
    gemini_limit_enabled: bool = True   # set to false to disable the guard entirely
    gemini_daily_limit: int = 100       # max AI calls per window
    gemini_window_hours: int = 24       # rolling window length in hours

    class Config:
        env_file = ".env"


settings = Settings()
