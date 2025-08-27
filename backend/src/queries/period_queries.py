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
        ✅ VERSIÓN ENHANCED - Obtiene períodos disponibles con análisis
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
        results = execute_query(query)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # ✅ ANÁLISIS ENHANCED con KPI_CALCULATOR
        enhanced_results = []
        for row in results:
            enhanced_row = {
                'periodo': row['periodo'],
                'num_movimientos': row['num_movimientos'],
                'fecha_inicio': row['fecha_inicio'],
                'fecha_fin': row['fecha_fin'],
                'es_periodo_actual': row['periodo'] == '2025-10',
                'es_periodo_anterior': row['periodo'] == '2025-09'
            }
            enhanced_results.append(enhanced_row)
        
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
                execution_time=0,
                row_count=0,
                query_sql=""
            )
        
        latest_period_data = periods_result.data[0]
        
        return QueryResult(
            data=[latest_period_data],
            query_type="latest_period_enhanced",
            execution_time=periods_result.execution_time,
            row_count=1,
            query_sql=periods_result.query_sql
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
        results = execute_query(query)
        return [row['periodo'] for row in results if row['periodo']]
    
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
