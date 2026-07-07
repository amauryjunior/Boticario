"""Configuração central da aplicação (12-factor via variáveis de ambiente)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Inclua Beauty AI"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./incluabeauty.db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    # "heuristic" (default, offline) | "adk" (Gemini/Vertex AI)
    analysis_engine: str = "heuristic"

    google_genai_use_vertexai: str = "FALSE"
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    google_api_key: str = ""
    model_fast: str = "gemini-2.5-flash"
    model_pro: str = "gemini-2.5-pro"

    seed_demo: bool = True
    demo_email: str = "demo@incluabeauty.ai"
    demo_password: str = "demo1234"


settings = Settings()
