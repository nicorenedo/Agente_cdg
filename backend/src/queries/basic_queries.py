"""
basic_queries.py - Consultas básicas para el Agente CDG
Biblioteca completa de queries SQL que utiliza la infraestructura de db_connection.py
"""

import logging
from typing import List, Dict, Any, Optional
from database.db_connection import query_executor, execute_query, execute_pandas_query
import pandas as pd

# Configurar logging
logger = logging.getLogger(__name__)

class BasicQueries:
    """
    Biblioteca de consultas básicas para el sistema CDG
    Utiliza QueryExecutor para todas las operaciones de base de datos
    """
    
    def __init__(self, query_exec: Optional[object] = None):
        self.query_executor = query_exec or query_executor
        logger.info("✅ BasicQueries inicializado")
    
    # =====================================
    # CONSULTAS DE CENTROS
    # =====================================
    
    def get_all_centros(self) -> List[Dict[str, Any]]:
        """Obtiene todos los centros"""
        query = """
        SELECT CENTRO_ID, DESC_CENTRO, IND_CENTRO_FINALISTA, EMPRESA_ID
        FROM MAESTRO_CENTROS
        ORDER BY CENTRO_ID
        """
        return self.query_executor.execute_query(query)
    
    def get_centros_finalistas(self) -> List[Dict[str, Any]]:
        """Obtiene solo los centros finalistas (con contratos)"""
        query = """
        SELECT CENTRO_ID, DESC_CENTRO, IND_CENTRO_FINALISTA, EMPRESA_ID
        FROM MAESTRO_CENTROS 
        WHERE IND_CENTRO_FINALISTA = 1
        ORDER BY CENTRO_ID
        """
        return self.query_executor.execute_query(query)
    
    def get_centros_no_finalistas(self) -> List[Dict[str, Any]]:
        """Obtiene solo los centros de soporte (sin contratos)"""
        query = """
        SELECT CENTRO_ID, DESC_CENTRO, IND_CENTRO_FINALISTA, EMPRESA_ID
        FROM MAESTRO_CENTROS 
        WHERE IND_CENTRO_FINALISTA = 0
        ORDER BY CENTRO_ID
        """
        return self.query_executor.execute_query(query)
    
    def count_centros_by_type(self) -> Dict[str, int]:
        """Cuenta centros por tipo (finalista/no finalista)"""
        query = """
        SELECT 
            SUM(CASE WHEN IND_CENTRO_FINALISTA = 1 THEN 1 ELSE 0 END) as finalistas,
            SUM(CASE WHEN IND_CENTRO_FINALISTA = 0 THEN 1 ELSE 0 END) as no_finalistas,
            COUNT(*) as total
        FROM MAESTRO_CENTROS
        """
        result = self.query_executor.execute_query(query, fetch_type="one")
        return result if result else {"finalistas": 0, "no_finalistas": 0, "total": 0}
    
    # =====================================
    # CONSULTAS DE GESTORES
    # =====================================
    
    def get_all_gestores(self) -> List[Dict[str, Any]]:
        """Obtiene todos los gestores"""
        query = """
        SELECT g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
               c.DESC_CENTRO, s.DESC_SEGMENTO
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
        LEFT JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
        ORDER BY g.GESTOR_ID
        """
        return self.query_executor.execute_query(query)
    
    def get_gestores_by_centro(self, centro_id: int) -> List[Dict[str, Any]]:
        """Obtiene gestores de un centro específico"""
        query = """
        SELECT g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
               c.DESC_CENTRO, s.DESC_SEGMENTO
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
        LEFT JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
        WHERE g.CENTRO = ?
        ORDER BY g.GESTOR_ID
        """
        return self.query_executor.execute_query(query, (centro_id,))
    
    def get_gestores_by_segmento(self, segmento_id: str) -> List[Dict[str, Any]]:
        """Obtiene gestores de un segmento específico"""
        query = """
        SELECT g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
               c.DESC_CENTRO, s.DESC_SEGMENTO
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
        LEFT JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
        WHERE g.SEGMENTO_ID = ?
        ORDER BY g.GESTOR_ID
        """
        return self.query_executor.execute_query(query, (segmento_id,))
    
    def get_gestor_info(self, gestor_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene información completa de un gestor específico"""
        query = """
        SELECT g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
               c.DESC_CENTRO, s.DESC_SEGMENTO, c.IND_CENTRO_FINALISTA
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
        LEFT JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
        WHERE g.GESTOR_ID = ?
        """
        return self.query_executor.execute_query(query, (gestor_id,), fetch_type="one")
    
    def count_gestores_by_centro(self) -> List[Dict[str, Any]]:
        """Cuenta gestores por centro"""
        query = """
        SELECT c.CENTRO_ID, c.DESC_CENTRO, COUNT(g.GESTOR_ID) as num_gestores
        FROM MAESTRO_CENTROS c
        LEFT JOIN MAESTRO_GESTORES g ON c.CENTRO_ID = g.CENTRO
        GROUP BY c.CENTRO_ID, c.DESC_CENTRO
        ORDER BY c.CENTRO_ID
        """
        return self.query_executor.execute_query(query)
    
    def count_gestores_by_segmento(self) -> List[Dict[str, Any]]:
        """Cuenta gestores por segmento"""
        query = """
        SELECT s.SEGMENTO_ID, s.DESC_SEGMENTO, COUNT(g.GESTOR_ID) as num_gestores
        FROM MAESTRO_SEGMENTOS s
        LEFT JOIN MAESTRO_GESTORES g ON s.SEGMENTO_ID = g.SEGMENTO_ID
        GROUP BY s.SEGMENTO_ID, s.DESC_SEGMENTO
        ORDER BY s.SEGMENTO_ID
        """
        return self.query_executor.execute_query(query)
    
    # =====================================
    # CONSULTAS DE PRODUCTOS
    # =====================================
    
    def get_all_productos(self) -> List[Dict[str, Any]]:
        """Obtiene todos los productos"""
        query = """
        SELECT PRODUCTO_ID, DESC_PRODUCTO, IND_FABRICA, FABRICA, BANCO, EMPRESA_ID
        FROM MAESTRO_PRODUCTOS
        ORDER BY PRODUCTO_ID
        """
        return self.query_executor.execute_query(query)
    
    def count_productos(self) -> int:
        """Cuenta total de productos"""
        query = "SELECT COUNT(*) as total FROM MAESTRO_PRODUCTOS"
        result = self.query_executor.execute_query(query, fetch_type="one")
        return result["total"] if result else 0
    
    def get_productos_fabrica_vs_banco(self) -> List[Dict[str, Any]]:
        """Obtiene productos clasificados por modelo fábrica vs banco"""
        query = """
        SELECT PRODUCTO_ID, DESC_PRODUCTO, 
               CASE WHEN IND_FABRICA = 1 THEN 'FABRICA' ELSE 'BANCO' END as modelo,
               FABRICA, BANCO
        FROM MAESTRO_PRODUCTOS
        ORDER BY IND_FABRICA DESC, PRODUCTO_ID
        """
        return self.query_executor.execute_query(query)
    
    # =====================================
    # CONSULTAS DE SEGMENTOS
    # =====================================
    
    def get_all_segmentos(self) -> List[Dict[str, Any]]:
        """Obtiene todos los segmentos"""
        query = """
        SELECT SEGMENTO_ID, DESC_SEGMENTO, EMPRESA_ID
        FROM MAESTRO_SEGMENTOS
        ORDER BY SEGMENTO_ID
        """
        return self.query_executor.execute_query(query)
    
    def count_segmentos(self) -> int:
        """Cuenta total de segmentos"""
        query = "SELECT COUNT(*) as total FROM MAESTRO_SEGMENTOS"
        result = self.query_executor.execute_query(query, fetch_type="one")
        return result["total"] if result else 0
    
    # =====================================
    # CONSULTAS DE CLIENTES
    # =====================================
    
    def get_all_clientes(self) -> List[Dict[str, Any]]:
        """Obtiene todos los clientes"""
        query = """
        SELECT c.CLIENTE_ID, c.NOMBRE_CLIENTE, c.GESTOR_ID, c.EMPRESA_ID,
               g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID
        FROM MAESTRO_CLIENTES c
        LEFT JOIN MAESTRO_GESTORES g ON c.GESTOR_ID = g.GESTOR_ID
        ORDER BY c.CLIENTE_ID
        """
        return self.query_executor.execute_query(query)
    
    def count_clientes(self) -> int:
        """Cuenta total de clientes"""
        query = "SELECT COUNT(*) as total FROM MAESTRO_CLIENTES"
        result = self.query_executor.execute_query(query, fetch_type="one")
        return result["total"] if result else 0
    
    def get_clientes_by_gestor(self, gestor_id: int) -> List[Dict[str, Any]]:
        """Obtiene clientes de un gestor específico"""
        query = """
        SELECT c.CLIENTE_ID, c.NOMBRE_CLIENTE, c.GESTOR_ID, c.EMPRESA_ID,
               g.DESC_GESTOR
        FROM MAESTRO_CLIENTES c
        LEFT JOIN MAESTRO_GESTORES g ON c.GESTOR_ID = g.GESTOR_ID
        WHERE c.GESTOR_ID = ?
        ORDER BY c.CLIENTE_ID
        """
        return self.query_executor.execute_query(query, (gestor_id,))
    
    def count_clientes_by_gestor(self) -> List[Dict[str, Any]]:
        """Cuenta clientes por gestor"""
        query = """
        SELECT g.GESTOR_ID, g.DESC_GESTOR, COUNT(c.CLIENTE_ID) as num_clientes
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CLIENTES c ON g.GESTOR_ID = c.GESTOR_ID
        GROUP BY g.GESTOR_ID, g.DESC_GESTOR
        ORDER BY num_clientes DESC
        """
        return self.query_executor.execute_query(query)
    
    def get_clientes_by_centro(self, centro_id: int) -> List[Dict[str, Any]]:
        """Obtiene clientes de un centro específico (a través de sus gestores)"""
        query = """
        SELECT c.CLIENTE_ID, c.NOMBRE_CLIENTE, c.GESTOR_ID,
               g.DESC_GESTOR, g.CENTRO
        FROM MAESTRO_CLIENTES c
        JOIN MAESTRO_GESTORES g ON c.GESTOR_ID = g.GESTOR_ID
        WHERE g.CENTRO = ?
        ORDER BY c.CLIENTE_ID
        """
        return self.query_executor.execute_query(query, (centro_id,))
    
    # =====================================
    # CONSULTAS DE CONTRATOS
    # =====================================
    
    def get_all_contratos(self) -> List[Dict[str, Any]]:
        """Obtiene todos los contratos con información relacionada"""
        query = """
        SELECT co.CONTRATO_ID, co.FECHA_ALTA, co.CLIENTE_ID, co.GESTOR_ID, 
               co.PRODUCTO_ID, co.CENTRO_CONTABLE, co.EMPRESA_ID,
               cl.NOMBRE_CLIENTE, g.DESC_GESTOR, p.DESC_PRODUCTO, c.DESC_CENTRO
        FROM MAESTRO_CONTRATOS co
        LEFT JOIN MAESTRO_CLIENTES cl ON co.CLIENTE_ID = cl.CLIENTE_ID
        LEFT JOIN MAESTRO_GESTORES g ON co.GESTOR_ID = g.GESTOR_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON co.PRODUCTO_ID = p.PRODUCTO_ID
        LEFT JOIN MAESTRO_CENTROS c ON co.CENTRO_CONTABLE = c.CENTRO_ID
        ORDER BY co.CONTRATO_ID
        """
        return self.query_executor.execute_query(query)
    
    def count_contratos(self) -> int:
        """Cuenta total de contratos"""
        query = "SELECT COUNT(*) as total FROM MAESTRO_CONTRATOS"
        result = self.query_executor.execute_query(query, fetch_type="one")
        return result["total"] if result else 0
    
    def get_contratos_by_gestor(self, gestor_id: int) -> List[Dict[str, Any]]:
        """Obtiene contratos de un gestor específico"""
        query = """
        SELECT co.CONTRATO_ID, co.FECHA_ALTA, co.CLIENTE_ID, co.PRODUCTO_ID,
               cl.NOMBRE_CLIENTE, p.DESC_PRODUCTO
        FROM MAESTRO_CONTRATOS co
        LEFT JOIN MAESTRO_CLIENTES cl ON co.CLIENTE_ID = cl.CLIENTE_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON co.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE co.GESTOR_ID = ?
        ORDER BY co.FECHA_ALTA DESC
        """
        return self.query_executor.execute_query(query, (gestor_id,))
    
    def get_contratos_by_cliente(self, cliente_id: int) -> List[Dict[str, Any]]:
        """Obtiene contratos de un cliente específico"""
        query = """
        SELECT co.CONTRATO_ID, co.FECHA_ALTA, co.GESTOR_ID, co.PRODUCTO_ID,
               g.DESC_GESTOR, p.DESC_PRODUCTO
        FROM MAESTRO_CONTRATOS co
        LEFT JOIN MAESTRO_GESTORES g ON co.GESTOR_ID = g.GESTOR_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON co.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE co.CLIENTE_ID = ?
        ORDER BY co.FECHA_ALTA DESC
        """
        return self.query_executor.execute_query(query, (cliente_id,))
    
    def get_contratos_by_producto(self, producto_id: str) -> List[Dict[str, Any]]:
        """Obtiene contratos de un producto específico"""
        query = """
        SELECT co.CONTRATO_ID, co.FECHA_ALTA, co.CLIENTE_ID, co.GESTOR_ID,
               cl.NOMBRE_CLIENTE, g.DESC_GESTOR
        FROM MAESTRO_CONTRATOS co
        LEFT JOIN MAESTRO_CLIENTES cl ON co.CLIENTE_ID = cl.CLIENTE_ID
        LEFT JOIN MAESTRO_GESTORES g ON co.GESTOR_ID = g.GESTOR_ID
        WHERE co.PRODUCTO_ID = ?
        ORDER BY co.FECHA_ALTA DESC
        """
        return self.query_executor.execute_query(query, (producto_id,))
    
    def count_contratos_by_gestor(self) -> List[Dict[str, Any]]:
        """Cuenta contratos por gestor"""
        query = """
        SELECT g.GESTOR_ID, g.DESC_GESTOR, COUNT(co.CONTRATO_ID) as num_contratos
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CONTRATOS co ON g.GESTOR_ID = co.GESTOR_ID
        GROUP BY g.GESTOR_ID, g.DESC_GESTOR
        ORDER BY num_contratos DESC
        """
        return self.query_executor.execute_query(query)
    
    def count_contratos_by_producto(self) -> List[Dict[str, Any]]:
        """Cuenta contratos por producto"""
        query = """
        SELECT p.PRODUCTO_ID, p.DESC_PRODUCTO, COUNT(co.CONTRATO_ID) as num_contratos
        FROM MAESTRO_PRODUCTOS p
        LEFT JOIN MAESTRO_CONTRATOS co ON p.PRODUCTO_ID = co.PRODUCTO_ID
        GROUP BY p.PRODUCTO_ID, p.DESC_PRODUCTO
        ORDER BY num_contratos DESC
        """
        return self.query_executor.execute_query(query)
    
    def count_contratos_by_centro(self) -> List[Dict[str, Any]]:
        """Cuenta contratos por centro"""
        query = """
        SELECT c.CENTRO_ID, c.DESC_CENTRO, COUNT(co.CONTRATO_ID) as num_contratos
        FROM MAESTRO_CENTROS c
        LEFT JOIN MAESTRO_CONTRATOS co ON c.CENTRO_ID = co.CENTRO_CONTABLE
        GROUP BY c.CENTRO_ID, c.DESC_CENTRO
        ORDER BY num_contratos DESC
        """
        return self.query_executor.execute_query(query)
    
    # =====================================
    # CONSULTAS DE LÍNEAS CDR
    # =====================================
    
    def get_all_lineas_cdr(self) -> List[Dict[str, Any]]:
        """Obtiene todas las líneas del Cuadro de Resultados"""
        query = """
        SELECT COD_LINEA_CDR, DES_LINEA_CDR
        FROM MAESTRO_LINEA_CDR
        ORDER BY COD_LINEA_CDR
        """
        return self.query_executor.execute_query(query)
    
    def count_lineas_cdr(self) -> int:
        """Cuenta total de líneas CDR"""
        query = "SELECT COUNT(*) as total FROM MAESTRO_LINEA_CDR"
        result = self.query_executor.execute_query(query, fetch_type="one")
        return result["total"] if result else 0
    
    # =====================================
    # CONSULTAS DE CUENTAS
    # =====================================
    
    def get_all_cuentas(self) -> List[Dict[str, Any]]:
        """Obtiene todas las cuentas contables"""
        query = """
        SELECT cu.CUENTA_ID, cu.DESC_CUENTA, cu.LINEA_CDR, cu.EMPRESA_ID,
               cdr.DES_LINEA_CDR
        FROM MAESTRO_CUENTAS cu
        LEFT JOIN MAESTRO_LINEA_CDR cdr ON cu.LINEA_CDR = cdr.COD_LINEA_CDR
        ORDER BY cu.CUENTA_ID
        """
        return self.query_executor.execute_query(query)
    
    def get_cuentas_by_linea_cdr(self, linea_cdr: str) -> List[Dict[str, Any]]:
        """Obtiene cuentas de una línea CDR específica"""
        query = """
        SELECT CUENTA_ID, DESC_CUENTA, LINEA_CDR, EMPRESA_ID
        FROM MAESTRO_CUENTAS
        WHERE LINEA_CDR = ?
        ORDER BY CUENTA_ID
        """
        return self.query_executor.execute_query(query, (linea_cdr,))
    
    # =====================================
    # CONSULTAS DE PRECIOS ESTÁNDAR
    # =====================================
    
    def get_all_precios_std(self) -> List[Dict[str, Any]]:
        """Obtiene todos los precios estándar"""
        query = """
        SELECT ps.SEGMENTO_ID, ps.PRODUCTO_ID, ps.PRECIO_MANTENIMIENTO, 
               ps.ANNO, ps.FECHA_ACTUALIZACION,
               s.DESC_SEGMENTO, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_STD ps
        LEFT JOIN MAESTRO_SEGMENTOS s ON ps.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON ps.PRODUCTO_ID = p.PRODUCTO_ID
        ORDER BY ps.SEGMENTO_ID, ps.PRODUCTO_ID
        """
        return self.query_executor.execute_query(query)
    
    def get_precio_std_by_segmento_producto(self, segmento_id: str, producto_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene precio estándar para una combinación específica segmento-producto"""
        query = """
        SELECT ps.*, s.DESC_SEGMENTO, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_STD ps
        LEFT JOIN MAESTRO_SEGMENTOS s ON ps.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON ps.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE ps.SEGMENTO_ID = ? AND ps.PRODUCTO_ID = ?
        """
        return self.query_executor.execute_query(query, (segmento_id, producto_id), fetch_type="one")
    
    def get_precios_std_by_segmento(self, segmento_id: str) -> List[Dict[str, Any]]:
        """Obtiene precios estándar de un segmento"""
        query = """
        SELECT ps.*, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_STD ps
        LEFT JOIN MAESTRO_PRODUCTOS p ON ps.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE ps.SEGMENTO_ID = ?
        ORDER BY ps.PRODUCTO_ID
        """
        return self.query_executor.execute_query(query, (segmento_id,))
    
    def get_precios_real_by_segmento_periodo(self, segmento_id: str, periodo: str) -> List[Dict[str, Any]]:
        """Obtiene precios reales de un segmento específico para un período determinado"""
        # Convertir período YYYY-MM a fecha YYYY-MM-01 para consulta
        fecha_calculo = f"{periodo}-01"
        
        query = """
        SELECT pr.*, s.DESC_SEGMENTO, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_REAL pr
        LEFT JOIN MAESTRO_SEGMENTOS s ON pr.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON pr.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE pr.SEGMENTO_ID = ? AND pr.FECHA_CALCULO = ?
        ORDER BY pr.PRODUCTO_ID
        """
        return self.query_executor.execute_query(query, (segmento_id, fecha_calculo))
    
    def get_precios_real_by_segmento(self, segmento_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los precios reales de un segmento (últimos disponibles)"""
        query = """
        SELECT pr.*, s.DESC_SEGMENTO, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_REAL pr
        LEFT JOIN MAESTRO_SEGMENTOS s ON pr.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON pr.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE pr.SEGMENTO_ID = ?
        ORDER BY pr.FECHA_CALCULO DESC, pr.PRODUCTO_ID
        """
        return self.query_executor.execute_query(query, (segmento_id,))
    
    
    # =====================================
    # CONSULTAS DE PRECIOS REALES
    # =====================================
    
    def get_all_precios_real(self) -> List[Dict[str, Any]]:
        """Obtiene todos los precios reales"""
        query = """
        SELECT pr.SEGMENTO_ID, pr.PRODUCTO_ID, pr.PRECIO_MANTENIMIENTO_REAL,
               pr.FECHA_CALCULO, pr.NUM_CONTRATOS_BASE, pr.GASTOS_TOTALES_ASIGNADOS,
               pr.COSTE_UNITARIO_CALCULADO,
               s.DESC_SEGMENTO, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_REAL pr
        LEFT JOIN MAESTRO_SEGMENTOS s ON pr.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON pr.PRODUCTO_ID = p.PRODUCTO_ID
        ORDER BY pr.FECHA_CALCULO DESC, pr.SEGMENTO_ID, pr.PRODUCTO_ID
        """
        return self.query_executor.execute_query(query)
    
    def get_precio_real_by_fecha(self, fecha_calculo: str) -> List[Dict[str, Any]]:
        """Obtiene precios reales de una fecha específica"""
        query = """
        SELECT pr.*, s.DESC_SEGMENTO, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_REAL pr
        LEFT JOIN MAESTRO_SEGMENTOS s ON pr.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON pr.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE pr.FECHA_CALCULO = ?
        ORDER BY pr.SEGMENTO_ID, pr.PRODUCTO_ID
        """
        return self.query_executor.execute_query(query, (fecha_calculo,))
    
    def get_precio_real_by_segmento_producto(self, segmento_id: str, producto_id: str) -> List[Dict[str, Any]]:
        """Obtiene evolución de precios reales para una combinación segmento-producto"""
        query = """
        SELECT pr.*, s.DESC_SEGMENTO, p.DESC_PRODUCTO
        FROM PRECIO_POR_PRODUCTO_REAL pr
        LEFT JOIN MAESTRO_SEGMENTOS s ON pr.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON pr.PRODUCTO_ID = p.PRODUCTO_ID
        WHERE pr.SEGMENTO_ID = ? AND pr.PRODUCTO_ID = ?
        ORDER BY pr.FECHA_CALCULO DESC
        """
        return self.query_executor.execute_query(query, (segmento_id, producto_id))
    
    # =====================================
    # COMPARATIVAS PRECIOS STD vs REAL
    # =====================================
    
    def compare_precios_std_vs_real(self, fecha_calculo: str = None) -> List[Dict[str, Any]]:
        """Compara precios estándar vs reales"""
        if fecha_calculo:
            where_clause = "WHERE pr.FECHA_CALCULO = ?"
            params = (fecha_calculo,)
        else:
            where_clause = ""
            params = ()
            
        query = f"""
        SELECT ps.SEGMENTO_ID, ps.PRODUCTO_ID,
               s.DESC_SEGMENTO, p.DESC_PRODUCTO,
               ps.PRECIO_MANTENIMIENTO as precio_std,
               pr.PRECIO_MANTENIMIENTO_REAL as precio_real,
               pr.FECHA_CALCULO,
               ROUND((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO), 2) as diferencia,
               ROUND(((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) / ps.PRECIO_MANTENIMIENTO * 100), 2) as porcentaje_desviacion
        FROM PRECIO_POR_PRODUCTO_STD ps
        JOIN PRECIO_POR_PRODUCTO_REAL pr ON ps.SEGMENTO_ID = pr.SEGMENTO_ID 
            AND ps.PRODUCTO_ID = pr.PRODUCTO_ID
        LEFT JOIN MAESTRO_SEGMENTOS s ON ps.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON ps.PRODUCTO_ID = p.PRODUCTO_ID
        {where_clause}
        ORDER BY porcentaje_desviacion DESC
        """
        return self.query_executor.execute_query(query, params)
    
    # =====================================
    # CONSULTAS DE GASTOS
    # =====================================
    
    def get_gastos_by_fecha(self, fecha: str) -> List[Dict[str, Any]]:
        """Obtiene gastos de una fecha específica"""
        query = """
        SELECT gc.EMPRESA, gc.CENTRO_CONTABLE, gc.CONCEPTO_COSTE, 
               gc.FECHA, gc.IMPORTE,
               c.DESC_CENTRO, c.IND_CENTRO_FINALISTA
        FROM GASTOS_CENTRO gc
        LEFT JOIN MAESTRO_CENTROS c ON gc.CENTRO_CONTABLE = c.CENTRO_ID
        WHERE gc.FECHA = ?
        ORDER BY gc.CENTRO_CONTABLE, gc.CONCEPTO_COSTE
        """
        return self.query_executor.execute_query(query, (fecha,))
    
    def get_gastos_by_centro(self, centro_id: int) -> List[Dict[str, Any]]:
        """Obtiene gastos de un centro específico"""
        query = """
        SELECT EMPRESA, CENTRO_CONTABLE, CONCEPTO_COSTE, FECHA, IMPORTE
        FROM GASTOS_CENTRO
        WHERE CENTRO_CONTABLE = ?
        ORDER BY FECHA DESC, CONCEPTO_COSTE
        """
        return self.query_executor.execute_query(query, (centro_id,))
    
    def get_gastos_totales_by_fecha(self, fecha: str) -> Dict[str, Any]:
        """Obtiene resumen de gastos totales por fecha"""
        query = """
        SELECT 
            FECHA,
            SUM(IMPORTE) as total_gastos,
            SUM(CASE WHEN c.IND_CENTRO_FINALISTA = 1 THEN IMPORTE ELSE 0 END) as gastos_finalistas,
            SUM(CASE WHEN c.IND_CENTRO_FINALISTA = 0 THEN IMPORTE ELSE 0 END) as gastos_centrales,
            COUNT(*) as num_registros
        FROM GASTOS_CENTRO gc
        LEFT JOIN MAESTRO_CENTROS c ON gc.CENTRO_CONTABLE = c.CENTRO_ID
        WHERE gc.FECHA = ?
        GROUP BY FECHA
        """
        return self.query_executor.execute_query(query, (fecha,), fetch_type="one")

    # =====================================
    # HELPERS DE COSTE INTERNO
    # =====================================

    def _get_gastos_centrales_periodo(self, periodo: Optional[str]) -> float:
        """Total de gastos de centros soporte (CONTRATO_ID IS NULL, cuentas 62/64/68/69).
        Fuente: MOVIMIENTOS_CONTRATOS. Los importes son negativos por convenio contable."""
        if periodo:
            query = """
            SELECT COALESCE(SUM(IMPORTE), 0) AS total
            FROM MOVIMIENTOS_CONTRATOS
            WHERE CONTRATO_ID IS NULL
              AND SUBSTR(CUENTA_ID, 1, 2) IN ('62','64','68','69')
              AND strftime('%Y-%m', FECHA) = ?
            """
            result = self.query_executor.execute_query(query, (periodo,), fetch_type="one")
        else:
            query = """
            SELECT COALESCE(SUM(IMPORTE), 0) AS total
            FROM MOVIMIENTOS_CONTRATOS
            WHERE CONTRATO_ID IS NULL
              AND SUBSTR(CUENTA_ID, 1, 2) IN ('62','64','68','69')
            """
            result = self.query_executor.execute_query(query, fetch_type="one")
        return float(result["total"]) if result else 0.0

    def _get_total_contratos_finalistas(self) -> int:
        """Total de contratos en centros finalistas (1-5). Denominador de redistribucion."""
        query = """
        SELECT COUNT(mc.CONTRATO_ID) AS total
        FROM MAESTRO_CONTRATOS mc
        JOIN MAESTRO_GESTORES g ON mc.GESTOR_ID = g.GESTOR_ID
        JOIN MAESTRO_CENTROS  c ON g.CENTRO     = c.CENTRO_ID
        WHERE c.IND_CENTRO_FINALISTA = 1
        """
        result = self.query_executor.execute_query(query, fetch_type="one")
        return int(result["total"]) if result and result["total"] else 1

    # =====================================
    # MÉTRICAS FINANCIERAS POR GESTOR
    # =====================================

    def get_gestor_metricas_completas(self, gestor_id: int, periodo: Optional[str] = None) -> Dict[str, Any]:
        """Métricas financieras completas de un gestor.

        Ingresos:              cuentas 76xxxx en MOVIMIENTOS_CONTRATOS.
        Gastos directos:       cuentas 62/64/68/69xxxx asociados a contratos del gestor.
        Gastos redistribuidos: gastos centrales (CONTRATO_ID IS NULL) x proporcion contratos.
        """
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, gestor_id) if periodo else (gestor_id,)

        query = f"""
        SELECT
            g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
            c.DESC_CENTRO, s.DESC_SEGMENTO,
            COUNT(DISTINCT mc.CONTRATO_ID)    AS total_contratos,
            COUNT(DISTINCT mc.CLIENTE_ID)     AS total_clientes,
            COUNT(DISTINCT mc.PRODUCTO_ID)    AS productos_diferentes,
            COUNT(DISTINCT mov.MOVIMIENTO_ID) AS total_movimientos,
            MIN(mc.FECHA_ALTA) AS fecha_primer_contrato,
            MAX(mc.FECHA_ALTA) AS fecha_ultimo_contrato,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_total,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos
        FROM MAESTRO_GESTORES g
        JOIN  MAESTRO_CENTROS   c  ON g.CENTRO      = c.CENTRO_ID
        JOIN  MAESTRO_SEGMENTOS s  ON g.SEGMENTO_ID = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_CONTRATOS     mc  ON g.GESTOR_ID    = mc.GESTOR_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            {periodo_filter}
        WHERE g.GESTOR_ID = ?
        GROUP BY g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO,
                 g.SEGMENTO_ID, c.DESC_CENTRO, s.DESC_SEGMENTO
        """
        result = self.query_executor.execute_query(query, params, fetch_type="one")
        if not result:
            return {}

        gastos_centrales = self._get_gastos_centrales_periodo(periodo)
        total_finalistas = self._get_total_contratos_finalistas()
        n_contratos      = result["total_contratos"]
        redistribuidos   = round(gastos_centrales * n_contratos / total_finalistas, 2)
        gastos_totales   = round(result["gastos_directos"] + redistribuidos, 2)
        ingresos         = result["ingresos_total"]
        beneficio        = round(ingresos + gastos_totales, 2)

        result.update({
            "gastos_redistribuidos": redistribuidos,
            "gastos_totales":        gastos_totales,
            "beneficio_neto":        beneficio,
            "margen_neto_pct":       round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
            "ingresos_por_contrato": round(ingresos / max(n_contratos, 1), 2),
            "ingresos_por_cliente":  round(ingresos / max(result["total_clientes"], 1), 2),
            "contratos_por_cliente": round(n_contratos / max(result["total_clientes"], 1), 1),
        })
        return result

    def get_gestor_clientes_con_metricas(self, gestor_id: int, periodo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Clientes del gestor con métricas financieras.
        Redistribucion proporcional al numero de contratos de cada cliente."""
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, gestor_id) if periodo else (gestor_id,)

        query = f"""
        SELECT
            cl.CLIENTE_ID, cl.NOMBRE_CLIENTE,
            COUNT(DISTINCT mc.CONTRATO_ID) AS num_contratos,
            COUNT(DISTINCT mc.PRODUCTO_ID) AS productos_diferentes,
            MIN(mc.FECHA_ALTA) AS fecha_alta_primer_contrato,
            MAX(mc.FECHA_ALTA) AS fecha_alta_ultimo_contrato,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_cliente,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos
        FROM MAESTRO_CLIENTES cl
        JOIN  MAESTRO_CONTRATOS     mc  ON cl.CLIENTE_ID   = mc.CLIENTE_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            {periodo_filter}
        WHERE mc.GESTOR_ID = ?
        GROUP BY cl.CLIENTE_ID, cl.NOMBRE_CLIENTE
        ORDER BY ingresos_cliente DESC
        """
        rows = self.query_executor.execute_query(query, params)
        if not rows:
            return []

        gastos_centrales = self._get_gastos_centrales_periodo(periodo)
        total_finalistas = self._get_total_contratos_finalistas()

        for row in rows:
            redistribuidos = round(gastos_centrales * row["num_contratos"] / total_finalistas, 2)
            ingresos       = row["ingresos_cliente"]
            gastos_totales = round(row["gastos_directos"] + redistribuidos, 2)
            beneficio      = round(ingresos + gastos_totales, 2)
            row.update({
                "gastos_redistribuidos": redistribuidos,
                "gastos_totales":        gastos_totales,
                "beneficio_neto":        beneficio,
                "margen_neto_pct":       round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
                "ingresos_por_contrato": round(ingresos / max(row["num_contratos"], 1), 2),
            })
        return rows

    # =====================================
    # MÉTRICAS FINANCIERAS POR CLIENTE
    # =====================================

    def get_cliente_metricas(self, cliente_id: int, periodo: Optional[str] = None) -> Dict[str, Any]:
        """Métricas financieras de un cliente específico."""
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, cliente_id) if periodo else (cliente_id,)

        query = f"""
        SELECT
            cl.CLIENTE_ID, cl.NOMBRE_CLIENTE, cl.GESTOR_ID,
            g.DESC_GESTOR,
            COUNT(DISTINCT mc.CONTRATO_ID) AS num_contratos,
            COUNT(DISTINCT mc.PRODUCTO_ID) AS productos_diferentes,
            MIN(mc.FECHA_ALTA) AS fecha_alta_primer_contrato,
            MAX(mc.FECHA_ALTA) AS fecha_alta_ultimo_contrato,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_total,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos
        FROM MAESTRO_CLIENTES cl
        LEFT JOIN MAESTRO_GESTORES      g   ON cl.GESTOR_ID  = g.GESTOR_ID
        LEFT JOIN MAESTRO_CONTRATOS     mc  ON cl.CLIENTE_ID = mc.CLIENTE_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            {periodo_filter}
        WHERE cl.CLIENTE_ID = ?
        GROUP BY cl.CLIENTE_ID, cl.NOMBRE_CLIENTE, cl.GESTOR_ID, g.DESC_GESTOR
        """
        result = self.query_executor.execute_query(query, params, fetch_type="one")

        if result and result.get("num_contratos"):
            gastos_centrales = self._get_gastos_centrales_periodo(periodo)
            total_finalistas = self._get_total_contratos_finalistas()
            n_contratos      = result["num_contratos"]
            redistribuidos   = round(gastos_centrales * n_contratos / total_finalistas, 2)
            ingresos         = result["ingresos_total"]
            gastos_totales   = round(result["gastos_directos"] + redistribuidos, 2)
            beneficio        = round(ingresos + gastos_totales, 2)
            result.update({
                "gastos_redistribuidos": redistribuidos,
                "gastos_totales":        gastos_totales,
                "beneficio_neto":        beneficio,
                "margen_neto_pct":       round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
                "valor_por_contrato":    round(beneficio / max(n_contratos, 1), 2),
            })
            return result

        # Cliente sin contratos o sin movimientos en el período
        query_base = """
        SELECT cl.CLIENTE_ID, cl.NOMBRE_CLIENTE, cl.GESTOR_ID, g.DESC_GESTOR
        FROM MAESTRO_CLIENTES cl
        LEFT JOIN MAESTRO_GESTORES g ON cl.GESTOR_ID = g.GESTOR_ID
        WHERE cl.CLIENTE_ID = ?
        """
        base = self.query_executor.execute_query(query_base, (cliente_id,), fetch_type="one")
        if base:
            return {**base, "num_contratos": 0, "ingresos_total": 0, "gastos_directos": 0,
                    "gastos_redistribuidos": 0, "gastos_totales": 0, "beneficio_neto": 0,
                    "margen_neto_pct": 0, "valor_por_contrato": 0,
                    "nota": "Cliente sin contratos activos en el periodo"}
        return {"error": "Cliente no encontrado", "CLIENTE_ID": cliente_id}

    def get_cliente_contratos_con_metricas(self, cliente_id: int, periodo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Contratos de un cliente con métricas financieras.
        Cada contrato recibe 1/total_finalistas de los gastos centrales del período."""
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, cliente_id) if periodo else (cliente_id,)

        query = f"""
        SELECT
            mc.CONTRATO_ID, mc.FECHA_ALTA, mc.PRODUCTO_ID,
            p.DESC_PRODUCTO,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_contrato,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos,
            COUNT(DISTINCT mov.MOVIMIENTO_ID) AS num_movimientos
        FROM MAESTRO_CONTRATOS mc
        LEFT JOIN MAESTRO_PRODUCTOS     p   ON mc.PRODUCTO_ID  = p.PRODUCTO_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID  = mov.CONTRATO_ID
            {periodo_filter}
        WHERE mc.CLIENTE_ID = ?
        GROUP BY mc.CONTRATO_ID, mc.FECHA_ALTA, mc.PRODUCTO_ID, p.DESC_PRODUCTO
        ORDER BY mc.FECHA_ALTA DESC
        """
        rows = self.query_executor.execute_query(query, params)
        if not rows:
            return []

        gastos_centrales  = self._get_gastos_centrales_periodo(periodo)
        total_finalistas  = self._get_total_contratos_finalistas()
        redistribuido_uno = round(gastos_centrales / total_finalistas, 2)

        for row in rows:
            ingresos       = row["ingresos_contrato"]
            gastos_totales = round(row["gastos_directos"] + redistribuido_uno, 2)
            beneficio      = round(ingresos + gastos_totales, 2)
            row.update({
                "gastos_redistribuidos": redistribuido_uno,
                "gastos_totales":        gastos_totales,
                "beneficio_neto":        beneficio,
                "margen_neto_pct":       round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
            })
        return rows

    # =====================================
    # MÉTRICAS FINANCIERAS POR CONTRATO
    # =====================================

    def get_contrato_detalle_completo(self, contrato_id: int, periodo: Optional[str] = None) -> Dict[str, Any]:
        """Detalle completo de un contrato con métricas financieras."""
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, contrato_id) if periodo else (contrato_id,)

        query = f"""
        SELECT
            mc.CONTRATO_ID, mc.FECHA_ALTA, mc.CLIENTE_ID, mc.GESTOR_ID,
            mc.PRODUCTO_ID, mc.CENTRO_CONTABLE,
            cl.NOMBRE_CLIENTE, g.DESC_GESTOR, p.DESC_PRODUCTO, c.DESC_CENTRO,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_total,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos,
            COUNT(DISTINCT mov.MOVIMIENTO_ID) AS num_movimientos,
            MIN(mov.FECHA) AS fecha_primer_movimiento,
            MAX(mov.FECHA) AS fecha_ultimo_movimiento
        FROM MAESTRO_CONTRATOS mc
        LEFT JOIN MAESTRO_CLIENTES      cl  ON mc.CLIENTE_ID      = cl.CLIENTE_ID
        LEFT JOIN MAESTRO_GESTORES      g   ON mc.GESTOR_ID       = g.GESTOR_ID
        LEFT JOIN MAESTRO_PRODUCTOS     p   ON mc.PRODUCTO_ID     = p.PRODUCTO_ID
        LEFT JOIN MAESTRO_CENTROS       c   ON mc.CENTRO_CONTABLE = c.CENTRO_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID     = mov.CONTRATO_ID
            {periodo_filter}
        WHERE mc.CONTRATO_ID = ?
        GROUP BY mc.CONTRATO_ID, mc.FECHA_ALTA, mc.CLIENTE_ID, mc.GESTOR_ID,
                 mc.PRODUCTO_ID, mc.CENTRO_CONTABLE, cl.NOMBRE_CLIENTE,
                 g.DESC_GESTOR, p.DESC_PRODUCTO, c.DESC_CENTRO
        """
        result = self.query_executor.execute_query(query, params, fetch_type="one")
        if not result:
            return {}

        gastos_centrales = self._get_gastos_centrales_periodo(periodo)
        total_finalistas = self._get_total_contratos_finalistas()
        redistribuidos   = round(gastos_centrales / total_finalistas, 2)
        ingresos         = result["ingresos_total"]
        gastos_totales   = round(result["gastos_directos"] + redistribuidos, 2)
        beneficio        = round(ingresos + gastos_totales, 2)

        result.update({
            "gastos_redistribuidos":    redistribuidos,
            "gastos_totales":           gastos_totales,
            "beneficio_neto":           beneficio,
            "margen_neto_pct":          round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
            "promedio_por_movimiento":  round(ingresos / max(result["num_movimientos"], 1), 2),
        })
        return result

    # =====================================
    # MÉTRICAS FINANCIERAS POR CENTRO
    # =====================================

    def get_centro_metricas_financieras(self, centro_id: int, periodo: Optional[str] = None) -> Dict[str, Any]:
        """Métricas financieras de un centro. Redistribucion proporcional a contratos del centro."""
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, centro_id) if periodo else (centro_id,)

        query = f"""
        SELECT
            c.CENTRO_ID, c.DESC_CENTRO, c.IND_CENTRO_FINALISTA,
            COUNT(DISTINCT g.GESTOR_ID)    AS total_gestores,
            COUNT(DISTINCT mc.CLIENTE_ID)  AS total_clientes,
            COUNT(DISTINCT mc.CONTRATO_ID) AS total_contratos,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_total,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos
        FROM MAESTRO_CENTROS c
        LEFT JOIN MAESTRO_GESTORES      g   ON c.CENTRO_ID    = g.CENTRO
        LEFT JOIN MAESTRO_CONTRATOS     mc  ON g.GESTOR_ID    = mc.GESTOR_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            {periodo_filter}
        WHERE c.CENTRO_ID = ?
        GROUP BY c.CENTRO_ID, c.DESC_CENTRO, c.IND_CENTRO_FINALISTA
        """
        result = self.query_executor.execute_query(query, params, fetch_type="one")
        if not result:
            return {}

        gastos_centrales = self._get_gastos_centrales_periodo(periodo)
        total_finalistas = self._get_total_contratos_finalistas()
        n_contratos      = result["total_contratos"]
        redistribuidos   = round(gastos_centrales * n_contratos / total_finalistas, 2)
        gastos_totales   = round(result["gastos_directos"] + redistribuidos, 2)
        ingresos         = result["ingresos_total"]
        beneficio        = round(ingresos + gastos_totales, 2)

        result.update({
            "gastos_redistribuidos": redistribuidos,
            "gastos_totales":        gastos_totales,
            "beneficio_neto":        beneficio,
            "margen_neto_pct":       round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
            "contratos_por_gestor":  round(n_contratos / max(result["total_gestores"], 1), 1),
            "clientes_por_gestor":   round(result["total_clientes"] / max(result["total_gestores"], 1), 1),
        })
        return result

    def get_centro_gestores_con_metricas(self, centro_id: int, periodo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Gestores de un centro con métricas financieras."""
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, centro_id) if periodo else (centro_id,)

        query = f"""
        SELECT
            g.GESTOR_ID, g.DESC_GESTOR, g.SEGMENTO_ID, s.DESC_SEGMENTO,
            COUNT(DISTINCT mc.CONTRATO_ID) AS num_contratos,
            COUNT(DISTINCT mc.CLIENTE_ID)  AS num_clientes,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_gestor,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_SEGMENTOS     s   ON g.SEGMENTO_ID  = s.SEGMENTO_ID
        LEFT JOIN MAESTRO_CONTRATOS     mc  ON g.GESTOR_ID    = mc.GESTOR_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            {periodo_filter}
        WHERE g.CENTRO = ?
        GROUP BY g.GESTOR_ID, g.DESC_GESTOR, g.SEGMENTO_ID, s.DESC_SEGMENTO
        ORDER BY ingresos_gestor DESC
        """
        rows = self.query_executor.execute_query(query, params)
        if not rows:
            return []

        gastos_centrales = self._get_gastos_centrales_periodo(periodo)
        total_finalistas = self._get_total_contratos_finalistas()

        for row in rows:
            redistribuidos = round(gastos_centrales * row["num_contratos"] / total_finalistas, 2)
            ingresos       = row["ingresos_gestor"]
            gastos_totales = round(row["gastos_directos"] + redistribuidos, 2)
            beneficio      = round(ingresos + gastos_totales, 2)
            row.update({
                "gastos_redistribuidos": redistribuidos,
                "gastos_totales":        gastos_totales,
                "beneficio_neto":        beneficio,
                "margen_neto_pct":       round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
                "ingresos_por_contrato": round(ingresos / max(row["num_contratos"], 1), 2),
                "ingresos_por_cliente":  round(ingresos / max(row["num_clientes"], 1), 2),
            })
        return rows

    # =====================================
    # MÉTRICAS FINANCIERAS POR SEGMENTO
    # =====================================

    def get_segmento_metricas_financieras(self, segmento_id: str, periodo: Optional[str] = None) -> Dict[str, Any]:
        """Métricas financieras de un segmento."""
        periodo_filter = "AND strftime('%Y-%m', mov.FECHA) = ?" if periodo else ""
        params = (periodo, segmento_id) if periodo else (segmento_id,)

        query = f"""
        SELECT
            s.SEGMENTO_ID, s.DESC_SEGMENTO,
            COUNT(DISTINCT g.GESTOR_ID)    AS total_gestores,
            COUNT(DISTINCT mc.CLIENTE_ID)  AS total_clientes,
            COUNT(DISTINCT mc.CONTRATO_ID) AS total_contratos,
            COUNT(DISTINCT mc.PRODUCTO_ID) AS productos_diferentes,
            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%'
                              THEN mov.IMPORTE ELSE 0 END), 0) AS ingresos_total,
            COALESCE(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID, 1, 2) IN ('62','64','68','69')
                              THEN mov.IMPORTE ELSE 0 END), 0) AS gastos_directos
        FROM MAESTRO_SEGMENTOS s
        LEFT JOIN MAESTRO_GESTORES      g   ON s.SEGMENTO_ID  = g.SEGMENTO_ID
        LEFT JOIN MAESTRO_CONTRATOS     mc  ON g.GESTOR_ID    = mc.GESTOR_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            {periodo_filter}
        WHERE s.SEGMENTO_ID = ?
        GROUP BY s.SEGMENTO_ID, s.DESC_SEGMENTO
        """
        result = self.query_executor.execute_query(query, params, fetch_type="one")
        if not result:
            return {}

        gastos_centrales = self._get_gastos_centrales_periodo(periodo)
        total_finalistas = self._get_total_contratos_finalistas()
        n_contratos      = result["total_contratos"]
        redistribuidos   = round(gastos_centrales * n_contratos / total_finalistas, 2)
        gastos_totales   = round(result["gastos_directos"] + redistribuidos, 2)
        ingresos         = result["ingresos_total"]
        beneficio        = round(ingresos + gastos_totales, 2)

        result.update({
            "gastos_redistribuidos": redistribuidos,
            "gastos_totales":        gastos_totales,
            "beneficio_neto":        beneficio,
            "margen_neto_pct":       round(beneficio / ingresos * 100, 2) if ingresos else 0.0,
            "ingresos_por_gestor":   round(ingresos / max(result["total_gestores"], 1), 2),
            "contratos_por_gestor":  round(n_contratos / max(result["total_gestores"], 1), 1),
        })
        return result

    # =====================================
    # CONSULTAS DE MOVIMIENTOS
    # =====================================
    
    def get_movimientos_by_contrato(self, contrato_id: int) -> List[Dict[str, Any]]:
        """Obtiene movimientos de un contrato específico"""
        query = """
        SELECT MOVIMIENTO_ID, EMPRESA_ID, FECHA, CONTRATO_ID, CENTRO_CONTABLE,
               CUENTA_ID, DIVISA, IMPORTE, LINEA_CUENTA_RESULTADOS, CONCEPTO_GESTION
        FROM MOVIMIENTOS_CONTRATOS
        WHERE CONTRATO_ID = ?
        ORDER BY FECHA DESC
        """
        return self.query_executor.execute_query(query, (contrato_id,))
    
    def get_movimientos_by_fecha(self, fecha: str) -> List[Dict[str, Any]]:
        """Obtiene movimientos de una fecha específica"""
        query = """
        SELECT MOVIMIENTO_ID, EMPRESA_ID, FECHA, CONTRATO_ID, CENTRO_CONTABLE,
               CUENTA_ID, DIVISA, IMPORTE, LINEA_CUENTA_RESULTADOS, CONCEPTO_GESTION
        FROM MOVIMIENTOS_CONTRATOS
        WHERE FECHA = ?
        ORDER BY MOVIMIENTO_ID
        """
        return self.query_executor.execute_query(query, (fecha,))
    
    def get_movimientos_by_gestor(self, gestor_id: int, fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict[str, Any]]:
        """Obtiene movimientos de contratos de un gestor específico"""
        base_query = """
        SELECT mc.MOVIMIENTO_ID, mc.FECHA, mc.CONTRATO_ID, mc.CUENTA_ID, 
               mc.IMPORTE, mc.LINEA_CUENTA_RESULTADOS, mc.CONCEPTO_GESTION,
               co.CLIENTE_ID, cl.NOMBRE_CLIENTE
        FROM MOVIMIENTOS_CONTRATOS mc
        JOIN MAESTRO_CONTRATOS co ON mc.CONTRATO_ID = co.CONTRATO_ID
        JOIN MAESTRO_CLIENTES cl ON co.CLIENTE_ID = cl.CLIENTE_ID
        WHERE co.GESTOR_ID = ?
        """
        
        params = [gestor_id]
        if fecha_inicio:
            base_query += " AND mc.FECHA >= ?"
            params.append(fecha_inicio)
        if fecha_fin:
            base_query += " AND mc.FECHA <= ?"
            params.append(fecha_fin)
            
        base_query += " ORDER BY mc.FECHA DESC"
        
        return self.query_executor.execute_query(base_query, tuple(params))
    
    # =====================================
    # CONSULTAS AGREGADAS Y ESTADÍSTICAS
    # =====================================
    
    def get_resumen_general(self) -> Dict[str, Any]:
        """Obtiene un resumen general del sistema"""
        queries = {
            'total_centros': "SELECT COUNT(*) as count FROM MAESTRO_CENTROS",
            'centros_finalistas': "SELECT COUNT(*) as count FROM MAESTRO_CENTROS WHERE IND_CENTRO_FINALISTA = 1",
            'total_gestores': "SELECT COUNT(*) as count FROM MAESTRO_GESTORES",
            'total_clientes': "SELECT COUNT(*) as count FROM MAESTRO_CLIENTES",
            'total_productos': "SELECT COUNT(*) as count FROM MAESTRO_PRODUCTOS",
            'total_contratos': "SELECT COUNT(*) as count FROM MAESTRO_CONTRATOS",
            'total_segmentos': "SELECT COUNT(*) as count FROM MAESTRO_SEGMENTOS"
        }
        
        resumen = {}
        for key, query in queries.items():
            result = self.query_executor.execute_query(query, fetch_type="one")
            resumen[key] = result['count'] if result else 0
        
        logger.info(f"✅ Resumen general generado: {len(resumen)} métricas")
        return resumen
    
    def get_ranking_gestores_por_contratos(self) -> List[Dict[str, Any]]:
        """Obtiene ranking de gestores por número de contratos"""
        query = """
        SELECT g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
               c.DESC_CENTRO, s.DESC_SEGMENTO,
               COUNT(co.CONTRATO_ID) as num_contratos
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CONTRATOS co ON g.GESTOR_ID = co.GESTOR_ID
        LEFT JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
        LEFT JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
        GROUP BY g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID, c.DESC_CENTRO, s.DESC_SEGMENTO
        ORDER BY num_contratos DESC
        """
        return self.query_executor.execute_query(query)
    
    def get_productos_mas_contratados(self) -> List[Dict[str, Any]]:
        """Obtiene ranking de productos más contratados"""
        query = """
        SELECT p.PRODUCTO_ID, p.DESC_PRODUCTO, p.IND_FABRICA,
               COUNT(co.CONTRATO_ID) as num_contratos
        FROM MAESTRO_PRODUCTOS p
        LEFT JOIN MAESTRO_CONTRATOS co ON p.PRODUCTO_ID = co.PRODUCTO_ID
        GROUP BY p.PRODUCTO_ID, p.DESC_PRODUCTO, p.IND_FABRICA
        ORDER BY num_contratos DESC
        """
        return self.query_executor.execute_query(query)
    
    # =====================================
    # ANÁLISIS CON PANDAS
    # =====================================
    
    def get_dataframe_movimientos(self, fecha_inicio: str = None, fecha_fin: str = None) -> pd.DataFrame:
        """Obtiene DataFrame de movimientos para análisis avanzado"""
        base_query = """
        SELECT mc.*, co.GESTOR_ID, co.CLIENTE_ID, co.PRODUCTO_ID,
               g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
               cl.NOMBRE_CLIENTE, p.DESC_PRODUCTO
        FROM MOVIMIENTOS_CONTRATOS mc
        LEFT JOIN MAESTRO_CONTRATOS co ON mc.CONTRATO_ID = co.CONTRATO_ID
        LEFT JOIN MAESTRO_GESTORES g ON co.GESTOR_ID = g.GESTOR_ID
        LEFT JOIN MAESTRO_CLIENTES cl ON co.CLIENTE_ID = cl.CLIENTE_ID
        LEFT JOIN MAESTRO_PRODUCTOS p ON co.PRODUCTO_ID = p.PRODUCTO_ID
        """
        
        params = []
        if fecha_inicio or fecha_fin:
            conditions = []
            if fecha_inicio:
                conditions.append("mc.FECHA >= ?")
                params.append(fecha_inicio)
            if fecha_fin:
                conditions.append("mc.FECHA <= ?")
                params.append(fecha_fin)
            base_query += " WHERE " + " AND ".join(conditions)
            
        base_query += " ORDER BY mc.FECHA DESC"
        
        return self.query_executor.execute_pandas_query(base_query, tuple(params) if params else None)

