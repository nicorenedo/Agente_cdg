# backend/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ✅ Azure OpenAI (sin cambios)
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_ID: str
    AZURE_OPENAI_API_VERSION: str
    
    # 🔧 CORREGIDO: Ruta correcta a la base de datos
    DATABASE_PATH: str = str(Path(__file__).parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db")
    DATABASE_TIMEOUT: int = 30
    
    # ✅ Configuración del agente (sin cambios)
    DEFAULT_TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 2000
    MAX_RETRIES: int = 3
    
    # ✅ Logging (sin cambios)
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ✅ Umbrales críticos (sin cambios)
    UMBRAL_DESVIACION_CRITICA: float = 15.0
    UMBRAL_ROE_MINIMO: float = 8.0
    UMBRAL_MARGEN_NETO_MINIMO: float = 12.0
    
    # ✅ Nombres de tablas (sin cambios)
    TABLA_CONTRATOS: str = "MAESTRO_CONTRATOS"
    TABLA_MOVIMIENTOS: str = "MOVIMIENTOS_CONTRATOS"
    TABLA_PRECIO_REAL: str = "PRECIO_POR_PRODUCTO_REAL"
    TABLA_PRECIO_STD: str = "PRECIO_POR_PRODUCTO_STD"
    TABLA_GESTORES: str = "MAESTRO_GESTORES"
    
    # 🔧 CORREGIDO: Ruta al .env en el directorio padre de backend
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",  # Subir un nivel desde backend/
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
