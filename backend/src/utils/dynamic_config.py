# backend/src/utils/dynamic_config.py
import logging
import sys
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 🔧 CORREGIDO: Import robusto que funciona desde cualquier contexto
try:
    # Intenta importación relativa (cuando se ejecuta como paquete)
    from ..database.db_connection import execute_query, execute_pandas_query
except ImportError:
    # Fallback a importación absoluta (cuando se ejecuta como script)
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from database.db_connection import execute_query, execute_pandas_query

logger = logging.getLogger(__name__)


@dataclass
class ProductoInfo:
    """Información de un producto bancario"""
    producto_id: str
    descripcion: str
    activo: bool = True


@dataclass
class CentroInfo:
    """Información de un centro"""
    centro_id: int
    descripcion: str
    tipo: str  # 'FINALISTA' o 'CENTRAL'


@dataclass
class SegmentoInfo:
    """Información de un segmento"""
    segmento_id: str
    descripcion: str
    activo: bool = True


@dataclass
class GestorInfo:
    """Información de un gestor"""
    gestor_id: str
    nombre: str
    centro_id: int
    segmento_id: str
    activo: bool = True


class DynamicBusinessConfig:
    """
    Configuración de negocio obtenida dinámicamente de la base de datos.
    Esta clase evita hardcodear datos de negocio en el código, permitiendo
    escalabilidad completa del sistema.
    """
    
    def __init__(self):
        self._cache = {}  # Cache simple para evitar consultas repetitivas
        self._cache_timestamp = {}
        self.cache_duration = 300  # 5 minutos de cache
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si el cache para una clave específica sigue siendo válido"""
        if key not in self._cache_timestamp:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp[key]).seconds
        return elapsed < self.cache_duration
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Establece un valor en cache con timestamp"""
        self._cache[key] = value
        self._cache_timestamp[key] = datetime.now()
    
    def get_productos_activos(self, force_refresh: bool = False) -> List[ProductoInfo]:
        """
        Obtiene todos los productos bancarios activos desde la base de datos.
        
        Args:
            force_refresh: Si True, ignora el cache y consulta la BD
            
        Returns:
            Lista de ProductoInfo con todos los productos activos
        """
        cache_key = "productos_activos"
        
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.debug("✅ Productos obtenidos desde cache")
            return self._cache[cache_key]
        
        try:
            query = """
                SELECT PRODUCTO_ID, DESC_PRODUCTO
                FROM MAESTRO_PRODUCTOS
                ORDER BY PRODUCTO_ID
            """
            
            results = execute_query(query)
            productos = [
                ProductoInfo(
                    producto_id=row["PRODUCTO_ID"],
                    descripcion=row["DESC_PRODUCTO"]
                )
                for row in results
            ]
            
            self._set_cache(cache_key, productos)
            logger.info(f"✅ {len(productos)} productos activos obtenidos de BD")
            return productos
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo productos activos: {e}")
            raise RuntimeError(f"Error obteniendo productos: {e}")
    
    def get_centros_por_tipo(self, force_refresh: bool = False) -> Dict[str, List[CentroInfo]]:
        """
        Obtiene centros clasificados por tipo (FINALISTA/CENTRAL).
        
        Returns:
            Dict con keys 'FINALISTA' y 'CENTRAL', values son listas de CentroInfo
        """
        cache_key = "centros_por_tipo"
        
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.debug("✅ Centros obtenidos desde cache")
            return self._cache[cache_key]
        
        try:
            query = """
                SELECT 
                    CENTRO_ID, 
                    DESC_CENTRO,
                    CASE 
                        WHEN CENTRO_ID <= 5 THEN 'FINALISTA' 
                        ELSE 'CENTRAL' 
                    END as TIPO_CENTRO
                FROM MAESTRO_CENTRO
                ORDER BY CENTRO_ID
            """
            
            results = execute_query(query)
            
            # Organizar por tipo
            centros_por_tipo = {"FINALISTA": [], "CENTRAL": []}
            
            for row in results:
                centro = CentroInfo(
                    centro_id=row["CENTRO_ID"],
                    descripcion=row["DESC_CENTRO"],
                    tipo=row["TIPO_CENTRO"]
                )
                centros_por_tipo[row["TIPO_CENTRO"]].append(centro)
            
            self._set_cache(cache_key, centros_por_tipo)
            logger.info(f"✅ Centros obtenidos: {len(centros_por_tipo['FINALISTA'])} finalistas, {len(centros_por_tipo['CENTRAL'])} centrales")
            return centros_por_tipo
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo centros: {e}")
            raise RuntimeError(f"Error obteniendo centros: {e}")
    
    def get_segmentos_activos(self, force_refresh: bool = False) -> List[SegmentoInfo]:
        """Obtiene todos los segmentos activos"""
        cache_key = "segmentos_activos"
        
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.debug("✅ Segmentos obtenidos desde cache")
            return self._cache[cache_key]
        
        try:
            query = """
                SELECT SEGMENTO_ID, DESC_SEGMENTO
                FROM MAESTRO_SEGMENTOS
                ORDER BY SEGMENTO_ID
            """
            
            results = execute_query(query)
            segmentos = [
                SegmentoInfo(
                    segmento_id=row["SEGMENTO_ID"],
                    descripcion=row["DESC_SEGMENTO"]
                )
                for row in results
            ]
            
            self._set_cache(cache_key, segmentos)
            logger.info(f"✅ {len(segmentos)} segmentos activos obtenidos")
            return segmentos
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo segmentos: {e}")
            raise RuntimeError(f"Error obteniendo segmentos: {e}")
    
    def get_gestores_por_centro(self, centro_id: Optional[int] = None, force_refresh: bool = False) -> List[GestorInfo]:
        """
        Obtiene gestores filtrados opcionalmente por centro.
        
        Args:
            centro_id: Si se especifica, filtra gestores de ese centro únicamente
            force_refresh: Si True, ignora cache
            
        Returns:
            Lista de GestorInfo
        """
        cache_key = f"gestores_centro_{centro_id}" if centro_id else "gestores_todos"
        
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.debug("✅ Gestores obtenidos desde cache")
            return self._cache[cache_key]
        
        try:
            query = """
                SELECT GESTOR_ID, DESC_GESTOR, CENTRO, SEGMENTO_ID
                FROM MAESTRO_GESTORES
            """
            params = None
            
            if centro_id:
                query += " WHERE CENTRO = ?"
                params = (centro_id,)
            
            query += " ORDER BY CENTRO, GESTOR_ID"
            
            results = execute_query(query, params)
            gestores = [
                GestorInfo(
                    gestor_id=row["GESTOR_ID"],
                    nombre=row["DESC_GESTOR"],
                    centro_id=row["CENTRO"],
                    segmento_id=row["SEGMENTO_ID"]
                )
                for row in results
            ]
            
            self._set_cache(cache_key, gestores)
            logger.info(f"✅ {len(gestores)} gestores obtenidos" + (f" para centro {centro_id}" if centro_id else ""))
            return gestores
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo gestores: {e}")
            raise RuntimeError(f"Error obteniendo gestores: {e}")
    
    def get_cuentas_contables(self, tipo_cuenta: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene cuentas contables, opcionalmente filtradas por tipo.
        
        Args:
            tipo_cuenta: Filtro opcional ('INGRESOS', 'GASTOS', 'MARGEN', etc.)
            force_refresh: Si True, ignora cache
        """
        cache_key = f"cuentas_{tipo_cuenta}" if tipo_cuenta else "cuentas_todas"
        
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.debug("✅ Cuentas contables obtenidas desde cache")
            return self._cache[cache_key]
        
        try:
            query = """
                SELECT CUENTA_ID, DESC_CUENTA, NATURALEZA, SIGNO
                FROM MAESTRO_CUENTAS
                ORDER BY CUENTA_ID
            """
            
            results = execute_query(query)
            
            # Filtrar por tipo si se especifica
            if tipo_cuenta:
                # Lógica simple de filtrado basada en el nombre de la cuenta
                tipo_filters = {
                    'INGRESOS': ['CR0001', 'CR0002', 'CR0003'],
                    'GASTOS': ['CR0010', 'CR0011', 'CR0012', 'CR0015'],
                    'MARGEN': ['CR0020', 'CR0025', 'CR0030']
                }
                
                if tipo_cuenta in tipo_filters:
                    cuenta_ids = tipo_filters[tipo_cuenta]
                    results = [r for r in results if r["CUENTA_ID"] in cuenta_ids]
            
            self._set_cache(cache_key, results)
            logger.info(f"✅ {len(results)} cuentas contables obtenidas")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo cuentas contables: {e}")
            raise RuntimeError(f"Error obteniendo cuentas: {e}")
    
    def get_configuracion_fondos(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtiene configuración específica para fondos (distribución 85%/15%).
        Busca en la base de datos para obtener los códigos de cuenta reales.
        """
        cache_key = "config_fondos"
        
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            # Buscar cuentas de reparto de fondos en movimientos
            query = """
                SELECT DISTINCT CUENTA_ID, COUNT(*) as FRECUENCIA
                FROM MOVIMIENTOS_CONTRATOS
                WHERE CUENTA_ID LIKE '7600%'
                GROUP BY CUENTA_ID
                ORDER BY FRECUENCIA DESC
                LIMIT 2
            """
            
            results = execute_query(query)
            
            # Configuración por defecto basada en los datos conocidos
            config = {
                "producto_fondos": "600100300300",
                "distribucion": {
                    "fabrica_pct": 85,
                    "banco_pct": 15
                },
                "cuentas_reparto": {
                    "fabrica": "760025",
                    "banco": "760024"
                }
            }
            
            # Actualizar con datos reales si están disponibles
            if len(results) >= 2:
                config["cuentas_reparto"]["fabrica"] = results[0]["CUENTA_ID"]
                config["cuentas_reparto"]["banco"] = results[1]["CUENTA_ID"]
            
            self._set_cache(cache_key, config)
            logger.info("✅ Configuración de fondos obtenida")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración fondos: {e}")
            return {
                "producto_fondos": "600100300300",
                "distribucion": {"fabrica_pct": 85, "banco_pct": 15},
                "cuentas_reparto": {"fabrica": "760025", "banco": "760024"}
            }
    
    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """
        Invalida cache completo o una clave específica.
        Útil cuando se detectan cambios en la base de datos.
        """
        if key:
            self._cache.pop(key, None)
            self._cache_timestamp.pop(key, None)
            logger.info(f"🔄 Cache invalidado para: {key}")
        else:
            self._cache.clear()
            self._cache_timestamp.clear()
            logger.info("🔄 Cache completo invalidado")


# Instancia global para uso en toda la aplicación
business_config = DynamicBusinessConfig()

# Funciones de conveniencia para importación directa
def get_productos_activos():
    """Función de conveniencia para obtener productos activos"""
    return business_config.get_productos_activos()

def get_centros_finalistas():
    """Función de conveniencia para obtener solo centros finalistas"""
    centros = business_config.get_centros_por_tipo()
    return [c.centro_id for c in centros["FINALISTA"]]

def get_centros_centrales():
    """Función de conveniencia para obtener solo centros centrales"""
    centros = business_config.get_centros_por_tipo()
    return [c.centro_id for c in centros["CENTRAL"]]

def get_segmentos_activos():
    """Función de conveniencia para obtener segmentos activos"""
    return business_config.get_segmentos_activos()