# Instancia global para uso en toda la aplicación
basic_queries = BasicQueries()

# Funciones de conveniencia para importación fácil
def get_all_centros(): return basic_queries.get_all_centros()
def get_centros_finalistas(): return basic_queries.get_centros_finalistas()
def get_centros_no_finalistas(): return basic_queries.get_centros_no_finalistas()
def get_all_gestores(): return basic_queries.get_all_gestores()
def get_gestores_by_centro(centro_id): return basic_queries.get_gestores_by_centro(centro_id)
def get_gestores_by_segmento(segmento_id): return basic_queries.get_gestores_by_segmento(segmento_id)
def get_all_productos(): return basic_queries.get_all_productos()
def get_all_clientes(): return basic_queries.get_all_clientes()
def get_clientes_by_gestor(gestor_id): return basic_queries.get_clientes_by_gestor(gestor_id)
def get_all_contratos(): return basic_queries.get_all_contratos()
def get_contratos_by_gestor(gestor_id): return basic_queries.get_contratos_by_gestor(gestor_id)
def get_all_precios_std(): return basic_queries.get_all_precios_std()
def get_all_precios_real(): return basic_queries.get_all_precios_real()
def compare_precios_std_vs_real(fecha=None): return basic_queries.compare_precios_std_vs_real(fecha)
def get_resumen_general(): return basic_queries.get_resumen_general()

