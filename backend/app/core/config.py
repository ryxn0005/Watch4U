"""Centralised settings loaded from environment variables / .env."""
import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    cors_origins: str = "http://localhost:8501,http://localhost:3000"

    def cors_allow_origins(self) -> list[str]:
        s = self.cors_origins.strip()
        if not s:
            return []
        if s.startswith("["):
            data = json.loads(s)
            if not isinstance(data, list):
                raise ValueError("CORS_ORIGINS must be a comma-separated list or a JSON array")
            return [str(x).strip() for x in data if str(x).strip()]
        return [x.strip() for x in s.split(",") if x.strip()]

    # LLM / RAG
    llm_provider: str = "ollama"
    llm_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1"
    vector_db_url: str = ""

    # Data
    data_dir: str = "/data"

    surreal_url: str = ""
    surreal_username: str = "root"
    surreal_password: str = "root"
    surreal_namespace: str = "watch4u"
    surreal_database: str = "main"
    surreal_apply_schema_on_startup: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
