# backend/config.py
"""
Configuración centralizada para el proyecto CDG Agent
=====================================================

Configuración basada en variables de entorno con soporte para Azure OpenAI
y integración completa con el sistema de Control de Gestión.

Versión: 2.0 - Compatible con Pydantic v2
"""

import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_V2 = True
except ImportError:
    try:
        from pydantic import BaseSettings
        PYDANTIC_V2 = False
    except ImportError:
        # Fallback manual para entornos sin pydantic
        class BaseSettings:
            pass
        PYDANTIC_V2 = False


class Settings(BaseSettings):
    """
    Configuración principal del sistema CDG Agent
    
    Todas las variables sensibles se cargan desde .env
    """
    
    # ✅ Azure OpenAI - Variables exactas del .env
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str  
    AZURE_OPENAI_DEPLOYMENT_ID: str
    AZURE_OPENAI_API_VERSION: str
    
    # 🗄️ Base de datos - Ruta dinámica calculada
    DATABASE_PATH: str = str(Path(__file__).parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db")
    DATABASE_TIMEOUT: int = 30
    
    # 🤖 Configuración del agente LLM
    DEFAULT_TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 2000
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 30
    
    # 📊 Logging
    LOG_LEVEL: str = "INFO" 
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 🎯 Umbrales de negocio críticos
    UMBRAL_DESVIACION_CRITICA: float = 15.0
    UMBRAL_ROE_MINIMO: float = 8.0
    UMBRAL_MARGEN_NETO_MINIMO: float = 12.0
    UMBRAL_EFICIENCIA_OBJETIVO: float = 65.0
    
    # 🏦 Nombres de tablas de la BD (constantes del sistema)
    TABLA_CONTRATOS: str = "MAESTRO_CONTRATOS"
    TABLA_MOVIMIENTOS: str = "MOVIMIENTOS_CONTRATOS"
    TABLA_PRECIO_REAL: str = "PRECIO_POR_PRODUCTO_REAL"
    TABLA_PRECIO_STD: str = "PRECIO_POR_PRODUCTO_STD"
    TABLA_GESTORES: str = "MAESTRO_GESTORES"
    TABLA_CLIENTES: str = "MAESTRO_CLIENTES"
    TABLA_CENTROS: str = "MAESTRO_CENTROS"
    TABLA_PRODUCTOS: str = "MAESTRO_PRODUCTOS"
    TABLA_SEGMENTOS: str = "MAESTRO_SEGMENTOS"
    TABLA_GASTOS: str = "GASTOS_CENTRO"
    TABLA_CUENTAS: str = "MAESTRO_CUENTAS"
    TABLA_CDR: str = "MAESTRO_LINEA_CDR"
    
    # 📊 Configuración de gráficos
    CHART_DEFAULT_LIMIT: int = 25
    CHART_CACHE_MINUTES: int = 5
    CHART_MAX_DATA_POINTS: int = 100
    
    # 🔐 Configuración de seguridad
    ALLOWED_SQL_OPERATIONS: list = ["SELECT"]
    MAX_QUERY_RESULTS: int = 1000
    QUERY_TIMEOUT_SECONDS: int = 30
    
    # 🌐 API Configuration
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_URL: str = "/docs"
    API_REDOC_URL: str = "/redoc"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]
    
    # 💾 Cache y performance
    SCHEMA_CACHE_DURATION: int = 300  # 5 minutos
    CONVERSATION_HISTORY_LIMIT: int = 50
    SESSION_TIMEOUT_MINUTES: int = 120
    
    if PYDANTIC_V2:
        # Configuración para Pydantic v2
        model_config = SettingsConfigDict(
            env_file=Path(__file__).parent.parent / ".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=True
        )
    else:
        # Configuración para Pydantic v1 (fallback)
        class Config:
            env_file = str(Path(__file__).parent.parent / ".env")
            env_file_encoding = "utf-8"
            extra = "ignore"
            case_sensitive = True
    
    def validate_azure_config(self) -> bool:
        """Valida que la configuración de Azure OpenAI esté completa"""
        required_fields = [
            self.AZURE_OPENAI_API_KEY,
            self.AZURE_OPENAI_ENDPOINT, 
            self.AZURE_OPENAI_DEPLOYMENT_ID,
            self.AZURE_OPENAI_API_VERSION
        ]
        return all(field for field in required_fields)
    
    def get_database_url(self) -> str:
        """Retorna la URL completa de la base de datos"""
        return f"sqlite:///{self.DATABASE_PATH}"
    
    def validate_database_path(self) -> bool:
        """Verifica que el archivo de base de datos existe"""
        return Path(self.DATABASE_PATH).exists()
    
    @property
    def is_production(self) -> bool:
        """Determina si estamos en modo producción"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_azure_openai_config(self) -> dict:
        """Retorna configuración completa de Azure OpenAI"""
        return {
            "api_key": self.AZURE_OPENAI_API_KEY,
            "azure_endpoint": self.AZURE_OPENAI_ENDPOINT,
            "api_version": self.AZURE_OPENAI_API_VERSION,
            "deployment_id": self.AZURE_OPENAI_DEPLOYMENT_ID,
            "temperature": self.DEFAULT_TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
            "timeout": self.TIMEOUT_SECONDS
        }


# Instancia global de configuración
try:
    settings = Settings()
    
    # Validaciones en tiempo de inicialización
    if not settings.validate_azure_config():
        raise ValueError("❌ Configuración de Azure OpenAI incompleta. Verifica tu archivo .env")
    
    # Log de estado de configuración
    import logging
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
    logger = logging.getLogger(__name__)
    
    logger.info("✅ Configuración CDG Agent cargada exitosamente")
    logger.info(f"📍 Base de datos: {settings.DATABASE_PATH}")
    logger.info(f"🤖 Azure OpenAI: {settings.AZURE_OPENAI_ENDPOINT}")
    logger.info(f"🎯 Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_ID}")
    logger.info(f"🏗️ Modo: {'PRODUCTION' if settings.is_production else 'DEVELOPMENT'}")
    
    if not settings.validate_database_path():
        logger.warning(f"⚠️ Base de datos no encontrada en: {settings.DATABASE_PATH}")
    
except Exception as e:
    # Configuración fallback en caso de error crítico
    print(f"❌ Error cargando configuración: {e}")
    print("🔄 Usando configuración fallback...")
    
    class FallbackSettings:
        DATABASE_PATH = str(Path(__file__).parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db")
        DATABASE_TIMEOUT = 30
        DEFAULT_TEMPERATURE = 0.0
        MAX_TOKENS = 2000
        MAX_RETRIES = 3
        LOG_LEVEL = "INFO"
        UMBRAL_DESVIACION_CRITICA = 15.0
        AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
        AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        AZURE_OPENAI_DEPLOYMENT_ID = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4")
        AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        def validate_azure_config(self):
            return bool(self.AZURE_OPENAI_API_KEY and self.AZURE_OPENAI_ENDPOINT)
        
        def get_azure_openai_config(self):
            return {
                "api_key": self.AZURE_OPENAI_API_KEY,
                "azure_endpoint": self.AZURE_OPENAI_ENDPOINT,
                "api_version": self.AZURE_OPENAI_API_VERSION,
                "deployment_id": self.AZURE_OPENAI_DEPLOYMENT_ID
            }
    
    settings = FallbackSettings()


# Configuraciones específicas por módulo
class DatabaseConfig:
    """Configuración específica para acceso a BD"""
    CONNECTION_STRING = settings.get_database_url() if hasattr(settings, 'get_database_url') else f"sqlite:///{settings.DATABASE_PATH}"
    TIMEOUT = settings.DATABASE_TIMEOUT
    MAX_CONNECTIONS = 10
    POOL_SIZE = 5


class LLMConfig:
    """Configuración específica para Azure OpenAI"""
    CONFIG = settings.get_azure_openai_config() if hasattr(settings, 'get_azure_openai_config') else {
        "api_key": settings.AZURE_OPENAI_API_KEY,
        "azure_endpoint": settings.AZURE_OPENAI_ENDPOINT,
        "api_version": settings.AZURE_OPENAI_API_VERSION,
        "deployment_id": settings.AZURE_OPENAI_DEPLOYMENT_ID
    }


class SecurityConfig:
    """Configuración de seguridad"""
    ALLOWED_OPERATIONS = ["SELECT"]
    MAX_RESULTS = getattr(settings, 'MAX_QUERY_RESULTS', 1000)
    QUERY_TIMEOUT = getattr(settings, 'QUERY_TIMEOUT_SECONDS', 30)


# Exports principales
__all__ = [
    'settings',
    'DatabaseConfig', 
    'LLMConfig',
    'SecurityConfig'
]

# Validación final
if __name__ == "__main__":
    print("🔧 Validando configuración CDG Agent...")
    print(f"✅ Azure OpenAI configurado: {settings.validate_azure_config()}")
    print(f"✅ Base de datos: {settings.DATABASE_PATH}")
    print(f"✅ Deployment ID: {settings.AZURE_OPENAI_DEPLOYMENT_ID}")
    print("🚀 Configuración lista para uso")