# Funciones de conveniencia para métricas financieras
def get_centro_metricas(centro_id, periodo=None): return basic_queries.get_centro_metricas_financieras(centro_id, periodo)
def get_centro_gestores_metricas(centro_id, periodo=None): return basic_queries.get_centro_gestores_con_metricas(centro_id, periodo)
def get_segmento_metricas(segmento_id, periodo=None): return basic_queries.get_segmento_metricas_financieras(segmento_id, periodo)
def get_gestor_metricas_completas(gestor_id, periodo=None): return basic_queries.get_gestor_metricas_completas(gestor_id, periodo)
def get_gestor_clientes_metricas(gestor_id, periodo=None): return basic_queries.get_gestor_clientes_con_metricas(gestor_id, periodo)
def get_cliente_metricas(cliente_id, periodo=None): return basic_queries.get_cliente_metricas(cliente_id, periodo)
def get_cliente_contratos_metricas(cliente_id, periodo=None): return basic_queries.get_cliente_contratos_con_metricas(cliente_id, periodo)
def get_contrato_detalle(contrato_id): return basic_queries.get_contrato_detalle_completo(contrato_id)

if __name__ == "__main__":
    # Ejemplo de uso
    try:
        print("=== RESUMEN GENERAL ===")
        resumen = get_resumen_general()
        for key, value in resumen.items():
            print(f"{key}: {value}")
        
        print("\n=== CENTROS FINALISTAS ===")
        centros = get_centros_finalistas()
        for centro in centros:
            print(f"Centro {centro['CENTRO_ID']}: {centro['DESC_CENTRO']}")
        
        print("\n=== TOP 5 GESTORES POR CONTRATOS ===")
        ranking = basic_queries.get_ranking_gestores_por_contratos()[:5]
        for gestor in ranking:
            print(f"{gestor['DESC_GESTOR']}: {gestor['num_contratos']} contratos")
            
        logger.info("✅ Ejemplo de uso ejecutado correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error en ejemplo de uso: {e}")
        print(f"Error: {e}")
