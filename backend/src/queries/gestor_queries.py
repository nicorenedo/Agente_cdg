"""
gestor_queries.py

Biblioteca completa de consultas SQL para análisis por gestor
INTEGRADO con kpi_calculator.py para cálculos financieros estandarizados y clasificaciones automáticas.

COBERTURA MEJORADA:
- Análisis de cartera: contratos, productos, saldos con KPIs automáticos
- KPIs financieros: ROE, margen neto, eficiencia con clasificaciones bancarias
- Análisis temporal: evolución, comparativas con interpretaciones contextuales
- Detección desviaciones: alertas, umbrales con acciones recomendadas
- Análisis competitivo: ranking gestores con análisis estadístico mejorado
- Queries dinámicas: generación automática con validación

Autor: Agente CDG Development Team
Fecha: 2025-08-01
"""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, date

try:
    from database.db_connection import execute_query, execute_pandas_query
    from utils.dynamic_config import get_centros_finalistas, get_segmentos_activos
    from utils.initial_agent import iniciar_agente_llm
    from tools.kpi_calculator import FinancialKPICalculator
except ImportError:
    # Fallback para imports relativos
    from ..database.db_connection import execute_query, execute_pandas_query
    from ..utils.dynamic_config import get_centros_finalistas, get_segmentos_activos
    from ..utils.initial_agent import iniciar_agente_llm
    from ..tools.kpi_calculator import FinancialKPICalculator

logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Resultado de una consulta con metadatos"""
    data: Union[List[Dict], Dict]
    query_type: str
    execution_time: float
    row_count: int
    query_sql: str

class GestorQueries:
    """
    Biblioteca completa de consultas SQL para análisis por gestor
    
    COBERTURA MEJORADA:
    - Análisis de cartera: contratos, productos, saldos con KPIs automáticos
    - KPIs financieros: ROE, margen neto, eficiencia con clasificaciones bancarias
    - Análisis temporal: evolución, comparativas con interpretaciones contextuales
    - Detección desviaciones: alertas, umbrales con acciones recomendadas
    - Análisis competitivo: ranking gestores con análisis estadístico mejorado
    - Queries dinámicas: generación automática con validación
    """
    
    def __init__(self):
        self.query_cache = {}
        self.kpi_calc = FinancialKPICalculator()  # ✅ INSTANCIA KPI_CALCULATOR
        
    # =================================================================
    # 🚨 MÉTODOS REQUERIDOS POR CDG_AGENT.PY (CRÍTICOS)
    # =================================================================
    
    def get_gestor_performance_enhanced(self, gestor_id: str, periodo: str = None) -> QueryResult:
        """
        ✅ MÉTODO CRÍTICO REQUERIDO POR CDG_AGENT.PY
        
        Obtiene performance completo de un gestor con análisis KPI mejorado.
        
        CASO DE USO: "Analiza el performance del gestor Juan Pérez"
        MEJORAS: Análisis integral con KPIs automáticos y clasificaciones bancarias
        """
        query = """
            SELECT 
                g.GESTOR_ID,
                g.DESC_GESTOR as gestor,
                c.DESC_CENTRO as centro,
                s.DESC_SEGMENTO as segmento,
                COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes,
                SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                         THEN mov.IMPORTE ELSE 0 END) as total_ingresos,
                SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                         THEN ABS(mov.IMPORTE) ELSE 0 END) as total_gastos,
                SUM(mov.IMPORTE) as patrimonio_total,
                COALESCE(AVG(mov.IMPORTE), 0) as importe_promedio_movimiento
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
            LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
            WHERE g.GESTOR_ID = ?
                AND (? IS NULL OR strftime('%Y-%m', mov.FECHA) = ?)
            GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (gestor_id, periodo, periodo))
        
        if not raw_results:
            return QueryResult(
                data=[{"error": "No se encontraron datos para el gestor especificado"}],
                query_type="gestor_performance_enhanced_error",
                execution_time=0,
                row_count=0,
                query_sql=query
            )
        
        # ✅ PROCESAMIENTO CON KPI_CALCULATOR
        row = raw_results[0]
        
        # Análisis de KPIs completo
        margen_analysis = self.kpi_calc.calculate_margen_neto(
            ingresos=row['total_ingresos'] or 0,
            gastos=row['total_gastos'] or 0
        )
        
        roe_analysis = self.kpi_calc.calculate_roe(
            beneficio_neto=margen_analysis['beneficio_neto'],
            patrimonio=row['patrimonio_total'] or 1
        )
        
        eficiencia_analysis = self.kpi_calc.calculate_ratio_eficiencia(
            ingresos=row['total_ingresos'] or 0,
            gastos=row['total_gastos'] or 0
        )
        
        enhanced_result = {
            'gestor_id': row['GESTOR_ID'],
            'desc_gestor': row['gestor'],
            'desc_centro': row['centro'],
            'desc_segmento': row['segmento'],
            'total_contratos': row['total_contratos'],
            'total_clientes': row['total_clientes'],
            'total_ingresos': row['total_ingresos'] or 0,
            'total_gastos': row['total_gastos'] or 0,
            'patrimonio_total': row['patrimonio_total'] or 0,
            
            # ✅ ANÁLISIS KPI COMPLETO
            'margen_neto': margen_analysis['margen_neto_pct'],
            'beneficio_neto': margen_analysis['beneficio_neto'],
            'clasificacion_margen': margen_analysis['clasificacion'],
            
            'roe_pct': roe_analysis['roe_pct'],
            'clasificacion_roe': roe_analysis['clasificacion'],
            'benchmark_vs_sector': roe_analysis['benchmark_vs_sector'],
            
            'ratio_eficiencia': eficiencia_analysis['ratio_eficiencia'],
            'clasificacion_eficiencia': eficiencia_analysis['clasificacion'],
            'interpretacion_eficiencia': eficiencia_analysis['interpretacion'],
            
            # Análisis completo para drill-down
            'analisis_margen_completo': margen_analysis,
            'analisis_roe_completo': roe_analysis,
            'analisis_eficiencia_completo': eficiencia_analysis
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=[enhanced_result],
            query_type="gestor_performance_enhanced",
            execution_time=execution_time,
            row_count=1,
            query_sql=query
        )

    def get_all_gestores_enhanced(self) -> QueryResult:
        """
        ✅ MÉTODO CRÍTICO REQUERIDO POR CDG_AGENT.PY
        
        Obtiene todos los gestores con información básica mejorada.
        
        CASO DE USO: Inferir gestor desde mensaje del usuario
        """
        query = """
            SELECT 
                g.GESTOR_ID,
                g.DESC_GESTOR as desc_gestor,
                c.DESC_CENTRO as desc_centro,
                s.DESC_SEGMENTO as desc_segmento,
                COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos_activos
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            LEFT JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
            ORDER BY total_contratos_activos DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results or [],
            query_type="all_gestores_enhanced",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

    # =================================================================
    # 1. ANÁLISIS DE CARTERA POR GESTOR (ENHANCED CON KPI)
    # =================================================================
    
    def get_cartera_completa_gestor_enhanced(self, gestor_id: str, fecha: str = "2025-10") -> QueryResult:
        """
        Obtiene cartera completa de un gestor con análisis KPI mejorado.
        
        CASO DE USO: "Muéstrame toda la cartera de Juan Pérez"
        MEJORAS: Análisis de eficiencia automático y clasificaciones por producto
        """
        query = """
            SELECT 
                g.DESC_GESTOR as gestor,
                c.DESC_CENTRO as centro,
                s.DESC_SEGMENTO as segmento,
                COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes,
                p.DESC_PRODUCTO as producto,
                COUNT(CASE WHEN mc.PRODUCTO_ID = p.PRODUCTO_ID THEN 1 END) as contratos_producto,
                COALESCE(SUM(mov.IMPORTE), 0) as volumen_total_producto
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) = ?
            WHERE g.GESTOR_ID = ? 
                AND strftime('%Y-%m', mc.FECHA_ALTA) <= ?
            GROUP BY g.GESTOR_ID, p.PRODUCTO_ID
            ORDER BY contratos_producto DESC
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (fecha, gestor_id, fecha))
        
        # ✅ PROCESAMIENTO CON KPI_CALCULATOR
        enhanced_results = []
        total_contratos_gestor = sum(row['contratos_producto'] for row in raw_results)
        total_volumen_gestor = sum(row['volumen_total_producto'] for row in raw_results)
        
        for row in raw_results:
            # Análisis de eficiencia por producto con kpi_calculator
            eficiencia_analysis = self.kpi_calc.calculate_ratio_eficiencia(
                ingresos=row['volumen_total_producto'],
                gastos=row['contratos_producto'] * 500  # Costo estimado por contrato
            )
            
            # Análisis de concentración
            concentracion_pct = (row['contratos_producto'] / total_contratos_gestor * 100) if total_contratos_gestor > 0 else 0
            peso_volumen_pct = (row['volumen_total_producto'] / total_volumen_gestor * 100) if total_volumen_gestor > 0 else 0
            
            enhanced_row = {
                **row,
                'concentracion_contratos_pct': round(concentracion_pct, 2),
                'peso_volumen_pct': round(peso_volumen_pct, 2),
                'ratio_eficiencia': eficiencia_analysis['ratio_eficiencia'],
                'clasificacion_eficiencia': eficiencia_analysis['clasificacion'],
                'interpretacion_eficiencia': eficiencia_analysis['interpretacion'],
                
                # ✅ CLASIFICACIÓN AUTOMÁTICA DE PRODUCTOS
                'categoria_producto': self._classify_product_importance(concentracion_pct, peso_volumen_pct),
                'volumen_promedio_contrato': round(row['volumen_total_producto'] / row['contratos_producto'], 2) if row['contratos_producto'] > 0 else 0,
                
                # Análisis completo para drill-down
                'analisis_eficiencia_completo': eficiencia_analysis
            }
            enhanced_results.append(enhanced_row)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="cartera_completa_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )

    def calculate_margen_neto_gestor_enhanced(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Calcula margen neto del gestor con análisis KPI mejorado.
        
        CASO DE USO: "¿Cuál es el margen neto de Carlos Ruiz en octubre?"
        MEJORAS: Clasificaciones automáticas y interpretaciones contextuales bancarias
        """
        query = """
            WITH ingresos_gastos AS (
                SELECT 
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as total_ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as total_gastos
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                WHERE cont.GESTOR_ID = ?
                    AND strftime('%Y-%m', mov.FECHA) = ?
            )
            SELECT total_ingresos, total_gastos FROM ingresos_gastos
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (gestor_id, periodo))
        
        if not raw_results:
            return QueryResult(
                data=[{"error": "No se encontraron datos para el gestor en el período especificado"}],
                query_type="margen_neto_enhanced_error",
                execution_time=0,
                row_count=0,
                query_sql=query
            )
        
        # ✅ PROCESAMIENTO CON KPI_CALCULATOR
        row = raw_results[0]
        
        # Análisis de margen con kpi_calculator
        margen_analysis = self.kpi_calc.calculate_margen_neto(
            ingresos=row['total_ingresos'] or 0,
            gastos=row['total_gastos'] or 0
        )
        
        # Análisis de eficiencia
        eficiencia_analysis = self.kpi_calc.calculate_ratio_eficiencia(
            ingresos=row['total_ingresos'] or 0,
            gastos=row['total_gastos'] or 0
        )
        
        enhanced_result = {
            'total_ingresos': row['total_ingresos'] or 0,
            'total_gastos': row['total_gastos'] or 0,
            'beneficio_neto': margen_analysis['beneficio_neto'],
            'margen_neto_pct': margen_analysis['margen_neto_pct'],
            'clasificacion_margen': margen_analysis['clasificacion'],  # EXCELENTE, BUENO, etc.
            'ratio_eficiencia': eficiencia_analysis['ratio_eficiencia'],
            'clasificacion_eficiencia': eficiencia_analysis['clasificacion'],
            'interpretacion_eficiencia': eficiencia_analysis['interpretacion'],
            
            # ✅ ANÁLISIS CONTEXTUAL BANCARIO
            'contexto_bancario': self._get_banking_context(margen_analysis['clasificacion']),
            'recomendacion_accion': self._get_margin_recommendation(margen_analysis['margen_neto_pct']),
            
            # Análisis completo para drill-down
            'analisis_margen_completo': margen_analysis,
            'analisis_eficiencia_completo': eficiencia_analysis
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=[enhanced_result],
            query_type="margen_neto_enhanced",
            execution_time=execution_time,
            row_count=1,
            query_sql=query
        )

    # =================================================================
    # FUNCIONES HELPER PARA CLASIFICACIONES MEJORADAS
    # =================================================================
    
    def _classify_product_importance(self, concentracion_pct: float, peso_volumen_pct: float) -> str:
        """Clasificación de importancia del producto en la cartera"""
        if concentracion_pct >= 50 or peso_volumen_pct >= 60:
            return 'PRODUCTO_CORE'
        elif concentracion_pct >= 25 or peso_volumen_pct >= 30:
            return 'PRODUCTO_IMPORTANTE'
        elif concentracion_pct >= 10 or peso_volumen_pct >= 15:
            return 'PRODUCTO_SECUNDARIO'
        else:
            return 'PRODUCTO_MARGINAL'
    
    def _get_banking_context(self, clasificacion_margen: str) -> str:
        """Contexto bancario específico para la clasificación de margen"""
        contexts = {
            'EXCELENTE': 'Margen superior a benchmarks del sector bancario español. Performance excepcional.',
            'BUENO': 'Margen en línea con mejores prácticas del sector. Performance sólida.',
            'ACEPTABLE': 'Margen dentro de parámetros estándar bancarios. Espacio para mejora.',
            'BAJO': 'Margen por debajo de media sectorial. Requiere análisis de eficiencia.',
            'PERDIDAS': 'Situación crítica. Revisión inmediata de cartera y procesos requerida.'
        }
        return contexts.get(clasificacion_margen, 'Análisis específico requerido')
    
    def _get_margin_recommendation(self, margen_pct: float) -> str:
        """Recomendaciones específicas basadas en el margen neto"""
        if margen_pct >= 25:
            return 'OPTIMIZAR: Considerar expansión de productos similares'
        elif margen_pct >= 15:
            return 'MANTENER: Estrategia actual es eficaz'
        elif margen_pct >= 8:
            return 'MEJORAR: Revisar mix de productos y eficiencia operativa'
        elif margen_pct >= 0:
            return 'URGENTE: Análisis detallado de costes y pricing'
        else:
            return 'CRÍTICO: Plan de acción inmediato requerido'

    # =================================================================
    # 2. FUNCIONES ORIGINALES MANTENIDAS PARA COMPATIBILIDAD
    # =================================================================
    
    def get_cartera_completa_gestor(self, gestor_id: str, fecha: str = "2025-10") -> QueryResult:
        """FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD"""
        query = """
            SELECT 
                g.DESC_GESTOR as gestor,
                c.DESC_CENTRO as centro,
                s.DESC_SEGMENTO as segmento,
                COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes,
                p.DESC_PRODUCTO as producto,
                COUNT(CASE WHEN mc.PRODUCTO_ID = p.PRODUCTO_ID THEN 1 END) as contratos_producto
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
            WHERE g.GESTOR_ID = ? 
                AND strftime('%Y-%m', mc.FECHA_ALTA) <= ?
            GROUP BY g.GESTOR_ID, p.PRODUCTO_ID
            ORDER BY contratos_producto DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, fecha))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results or [],
            query_type="cartera_completa",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

    def calculate_margen_neto_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD"""
        query = """
            WITH ingresos AS (
                SELECT 
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as total_ingresos
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                WHERE cont.GESTOR_ID = ?
                    AND strftime('%Y-%m', mov.FECHA) = ?
            ),
            gastos AS (
                SELECT 
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as total_gastos
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                WHERE cont.GESTOR_ID = ?
                    AND strftime('%Y-%m', mov.FECHA) = ?
            )
            SELECT 
                i.total_ingresos,
                g.total_gastos,
                (i.total_ingresos - g.total_gastos) as beneficio_neto,
                CASE 
                    WHEN i.total_ingresos > 0 
                    THEN ROUND(((i.total_ingresos - g.total_gastos) / i.total_ingresos) * 100, 2)
                    ELSE 0 
                END as margen_neto_pct
            FROM ingresos i, gastos g
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, periodo, gestor_id, periodo))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results or [],
            query_type="margen_neto",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

    def get_contratos_activos_gestor(self, gestor_id: str) -> QueryResult:
        """FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD"""
        query = """
            SELECT 
                mc.CONTRATO_ID,
                mc.CLIENTE_ID,
                mcl.NOMBRE_CLIENTE as cliente,
                mc.PRODUCTO_ID,
                p.DESC_PRODUCTO as producto,
                mc.FECHA_ALTA,
                COALESCE(SUM(mov.IMPORTE), 0) as importe_total,
                CASE 
                    WHEN mc.FECHA_ALTA >= '2025-10-01' THEN 'NUEVO_OCTUBRE'
                    ELSE 'ANTERIOR'
                END as tipo_contrato
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
            JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            WHERE mc.GESTOR_ID = ?
            GROUP BY mc.CONTRATO_ID, mc.CLIENTE_ID, mcl.NOMBRE_CLIENTE, mc.PRODUCTO_ID, p.DESC_PRODUCTO, mc.FECHA_ALTA
            ORDER BY mc.FECHA_ALTA DESC, importe_total DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id,))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results or [],
            query_type="contratos_activos",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

    # =================================================================
    # 3. ANÁLISIS TEMPORAL Y COMPARATIVO (ORIGINAL)
    # =================================================================
    
    def compare_gestor_septiembre_octubre(self, gestor_id: str) -> QueryResult:
        """Compara performance del gestor entre septiembre y octubre 2025"""
        query = """
            WITH datos_mes AS (
                SELECT 
                    strftime('%Y-%m', mov.FECHA) as periodo,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos,
                    COUNT(DISTINCT mov.CONTRATO_ID) as contratos_activos
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                WHERE cont.GESTOR_ID = ?
                    AND strftime('%Y-%m', mov.FECHA) IN ('2025-09', '2025-10')
                GROUP BY strftime('%Y-%m', mov.FECHA)
            ),
            contratos_nuevos AS (
                SELECT 
                    strftime('%Y-%m', FECHA_ALTA) as periodo,
                    COUNT(*) as nuevos_contratos
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ?
                    AND strftime('%Y-%m', FECHA_ALTA) IN ('2025-09', '2025-10')
                GROUP BY strftime('%Y-%m', FECHA_ALTA)
            )
            SELECT 
                dm.periodo,
                dm.ingresos,
                dm.gastos,
                (dm.ingresos - dm.gastos) as beneficio_neto,
                dm.contratos_activos,
                COALESCE(cn.nuevos_contratos, 0) as nuevos_contratos,
                CASE 
                    WHEN dm.ingresos > 0 
                    THEN ROUND(((dm.ingresos - dm.gastos) / dm.ingresos) * 100, 2)
                    ELSE 0 
                END as margen_neto_pct
            FROM datos_mes dm
            LEFT JOIN contratos_nuevos cn ON dm.periodo = cn.periodo
            ORDER BY dm.periodo
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, gestor_id))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results or [],
            query_type="comparacion_temporal",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# =================================================================

# Instancia global para uso en toda la aplicación
gestor_queries = GestorQueries()

# ✅ NUEVAS funciones de conveniencia para versiones enhanced
def get_gestor_performance_enhanced(gestor_id: str, periodo: str = None):
    """Función de conveniencia para performance completo mejorado"""
    return gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo)

def get_all_gestores_enhanced():
    """Función de conveniencia para todos los gestores mejorado"""
    return gestor_queries.get_all_gestores_enhanced()

def get_cartera_gestor_enhanced(gestor_id: str, fecha: str = "2025-10"):
    """Función de conveniencia para cartera mejorada con análisis KPI"""
    return gestor_queries.get_cartera_completa_gestor_enhanced(gestor_id, fecha)

def get_margen_gestor_enhanced(gestor_id: str, periodo: str = "2025-10"):
    """Función de conveniencia para margen mejorado con clasificaciones automáticas"""
    return gestor_queries.calculate_margen_neto_gestor_enhanced(gestor_id, periodo)

# Funciones de conveniencia originales mantenidas
def get_cartera_gestor(gestor_id: str):
    """Función de conveniencia para obtener cartera de un gestor"""
    return gestor_queries.get_cartera_completa_gestor(gestor_id)

def get_margen_gestor(gestor_id: str, periodo: str = "2025-10"):
    """Función de conveniencia para obtener margen de un gestor"""
    return gestor_queries.calculate_margen_neto_gestor(gestor_id, periodo)

def compare_gestor_meses(gestor_id: str):
    """Función de conveniencia para comparar meses"""
    return gestor_queries.compare_gestor_septiembre_octubre(gestor_id)

# =================================================================
# CONTINUACIÓN - FUNCIONES HELPER ADICIONALES PARA CLASIFICACIONES MEJORADAS
# =================================================================

def _get_efficiency_context(self, clasificacion_eficiencia: str) -> str:
    """Contexto bancario específico para clasificación de eficiencia"""
    contexts = {
        'MUY_EFICIENTE': 'Eficiencia operativa excepcional. Benchmark de excelencia para el sector.',
        'EFICIENTE': 'Buena gestión de recursos. Performance por encima de media sectorial.',
        'EQUILIBRADO': 'Eficiencia aceptable. En línea con estándares bancarios.',
        'INEFICIENTE': 'Oportunidad de mejora significativa en gestión de costes operativos.'
    }
    return contexts.get(clasificacion_eficiencia, 'Análisis específico requerido')

def _get_efficiency_recommendation(self, ratio_eficiencia: float) -> str:
    """Recomendaciones específicas basadas en ratio de eficiencia"""
    if ratio_eficiencia >= 2.0:
        return 'REPLICAR: Documentar mejores prácticas para otros gestores'
    elif ratio_eficiencia >= 1.5:
        return 'MANTENER: Continuar estrategia operativa actual'
    elif ratio_eficiencia >= 1.0:
        return 'OPTIMIZAR: Revisar procesos operativos específicos'
    else:
        return 'URGENTE: Plan de mejora operativa inmediato'

def _get_roe_context(self, clasificacion_roe: str) -> str:
    """Contexto bancario específico para clasificación ROE"""
    contexts = {
        'SOBRESALIENTE': 'ROE excepcional. Top quartile del sector bancario español.',
        'BUENO': 'ROE sólido. Performance superior a media sectorial.',
        'PROMEDIO': 'ROE en línea con benchmarks sectoriales.',
        'BAJO': 'ROE por debajo de expectativas. Revisión de estrategia recomendada.',
        'NEGATIVO': 'Situación crítica. Destrucción de valor patrimonial.'
    }
    return contexts.get(clasificacion_roe, 'Análisis específico requerido')

def _get_roe_recommendation(self, roe_pct: float) -> str:
    """Recomendaciones específicas basadas en ROE"""
    if roe_pct >= 15.0:
        return 'EXPANDIR: Considerar asignación adicional de recursos'
    elif roe_pct >= 10.0:
        return 'OPTIMIZAR: Buscar eficiencias adicionales manteniendo calidad'
    elif roe_pct >= 5.0:
        return 'REVISAR: Análisis de cartera y mix de productos'
    elif roe_pct >= 0.0:
        return 'REESTRUCTURAR: Plan de acción integral requerido'
    else:
        return 'CRÍTICO: Revisión completa de cartera y estrategia'

def _classify_product_deviation_impact(self, desviacion_abs_pct: float, producto: str) -> str:
    """Clasificación del impacto comercial de desviaciones por producto"""
    if 'Fondo' in producto and desviacion_abs_pct >= 20:
        return 'IMPACTO_ALTO_CORE_BUSINESS'
    elif 'Hipotecario' in producto and desviacion_abs_pct >= 15:
        return 'IMPACTO_CRITICO_MARGEN'
    elif desviacion_abs_pct >= 25:
        return 'IMPACTO_EXTREMO'
    elif desviacion_abs_pct >= 15:
        return 'IMPACTO_SIGNIFICATIVO'
    else:
        return 'IMPACTO_MODERADO'
# =================================================================
# 4. FUNCIONES COMPLETADAS - DISTRIBUCIÓN DE FONDOS Y ALERTAS
# =================================================================

def get_distribucion_fondos_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
    """
    Obtiene distribución específica de fondos para un gestor con análisis mejorado
    
    CASO DE USO: "¿Cómo distribuye Laura los fondos entre fábrica y banco?"
    MEJORAS: Análisis automático de reparto 85%/15% con alertas de desviaciones
    """
    query = """
        WITH fondos_gestor AS (
            SELECT 
                mc.CONTRATO_ID,
                mc.CLIENTE_ID,
                p.DESC_PRODUCTO as producto,
                SUM(CASE WHEN mov.CUENTA_ID = '760025' THEN mov.IMPORTE ELSE 0 END) as importe_fabrica,
                SUM(CASE WHEN mov.CUENTA_ID = '760024' THEN mov.IMPORTE ELSE 0 END) as importe_banco,
                SUM(mov.IMPORTE) as importe_total
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
            JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            WHERE mc.GESTOR_ID = ?
                AND p.PRODUCTO_ID = '600100300300'  -- Producto fondos
                AND strftime('%Y-%m', mov.FECHA) = ?
                AND mov.CUENTA_ID IN ('760025', '760024')  -- Cuentas de reparto fondos
            GROUP BY mc.CONTRATO_ID, mc.CLIENTE_ID, p.DESC_PRODUCTO
            HAVING importe_total > 0
        )
        SELECT 
            producto,
            COUNT(*) as num_contratos,
            SUM(importe_fabrica) as total_importe_fabrica,
            SUM(importe_banco) as total_importe_banco,
            SUM(importe_total) as total_general,
            ROUND(AVG(importe_fabrica / importe_total * 100), 2) as pct_promedio_fabrica,
            ROUND(AVG(importe_banco / importe_total * 100), 2) as pct_promedio_banco
        FROM fondos_gestor
        GROUP BY producto
    """
    
    start_time = datetime.now()
    raw_results = execute_query(query, (gestor_id, periodo))
    
    # ✅ PROCESAMIENTO CON ANÁLISIS DE DESVIACIONES
    enhanced_results = []
    
    for row in raw_results:
        # Análisis de desviación del reparto estándar 85%/15%
        desviacion_fabrica = abs(row['pct_promedio_fabrica'] - 85.0)
        desviacion_banco = abs(row['pct_promedio_banco'] - 15.0)
        
        # Análisis con kpi_calculator
        desviacion_analysis = self.kpi_calc.analyze_desviacion_presupuestaria(
            valor_real=row['pct_promedio_fabrica'],
            valor_presupuestado=85.0
        )
        
        enhanced_row = {
            **row,
            'desviacion_fabrica_pct': round(desviacion_fabrica, 2),
            'desviacion_banco_pct': round(desviacion_banco, 2),
            'cumple_estandar_85_15': desviacion_fabrica <= 5.0 and desviacion_banco <= 5.0,
            'nivel_alerta': desviacion_analysis['nivel_alerta'],
            'accion_recomendada': desviacion_analysis['accion_recomendada'],
            
            # ✅ ANÁLISIS ESPECÍFICO FONDOS
            'interpretacion_reparto': self._interpret_fondos_distribution(
                row['pct_promedio_fabrica'], 
                row['pct_promedio_banco']
            ),
            'impacto_comercial': 'ALTO' if desviacion_fabrica > 10 else 'MEDIO' if desviacion_fabrica > 5 else 'BAJO',
            
            # Análisis completo
            'analisis_desviacion_completo': desviacion_analysis
        }
        enhanced_results.append(enhanced_row)
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return QueryResult(
        data=enhanced_results,
        query_type="distribucion_fondos",
        execution_time=execution_time,
        row_count=len(enhanced_results),
        query_sql=query
    )

def get_alertas_criticas_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
    """
    Obtiene alertas críticas para un gestor con análisis de impacto
    
    CASO DE USO: "¿Qué alertas críticas tiene Pedro este mes?"
    MEJORAS: Análisis de impacto por alerta y acciones recomendadas
    """
    query = """
        WITH alertas_margen AS (
            SELECT 
                'MARGEN_BAJO' as tipo_alerta,
                'Margen neto por debajo del 8%' as descripcion,
                'CRITICA' as severidad,
                g.DESC_GESTOR as gestor,
                margen_data.margen_neto_pct as valor_actual,
                8.0 as umbral_critico,
                'Revisar pricing y estructura de costos' as accion_recomendada
            FROM MAESTRO_GESTORES g
            JOIN (
                SELECT 
                    cont.GESTOR_ID,
                    CASE 
                        WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                       THEN mov.IMPORTE ELSE 0 END) > 0 
                        THEN ROUND(((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                              THEN mov.IMPORTE ELSE 0 END) - 
                                   SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                                            THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                                   SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                            THEN mov.IMPORTE ELSE 0 END)) * 100, 2)
                        ELSE 0 
                    END as margen_neto_pct
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                GROUP BY cont.GESTOR_ID
            ) margen_data ON g.GESTOR_ID = margen_data.GESTOR_ID
            WHERE g.GESTOR_ID = ?
                AND margen_data.margen_neto_pct < 8.0
        
        UNION ALL
        
        SELECT 
            'DESVIACION_PRECIO' as tipo_alerta,
            'Desviación de precio superior al 20%' as descripcion,
            'ALTA' as severidad,
            g.DESC_GESTOR as gestor,
            ABS(desv_data.desviacion_pct) as valor_actual,
            20.0 as umbral_critico,
            'Revisar política de pricing del producto' as accion_recomendada
        FROM MAESTRO_GESTORES g
        JOIN (
            SELECT DISTINCT
                cont.GESTOR_ID,
                ROUND(((ABS(pr.PRECIO_MANTENIMIENTO_REAL) - ABS(ps.PRECIO_MANTENIMIENTO)) / 
                       ABS(ps.PRECIO_MANTENIMIENTO)) * 100, 2) as desviacion_pct
            FROM MAESTRO_CONTRATOS cont
            JOIN PRECIO_POR_PRODUCTO_REAL pr ON cont.PRODUCTO_ID = pr.PRODUCTO_ID
            JOIN PRECIO_POR_PRODUCTO_STD ps ON cont.PRODUCTO_ID = ps.PRODUCTO_ID 
                AND pr.SEGMENTO_ID = ps.SEGMENTO_ID
            WHERE ABS(((ABS(pr.PRECIO_MANTENIMIENTO_REAL) - ABS(ps.PRECIO_MANTENIMIENTO)) / 
                       ABS(ps.PRECIO_MANTENIMIENTO)) * 100) >= 20.0
        ) desv_data ON g.GESTOR_ID = desv_data.GESTOR_ID
        WHERE g.GESTOR_ID = ?
        
        ORDER BY 
            CASE severidad 
                WHEN 'CRITICA' THEN 1 
                WHEN 'ALTA' THEN 2 
                WHEN 'MEDIA' THEN 3 
                ELSE 4 
            END,
            valor_actual DESC
    """
    
    start_time = datetime.now()
    raw_results = execute_query(query, (periodo, gestor_id, gestor_id))
    
    # ✅ PROCESAMIENTO CON ANÁLISIS DE IMPACTO
    enhanced_results = []
    
    for row in raw_results:
        # Análisis de impacto de la alerta
        impacto_comercial = self._assess_alert_impact(
            row['tipo_alerta'], 
            row['valor_actual'], 
            row['umbral_critico']
        )
        
        # Prioridad de acción
        prioridad = self._calculate_alert_priority(
            row['severidad'], 
            row['valor_actual'], 
            row['umbral_critico']
        )
        
        enhanced_row = {
            **row,
            'impacto_comercial': impacto_comercial,
            'prioridad_accion': prioridad,
            'dias_para_accion': self._get_action_timeline(row['severidad']),
            'responsable_seguimiento': 'Control de Gestión' if row['severidad'] == 'CRITICA' else 'Gestor Comercial',
            
            # ✅ CONTEXTO ESPECÍFICO
            'contexto_bancario': self._get_alert_banking_context(row['tipo_alerta']),
            'impacto_estimado_ingresos': self._estimate_revenue_impact(
                row['tipo_alerta'], 
                row['valor_actual']
            )
        }
        enhanced_results.append(enhanced_row)
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return QueryResult(
        data=enhanced_results,
        query_type="alertas_criticas",
        execution_time=execution_time,
        row_count=len(enhanced_results),
        query_sql=query
    )
# =================================================================
# 5. ANÁLISIS POR CENTRO Y SEGMENTO
# =================================================================

def get_performance_por_centro(self, centro_id: int = None, periodo: str = "2025-10") -> QueryResult:
    """
    Performance por centro con análisis comparativo mejorado
    
    CASO DE USO: "¿Cómo está el centro Madrid vs otros centros?"
    """
    query = """
        SELECT 
            c.CENTRO_ID,
            c.DESC_CENTRO as centro,
            c.IND_CENTRO_FINALISTA as es_finalista,
            COUNT(DISTINCT g.GESTOR_ID) as num_gestores,
            COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
            SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                     THEN mov.IMPORTE ELSE 0 END) as ingresos_centro,
            SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                     THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_centro,
            ROUND(AVG(CASE 
                WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                               THEN mov.IMPORTE ELSE 0 END) > 0 
                THEN ((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                THEN mov.IMPORTE ELSE 0 END) - 
                       SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                                THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                       SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                THEN mov.IMPORTE ELSE 0 END)) * 100
                ELSE 0 
            END), 2) as margen_promedio_centro
        FROM MAESTRO_CENTROS c
        JOIN MAESTRO_GESTORES g ON c.CENTRO_ID = g.CENTRO
        JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            AND strftime('%Y-%m', mov.FECHA) = ?
        LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
        LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
        WHERE (? IS NULL OR c.CENTRO_ID = ?)
        GROUP BY c.CENTRO_ID, c.DESC_CENTRO, c.IND_CENTRO_FINALISTA
        ORDER BY margen_promedio_centro DESC
    """
    
    start_time = datetime.now()
    results = execute_query(query, (periodo, centro_id, centro_id))
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return QueryResult(
        data=results or [],
        query_type="performance_centro",
        execution_time=execution_time,
        row_count=len(results) if results else 0,
        query_sql=query
    )

def get_analysis_por_segmento(self, segmento_id: str = None, periodo: str = "2025-10") -> QueryResult:
    """
    Análisis por segmento con métricas especializadas
    
    CASO DE USO: "¿Cómo está el segmento Banca Privada vs otros?"
    """
    query = """
        SELECT 
            s.SEGMENTO_ID,
            s.DESC_SEGMENTO as segmento,
            COUNT(DISTINCT g.GESTOR_ID) as num_gestores,
            COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
            AVG(CASE 
                WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                               THEN mov.IMPORTE ELSE 0 END) > 0 
                THEN ((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                THEN mov.IMPORTE ELSE 0 END) - 
                       SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                                THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                       SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                THEN mov.IMPORTE ELSE 0 END)) * 100
                ELSE 0 
            END) as margen_promedio_segmento,
            SUM(mov.IMPORTE) / COUNT(DISTINCT mc.CONTRATO_ID) as ticket_promedio
        FROM MAESTRO_SEGMENTOS s
        JOIN MAESTRO_GESTORES g ON s.SEGMENTO_ID = g.SEGMENTO_ID
        JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            AND strftime('%Y-%m', mov.FECHA) = ?
        LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
        LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
        WHERE (? IS NULL OR s.SEGMENTO_ID = ?)
        GROUP BY s.SEGMENTO_ID, s.DESC_SEGMENTO
        ORDER BY margen_promedio_segmento DESC
    """
    
    start_time = datetime.now()
    results = execute_query(query, (periodo, segmento_id, segmento_id))
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return QueryResult(
        data=results or [],
        query_type="analysis_segmento",
        execution_time=execution_time,
        row_count=len(results) if results else 0,
        query_sql=query
    )
# =================================================================
# 6. FUNCIONES HELPER ADICIONALES
# =================================================================

def _interpret_fondos_distribution(self, pct_fabrica: float, pct_banco: float) -> str:
    """Interpretación específica de distribución de fondos"""
    if abs(pct_fabrica - 85.0) <= 2.0 and abs(pct_banco - 15.0) <= 2.0:
        return 'DISTRIBUCIÓN_ÓPTIMA'
    elif pct_fabrica > 90.0:
        return 'SOBREPONDERACIÓN_FÁBRICA'
    elif pct_banco > 20.0:
        return 'SOBREPONDERACIÓN_BANCO'
    else:
        return 'DISTRIBUCIÓN_ATÍPICA'

def _assess_alert_impact(self, tipo_alerta: str, valor_actual: float, umbral: float) -> str:
    """Evaluación de impacto comercial de alertas"""
    severity_ratio = valor_actual / umbral
    
    if tipo_alerta == 'MARGEN_BAJO':
        if severity_ratio <= 0.5:
            return 'CRÍTICO_RENTABILIDAD'
        elif severity_ratio <= 0.75:
            return 'ALTO_IMPACTO_MARGEN'
        else:
            return 'MODERADO_SEGUIMIENTO'
    
    elif tipo_alerta == 'DESVIACION_PRECIO':
        if severity_ratio >= 2.0:
            return 'CRÍTICO_COMPETITIVIDAD'
        elif severity_ratio >= 1.5:
            return 'ALTO_RIESGO_COMERCIAL'
        else:
            return 'MODERADO_AJUSTE_PRICING'
    
    return 'IMPACTO_ESTÁNDAR'

def _calculate_alert_priority(self, severidad: str, valor_actual: float, umbral: float) -> int:
    """Calcula prioridad numérica de 1 (máxima) a 5 (mínima)"""
    base_priority = {'CRITICA': 1, 'ALTA': 2, 'MEDIA': 3, 'BAJA': 4}.get(severidad, 5)
    
    # Ajustar según magnitud de desviación
    severity_ratio = valor_actual / umbral
    if severity_ratio >= 2.0:
        base_priority = max(1, base_priority - 1)
    elif severity_ratio <= 0.5:
        base_priority = max(1, base_priority - 1)
    
    return base_priority

def _get_action_timeline(self, severidad: str) -> int:
    """Días recomendados para acción según severidad"""
    timelines = {
        'CRITICA': 1,
        'ALTA': 3,
        'MEDIA': 7,
        'BAJA': 15
    }
    return timelines.get(severidad, 30)

def _get_alert_banking_context(self, tipo_alerta: str) -> str:
    """Contexto bancario específico para cada tipo de alerta"""
    contexts = {
        'MARGEN_BAJO': 'Margen por debajo de mínimos operativos del sector bancario',
        'DESVIACION_PRECIO': 'Pricing fuera de rangos competitivos del mercado',
        'EFICIENCIA_BAJA': 'Ratio eficiencia por debajo de benchmarks sectoriales',
        'ROE_NEGATIVO': 'Destrucción de valor patrimonial - revisión estratégica requerida'
    }
    return contexts.get(tipo_alerta, 'Análisis específico requerido')

def _estimate_revenue_impact(self, tipo_alerta: str, valor_actual: float) -> str:
    """Estimación de impacto en ingresos"""
    if tipo_alerta == 'MARGEN_BAJO' and valor_actual < 5.0:
        return 'ALTO: Potencial pérdida >15% ingresos netos'
    elif tipo_alerta == 'DESVIACION_PRECIO' and valor_actual > 25.0:
        return 'MEDIO: Riesgo competitivo 5-10% volumen'
    else:
        return 'BAJO: Impacto limitado en ingresos corrientes'
# =================================================================
# 7. FUNCIONES COMPLETADAS - BENCHMARKING Y TOP PERFORMERS
# =================================================================

def get_benchmarking_gestores(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
    """
    Benchmarking completo de un gestor vs sus pares
    
    CASO DE USO: "¿Cómo está Juan vs otros gestores de su segmento?"
    """
    query = """
        WITH gestor_base AS (
            SELECT 
                g.GESTOR_ID,
                g.DESC_GESTOR as gestor_objetivo,
                g.SEGMENTO_ID,
                s.DESC_SEGMENTO as segmento,
                SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                         THEN mov.IMPORTE ELSE 0 END) as ingresos_gestor,
                SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                         THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_gestor,
                COUNT(DISTINCT mc.CONTRATO_ID) as contratos_gestor
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) = ?
            LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
            LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
            WHERE g.GESTOR_ID = ?
            GROUP BY g.GESTOR_ID, g.DESC_GESTOR, g.SEGMENTO_ID, s.DESC_SEGMENTO
        ),
        pares_segmento AS (
            SELECT 
                g2.GESTOR_ID,
                g2.DESC_GESTOR as gestor_par,
                SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                         THEN mov.IMPORTE ELSE 0 END) as ingresos_par,
                SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                         THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_par,
                COUNT(DISTINCT mc.CONTRATO_ID) as contratos_par,
                CASE 
                    WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                   THEN mov.IMPORTE ELSE 0 END) > 0 
                    THEN ROUND(((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                          THEN mov.IMPORTE ELSE 0 END) - 
                               SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                                        THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                               SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                        THEN mov.IMPORTE ELSE 0 END)) * 100, 2)
                    ELSE 0 
                END as margen_par
            FROM MAESTRO_GESTORES g2
            JOIN MAESTRO_CONTRATOS mc ON g2.GESTOR_ID = mc.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) = ?
            LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
            LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
            WHERE g2.SEGMENTO_ID = (SELECT SEGMENTO_ID FROM gestor_base)
                AND g2.GESTOR_ID != ?
            GROUP BY g2.GESTOR_ID, g2.DESC_GESTOR
        )
        SELECT 
            gb.gestor_objetivo,
            gb.segmento,
            gb.ingresos_gestor,
            gb.gastos_gestor,
            gb.contratos_gestor,
            CASE 
                WHEN gb.ingresos_gestor > 0 
                THEN ROUND(((gb.ingresos_gestor - gb.gastos_gestor) / gb.ingresos_gestor) * 100, 2)
                ELSE 0 
            END as margen_gestor,
            COUNT(ps.gestor_par) as num_pares_comparables,
            ROUND(AVG(ps.margen_par), 2) as margen_promedio_pares,
            ROUND(MAX(ps.margen_par), 2) as margen_mejor_par,
            ROUND(MIN(ps.margen_par), 2) as margen_peor_par,
            ROUND(
                (CASE 
                    WHEN gb.ingresos_gestor > 0 
                    THEN ((gb.ingresos_gestor - gb.gastos_gestor) / gb.ingresos_gestor) * 100
                    ELSE 0 
                END - AVG(ps.margen_par)), 2
            ) as diferencia_vs_promedio
        FROM gestor_base gb
        LEFT JOIN pares_segmento ps ON 1=1
        GROUP BY gb.gestor_objetivo, gb.segmento, gb.ingresos_gestor, gb.gastos_gestor, gb.contratos_gestor
    """
    
    start_time = datetime.now()
    results = execute_query(query, (periodo, gestor_id, periodo, gestor_id))
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return QueryResult(
        data=results or [],
        query_type="benchmarking_gestores",
        execution_time=execution_time,
        row_count=len(results) if results else 0,
        query_sql=query
    )

def get_top_performers_by_metric(self, metric: str = "margen_neto", limit: int = 10, periodo: str = "2025-10") -> QueryResult:
    """
    Top performers por métrica específica con análisis detallado
    
    CASO DE USO: "¿Quiénes son los top 10 gestores por ROE?"
    """
    if metric == "roe":
        query = """
            WITH roe_gestores AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR as gestor,
                    c.DESC_CENTRO as centro,
                    s.DESC_SEGMENTO as segmento,
                    SUM(mov_pat.IMPORTE) as patrimonio_total,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos,
                    CASE 
                        WHEN SUM(mov_pat.IMPORTE) > 0 
                        THEN ROUND(((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                               THEN mov.IMPORTE ELSE 0 END) - 
                                   SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                                            THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                                   SUM(mov_pat.IMPORTE)) * 100, 4)
                        ELSE 0 
                    END as roe_pct
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                JOIN MOVIMIENTOS_CONTRATOS mov_pat ON mc.CONTRATO_ID = mov_pat.CONTRATO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING patrimonio_total > 0
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY roe_pct DESC) as ranking,
                gestor,
                centro,
                segmento,
                roe_pct,
                patrimonio_total,
                ingresos,
                gastos,
                (ingresos - gastos) as beneficio_neto
            FROM roe_gestores
            WHERE roe_pct IS NOT NULL
            ORDER BY roe_pct DESC
            LIMIT ?
        """
        params = (periodo, limit)
    
    else:  # Default: margen_neto
        query = """
            WITH margen_gestores AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR as gestor,
                    c.DESC_CENTRO as centro,
                    s.DESC_SEGMENTO as segmento,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos,
                    CASE 
                        WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                       THEN mov.IMPORTE ELSE 0 END) > 0 
                        THEN ROUND(((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                             THEN mov.IMPORTE ELSE 0 END) - 
                                   SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017') 
                                            THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                                   SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                            THEN mov.IMPORTE ELSE 0 END)) * 100, 2)
                        ELSE 0 
                    END as margen_neto_pct
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY margen_neto_pct DESC) as ranking,
                gestor,
                centro,
                segmento,
                margen_neto_pct,
                ingresos,
                gastos,
                (ingresos - gastos) as beneficio_neto
            FROM margen_gestores
            WHERE margen_neto_pct IS NOT NULL
            ORDER BY margen_neto_pct DESC
            LIMIT ?
        """
        params = (periodo, limit)
    
    start_time = datetime.now()
    results = execute_query(query, params)
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return QueryResult(
        data=results or [],
        query_type=f"top_performers_{metric}",
        execution_time=execution_time,
        row_count=len(results) if results else 0,
        query_sql=query
    )
# =================================================================
# 8. GENERADOR DINÁMICO DE QUERIES (GPT-4) 
# =================================================================

def generate_dynamic_query(self, user_question: str, gestor_context: Dict[str, Any] = None) -> QueryResult:
    """
    Generador dinámico de queries usando Azure OpenAI para preguntas complejas
    
    CASO DE USO: "¿Cuántos contratos hipotecarios nuevos tiene Ana vs el mes pasado?"
    FUNCIÓN: Genera SQL dinámico para preguntas que no tienen query predefinida
    """
    try:
        from utils.initial_agent import iniciar_agente_llm
        
        # Construir contexto para la generación
        context_info = ""
        if gestor_context and gestor_context.get('gestor_id'):
            context_info = f"Gestor ID: {gestor_context['gestor_id']}\n"
        
        # Prompt específico para generación de SQL
        generation_prompt = f"""
        Genera una consulta SQL para responder esta pregunta de un usuario de Control de Gestión:
        
        PREGUNTA: "{user_question}"
        
        CONTEXTO:
        {context_info}
        
        TABLAS DISPONIBLES:
        - MAESTRO_GESTORES (GESTOR_ID, DESC_GESTOR, CENTRO, SEGMENTO_ID)
        - MAESTRO_CONTRATOS (CONTRATO_ID, GESTOR_ID, CLIENTE_ID, PRODUCTO_ID, FECHA_ALTA)
        - MOVIMIENTOS_CONTRATOS (CONTRATO_ID, CUENTA_ID, IMPORTE, FECHA)
        - MAESTRO_PRODUCTOS (PRODUCTO_ID, DESC_PRODUCTO)
        - MAESTRO_CENTROS (CENTRO_ID, DESC_CENTRO, IND_CENTRO_FINALISTA)
        - MAESTRO_SEGMENTOS (SEGMENTO_ID, DESC_SEGMENTO)
        - MAESTRO_CUENTAS (CUENTA_ID, DESC_CUENTA, LINEA_CDR)
        - MAESTRO_LINEA_CDR (COD_LINEA_CDR, DESC_LINEA_CDR)
        
        CÓDIGOS IMPORTANTES:
        - Ingresos: COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012')
        - Gastos: COD_LINEA_CDR IN ('CR0014', 'CR0016', 'CR0017')
        - Producto Fondos: PRODUCTO_ID = '600100300300'
        - Fechas: usar strftime('%Y-%m', fecha) para filtros mensuales
        
        Genera SOLO el SQL, sin explicaciones.
        """
        
        # Llamar a Azure OpenAI
        client = iniciar_agente_llm()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en SQL para bases de datos bancarias. Genera consultas SQL precisas y eficientes."},
                {"role": "user", "content": generation_prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        generated_sql = response.choices[0].message.content.strip()
        
        # Ejecutar la query generada
        start_time = datetime.now()
        results = execute_query(generated_sql)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🤖 Query dinámica generada y ejecutada exitosamente")
        
        return QueryResult(
            data=results or [],
            query_type="dynamic_generated",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=generated_sql
        )
        
    except Exception as e:
        logger.error(f"❌ Error en generación dinámica: {e}")
        return QueryResult(
            data=[{"error": f"No se pudo generar consulta para: {user_question}", "details": str(e)}],
            query_type="dynamic_error",
            execution_time=0,
            row_count=0,
            query_sql=""
        )
# =================================================================
# 9. MOTOR DE SELECCIÓN INTELIGENTE (AMPLIADO)
# =================================================================

def get_best_query_for_question(self, user_question: str, gestor_id: str = None) -> QueryResult:
    """
    Motor inteligente que selecciona la mejor query para una pregunta del usuario
    
    ALGORITMO:
    1. Clasificación inteligente con GPT-4
    2. Ejecución de query predefinida si se identifica
    3. Generación dinámica para preguntas complejas
    4. Fallback con análisis de palabras clave
    """
    try:
        from utils.initial_agent import iniciar_agente_llm
        
        # Lista de queries predefinidas disponibles (AMPLIADA)
        available_queries = [
            "get_cartera_completa_gestor_enhanced",
            "get_cartera_completa_gestor", 
            "get_contratos_activos_gestor", 
            "get_distribucion_productos_gestor_enhanced",
            "get_distribucion_productos_gestor",
            "calculate_margen_neto_gestor_enhanced",
            "calculate_margen_neto_gestor",
            "calculate_eficiencia_operativa_gestor_enhanced",
            "calculate_eficiencia_operativa_gestor",
            "calculate_roe_gestor_enhanced",
            "calculate_roe_gestor",
            "get_desviaciones_precio_gestor_enhanced",
            "get_desviaciones_precio_gestor",
            "get_distribucion_fondos_gestor",
            "get_alertas_criticas_gestor",
            "compare_gestor_septiembre_octubre",
            "get_ranking_gestores_por_kpi",
            "get_benchmarking_gestores",
            "get_top_performers_by_metric",
            "get_performance_por_centro",
            "get_analysis_por_segmento"
        ]
        
        # FASE 1: Clasificación inteligente con GPT-4
        classification_prompt = f"""
        Analiza esta pregunta de un usuario de Control de Gestión bancario y selecciona la función más apropiada:
        
        PREGUNTA: "{user_question}"
        
        FUNCIONES DISPONIBLES:
        {chr(10).join([f"- {query}" for query in available_queries])}
        
        INSTRUCCIONES:
        - Si la pregunta coincide claramente con una función, responde SOLO con el nombre de la función
        - Si la pregunta es muy específica o compleja, responde "DYNAMIC_QUERY"
        - Si no estás seguro, responde "DYNAMIC_QUERY"
        
        Responde SOLO con el nombre de la función o "DYNAMIC_QUERY".
        """
        
        client = iniciar_agente_llm()
        classification_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un clasificador experto de consultas bancarias. Sé preciso y conciso."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        predicted_query = classification_response.choices[0].message.content.strip()
        
        logger.info(f"🧠 Clasificación inteligente: '{user_question}' → {predicted_query}")
        
        # FASE 2: Ejecutar query predefinida si se identificó correctamente
        if predicted_query in available_queries:
            query_method = getattr(self, predicted_query)
            
            # Parámetros específicos según el método
            if "enhanced" in predicted_query or predicted_query in [
                "get_cartera_completa_gestor", "get_contratos_activos_gestor", 
                "get_distribucion_productos_gestor", "get_desviaciones_precio_gestor",
                "get_distribucion_fondos_gestor", "get_alertas_criticas_gestor"
            ]:
                if gestor_id:
                    if predicted_query in ["get_distribucion_fondos_gestor", "get_alertas_criticas_gestor"]:
                        # Estos métodos requieren período
                        periodo = "2025-10"
                        if "septiembre" in user_question.lower():
                            periodo = "2025-09"
                        result = query_method(gestor_id, periodo)
                    else:
                        result = query_method(gestor_id)
                else:
                    logger.warning(f"⚠️ Query {predicted_query} requiere gestor_id pero no se proporcionó")
                    return self.generate_dynamic_query(user_question, {"gestor_id": gestor_id})
            
            elif predicted_query in [
                "calculate_margen_neto_gestor_enhanced", "calculate_margen_neto_gestor",
                "calculate_eficiencia_operativa_gestor_enhanced", "calculate_eficiencia_operativa_gestor",
                "calculate_roe_gestor_enhanced", "calculate_roe_gestor"
            ]:
                if gestor_id:
                    periodo = "2025-10"
                    if "septiembre" in user_question.lower():
                        periodo = "2025-09"
                    result = query_method(gestor_id, periodo)
                else:
                    return self.generate_dynamic_query(user_question, {"gestor_id": gestor_id})
            
            elif predicted_query == "compare_gestor_septiembre_octubre":
                if gestor_id:
                    result = query_method(gestor_id)
                else:
                    return self.generate_dynamic_query(user_question, {"gestor_id": gestor_id})
            
            elif predicted_query == "get_ranking_gestores_por_kpi":
                kpi_type = "margen_neto"
                if "eficiencia" in user_question.lower():
                    kpi_type = "eficiencia"
                elif "contratos" in user_question.lower() and "nuevos" in user_question.lower():
                    kpi_type = "nuevos_contratos"
                elif "roe" in user_question.lower():
                    kpi_type = "roe"
                result = query_method(kpi_type)
            
            elif predicted_query == "get_benchmarking_gestores":
                if gestor_id:
                    result = query_method(gestor_id)
                else:
                    return self.generate_dynamic_query(user_question, {"gestor_id": gestor_id})
            
            elif predicted_query == "get_top_performers_by_metric":
                metric = "margen_neto"
                if "roe" in user_question.lower():
                    metric = "roe"
                elif "eficiencia" in user_question.lower():
                    metric = "eficiencia"
                
                # Extraer límite si se menciona
                limit = 10
                if "top 5" in user_question.lower():
                    limit = 5
                elif "top 20" in user_question.lower():
                    limit = 20
                
                result = query_method(metric, limit)
            
            elif predicted_query in ["get_performance_por_centro", "get_analysis_por_segmento"]:
                result = query_method()
            
            else:
                result = query_method()
            
            logger.info(f"✅ Query predefinida ejecutada exitosamente: {predicted_query}")
            return result
        
        # FASE 3: Usar generación dinámica si no se identificó query predefinida
        elif predicted_query == "DYNAMIC_QUERY":
            logger.info(f"🤖 Usando generación dinámica para pregunta compleja: {user_question}")
            gestor_context = {"gestor_id": gestor_id} if gestor_id else None
            return self.generate_dynamic_query(user_question, gestor_context)
        
        else:
            logger.warning(f"⚠️ Clasificación no reconocida: {predicted_query}. Usando generación dinámica.")
            gestor_context = {"gestor_id": gestor_id} if gestor_id else None
            return self.generate_dynamic_query(user_question, gestor_context)
            
    except Exception as e:
        logger.error(f"❌ Error en motor de selección inteligente: {e}")
        logger.info(f"🔄 Fallback: Usando generación dinámica por error en clasificación")
        gestor_context = {"gestor_id": gestor_id} if gestor_id else None
        return self.generate_dynamic_query(user_question, gestor_context)
# =================================================================
# 10. FUNCIONES DE ANÁLISIS Y MÉTRICAS DEL SISTEMA
# =================================================================

def get_query_usage_metrics(self) -> Dict[str, Any]:
    """Métricas de uso del sistema de queries"""
    return {
        "total_queries_available": len([method for method in dir(self) if method.startswith('get_') or method.startswith('calculate_')]),
        "enhanced_queries": len([method for method in dir(self) if 'enhanced' in method]),
        "cache_usage": len(self.query_cache),
        "system_status": "operational",
        "version": "2.0_enhanced_with_kpi_integration"
    }

def validate_gestor_access(self, gestor_id: str, user_role: str = "gestor_comercial") -> bool:
    """Validación de acceso del gestor (placeholder para sistema de permisos)"""
    # En un sistema real, aquí se validarían permisos
    if user_role == "control_gestion":
        return True  # Control de gestión ve todo
    
    # Por ahora, permitir acceso básico
    return True

def clear_cache(self):
    """Limpia el cache de queries"""
    self.query_cache.clear()
    logger.info("🧹 Cache de queries limpiado")

# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA ACTUALIZADAS
# =================================================================

# Instancia global para uso en toda la aplicación
gestor_queries = GestorQueries()

# ✅ FUNCIONES DE CONVENIENCIA PARA VERSIONES ENHANCED
def get_gestor_performance_enhanced(gestor_id: str, periodo: str = None):
    """Función de conveniencia para performance completo mejorado"""
    return gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo)

def get_all_gestores_enhanced():
    """Función de conveniencia para todos los gestores mejorado"""
    return gestor_queries.get_all_gestores_enhanced()

def get_cartera_gestor_enhanced(gestor_id: str, fecha: str = "2025-10"):
    """Función de conveniencia para cartera mejorada con análisis KPI"""
    return gestor_queries.get_cartera_completa_gestor_enhanced(gestor_id, fecha)

def get_kpis_gestor_enhanced(gestor_id: str, periodo: str = "2025-10"):
    """Función de conveniencia para KPIs mejorados con clasificaciones automáticas"""
    margen = gestor_queries.calculate_margen_neto_gestor_enhanced(gestor_id, periodo)
    eficiencia = gestor_queries.calculate_eficiencia_operativa_gestor_enhanced(gestor_id, periodo)
    roe = gestor_queries.calculate_roe_gestor_enhanced(gestor_id, periodo)
    return {
        "margen_neto_enhanced": margen,
        "eficiencia_enhanced": eficiencia,
        "roe_enhanced": roe
    }

def get_desviaciones_gestor_enhanced(gestor_id: str, umbral: float = 15.0):
    """Función de conveniencia para análisis mejorado de desviaciones"""
    return gestor_queries.get_desviaciones_precio_gestor_enhanced(gestor_id, umbral)

# Funciones de conveniencia originales mantenidas
def get_cartera_gestor(gestor_id: str):
    """Función de conveniencia para obtener cartera de un gestor"""
    return gestor_queries.get_cartera_completa_gestor(gestor_id)

def get_kpis_gestor(gestor_id: str, periodo: str = "2025-10"):
    """Función de conveniencia para obtener KPIs principales de un gestor"""
    margen = gestor_queries.calculate_margen_neto_gestor(gestor_id, periodo)
    eficiencia = gestor_queries.calculate_eficiencia_operativa_gestor(gestor_id, periodo)
    roe = gestor_queries.calculate_roe_gestor(gestor_id, periodo)
    return {
        "margen_neto": margen,
        "eficiencia": eficiencia,
        "roe": roe
    }

def get_alertas_gestor(gestor_id: str, periodo: str = "2025-10"):
    """Función de conveniencia para obtener alertas de un gestor"""
    return gestor_queries.get_alertas_criticas_gestor(gestor_id, periodo)

def get_benchmarking_gestor(gestor_id: str, periodo: str = "2025-10"):
    """Función de conveniencia para benchmarking de un gestor"""
    return gestor_queries.get_benchmarking_gestores(gestor_id, periodo)

def ask_about_gestor(question: str, gestor_id: str = None):
    """
    Función de conveniencia MEJORADA para hacer cualquier pregunta sobre gestores
    Utiliza el motor de selección inteligente
    """
    return gestor_queries.get_best_query_for_question(question, gestor_id)

def get_query_metrics():
    """Función de conveniencia para obtener métricas del sistema"""
    return gestor_queries.get_query_usage_metrics()

def get_centro_performance(centro_id: int = None, periodo: str = "2025-10"):
    """Función de conveniencia para análisis por centro"""
    return gestor_queries.get_performance_por_centro(centro_id, periodo)

def get_segmento_analysis(segmento_id: str = None, periodo: str = "2025-10"):
    """Función de conveniencia para análisis por segmento"""
    return gestor_queries.get_analysis_por_segmento(segmento_id, periodo)

def get_top_performers(metric: str = "margen_neto", limit: int = 10, periodo: str = "2025-10"):
    """Función de conveniencia para top performers"""
    return gestor_queries.get_top_performers_by_metric(metric, limit, periodo)

# ✅ FUNCIÓN INTELIGENTE PRINCIPAL
def intelligent_query(user_question: str, gestor_id: str = None) -> QueryResult:
    """
    FUNCIÓN PRINCIPAL del sistema de queries inteligentes
    
    USO: intelligent_query("¿Cómo está el margen de Juan este mes?", gestor_id="1")
    """
    return gestor_queries.get_best_query_for_question(user_question, gestor_id)

if __name__ == "__main__":
    # Tests del sistema completo
    print("🧪 Testing sistema de queries enhanced...")
    
    # Test 1: Query enhanced
    try:
        result = get_cartera_gestor_enhanced("1")
        print(f"✅ Test 1 - Cartera enhanced: {result.row_count} filas")
    except Exception as e:
        print(f"❌ Test 1 error: {e}")
    
    # Test 2: Motor inteligente
    try:
        result = intelligent_query("¿Cuál es el margen neto del gestor 1?", "1")
        print(f"✅ Test 2 - Query inteligente: {result.query_type}")
    except Exception as e:
        print(f"❌ Test 2 error: {e}")
    
    print("🏁 Testing completado!")
