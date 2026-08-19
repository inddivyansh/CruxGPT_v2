"""
Centralized application configuration.

Everything is read from environment variables (see .env.example). Nothing
secret ever gets hard-coded here, and nothing here is ever exposed to the
frontend directly - the frontend only ever talks to our own API.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/crux.db"

    # Auth
    jwt_secret: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # LLM / Embeddings
    gemini_api_key: str = ""
    gemini_llm_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "models/text-embedding-004"

    # Storage
    storage_path: str = "./uploads"
    max_file_size_mb: int = 10

    # Chunking
    chunk_size_chars: int = 3000
    chunk_overlap_chars: int = 400

    # Retrieval
    retrieval_top_k: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
