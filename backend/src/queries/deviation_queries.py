"""
deviation_queries.py

Consultas para detección de desviaciones y anomalías financieras en Banca March.
Incluye alertas sobre desviaciones de precio, margen, volumen y patrones anómalos.
INTEGRADO con kpi_calculator.py para análisis de desviaciones estandarizados y clasificaciones automáticas.
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

class DeviationQueries:
    """
    Biblioteca completa de consultas para detección de desviaciones y anomalías
    
    COBERTURA MEJORADA:
    - Desviaciones de precios: real vs estándar con análisis KPI mejorado
    - Anomalías de margen: comportamiento atípico con clasificaciones automáticas
    - Outliers de volumen: actividad anómala con interpretaciones contextuales
    - Patrones temporales: tendencias irregulares con análisis estadístico
    - Queries dinámicas: generación automática con validación
    """
    
    def __init__(self):
        self.query_cache = {}
        self.deviation_threshold = 15.0  # Umbral crítico por defecto
        self.anomaly_z_score = 2.0       # Puntuación Z para outliers
        self.kpi_calc = kpi_calculator   # ✅ INSTANCIA KPI_CALCULATOR
    
    # =================================================================
    # 1. DETECCIÓN DE DESVIACIONES DE PRECIOS (MEJORADAS)
    # =================================================================
    
    def detect_precio_desviaciones_criticas_enhanced(self, periodo: str = "2025-10", threshold: float = 15.0) -> QueryResult:
        """
        Detecta desviaciones críticas entre precio real y estándar con análisis KPI mejorado.
        
        CASO DE USO: "¿Qué productos tienen precios muy desviados del estándar?"
        MEJORAS: Usa kpi_calculator para análisis de desviaciones con acciones recomendadas
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
            JOIN PRECIO_POR_PRODUCTO_STD ps ON pr.PRODUCTO_ID = ps.PRODUCTO_ID 
                AND pr.SEGMENTO_ID = ps.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS mp ON pr.PRODUCTO_ID = mp.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS ms ON pr.SEGMENTO_ID = ms.SEGMENTO_ID
            WHERE substr(pr.FECHA_CALCULO, 1, 7) = ?
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
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
            
            # Solo incluir si supera el umbral
            if abs(desviacion_analysis['desviacion_pct']) >= threshold:
                # Combinar datos originales con análisis KPI
                enhanced_row = {
                    **row,
                    'desviacion_pct': desviacion_analysis['desviacion_pct'],
                    'desviacion_absoluta': desviacion_analysis['desviacion_absoluta'],
                    'desviacion_abs_pct': abs(desviacion_analysis['desviacion_pct']),
                    'nivel_alerta': desviacion_analysis['nivel_alerta'],  # CRITICA, ALTA, MEDIA, NORMAL
                    'accion_recomendada': desviacion_analysis['accion_recomendada'],
                    'tipo_desviacion': desviacion_analysis['tipo_desviacion'],  # POSITIVA/NEGATIVA
                    
                    # ✅ CLASIFICACIÓN MEJORADA BASADA EN SEVERIDAD
                    'nivel_severidad': self._classify_deviation_severity(abs(desviacion_analysis['desviacion_pct'])),
                    'analisis_kpi_completo': desviacion_analysis  # Para drill-down
                }
                enhanced_results.append(enhanced_row)
        
        # Ordenar por desviación absoluta
        enhanced_results.sort(key=lambda x: x['desviacion_abs_pct'], reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="precio_desviaciones_criticas_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def detect_precio_desviaciones_criticas(self, periodo: str = "2025-10", threshold: float = 15.0) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
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
                    ABS((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                    NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100), 2
                ) as desviacion_abs_pct,
                ROUND(
                    (pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                    NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100, 2
                ) as desviacion_pct,
                CASE 
                    WHEN ABS((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                         NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100) >= 25.0 THEN 'CRITICA'
                    WHEN ABS((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                         NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100) >= 15.0 THEN 'ALTA'
                    ELSE 'MEDIA'
                END as nivel_severidad,
                CASE 
                    WHEN pr.PRECIO_MANTENIMIENTO_REAL > ps.PRECIO_MANTENIMIENTO THEN 'SOBRECOSTO'
                    ELSE 'EFICIENCIA'
                END as tipo_desviacion,
                pr.FECHA_CALCULO,
                pr.NUM_CONTRATOS_BASE
            FROM PRECIO_POR_PRODUCTO_REAL pr
            JOIN PRECIO_POR_PRODUCTO_STD ps ON pr.PRODUCTO_ID = ps.PRODUCTO_ID 
                AND pr.SEGMENTO_ID = ps.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS mp ON pr.PRODUCTO_ID = mp.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS ms ON pr.SEGMENTO_ID = ms.SEGMENTO_ID
            WHERE substr(pr.FECHA_CALCULO, 1, 7) = ?
                AND ABS((pr.PRECIO_MANTENIMIENTO_REAL - ps.PRECIO_MANTENIMIENTO) /
                    NULLIF(ps.PRECIO_MANTENIMIENTO, 0) * 100) >= ?
            ORDER BY desviacion_abs_pct DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, threshold))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="precio_desviaciones_criticas",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def analyze_precio_trend_anomalies(self, producto_id: str, segmento_id: str, num_periods: int = 3) -> QueryResult:
        """
        Analiza anomalías en la tendencia de precios reales a lo largo del tiempo.
        FUNCIÓN ORIGINAL MANTENIDA
        """
        query = """
            WITH precio_historico AS (
                SELECT 
                    PRODUCTO_ID,
                    SEGMENTO_ID,
                    FECHA_CALCULO,
                    PRECIO_MANTENIMIENTO_REAL,
                    LAG(PRECIO_MANTENIMIENTO_REAL, 1) OVER (
                        PARTITION BY PRODUCTO_ID, SEGMENTO_ID 
                        ORDER BY FECHA_CALCULO
                    ) as precio_anterior,
                    ROW_NUMBER() OVER (
                        PARTITION BY PRODUCTO_ID, SEGMENTO_ID 
                        ORDER BY FECHA_CALCULO DESC
                    ) as rn
                FROM PRECIO_POR_PRODUCTO_REAL
                WHERE PRODUCTO_ID = ? AND SEGMENTO_ID = ?
            ),
            variaciones AS (
                SELECT 
                    *,
                    CASE 
                        WHEN precio_anterior IS NOT NULL AND precio_anterior != 0 
                        THEN ROUND(((PRECIO_MANTENIMIENTO_REAL - precio_anterior) / 
                             ABS(precio_anterior)) * 100, 2)
                        ELSE 0
                    END as variacion_pct
                FROM precio_historico
                WHERE rn <= ?
            )
            SELECT 
                PRODUCTO_ID,
                SEGMENTO_ID,
                FECHA_CALCULO,
                PRECIO_MANTENIMIENTO_REAL,
                precio_anterior,
                variacion_pct,
                CASE 
                    WHEN ABS(variacion_pct) >= 20.0 THEN 'ANOMALIA'
                    WHEN ABS(variacion_pct) >= 10.0 THEN 'ALERTA'
                    ELSE 'NORMAL'
                END as evaluacion_tendencia
            FROM variaciones
            ORDER BY FECHA_CALCULO DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (producto_id, segmento_id, num_periods))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="precio_trend_anomalies",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 2. DETECCIÓN DE ANOMALÍAS DE MARGEN (MEJORADAS CON KPI)
    # =================================================================
    
    def analyze_margen_anomalies_enhanced(self, periodo: str = "2025-10", z_threshold: float = 2.0) -> QueryResult:
        """
        Detecta gestores con márgenes anómalos usando análisis estadístico mejorado con KPI.
        
        CASO DE USO: "¿Hay gestores con rendimiento muy por debajo de lo normal?"
        MEJORAS: Usa kpi_calculator para clasificaciones automáticas y análisis contextual
        """
        # Query simplificada - solo extrae datos base
        query = """
            WITH gestor_data AS (
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
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', COALESCE(mov.FECHA, mc.FECHA_ALTA)) <= ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING ingresos_total > 0
            )
            SELECT * FROM gestor_data
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo,))
        
        # ✅ PROCESAMIENTO AVANZADO CON KPI_CALCULATOR
        enhanced_results = []
        margenes_para_estadisticas = []
        
        # Primera pasada: calcular todos los márgenes y estadísticas
        for row in raw_results:
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            margenes_para_estadisticas.append(margen_analysis['margen_neto_pct'])
        
        # Calcular estadísticas para Z-score
        if margenes_para_estadisticas:
            media_margen = sum(margenes_para_estadisticas) / len(margenes_para_estadisticas)
            varianza = sum((x - media_margen) ** 2 for x in margenes_para_estadisticas) / len(margenes_para_estadisticas)
            desv_estandar = varianza ** 0.5 if varianza > 0 else 0
        else:
            media_margen = desv_estandar = 0
        
        # Segunda pasada: generar resultados con análisis de anomalías
        for row in raw_results:
            # Análisis de margen con kpi_calculator
            margen_analysis = self.kpi_calc.calculate_margen_neto(
                ingresos=row['ingresos_total'],
                gastos=row['gastos_total']
            )
            
            # Cálculo Z-score
            z_score = 0
            if desv_estandar > 0:
                z_score = (margen_analysis['margen_neto_pct'] - media_margen) / desv_estandar
            
            # Solo incluir si es anomalía (supera threshold Z-score)
            if abs(z_score) >= z_threshold:
                enhanced_row = {
                    **row,
                    'margen_neto': margen_analysis['margen_neto_pct'],
                    'beneficio_neto': margen_analysis['beneficio_neto'],
                    'clasificacion_margen': margen_analysis['clasificacion'],  # EXCELENTE, BUENO, etc.
                    'media_margen': round(media_margen, 2),
                    'desv_estandar': round(desv_estandar, 2),
                    'z_score': round(z_score, 2),
                    
                    # ✅ CLASIFICACIÓN AUTOMÁTICA DE ANOMALÍAS
                    'clasificacion_anomalia': self._classify_anomaly_by_zscore(abs(z_score)),
                    'tipo_anomalia': 'PERFORMANCE_SUPERIOR' if z_score > 0 else 'PERFORMANCE_INFERIOR',
                    
                    # Análisis completo para drill-down
                    'analisis_margen_completo': margen_analysis
                }
                enhanced_results.append(enhanced_row)
        
        # Ordenar por Z-score absoluto (anomalías más extremas primero)
        enhanced_results.sort(key=lambda x: abs(x['z_score']), reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="margen_anomalies_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def analyze_margen_anomalies(self, periodo: str = "2025-10", z_threshold: float = 2.0) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
        """
        query = """
            WITH gestor_margenes AS (
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
                        CASE 
                            WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                           THEN mov.IMPORTE ELSE 0 END) > 0
                            THEN (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                          THEN mov.IMPORTE ELSE 0 END) - 
                                  SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                           THEN ABS(mov.IMPORTE) ELSE 0 END)) /
                                 SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                          THEN mov.IMPORTE ELSE 0 END) * 100
                            ELSE NULL
                        END, 2
                    ) as margen_neto
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', COALESCE(mov.FECHA, mc.FECHA_ALTA)) <= ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING margen_neto IS NOT NULL
            ),
            estadisticas AS (
                SELECT 
                    AVG(margen_neto) as media_margen,
                    CASE 
                        WHEN COUNT(*) > 1 
                        THEN SQRT(SUM(margen_neto * margen_neto) / COUNT(*) - 
                             (AVG(margen_neto) * AVG(margen_neto)))
                        ELSE 0 
                    END as desv_estandar
                FROM gestor_margenes
            )
            SELECT 
                gm.GESTOR_ID,
                gm.DESC_GESTOR,
                gm.DESC_CENTRO,
                gm.DESC_SEGMENTO,
                gm.margen_neto,
                est.media_margen,
                est.desv_estandar,
                ROUND(
                    CASE 
                        WHEN est.desv_estandar > 0 
                        THEN (gm.margen_neto - est.media_margen) / est.desv_estandar
                        ELSE 0 
                    END, 2
                ) as z_score,
                CASE 
                    WHEN ABS((gm.margen_neto - est.media_margen) / NULLIF(est.desv_estandar, 0)) >= 3.0 THEN 'OUTLIER_EXTREMO'
                    WHEN ABS((gm.margen_neto - est.media_margen) / NULLIF(est.desv_estandar, 0)) >= 2.0 THEN 'OUTLIER_MODERADO'
                    WHEN ABS((gm.margen_neto - est.media_margen) / NULLIF(est.desv_estandar, 0)) >= 1.5 THEN 'ATIPICO'
                    ELSE 'NORMAL'
                END as clasificacion_anomalia,
                gm.ingresos_total,
                gm.gastos_total
            FROM gestor_margenes gm
            CROSS JOIN estadisticas est
            WHERE est.desv_estandar > 0 
                AND ABS((gm.margen_neto - est.media_margen) / est.desv_estandar) >= ?
            ORDER BY ABS(z_score) DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, z_threshold))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="margen_anomalies",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 3. DETECCIÓN DE OUTLIERS DE VOLUMEN (MEJORADA)
    # =================================================================
    
    def identify_volumen_outliers_enhanced(self, periodo: str = "2025-10", factor_outlier: float = 3.0) -> QueryResult:
        """
        Identifica gestores con volumen de contratos o actividad atípica con análisis contextual.
        
        CASO DE USO: "¿Hay gestores con actividad comercial inusual?"
        MEJORAS: Análisis de eficiencia mejorado con interpretaciones contextuales
        """
        # Query base para datos de actividad
        query = """
            WITH actividad_gestores AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                    COUNT(DISTINCT CASE WHEN strftime('%Y-%m', mc.FECHA_ALTA) = ? 
                                       THEN mc.CONTRATO_ID ELSE NULL END) as contratos_nuevos_periodo,
                    COALESCE(COUNT(DISTINCT mov.MOVIMIENTO_ID), 0) as total_movimientos,
                    COALESCE(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_generados
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
            )
            SELECT * FROM actividad_gestores
        """
        
        start_time = datetime.now()
        raw_results = execute_query(query, (periodo, periodo))
        
        # ✅ PROCESAMIENTO CON KPI_CALCULATOR
        enhanced_results = []
        
        # Calcular medias para comparación
        if raw_results:
            media_contratos = sum(row['total_contratos'] for row in raw_results) / len(raw_results)
            media_nuevos = sum(row['contratos_nuevos_periodo'] for row in raw_results) / len(raw_results)
            media_movimientos = sum(row['total_movimientos'] for row in raw_results) / len(raw_results)
            media_ingresos = sum(row['ingresos_generados'] for row in raw_results) / len(raw_results)
        else:
            media_contratos = media_nuevos = media_movimientos = media_ingresos = 0
        
        for row in raw_results:
            # Calcular ratios vs media
            ratio_contratos = row['total_contratos'] / media_contratos if media_contratos > 0 else 0
            ratio_nuevos = row['contratos_nuevos_periodo'] / media_nuevos if media_nuevos > 0 else 0
            
            # Determinar si es outlier
            is_outlier = (
                row['total_contratos'] >= media_contratos * factor_outlier or
                row['total_contratos'] <= media_contratos / factor_outlier or
                row['contratos_nuevos_periodo'] >= media_nuevos * factor_outlier or
                (row['contratos_nuevos_periodo'] == 0 and media_nuevos > 0)
            )
            
            if is_outlier:
                # ✅ ANÁLISIS DE EFICIENCIA CON KPI_CALCULATOR
                eficiencia_analysis = self.kpi_calc.calculate_ratio_eficiencia(
                    ingresos=row['ingresos_generados'],
                    gastos=row['total_contratos'] * 100  # Asumiendo costo promedio por contrato
                )
                
                enhanced_row = {
                    **row,
                    'media_contratos': round(media_contratos, 1),
                    'media_nuevos': round(media_nuevos, 1),
                    'media_movimientos': round(media_movimientos, 1),
                    'media_ingresos': round(media_ingresos, 2),
                    'ratio_contratos_vs_media': round(ratio_contratos, 2),
                    'ratio_nuevos_vs_media': round(ratio_nuevos, 2),
                    
                    # ✅ CLASIFICACIÓN MEJORADA DE OUTLIERS
                    'tipo_outlier': self._classify_volume_outlier(
                        row['total_contratos'], media_contratos,
                        row['contratos_nuevos_periodo'], media_nuevos,
                        factor_outlier
                    ),
                    
                    # Análisis de eficiencia
                    'ratio_eficiencia': eficiencia_analysis['ratio_eficiencia'],
                    'clasificacion_eficiencia': eficiencia_analysis['clasificacion'],
                    'interpretacion_eficiencia': eficiencia_analysis['interpretacion'],
                    
                    # Análisis completo
                    'analisis_eficiencia_completo': eficiencia_analysis
                }
                enhanced_results.append(enhanced_row)
        
        # Ordenar por desviación de la media
        enhanced_results.sort(key=lambda x: abs(x['total_contratos'] - x['media_contratos']), reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=enhanced_results,
            query_type="volumen_outliers_enhanced",
            execution_time=execution_time,
            row_count=len(enhanced_results),
            query_sql=query
        )
    
    def identify_volumen_outliers(self, periodo: str = "2025-10", factor_outlier: float = 3.0) -> QueryResult:
        """
        FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
        """
        query = """
            WITH actividad_gestores AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                    COUNT(DISTINCT CASE WHEN strftime('%Y-%m', mc.FECHA_ALTA) = ? 
                                       THEN mc.CONTRATO_ID ELSE NULL END) as contratos_nuevos_periodo,
                    COALESCE(COUNT(DISTINCT mov.MOVIMIENTO_ID), 0) as total_movimientos,
                    COALESCE(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) as ingresos_generados
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                WHERE c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
            ),
            medias AS (
                SELECT 
                    AVG(total_contratos) as media_contratos,
                    AVG(contratos_nuevos_periodo) as media_nuevos,
                    AVG(total_movimientos) as media_movimientos,
                    AVG(ingresos_generados) as media_ingresos
                FROM actividad_gestores
            )
            SELECT 
                ag.GESTOR_ID,
                ag.DESC_GESTOR,
                ag.DESC_CENTRO,
                ag.DESC_SEGMENTO,
                ag.total_contratos,
                ag.contratos_nuevos_periodo,
                ag.total_movimientos,
                ag.ingresos_generados,
                ROUND(m.media_contratos, 1) as media_contratos,
                ROUND(m.media_nuevos, 1) as media_nuevos,
                ROUND(m.media_movimientos, 1) as media_movimientos,
                ROUND(m.media_ingresos, 2) as media_ingresos,
                ROUND(ag.total_contratos / NULLIF(m.media_contratos, 0), 2) as ratio_contratos_vs_media,
                ROUND(ag.contratos_nuevos_periodo / NULLIF(m.media_nuevos, 0), 2) as ratio_nuevos_vs_media,
                CASE 
                    WHEN ag.total_contratos >= m.media_contratos * ? THEN 'HIPERACTIVIDAD'
                    WHEN ag.total_contratos <= m.media_contratos / ? THEN 'BAJA_ACTIVIDAD'
                    WHEN ag.contratos_nuevos_periodo >= m.media_nuevos * ? THEN 'PICO_COMERCIAL'
                    WHEN ag.contratos_nuevos_periodo = 0 AND m.media_nuevos > 0 THEN 'SIN_ACTIVIDAD'
                    ELSE 'NORMAL'
                END as tipo_outlier
            FROM actividad_gestores ag
            CROSS JOIN medias m
            WHERE (ag.total_contratos >= m.media_contratos * ? OR 
                   ag.total_contratos <= m.media_contratos / ? OR
                   ag.contratos_nuevos_periodo >= m.media_nuevos * ? OR
                   (ag.contratos_nuevos_periodo = 0 AND m.media_nuevos > 0))
            ORDER BY ABS(ag.total_contratos - m.media_contratos) DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, periodo, factor_outlier, factor_outlier, factor_outlier, factor_outlier, factor_outlier, factor_outlier))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="volumen_outliers",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 4. DETECCIÓN DE PATRONES TEMPORALES (MANTENER ORIGINAL)
    # =================================================================
    
    def detect_patron_temporal_anomalias(self, gestor_id: str = None, num_periods: int = 6) -> QueryResult:
        """
        Detecta patrones temporales anómalos en la evolución de KPIs.
        FUNCIÓN ORIGINAL MANTENIDA
        """
        where_clause = "WHERE g.GESTOR_ID = ?" if gestor_id else "WHERE c.IND_CENTRO_FINALISTA = 1"
        params = (gestor_id, num_periods) if gestor_id else (num_periods,)
        
        query = f"""
            WITH evolucion_mensual AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    strftime('%Y-%m', mov.FECHA) as periodo,
                    SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END) as ingresos_mes,
                    COUNT(DISTINCT mov.CONTRATO_ID) as contratos_activos,
                    COUNT(DISTINCT mov.MOVIMIENTO_ID) as num_transacciones
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                {where_clause}
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, strftime('%Y-%m', mov.FECHA)
                HAVING periodo IS NOT NULL
                ORDER BY g.GESTOR_ID, periodo DESC
            ),
            ventana_temporal AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (PARTITION BY GESTOR_ID ORDER BY periodo DESC) as rn,
                    LAG(ingresos_mes, 1) OVER (PARTITION BY GESTOR_ID ORDER BY periodo) as ingresos_anterior,
                    LAG(contratos_activos, 1) OVER (PARTITION BY GESTOR_ID ORDER BY periodo) as contratos_anterior
                FROM evolucion_mensual
            ),
            variaciones AS (
                SELECT 
                    *,
                    CASE 
                        WHEN ingresos_anterior > 0 
                        THEN ROUND(((ingresos_mes - ingresos_anterior) / ingresos_anterior) * 100, 2)
                        ELSE 0 
                    END as variacion_ingresos_pct,
                    CASE 
                        WHEN contratos_anterior > 0 
                        THEN ROUND(((contratos_activos - contratos_anterior) / CAST(contratos_anterior AS FLOAT)) * 100, 2)
                        ELSE 0 
                    END as variacion_contratos_pct
                FROM ventana_temporal
                WHERE rn <= ?
            )
            SELECT 
                GESTOR_ID,
                DESC_GESTOR,
                periodo,
                ingresos_mes,
                contratos_activos,
                num_transacciones,
                variacion_ingresos_pct,
                variacion_contratos_pct,
                CASE 
                    WHEN ABS(variacion_ingresos_pct) >= 50.0 THEN 'VOLATILIDAD_EXTREMA'
                    WHEN ABS(variacion_ingresos_pct) >= 25.0 THEN 'ALTA_VOLATILIDAD'
                    WHEN ABS(variacion_contratos_pct) >= 30.0 THEN 'CAMBIO_ESTRUCTURAL'
                    WHEN variacion_ingresos_pct = 0 AND variacion_contratos_pct = 0 THEN 'ESTANCAMIENTO'
                    ELSE 'NORMAL'
                END as patron_anomalia
            FROM variaciones
            WHERE patron_anomalia != 'NORMAL'
            ORDER BY GESTOR_ID, periodo DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, params)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="patron_temporal_anomalias",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 5. ANÁLISIS CRUZADO DE DESVIACIONES (MANTENER ORIGINAL)
    # =================================================================
    
    def analyze_cross_producto_desviaciones(self, periodo: str = "2025-10") -> QueryResult:
        """
        Analiza correlaciones extrañas entre desviaciones de diferentes productos.
        FUNCIÓN ORIGINAL MANTENIDA
        """
        query = """
            WITH producto_gestor_performance AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    mc.PRODUCTO_ID,
                    mp.DESC_PRODUCTO,
                    COUNT(DISTINCT mc.CONTRATO_ID) as num_contratos,
                    COALESCE(SUM(mov.IMPORTE), 0) as volumen_total,
                    AVG(ABS(pr.PRECIO_MANTENIMIENTO_REAL)) as precio_real_promedio
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                JOIN MAESTRO_PRODUCTOS mp ON mc.PRODUCTO_ID = mp.PRODUCTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                LEFT JOIN PRECIO_POR_PRODUCTO_REAL pr ON mc.PRODUCTO_ID = pr.PRODUCTO_ID 
                    AND g.SEGMENTO_ID = pr.SEGMENTO_ID
                    AND substr(pr.FECHA_CALCULO, 1, 7) = ?
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, mc.PRODUCTO_ID, mp.DESC_PRODUCTO
            ),
            gestor_diversificacion AS (
                SELECT 
                    GESTOR_ID,
                    DESC_GESTOR,
                    COUNT(DISTINCT PRODUCTO_ID) as productos_diferentes,
                    SUM(num_contratos) as total_contratos,
                    SUM(volumen_total) as volumen_total_gestor,
                    MAX(num_contratos) as max_contratos_producto,
                    MIN(num_contratos) as min_contratos_producto,
                    AVG(num_contratos) as promedio_contratos_producto
                FROM producto_gestor_performance
                GROUP BY GESTOR_ID, DESC_GESTOR
            )
            SELECT 
                gd.GESTOR_ID,
                gd.DESC_GESTOR,
                gd.productos_diferentes,
                gd.total_contratos,
                gd.max_contratos_producto,
                gd.min_contratos_producto,
                ROUND(gd.promedio_contratos_producto, 1) as promedio_contratos,
                ROUND((gd.max_contratos_producto - gd.min_contratos_producto) / 
                      NULLIF(gd.promedio_contratos_producto, 0) * 100, 2) as coef_variacion_pct,
                CASE 
                    WHEN gd.productos_diferentes = 1 THEN 'ESPECIALIZACION_EXTREMA'
                    WHEN gd.max_contratos_producto >= gd.promedio_contratos_producto * 3 THEN 'CONCENTRACION_ALTA'
                    WHEN gd.min_contratos_producto = 0 AND gd.productos_diferentes > 1 THEN 'ABANDONO_PRODUCTO'
                    WHEN (gd.max_contratos_producto - gd.min_contratos_producto) / 
                         NULLIF(gd.promedio_contratos_producto, 0) >= 2.0 THEN 'DESEQUILIBRIO_SEVERO'
                    ELSE 'NORMAL'
                END as patron_cross_producto
            FROM gestor_diversificacion gd
            WHERE patron_cross_producto != 'NORMAL'
            ORDER BY coef_variacion_pct DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo, periodo))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="cross_producto_desviaciones",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # FUNCIONES HELPER PARA CLASIFICACIONES MEJORADAS
    # =================================================================
    
    def _classify_deviation_severity(self, desviacion_abs_pct: float) -> str:
        """Clasificación de severidad de desviaciones basada en umbrales CDG"""
        if desviacion_abs_pct >= 25.0:
            return 'CRITICA'
        elif desviacion_abs_pct >= 15.0:
            return 'ALTA'
        elif desviacion_abs_pct >= 8.0:
            return 'MEDIA'
        else:
            return 'BAJA'
    
    def _classify_anomaly_by_zscore(self, z_score_abs: float) -> str:
        """Clasificación de anomalías basada en Z-score"""
        if z_score_abs >= 3.0:
            return 'OUTLIER_EXTREMO'
        elif z_score_abs >= 2.0:
            return 'OUTLIER_MODERADO'
        elif z_score_abs >= 1.5:
            return 'ATIPICO'
        else:
            return 'NORMAL'
    
    def _classify_volume_outlier(self, contratos: int, media_contratos: float, 
                                contratos_nuevos: int, media_nuevos: float, 
                                factor: float) -> str:
        """Clasificación de outliers de volumen"""
        if contratos >= media_contratos * factor:
            return 'HIPERACTIVIDAD'
        elif contratos <= media_contratos / factor:
            return 'BAJA_ACTIVIDAD'
        elif contratos_nuevos >= media_nuevos * factor:
            return 'PICO_COMERCIAL'
        elif contratos_nuevos == 0 and media_nuevos > 0:
            return 'SIN_ACTIVIDAD'
        else:
            return 'NORMAL'
    
    # =================================================================
    # 6. GENERADOR DINÁMICO DE QUERIES DE DESVIACIONES (MANTENER)
    # =================================================================
    
    def generate_dynamic_deviation_query(self, user_question: str, context: Dict[str, Any] = None) -> QueryResult:
        """
        Genera consultas de desviaciones SQL dinámicas usando GPT-4 para preguntas específicas.
        FUNCIÓN ORIGINAL MANTENIDA
        """
        from ..prompts.system_prompts import get_deviation_generation_prompt
        
        try:
            # Usar prompt especializado para desviaciones
            system_prompt = get_deviation_generation_prompt(context)
            
            user_prompt = f"""
            Genera una consulta SQL para detectar desviaciones/anomalías para responder: "{user_question}"
            
            La consulta debe enfocarse en identificar comportamientos anómalos, outliers o patrones irregulares.
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
                generated_sql = generated_sql.split("```")[0].strip()
            
            # Validar la consulta antes de ejecutarla
            if not is_query_safe(generated_sql):
                logger.error(f"❌ Consulta SQL bloqueada por seguridad: {generated_sql}")
                return QueryResult(
                    data=[{"error": "Consulta SQL bloqueada por contener instrucciones no autorizadas"}],
                    query_type="deviation_security_error",
                    execution_time=0,
                    row_count=0,
                    query_sql=generated_sql
                )
            
            logger.info(f"✅ Query de desviaciones dinámica generada para: {user_question}")
            
            # Ejecutar la query validada
            start_time = datetime.now()
            results = execute_query(generated_sql)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                data=results,
                query_type="dynamic_deviation_generated",
                execution_time=execution_time,
                row_count=len(results) if results else 0,
                query_sql=generated_sql
            )
            
        except Exception as e:
            logger.error(f"❌ Error generando query de desviaciones dinámica: {e}")
            return QueryResult(
                data=[{"error": f"No se pudo generar consulta de desviaciones para: {user_question}", "details": str(e)}],
                query_type="deviation_dynamic_error",
                execution_time=0,
                row_count=0,
                query_sql="-- Error en generación dinámica de desviaciones"
            )
    
    # =================================================================
    # 7. MOTOR DE SELECCIÓN INTELIGENTE PARA DESVIACIONES (AMPLIADO)
    # =================================================================
    
    def get_best_deviation_query_for_question(self, user_question: str, context: Dict[str, Any] = None) -> QueryResult:
        """
        Motor inteligente que decide qué query de desviaciones usar según la pregunta del usuario.
        FUNCIÓN AMPLIADA CON VERSIONES ENHANCED
        """
        from ..prompts.system_prompts import get_deviation_classification_prompt
        
        # Lista de queries predefinidas disponibles (AMPLIADA)
        available_queries = [
            "detect_precio_desviaciones_criticas",
            "detect_precio_desviaciones_criticas_enhanced",  # ✅ NUEVA
            "analyze_precio_trend_anomalies",
            "analyze_margen_anomalies",
            "analyze_margen_anomalies_enhanced",  # ✅ NUEVA
            "identify_volumen_outliers",
            "identify_volumen_outliers_enhanced",  # ✅ NUEVA
            "detect_patron_temporal_anomalias",
            "analyze_cross_producto_desviaciones"
        ]
        
        try:
            # FASE 1: Clasificación inteligente con GPT-4 especializada en desviaciones
            classification_prompt = get_deviation_classification_prompt(available_queries)
            
            classification_response = iniciar_agente_llm(
                system_prompt=classification_prompt,
                user_prompt=f'Clasifica esta pregunta de desviaciones: "{user_question}"',
                temperature=0.0,
                max_tokens=50
            )
            
            predicted_query = classification_response.choices[0].message.content.strip()
            
            logger.info(f"🧠 Clasificación de desviaciones: '{user_question}' → {predicted_query}")
            
            # FASE 2: Ejecutar query predefinida si se identificó correctamente
            if predicted_query in available_queries:
                query_method = getattr(self, predicted_query)
                
                # Usar contexto si está disponible para parámetros
                if context and 'params' in context:
                    result = query_method(**context['params'])
                else:
                    # Parámetros por defecto para testing
                    if predicted_query in ["analyze_precio_trend_anomalies"]:
                        result = query_method("600100300300", "N20301")  # Fondo Banca March
                    elif predicted_query in ["detect_patron_temporal_anomalias"]:
                        result = query_method(gestor_id=None)  # Todos los gestores
                    elif predicted_query in ["identify_volumen_outliers", "identify_volumen_outliers_enhanced"]:
                        result = query_method("2025-10", 3.0)
                    else:
                        result = query_method("2025-10")
                
                logger.info(f"✅ Query de desviaciones predefinida ejecutada exitosamente: {predicted_query}")
                return result
            
            # FASE 3: Usar generación dinámica si no se identificó query predefinida
            elif predicted_query == "DYNAMIC_QUERY":
                logger.info(f"🤖 Usando generación dinámica para pregunta de desviaciones compleja: {user_question}")
                return self.generate_dynamic_deviation_query(user_question, context)
            
            else:
                # FASE 4: Fallback por clasificación incorrecta
                logger.warning(f"⚠️ Clasificación de desviaciones no reconocida: {predicted_query}. Usando generación dinámica.")
                return self.generate_dynamic_deviation_query(user_question, context)
                
        except Exception as e:
            logger.error(f"❌ Error en motor de selección de desviaciones: {e}")
            
            # Fallback final: generación dinámica
            logger.info(f"🔄 Fallback: Usando generación dinámica por error en clasificación de desviaciones")
            return self.generate_dynamic_deviation_query(user_question, context)

# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# =================================================================

# Instancia global para uso en toda la aplicación
deviation_queries = DeviationQueries()

# Funciones de conveniencia originales mantenidas
def detect_precio_desviaciones(periodo: str = "2025-10", threshold: float = 15.0):
    """Función de conveniencia para detectar desviaciones críticas de precio"""
    return deviation_queries.detect_precio_desviaciones_criticas(periodo, threshold)

def analyze_margen_anomalies(periodo: str = "2025-10"):
    """Función de conveniencia para análisis de anomalías de margen"""
    return deviation_queries.analyze_margen_anomalies(periodo)

def identify_outliers_actividad(periodo: str = "2025-10"):
    """Función de conveniencia para identificar outliers de actividad"""
    return deviation_queries.identify_volumen_outliers(periodo)

def ask_deviation_question(question: str, context: Dict[str, Any] = None):
    """
    Función de conveniencia para hacer cualquier pregunta sobre desviaciones
    """
    return deviation_queries.get_best_deviation_query_for_question(question, context)

# ✅ NUEVAS funciones de conveniencia para versiones enhanced
def detect_precio_desviaciones_enhanced(periodo: str = "2025-10", threshold: float = 15.0):
    """Función de conveniencia para detección mejorada de desviaciones de precio"""
    return deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, threshold)

def analyze_margen_anomalies_enhanced(periodo: str = "2025-10", z_threshold: float = 2.0):
    """Función de conveniencia para análisis mejorado de anomalías de margen"""
    return deviation_queries.analyze_margen_anomalies_enhanced(periodo, z_threshold)

def identify_outliers_enhanced(periodo: str = "2025-10", factor_outlier: float = 3.0):
    """Función de conveniencia para identificación mejorada de outliers de volumen"""
    return deviation_queries.identify_volumen_outliers_enhanced(periodo, factor_outlier)
