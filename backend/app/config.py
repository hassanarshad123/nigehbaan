"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central settings for the Nigehbaan backend.

    All values can be overridden via environment variables or a ``.env`` file
    located in the project root.
    """

    database_url: str = "postgresql+asyncpg://localhost/nigehbaan"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    cors_origins: str = "http://localhost:3000"
    s3_bucket: str = "nigehbaan-data"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    mapbox_token: str = ""

    # AI extraction settings (OpenAI-compatible: works with OpenRouter, etc.)
    openai_api_key: str = ""
    openai_api_base: str = ""  # e.g. "https://openrouter.ai/api/v1"
    openai_model: str = "gpt-4o-mini"
    openai_max_concurrent: int = 5

    # Firecrawl settings (self-hosted)
    firecrawl_api_url: str = ""  # e.g. "http://72.61.124.88:3002"
    firecrawl_api_key: str = ""

    # External Neon DB for court judgment import (READ ONLY)
    external_judgments_db_url: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a list, splitting on commas."""
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
