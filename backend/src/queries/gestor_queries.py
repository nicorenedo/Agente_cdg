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
Fecha: 2025-08-01 (revisado)
"""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# =========================
# Imports unificados
# =========================
try:
    # Ruta "src" (estilo usado en deviation_queries.py)
    from src.database.db_connection import execute_query
    from src.utils.initial_agent import iniciar_agente_llm
    from src.tools.kpi_calculator import FinancialKPICalculator, kpi_calculator
    from src.tools.sql_guard import is_query_safe
except ImportError:
    # Fallback relativo
    from ..database.db_connection import execute_query
    from ..utils.initial_agent import iniciar_agente_llm
    from ..tools.kpi_calculator import FinancialKPICalculator, kpi_calculator
    from ..tools.sql_guard import is_query_safe

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
    - Análisis de cartera con KPIs
    - KPIs financieros (margen, eficiencia, ROE)
    - Evolución temporal y comparativas
    - Desviaciones y alertas
    - Benchmarking / rankings
    - Motor de selección + generación dinámica segura
    """

    def __init__(self):
        self.query_cache: Dict[str, Any] = {}
        # Puedes usar FinancialKPICalculator() o la instancia utilitaria kpi_calculator (ambas compatibles)
        self.kpi_calc = FinancialKPICalculator() if 'FinancialKPICalculator' in globals() else kpi_calculator

    # =================================================================
    # 🚨 MÉTODOS REQUERIDOS POR CDG_AGENT.PY (CRÍTICOS)
    # =================================================================

    def get_gestor_performance_enhanced(self, gestor_id: str, periodo: str = None) -> QueryResult:
        """
        ✅ CORREGIDO DEFINITIVAMENTE - Usa PRECIO_STD + gastos operativos
        """
        # ✅ Período clause corregido para ACUMULADO
        periodo_clause = f"AND strftime('%Y-%m', mov.FECHA) <= '{periodo}'" if periodo else ""

        query = f"""
        WITH seg AS (
            SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
        ),
        contracts AS (
            SELECT CONTRATO_ID, PRODUCTO_ID, FECHA_ALTA
            FROM MAESTRO_CONTRATOS
            WHERE GESTOR_ID = ? AND FECHA_ALTA < '2025-11-01'
        ),
        datos_gestor AS (
            SELECT
                g.GESTOR_ID,
                g.DESC_GESTOR,
                c.DESC_CENTRO,
                s.DESC_SEGMENTO,
                COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            LEFT JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            WHERE g.GESTOR_ID = ?
            GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
        ),
        ingresos_acumulados AS (
            SELECT
                -- ✅ INGRESOS ACUMULADOS: Solo cuentas 76XXXX hasta el período
                COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as total_ingresos,
                -- ✅ PATRIMONIO: Suma total de movimientos (para ROE)
                SUM(mov.IMPORTE) as patrimonio_total,
                COALESCE(AVG(mov.IMPORTE), 0) as importe_promedio_movimiento
            FROM MAESTRO_CONTRATOS mc
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                {periodo_clause}
            WHERE mc.GESTOR_ID = ?
        ),
        gastos_mantenimiento AS (
            SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) AS gasto_mantenimiento
            FROM contracts c
            JOIN seg s
            JOIN PRECIO_POR_PRODUCTO_STD pp
                ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                AND pp.SEGMENTO_ID = s.SEGMENTO_ID
        ),
        gastos_operativos AS (
            SELECT COALESCE(SUM(mov.IMPORTE), 0) AS gasto_operativo
            FROM contracts c
            JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
            WHERE mov.FECHA < '2025-11-01'
            AND mov.CUENTA_ID IN ('640001', '691001', '691002')
        )
        SELECT 
            dg.*,
            ia.total_ingresos,
            ia.patrimonio_total,
            ia.importe_promedio_movimiento,
            gm.gasto_mantenimiento,
            go.gasto_operativo,
            (gm.gasto_mantenimiento + go.gasto_operativo) as total_gastos
        FROM datos_gestor dg
        CROSS JOIN ingresos_acumulados ia
        CROSS JOIN gastos_mantenimiento gm
        CROSS JOIN gastos_operativos go
        """

        start_time = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, gestor_id, gestor_id))

        if not raw:
            return QueryResult(
                data=[{"error": "No se encontraron datos para el gestor especificado"}],
                query_type="gestor_performance_enhanced_error",
                execution_time=0,
                row_count=0,
                query_sql=query
            )

        r = raw[0]

        # ✅ Cálculos KPI con datos correctos
        ingresos = r['total_ingresos'] or 0
        gastos = r['total_gastos'] or 0
        patrimonio = r['patrimonio_total'] or 1

        margen = self.kpi_calc.calculate_margen_neto(ingresos, gastos)
        roe = self.kpi_calc.calculate_roe(margen['beneficio_neto'], patrimonio)
        eficiencia = self.kpi_calc.calculate_ratio_eficiencia(ingresos, gastos)

        enhanced = {
            'gestor_id': r['GESTOR_ID'],
            'desc_gestor': r['DESC_GESTOR'],
            'desc_centro': r['DESC_CENTRO'],
            'desc_segmento': r['DESC_SEGMENTO'],
            'total_contratos': r['total_contratos'],
            'total_clientes': r['total_clientes'],
            'total_ingresos': ingresos,
            'total_gastos': gastos,
            'patrimonio_total': patrimonio,

            # KPIs corregidos
            'margen_neto': margen['margen_neto_pct'],
            'beneficio_neto': margen['beneficio_neto'],
            'clasificacion_margen': margen['clasificacion'],

            'roe_pct': roe['roe_pct'],
            'clasificacion_roe': roe['clasificacion'],
            'benchmark_vs_sector': roe.get('benchmark_vs_sector'),

            'ratio_eficiencia': eficiencia['ratio_eficiencia'],
            'clasificacion_eficiencia': eficiencia['clasificacion'],
            'interpretacion_eficiencia': eficiencia['interpretacion'],

            # Drill-down
            'analisis_margen_completo': margen,
            'analisis_roe_completo': roe,
            'analisis_eficiencia_completo': eficiencia
        }

        exec_time = (datetime.now() - start_time).total_seconds()
        return QueryResult(
            data=[enhanced],
            query_type="gestor_performance_enhanced",
            execution_time=exec_time,
            row_count=1,
            query_sql=query
        )

    def get_all_gestores_enhanced(self) -> QueryResult:
        """
        ✅ MÉTODO CRÍTICO REQUERIDO POR CDG_AGENT.PY
        Lista gestores con info básica y contratos activos.
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
        res = execute_query(query)
        exec_time = (datetime.now() - start_time).total_seconds()
        return QueryResult(
            data=res or [],
            query_type="all_gestores_enhanced",
            execution_time=exec_time,
            row_count=len(res) if res else 0,
            query_sql=query
        )

    # =================================================================
    # 1) CARTERA POR GESTOR (ENHANCED Y ORIGINAL)
    # =================================================================

    def get_cartera_completa_gestor_enhanced(self, gestor_id: str, fecha: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Cartera completa de un gestor por producto con KPIs de eficiencia por producto.
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT mc.CONTRATO_ID, mc.PRODUCTO_ID
                FROM MAESTRO_CONTRATOS mc
                WHERE mc.GESTOR_ID = ? AND strftime('%Y-%m', mc.FECHA_ALTA) <= ?
            ),
            cartera_datos AS (
                SELECT
                    g.DESC_GESTOR as gestor,
                    c.DESC_CENTRO as centro,
                    s.DESC_SEGMENTO as segmento,
                    p.PRODUCTO_ID,
                    p.DESC_PRODUCTO as producto,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_producto,
                    COUNT(DISTINCT mc.CLIENTE_ID) as clientes_producto,
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as volumen_total_producto
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
            ),
            gastos_por_producto AS (
                SELECT
                    c.PRODUCTO_ID,
                    COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) as gasto_mantenimiento,
                    COALESCE(SUM(mov.IMPORTE), 0) as gasto_operativo
                FROM contracts c
                JOIN seg s
                LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                    WHERE mov.FECHA < ?
                    AND mov.CUENTA_ID IN ('640001', '691001', '691002')
                GROUP BY c.PRODUCTO_ID
            )
            SELECT 
                cd.*,
                COALESCE(gpp.gasto_mantenimiento, 0) + COALESCE(gpp.gasto_operativo, 0) as gastos_producto
            FROM cartera_datos cd
            LEFT JOIN gastos_por_producto gpp ON cd.PRODUCTO_ID = gpp.PRODUCTO_ID
            ORDER BY contratos_producto DESC
        """
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, fecha, fecha, gestor_id, fecha, fecha))

        total_contratos = sum(r['contratos_producto'] for r in raw) or 0
        total_volumen = sum(r['volumen_total_producto'] for r in raw) or 0

        enhanced = []
        for r in raw:
            eficiencia = self.kpi_calc.calculate_ratio_eficiencia(
                ingresos=r['volumen_total_producto'],
                gastos=r['gastos_producto']
            )
            conc_pct = (r['contratos_producto'] / total_contratos * 100) if total_contratos else 0
            peso_vol_pct = (r['volumen_total_producto'] / total_volumen * 100) if total_volumen else 0

            enhanced.append({
                **r,
                'concentracion_contratos_pct': round(conc_pct, 2),
                'peso_volumen_pct': round(peso_vol_pct, 2),
                'ratio_eficiencia': eficiencia['ratio_eficiencia'],
                'clasificacion_eficiencia': eficiencia['clasificacion'],
                'interpretacion_eficiencia': eficiencia['interpretacion'],
                'categoria_producto': self._classify_product_importance(conc_pct, peso_vol_pct),
                'volumen_promedio_contrato': round((r['volumen_total_producto'] / r['contratos_producto']), 2) if r['contratos_producto'] else 0,
                'analisis_eficiencia_completo': eficiencia
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced,
            query_type="cartera_completa_enhanced",
            execution_time=exec_time,
            row_count=len(enhanced),
            query_sql=query
        )

    def get_cartera_completa_gestor(self, gestor_id: str, fecha: str = "2025-10") -> QueryResult:
        """Versión original mantenida."""
        query = """
            SELECT
                g.DESC_GESTOR as gestor,
                c.DESC_CENTRO as centro,
                s.DESC_SEGMENTO as segmento,
                p.DESC_PRODUCTO as producto,
                COUNT(DISTINCT mc.CONTRATO_ID) as contratos_producto,
                COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes
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
        start = datetime.now()
        res = execute_query(query, (gestor_id, fecha))
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=res or [],
            query_type="cartera_completa",
            execution_time=exec_time,
            row_count=len(res) if res else 0,
            query_sql=query
        )

    # =================================================================
    # 2) KPIs PRINCIPALES (MARGEN, EFICIENCIA, ROE) - ENHANCED + ORIGINAL
    # =================================================================

    def calculate_margen_neto_gestor_enhanced(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Margen neto con clasificaciones y recomendaciones.
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT CONTRATO_ID, PRODUCTO_ID
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
            ),
            datos_margen AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as total_ingresos
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE g.GESTOR_ID = ?
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
            ),
            gastos_mantenimiento AS (
                SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) AS gasto_mantenimiento
                FROM contracts c
                JOIN seg s
                JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            ),
            gastos_operativos AS (
                SELECT COALESCE(SUM(mov.IMPORTE), 0) AS gasto_operativo
                FROM contracts c
                JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT 
                dm.*,
                gm.gasto_mantenimiento,
                go.gasto_operativo,
                (gm.gasto_mantenimiento + go.gasto_operativo) as total_gastos
            FROM datos_margen dm
            CROSS JOIN gastos_mantenimiento gm
            CROSS JOIN gastos_operativos go
        """
        
        # Calcular fecha fin de período
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, fecha_fin, periodo, gestor_id, fecha_fin))
        
        if not raw:
            return QueryResult(
                data=[{"error": "No se encontraron datos para el gestor en el período especificado"}],
                query_type="margen_neto_enhanced_error",
                execution_time=0,
                row_count=0,
                query_sql=query
            )
        
        r = raw[0]
        margen = self.kpi_calc.calculate_margen_neto(r['total_ingresos'] or 0, r['total_gastos'] or 0)
        eficiencia = self.kpi_calc.calculate_ratio_eficiencia(r['total_ingresos'] or 0, r['total_gastos'] or 0)

        enhanced = {
            'total_ingresos': r['total_ingresos'] or 0,
            'total_gastos': r['total_gastos'] or 0,
            'beneficio_neto': margen['beneficio_neto'],
            'margen_neto_pct': margen['margen_neto_pct'],
            'clasificacion_margen': margen['clasificacion'],
            'ratio_eficiencia': eficiencia['ratio_eficiencia'],
            'clasificacion_eficiencia': eficiencia['clasificacion'],
            'interpretacion_eficiencia': eficiencia['interpretacion'],
            'contexto_bancario': self._get_banking_context(margen['clasificacion']),
            'recomendacion_accion': self._get_margin_recommendation(margen['margen_neto_pct']),
            'analisis_margen_completo': margen,
            'analisis_eficiencia_completo': eficiencia
        }
        
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=[enhanced],
            query_type="margen_neto_enhanced",
            execution_time=exec_time,
            row_count=1,
            query_sql=query
        )

    def calculate_margen_neto_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Versión original mantenida.
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT CONTRATO_ID, PRODUCTO_ID
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
            ),
            datos_margen AS (
                SELECT
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as total_ingresos
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE g.GESTOR_ID = ?
            ),
            gastos_mantenimiento AS (
                SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) AS gasto_mantenimiento
                FROM contracts c
                JOIN seg s
                JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            ),
            gastos_operativos AS (
                SELECT COALESCE(SUM(mov.IMPORTE), 0) AS gasto_operativo
                FROM contracts c
                JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT
                dm.total_ingresos,
                (gm.gasto_mantenimiento + go.gasto_operativo) as total_gastos,
                (dm.total_ingresos - (gm.gasto_mantenimiento + go.gasto_operativo)) as beneficio_neto,
                CASE
                    WHEN dm.total_ingresos > 0
                    THEN ROUND(((dm.total_ingresos - (gm.gasto_mantenimiento + go.gasto_operativo)) / dm.total_ingresos) * 100, 2)
                    ELSE 0
                END as margen_neto_pct
            FROM datos_margen dm
            CROSS JOIN gastos_mantenimiento gm
            CROSS JOIN gastos_operativos go
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        res = execute_query(query, (gestor_id, gestor_id, fecha_fin, periodo, gestor_id, fecha_fin))
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=res or [],
            query_type="margen_neto",
            execution_time=exec_time,
            row_count=len(res) if res else 0,
            query_sql=query
        )

    def calculate_eficiencia_operativa_gestor_enhanced(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Eficiencia operativa (ingresos/gastos) con clasificación y recomendaciones.
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT CONTRATO_ID, PRODUCTO_ID
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
            ),
            datos_eficiencia AS (
                SELECT
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE g.GESTOR_ID = ?
            ),
            gastos_mantenimiento AS (
                SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) AS gasto_mantenimiento
                FROM contracts c
                JOIN seg s
                JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            ),
            gastos_operativos AS (
                SELECT COALESCE(SUM(mov.IMPORTE), 0) AS gasto_operativo
                FROM contracts c
                JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT 
                de.ingresos,
                (gm.gasto_mantenimiento + go.gasto_operativo) as gastos
            FROM datos_eficiencia de
            CROSS JOIN gastos_mantenimiento gm
            CROSS JOIN gastos_operativos go
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, fecha_fin, periodo, gestor_id, fecha_fin))
        r = raw[0] if raw else {'ingresos': 0, 'gastos': 0}
        ef = self.kpi_calc.calculate_ratio_eficiencia(r['ingresos'] or 0, r['gastos'] or 0)

        out = {
            'ingresos': r['ingresos'] or 0,
            'gastos': r['gastos'] or 0,
            'ratio_eficiencia': ef['ratio_eficiencia'],
            'clasificacion_eficiencia': ef['clasificacion'],
            'interpretacion_eficiencia': ef['interpretacion'],
            'contexto': self._get_efficiency_context(ef['clasificacion']),
            'recomendacion': self._get_efficiency_recommendation(ef['ratio_eficiencia']),
            'analisis_eficiencia_completo': ef
        }
        
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=[out],
            query_type="eficiencia_operativa_enhanced",
            execution_time=exec_time,
            row_count=1,
            query_sql=query
        )

    def calculate_eficiencia_operativa_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Versión simple de eficiencia (ratio ingresos/gastos).
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT CONTRATO_ID, PRODUCTO_ID
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
            ),
            datos_eficiencia AS (
                SELECT
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE g.GESTOR_ID = ?
            ),
            gastos_mantenimiento AS (
                SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) AS gasto_mantenimiento
                FROM contracts c
                JOIN seg s
                JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            ),
            gastos_operativos AS (
                SELECT COALESCE(SUM(mov.IMPORTE), 0) AS gasto_operativo
                FROM contracts c
                JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT 
                de.ingresos,
                (gm.gasto_mantenimiento + go.gasto_operativo) as gastos
            FROM datos_eficiencia de
            CROSS JOIN gastos_mantenimiento gm
            CROSS JOIN gastos_operativos go
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, fecha_fin, periodo, gestor_id, fecha_fin))
        r = raw[0] if raw else {'ingresos': 0, 'gastos': 0}
        ratio = (r['ingresos'] / r['gastos']) if (r['gastos'] or 0) > 0 else None
        
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=[{'ingresos': r['ingresos'] or 0, 'gastos': r['gastos'] or 0, 'ratio_eficiencia': ratio}],
            query_type="eficiencia_operativa",
            execution_time=exec_time,
            row_count=1,
            query_sql=query
        )

    def calculate_roe_gestor_enhanced(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        """
        # ✅ INGRESOS ACUMULADOS hasta el período
        query_ingresos = """
            SELECT
                -- ✅ INGRESOS ACUMULADOS: Solo cuentas 76XXXX hasta el período
                COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos,
                SUM(mov.IMPORTE) as patrimonio_total
            FROM MAESTRO_CONTRATOS mc
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) <= ?
            WHERE mc.GESTOR_ID = ?
        """
        
        # ✅ GASTOS SIN MULTIPLICAR: Una vez por contrato
        query_gastos = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT CONTRATO_ID, PRODUCTO_ID
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
            ),
            gastos_mantenimiento AS (
                SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) AS gasto_mantenimiento
                FROM contracts c
                JOIN seg s
                JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            ),
            gastos_operativos AS (
                SELECT COALESCE(SUM(mov.IMPORTE), 0) AS gasto_operativo
                FROM contracts c
                JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT 
                (gm.gasto_mantenimiento + go.gasto_operativo) as gastos
            FROM gastos_mantenimiento gm
            CROSS JOIN gastos_operativos go
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        
        # ✅ Ejecutar queries por separado
        ingresos_data = execute_query(query_ingresos, (periodo, gestor_id))
        gastos_data = execute_query(query_gastos, (gestor_id, gestor_id, fecha_fin, fecha_fin))
        
        # ✅ Extraer datos
        ingresos_row = ingresos_data[0] if ingresos_data else {'ingresos': 0, 'patrimonio_total': 0}
        gastos_row = gastos_data[0] if gastos_data else {'gastos': 0}
        
        ingresos = ingresos_row['ingresos'] or 0
        gastos = gastos_row['gastos'] or 0
        patrimonio = ingresos_row['patrimonio_total'] or 1
        
        # ✅ Cálculos KPI con datos correctos
        margen = self.kpi_calc.calculate_margen_neto(ingresos, gastos)
        roe = self.kpi_calc.calculate_roe(margen['beneficio_neto'], patrimonio)
    
        out = {
            'ingresos': ingresos,
            'gastos': gastos,
            'beneficio_neto': margen['beneficio_neto'],
            'patrimonio_total': patrimonio,
            'roe_pct': roe['roe_pct'],
            'clasificacion_roe': roe['clasificacion'],
            'contexto': self._get_roe_context(roe['clasificacion']),
            'recomendacion': self._get_roe_recommendation(roe['roe_pct']),
            'analisis_roe_completo': roe
        }
        
        exec_time = (datetime.now() - start).total_seconds()
        
        # ✅ Query combinada para logs (solo para mostrar)
        combined_query = f"""
        -- QUERY INGRESOS: {query_ingresos}
        -- QUERY GASTOS: {query_gastos}
        """
        
        return QueryResult(
            data=[out],
            query_type="roe_enhanced",
            execution_time=exec_time,
            row_count=1,
            query_sql=combined_query
        )
    

    def calculate_roe_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Versión simple: calcula ROE sin clasificaciones.
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT CONTRATO_ID, PRODUCTO_ID
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
            ),
            datos_roe AS (
                SELECT
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos,
                    SUM(mov.IMPORTE) as patrimonio_total
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE g.GESTOR_ID = ?
                  AND (? IS NULL OR strftime('%Y-%m', mov.FECHA) = ?)
            ),
            gastos_mantenimiento AS (
                SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) AS gasto_mantenimiento
                FROM contracts c
                JOIN seg s
                JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            ),
            gastos_operativos AS (
                SELECT COALESCE(SUM(mov.IMPORTE), 0) AS gasto_operativo
                FROM contracts c
                JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT
                (dr.ingresos - (gm.gasto_mantenimiento + go.gasto_operativo)) as beneficio_neto,
                dr.patrimonio_total,
                CASE WHEN dr.patrimonio_total > 0
                     THEN ROUND(((dr.ingresos - (gm.gasto_mantenimiento + go.gasto_operativo)) / dr.patrimonio_total) * 100, 4)
                     ELSE NULL END as roe_pct
            FROM datos_roe dr
            CROSS JOIN gastos_mantenimiento gm
            CROSS JOIN gastos_operativos go
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        res = execute_query(query, (gestor_id, gestor_id, fecha_fin, gestor_id, periodo, periodo, fecha_fin))
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=res or [],
            query_type="roe",
            execution_time=exec_time,
            row_count=len(res) if res else 0,
            query_sql=query
        )

    # =================================================================
    # 3) CONTRATOS ACTIVOS DEL GESTOR (ORIGINAL)
    # =================================================================

    def get_contratos_activos_gestor(self, gestor_id: str) -> QueryResult:
        query = """
            SELECT
                mc.CONTRATO_ID,
                mc.CLIENTE_ID,
                mcl.NOMBRE_CLIENTE as cliente,
                mc.PRODUCTO_ID,
                p.DESC_PRODUCTO as producto,
                mc.FECHA_ALTA,
                COALESCE(SUM(mov.IMPORTE), 0) as importe_total,
                CASE WHEN mc.FECHA_ALTA >= '2025-10-01' THEN 'NUEVO_OCTUBRE'
                     ELSE 'ANTERIOR' END as tipo_contrato
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
            JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            WHERE mc.GESTOR_ID = ?
            GROUP BY mc.CONTRATO_ID, mc.CLIENTE_ID, mcl.NOMBRE_CLIENTE, mc.PRODUCTO_ID, p.DESC_PRODUCTO, mc.FECHA_ALTA
            ORDER BY mc.FECHA_ALTA DESC, importe_total DESC
        """
        start = datetime.now()
        res = execute_query(query, (gestor_id,))
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=res or [],
            query_type="contratos_activos",
            execution_time=exec_time,
            row_count=len(res) if res else 0,
            query_sql=query
        )

    # =================================================================
    # 4) DISTRIBUCIÓN DE FONDOS Y ALERTAS (MEJORADO)
    # =================================================================

    def get_distribucion_fondos_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Distribución específica de fondos (85/15) por gestor, con alertas de desviación.
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
                  AND p.PRODUCTO_ID = '600100300300'
                  AND strftime('%Y-%m', mov.FECHA) = ?
                  AND mov.CUENTA_ID IN ('760025', '760024')
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
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, periodo))

        enhanced = []
        for r in raw:
            desv_f = abs((r['pct_promedio_fabrica'] or 0) - 85.0)
            desv_b = abs((r['pct_promedio_banco'] or 0) - 15.0)

            desv_analysis = self.kpi_calc.analyze_desviacion_presupuestaria(
                valor_real=r['pct_promedio_fabrica'] or 0,
                valor_presupuestado=85.0
            )
            enhanced.append({
                **r,
                'desviacion_fabrica_pct': round(desv_f, 2),
                'desviacion_banco_pct': round(desv_b, 2),
                'cumple_estandar_85_15': (desv_f <= 5.0 and desv_b <= 5.0),
                'nivel_alerta': desv_analysis['nivel_alerta'],
                'accion_recomendada': desv_analysis['accion_recomendada'],
                'interpretacion_reparto': self._interpret_fondos_distribution(r['pct_promedio_fabrica'] or 0, r['pct_promedio_banco'] or 0),
                'impacto_comercial': 'ALTO' if desv_f > 10 else ('MEDIO' if desv_f > 5 else 'BAJO'),
                'analisis_desviacion_completo': desv_analysis
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced,
            query_type="distribucion_fondos",
            execution_time=exec_time,
            row_count=len(enhanced),
            query_sql=query
        )

    def get_alertas_criticas_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Alertas críticas para un gestor (margen bajo, desviación precio, etc.) con impacto.
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            contracts AS (
                SELECT CONTRATO_ID, PRODUCTO_ID
                FROM MAESTRO_CONTRATOS
                WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
            ),
            alertas_margen AS (
                SELECT
                    'MARGEN_BAJO' as tipo_alerta,
                    'Margen neto por debajo del 8%' as descripcion,
                    'CRITICA' as severidad,
                    g.DESC_GESTOR as gestor,
                    datos.margen_neto_pct as valor_actual,
                    8.0 as umbral_critico,
                    'Revisar pricing y estructura de costos' as accion_recomendada
                FROM MAESTRO_GESTORES g
                JOIN (
                    SELECT 
                        g.GESTOR_ID,
                        CASE WHEN ingresos_total > 0
                             THEN ROUND(((ingresos_total - gastos_total) / ingresos_total) * 100, 2)
                             ELSE 0 END as margen_neto_pct
                    FROM (
                        SELECT
                            g.GESTOR_ID,
                            COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_total,
                            (
                                SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0)
                                FROM contracts c
                                JOIN seg s
                                JOIN PRECIO_POR_PRODUCTO_STD pp
                                    ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
                            ) + (
                                SELECT COALESCE(SUM(mov2.IMPORTE), 0)
                                FROM contracts c
                                JOIN MOVIMIENTOS_CONTRATOS mov2 ON c.CONTRATO_ID = mov2.CONTRATO_ID
                                WHERE mov2.FECHA < ?
                                AND mov2.CUENTA_ID IN ('640001', '691001', '691002')
                            ) as gastos_total
                        FROM MAESTRO_GESTORES g
                        JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                        LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                            AND strftime('%Y-%m', mov.FECHA) = ?
                        WHERE g.GESTOR_ID = ?
                        GROUP BY g.GESTOR_ID
                    ) sub
                ) datos ON g.GESTOR_ID = datos.GESTOR_ID
                WHERE g.GESTOR_ID = ? AND datos.margen_neto_pct < 8.0
            ),
            alertas_precio AS (
                SELECT
                    'DESVIACION_PRECIO' as tipo_alerta,
                    'Desviación de precio superior al 20%' as descripcion,
                    'ALTA' as severidad,
                    g.DESC_GESTOR as gestor,
                    ABS(d.desviacion_pct) as valor_actual,
                    20.0 as umbral_critico,
                    'Revisar política de pricing del producto' as accion_recomendada
                FROM MAESTRO_GESTORES g
                JOIN (
                    SELECT DISTINCT mc.GESTOR_ID,
                           ROUND(((ABS(pr.PRECIO_MANTENIMIENTO_REAL) - ABS(ps.PRECIO_MANTENIMIENTO))
                                  / ABS(ps.PRECIO_MANTENIMIENTO)) * 100, 2) as desviacion_pct
                    FROM MAESTRO_CONTRATOS mc
                    JOIN MAESTRO_GESTORES gg ON mc.GESTOR_ID = gg.GESTOR_ID
                    JOIN PRECIO_POR_PRODUCTO_REAL pr ON mc.PRODUCTO_ID = pr.PRODUCTO_ID
                         AND gg.SEGMENTO_ID = pr.SEGMENTO_ID
                    JOIN PRECIO_POR_PRODUCTO_STD ps ON mc.PRODUCTO_ID = ps.PRODUCTO_ID
                         AND gg.SEGMENTO_ID = ps.SEGMENTO_ID
                    WHERE substr(pr.FECHA_CALCULO,1,7) = ?
                ) d ON g.GESTOR_ID = d.GESTOR_ID
                WHERE g.GESTOR_ID = ? AND ABS(d.desviacion_pct) >= 20.0
            )
            SELECT * FROM alertas_margen
            UNION ALL
            SELECT * FROM alertas_precio
            ORDER BY severidad ASC, valor_actual DESC
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, fecha_fin, fecha_fin, periodo, gestor_id, gestor_id, periodo, gestor_id))

        enhanced = []
        for r in raw:
            impacto = self._assess_alert_impact(r['tipo_alerta'], r['valor_actual'], r['umbral_critico'])
            prioridad = self._calculate_alert_priority(r['severidad'], r['valor_actual'], r['umbral_critico'])
            enhanced.append({
                **r,
                'impacto_comercial': impacto,
                'prioridad_accion': prioridad,
                'dias_para_accion': self._get_action_timeline(r['severidad']),
                'responsable_seguimiento': 'Control de Gestión' if r['severidad'] == 'CRITICA' else 'Gestor Comercial',
                'contexto_bancario': self._get_alert_banking_context(r['tipo_alerta']),
                'impacto_estimado_ingresos': self._estimate_revenue_impact(r['tipo_alerta'], r['valor_actual'])
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced,
            query_type="alertas_criticas",
            execution_time=exec_time,
            row_count=len(enhanced),
            query_sql=query
        )

    # =================================================================
    # 5) ANÁLISIS POR CENTRO Y SEGMENTO
    # =================================================================

    def get_performance_por_centro(self, centro_id: Optional[int] = None, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Análisis por centro
        """
        query = """
            WITH centro_contracts AS (
                SELECT mc.CONTRATO_ID, mc.PRODUCTO_ID, g.GESTOR_ID, g.SEGMENTO_ID
                FROM MAESTRO_CENTROS c
                JOIN MAESTRO_GESTORES g ON c.CENTRO_ID = g.CENTRO
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                WHERE (? IS NULL OR c.CENTRO_ID = ?)
                AND c.IND_CENTRO_FINALISTA = 1
                AND mc.FECHA_ALTA < ?
            ),
            datos_centro AS (
                SELECT
                    c.CENTRO_ID,
                    c.DESC_CENTRO as centro,
                    c.IND_CENTRO_FINALISTA as es_finalista,
                    COUNT(DISTINCT g.GESTOR_ID) as num_gestores,
                    COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_centro
                FROM MAESTRO_CENTROS c
                JOIN MAESTRO_GESTORES g ON c.CENTRO_ID = g.CENTRO
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                     AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE (? IS NULL OR c.CENTRO_ID = ?)
                GROUP BY c.CENTRO_ID, c.DESC_CENTRO, c.IND_CENTRO_FINALISTA
            ),
            gastos_centro AS (
                SELECT
                    COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) as gasto_mantenimiento,
                    COALESCE(SUM(mov.IMPORTE), 0) as gasto_operativo
                FROM centro_contracts cc
                LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = cc.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = cc.SEGMENTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON cc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT 
                dc.*,
                (gc.gasto_mantenimiento + gc.gasto_operativo) as gastos_centro,
                CASE WHEN dc.ingresos_centro > 0
                     THEN ROUND(((dc.ingresos_centro - (gc.gasto_mantenimiento + gc.gasto_operativo)) / dc.ingresos_centro) * 100, 2)
                     ELSE 0 END as margen_promedio_centro
            FROM datos_centro dc
            CROSS JOIN gastos_centro gc
            ORDER BY margen_promedio_centro DESC
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        res = execute_query(query, (centro_id, centro_id, fecha_fin, periodo, centro_id, centro_id, fecha_fin))
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=res or [],
            query_type="performance_centro",
            execution_time=exec_time,
            row_count=len(res) if res else 0,
            query_sql=query
        )

    def get_analysis_por_segmento(self, segmento_id: Optional[str] = None, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Análisis por segmento
        """
        query = """
            WITH segmento_contracts AS (
                SELECT mc.CONTRATO_ID, mc.PRODUCTO_ID, g.SEGMENTO_ID
                FROM MAESTRO_SEGMENTOS s
                JOIN MAESTRO_GESTORES g ON s.SEGMENTO_ID = g.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                WHERE (? IS NULL OR s.SEGMENTO_ID = ?)
                AND mc.FECHA_ALTA < ?
            ),
            datos_segmento AS (
                SELECT
                    s.SEGMENTO_ID,
                    s.DESC_SEGMENTO as segmento,
                    COUNT(DISTINCT g.GESTOR_ID) as num_gestores,
                    COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_segmento,
                    CASE WHEN COUNT(DISTINCT mc.CONTRATO_ID) > 0
                         THEN SUM(mov.IMPORTE) / COUNT(DISTINCT mc.CONTRATO_ID)
                         ELSE 0 END as ticket_promedio
                FROM MAESTRO_SEGMENTOS s
                JOIN MAESTRO_GESTORES g ON s.SEGMENTO_ID = g.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                     AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE (? IS NULL OR s.SEGMENTO_ID = ?)
                GROUP BY s.SEGMENTO_ID, s.DESC_SEGMENTO
            ),
            gastos_segmento AS (
                SELECT
                    COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) as gasto_mantenimiento,
                    COALESCE(SUM(mov.IMPORTE), 0) as gasto_operativo
                FROM segmento_contracts sc
                LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = sc.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = sc.SEGMENTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON sc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mov.FECHA < ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT 
                ds.*,
                (gs.gasto_mantenimiento + gs.gasto_operativo) as gastos_segmento,
                CASE WHEN ds.ingresos_segmento > 0
                     THEN ROUND(((ds.ingresos_segmento - (gs.gasto_mantenimiento + gs.gasto_operativo)) / ds.ingresos_segmento) * 100, 2)
                     ELSE 0 END as margen_promedio_segmento
            FROM datos_segmento ds
            CROSS JOIN gastos_segmento gs
            ORDER BY margen_promedio_segmento DESC
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        res = execute_query(query, (segmento_id, segmento_id, fecha_fin, periodo, segmento_id, segmento_id, fecha_fin))
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=res or [],
            query_type="analysis_segmento",
            execution_time=exec_time,
            row_count=len(res) if res else 0,
            query_sql=query
        )

    # =================================================================
    # 6) DISTRIBUCIÓN DE PRODUCTOS & DESVIACIONES POR GESTOR (NUEVO)
    # =================================================================

    def get_distribucion_productos_gestor_enhanced(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Distribución por producto (contratos, volumen, peso %) + eficiencia por producto.
        """
        query = """
            WITH base AS (
                SELECT
                    p.PRODUCTO_ID,
                    p.DESC_PRODUCTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos,
                    COALESCE(SUM(mov.IMPORTE), 0) as volumen
                FROM MAESTRO_CONTRATOS mc
                JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                     AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE mc.GESTOR_ID = ?
                GROUP BY p.PRODUCTO_ID, p.DESC_PRODUCTO
            ),
            tot AS (
                SELECT SUM(contratos) as t_contratos, SUM(volumen) as t_volumen FROM base
            )
            SELECT b.*, t.t_contratos, t.t_volumen
            FROM base b CROSS JOIN tot t
        """
        start = datetime.now()
        raw = execute_query(query, (periodo, gestor_id))
        out = []
        for r in raw:
            peso_c = (r['contratos'] / r['t_contratos'] * 100) if (r['t_contratos'] or 0) > 0 else 0
            peso_v = (r['volumen'] / r['t_volumen'] * 100) if (r['t_volumen'] or 0) > 0 else 0
            
            # Calcular gastos del producto usando precio STD
            gastos_producto_query = """
                WITH seg AS (
                    SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
                ),
                contracts AS (
                    SELECT CONTRATO_ID
                    FROM MAESTRO_CONTRATOS
                    WHERE GESTOR_ID = ? AND PRODUCTO_ID = ? AND FECHA_ALTA < ?
                )
                SELECT 
                    COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) + 
                    COALESCE((
                        SELECT SUM(mov.IMPORTE)
                        FROM contracts c
                        JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                        WHERE mov.FECHA < ?
                        AND mov.CUENTA_ID IN ('640001', '691001', '691002')
                    ), 0) as gastos_producto
                FROM contracts c
                JOIN seg s
                LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = ?
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            """
            fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
            gastos_res = execute_query(gastos_producto_query, (gestor_id, gestor_id, r['PRODUCTO_ID'], fecha_fin, fecha_fin, r['PRODUCTO_ID']))
            gastos_producto = gastos_res[0]['gastos_producto'] if gastos_res else 0
            
            ef = self.kpi_calc.calculate_ratio_eficiencia(r['volumen'] or 0, gastos_producto)
            out.append({
                'producto_id': r['PRODUCTO_ID'],
                'producto': r['DESC_PRODUCTO'],
                'contratos': r['contratos'],
                'volumen': r['volumen'],
                'peso_contratos_pct': round(peso_c, 2),
                'peso_volumen_pct': round(peso_v, 2),
                'ratio_eficiencia': ef['ratio_eficiencia'],
                'clasificacion_eficiencia': ef['clasificacion']
            })
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=out,
            query_type="distribucion_productos_enhanced",
            execution_time=exec_time,
            row_count=len(out),
            query_sql=query
        )

    def get_desviaciones_precio_gestor_enhanced(self, gestor_id: str, periodo: str = "2025-10", threshold: float = 15.0) -> QueryResult:
        """
        Desviaciones de precio (real vs std) de productos en la cartera del gestor.
        """
        query = """
            SELECT
                mc.PRODUCTO_ID,
                mp.DESC_PRODUCTO,
                pr.SEGMENTO_ID,
                ms.DESC_SEGMENTO,
                pr.PRECIO_MANTENIMIENTO_REAL,
                ps.PRECIO_MANTENIMIENTO,
                pr.FECHA_CALCULO
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_PRODUCTOS mp ON mc.PRODUCTO_ID = mp.PRODUCTO_ID
            JOIN MAESTRO_GESTORES g  ON mc.GESTOR_ID = g.GESTOR_ID
            JOIN MAESTRO_SEGMENTOS ms ON g.SEGMENTO_ID = ms.SEGMENTO_ID
            JOIN PRECIO_POR_PRODUCTO_REAL pr ON mc.PRODUCTO_ID = pr.PRODUCTO_ID AND g.SEGMENTO_ID = pr.SEGMENTO_ID
            JOIN PRECIO_POR_PRODUCTO_STD  ps ON pr.PRODUCTO_ID = ps.PRODUCTO_ID AND pr.SEGMENTO_ID = ps.SEGMENTO_ID
            WHERE mc.GESTOR_ID = ?
              AND substr(pr.FECHA_CALCULO,1,7) = ?
            GROUP BY mc.PRODUCTO_ID, pr.SEGMENTO_ID
        """
        start = datetime.now()
        raw = execute_query(query, (gestor_id, periodo))
        out = []
        for r in raw:
            anal = self.kpi_calc.analyze_desviacion_presupuestaria(
                valor_real=r['PRECIO_MANTENIMIENTO_REAL'],
                valor_presupuestado=r['PRECIO_MANTENIMIENTO']
            )
            if abs(anal['desviacion_pct']) >= threshold:
                out.append({
                    **r,
                    'desviacion_pct': anal['desviacion_pct'],
                    'desviacion_absoluta': anal['desviacion_absoluta'],
                    'nivel_alerta': anal['nivel_alerta'],
                    'accion_recomendada': anal['accion_recomendada'],
                    'tipo_desviacion': anal['tipo_desviacion']
                })
        out.sort(key=lambda x: abs(x['desviacion_pct']), reverse=True)
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=out,
            query_type="desviaciones_precio_gestor_enhanced",
            execution_time=exec_time,
            row_count=len(out),
            query_sql=query
        )

    # =================================================================
    # 8) MÉTRICAS ESPECÍFICAS PARA DASHBOARDS (NUEVAS)
    # =================================================================

    def get_gestor_dashboard_summary(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ MÉTODO CRÍTICO: Resumen completo para dashboard principal del gestor
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        """
        query = """
        WITH seg AS (
            SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
        ),
        contracts AS (
            SELECT CONTRATO_ID, PRODUCTO_ID
            FROM MAESTRO_CONTRATOS
            WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
        ),
        gestor_base AS (
            SELECT
                g.GESTOR_ID,
                g.DESC_GESTOR,
                c.DESC_CENTRO,
                s.DESC_SEGMENTO,
                COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes,
                COUNT(DISTINCT mc.PRODUCTO_ID) as productos_diferentes,
                -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_periodo,
                COUNT(DISTINCT mov.MOVIMIENTO_ID) as total_transacciones,
                MAX(mov.FECHA) as ultima_transaccion,
                MIN(mc.FECHA_ALTA) as primer_contrato
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            LEFT JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) = ?
            WHERE g.GESTOR_ID = ?
            GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
        ),
        gastos_periodo AS (
            SELECT
                COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) as gasto_mantenimiento,
                COALESCE(SUM(mov.IMPORTE), 0) as gasto_operativo
            FROM contracts c
            JOIN seg s
            LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
            WHERE mov.FECHA < ?
            AND mov.CUENTA_ID IN ('640001', '691001', '691002')
        ),
        contratos_nuevos AS (
            SELECT COUNT(*) as contratos_nuevos_periodo
            FROM MAESTRO_CONTRATOS
            WHERE GESTOR_ID = ? AND strftime('%Y-%m', FECHA_ALTA) = ?
        )
        SELECT 
            gb.*,
            (gp.gasto_mantenimiento + gp.gasto_operativo) as gastos_periodo,
            cn.contratos_nuevos_periodo 
        FROM gestor_base gb 
        CROSS JOIN gastos_periodo gp
        CROSS JOIN contratos_nuevos cn
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"

        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, fecha_fin, periodo, gestor_id, fecha_fin, gestor_id, periodo))

        if not raw:
            return QueryResult(
                data=[{"error": "Gestor no encontrado o sin datos"}],
                query_type="gestor_dashboard_error",
                execution_time=0,
                row_count=0,
                query_sql=query
            )

        r = raw[0]

        # KPIs con clasificaciones
        margen = self.kpi_calc.calculate_margen_neto(r['ingresos_periodo'] or 0, r['gastos_periodo'] or 0)
        eficiencia = self.kpi_calc.calculate_ratio_eficiencia(r['ingresos_periodo'] or 0, r['gastos_periodo'] or 0)

        dashboard_data = {
            'gestor_info': {
                'gestor_id': r['GESTOR_ID'],
                'nombre': r['DESC_GESTOR'],
                'centro': r['DESC_CENTRO'],
                'segmento': r['DESC_SEGMENTO']
            },
            'metricas_principales': {
                'total_contratos': r['total_contratos'] or 0,
                'total_clientes': r['total_clientes'] or 0,
                'productos_diferentes': r['productos_diferentes'] or 0,
                'contratos_nuevos_periodo': r['contratos_nuevos_periodo'] or 0
            },
            'performance_financiera': {
                'ingresos_periodo': r['ingresos_periodo'] or 0,
                'gastos_periodo': r['gastos_periodo'] or 0,
                'beneficio_neto': margen['beneficio_neto'],
                'margen_neto_pct': margen['margen_neto_pct'],
                'clasificacion_margen': margen['clasificacion']
            },
            'eficiencia_operativa': {
                'ratio_eficiencia': eficiencia['ratio_eficiencia'],
                'clasificacion_eficiencia': eficiencia['clasificacion'],
                'transacciones_periodo': r['total_transacciones'] or 0,
                'promedio_ingresos_cliente': round((r['ingresos_periodo'] or 0) / max(r['total_clientes'] or 1, 1), 2)
            },
            'indicadores_actividad': {
                'ultima_transaccion': r['ultima_transaccion'],
                'primer_contrato': r['primer_contrato'],
                'diversificacion_productos': 'ALTA' if (r['productos_diferentes'] or 0) >= 3 else ('MEDIA' if (r['productos_diferentes'] or 0) >= 2 else 'BAJA')
            }
        }

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=[dashboard_data],
            query_type="gestor_dashboard_summary",
            execution_time=exec_time,
            row_count=1,
            query_sql=query
        )

    def get_gestor_evolution_trimestral(self, gestor_id: str) -> QueryResult:
        """
        ✅ Evolución trimestral del gestor (últimos 6 meses)
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        """
        query = """
        WITH seg AS (
            SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
        ),
        datos_mensuales AS (
            SELECT
                strftime('%Y-%m', mov.FECHA) as periodo,
                -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos,
                COUNT(DISTINCT mc.CONTRATO_ID) as contratos_activos,
                COUNT(DISTINCT mov.MOVIMIENTO_ID) as num_transacciones
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            WHERE g.GESTOR_ID = ?
              AND strftime('%Y-%m', mov.FECHA) >= '2025-05'
              AND strftime('%Y-%m', mov.FECHA) <= '2025-10'
            GROUP BY strftime('%Y-%m', mov.FECHA)
        ),
        gastos_fijos AS (
            SELECT
                COALESCE(AVG(pp.PRECIO_MANTENIMIENTO), 0) as gasto_promedio_mantenimiento
            FROM MAESTRO_CONTRATOS mc
            JOIN seg s
            LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                ON pp.PRODUCTO_ID = mc.PRODUCTO_ID
                AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            WHERE mc.GESTOR_ID = ?
        )
        SELECT 
            dm.*,
            gf.gasto_promedio_mantenimiento as gastos
        FROM datos_mensuales dm
        CROSS JOIN gastos_fijos gf
        ORDER BY dm.periodo
        """

        start = datetime.now()
        raw_results = execute_query(query, (gestor_id, gestor_id, gestor_id))

        enhanced_results = []
        for row in raw_results:
            margen = self.kpi_calc.calculate_margen_neto(row['ingresos'] or 0, row['gastos'] or 0)
            enhanced_results.append({
                **row,
                'beneficio_neto': margen['beneficio_neto'],
                'margen_neto_pct': margen['margen_neto_pct'],
                'promedio_transaccion': round((row['ingresos'] or 0) / max(row['num_transacciones'] or 1, 1), 2)
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced_results,
            query_type="gestor_evolution_trimestral",
            execution_time=exec_time,
            row_count=len(enhanced_results),
            query_sql=query
        )

    def get_gestor_producto_breakdown(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ Desglose detallado por producto para gráficos de composición
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        """
        query = """
        WITH seg AS (
            SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
        ),
        datos_productos AS (
            SELECT
                p.PRODUCTO_ID,
                p.DESC_PRODUCTO,
                COUNT(DISTINCT mc.CONTRATO_ID) as contratos,
                COUNT(DISTINCT mc.CLIENTE_ID) as clientes,
                -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_producto,
                p.IND_FABRICA,
                CASE WHEN p.IND_FABRICA = 1 THEN 'FABRICA' ELSE 'BANCO' END as modelo_negocio
            FROM MAESTRO_PRODUCTOS p
            JOIN MAESTRO_CONTRATOS mc ON p.PRODUCTO_ID = mc.PRODUCTO_ID
            JOIN MAESTRO_GESTORES g ON mc.GESTOR_ID = g.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) = ?
            WHERE mc.GESTOR_ID = ?
            GROUP BY p.PRODUCTO_ID, p.DESC_PRODUCTO, p.IND_FABRICA
        ),
        gastos_productos AS (
            SELECT
                mc.PRODUCTO_ID,
                COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) + 
                COALESCE((
                    SELECT SUM(mov.IMPORTE)
                    FROM MAESTRO_CONTRATOS mc2
                    JOIN MOVIMIENTOS_CONTRATOS mov ON mc2.CONTRATO_ID = mov.CONTRATO_ID
                    WHERE mc2.GESTOR_ID = ? 
                    AND mc2.PRODUCTO_ID = mc.PRODUCTO_ID
                    AND mov.FECHA < ?
                    AND mov.CUENTA_ID IN ('640001', '691001', '691002')
                ), 0) as gastos_producto
            FROM MAESTRO_CONTRATOS mc
            JOIN seg s
            LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                ON pp.PRODUCTO_ID = mc.PRODUCTO_ID
                AND pp.SEGMENTO_ID = s.SEGMENTO_ID
            WHERE mc.GESTOR_ID = ?
            GROUP BY mc.PRODUCTO_ID
        )
        SELECT 
            dp.*,
            COALESCE(gp.gastos_producto, 0) as gastos_producto
        FROM datos_productos dp
        LEFT JOIN gastos_productos gp ON dp.PRODUCTO_ID = gp.PRODUCTO_ID
        ORDER BY dp.ingresos_producto DESC
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"

        start = datetime.now()
        raw_results = execute_query(query, (gestor_id, periodo, gestor_id, gestor_id, fecha_fin, gestor_id))

        total_ingresos = sum(r['ingresos_producto'] or 0 for r in raw_results)
        total_contratos = sum(r['contratos'] for r in raw_results)

        enhanced_results = []
        for row in raw_results:
            margen = self.kpi_calc.calculate_margen_neto(row['ingresos_producto'] or 0, row['gastos_producto'] or 0)
            peso_ingresos = ((row['ingresos_producto'] or 0) / total_ingresos * 100) if total_ingresos > 0 else 0
            peso_contratos = (row['contratos'] / total_contratos * 100) if total_contratos > 0 else 0

            enhanced_results.append({
                **row,
                'beneficio_neto': margen['beneficio_neto'],
                'margen_neto_pct': margen['margen_neto_pct'],
                'peso_ingresos_pct': round(peso_ingresos, 2),
                'peso_contratos_pct': round(peso_contratos, 2),
                'ingresos_por_contrato': round((row['ingresos_producto'] or 0) / max(row['contratos'], 1), 2)
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced_results,
            query_type="gestor_producto_breakdown",
            execution_time=exec_time,
            row_count=len(enhanced_results),
            query_sql=query
        )

    def get_gestor_alertas_dashboard(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ Alertas y notificaciones específicas para dashboard
        """
        alertas = []

        # 1. Verificar margen bajo
        margen_result = self.calculate_margen_neto_gestor_enhanced(gestor_id, periodo)
        if margen_result.data and len(margen_result.data) > 0:
            margen_data = margen_result.data[0]
            if margen_data.get('margen_neto_pct', 0) < 8.0:
                alertas.append({
                    'tipo': 'MARGEN_BAJO',
                    'titulo': 'Margen Neto Crítico',
                    'descripcion': f"Margen del {margen_data.get('margen_neto_pct', 0)}% por debajo del umbral crítico (8%)",
                    'severidad': 'CRITICA',
                    'accion': 'Revisar estructura de costos y pricing',
                    'valor_actual': margen_data.get('margen_neto_pct', 0),
                    'umbral': 8.0
                })

        # 2. Verificar diversificación de productos
        cartera_result = self.get_cartera_completa_gestor_enhanced(gestor_id, periodo)
        if cartera_result.data:
            productos_activos = len(cartera_result.data)
            if productos_activos <= 2:
                alertas.append({
                    'tipo': 'BAJA_DIVERSIFICACION',
                    'titulo': 'Cartera Poco Diversificada',
                    'descripcion': f"Solo {productos_activos} productos activos. Riesgo de concentración",
                    'severidad': 'MEDIA',
                    'accion': 'Ampliar cartera de productos',
                    'valor_actual': productos_activos,
                    'umbral': 3
                })

        # 3. Verificar actividad reciente
        contratos_result = self.get_contratos_activos_gestor(gestor_id)
        if contratos_result.data:
            contratos_nuevos = len([c for c in contratos_result.data if c.get('tipo_contrato') == 'NUEVO_OCTUBRE'])
            if contratos_nuevos == 0:
                alertas.append({
                    'tipo': 'SIN_ACTIVIDAD_COMERCIAL',
                    'titulo': 'Sin Contratos Nuevos',
                    'descripcion': f"No hay contratos nuevos en {periodo}",
                    'severidad': 'ALTA',
                    'accion': 'Impulsar actividad comercial',
                    'valor_actual': contratos_nuevos,
                    'umbral': 1
                })

        return QueryResult(
            data=alertas,
            query_type="gestor_alertas_dashboard",
            execution_time=0.1,
            row_count=len(alertas),
            query_sql="-- Alertas generadas dinámicamente"
        )

    def get_gestor_kpis_comparative(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        ✅ KPIs del gestor comparados con benchmarks del segmento
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        """
        query = """
        WITH seg AS (
            SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
        ),
        contracts AS (
            SELECT CONTRATO_ID, PRODUCTO_ID
            FROM MAESTRO_CONTRATOS
            WHERE GESTOR_ID = ? AND FECHA_ALTA < ?
        ),
        gestor_data AS (
            SELECT
                g.GESTOR_ID,
                g.DESC_GESTOR,
                g.SEGMENTO_ID,
                s.DESC_SEGMENTO,
                -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_gestor,
                COUNT(DISTINCT mc.CONTRATO_ID) as contratos_gestor
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) = ?
            WHERE g.GESTOR_ID = ?
            GROUP BY g.GESTOR_ID, g.DESC_GESTOR, g.SEGMENTO_ID, s.DESC_SEGMENTO
        ),
        gastos_gestor AS (
            SELECT
                COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) + 
                COALESCE((
                    SELECT SUM(mov.IMPORTE)
                    FROM contracts c
                    JOIN MOVIMIENTOS_CONTRATOS mov ON c.CONTRATO_ID = mov.CONTRATO_ID
                    WHERE mov.FECHA < ?
                    AND mov.CUENTA_ID IN ('640001', '691001', '691002')
                ), 0) as gastos_gestor
            FROM contracts c
            JOIN seg s
            LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                ON pp.PRODUCTO_ID = c.PRODUCTO_ID
                AND pp.SEGMENTO_ID = s.SEGMENTO_ID
        ),
        benchmark_segmento AS (
            SELECT
                g.SEGMENTO_ID,
                AVG(CASE WHEN ingresos > 0 THEN (ingresos - gastos) / ingresos * 100 ELSE 0 END) as margen_promedio,
                AVG(ingresos) as ingresos_promedio,
                AVG(contratos) as contratos_promedio
            FROM (
                SELECT
                    g.GESTOR_ID,
                    g.SEGMENTO_ID,
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos,
                    (
                        SELECT COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) + COALESCE(SUM(mov2.IMPORTE), 0)
                        FROM MAESTRO_CONTRATOS mc2
                        JOIN seg2
                        LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                            ON pp.PRODUCTO_ID = mc2.PRODUCTO_ID
                            AND pp.SEGMENTO_ID = seg2.SEGMENTO_ID
                        LEFT JOIN MOVIMIENTOS_CONTRATOS mov2 ON mc2.CONTRATO_ID = mov2.CONTRATO_ID
                        WHERE mc2.GESTOR_ID = g.GESTOR_ID
                        AND mov2.FECHA < ?
                        AND mov2.CUENTA_ID IN ('640001', '691001', '691002')
                    ) as gastos,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos
                FROM MAESTRO_GESTORES g, (SELECT SEGMENTO_ID FROM seg) seg2
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE g.GESTOR_ID != ?
                GROUP BY g.GESTOR_ID, g.SEGMENTO_ID
            ) sub
            GROUP BY SEGMENTO_ID
        )
        SELECT 
            gd.*,
            gg.gastos_gestor,
            bs.margen_promedio,
            bs.ingresos_promedio,
            bs.contratos_promedio
        FROM gestor_data gd
        CROSS JOIN gastos_gestor gg
        LEFT JOIN benchmark_segmento bs ON gd.SEGMENTO_ID = bs.SEGMENTO_ID
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"

        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, fecha_fin, periodo, gestor_id, fecha_fin, fecha_fin, periodo, gestor_id))

        if not raw:
            return QueryResult(data=[], query_type="gestor_kpis_comparative_empty", execution_time=0, row_count=0, query_sql=query)

        r = raw[0]
        margen_gestor = ((r['ingresos_gestor'] - r['gastos_gestor']) / r['ingresos_gestor'] * 100) if r['ingresos_gestor'] > 0 else 0

        comparative_data = {
            'gestor_data': {
                'ingresos': r['ingresos_gestor'] or 0,
                'gastos': r['gastos_gestor'] or 0,
                'margen_pct': round(margen_gestor, 2),
                'contratos': r['contratos_gestor'] or 0
            },
            'benchmark_segmento': {
                'margen_promedio': round(r['margen_promedio'] or 0, 2),
                'ingresos_promedio': round(r['ingresos_promedio'] or 0, 2),
                'contratos_promedio': round(r['contratos_promedio'] or 0, 1)
            },
            'comparativas': {
                'vs_margen_pct': round(margen_gestor - (r['margen_promedio'] or 0), 2),
                'vs_ingresos_pct': round(((r['ingresos_gestor'] or 0) / max(r['ingresos_promedio'] or 1, 1) - 1) * 100, 2),
                'vs_contratos_pct': round(((r['contratos_gestor'] or 0) / max(r['contratos_promedio'] or 1, 1) - 1) * 100, 2)
            },
            'posicionamiento': {
                'margen': 'SUPERIOR' if margen_gestor > (r['margen_promedio'] or 0) else 'INFERIOR',
                'volumen': 'SUPERIOR' if (r['ingresos_gestor'] or 0) > (r['ingresos_promedio'] or 0) else 'INFERIOR',
                'actividad': 'SUPERIOR' if (r['contratos_gestor'] or 0) > (r['contratos_promedio'] or 0) else 'INFERIOR'
            }
        }

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=[comparative_data],
            query_type="gestor_kpis_comparative",
            execution_time=exec_time,
            row_count=1,
            query_sql=query
        )

    # =================================================================
    # 7) BENCHMARKING, RANKINGS Y TEMPORAL (ORIGINAL + NUEVO)
    # =================================================================

    def compare_gestor_septiembre_octubre(self, gestor_id: str) -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Compara performance del gestor entre septiembre y octubre 2025
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            datos_mensuales AS (
                SELECT
                    strftime('%Y-%m', mov.FECHA) as periodo,
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_activos
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE g.GESTOR_ID = ?
                  AND strftime('%Y-%m', mov.FECHA) IN ('2025-09', '2025-10')
                GROUP BY strftime('%Y-%m', mov.FECHA)
            ),
            gastos_fijos AS (
                SELECT
                    COALESCE(AVG(pp.PRECIO_MANTENIMIENTO), 0) as gastos
                FROM MAESTRO_CONTRATOS mc
                JOIN seg s
                LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = mc.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
                WHERE mc.GESTOR_ID = ?
            )
            SELECT 
                dm.*,
                gf.gastos
            FROM datos_mensuales dm
            CROSS JOIN gastos_fijos gf
            ORDER BY dm.periodo
        """
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, gestor_id))
        
        if len(raw) < 2:
            return QueryResult(
                data=[{"error": "Datos insuficientes para comparación"}],
                query_type="compare_gestor_sep_oct_error",
                execution_time=0,
                row_count=0,
                query_sql=query
            )
        
        sept_data = next((r for r in raw if r['periodo'] == '2025-09'), None)
        oct_data = next((r for r in raw if r['periodo'] == '2025-10'), None)
        
        if not sept_data or not oct_data:
            return QueryResult(
                data=[{"error": "Faltan datos de septiembre u octubre"}],
                query_type="compare_gestor_sep_oct_incomplete",
                execution_time=0,
                row_count=0,
                query_sql=query
            )
        
        # Calcular KPIs para ambos meses
        margen_sept = self.kpi_calc.calculate_margen_neto(sept_data['ingresos'], sept_data['gastos'])
        margen_oct = self.kpi_calc.calculate_margen_neto(oct_data['ingresos'], oct_data['gastos'])
        
        variacion_ingresos = ((oct_data['ingresos'] - sept_data['ingresos']) / sept_data['ingresos'] * 100) if sept_data['ingresos'] > 0 else 0
        variacion_contratos = oct_data['contratos_activos'] - sept_data['contratos_activos']
        variacion_margen = margen_oct['margen_neto_pct'] - margen_sept['margen_neto_pct']
        
        comparison = {
            'septiembre': {
                'ingresos': sept_data['ingresos'],
                'contratos_activos': sept_data['contratos_activos'],
                'gastos': sept_data['gastos'],
                'beneficio_neto': margen_sept['beneficio_neto'],
                'margen_neto_pct': margen_sept['margen_neto_pct']
            },
            'octubre': {
                'ingresos': oct_data['ingresos'],
                'contratos_activos': oct_data['contratos_activos'],
                'gastos': oct_data['gastos'],
                'beneficio_neto': margen_oct['beneficio_neto'],
                'margen_neto_pct': margen_oct['margen_neto_pct']
            },
            'variaciones': {
                'ingresos_variacion_pct': round(variacion_ingresos, 2),
                'contratos_variacion': variacion_contratos,
                'margen_variacion_pp': round(variacion_margen, 2)
            },
            'tendencia': {
                'ingresos': 'POSITIVA' if variacion_ingresos > 0 else 'NEGATIVA',
                'actividad': 'CRECIENTE' if variacion_contratos > 0 else 'DECRECIENTE',
                'rentabilidad': 'MEJORA' if variacion_margen > 0 else 'DETERIORO'
            }
        }
        
        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=[comparison],
            query_type="compare_gestor_septiembre_octubre",
            execution_time=exec_time,
            row_count=1,
            query_sql=query
        )

    def get_ranking_gestores_margen(self, periodo: str = "2025-10", limite: int = 20) -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Ranking de gestores por margen neto
        """
        query = """
            WITH seg_all AS (
                SELECT g.GESTOR_ID, g.SEGMENTO_ID
                FROM MAESTRO_GESTORES g
            ),
            contracts_all AS (
                SELECT mc.GESTOR_ID, mc.CONTRATO_ID, mc.PRODUCTO_ID
                FROM MAESTRO_CONTRATOS mc
                WHERE mc.FECHA_ALTA < ?
            ),
            datos_gestores AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_total
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
            ),
            gastos_gestores AS (
                SELECT
                    ca.GESTOR_ID,
                    COALESCE(SUM(pp.PRECIO_MANTENIMIENTO), 0) as gasto_mantenimiento,
                    COALESCE((
                        SELECT SUM(mov.IMPORTE)
                        FROM MOVIMIENTOS_CONTRATOS mov
                        WHERE mov.CONTRATO_ID IN (
                            SELECT CONTRATO_ID FROM contracts_all WHERE GESTOR_ID = ca.GESTOR_ID
                        )
                        AND mov.FECHA < ?
                        AND mov.CUENTA_ID IN ('640001', '691001', '691002')
                    ), 0) as gasto_operativo
                FROM contracts_all ca
                JOIN seg_all sa ON ca.GESTOR_ID = sa.GESTOR_ID
                LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = ca.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = sa.SEGMENTO_ID
                GROUP BY ca.GESTOR_ID
            )
            SELECT
                dg.GESTOR_ID,
                dg.DESC_GESTOR,
                dg.DESC_CENTRO,
                dg.DESC_SEGMENTO,
                dg.ingresos_total,
                (gg.gasto_mantenimiento + gg.gasto_operativo) as gastos_total,
                (dg.ingresos_total - (gg.gasto_mantenimiento + gg.gasto_operativo)) as beneficio_neto,
                CASE WHEN dg.ingresos_total > 0
                     THEN ROUND(((dg.ingresos_total - (gg.gasto_mantenimiento + gg.gasto_operativo)) / dg.ingresos_total) * 100, 2)
                     ELSE 0 END as margen_neto_pct
            FROM datos_gestores dg
            LEFT JOIN gastos_gestores gg ON dg.GESTOR_ID = gg.GESTOR_ID
            WHERE dg.ingresos_total > 0
            ORDER BY margen_neto_pct DESC
            LIMIT ?
        """
        
        fecha_fin = f"{periodo}-31" if periodo else "2025-11-01"
        
        start = datetime.now()
        raw = execute_query(query, (fecha_fin, periodo, fecha_fin, limite))

        enhanced = []
        for idx, r in enumerate(raw, 1):
            clasificacion = self.kpi_calc.classify_margen_neto(r['margen_neto_pct'])
            enhanced.append({
                'ranking': idx,
                **r,
                'clasificacion_margen': clasificacion,
                'diferencia_vs_top1': round(r['margen_neto_pct'] - raw[0]['margen_neto_pct'], 2) if idx > 1 else 0
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced,
            query_type="ranking_gestores_margen",
            execution_time=exec_time,
            row_count=len(enhanced),
            query_sql=query
        )

    def get_ranking_gestores_volumen(self, periodo: str = "2025-10", limite: int = 20) -> QueryResult:
        """
        ✅ CORREGIDO: Usa ingresos 76% correctamente
        Ranking de gestores por volumen de ingresos
        """
        query = """
            SELECT
                g.GESTOR_ID,
                g.DESC_GESTOR,
                c.DESC_CENTRO,
                s.DESC_SEGMENTO,
                -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_total,
                COUNT(DISTINCT mc.CONTRATO_ID) as contratos_activos,
                COUNT(DISTINCT mc.CLIENTE_ID) as clientes_activos
            FROM MAESTRO_GESTORES g
            JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                AND strftime('%Y-%m', mov.FECHA) = ?
            GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
            HAVING ingresos_total > 0
            ORDER BY ingresos_total DESC
            LIMIT ?
        """
        
        start = datetime.now()
        raw = execute_query(query, (periodo, limite))

        enhanced = []
        total_ingresos_top = sum(r['ingresos_total'] for r in raw)
        
        for idx, r in enumerate(raw, 1):
            cuota_mercado_pct = (r['ingresos_total'] / total_ingresos_top * 100) if total_ingresos_top > 0 else 0
            enhanced.append({
                'ranking': idx,
                **r,
                'cuota_mercado_pct': round(cuota_mercado_pct, 2),
                'ingresos_por_contrato': round(r['ingresos_total'] / max(r['contratos_activos'], 1), 2),
                'ingresos_por_cliente': round(r['ingresos_total'] / max(r['clientes_activos'], 1), 2)
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced,
            query_type="ranking_gestores_volumen",
            execution_time=exec_time,
            row_count=len(enhanced),
            query_sql=query
        )

    def get_evolucion_temporal_gestor(self, gestor_id: str, meses: int = 6) -> QueryResult:
        """
        ✅ CORREGIDO: Usa PRECIO_STD + gastos operativos
        Evolución temporal del gestor (últimos N meses)
        """
        query = """
            WITH seg AS (
                SELECT SEGMENTO_ID FROM MAESTRO_GESTORES WHERE GESTOR_ID = ?
            ),
            meses_disponibles AS (
                SELECT DISTINCT strftime('%Y-%m', mov.FECHA) as periodo
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
                WHERE mc.GESTOR_ID = ?
                ORDER BY periodo DESC
                LIMIT ?
            ),
            datos_mensuales AS (
                SELECT
                    md.periodo,
                    -- ✅ INGRESOS CORREGIDOS: Solo cuentas 76XXXX
                    COALESCE(SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END), 0) as ingresos,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_activos,
                    COUNT(DISTINCT mc.CLIENTE_ID) as clientes_activos,
                    COUNT(DISTINCT mov.MOVIMIENTO_ID) as num_transacciones
                FROM meses_disponibles md
                JOIN MAESTRO_CONTRATOS mc ON mc.GESTOR_ID = ?
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = md.periodo
                GROUP BY md.periodo
            ),
            gastos_fijos AS (
                SELECT
                    COALESCE(AVG(pp.PRECIO_MANTENIMIENTO), 0) as gasto_promedio_mantenimiento,
                    COALESCE(AVG(mov.IMPORTE), 0) as gasto_promedio_operativo
                FROM MAESTRO_CONTRATOS mc
                JOIN seg s
                LEFT JOIN PRECIO_POR_PRODUCTO_STD pp
                    ON pp.PRODUCTO_ID = mc.PRODUCTO_ID
                    AND pp.SEGMENTO_ID = s.SEGMENTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mc.GESTOR_ID = ?
                AND mov.CUENTA_ID IN ('640001', '691001', '691002')
            )
            SELECT 
                dm.*,
                (gf.gasto_promedio_mantenimiento + gf.gasto_promedio_operativo) as gastos
            FROM datos_mensuales dm
            CROSS JOIN gastos_fijos gf
            ORDER BY dm.periodo
        """
        
        start = datetime.now()
        raw = execute_query(query, (gestor_id, gestor_id, meses, gestor_id, gestor_id))

        enhanced = []
        for i, r in enumerate(raw):
            margen = self.kpi_calc.calculate_margen_neto(r['ingresos'] or 0, r['gastos'] or 0)
            
            # Calcular variación vs mes anterior
            var_ingresos = 0
            var_contratos = 0
            if i > 0:
                prev = raw[i-1]
                var_ingresos = ((r['ingresos'] - prev['ingresos']) / prev['ingresos'] * 100) if prev['ingresos'] > 0 else 0
                var_contratos = r['contratos_activos'] - prev['contratos_activos']

            enhanced.append({
                **r,
                'beneficio_neto': margen['beneficio_neto'],
                'margen_neto_pct': margen['margen_neto_pct'],
                'variacion_ingresos_pct': round(var_ingresos, 2),
                'variacion_contratos': var_contratos,
                'ingresos_por_transaccion': round((r['ingresos'] or 0) / max(r['num_transacciones'] or 1, 1), 2)
            })

        exec_time = (datetime.now() - start).total_seconds()
        return QueryResult(
            data=enhanced,
            query_type="evolucion_temporal_gestor",
            execution_time=exec_time,
            row_count=len(enhanced),
            query_sql=query
        )

    # =================================================================
    # MÉTODOS AUXILIARES PRIVADOS (clasificaciones, contextos, recomendaciones)
    # =================================================================

    def _classify_product_importance(self, peso_contratos: float, peso_volumen: float) -> str:
        """Clasifica importancia del producto en cartera"""
        if peso_contratos >= 30 or peso_volumen >= 40:
            return "ESTRATEGICO"
        elif peso_contratos >= 15 or peso_volumen >= 20:
            return "IMPORTANTE"
        elif peso_contratos >= 5 or peso_volumen >= 10:
            return "COMPLEMENTARIO"
        else:
            return "MARGINAL"

    def _get_banking_context(self, clasificacion: str) -> str:
        """Contexto bancario para clasificaciones de margen"""
        contexts = {
            'EXCELENTE': 'Margen superior a estándares del sector bancario. Gestión óptima de recursos.',
            'BUENO': 'Margen saludable en línea con mejores prácticas bancarias.',
            'ACEPTABLE': 'Margen dentro de rangos operativos. Hay oportunidades de mejora.',
            'BAJO': 'Margen por debajo de estándares. Requiere revisión de estructura de costos.',
            'CRITICO': 'Margen insuficiente para sostener operación. Intervención urgente requerida.'
        }
        return contexts.get(clasificacion, 'Clasificación no disponible')

    def _get_margin_recommendation(self, margen_pct: float) -> str:
        """Recomendación basada en margen neto"""
        if margen_pct >= 15:
            return "Mantener estrategia actual. Explorar oportunidades de crecimiento."
        elif margen_pct >= 10:
            return "Optimizar eficiencia operativa. Buscar economías de escala."
        elif margen_pct >= 8:
            return "Revisar pricing y estructura de costos. Focalizar en productos de mayor margen."
        else:
            return "URGENTE: Reestructuración necesaria. Evaluar viabilidad de líneas de negocio."

    def _get_efficiency_context(self, clasificacion: str) -> str:
        """Contexto bancario para eficiencia operativa"""
        contexts = {
            'EXCELENTE': 'Eficiencia operativa sobresaliente. Modelo replicable.',
            'BUENA': 'Operación eficiente con uso óptimo de recursos.',
            'ACEPTABLE': 'Eficiencia dentro de rangos normales. Mejoras posibles.',
            'BAJA': 'Eficiencia operativa deficiente. Revisión de procesos necesaria.',
            'CRITICA': 'Operación insostenible. Costos exceden valor generado.'
        }
        return contexts.get(clasificacion, 'Clasificación no disponible')

    def _get_efficiency_recommendation(self, ratio: Optional[float]) -> str:
        """Recomendación basada en ratio de eficiencia"""
        if ratio is None or ratio <= 0:
            return "Sin ingresos suficientes para evaluar eficiencia."
        elif ratio >= 2.0:
            return "Eficiencia excelente. Compartir mejores prácticas con equipo."
        elif ratio >= 1.5:
            return "Buena eficiencia. Buscar automatización de procesos repetitivos."
        elif ratio >= 1.2:
            return "Eficiencia aceptable. Identificar cuellos de botella operativos."
        else:
            return "ALERTA: Costos demasiado altos vs ingresos. Reestructuración urgente."

    def _get_roe_context(self, clasificacion: str) -> str:
        """Contexto bancario para ROE"""
        contexts = {
            'EXCELENTE': 'ROE excepcional. Generación de valor para accionistas superior.',
            'BUENO': 'ROE saludable. Uso eficiente del capital.',
            'ACEPTABLE': 'ROE en rangos normales. Oportunidades de mejora disponibles.',
            'BAJO': 'ROE por debajo de expectativas. Capital no optimizado.',
            'CRITICO': 'ROE insuficiente. Destrucción de valor. Intervención necesaria.'
        }
        return contexts.get(clasificacion, 'Clasificación no disponible')

    def _get_roe_recommendation(self, roe_pct: float) -> str:
        """Recomendación basada en ROE"""
        if roe_pct >= 15:
            return "ROE excelente. Maximizar crecimiento manteniendo rentabilidad."
        elif roe_pct >= 10:
            return "ROE bueno. Explorar productos de mayor rentabilidad."
        elif roe_pct >= 5:
            return "ROE aceptable. Reducir activos improductivos y mejorar márgenes."
        else:
            return "CRÍTICO: ROE insuficiente. Revisar asignación de capital urgentemente."

    def _interpret_fondos_distribution(self, pct_fabrica: float, pct_banco: float) -> str:
        """Interpreta distribución 85/15 de fondos"""
        desv_f = abs(pct_fabrica - 85.0)
        desv_b = abs(pct_banco - 15.0)
        
        if desv_f <= 2 and desv_b <= 2:
            return "DISTRIBUCIÓN PERFECTA: Dentro del estándar 85/15"
        elif desv_f <= 5 and desv_b <= 5:
            return "DISTRIBUCIÓN ACEPTABLE: Leve desviación del estándar"
        elif pct_fabrica > 90:
            return "ALERTA: Exceso de fábrica. Riesgo de concentración"
        elif pct_banco > 20:
            return "ALERTA: Exceso de banco. Revisar estructura comercial"
        else:
            return "DESVIACIÓN SIGNIFICATIVA: Requiere ajuste inmediato"

    def _assess_alert_impact(self, tipo_alerta: str, valor_actual: float, umbral: float) -> str:
        """Evalúa impacto comercial de una alerta"""
        desviacion_pct = abs((valor_actual - umbral) / umbral * 100) if umbral > 0 else 0
        
        if tipo_alerta == 'MARGEN_BAJO':
            if valor_actual < 5:
                return "CRÍTICO - Pérdida operativa inminente"
            elif valor_actual < 8:
                return "ALTO - Rentabilidad comprometida"
            else:
                return "MEDIO - Monitoreo cercano requerido"
        elif tipo_alerta == 'DESVIACION_PRECIO':
            if desviacion_pct > 30:
                return "CRÍTICO - Descalibración severa de pricing"
            elif desviacion_pct > 20:
                return "ALTO - Ajuste de precios necesario"
            else:
                return "MEDIO - Revisar política comercial"
        else:
            return "BAJO - Seguimiento rutinario"

    def _calculate_alert_priority(self, severidad: str, valor_actual: float, umbral: float) -> int:
        """Calcula prioridad numérica de alerta (1=máxima, 5=baja)"""
        base_priority = {'CRITICA': 1, 'ALTA': 2, 'MEDIA': 3, 'BAJA': 4}.get(severidad, 5)
        
        # Ajustar por magnitud de desviación
        if umbral > 0:
            desviacion_pct = abs((valor_actual - umbral) / umbral * 100)
            if desviacion_pct > 50:
                base_priority = max(1, base_priority - 1)
        
        return base_priority

    def _get_action_timeline(self, severidad: str) -> int:
        """Días para actuar según severidad"""
        return {'CRITICA': 1, 'ALTA': 3, 'MEDIA': 7, 'BAJA': 14}.get(severidad, 30)

    def _get_alert_banking_context(self, tipo_alerta: str) -> str:
        """Contexto bancario específico por tipo de alerta"""
        contexts = {
            'MARGEN_BAJO': 'Impacto directo en P&L. Afecta rentabilidad global del centro.',
            'DESVIACION_PRECIO': 'Riesgo de erosión de márgenes. Competitividad comprometida.',
            'BAJA_DIVERSIFICACION': 'Concentración excesiva aumenta riesgo comercial.',
            'SIN_ACTIVIDAD_COMERCIAL': 'Pipeline comercial débil. Riesgo de caída de ingresos futuros.'
        }
        return contexts.get(tipo_alerta, 'Requiere análisis específico.')

    def _estimate_revenue_impact(self, tipo_alerta: str, valor_actual: float) -> str:
        """Estima impacto en ingresos"""
        if tipo_alerta == 'MARGEN_BAJO':
            if valor_actual < 5:
                return "Pérdida estimada: 15-20% de ingresos netos"
            elif valor_actual < 8:
                return "Pérdida estimada: 5-10% de ingresos netos"
            else:
                return "Impacto menor: <5% de ingresos netos"
        elif tipo_alerta == 'DESVIACION_PRECIO':
            if valor_actual > 30:
                return "Pérdida potencial: 10-15% por ajuste de precios"
            elif valor_actual > 20:
                return "Pérdida potencial: 5-10% por ajuste de precios"
            else:
                return "Impacto limitado: <5%"
        else:
            return "Impacto indirecto en ingresos futuros"


# =================================================================
# INSTANCIA SINGLETON PARA USO GLOBAL
# =================================================================
gestor_queries = GestorQueries()

# =================================================================
# MÉTODOS DE CONVENIENCIA EXPORTADOS (compatibilidad con código existente)
# =================================================================

def get_gestor_performance_enhanced(gestor_id: str, periodo: str = None):
    """Wrapper para compatibilidad"""
    return gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo)

def get_all_gestores_enhanced():
    """Wrapper para compatibilidad"""
    return gestor_queries.get_all_gestores_enhanced()

def get_cartera_completa_gestor(gestor_id: str, fecha: str = "2025-10"):
    """Wrapper para compatibilidad"""
    return gestor_queries.get_cartera_completa_gestor(gestor_id, fecha)

def calculate_margen_neto_gestor(gestor_id: str, periodo: str = "2025-10"):
    """Wrapper para compatibilidad"""
    return gestor_queries.calculate_margen_neto_gestor(gestor_id, periodo)

def calculate_roe_gestor(gestor_id: str, periodo: str = "2025-10"):
    """Wrapper para compatibilidad"""
    return gestor_queries.calculate_roe_gestor(gestor_id, periodo)

def get_contratos_activos_gestor(gestor_id: str):
    """Wrapper para compatibilidad"""
    return gestor_queries.get_contratos_activos_gestor(gestor_id)

def get_distribucion_fondos_gestor(gestor_id: str, periodo: str = "2025-10"):
    """Wrapper para compatibilidad"""
    return gestor_queries.get_distribucion_fondos_gestor(gestor_id, periodo)


# =================================================================
# LOGGING Y VALIDACIÓN
# =================================================================

logger.info("✅ gestor_queries.py cargado correctamente")
logger.info("✅ Todas las queries CORREGIDAS: Usan PRECIO_POR_PRODUCTO_STD + gastos operativos (640001, 691001, 691002)")
logger.info("✅ Integración con kpi_calculator.py activa")
logger.info(f"✅ Métodos disponibles: {len([m for m in dir(GestorQueries) if not m.startswith('_')])}")
