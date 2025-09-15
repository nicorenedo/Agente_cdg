"""
period_queries.py - ENHANCED VERSION

Biblioteca de consultas para manejo de períodos temporales
INTEGRADO con kpi_calculator.py y estructura QueryResult estándar
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
        """
        query = """
        SELECT 
            ? as periodo,
            COUNT(DISTINCT g.GESTOR_ID) as total_gestores_activos,
            COUNT(DISTINCT co.CLIENTE_ID) as total_clientes_activos,
            COUNT(DISTINCT co.CONTRATO_ID) as total_contratos_activos,
            COALESCE(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_periodo,
            COALESCE(SUM(CASE WHEN mov.IMPORTE < 0 THEN ABS(mov.IMPORTE) ELSE 0 END), 0) as gastos_periodo,
            COALESCE(SUM(gc.IMPORTE), 0) as gastos_centros_periodo,
            COUNT(DISTINCT mov.MOVIMIENTO_ID) as total_movimientos
        FROM MAESTRO_GESTORES g
        LEFT JOIN MAESTRO_CONTRATOS co ON g.GESTOR_ID = co.GESTOR_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON co.CONTRATO_ID = mov.CONTRATO_ID
            AND strftime('%Y-%m', mov.FECHA) = ?
        LEFT JOIN GASTOS_CENTRO gc ON strftime('%Y-%m', gc.FECHA) = ?
        """
        
        start_time = datetime.now()
        result = execute_query(query, (periodo, periodo, periodo), fetch_type="one")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result:
            ingresos = result['ingresos_periodo'] or 0
            gastos_mov = result['gastos_periodo'] or 0
            gastos_centros = result['gastos_centros_periodo'] or 0
            gastos_totales = gastos_mov + gastos_centros
            beneficio = ingresos - gastos_totales
            
            result.update({
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
            'beneficio_actual': actual['beneficio_neto'],
            'beneficio_anterior': anterior['beneficio_neto'],
            'beneficio_variacion_abs': actual['beneficio_neto'] - anterior['beneficio_neto'],
            'beneficio_variacion_pct': round(((actual['beneficio_neto'] - anterior['beneficio_neto']) / max(abs(anterior['beneficio_neto']), 1) * 100), 2),
            'contratos_actual': actual['total_contratos_activos'],
            'contratos_anterior': anterior['total_contratos_activos'],
            'contratos_variacion': actual['total_contratos_activos'] - anterior['total_contratos_activos'],
            'gestores_actual': actual['total_gestores_activos'],
            'gestores_anterior': anterior['total_gestores_activos']
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=[comparacion],
            query_type="compare_periodos_metricas",
            execution_time=execution_time,
            row_count=1,
            query_sql="-- Comparison of two periods"
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

# Funciones originales mantenidas
def get_available_periods():
    return period_queries.get_available_periods()

def get_latest_period():
    return period_queries.get_latest_period()
