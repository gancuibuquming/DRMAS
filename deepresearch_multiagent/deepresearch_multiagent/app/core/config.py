from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DeepResearch Multi-Agent System"
    app_env: str = "dev"
    log_level: str = "INFO"
    checkpoint_dir: Path = Path("data/checkpoints")

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    llm_timeout_seconds: int = Field(default=60, alias="LLM_TIMEOUT_SECONDS")

    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    serpapi_api_key: Optional[str] = Field(default=None, alias="SERPAPI_API_KEY")
    search_timeout_seconds: int = Field(default=20, alias="SEARCH_TIMEOUT_SECONDS")
    max_search_results: int = Field(default=5, alias="MAX_SEARCH_RESULTS")

    @property
    def is_mock_llm(self) -> bool:
        return not bool(self.openai_api_key)

    @property
    def is_mock_search(self) -> bool:
        return not bool(self.tavily_api_key or self.serpapi_api_key)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return settings
