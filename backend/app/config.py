from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LLM_API_BASE: str = "http://localhost:1234/v1"
    LLM_API_KEY: str = "not-needed"
    LLM_MODEL: str = "qwen/qwen3.5-35b-a3b"
    LLM_MAX_TOKENS: int = 32768

    SEARXNG_URL: str = ""

    DATABASE_PATH: str = str(PROJECT_ROOT / "data.db")
    DEV_MODE: bool = True


settings = Settings()
