"""
comparative_queries.py

Consultas comparativas y de benchmarking para el agente de Control de Gestión.
Incluye funciones entre productos, segmentos, centros, gestores y periodos.
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

class ComparativeQueries:
    """
    Biblioteca completa de consultas comparativas para análisis de benchmarking
    
    COBERTURA MEJORADA:
    - Comparativas temporales: período a período con KPIs estandarizados
    - Benchmarking entre entidades: gestores, centros, productos con clasificaciones automáticas
    - Análisis de desviaciones: real vs estándar con acciones recomendadas
    - Rankings y posicionamiento relativo con interpretaciones contextuales
    - Queries dinámicas: generación automática con validación
    """
    
    def __init__(self):
        self.query_cache = {}
        self.kpi_calc = kpi_calculator  # ✅ INSTANCIA KPI_CALCULATOR
    
    # =================================================================
    # 1. COMPARATIVAS DE PRECIOS Y PRODUCTOS (CORREGIDAS PARA CDG)
    # =================================================================
    
    def compare_precio_producto_real_mes(self, producto_id: str, segmento_id: str, mes_ini: str, mes_fin: str) -> QueryResult:
        """
        Variación del precio real de un producto-segmento entre dos meses (AAAA-MM).
        ✅ CORREGIDO PARA CDG: Usa productos reales como 600100300300 y segmentos N20301
        """
        query = """
            SELECT
                p1.PRODUCTO_ID,
                p1.SEGMENTO_ID,
                p1.PRECIO_MANTENIMIENTO_REAL AS precio_ini,
                p2.PRECIO_MANTENIMIENTO_REAL AS precio_fin,
                ROUND(
                    (p2.PRECIO_MANTENIMIENTO_REAL - p1.PRECIO_MANTENIMIENTO_REAL) / 
                    NULLIF(p1.PRECIO_MANTENIMIENTO_REAL, 0) * 100, 2
                ) AS variacion_pct,
                p1.FECHA_CALCULO AS fecha_ini,
                p2.FECHA_CALCULO AS fecha_fin
            FROM PRECIO_POR_PRODUCTO_REAL p1
            JOIN PRECIO_POR_PRODUCTO_REAL p2
                ON p1.PRODUCTO_ID = p2.PRODUCTO_ID AND p1.SEGMENTO_ID = p2.SEGMENTO_ID
            WHERE p1.PRODUCTO_ID = ?
              AND p1.SEGMENTO_ID = ?
              AND substr(p1.FECHA_CALCULO, 1, 7) = ?
              AND substr(p2.FECHA_CALCULO, 1, 7) = ?
        """
        
        start_time = datetime.now()
        results = execute_query(query, (producto_id, segmento_id, mes_ini, mes_fin))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="comparativa_precio_producto_real",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def compare_precio_real_vs_std_enhanced(self, producto_id: str, segmento_id: str, periodo: str) -> QueryResult:
        """
        Diferencia entre precio real y estándar con análisis de desviaciones MEJORADO.
        
        CASO DE USO: "¿Cuál es la desviación entre precio real y estándar del producto X?"
        ✅ CORREGIDO: Usa kpi_calculator para análisis de desviaciones con acciones recomendadas
        """
        query = """
            SELECT
                pr.PRODUCTO_ID,
                mp.DESC_PRODUCTO,
                pr.SEGMENTO_ID,
                ms.DESC_SEGMENTO,
                pr.PRECIO_MANTENIMIENTO_REAL,
                ps.PRECIO_MANTENIMIENTO,
                pr.FECHA_CALCULO,
                pr.NUM_CONTRATOS_BASE
            FROM PRECIO_POR_PRODUCTO_REAL pr
            JOIN PRECIO_POR_PRODUCTO_STD ps
                ON pr.PRODUCTO_ID = ps.PRODUCTO_ID AND pr.SEGMENTO_ID = ps.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS mp ON pr.PRODUCTO_ID = mp.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS ms ON pr.SEGMENTO_ID = ms.SEGMENTO_ID
            WHERE pr.PRODUCTO_ID = ?
              AND pr.SEGMENTO_ID = ?
              AND substr(pr.FECHA_CALCULO, 1, 7) = ?
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (producto_id, segmento_id, periodo))
        
        # ✅ PROCESO MEJORADO CON KPI_CALCULATOR
        enhanced_results = []
        for row in raw_results:
            precio_real = row['PRECIO_MANTENIMIENTO_REAL']
            precio_std = row['PRECIO_MANTENIMIENTO']
            
            # Usar kpi_calculator para análisis de desviación estandarizado
            desviacion_analysis = self.kpi_calc.analyze_desviacion_presupuestaria(
                valor_real=precio_real,
                valor_presupuestado=precio_std
            )
            
            # Combinar datos originales con análisis KPI
            enhanced_row = {
                **row,
                'desviacion_pct': desviacion_analysis['desviacion_pct'],
                'desviacion_absoluta': desviacion_analysis['desviacion_absoluta'],
                'nivel_alerta': desviacion_analysis['nivel_alerta'],  # CRITICA, ALTA, MEDIA, NORMAL
                'accion_recomendada': desviacion_analysis['accion_recomendada'],
                'tipo_desviacion': desviacion_analysis['tipo_desviacion'],  # POSITIVA/NEGATIVA
                'analisis_kpi': desviacion_analysis  # Análisis completo para drill-down
            }
            enhanced_results.append(enhanced_row)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="comparativa_precio_real_vs_std_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def compare_precio_real_vs_std(self, producto_id: str, segmento_id: str, periodo: str) -> QueryResult:
        """
        ✅ CORREGIDO: Función original con datos CDG reales
        """
        query = """
            SELECT
                pr.PRODUCTO_ID,
                mp.DESC_PRODUCTO,
                pr.SEGMENTO_ID,
                ms.DESC_SEGMENTO,
                pr.PRECIO_MANTENIMIENTO_REAL,
                ps.PRECIO_MANTENIMIENTO,
                ROUND(
                    (pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                    NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100, 2
                ) AS desviacion_pct,
                CASE 
                    WHEN ABS((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                         NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100) >= 15.0 THEN 'CRITICA'
                    WHEN ABS((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                         NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100) >= 10.0 THEN 'ALTA'
                    ELSE 'NORMAL'
                END AS nivel_alerta
            FROM PRECIO_POR_PRODUCTO_REAL pr
            JOIN PRECIO_POR_PRODUCTO_STD ps
                ON pr.PRODUCTO_ID = ps.PRODUCTO_ID AND pr.SEGMENTO_ID = ps.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS mp ON pr.PRODUCTO_ID = mp.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS ms ON pr.SEGMENTO_ID = ms.SEGMENTO_ID
            WHERE pr.PRODUCTO_ID = ?
              AND pr.SEGMENTO_ID = ?
              AND substr(pr.FECHA_CALCULO, 1, 7) = ?
        """
        
        start_time = datetime.now()
        results = execute_query(query, (producto_id, segmento_id, periodo))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="comparativa_precio_real_vs_std",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def ranking_productos_desviacion_precio(self, periodo: str, limite: int = 10) -> QueryResult:
        """
        Ranking de productos por desviación porcentual entre precio real y estándar.
        ✅ CORREGIDO: Compatible con productos CDG reales
        """
        query = """
            SELECT
                pr.PRODUCTO_ID,
                mp.DESC_PRODUCTO,
                pr.SEGMENTO_ID,
                ms.DESC_SEGMENTO,
                pr.PRECIO_MANTENIMIENTO_REAL,
                ps.PRECIO_MANTENIMIENTO,
                ROUND(
                    (pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                    NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100, 2
                ) as desviacion_pct,
                CASE 
                    WHEN pr.PRECIO_MANTENIMIENTO_REAL > ps.PRECIO_MANTENIMIENTO THEN 'SOBRECOSTO'
                    ELSE 'EFICIENCIA'
                END as tipo_desviacion
            FROM PRECIO_POR_PRODUCTO_REAL pr
            JOIN PRECIO_POR_PRODUCTO_STD ps ON pr.PRODUCTO_ID = ps.PRODUCTO_ID 
                AND pr.SEGMENTO_ID = ps.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS mp ON pr.PRODUCTO_ID = mp.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS ms ON pr.SEGMENTO_ID = ms.SEGMENTO_ID
            WHERE substr(pr.FECHA_CALCULO, 1, 7) = ?
            ORDER BY ABS(desviacion_pct) DESC
            LIMIT ?
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, limite))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="ranking_productos_desviacion_precio",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 2. COMPARATIVAS DE GESTORES MEJORADAS CON CÓDIGOS CDR CORRECTOS
    # =================================================================
    
    def ranking_gestores_por_margen_enhanced(self, periodo: str) -> QueryResult:
        """
        Ranking de gestores con análisis de margen estandarizado y clasificaciones automáticas.
        
        CASO DE USO: "¿Qué gestores tienen mejor margen que la media?"
        ✅ CORREGIDO: Usa códigos CDR reales de tu BD y kpi_calculator para cálculos
        """
        # Query corregida con códigos CDR reales
        query = """
            WITH gestor_data AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_total,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_total
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                JOIN MAESTRO_GESTORES g ON cont.GESTOR_ID = g.GESTOR_ID
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                THEN mov.IMPORTE ELSE 0 END) > 0
            )
            SELECT * FROM gestor_data
            ORDER BY ingresos_total DESC
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
        # ✅ PROCESAMIENTO AVANZADO CON KPI_CALCULATOR
        enhanced_results = []
        margenes_para_media = []
        
        # Validar que hay datos antes del procesamiento
        if not raw_results:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                data=[],
                query_type="ranking_gestores_margen_enhanced",
                execution_time=execution_time,
                row_count=0,
                query_sql=query
            )
        
        # Primera pasada: calcular todos los márgenes
        for row in raw_results:
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            margenes_para_media.append(margen_analysis['margen_neto_pct'])
        
        # Calcular media para comparaciones
        media_margen = sum(margenes_para_media) / len(margenes_para_media) if margenes_para_media else 0
        
        # Segunda pasada: generar resultados mejorados
        for i, row in enumerate(raw_results):
            # Análisis de margen con kpi_calculator
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            
            # Análisis de eficiencia
            eficiencia_analysis = self.kpi_calc.calculate_ratio_eficiencia(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            
            enhanced_row = {
                **row,
                'ranking': i + 1,
                'margen_neto': margen_analysis['margen_neto_pct'],
                'beneficio_neto': margen_analysis['beneficio_neto'],
                'clasificacion_margen': margen_analysis['clasificacion'],  # EXCELENTE, BUENO, ACEPTABLE, etc.
                'media_margen': round(media_margen, 2),
                'desviacion_vs_media': round(margen_analysis['margen_neto_pct'] - media_margen, 2),
                'ratio_eficiencia': eficiencia_analysis['ratio_eficiencia'],
                'clasificacion_eficiencia': eficiencia_analysis['clasificacion'],
                'interpretacion': eficiencia_analysis['interpretacion'],
                
                # ✅ NUEVA CLASIFICACIÓN INTEGRAL
                'categoria_performance': self._classify_gestor_performance(
                    margen_analysis['clasificacion'],
                    eficiencia_analysis['clasificacion'],
                    margen_analysis['margen_neto_pct'] - media_margen
                ),
                
                # Análisis completo para drill-down
                'analisis_completo': {
                    'margen': margen_analysis,
                    'eficiencia': eficiencia_analysis
                }
            }
            enhanced_results.append(enhanced_row)
        
        # Ordenar por margen neto
        enhanced_results.sort(key=lambda x: x['margen_neto'], reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="ranking_gestores_margen_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    def ranking_gestores_por_margen(self, periodo: str) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD CON DATOS CORREGIDOS
        ✅ CORREGIDO: Usa códigos CDR reales de tu BD (CR0001, CR0008, CR0012, CR0014, CR0016, CR0017)
        """
        query = """
            WITH gestor_margenes AS (
                SELECT
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_total,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_total,
                    ROUND(
                        (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                  THEN mov.IMPORTE ELSE 0 END)
                        - SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                                  THEN ABS(mov.IMPORTE) ELSE 0 END))
                        /
                        NULLIF(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                       THEN mov.IMPORTE ELSE 0 END), 0) * 100, 2
                    ) AS margen_neto
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                JOIN MAESTRO_GESTORES g ON cont.GESTOR_ID = g.GESTOR_ID
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                THEN mov.IMPORTE ELSE 0 END) > 0
            ),
            media AS (
                SELECT AVG(margen_neto) as media_margen FROM gestor_margenes
            )
            SELECT
                ROW_NUMBER() OVER (ORDER BY gm.margen_neto DESC) as ranking,
                gm.GESTOR_ID,
                gm.DESC_GESTOR,
                gm.DESC_CENTRO,
                gm.DESC_SEGMENTO,
                gm.ingresos_total,
                gm.gastos_total,
                gm.margen_neto,
                m.media_margen,
                ROUND(gm.margen_neto - m.media_margen, 2) AS desviacion_vs_media,
                CASE 
                    WHEN gm.margen_neto > m.media_margen + 5 THEN 'SUPERIOR'
                    WHEN gm.margen_neto < m.media_margen - 5 THEN 'INFERIOR'
                    ELSE 'PROMEDIO'
                END as categoria_performance
            FROM gestor_margenes gm
            CROSS JOIN media m
            ORDER BY gm.margen_neto DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo,))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="ranking_gestores_margen",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def compare_roe_gestores_enhanced(self, periodo: str) -> QueryResult:
        """
        Ranking de gestores con ROE estandarizado y clasificaciones bancarias automáticas.
        ✅ CORREGIDO: Usa códigos CDR reales y kpi_calculator para ROE con benchmarks sector bancario
        """
        query = """
            WITH gestor_financials AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    COALESCE(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) as patrimonio_total,
                    (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                              THEN mov.IMPORTE ELSE 0 END) - 
                     SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                              THEN ABS(mov.IMPORTE) ELSE 0 END)) as beneficio_neto
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', COALESCE(mov.FECHA, mc.FECHA_ALTA)) <= ?
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO
                HAVING patrimonio_total > 0
            )
            SELECT * FROM gestor_financials
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
        enhanced_results = []
        roes_para_media = []
        
        # Validar que hay datos antes del procesamiento
        if not raw_results:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                data=[],
                query_type="comparativa_roe_gestores_enhanced",
                execution_time=execution_time,
                row_count=0,
                query_sql=query
            )
        
        # Primera pasada: calcular todos los ROEs
        for row in raw_results:
            roe_analysis = self.kpi_calc.calculate_roe(
                beneficio_neto=row['beneficio_neto'],
                patrimonio=row['patrimonio_total']
            )
            if roe_analysis['roe_pct'] != 0:  # Excluir casos sin patrimonio
                roes_para_media.append(roe_analysis['roe_pct'])
        
        # Calcular media
        media_roe = sum(roes_para_media) / len(roes_para_media) if roes_para_media else 0
        
        # Segunda pasada: generar resultados mejorados
        for i, row in enumerate(raw_results):
            # Análisis ROE con kpi_calculator
            roe_analysis = self.kpi_calc.calculate_roe(
                beneficio_neto=row['beneficio_neto'],
                patrimonio=row['patrimonio_total']
            )
            
            enhanced_row = {
                **row,
                'ranking': i + 1,
                'roe': roe_analysis['roe_pct'],
                'clasificacion_roe': roe_analysis['clasificacion'],  # SOBRESALIENTE, BUENO, PROMEDIO, etc.
                'benchmark_vs_sector': roe_analysis['benchmark_vs_sector'],
                'media_roe': round(media_roe, 4),
                'desviacion_vs_media': round(roe_analysis['roe_pct'] - media_roe, 4),
                'analisis_roe_completo': roe_analysis  # Para drill-down
            }
            enhanced_results.append(enhanced_row)
        
        # Ordenar por ROE
        enhanced_results.sort(key=lambda x: x['roe'], reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="comparativa_roe_gestores_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def compare_roe_gestores(self, periodo: str) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
        ✅ CORREGIDO: Usa códigos CDR reales de tu BD
        """
        query = """
            WITH patrimonio_gestores AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    COALESCE(SUM(mov.IMPORTE), 0) as patrimonio_total
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE c.IND_CENTRO_FINALISTA = 1
                    AND strftime('%Y-%m', COALESCE(mov.FECHA, mc.FECHA_ALTA)) <= ?
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO
            ),
            beneficios_gestores AS (
                SELECT 
                    g.GESTOR_ID,
                    (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                              THEN mov.IMPORTE ELSE 0 END) - 
                     SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                              THEN ABS(mov.IMPORTE) ELSE 0 END)) as beneficio_neto
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                GROUP BY g.GESTOR_ID
            ),
            roe_calculated AS (
                SELECT 
                    pg.GESTOR_ID,
                    pg.DESC_GESTOR,
                    pg.DESC_CENTRO,
                    pg.patrimonio_total,
                    COALESCE(bg.beneficio_neto, 0) as beneficio_neto,
                    CASE 
                        WHEN pg.patrimonio_total > 0 
                        THEN ROUND((COALESCE(bg.beneficio_neto, 0) / pg.patrimonio_total) * 100, 4)
                        ELSE 0 
                    END as roe
                FROM patrimonio_gestores pg
                LEFT JOIN beneficios_gestores bg ON pg.GESTOR_ID = bg.GESTOR_ID
                WHERE pg.patrimonio_total > 0
            ),
            media_roe AS (
                SELECT AVG(roe) as media FROM roe_calculated WHERE roe IS NOT NULL
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY rc.roe DESC) as ranking,
                rc.GESTOR_ID,
                rc.DESC_GESTOR,
                rc.DESC_CENTRO,
                rc.patrimonio_total,
                rc.beneficio_neto,
                rc.roe,
                mr.media as media_roe,
                ROUND(rc.roe - mr.media, 4) as desviacion_vs_media
            FROM roe_calculated rc
            CROSS JOIN media_roe mr
            ORDER BY rc.roe DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, periodo))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="comparativa_roe_gestores",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 3. COMPARATIVAS POR CENTRO (CORREGIDAS)
    # =================================================================
    
    def compare_eficiencia_centro_enhanced(self, periodo: str) -> QueryResult:
        """
        Ranking de centros con análisis de eficiencia estandarizado y clasificaciones automáticas.
        ✅ CORREGIDO: Usa códigos CDR reales y kpi_calculator para ratios de eficiencia
        """
        query = """
            WITH centro_data AS (
                SELECT
                    mc.CENTRO_CONTABLE,
                    c.DESC_CENTRO,
                    COUNT(DISTINCT g.GESTOR_ID) as num_gestores,
                    COUNT(DISTINCT mc.CONTRATO_ID) as num_contratos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
                JOIN MAESTRO_CENTROS c ON mc.CENTRO_CONTABLE = c.CENTRO_ID
                JOIN MAESTRO_GESTORES g ON mc.GESTOR_ID = g.GESTOR_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY mc.CENTRO_CONTABLE, c.DESC_CENTRO
            )
            SELECT * FROM centro_data
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
        enhanced_results = []
        
        # Validar que hay datos antes del procesamiento
        if not raw_results:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                data=[],
                query_type="comparativa_eficiencia_centro_enhanced",
                execution_time=execution_time,
                row_count=0,
                query_sql=query
            )
        
        for i, row in enumerate(raw_results):
            # Análisis de margen con kpi_calculator
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos'],
                gastos=row['gastos']
            )
            
            # Análisis de eficiencia con kpi_calculator
            eficiencia_analysis = self.kpi_calc.calculate_ratio_eficiencia(
                ingresos=row['ingresos'],
                gastos=row['gastos']
            )
            
            enhanced_row = {
                **row,
                'ranking': i + 1,  # Se reordenará después
                'ingresos': round(row['ingresos'], 2),
                'gastos': round(row['gastos'], 2),
                'beneficio_neto': margen_analysis['beneficio_neto'],
                'margen_neto_pct': margen_analysis['margen_neto_pct'],
                'clasificacion_margen': margen_analysis['clasificacion'],
                
                # ✅ ANÁLISIS DE EFICIENCIA MEJORADO
                'ratio_eficiencia': eficiencia_analysis['ratio_eficiencia'],
                'clasificacion_eficiencia': eficiencia_analysis['clasificacion'],
                'interpretacion_eficiencia': eficiencia_analysis['interpretacion'],
                
                # Métricas adicionales
                'gasto_por_contrato': round(row['gastos'] / row['num_contratos'], 2) if row['num_contratos'] > 0 else 0,
                'ingreso_por_gestor': round(row['ingresos'] / row['num_gestores'], 2) if row['num_gestores'] > 0 else 0,
                
                # Análisis completo para drill-down
                'analisis_completo': {
                    'margen': margen_analysis,
                    'eficiencia': eficiencia_analysis
                }
            }
            enhanced_results.append(enhanced_row)
        
        # Ordenar por ratio de eficiencia
        enhanced_results.sort(key=lambda x: x['ratio_eficiencia'] if x['ratio_eficiencia'] != float('inf') else 0, reverse=True)
        
        # Actualizar rankings
        for i, row in enumerate(enhanced_results):
            row['ranking'] = i + 1
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="comparativa_eficiencia_centro_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def compare_eficiencia_centro(self, periodo: str) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
        ✅ CORREGIDO: Usa códigos CDR reales de tu BD
        """
        query = """
            WITH centro_eficiencia AS (
                SELECT
                    mc.CENTRO_CONTABLE,
                    c.DESC_CENTRO,
                    COUNT(DISTINCT g.GESTOR_ID) as num_gestores,
                    COUNT(DISTINCT mc.CONTRATO_ID) as num_contratos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
                JOIN MAESTRO_CENTROS c ON mc.CENTRO_CONTABLE = c.CENTRO_ID
                JOIN MAESTRO_GESTORES g ON mc.GESTOR_ID = g.GESTOR_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY mc.CENTRO_CONTABLE, c.DESC_CENTRO
            )
            SELECT
                ROW_NUMBER() OVER (ORDER BY 
                    CASE WHEN gastos = 0 THEN NULL 
                         ELSE (ingresos / gastos) END DESC NULLS LAST
                ) as ranking,
                CENTRO_CONTABLE,
                DESC_CENTRO,
                num_gestores,
                num_contratos,
                ROUND(ingresos, 2) as ingresos,
                ROUND(gastos, 2) as gastos,
                ROUND(ingresos - gastos, 2) as beneficio_neto,
                ROUND(CASE WHEN gastos = 0 THEN NULL 
                           ELSE (ingresos / gastos) END, 2) AS ratio_eficiencia,
                ROUND(CASE WHEN num_contratos = 0 THEN 0 
                           ELSE gastos / num_contratos END, 2) as gasto_por_contrato,
                ROUND(CASE WHEN ingresos = 0 THEN 0 
                           ELSE ((ingresos - gastos) / ingresos) * 100 END, 2) as margen_neto_pct
            FROM centro_eficiencia
            ORDER BY ratio_eficiencia DESC NULLS LAST
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo,))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="comparativa_eficiencia_centro",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def compare_gastos_centro_periodo(self, centro_contable: int, mes_ini: str, mes_fin: str) -> QueryResult:
        """
        Variación de gastos de un centro contable entre dos meses.
        FUNCIÓN ORIGINAL MANTENIDA - Sin cambios necesarios
        """
        query = """
            WITH gastos_ini AS (
                SELECT 
                    gc.CENTRO_CONTABLE,
                    c.DESC_CENTRO,
                    gc.CONCEPTO_COSTE,
                    SUM(gc.IMPORTE) as importe_ini
                FROM GASTOS_CENTRO gc
                JOIN MAESTRO_CENTROS c ON gc.CENTRO_CONTABLE = c.CENTRO_ID
                WHERE gc.CENTRO_CONTABLE = ?
                    AND substr(gc.FECHA, 1, 7) = ?
                GROUP BY gc.CENTRO_CONTABLE, c.DESC_CENTRO, gc.CONCEPTO_COSTE
            ),
            gastos_fin AS (
                SELECT 
                    gc.CENTRO_CONTABLE,
                    gc.CONCEPTO_COSTE,
                    SUM(gc.IMPORTE) as importe_fin
                FROM GASTOS_CENTRO gc
                WHERE gc.CENTRO_CONTABLE = ?
                    AND substr(gc.FECHA, 1, 7) = ?
                GROUP BY gc.CENTRO_CONTABLE, gc.CONCEPTO_COSTE
            )
            SELECT
                gi.CENTRO_CONTABLE,
                gi.DESC_CENTRO,
                gi.CONCEPTO_COSTE,
                gi.importe_ini,
                COALESCE(gf.importe_fin, 0) as importe_fin,
                ROUND(COALESCE(gf.importe_fin, 0) - gi.importe_ini, 2) as diferencia_absoluta,
                ROUND(
                    CASE WHEN gi.importe_ini = 0 THEN NULL
                         ELSE ((COALESCE(gf.importe_fin, 0) - gi.importe_ini) / gi.importe_ini) * 100 
                    END, 2
                ) as variacion_pct,
                ? as periodo_inicio,
                ? as periodo_final
            FROM gastos_ini gi
            LEFT JOIN gastos_fin gf ON gi.CENTRO_CONTABLE = gf.CENTRO_CONTABLE 
                AND gi.CONCEPTO_COSTE = gf.CONCEPTO_COSTE
            ORDER BY ABS(variacion_pct) DESC NULLS LAST
        """
        
        start_time = datetime.now()
        results = execute_query(query, (centro_contable, mes_ini, centro_contable, mes_fin, mes_ini, mes_fin))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="comparativa_gastos_centro",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def compare_margen_segmento_periodos(self, segmento_id: str, periodo_ini: str, periodo_fin: str) -> QueryResult:
        """
        Variación del margen neto de un segmento entre dos períodos.
        ✅ CORREGIDO: Usa códigos CDR reales de tu BD
        """
        query = """
            WITH margen_periodo AS (
                SELECT
                    g.SEGMENTO_ID,
                    s.DESC_SEGMENTO,
                    strftime('%Y-%m', mov.FECHA) as periodo,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos,
                    ROUND(
                        (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                  THEN mov.IMPORTE ELSE 0 END)
                        - SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0003', 'CR0014', 'CR0016', 'CR0017', 'CR0029') 
                                  THEN ABS(mov.IMPORTE) ELSE 0 END))
                        /
                        NULLIF(SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('CR0001', 'CR0008', 'CR0012') 
                                       THEN mov.IMPORTE ELSE 0 END), 0) * 100, 2
                    ) AS margen_neto
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                JOIN MAESTRO_GESTORES g ON cont.GESTOR_ID = g.GESTOR_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE g.SEGMENTO_ID = ?
                    AND strftime('%Y-%m', mov.FECHA) IN (?, ?)
                GROUP BY g.SEGMENTO_ID, s.DESC_SEGMENTO, strftime('%Y-%m', mov.FECHA)
            ),
            margen_inicial AS (
                SELECT * FROM margen_periodo WHERE periodo = ?
            ),
            margen_final AS (
                SELECT * FROM margen_periodo WHERE periodo = ?
            )
            SELECT
                COALESCE(mi.SEGMENTO_ID, mf.SEGMENTO_ID) as SEGMENTO_ID,
                COALESCE(mi.DESC_SEGMENTO, mf.DESC_SEGMENTO) as DESC_SEGMENTO,
                COALESCE(mi.ingresos, 0) as ingresos_inicial,
                COALESCE(mf.ingresos, 0) as ingresos_final,
                COALESCE(mi.gastos, 0) as gastos_inicial,
                COALESCE(mf.gastos, 0) as gastos_final,
                COALESCE(mi.margen_neto, 0) as margen_inicial,
                COALESCE(mf.margen_neto, 0) as margen_final,
                ROUND(COALESCE(mf.margen_neto, 0) - COALESCE(mi.margen_neto, 0), 2) as diferencia_margen,
                ROUND(
                    CASE WHEN COALESCE(mi.margen_neto, 0) = 0 THEN NULL
                         ELSE ((COALESCE(mf.margen_neto, 0) - COALESCE(mi.margen_neto, 0)) / mi.margen_neto) * 100 
                    END, 2
                ) as variacion_pct,
                ? as periodo_inicio,
                ? as periodo_final
            FROM margen_inicial mi
            FULL OUTER JOIN margen_final mf ON mi.SEGMENTO_ID = mf.SEGMENTO_ID
        """
        
        start_time = datetime.now()
        results = execute_query(query, (segmento_id, periodo_ini, periodo_fin, periodo_ini, periodo_fin, periodo_ini, periodo_fin))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="comparativa_margen_segmento",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # FUNCIONES HELPER PARA CLASIFICACIONES (SIN CAMBIOS)
    # =================================================================
    
    def _classify_gestor_performance(self, clasificacion_margen: str, clasificacion_eficiencia: str, 
                                   desviacion_vs_media: float) -> str:
        """
        Clasificación integral del gestor basada en múltiples KPIs
        FUNCIÓN ORIGINAL MANTENIDA SIN CAMBIOS
        """
        # Pesos para la clasificación integral
        score = 0
        
        # Puntuación por margen
        margen_scores = {
            'EXCELENTE': 4, 'BUENO': 3, 'ACEPTABLE': 2, 'BAJO': 1, 'PERDIDAS': 0
        }
        score += margen_scores.get(clasificacion_margen, 0) * 0.4
        
        # Puntuación por eficiencia
        eficiencia_scores = {
            'MUY_EFICIENTE': 4, 'EFICIENTE': 3, 'EQUILIBRADO': 2, 'INEFICIENTE': 1
        }
        score += eficiencia_scores.get(clasificacion_eficiencia, 0) * 0.3
        
        # Puntuación por desviación vs media
        if desviacion_vs_media > 5:
            score += 1.2  # 30% del total
        elif desviacion_vs_media > 0:
            score += 0.9
        elif desviacion_vs_media > -5:
            score += 0.6
        else:
            score += 0.3
        
        # Clasificación final
        if score >= 3.5:
            return 'HIGH_PERFORMER'
        elif score >= 2.5:
            return 'GOOD_PERFORMER'
        elif score >= 1.5:
            return 'AVERAGE_PERFORMER'
        else:
            return 'NEEDS_IMPROVEMENT'
    
    # =================================================================
    # 4. GENERADOR DINÁMICO DE QUERIES COMPARATIVAS (SIN CAMBIOS)
    # =================================================================
    
    def generate_dynamic_comparative_query(self, user_question: str, context: Dict[str, Any] = None) -> QueryResult:
        """
        Genera consultas comparativas SQL dinámicas usando GPT-4 para preguntas específicas.
        FUNCIÓN ORIGINAL MANTENIDA SIN CAMBIOS
        """
        from ..prompts.system_prompts import get_comparative_generation_prompt
        
        try:
            # Usar prompt especializado para comparativas
            system_prompt = get_comparative_generation_prompt(context)
            
            user_prompt = f"""
            Genera una consulta SQL comparativa para responder: "{user_question}"
            
            La consulta debe ser ejecutable directamente en SQLite y enfocarse en comparar entidades.
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
                    query_type="comparative_security_error",
                    execution_time=0,
                    row_count=0,
                    query_sql=generated_sql
                )
            
            logger.info(f"✅ Query comparativa dinámica generada para: {user_question}")
            
            # Ejecutar la query validada
            start_time = datetime.now()
            results = execute_query(generated_sql)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                data=results,
                query_type="dynamic_comparative_generated",
                execution_time=execution_time,
                row_count=len(results) if results else 0,
                query_sql=generated_sql
            )
            
        except Exception as e:
            logger.error(f"❌ Error generando query comparativa dinámica: {e}")
            return QueryResult(
                data=[{"error": f"No se pudo generar consulta comparativa para: {user_question}", "details": str(e)}],
                query_type="comparative_dynamic_error",
                execution_time=0,
                row_count=0,
                query_sql="-- Error en generación dinámica comparativa"
            )
    
    # =================================================================
    # 5. MOTOR DE SELECCIÓN INTELIGENTE PARA COMPARATIVAS (SIN CAMBIOS)
    # =================================================================
    
    def get_best_comparative_query_for_question(self, user_question: str, context: Dict[str, Any] = None) -> QueryResult:
        """
        Motor inteligente que decide qué query comparativa usar según la pregunta del usuario.
        FUNCIÓN ORIGINAL MANTENIDA CON FUNCIONES ENHANCED AÑADIDAS
        """
        from ..prompts.system_prompts import get_comparative_classification_prompt
        
        # Lista de queries predefinidas disponibles (AMPLIADA)
        available_queries = [
            "compare_precio_producto_real_mes",
            "compare_precio_real_vs_std",
            "compare_precio_real_vs_std_enhanced",
            "ranking_productos_desviacion_precio",
            "ranking_gestores_por_margen",
            "ranking_gestores_por_margen_enhanced",
            "compare_roe_gestores",
            "compare_roe_gestores_enhanced",
            "compare_eficiencia_centro",
            "compare_eficiencia_centro_enhanced",
            "compare_gastos_centro_periodo",
            "compare_margen_segmento_periodos"
        ]
        
        try:
            # FASE 1: Clasificación inteligente con GPT-4 especializada en comparativas
            classification_prompt = get_comparative_classification_prompt(available_queries)
            
            classification_response = iniciar_agente_llm(
                system_prompt=classification_prompt,
                user_prompt=f'Clasifica esta pregunta comparativa: "{user_question}"',
                temperature=0.0,
                max_tokens=50
            )
            
            predicted_query = classification_response.choices[0].message.content.strip()
            
            logger.info(f"🧠 Clasificación comparativa: '{user_question}' → {predicted_query}")
            
            # FASE 2: Ejecutar query predefinida si se identificó correctamente
            if predicted_query in available_queries:
                query_method = getattr(self, predicted_query)
                
                # Usar contexto si está disponible para parámetros
                if context and 'params' in context:
                    result = query_method(**context['params'])
                else:
                    # Parámetros por defecto usando datos CDG reales
                    if predicted_query in ["compare_precio_producto_real_mes"]:
                        result = query_method("600100300300", "N20301", "2025-09", "2025-10")
                    elif predicted_query in ["compare_precio_real_vs_std", "compare_precio_real_vs_std_enhanced"]:
                        result = query_method("600100300300", "N20301", "2025-10")
                    elif predicted_query in ["compare_gastos_centro_periodo"]:
                        result = query_method(1, "2025-09", "2025-10")
                    elif predicted_query in ["compare_margen_segmento_periodos"]:
                        result = query_method("N20301", "2025-09", "2025-10")
                    else:
                        result = query_method("2025-10")
                
                logger.info(f"✅ Query comparativa predefinida ejecutada exitosamente: {predicted_query}")
                return result
            
            # FASE 3: Usar generación dinámica si no se identificó query predefinida
            elif predicted_query == "DYNAMIC_QUERY":
                logger.info(f"🤖 Usando generación dinámica para pregunta comparativa compleja: {user_question}")
                return self.generate_dynamic_comparative_query(user_question, context)
            
            else:
                # FASE 4: Fallback por clasificación incorrecta
                logger.warning(f"⚠️ Clasificación comparativa no reconocida: {predicted_query}. Usando generación dinámica.")
                return self.generate_dynamic_comparative_query(user_question, context)
                
        except Exception as e:
            logger.error(f"❌ Error en motor de selección comparativo: {e}")
            
            # Fallback final: generación dinámica
            logger.info(f"🔄 Fallback: Usando generación dinámica por error en clasificación comparativa")
            return self.generate_dynamic_comparative_query(user_question, context)


# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA (MANTENIDAS)
# =================================================================

# Instancia global para uso en toda la aplicación
comparative_queries = ComparativeQueries()

# Funciones de conveniencia originales mantenidas
def compare_precios_producto(producto_id: str, segmento_id: str, mes_ini: str, mes_fin: str):
    """Función de conveniencia para comparar precios de producto"""
    return comparative_queries.compare_precio_producto_real_mes(producto_id, segmento_id, mes_ini, mes_fin)

def get_ranking_gestores_margen(periodo: str = "2025-10"):
    """Función de conveniencia para ranking de gestores por margen"""
    return comparative_queries.ranking_gestores_por_margen(periodo)

def compare_centros_eficiencia(periodo: str = "2025-10"):
    """Función de conveniencia para comparar eficiencia entre centros"""
    return comparative_queries.compare_eficiencia_centro(periodo)

def ask_comparative_question(question: str, context: Dict[str, Any] = None):
    """
    Función de conveniencia para hacer cualquier pregunta comparativa
    """
    return comparative_queries.get_best_comparative_query_for_question(question, context)

# ✅ NUEVAS funciones de conveniencia para versiones enhanced
def get_ranking_gestores_margen_enhanced(periodo: str = "2025-10"):
    """Función de conveniencia para ranking mejorado de gestores por margen"""
    return comparative_queries.ranking_gestores_por_margen_enhanced(periodo)

def compare_roe_gestores_enhanced(periodo: str = "2025-10"):
    """Función de conveniencia para comparación ROE mejorada"""
    return comparative_queries.compare_roe_gestores_enhanced(periodo)

def compare_centros_eficiencia_enhanced(periodo: str = "2025-10"):
    """Función de conveniencia para comparación eficiencia centros mejorada"""
    return comparative_queries.compare_eficiencia_centro_enhanced(periodo)

def compare_precio_std_enhanced(producto_id: str, segmento_id: str, periodo: str):
    """Función de conveniencia para comparación precio estándar vs real mejorada"""
    return comparative_queries.compare_precio_real_vs_std_enhanced(producto_id, segmento_id, periodo)
