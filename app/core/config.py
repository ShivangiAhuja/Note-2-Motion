"""
Centralized configuration using Pydantic Settings.
All env vars flow through this single object.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Note2Motion"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/note2motion"

    # LLM
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Pipeline
    MAX_NOTE_CHARS: int = 20000
    DEFAULT_LANGUAGES: str = "en,hi,hinglish"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def default_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.DEFAULT_LANGUAGES.split(",") if lang.strip()]


settings = Settings()