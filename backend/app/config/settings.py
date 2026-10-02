from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentic Returns Exception Decision Assistant"
    environment: str = "development"
    api_prefix: str = "/api"
    secret_key: str = ""
    database_url: str = "sqlite:///./data/agentic_returns.db"
    redis_url: str = ""
    chroma_host: str = ""
    chroma_port: int = 8000
    chroma_persist_directory: str = "./data/chroma"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "agentic-returns"
    cors_origins: str = "http://localhost:3000"
    max_upload_bytes: int = 2_000_000
    confidence_threshold: float = 0.7
    max_workflow_retries: int = 2

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
