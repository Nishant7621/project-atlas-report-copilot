"""
Configuration settings for Project Atlas.
Loads settings from environment variables with sensible defaults and fallback options.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_KEY: str = os.getenv("ATLAS_API_KEY", "atlas_secret_key_12345")
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

    # Database Configuration (MySQL in Docker, SQLite fallback for local test)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'atlas.db'}"
    )
    READONLY_DATABASE_URL: str = os.getenv(
        "READONLY_DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'atlas.db'}"
    )

    # LLM Settings (OpenAI, Gemini, Claude, or local Ollama)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # 'gemini', 'openai', 'anthropic', 'ollama'
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Confidence threshold for human escalation
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

    # Vector store paths
    REPORTS_DIR: Path = BASE_DIR / "data" / "reports"
    VECTOR_DB_DIR: Path = BASE_DIR / "data" / "vector_db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
