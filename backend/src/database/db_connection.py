# backend/src/database/db_connection.py
import sqlite3
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager
import sys
import os

# 🔧 CORREGIDO: Import absoluto para config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import settings

# Configurar logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manager de conexiones SQLite para la base de datos BM_CONTABILIDAD_CDG.db
    Implementa connection pooling básico y manejo robusto de errores.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.timeout = settings.DATABASE_TIMEOUT
        self._validate_database_exists()
    
    def _validate_database_exists(self) -> None:
        """Valida que la base de datos existe y es accesible"""
        db_file = Path(self.db_path)
        if not db_file.exists():
            raise FileNotFoundError(f"❌ Base de datos no encontrada: {self.db_path}")
        
        if not db_file.is_file():
            raise ValueError(f"❌ La ruta no es un archivo válido: {self.db_path}")
        
        logger.info(f"✅ Base de datos validada: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para conexiones SQLite con manejo automático de errores
        
        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tabla")
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False
            )
            # Configurar para mejores resultados
            conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
            conn.execute("PRAGMA foreign_keys = ON")  # Habilitar foreign keys
            
            logger.debug(f"🔗 Conexión SQLite establecida: {self.db_path}")
            yield conn
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error de base de datos: {e}")
            if conn:
                conn.rollback()
            raise RuntimeError(f"Error de base de datos: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error inesperado en conexión: {e}")
            if conn:
                conn.rollback()
            raise RuntimeError(f"Error inesperado: {e}")
        
        finally:
            if conn:
                conn.close()
                logger.debug("🔒 Conexión SQLite cerrada")


class QueryExecutor:
    """
    Ejecutor de consultas SQL con funcionalidades específicas para el Agente CDG
    Maneja tanto consultas de lectura como escritura de forma segura.
    """
    
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        self.db_manager = db_connection or DatabaseConnection()
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[tuple, dict]] = None,
        fetch_type: str = "all"
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Ejecuta una consulta SQL y devuelve resultados formateados
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta (opcional)
            fetch_type: "all", "one", "none" para diferentes tipos de resultado
            
        Returns:
            Resultados de la consulta en formato dict o lista de dicts
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Ejecutar consulta con o sin parámetros
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Procesar resultados según tipo solicitado
                if fetch_type == "none":
                    conn.commit()  # Para INSERT, UPDATE, DELETE
                    return None
                
                elif fetch_type == "one":
                    row = cursor.fetchone()
                    return dict(row) if row else None
                
                else:  # fetch_type == "all"
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"❌ Error ejecutando query: {e}")
            logger.debug(f"Query problemática: {query}")
            raise RuntimeError(f"Error en consulta SQL: {e}")
    
    def execute_pandas_query(
        self, 
        query: str, 
        params: Optional[Union[tuple, dict]] = None
    ) -> pd.DataFrame:
        """
        Ejecuta una consulta SQL y devuelve un DataFrame de pandas
        Útil para análisis de datos y cálculos complejos.
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta (opcional)
            
        Returns:
            DataFrame con los resultados de la consulta
        """
        try:
            with self.db_manager.get_connection() as conn:
                if params:
                    df = pd.read_sql_query(query, conn, params=params)
                else:
                    df = pd.read_sql_query(query, conn)
                
                logger.info(f"✅ Consulta pandas ejecutada: {len(df)} filas obtenidas")
                return df
                
        except Exception as e:
            logger.error(f"❌ Error en consulta pandas: {e}")
            raise RuntimeError(f"Error en consulta pandas: {e}")
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Obtiene información sobre una tabla específica (columnas, tipos, etc.)
        Útil para validaciones y debugging.
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def get_table_count(self, table_name: str) -> int:
        """Obtiene el número de registros en una tabla"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query, fetch_type="one")
        return result["count"] if result else 0
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa la conexión y devuelve información básica de la base de datos
        Útil para verificar que todo funciona correctamente.
        """
        try:
            # Obtener lista de tablas
            tables_query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            tables = self.execute_query(tables_query)
            
            # Información básica por tabla
            table_info = {}
            for table in tables:
                table_name = table["name"]
                count = self.get_table_count(table_name)
                table_info[table_name] = count
            
            logger.info("✅ Test de conexión exitoso")
            return {
                "status": "success",
                "database_path": self.db_manager.db_path,
                "total_tables": len(tables),
                "tables": table_info
            }
            
        except Exception as e:
            logger.error(f"❌ Test de conexión fallido: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database_path": self.db_manager.db_path
            }


# Instancias globales para uso en toda la aplicación
db_manager = DatabaseConnection()
query_executor = QueryExecutor(db_manager)

# Funciones de conveniencia para importación fácil
def execute_query(query: str, params: Optional[Union[tuple, dict]] = None, fetch_type: str = "all"):
    """Función de conveniencia para ejecutar consultas SQL"""
    return query_executor.execute_query(query, params, fetch_type)

def execute_pandas_query(query: str, params: Optional[Union[tuple, dict]] = None):
    """Función de conveniencia para consultas que devuelven DataFrame"""
    return query_executor.execute_pandas_query(query, params)

def test_database_connection():
    """Función de conveniencia para testar la conexión"""
    return query_executor.test_connection()
