# backend/src/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_ID: str
    AZURE_OPENAI_API_VERSION: str

    # Configuración de cómo cargar .env y qué hacer con variables extra
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",          # <-- aquí ignoramos las vars que no estén definidas
    )

settings = Settings()
