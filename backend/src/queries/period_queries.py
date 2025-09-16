"""
period_queries.py - ENHANCED VERSION

Biblioteca de consultas para manejo de períodos temporales
INTEGRADO con kpi_calculator.py y estructura QueryResult estándar
✅ CORREGIDO: Lógica de gastos usando PRECIO_POR_PRODUCTO_REAL
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from database.db_connection import execute_query
    from tools.kpi_calculator import FinancialKPICalculator
except ImportError:
    from ..database.db_connection import execute_query
    from ..tools.kpi_calculator import FinancialKPICalculator

logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Resultado de una consulta con metadatos"""
    data: List[Dict]
    query_type: str
    execution_time: float
    row_count: int
    query_sql: str

class PeriodQueries:
    """
    Biblioteca de consultas para manejo de períodos temporales
    INTEGRADO con kpi_calculator.py para análisis temporal
    ✅ CORREGIDO: Lógica de gastos usando PRECIO_POR_PRODUCTO_REAL
    """
    def __init__(self):
        self.kpi_calc = FinancialKPICalculator()

    def get_available_periods_enhanced(self) -> QueryResult:
        """
        ✅ VERSIÓN ENHANCED - Obtiene períodos disponibles con análisis dinámico
        """
        query = """
            SELECT DISTINCT 
                strftime('%Y-%m', FECHA) as periodo,
                COUNT(*) as num_movimientos,
                MIN(FECHA) as fecha_inicio,
                MAX(FECHA) as fecha_fin
            FROM MOVIMIENTOS_CONTRATOS
            WHERE FECHA IS NOT NULL
            GROUP BY strftime('%Y-%m', FECHA)
            ORDER BY periodo DESC
        """
        start_time = datetime.now()
        results = execute_query(query) or []
        execution_time = (datetime.now() - start_time).total_seconds()

        # Determinar periodo actual y anterior de forma dinámica
        periodos_ordenados = sorted(
            (r for r in results if r.get("periodo")),
            key=lambda r: r["periodo"],
            reverse=True
        )
        periodo_actual = periodos_ordenados[0]["periodo"] if periodos_ordenados else None
        periodo_anterior = periodos_ordenados[1]["periodo"] if len(periodos_ordenados) > 1 else None

        enhanced_results = []
        for row in results:
            p = row.get("periodo")
            enhanced_results.append({
                'periodo': p,
                'num_movimientos': row.get('num_movimientos', 0),
                'fecha_inicio': row.get('fecha_inicio'),
                'fecha_fin': row.get('fecha_fin'),
                'es_periodo_actual': (p == periodo_actual),
                'es_periodo_anterior': (p == periodo_anterior)
            })

        return QueryResult(
            data=enhanced_results,
            query_type="available_periods_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )

    def get_latest_period_enhanced(self) -> QueryResult:
        """
        ✅ VERSIÓN ENHANCED - Obtiene período más reciente con contexto
        """
        periods_result = self.get_available_periods_enhanced()
        if not periods_result.data:
            return QueryResult(
                data=[],
                query_type="latest_period_enhanced_empty",
                execution_time=periods_result.execution_time,
                row_count=0,
                query_sql=periods_result.query_sql
            )

        latest = next((r for r in periods_result.data if r.get('es_periodo_actual')), periods_result.data[0])
        return QueryResult(
            data=[latest],
            query_type="latest_period_enhanced",
            execution_time=periods_result.execution_time,
            row_count=1,
            query_sql=periods_result.query_sql
        )
        
    # =====================================
    # ANÁLISIS TEMPORAL DE MÉTRICAS
    # =====================================
    
    def get_periodo_metricas_financieras(self, periodo: str) -> QueryResult:
        """
        ✅ Obtiene métricas financieras agregadas para un período específico
        ✅ CORREGIDO: Gastos calculados usando PRECIO_POR_PRODUCTO_REAL
        """
        # Convertir periodo a formato FECHA_CALCULO
        fecha_calculo = f"{periodo}-01"
        
        query = """
        SELECT 
            ? as periodo,
            COUNT(DISTINCT g.GESTOR_ID) as total_gestores_activos,
            COUNT(DISTINCT co.CLIENTE_ID) as total_clientes_activos,
            COUNT(DISTINCT co.CONTRATO_ID) as total_contratos_activos,
            -- INGRESOS: Suma de movimientos positivos
            COALESCE(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_periodo,
            -- ✅ GASTOS CORREGIDOS: Usar PRECIO_POR_PRODUCTO_REAL
            COALESCE(SUM(ABS(p.PRECIO_MANTENIMIENTO_REAL)), 0) as gastos_periodo,
            -- GASTOS CENTROS (mantener lógica original para gastos centrales)
            COALESCE(SUM(gc.IMPORTE), 0) as gastos_centros_periodo,
            COUNT(DISTINCT mov.MOVIMIENTO_ID) as total_movimientos
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CONTRATOS co ON g.GESTOR_ID = co.GESTOR_ID
        LEFT JOIN PRECIO_POR_PRODUCTO_REAL p ON g.SEGMENTO_ID = p.SEGMENTO_ID
                                              AND co.PRODUCTO_ID = p.PRODUCTO_ID
                                              AND p.FECHA_CALCULO = ?
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON co.CONTRATO_ID = mov.CONTRATO_ID
            AND strftime('%Y-%m', mov.FECHA) = ?
        LEFT JOIN GASTOS_CENTRO gc ON strftime('%Y-%m', gc.FECHA) = ?
        """
        
        start_time = datetime.now()
        result = execute_query(query, (periodo, fecha_calculo, periodo, periodo), fetch_type="one")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result:
            ingresos = result['ingresos_periodo'] or 0
            gastos_productos = result['gastos_periodo'] or 0  # Gastos de productos usando precios reales
            gastos_centros = result['gastos_centros_periodo'] or 0  # Gastos centrales
            gastos_totales = gastos_productos + gastos_centros
            beneficio = ingresos - gastos_totales
            
            result.update({
                'gastos_productos': gastos_productos,
                'gastos_centros': gastos_centros,
                'gastos_totales': gastos_totales,
                'beneficio_neto': beneficio,
                'margen_neto_pct': round((beneficio / ingresos * 100), 2) if ingresos > 0 else 0,
                'promedio_ingresos_por_gestor': round(ingresos / max(result['total_gestores_activos'], 1), 2),
                'promedio_contratos_por_gestor': round(result['total_contratos_activos'] / max(result['total_gestores_activos'], 1), 1)
            })
        
        return QueryResult(
            data=[result] if result else [],
            query_type="periodo_metricas_financieras",
            execution_time=execution_time,
            row_count=1 if result else 0,
            query_sql=query
        )
    
    def compare_periodos_metricas(self, periodo_actual: str, periodo_anterior: str) -> QueryResult:
        """
        ✅ Compara métricas financieras entre dos períodos
        ✅ CORREGIDO: Usa métricas corregidas con PRECIO_POR_PRODUCTO_REAL
        """
        start_time = datetime.now()
        
        # Obtener métricas de ambos períodos
        metricas_actual = self.get_periodo_metricas_financieras(periodo_actual)
        metricas_anterior = self.get_periodo_metricas_financieras(periodo_anterior)
        
        if not metricas_actual.data or not metricas_anterior.data:
            return QueryResult(
                data=[],
                query_type="compare_periodos_metricas_empty",
                execution_time=0,
                row_count=0,
                query_sql="-- No data available for comparison"
            )
        
        actual = metricas_actual.data[0]
        anterior = metricas_anterior.data[0]
        
        # Calcular variaciones
        comparacion = {
            'periodo_actual': periodo_actual,
            'periodo_anterior': periodo_anterior,
            'ingresos_actual': actual['ingresos_periodo'],
            'ingresos_anterior': anterior['ingresos_periodo'],
            'ingresos_variacion_abs': actual['ingresos_periodo'] - anterior['ingresos_periodo'],
            'ingresos_variacion_pct': round(((actual['ingresos_periodo'] - anterior['ingresos_periodo']) / max(anterior['ingresos_periodo'], 1) * 100), 2),
            'gastos_productos_actual': actual['gastos_productos'],
            'gastos_productos_anterior': anterior['gastos_productos'],
            'gastos_productos_variacion_abs': actual['gastos_productos'] - anterior['gastos_productos'],
            'gastos_productos_variacion_pct': round(((actual['gastos_productos'] - anterior['gastos_productos']) / max(anterior['gastos_productos'], 1) * 100), 2),
            'beneficio_actual': actual['beneficio_neto'],
            'beneficio_anterior': anterior['beneficio_neto'],
            'beneficio_variacion_abs': actual['beneficio_neto'] - anterior['beneficio_neto'],
            'beneficio_variacion_pct': round(((actual['beneficio_neto'] - anterior['beneficio_neto']) / max(abs(anterior['beneficio_neto']), 1) * 100), 2),
            'contratos_actual': actual['total_contratos_activos'],
            'contratos_anterior': anterior['total_contratos_activos'],
            'contratos_variacion': actual['total_contratos_activos'] - anterior['total_contratos_activos'],
            'gestores_actual': actual['total_gestores_activos'],
            'gestores_anterior': anterior['total_gestores_activos'],
            'margen_neto_actual': actual['margen_neto_pct'],
            'margen_neto_anterior': anterior['margen_neto_pct'],
            'margen_neto_variacion_pp': round(actual['margen_neto_pct'] - anterior['margen_neto_pct'], 2)
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=[comparacion],
            query_type="compare_periodos_metricas",
            execution_time=execution_time,
            row_count=1,
            query_sql="-- Comparison of two periods with corrected cost logic"
        )

    def get_periodo_analisis_gastos(self, periodo: str) -> QueryResult:
        """
        ✅ NUEVO: Análisis detallado de gastos por período usando PRECIO_POR_PRODUCTO_REAL
        """
        # Convertir periodo a formato FECHA_CALCULO
        fecha_calculo = f"{periodo}-01"
        
        query = """
        WITH gastos_por_segmento AS (
            SELECT
                s.SEGMENTO_ID,
                s.DESC_SEGMENTO,
                COUNT(DISTINCT g.GESTOR_ID) as gestores_segmento,
                COUNT(DISTINCT co.CONTRATO_ID) as contratos_segmento,
                COALESCE(SUM(ABS(p.PRECIO_MANTENIMIENTO_REAL)), 0) as gastos_segmento
            FROM MAESTRO_SEGMENTOS s
            LEFT JOIN MAESTRO_GESTORES g ON s.SEGMENTO_ID = g.SEGMENTO_ID
            LEFT JOIN MAESTRO_CONTRATOS co ON g.GESTOR_ID = co.GESTOR_ID
            LEFT JOIN PRECIO_POR_PRODUCTO_REAL p ON s.SEGMENTO_ID = p.SEGMENTO_ID
                                                  AND co.PRODUCTO_ID = p.PRODUCTO_ID
                                                  AND p.FECHA_CALCULO = ?
            GROUP BY s.SEGMENTO_ID, s.DESC_SEGMENTO
        ),
        gastos_por_producto AS (
            SELECT
                pr.PRODUCTO_ID,
                pr.DESC_PRODUCTO,
                COUNT(DISTINCT co.CONTRATO_ID) as contratos_producto,
                COALESCE(SUM(ABS(p.PRECIO_MANTENIMIENTO_REAL)), 0) as gastos_producto
            FROM MAESTRO_PRODUCTOS pr
            LEFT JOIN MAESTRO_CONTRATOS co ON pr.PRODUCTO_ID = co.PRODUCTO_ID
            LEFT JOIN MAESTRO_GESTORES g ON co.GESTOR_ID = g.GESTOR_ID
            LEFT JOIN PRECIO_POR_PRODUCTO_REAL p ON g.SEGMENTO_ID = p.SEGMENTO_ID
                                                  AND pr.PRODUCTO_ID = p.PRODUCTO_ID
                                                  AND p.FECHA_CALCULO = ?
            GROUP BY pr.PRODUCTO_ID, pr.DESC_PRODUCTO
        )
        SELECT
            ? as periodo,
            'RESUMEN' as tipo_analisis,
            (SELECT SUM(gastos_segmento) FROM gastos_por_segmento) as total_gastos,
            (SELECT COUNT(*) FROM gastos_por_segmento WHERE gastos_segmento > 0) as segmentos_con_gastos,
            (SELECT COUNT(*) FROM gastos_por_producto WHERE gastos_producto > 0) as productos_con_gastos
        UNION ALL
        SELECT
            ? as periodo,
            'SEGMENTO' as tipo_analisis,
            gastos_segmento as total_gastos,
            gestores_segmento as segmentos_con_gastos,
            contratos_segmento as productos_con_gastos,
            SEGMENTO_ID as detalle_id,
            DESC_SEGMENTO as detalle_desc
        FROM gastos_por_segmento
        WHERE gastos_segmento > 0
        ORDER BY total_gastos DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (fecha_calculo, fecha_calculo, periodo, periodo))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results or [],
            query_type="periodo_analisis_gastos",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

    def get_periodo_evolucion_gastos(self, periodo_inicio: str, periodo_fin: str) -> QueryResult:
        """
        ✅ NUEVO: Evolución de gastos por rango de períodos usando PRECIO_POR_PRODUCTO_REAL
        """
        query = """
        WITH gastos_mensuales AS (
            SELECT
                strftime('%Y-%m', p.FECHA_CALCULO) as periodo,
                COUNT(DISTINCT co.CONTRATO_ID) as contratos_activos,
                COALESCE(SUM(ABS(p.PRECIO_MANTENIMIENTO_REAL)), 0) as gastos_periodo
            FROM PRECIO_POR_PRODUCTO_REAL p
            JOIN MAESTRO_CONTRATOS co ON p.PRODUCTO_ID = co.PRODUCTO_ID
            JOIN MAESTRO_GESTORES g ON co.GESTOR_ID = g.GESTOR_ID
                                    AND p.SEGMENTO_ID = g.SEGMENTO_ID
            WHERE strftime('%Y-%m', p.FECHA_CALCULO) >= ?
              AND strftime('%Y-%m', p.FECHA_CALCULO) <= ?
            GROUP BY strftime('%Y-%m', p.FECHA_CALCULO)
        )
        SELECT
            periodo,
            contratos_activos,
            gastos_periodo,
            ROUND(gastos_periodo / NULLIF(contratos_activos, 0), 2) as gasto_unitario,
            LAG(gastos_periodo) OVER (ORDER BY periodo) as gastos_periodo_anterior,
            ROUND(
                ((gastos_periodo - LAG(gastos_periodo) OVER (ORDER BY periodo)) 
                / NULLIF(LAG(gastos_periodo) OVER (ORDER BY periodo), 0)) * 100, 2
            ) as variacion_pct
        FROM gastos_mensuales
        ORDER BY periodo
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo_inicio, periodo_fin))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results or [],
            query_type="periodo_evolucion_gastos",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

    # ✅ VERSIONES ORIGINALES MANTENIDAS PARA COMPATIBILIDAD
    def get_available_periods(self) -> List[str]:
        """FUNCIÓN ORIGINAL MANTENIDA"""
        query = """
            SELECT DISTINCT strftime('%Y-%m', FECHA) as periodo
            FROM MOVIMIENTOS_CONTRATOS
            WHERE FECHA IS NOT NULL
            ORDER BY periodo DESC
        """
        results = execute_query(query) or []
        return [row['periodo'] for row in results if row.get('periodo')]

    def get_latest_period(self) -> Optional[str]:
        """FUNCIÓN ORIGINAL MANTENIDA"""
        periods = self.get_available_periods()
        return periods[0] if periods else None

# ✅ INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
period_queries = PeriodQueries()

# Funciones enhanced
def get_available_periods_enhanced():
    return period_queries.get_available_periods_enhanced()

def get_latest_period_enhanced():
    return period_queries.get_latest_period_enhanced()

def get_periodo_metricas_financieras(periodo: str):
    return period_queries.get_periodo_metricas_financieras(periodo)

def compare_periodos_metricas(periodo_actual: str, periodo_anterior: str):
    return period_queries.compare_periodos_metricas(periodo_actual, periodo_anterior)

def get_periodo_analisis_gastos(periodo: str):
    return period_queries.get_periodo_analisis_gastos(periodo)

def get_periodo_evolucion_gastos(periodo_inicio: str, periodo_fin: str):
    return period_queries.get_periodo_evolucion_gastos(periodo_inicio, periodo_fin)

# Funciones originales mantenidas
def get_available_periods():
    return period_queries.get_available_periods()

def get_latest_period():
    return period_queries.get_latest_period()
