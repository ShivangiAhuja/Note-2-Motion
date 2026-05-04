"""
Centralized configuration using Pydantic Settings.
All env vars flow through this single object.
"""

from typing import List
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Note2Motion"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/note2motion"

    # LLM provider selection (mock | groq | openai | anthropic)
    LLM_PROVIDER: str = "mock"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Pipeline
    MAX_NOTE_CHARS: int = 20000
    DEFAULT_LANGUAGES: str = "en,hi,hinglish"

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")

    @property
    def default_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.DEFAULT_LANGUAGES.split(",") if lang.strip()]


settings = Settings()