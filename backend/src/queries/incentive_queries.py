"""
incentive_queries.py

Consultas específicas para detección de incentivos y evaluación de performance de gestores en Banca March.
Incluye análisis de crecimiento comercial, expansión de productos, captación de clientes y mejora de márgenes.
INTEGRADO con kpi_calculator.py para cálculos financieros estandarizados y clasificaciones automáticas.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .gestor_queries import QueryResult
from src.database.db_connection import execute_query
from src.tools.sql_guard import is_query_safe
from src.tools.kpi_calculator import kpi_calculator, get_kpis_from_data  # ✅ NUEVA INTEGRACIÓN
from src.utils.initial_agent import iniciar_agente_llm

logger = logging.getLogger(__name__)

class IncentiveQueries:
    """
    Biblioteca completa de consultas para detección de incentivos y performance positiva
    
    COBERTURA MEJORADA:
    - High performers: Gestores con performance excepcional con análisis KPI estandarizado
    - Crecimiento de productos: Expansión en diversificación comercial con métricas automáticas
    - Captación de clientes: Incremento en base de clientes con clasificaciones inteligentes
    - Mejora de márgenes: Optimización de rentabilidad con benchmarks bancarios
    - Cumplimiento de objetivos: Evaluación vs targets con acciones recomendadas
    - Queries dinámicas: Generación automática con validación
    """
    
    def __init__(self):
        self.query_cache = {}
        self.performance_threshold = 15.0  # Umbral de crecimiento para incentivos
        self.top_performers_limit = 10     # Top N gestores por defecto
        self.kpi_calc = kpi_calculator     # ✅ INSTANCIA KPI_CALCULATOR
    
    # =================================================================
    # 1. DETECCIÓN DE HIGH PERFORMERS (MEJORADAS CON KPI)
    # =================================================================
    
    def calculate_incentivo_cumplimiento_objetivos_enhanced(self, periodo: str = "2025-10", umbral_cumplimiento: float = 100.0) -> QueryResult:
        """
        Calcula incentivos basados en cumplimiento de objetivos con análisis KPI mejorado.
        
        CASO DE USO: "¿Qué gestores han cumplido objetivos y merecen incentivos?"
        MEJORAS: Usa kpi_calculator para clasificaciones automáticas y análisis contextual
        """
        # Query simplificada para extraer datos base
        query = """
            WITH objetivos_reales AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_reales,
                    COUNT(DISTINCT mc.CLIENTE_ID) as clientes_reales,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_reales,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_reales
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
            SELECT * FROM objetivos_reales
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
        # ✅ PROCESAMIENTO AVANZADO CON KPI_CALCULATOR
        enhanced_results = []
        
        # Calcular objetivos benchmark (promedio + 10% por segmento)
        objetivos_por_segmento = {}
        for row in raw_results:
            segmento = row['DESC_SEGMENTO']
            if segmento not in objetivos_por_segmento:
                objetivos_por_segmento[segmento] = {
                    'contratos': [], 'clientes': [], 'margenes': []
                }
            
            # Calcular margen neto con kpi_calculator
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_reales'],
                gastos=row['gastos_reales']
            )
            objetivos_por_segmento[segmento]['contratos'].append(row['contratos_reales'])
            objetivos_por_segmento[segmento]['clientes'].append(row['clientes_reales'])
            objetivos_por_segmento[segmento]['margenes'].append(margen_analysis['margen_neto_pct'])
        
        # Calcular medias para objetivos
        for segmento in objetivos_por_segmento:
            datos = objetivos_por_segmento[segmento]
            objetivos_por_segmento[segmento] = {
                'objetivo_contratos': (sum(datos['contratos']) / len(datos['contratos'])) * 1.1,
                'objetivo_clientes': (sum(datos['clientes']) / len(datos['clientes'])) * 1.1,
                'objetivo_margen': (sum(datos['margenes']) / len(datos['margenes'])) * 1.05
            }
        
        # Procesar cada gestor con KPI calculator
        for row in raw_results:
            # Análisis de margen con kpi_calculator
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_reales'],
                gastos=row['gastos_reales']
            )
            
            # Obtener objetivos del segmento
            segmento = row['DESC_SEGMENTO']
            objetivos = objetivos_por_segmento.get(segmento, {
                'objetivo_contratos': 0, 'objetivo_clientes': 0, 'objetivo_margen': 0
            })
            
            # Calcular cumplimientos
            cumpl_contratos = (row['contratos_reales'] / objetivos['objetivo_contratos'] * 100) if objetivos['objetivo_contratos'] > 0 else 0
            cumpl_clientes = (row['clientes_reales'] / objetivos['objetivo_clientes'] * 100) if objetivos['objetivo_clientes'] > 0 else 0
            cumpl_margen = (margen_analysis['margen_neto_pct'] / objetivos['objetivo_margen'] * 100) if objetivos['objetivo_margen'] > 0 else 0
            
            cumplimiento_global = (cumpl_contratos + cumpl_clientes + cumpl_margen) / 3
            
            # Solo incluir si supera umbral
            if cumplimiento_global >= umbral_cumplimiento:
                enhanced_row = {
                    **row,
                    'margen_neto_real': margen_analysis['margen_neto_pct'],
                    'clasificacion_margen': margen_analysis['clasificacion'],
                    'objetivo_contratos': round(objetivos['objetivo_contratos'], 1),
                    'objetivo_clientes': round(objetivos['objetivo_clientes'], 1),
                    'objetivo_margen': round(objetivos['objetivo_margen'], 2),
                    'cumpl_contratos_pct': round(cumpl_contratos, 2),
                    'cumpl_clientes_pct': round(cumpl_clientes, 2),
                    'cumpl_margen_pct': round(cumpl_margen, 2),
                    'cumplimiento_global_pct': round(cumplimiento_global, 2),
                    
                    # ✅ CLASIFICACIÓN AUTOMÁTICA MEJORADA
                    'categoria_cumplimiento': self._classify_performance_category(cumplimiento_global),
                    'incentivo_calculado_eur': self._calculate_incentive_amount(cumplimiento_global, margen_analysis['clasificacion']),
                    
                    # Análisis completo
                    'analisis_margen_completo': margen_analysis
                }
                enhanced_results.append(enhanced_row)
        
        # Ordenar por cumplimiento global
        enhanced_results.sort(key=lambda x: x['cumplimiento_global_pct'], reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="incentivo_cumplimiento_objetivos_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def calculate_incentivo_cumplimiento_objetivos(self, periodo: str = "2025-10", umbral_cumplimiento: float = 100.0) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
        """
        query = """
            WITH objetivos_reales AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_reales,
                    COUNT(DISTINCT mc.CLIENTE_ID) as clientes_reales,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_reales,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_reales,
                    ROUND(
                        (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                  THEN mov.IMPORTE ELSE 0 END)
                        - SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                  THEN ABS(mov.IMPORTE) ELSE 0 END))
                        /
                        NULLIF(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                       THEN mov.IMPORTE ELSE 0 END), 0) * 100, 2
                    ) as margen_neto_real
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
            ),
            objetivos_benchmark AS (
                -- Objetivos basados en medias del centro/segmento
                SELECT
                    s.SEGMENTO_ID,
                    AVG(contratos_reales) * 1.1 as objetivo_contratos,     -- +10% vs media
                    AVG(clientes_reales) * 1.1 as objetivo_clientes,       -- +10% vs media
                    AVG(margen_neto_real) * 1.05 as objetivo_margen        -- +5% vs media
                FROM objetivos_reales o
                JOIN MAESTRO_SEGMENTOS s ON o.DESC_SEGMENTO = s.DESC_SEGMENTO
                GROUP BY s.SEGMENTO_ID
            ),
            cumplimiento AS (
                SELECT
                    or_.*,
                    ob.objetivo_contratos,
                    ob.objetivo_clientes,
                    ob.objetivo_margen,
                    ROUND((or_.contratos_reales / NULLIF(ob.objetivo_contratos, 0)) * 100, 2) as cumpl_contratos_pct,
                    ROUND((or_.clientes_reales / NULLIF(ob.objetivo_clientes, 0)) * 100, 2) as cumpl_clientes_pct,
                    ROUND((or_.margen_neto_real / NULLIF(ob.objetivo_margen, 0)) * 100, 2) as cumpl_margen_pct
                FROM objetivos_reales or_
                JOIN MAESTRO_SEGMENTOS s ON or_.DESC_SEGMENTO = s.DESC_SEGMENTO
                JOIN objetivos_benchmark ob ON s.SEGMENTO_ID = ob.SEGMENTO_ID
            )
            SELECT
                GESTOR_ID,
                DESC_GESTOR,
                DESC_CENTRO,
                DESC_SEGMENTO,
                contratos_reales,
                clientes_reales,
                margen_neto_real,
                ROUND(objetivo_contratos, 1) as objetivo_contratos,
                ROUND(objetivo_clientes, 1) as objetivo_clientes,
                ROUND(objetivo_margen, 2) as objetivo_margen,
                cumpl_contratos_pct,
                cumpl_clientes_pct,
                cumpl_margen_pct,
                ROUND((cumpl_contratos_pct + cumpl_clientes_pct + cumpl_margen_pct) / 3, 2) as cumplimiento_global_pct,
                CASE 
                    WHEN (cumpl_contratos_pct + cumpl_clientes_pct + cumpl_margen_pct) / 3 >= 120.0 THEN 'EXCELENTE'
                    WHEN (cumpl_contratos_pct + cumpl_clientes_pct + cumpl_margen_pct) / 3 >= 100.0 THEN 'CUMPLE'
                    WHEN (cumpl_contratos_pct + cumpl_clientes_pct + cumpl_margen_pct) / 3 >= 80.0 THEN 'PARCIAL'
                    ELSE 'INCUMPLE'
                END as categoria_cumplimiento,
                ROUND(
                    CASE 
                        WHEN (cumpl_contratos_pct + cumpl_clientes_pct + cumpl_margen_pct) / 3 >= 120.0 THEN 5000 * 1.5
                        WHEN (cumpl_contratos_pct + cumpl_clientes_pct + cumpl_margen_pct) / 3 >= 100.0 THEN 5000 * 1.25
                        WHEN (cumpl_contratos_pct + cumpl_clientes_pct + cumpl_margen_pct) / 3 >= 80.0 THEN 5000 * 0.8
                        ELSE 0
                    END, 2
                ) as incentivo_calculado_eur
            FROM cumplimiento
            WHERE cumplimiento_global_pct >= ?
            ORDER BY cumplimiento_global_pct DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, umbral_cumplimiento))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="incentivo_cumplimiento_objetivos",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def analyze_bonus_margen_neto_enhanced(self, periodo: str = "2025-10", umbral_margen: float = 15.0) -> QueryResult:
        """
        Analiza gestores elegibles para bonus por margen neto con análisis KPI mejorado.
        
        CASO DE USO: "¿Qué gestores merecen bonus por alta rentabilidad?"
        MEJORAS: Usa kpi_calculator para clasificaciones automáticas y benchmarks bancarios
        """
        # Query simplificada para extraer datos base
        query = """
            WITH margen_gestores AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_total,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_total
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
                HAVING ingresos_total > 0
            )
            SELECT * FROM margen_gestores
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
        # ✅ PROCESAMIENTO CON KPI_CALCULATOR
        enhanced_results = []
        margenes_para_ranking = []
        
        # Primera pasada: calcular todos los márgenes
        for row in raw_results:
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            if margen_analysis['margen_neto_pct'] >= umbral_margen:
                margenes_para_ranking.append({
                    'gestor_data': row,
                    'margen_analysis': margen_analysis
                })
        
        # Ordenar por margen para ranking
        margenes_para_ranking.sort(key=lambda x: x['margen_analysis']['margen_neto_pct'], reverse=True)
        
        # Segunda pasada: generar resultados con análisis mejorado
        for i, data in enumerate(margenes_para_ranking):
            row = data['gestor_data']
            margen_analysis = data['margen_analysis']
            
            # Calcular cuartil (dividir en 4 grupos)
            total_gestores = len(margenes_para_ranking)
            cuartil = min(4, (i // (total_gestores // 4 if total_gestores >= 4 else 1)) + 1)
            
            enhanced_row = {
                **row,
                'margen_neto_pct': margen_analysis['margen_neto_pct'],
                'beneficio_neto': margen_analysis['beneficio_neto'],
                'clasificacion_margen': margen_analysis['clasificacion'],  # EXCELENTE, BUENO, etc.
                'ranking_margen': i + 1,
                'cuartil_margen': cuartil,
                
                # ✅ CLASIFICACIÓN AUTOMÁTICA DE BONUS
                'categoria_bonus': self._classify_bonus_category(cuartil, margen_analysis['margen_neto_pct']),
                'bonus_margen_eur': self._calculate_bonus_amount(cuartil, margen_analysis['margen_neto_pct']),
                'bonus_volumen_eur': round(row['ingresos_total'] * 0.01, 2),
                'bonus_total_eur': round(
                    self._calculate_bonus_amount(cuartil, margen_analysis['margen_neto_pct']) + 
                    (row['ingresos_total'] * 0.01), 2
                ),
                
                # Análisis completo
                'analisis_margen_completo': margen_analysis
            }
            enhanced_results.append(enhanced_row)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="bonus_margen_neto_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def analyze_bonus_margen_neto(self, periodo: str = "2025-10", umbral_margen: float = 15.0) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
        """
        query = """
            WITH margen_gestores AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_total,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_total,
                    ROUND(
                        (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                  THEN mov.IMPORTE ELSE 0 END)
                        - SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                  THEN ABS(mov.IMPORTE) ELSE 0 END))
                        /
                        NULLIF(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                       THEN mov.IMPORTE ELSE 0 END), 0) * 100, 2
                    ) as margen_neto_pct
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
                HAVING margen_neto_pct >= ?
            ),
            ranking_margen AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (ORDER BY margen_neto_pct DESC) as ranking_margen,
                    NTILE(4) OVER (ORDER BY margen_neto_pct DESC) as cuartil_margen
                FROM margen_gestores
            )
            SELECT
                GESTOR_ID,
                DESC_GESTOR,
                DESC_CENTRO,
                DESC_SEGMENTO,
                ingresos_total,
                gastos_total,
                margen_neto_pct,
                ranking_margen,
                cuartil_margen,
                CASE 
                    WHEN cuartil_margen = 1 THEN 'TOP_QUARTILE'
                    WHEN cuartil_margen = 2 THEN 'SECOND_QUARTILE'
                    ELSE 'GOOD_PERFORMANCE'
                END as categoria_bonus,
                ROUND(
                    CASE 
                        WHEN cuartil_margen = 1 AND margen_neto_pct >= 25.0 THEN 3000
                        WHEN cuartil_margen = 1 THEN 2500
                        WHEN cuartil_margen = 2 THEN 2000
                        ELSE 1500
                    END, 2
                ) as bonus_margen_eur,
                ROUND(ingresos_total * 0.01, 2) as bonus_volumen_eur,
                ROUND(
                    (CASE 
                        WHEN cuartil_margen = 1 AND margen_neto_pct >= 25.0 THEN 3000
                        WHEN cuartil_margen = 1 THEN 2500
                        WHEN cuartil_margen = 2 THEN 2000
                        ELSE 1500
                    END) + (ingresos_total * 0.01), 2
                ) as bonus_total_eur
            FROM ranking_margen
            ORDER BY margen_neto_pct DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, umbral_margen))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="bonus_margen_neto",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # FUNCIONES HELPER PARA CLASIFICACIONES MEJORADAS
    # =================================================================
    
    def _classify_performance_category(self, cumplimiento_global: float) -> str:
        """Clasificación de categorías de cumplimiento basada en umbrales CDG"""
        if cumplimiento_global >= 120.0:
            return 'EXCELENTE'
        elif cumplimiento_global >= 100.0:
            return 'CUMPLE'
        elif cumplimiento_global >= 80.0:
            return 'PARCIAL'
        else:
            return 'INCUMPLE'
    
    def _calculate_incentive_amount(self, cumplimiento_global: float, clasificacion_margen: str) -> float:
        """Cálculo de incentivos con bonus por clasificación de margen"""
        base_incentive = 0
        if cumplimiento_global >= 120.0:
            base_incentive = 5000 * 1.5
        elif cumplimiento_global >= 100.0:
            base_incentive = 5000 * 1.25
        elif cumplimiento_global >= 80.0:
            base_incentive = 5000 * 0.8
        
        # Bonus adicional por excelente margen
        if clasificacion_margen == 'EXCELENTE':
            base_incentive *= 1.2
        elif clasificacion_margen == 'BUENO':
            base_incentive *= 1.1
        
        return round(base_incentive, 2)
    
    def _classify_bonus_category(self, cuartil: int, margen_pct: float) -> str:
        """Clasificación de categorías de bonus"""
        if cuartil == 1:
            return 'TOP_QUARTILE'
        elif cuartil == 2:
            return 'SECOND_QUARTILE'
        else:
            return 'GOOD_PERFORMANCE'
    
    def _calculate_bonus_amount(self, cuartil: int, margen_pct: float) -> float:
        """Cálculo de bonus basado en cuartil y margen"""
        if cuartil == 1 and margen_pct >= 25.0:
            return 3000.0
        elif cuartil == 1:
            return 2500.0
        elif cuartil == 2:
            return 2000.0
        else:
            return 1500.0
    
    # =================================================================
    # 2. CRECIMIENTO DE PRODUCTOS Y CLIENTES (MANTENER ORIGINALES)
    # =================================================================
    
    def detect_producto_expansion(self, periodo_ini: str = "2025-09", periodo_fin: str = "2025-10", 
                                  min_crecimiento: float = 10.0) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA
        """
        query = """
            WITH productos_ini AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    COUNT(DISTINCT mc.PRODUCTO_ID) as productos_diferentes_ini,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_ini
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                WHERE strftime('%Y-%m', mc.FECHA_ALTA) <= ?
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR
            ),
            productos_fin AS (
                SELECT
                    g.GESTOR_ID,
                    COUNT(DISTINCT mc.PRODUCTO_ID) as productos_diferentes_fin,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_fin
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                WHERE strftime('%Y-%m', mc.FECHA_ALTA) <= ?
                GROUP BY g.GESTOR_ID
            ),
            detalle_productos AS (
                SELECT
                    g.GESTOR_ID,
                    mc.PRODUCTO_ID,
                    mp.DESC_PRODUCTO,
                    COUNT(mc.CONTRATO_ID) as contratos_producto,
                    strftime('%Y-%m', mc.FECHA_ALTA) as periodo_alta
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                JOIN MAESTRO_PRODUCTOS mp ON mc.PRODUCTO_ID = mp.PRODUCTO_ID
                WHERE strftime('%Y-%m', mc.FECHA_ALTA) BETWEEN ? AND ?
                GROUP BY g.GESTOR_ID, mc.PRODUCTO_ID, mp.DESC_PRODUCTO, periodo_alta
            )
            SELECT
                pi.GESTOR_ID,
                pi.DESC_GESTOR,
                COALESCE(pi.productos_diferentes_ini, 0) as productos_ini,
                COALESCE(pf.productos_diferentes_fin, 0) as productos_fin,
                COALESCE(pi.contratos_ini, 0) as contratos_ini,
                COALESCE(pf.contratos_fin, 0) as contratos_fin,
                COALESCE(pf.productos_diferentes_fin, 0) - COALESCE(pi.productos_diferentes_ini, 0) as productos_nuevos,
                COALESCE(pf.contratos_fin, 0) - COALESCE(pi.contratos_ini, 0) as contratos_nuevos,
                ROUND(
                    CASE WHEN COALESCE(pi.productos_diferentes_ini, 0) > 0 
                         THEN ((COALESCE(pf.productos_diferentes_fin, 0) - COALESCE(pi.productos_diferentes_ini, 0)) / 
                               CAST(pi.productos_diferentes_ini AS FLOAT)) * 100
                         ELSE 0 END, 2
                ) as crecimiento_productos_pct,
                ROUND(
                    CASE WHEN COALESCE(pi.contratos_ini, 0) > 0 
                         THEN ((COALESCE(pf.contratos_fin, 0) - COALESCE(pi.contratos_ini, 0)) / 
                               CAST(pi.contratos_ini AS FLOAT)) * 100
                         ELSE 0 END, 2
                ) as crecimiento_contratos_pct,
                CASE 
                    WHEN (COALESCE(pf.productos_diferentes_fin, 0) - COALESCE(pi.productos_diferentes_ini, 0)) >= 2 THEN 'EXPANSION_ALTA'
                    WHEN (COALESCE(pf.productos_diferentes_fin, 0) - COALESCE(pi.productos_diferentes_ini, 0)) >= 1 THEN 'EXPANSION_MEDIA'
                    ELSE 'SIN_EXPANSION'
                END as tipo_expansion
            FROM productos_ini pi
            LEFT JOIN productos_fin pf ON pi.GESTOR_ID = pf.GESTOR_ID
            WHERE (COALESCE(pf.productos_diferentes_fin, 0) - COALESCE(pi.productos_diferentes_ini, 0)) > 0
                AND ((COALESCE(pf.productos_diferentes_fin, 0) - COALESCE(pi.productos_diferentes_ini, 0)) / 
                     NULLIF(CAST(pi.productos_diferentes_ini AS FLOAT), 0)) * 100 >= ?
            ORDER BY crecimiento_productos_pct DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo_ini, periodo_fin, periodo_ini, periodo_fin, min_crecimiento))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="producto_expansion",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )

    # =================================================================
    # 4. RANKING Y POOL DE INCENTIVOS (MEJORADO CON KPI)
    # =================================================================
    
    def calculate_ranking_bonus_pool_enhanced(self, periodo: str = "2025-10", pool_total: float = 50000.0) -> QueryResult:
        """
        Calcula distribución del pool de incentivos entre top performers con análisis KPI mejorado.
        
        CASO DE USO: "¿Cómo se distribuye el pool de €50,000 entre los mejores gestores?"
        MEJORAS: Usa kpi_calculator para análisis integral de performance y clasificaciones automáticas
        """
        # Query simplificada para extraer datos base
        query = """
            WITH performance_completa AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                    COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes,
                    COALESCE(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                     THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_total,
                    COALESCE(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                     THEN ABS(mov.IMPORTE) ELSE 0 END), 0) as gastos_total
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                LEFT JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING ingresos_total > 0
            )
            SELECT * FROM performance_completa
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
        # ✅ PROCESAMIENTO AVANZADO CON KPI_CALCULATOR
        enhanced_results = []
        
        for row in raw_results:
            # Análisis integral con kpi_calculator
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            
            eficiencia_analysis = self.kpi_calc.calculate_ratio_eficiencia(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            
            # Análisis de crecimiento (mock data para demo)
            crecimiento_analysis = self.kpi_calc.calculate_crecimiento_captacion(
                clientes_fin=row['total_clientes'],
                clientes_ini=max(1, row['total_clientes'] - 2),  # Mock baseline
                periodo_dias=30
            )
            
            # Score ponderado mejorado con KPIs
            score_margen = margen_analysis['margen_neto_pct'] * 0.4 if margen_analysis['margen_neto_pct'] > 0 else 0
            score_eficiencia = min(eficiencia_analysis['ratio_eficiencia'] * 100, 400) * 0.3  # Cap at 400%
            score_volumen = (row['total_contratos'] * 500 + row['total_clientes'] * 1000) * 0.3
            
            score_ponderado = score_margen + score_eficiencia + score_volumen
            
            enhanced_row = {
                **row,
                'beneficio_neto': margen_analysis['beneficio_neto'],
                'margen_neto_pct': margen_analysis['margen_neto_pct'],
                'clasificacion_margen': margen_analysis['clasificacion'],
                'ratio_eficiencia': eficiencia_analysis['ratio_eficiencia'],
                'clasificacion_eficiencia': eficiencia_analysis['clasificacion'],
                'tasa_crecimiento_pct': crecimiento_analysis['crecimiento_pct'],
                'clasificacion_crecimiento': crecimiento_analysis['clasificacion'],
                'score_ponderado': round(score_ponderado, 2)
            }
            enhanced_results.append(enhanced_row)
        
        # Ordenar por score ponderado y asignar rankings
        enhanced_results.sort(key=lambda x: x['score_ponderado'], reverse=True)
        
        # Calcular distribución del pool
        total_score = sum(row['score_ponderado'] for row in enhanced_results[:20])  # Top 20
        
        for i, row in enumerate(enhanced_results[:20]):
            ranking = i + 1
            porcentaje_pool = (row['score_ponderado'] / total_score) * 100 if total_score > 0 else 0
            asignacion_pool = (row['score_ponderado'] / total_score) * pool_total if total_score > 0 else 0
            
            # ✅ CLASIFICACIÓN AUTOMÁTICA DE TIER MEJORADA
            tier_incentivo = self._classify_incentive_tier(ranking, row['clasificacion_margen'], row['clasificacion_eficiencia'])
            
            # Multiplicador por tier
            multiplicador = self._get_tier_multiplier(tier_incentivo)
            incentivo_final = asignacion_pool * multiplicador
            
            row.update({
                'ranking_general': ranking,
                'porcentaje_pool': round(porcentaje_pool, 2),
                'asignacion_pool_eur': round(asignacion_pool, 2),
                'tier_incentivo': tier_incentivo,
                'multiplicador_tier': multiplicador,
                'incentivo_final_eur': round(incentivo_final, 2)
            })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results[:20],
            query_type="ranking_bonus_pool_enhanced",
            execution_time=execution_time,
            row_count=min(20, len(enhanced_results)),
            query_sql=query
        )
    
    def calculate_ranking_bonus_pool(self, periodo: str = "2025-10", pool_total: float = 50000.0) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
        """
        query = """
            WITH performance_completa AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                    COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes,
                    COALESCE(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                     THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_total,
                    COALESCE(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                     THEN ABS(mov.IMPORTE) ELSE 0 END), 0) as gastos_total,
                    ROUND(
                        COALESCE((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                          THEN mov.IMPORTE ELSE 0 END)
                                - SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                          THEN ABS(mov.IMPORTE) ELSE 0 END)), 0), 2
                    ) as beneficio_neto
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                LEFT JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING beneficio_neto > 0
            ),
            ranking_ponderado AS (
                SELECT
                    *,
                    -- Score ponderado: 40% beneficio, 30% contratos, 30% clientes
                    ROUND(
                        (beneficio_neto * 0.4) + 
                        (total_contratos * 500 * 0.3) + 
                        (total_clientes * 1000 * 0.3), 2
                    ) as score_ponderado,
                    ROW_NUMBER() OVER (ORDER BY 
                        (beneficio_neto * 0.4) + 
                        (total_contratos * 500 * 0.3) + 
                        (total_clientes * 1000 * 0.3) DESC
                    ) as ranking_general
                FROM performance_completa
            ),
            distribucion_pool AS (
                SELECT
                    *,
                    SUM(score_ponderado) OVER () as score_total,
                    ROUND((score_ponderado / SUM(score_ponderado) OVER ()) * ?, 2) as asignacion_pool_eur,
                    CASE 
                        WHEN ranking_general <= 3 THEN 'TIER_1_PREMIUM'
                        WHEN ranking_general <= 8 THEN 'TIER_2_EXCELENTE'
                        WHEN ranking_general <= 15 THEN 'TIER_3_BUENO'
                        ELSE 'TIER_4_PARTICIPACION'
                    END as tier_incentivo
                FROM ranking_ponderado
                WHERE ranking_general <= 20  -- Top 20 gestores
            )
            SELECT
                ranking_general,
                GESTOR_ID,
                DESC_GESTOR,
                DESC_CENTRO,
                DESC_SEGMENTO,
                total_contratos,
                total_clientes,
                beneficio_neto,
                score_ponderado,
                tier_incentivo,
                asignacion_pool_eur,
                ROUND((asignacion_pool_eur / ?) * 100, 2) as porcentaje_pool,
                -- Bonus adicional por tier
                ROUND(
                    CASE 
                        WHEN tier_incentivo = 'TIER_1_PREMIUM' THEN asignacion_pool_eur * 1.5
                        WHEN tier_incentivo = 'TIER_2_EXCELENTE' THEN asignacion_pool_eur * 1.25
                        WHEN tier_incentivo = 'TIER_3_BUENO' THEN asignacion_pool_eur * 1.1
                        ELSE asignacion_pool_eur
                    END, 2
                ) as incentivo_final_eur
            FROM distribucion_pool
            ORDER BY ranking_general
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, pool_total, pool_total))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="ranking_bonus_pool",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # FUNCIONES HELPER ADICIONALES PARA CLASIFICACIONES MEJORADAS
    # =================================================================
    
    def _classify_incentive_tier(self, ranking: int, clasificacion_margen: str, clasificacion_eficiencia: str) -> str:
        """Clasificación de tier de incentivos basada en ranking y KPIs"""
        if ranking <= 3 and clasificacion_margen in ['EXCELENTE'] and clasificacion_eficiencia in ['MUY_EFICIENTE']:
            return 'TIER_1_PREMIUM'
        elif ranking <= 8 and clasificacion_margen in ['EXCELENTE', 'BUENO']:
            return 'TIER_2_EXCELENTE'
        elif ranking <= 15:
            return 'TIER_3_BUENO'
        else:
            return 'TIER_4_PARTICIPACION'
    
    def _get_tier_multiplier(self, tier: str) -> float:
        """Multiplicador de incentivos por tier"""
        multipliers = {
            'TIER_1_PREMIUM': 1.5,
            'TIER_2_EXCELENTE': 1.25,
            'TIER_3_BUENO': 1.1,
            'TIER_4_PARTICIPACION': 1.0
        }
        return multipliers.get(tier, 1.0)
    
    # =================================================================
    # 5. GENERADOR DINÁMICO DE QUERIES DE INCENTIVOS (MANTENER)
    # =================================================================
    
    def generate_dynamic_incentive_query(self, user_question: str, context: Dict[str, Any] = None) -> QueryResult:
        """
        Genera consultas de incentivos SQL dinámicas usando GPT-4 para preguntas específicas.
        FUNCIÓN ORIGINAL MANTENIDA
        """
        from ..prompts.system_prompts import get_incentive_generation_prompt
        
        try:
            # Usar prompt especializado para incentivos
            system_prompt = get_incentive_generation_prompt(context)
            
            user_prompt = f"""
            Genera una consulta SQL para análisis de incentivos para responder: "{user_question}"
            
            La consulta debe enfocarse en detectar performance positiva, crecimiento, y elegibilidad para bonos.
            """
            
            # Generar la consulta con GPT-4
            response = iniciar_agente_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=1000
            )
            
            generated_sql = response.choices[0].message.content.strip()
            
            # Limpiar la respuesta
            if "```sql" in generated_sql:
                generated_sql = generated_sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in generated_sql:
                generated_sql = generated_sql.split("```")[1].split("```")[0].strip()
            
            # Validar la consulta antes de ejecutarla
            if not is_query_safe(generated_sql):
                logger.error(f"❌ Consulta SQL bloqueada por seguridad: {generated_sql}")
                return QueryResult(
                    data=[{"error": "Consulta SQL bloqueada por contener instrucciones no autorizadas"}],
                    query_type="incentive_security_error",
                    execution_time=0,
                    row_count=0,
                    query_sql=generated_sql
                )
            
            logger.info(f"✅ Query de incentivos dinámica generada para: {user_question}")
            
            # Ejecutar la query validada
            start_time = datetime.now()
            results = execute_query(generated_sql)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                data=results,
                query_type="dynamic_incentive_generated",
                execution_time=execution_time,
                row_count=len(results) if results else 0,
                query_sql=generated_sql
            )
            
        except Exception as e:
            logger.error(f"❌ Error generando query de incentivos dinámica: {e}")
            return QueryResult(
                data=[{"error": f"No se pudo generar consulta de incentivos para: {user_question}", "details": str(e)}],
                query_type="incentive_dynamic_error",
                execution_time=0,
                row_count=0,
                query_sql="-- Error en generación dinámica de incentivos"
            )
    
    # =================================================================
    # 6. MOTOR DE SELECCIÓN INTELIGENTE PARA INCENTIVOS (AMPLIADO)
    # =================================================================
    
    def get_best_incentive_query_for_question(self, user_question: str, context: Dict[str, Any] = None) -> QueryResult:
        """
        Motor inteligente que decide qué query de incentivos usar según la pregunta del usuario.
        FUNCIÓN AMPLIADA CON VERSIONES ENHANCED
        """
        from ..prompts.system_prompts import get_incentive_classification_prompt
        
        # Lista de queries predefinidas disponibles (AMPLIADA)
        available_queries = [
            "calculate_incentivo_cumplimiento_objetivos",
            "calculate_incentivo_cumplimiento_objetivos_enhanced",  # ✅ NUEVA
            "analyze_bonus_margen_neto",
            "analyze_bonus_margen_neto_enhanced",  # ✅ NUEVA
            "detect_producto_expansion",
            "detect_captacion_clientes",
            "simulate_incentivo_scenarios",
            "calculate_ranking_bonus_pool",
            "calculate_ranking_bonus_pool_enhanced"  # ✅ NUEVA
        ]
        
        try:
            # FASE 1: Clasificación inteligente con GPT-4 especializada en incentivos
            classification_prompt = get_incentive_classification_prompt(available_queries)
            
            classification_response = iniciar_agente_llm(
                system_prompt=classification_prompt,
                user_prompt=f'Clasifica esta pregunta de incentivos: "{user_question}"',
                temperature=0.0,
                max_tokens=50
            )
            
            predicted_query = classification_response.choices[0].message.content.strip()
            
            logger.info(f"🧠 Clasificación de incentivos: '{user_question}' → {predicted_query}")
            
            # FASE 2: Ejecutar query predefinida si se identificó correctamente
            if predicted_query in available_queries:
                query_method = getattr(self, predicted_query)
                
                # Usar contexto si está disponible para parámetros
                if context and 'params' in context:
                    result = query_method(**context['params'])
                else:
                    # Parámetros por defecto para testing
                    if predicted_query in ["simulate_incentivo_scenarios"]:
                        result = query_method("1", {"optimista": 1.2, "conservador": 1.1})  # Gestor ID 1
                    elif predicted_query in ["detect_producto_expansion", "detect_captacion_clientes"]:
                        result = query_method("2025-09", "2025-10")
                    elif predicted_query in ["calculate_ranking_bonus_pool", "calculate_ranking_bonus_pool_enhanced"]:
                        result = query_method("2025-10", 50000.0)
                    else:
                        result = query_method("2025-10")
                
                logger.info(f"✅ Query de incentivos predefinida ejecutada exitosamente: {predicted_query}")
                return result
            
            # FASE 3: Usar generación dinámica si no se identificó query predefinida
            elif predicted_query == "DYNAMIC_QUERY":
                logger.info(f"🤖 Usando generación dinámica para pregunta de incentivos compleja: {user_question}")
                return self.generate_dynamic_incentive_query(user_question, context)
            
            else:
                # FASE 4: Fallback por clasificación incorrecta
                logger.warning(f"⚠️ Clasificación de incentivos no reconocida: {predicted_query}. Usando generación dinámica.")
                return self.generate_dynamic_incentive_query(user_question, context)
                
        except Exception as e:
            logger.error(f"❌ Error en motor de selección de incentivos: {e}")
            
            # Fallback final: generación dinámica
            logger.info(f"🔄 Fallback: Usando generación dinámica por error en clasificación de incentivos")
            return self.generate_dynamic_incentive_query(user_question, context)

# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# =================================================================

# Instancia global para uso en toda la aplicación
incentive_queries = IncentiveQueries()

# Funciones de conveniencia originales mantenidas
def calculate_incentivos_objetivos(periodo: str = "2025-10", umbral: float = 100.0):
    """Función de conveniencia para calcular incentivos por cumplimiento de objetivos"""
    return incentive_queries.calculate_incentivo_cumplimiento_objetivos(periodo, umbral)

def analyze_bonus_por_margen(periodo: str = "2025-10", umbral_margen: float = 15.0):
    """Función de conveniencia para análisis de bonus por margen alto"""
    return incentive_queries.analyze_bonus_margen_neto(periodo, umbral_margen)

def detect_expansion_productos(periodo_ini: str = "2025-09", periodo_fin: str = "2025-10"):
    """Función de conveniencia para detectar expansión de productos"""
    return incentive_queries.detect_producto_expansion(periodo_ini, periodo_fin)

def calculate_ranking_bonus(periodo: str = "2025-10", pool: float = 50000.0):
    """Función de conveniencia para calcular ranking y distribución de bonus"""
    return incentive_queries.calculate_ranking_bonus_pool(periodo, pool)

def ask_incentive_question(question: str, context: Dict[str, Any] = None):
    """
    Función de conveniencia para hacer cualquier pregunta sobre incentivos
    """
    return incentive_queries.get_best_incentive_query_for_question(question, context)

# ✅ NUEVAS funciones de conveniencia para versiones enhanced
def calculate_incentivos_objetivos_enhanced(periodo: str = "2025-10", umbral: float = 100.0):
    """Función de conveniencia para cálculo mejorado de incentivos por cumplimiento"""
    return incentive_queries.calculate_incentivo_cumplimiento_objetivos_enhanced(periodo, umbral)

def analyze_bonus_margen_enhanced(periodo: str = "2025-10", umbral_margen: float = 15.0):
    """Función de conveniencia para análisis mejorado de bonus por margen"""
    return incentive_queries.analyze_bonus_margen_neto_enhanced(periodo, umbral_margen)

def calculate_ranking_bonus_enhanced(periodo: str = "2025-10", pool: float = 50000.0):
    """Función de conveniencia para cálculo mejorado de ranking y distribución de bonus"""
    return incentive_queries.calculate_ranking_bonus_pool_enhanced(periodo, pool)
