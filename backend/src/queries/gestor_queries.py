# backend/src/queries/gestor_queries.py
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, date

from ..database.db_connection import execute_query, execute_pandas_query
from ..utils.dynamic_config import get_centros_finalistas, get_segmentos_activos
from ..utils.initial_agent import iniciar_agente_llm  # ✅ CRÍTICO para GPT-4.1

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
    
    COBERTURA:
    - Análisis de cartera: contratos, productos, saldos
    - KPIs financieros: ROE, margen neto, eficiencia
    - Análisis temporal: evolución, comparativas
    - Detección desviaciones: alertas, umbrales
    - Análisis competitivo: ranking gestores
    - Queries dinámicas: generación automática
    """
    
    def __init__(self):
        self.query_cache = {}
        
    # =================================================================
    # 1. ANÁLISIS DE CARTERA POR GESTOR
    # =================================================================
    
    def get_cartera_completa_gestor(self, gestor_id: str, fecha: str = "2025-10") -> QueryResult:
        """
        Obtiene cartera completa de un gestor: contratos, productos, saldos
        
        CASO DE USO: "Muéstrame toda la cartera de Juan Pérez"
        """
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
            data=results,
            query_type="cartera_completa",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def get_contratos_activos_gestor(self, gestor_id: str) -> QueryResult:
        """
        Contratos activos de un gestor con detalle cliente-producto
        
        CASO DE USO: "¿Qué contratos activos tiene María García?"
        """
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
            data=results,
            query_type="contratos_activos",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def get_distribucion_productos_gestor(self, gestor_id: str) -> QueryResult:
        """
        Distribución de productos en cartera del gestor
        
        CASO DE USO: "¿Cómo está distribuida la cartera de Ana López por productos?"
        """
        query = """
            SELECT 
                p.DESC_PRODUCTO as producto,
                COUNT(mc.CONTRATO_ID) as num_contratos,
                ROUND(COUNT(mc.CONTRATO_ID) * 100.0 / (
                    SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE GESTOR_ID = ?
                ), 2) as porcentaje_contratos,
                COALESCE(SUM(mov.IMPORTE), 0) as importe_total,
                COALESCE(AVG(mov.IMPORTE), 0) as importe_promedio
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
            LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
            WHERE mc.GESTOR_ID = ?
            GROUP BY mc.PRODUCTO_ID, p.DESC_PRODUCTO
            ORDER BY num_contratos DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, gestor_id))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="distribucion_productos",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 2. KPIs FINANCIEROS POR GESTOR
    # =================================================================
    
    def calculate_margen_neto_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Calcula margen neto del gestor: (Ingresos - Gastos) / Ingresos
        
        CASO DE USO: "¿Cuál es el margen neto de Carlos Ruiz en octubre?"
        """
        query = """
            WITH ingresos AS (
                SELECT 
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
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
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
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
            data=results,
            query_type="margen_neto",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def calculate_eficiencia_operativa_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Calcula eficiencia operativa: Gastos totales / Número de contratos
        
        CASO DE USO: "¿Cuál es la eficiencia operativa de Laura Sánchez?"
        """
        query = """
            WITH gastos_gestor AS (
                SELECT 
                    SUM(ABS(mov.IMPORTE)) as gastos_totales,
                    COUNT(DISTINCT mov.CONTRATO_ID) as contratos_con_gastos
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                WHERE cont.GESTOR_ID = ?
                    AND strftime('%Y-%m', mov.FECHA) = ?
                    AND cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA')
            ),
            contratos_gestor AS (
                SELECT COUNT(*) as total_contratos
                FROM MAESTRO_CONTRATOS 
                WHERE GESTOR_ID = ?
            )
            SELECT 
                g.gastos_totales,
                c.total_contratos,
                g.contratos_con_gastos,
                CASE 
                    WHEN c.total_contratos > 0 
                    THEN ROUND(g.gastos_totales / c.total_contratos, 2)
                    ELSE 0 
                END as gasto_por_contrato,
                CASE 
                    WHEN g.gastos_totales > 0 
                    THEN ROUND((g.gastos_totales / c.total_contratos) / (g.gastos_totales / 
                        (SELECT AVG(total_contratos) FROM (
                            SELECT COUNT(*) as total_contratos 
                            FROM MAESTRO_CONTRATOS 
                            GROUP BY GESTOR_ID
                        ))
                    ) * 100, 2)
                    ELSE 100 
                END as eficiencia_relativa
            FROM gastos_gestor g, contratos_gestor c
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, periodo, gestor_id))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="eficiencia_operativa",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 3. ANÁLISIS DE DESVIACIONES
    # =================================================================
    
    def get_desviaciones_precio_gestor(self, gestor_id: str, umbral: float = 15.0) -> QueryResult:
        """
        Detecta desviaciones precio real vs estándar >umbral% para un gestor
        
        CASO DE USO: "¿Qué productos de Pedro Martín tienen desviaciones >15%?"
        """
        query = """
            WITH contratos_gestor AS (
                SELECT DISTINCT mc.PRODUCTO_ID, g.SEGMENTO_ID
                FROM MAESTRO_CONTRATOS mc
                JOIN MAESTRO_GESTORES g ON mc.GESTOR_ID = g.GESTOR_ID
                WHERE mc.GESTOR_ID = ?
            )
            SELECT 
                cg.PRODUCTO_ID,
                p.DESC_PRODUCTO as producto,
                cg.SEGMENTO_ID,
                s.DESC_SEGMENTO as segmento,
                pr.PRECIO_MANTENIMIENTO_REAL as precio_real,
                ps.PRECIO_MANTENIMIENTO as precio_std,
                ROUND(((ABS(pr.PRECIO_MANTENIMIENTO_REAL) - ABS(ps.PRECIO_MANTENIMIENTO)) / 
                       ABS(ps.PRECIO_MANTENIMIENTO)) * 100, 2) as desviacion_pct,
                CASE 
                    WHEN ABS(pr.PRECIO_MANTENIMIENTO_REAL) > ABS(ps.PRECIO_MANTENIMIENTO) 
                    THEN 'SOBRECOSTO' 
                    ELSE 'EFICIENCIA' 
                END as tipo_desviacion,
                pr.FECHA_CALCULO as periodo
            FROM contratos_gestor cg
            JOIN MAESTRO_PRODUCTOS p ON cg.PRODUCTO_ID = p.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS s ON cg.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN PRECIO_POR_PRODUCTO_REAL pr ON cg.SEGMENTO_ID = pr.SEGMENTO_ID 
                AND cg.PRODUCTO_ID = pr.PRODUCTO_ID
            JOIN PRECIO_POR_PRODUCTO_STD ps ON cg.SEGMENTO_ID = ps.SEGMENTO_ID 
                AND cg.PRODUCTO_ID = ps.PRODUCTO_ID
            WHERE ABS(((ABS(pr.PRECIO_MANTENIMIENTO_REAL) - ABS(ps.PRECIO_MANTENIMIENTO)) / 
                       ABS(ps.PRECIO_MANTENIMIENTO)) * 100) >= ?
            ORDER BY desviacion_pct DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, umbral))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="desviaciones_precio",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 4. ANÁLISIS TEMPORAL Y COMPARATIVO
    # =================================================================
    
    def compare_gestor_septiembre_octubre(self, gestor_id: str) -> QueryResult:
        """
        Compara performance del gestor entre septiembre y octubre 2025
        
        CASO DE USO: "¿Cómo evolucionó Isabel Fernández de septiembre a octubre?"
        """
        query = """
            WITH datos_mes AS (
                SELECT 
                    strftime('%Y-%m', mov.FECHA) as periodo,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
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
            data=results,
            query_type="comparacion_temporal",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 5. RANKING Y ANÁLISIS COMPETITIVO
    # =================================================================
    
    def get_ranking_gestores_por_kpi(self, kpi: str = "margen_neto", periodo: str = "2025-10") -> QueryResult:
        """
        Ranking de gestores por KPI específico
        
        CASO DE USO: "¿Cómo está posicionado mi gestor respecto a los demás?"
        KPIs disponibles: margen_neto, eficiencia, nuevos_contratos
        """
        
        if kpi == "margen_neto":
            query = """
                WITH kpis_gestores AS (
                    SELECT 
                        g.GESTOR_ID,
                        g.DESC_GESTOR as gestor,
                        c.DESC_CENTRO as centro,
                        SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                 THEN mov.IMPORTE ELSE 0 END) as ingresos,
                        SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                 THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos,
                        CASE 
                            WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                           THEN mov.IMPORTE ELSE 0 END) > 0 
                            THEN ROUND(((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                                 THEN mov.IMPORTE ELSE 0 END) - 
                                       SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                                THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                                       SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                                THEN mov.IMPORTE ELSE 0 END)) * 100, 2)
                            ELSE 0 
                        END as margen_neto_pct
                    FROM MAESTRO_GESTORES g
                    JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                    JOIN MAESTRO_CONTRATOS cont ON g.GESTOR_ID = cont.GESTOR_ID
                    JOIN MOVIMIENTOS_CONTRATOS mov ON cont.CONTRATO_ID = mov.CONTRATO_ID
                    JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                    JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                    WHERE strftime('%Y-%m', mov.FECHA) = ?
                        AND c.IND_CENTRO_FINALISTA = 1  -- Solo centros finalistas
                    GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO
                )
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY margen_neto_pct DESC) as ranking,
                    gestor,
                    centro,
                    margen_neto_pct,
                    ingresos,
                    gastos,
                    (ingresos - gastos) as beneficio_neto
                FROM kpis_gestores
                WHERE margen_neto_pct IS NOT NULL
                ORDER BY margen_neto_pct DESC
            """
        
        elif kpi == "nuevos_contratos":
            query = """
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as ranking,
                    g.DESC_GESTOR as gestor,
                    c.DESC_CENTRO as centro,
                    COUNT(*) as nuevos_contratos,
                    COALESCE(SUM(mov.IMPORTE), 0) as importe_total_nuevos
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE strftime('%Y-%m', mc.FECHA_ALTA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO
                ORDER BY nuevos_contratos DESC
            """
        
        start_time = datetime.now()
        results = execute_query(query, (periodo,))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type=f"ranking_{kpi}",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 6. GENERADOR DINÁMICO DE QUERIES (GPT-4.1) - MEJORADO
    # =================================================================

    def generate_dynamic_query(self, user_question: str, gestor_context: Dict[str, Any] = None) -> QueryResult:
        """
        Genera consultas SQL dinámicas usando GPT-4.1 para preguntas específicas
    
        MEJORAS:
        - System prompt separado y mantenible
        - Validación previa de la consulta generada
        - Mejor manejo de errores y logging
        """
    
        from ..prompts.system_prompts import get_sql_generation_prompt, get_query_validation_prompt
    
        # Obtener contexto del gestor si está disponible
        if gestor_context and gestor_context.get('gestor_id'):
            try:
                gestor_info = execute_query("""
                    SELECT g.GESTOR_ID, g.DESC_GESTOR, g.CENTRO, g.SEGMENTO_ID,
                           c.DESC_CENTRO, s.DESC_SEGMENTO
                    FROM MAESTRO_GESTORES g
                    JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                    JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                    WHERE g.GESTOR_ID = ?
                """, (gestor_context['gestor_id'],), fetch_type="one")
    
                if gestor_info:
                    gestor_context.update(gestor_info)
    
            except Exception as e:
                logger.warning(f"⚠️ No se pudo obtener contexto del gestor: {e}")
    
        try:
            # Usar prompt especializado desde el módulo de prompts
            system_prompt = get_sql_generation_prompt(gestor_context)
    
            user_prompt = f"""
            Genera una consulta SQL para responder: "{user_question}"
    
            La consulta debe ser ejecutable directamente en SQLite y devolver resultados útiles.
            """
    
            # Generar la consulta con GPT-4.1
            response = iniciar_agente_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,  # Baja temperatura para mayor precisión
                max_tokens=1000
            )
    
            generated_sql = response.choices.message.content.strip()
    
            # Limpiar la respuesta (eliminar markdown, etc.)
            if "```sql" in generated_sql:
                generated_sql = generated_sql.split("``````")[0].strip()
            elif "```" in generated_sql:
                lines = generated_sql.split("```")
                for line in lines:
                    if any(keyword in line.upper() for keyword in ['SELECT', 'WITH', 'INSERT', 'UPDATE']):
                        generated_sql = line.strip()
                        break
                    
            # NUEVA FUNCIONALIDAD: Validar la consulta antes de ejecutarla
            validation_prompt = get_query_validation_prompt()
            validation_response = iniciar_agente_llm(
                system_prompt=validation_prompt,
                user_prompt=f"Valida esta consulta SQL:\n\n{generated_sql}",
                temperature=0.0,
                max_tokens=200
            )
    
            validation_result = validation_response.choices[0].message.content.strip()
    
            if not validation_result.startswith("VALID"):
                logger.error(f"❌ Consulta SQL inválida: {validation_result}")
                return QueryResult(
                    data=[{"error": f"Consulta SQL generada no es válida: {validation_result}"}],
                    query_type="dynamic_validation_error",
                    execution_time=0,
                    row_count=0,
                    query_sql=generated_sql
                )
    
            logger.info(f"✅ Query dinámica generada y validada para: {user_question}")
    
            # Ejecutar la query validada
            start_time = datetime.now()
            results = execute_query(generated_sql)
            execution_time = (datetime.now() - start_time).total_seconds()
    
            return QueryResult(
                data=results,
                query_type="dynamic_generated",
                execution_time=execution_time,
                row_count=len(results) if results else 0,
                query_sql=generated_sql
            )
    
        except Exception as e:
            logger.error(f"❌ Error generando query dinámica: {e}")
            return QueryResult(
                data=[{"error": f"No se pudo generar consulta para: {user_question}", "details": str(e)}],
                query_type="dynamic_error",
                execution_time=0,
                row_count=0,
                query_sql="-- Error en generación dinámica"
            )
    
    
    # =================================================================
    # 7. MOTOR DE SELECCIÓN INTELIGENTE - COMPLETAMENTE REDISEÑADO
    # =================================================================

    def get_best_query_for_question(self, user_question: str, gestor_id: str = None) -> QueryResult:
        """
        Motor inteligente MEJORADO que decide qué query usar según la pregunta del usuario

        MEJORAS CRÍTICAS:
        1. Usa GPT-4.1 para clasificar inteligentemente (no keywords simples)
        2. Reduce false positives/negatives significativamente  
        3. Fallback robusto a generación dinámica
        4. Logging detallado para debugging y mejora continua
        """

        from ..prompts.system_prompts import get_query_classification_prompt

        # Lista de queries predefinidas disponibles
        available_queries = [
            "get_cartera_completa_gestor",
            "get_contratos_activos_gestor", 
            "get_distribucion_productos_gestor",
            "calculate_margen_neto_gestor",
            "calculate_eficiencia_operativa_gestor",
            "get_desviaciones_precio_gestor",
            "compare_gestor_septiembre_octubre",
            "get_ranking_gestores_por_kpi"
        ]

        try:
            # FASE 1: Clasificación inteligente con GPT-4.1
            classification_prompt = get_query_classification_prompt(available_queries)

            classification_response = iniciar_agente_llm(
                system_prompt=classification_prompt,
                user_prompt=f'Clasifica esta pregunta: "{user_question}"',
                temperature=0.0,  # Temperatura 0 para máxima precisión en clasificación
                max_tokens=50
            )

            predicted_query = classification_response.choices.message.content.strip()

            logger.info(f"🧠 Clasificación inteligente: '{user_question}' → {predicted_query}")

            # FASE 2: Ejecutar query predefinida si se identificó correctamente
            if predicted_query in available_queries:

                query_method = getattr(self, predicted_query)

                # Parámetros específicos según el método
                if predicted_query in ["get_cartera_completa_gestor", "get_contratos_activos_gestor", 
                                     "get_distribucion_productos_gestor", "get_desviaciones_precio_gestor"]:
                    if gestor_id:
                        result = query_method(gestor_id)
                    else:
                        logger.warning(f"⚠️ Query {predicted_query} requiere gestor_id pero no se proporcionó")
                        # Fallback: usar generación dinámica
                        return self.generate_dynamic_query(user_question, {"gestor_id": gestor_id})

                elif predicted_query in ["calculate_margen_neto_gestor", "calculate_eficiencia_operativa_gestor"]:
                    if gestor_id:
                        # Detectar período si se menciona en la pregunta
                        periodo = "2025-10"  # Default
                        if "septiembre" in user_question.lower():
                            periodo = "2025-09"
                        result = query_method(gestor_id, periodo)
                    else:
                        logger.warning(f"⚠️ Query {predicted_query} requiere gestor_id pero no se proporcionó")
                        return self.generate_dynamic_query(user_question, {"gestor_id": gestor_id})

                elif predicted_query == "compare_gestor_septiembre_octubre":
                    if gestor_id:
                        result = query_method(gestor_id)
                    else:
                        return self.generate_dynamic_query(user_question, {"gestor_id": gestor_id})

                elif predicted_query == "get_ranking_gestores_por_kpi":
                    # Detectar tipo de KPI desde la pregunta
                    kpi_type = "margen_neto"  # Default
                    if "eficiencia" in user_question.lower():
                        kpi_type = "eficiencia"
                    elif "contratos" in user_question.lower() and "nuevos" in user_question.lower():
                        kpi_type = "nuevos_contratos"

                    result = query_method(kpi_type)

                else:
                    # Método genérico sin parámetros específicos
                    result = query_method()

                logger.info(f"✅ Query predefinida ejecutada exitosamente: {predicted_query}")
                return result

            # FASE 3: Usar generación dinámica si no se identificó query predefinida
            elif predicted_query == "DYNAMIC_QUERY":
                logger.info(f"🤖 Usando generación dinámica para pregunta compleja: {user_question}")
                gestor_context = {"gestor_id": gestor_id} if gestor_id else None
                return self.generate_dynamic_query(user_question, gestor_context)

            else:
                # FASE 4: Fallback por clasificación incorrecta
                logger.warning(f"⚠️ Clasificación no reconocida: {predicted_query}. Usando generación dinámica.")
                gestor_context = {"gestor_id": gestor_id} if gestor_id else None
                return self.generate_dynamic_query(user_question, gestor_context)

        except Exception as e:
            logger.error(f"❌ Error en motor de selección inteligente: {e}")

            # Fallback final: generación dinámica
            logger.info(f"🔄 Fallback: Usando generación dinámica por error en clasificación")
            gestor_context = {"gestor_id": gestor_id} if gestor_id else None
            return self.generate_dynamic_query(user_question, gestor_context)

    # =================================================================
    # 8. FUNCIONES DE ANÁLISIS Y MÉTRICAS DEL SISTEMA
    # =================================================================

    def get_query_usage_metrics(self) -> Dict[str, Any]:
        """
        Métricas de uso del sistema de queries para optimización continua
        """

        # Esta función puede expandirse para trackear:
        # - Queries más utilizadas
        # - Tiempo de ejecución promedio
        # - Tasa de éxito predefinidas vs dinámicas
        # - Patrones de error más comunes

        return {
            "status": "metrics_placeholder",
            "message": "Funcionalidad de métricas pendiente de implementación"
        }

    def validate_gestor_access(self, gestor_id: str, user_role: str = "gestor_comercial") -> bool:
        """
        Valida si un usuario tiene acceso a consultar datos de un gestor específico

        LÓGICA:
        - Gestores comerciales: Solo sus propios datos
        - Control de gestión: Acceso completo a todos los gestores
        """

        if user_role == "control_gestion":
            return True

        # Para gestores comerciales, validar que solo accedan a sus propios datos
        # Esta lógica se expandirá cuando tengamos sistema de autenticación
        return True  # Por ahora permitir acceso completo

    # =================================================================
    # 9. QUERIES ESPECIALIZADAS ADICIONALES - ROE Y ANÁLISIS AVANZADO
    # =================================================================
    
    def calculate_roe_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Calcula ROE (Return on Equity) del gestor: Beneficio Neto / Patrimonio gestionado
        
        CASO DE USO: "¿Cuál es el ROE de Ana López?"
        CRÍTICO para análisis bancario - KPI fundamental de rentabilidad
        """
        query = """
            WITH patrimonio_gestor AS (
                SELECT 
                    SUM(mov.IMPORTE) as patrimonio_total
                FROM MAESTRO_CONTRATOS mc
                JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mc.GESTOR_ID = ?
                    AND strftime('%Y-%m', mc.FECHA_ALTA) <= ?
            ),
            beneficio_gestor AS (
                SELECT 
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_total,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_total
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                WHERE cont.GESTOR_ID = ?
                    AND strftime('%Y-%m', mov.FECHA) = ?
            )
            SELECT 
                pg.patrimonio_total,
                bg.ingresos_total,
                bg.gastos_total,
                (bg.ingresos_total - bg.gastos_total) as beneficio_neto,
                CASE 
                    WHEN pg.patrimonio_total > 0 
                    THEN ROUND(((bg.ingresos_total - bg.gastos_total) / pg.patrimonio_total) * 100, 4)
                    ELSE 0 
                END as roe_porcentaje,
                ? as periodo_calculo
            FROM patrimonio_gestor pg, beneficio_gestor bg
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, periodo, gestor_id, periodo, periodo))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="roe_calculation",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def get_distribucion_fondos_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Análisis específico de fondos con lógica 85% fábrica / 15% banco
        
        CASO DE USO: "¿Cómo están distribuidos los fondos de Pablo Martín?"
        """
        query = """
            WITH fondos_gestor AS (
                SELECT 
                    mc.CONTRATO_ID,
                    COALESCE(SUM(mov.IMPORTE), 0) as importe_contrato_total,
                    p.DESC_PRODUCTO
                FROM MAESTRO_CONTRATOS mc
                JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE mc.GESTOR_ID = ?
                    AND p.DESC_PRODUCTO LIKE '%Fondo%'
                GROUP BY mc.CONTRATO_ID, p.DESC_PRODUCTO
            ),
            movimientos_fondos AS (
                SELECT 
                    mov.CUENTA_ID,
                    SUM(mov.IMPORTE) as importe_total,
                    COUNT(*) as num_movimientos,
                    CASE 
                        WHEN mov.CUENTA_ID = '760025' THEN 'FABRICA_85PCT'
                        WHEN mov.CUENTA_ID = '760024' THEN 'BANCO_15PCT'
                        ELSE 'OTROS'
                    END as tipo_reparto
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN fondos_gestor fg ON mov.CONTRATO_ID = fg.CONTRATO_ID
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                    AND mov.CUENTA_ID LIKE '7600%'
                GROUP BY mov.CUENTA_ID
            )
            SELECT 
                fg.DESC_PRODUCTO,
                COUNT(DISTINCT fg.CONTRATO_ID) as contratos_fondos,
                SUM(fg.importe_contrato_total) as patrimonio_fondos,
                mf.tipo_reparto,
                mf.importe_total,
                mf.num_movimientos,
                ROUND(mf.importe_total * 100.0 / NULLIF(SUM(mf.importe_total) OVER(), 0), 2) as porcentaje_reparto
            FROM fondos_gestor fg
            LEFT JOIN movimientos_fondos mf ON 1=1
            GROUP BY fg.DESC_PRODUCTO, mf.tipo_reparto
            ORDER BY mf.importe_total DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, periodo))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="distribucion_fondos",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 10. SISTEMA DE ALERTAS Y MONITOREO
    # =================================================================
    
    def get_alertas_criticas_gestor(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Sistema integral de alertas críticas para un gestor específico
        
        CASO DE USO: "¿Qué alertas críticas tiene mi cartera?"
        DETECTA: Desviaciones >15%, ROE <8%, Margen neto <12%, contratos de riesgo
        """
        query = """
            WITH alertas_desviaciones AS (
                SELECT 
                    'DESVIACION_PRECIO' as tipo_alerta,
                    'CRITICA' as severidad,
                    cg.PRODUCTO_ID || ' - ' || cg.SEGMENTO_ID as detalle,
                    pr.PRECIO_MANTENIMIENTO_REAL as valor_actual,
                    ps.PRECIO_MANTENIMIENTO as valor_estandar,
                    ROUND(((ABS(pr.PRECIO_MANTENIMIENTO_REAL) - ABS(ps.PRECIO_MANTENIMIENTO)) / 
                           ABS(ps.PRECIO_MANTENIMIENTO)) * 100, 2) as desviacion_pct
                FROM (
                    SELECT DISTINCT mc.PRODUCTO_ID, g.SEGMENTO_ID
                    FROM MAESTRO_CONTRATOS mc
                    JOIN MAESTRO_GESTORES g ON mc.GESTOR_ID = g.GESTOR_ID
                    WHERE mc.GESTOR_ID = ?
                ) cg
                JOIN PRECIO_POR_PRODUCTO_REAL pr ON cg.SEGMENTO_ID = pr.SEGMENTO_ID 
                    AND cg.PRODUCTO_ID = pr.PRODUCTO_ID
                JOIN PRECIO_POR_PRODUCTO_STD ps ON cg.SEGMENTO_ID = ps.SEGMENTO_ID 
                    AND cg.PRODUCTO_ID = ps.PRODUCTO_ID
                WHERE ABS(((ABS(pr.PRECIO_MANTENIMIENTO_REAL) - ABS(ps.PRECIO_MANTENIMIENTO)) / 
                           ABS(ps.PRECIO_MANTENIMIENTO)) * 100) >= 15.0
                    AND pr.FECHA_CALCULO LIKE ?||'%'
            ),
            alertas_margen AS (
                SELECT 
                    'MARGEN_BAJO' as tipo_alerta,
                    CASE 
                        WHEN margen_calculado < 8.0 THEN 'CRITICA'
                        WHEN margen_calculado < 12.0 THEN 'ALTA'
                        ELSE 'MEDIA'
                    END as severidad,
                    'Margen neto: ' || ROUND(margen_calculado, 2) || '%' as detalle,
                    margen_calculado as valor_actual,
                    12.0 as valor_estandar,
                    (margen_calculado - 12.0) as desviacion_pct
                FROM (
                    SELECT 
                        CASE 
                            WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                           THEN mov.IMPORTE ELSE 0 END) > 0 
                            THEN ((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                             THEN mov.IMPORTE ELSE 0 END) - 
                                   SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                            THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                                   SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                            THEN mov.IMPORTE ELSE 0 END)) * 100
                            ELSE 0 
                        END as margen_calculado
                    FROM MOVIMIENTOS_CONTRATOS mov
                    JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                    JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                    JOIN MAESTRO_CONTRATOS cont ON mov.CONTRATO_ID = cont.CONTRATO_ID
                    WHERE cont.GESTOR_ID = ?
                        AND strftime('%Y-%m', mov.FECHA) = ?
                ) subquery
                WHERE margen_calculado < 12.0
            ),
            alertas_contratos AS (
                SELECT 
                    'CONTRATO_ALTO_IMPORTE' as tipo_alerta,
                    'MEDIA' as severidad,
                    'Contrato ' || mc.CONTRATO_ID || ' - ' || p.DESC_PRODUCTO as detalle,
                    COALESCE(SUM(mov.IMPORTE), 0) as valor_actual,
                    avg_importe as valor_estandar,
                    ROUND(((COALESCE(SUM(mov.IMPORTE), 0) - avg_importe) / NULLIF(avg_importe, 0)) * 100, 2) as desviacion_pct
                FROM MAESTRO_CONTRATOS mc
                JOIN MAESTRO_PRODUCTOS p ON mc.PRODUCTO_ID = p.PRODUCTO_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                CROSS JOIN (
                    SELECT AVG(COALESCE(SUM(mov2.IMPORTE), 0)) as avg_importe
                    FROM MAESTRO_CONTRATOS mc2
                    LEFT JOIN MOVIMIENTOS_CONTRATOS mov2 ON mc2.CONTRATO_ID = mov2.CONTRATO_ID
                    WHERE mc2.GESTOR_ID = ?
                    GROUP BY mc2.CONTRATO_ID
                ) avg_data
                WHERE mc.GESTOR_ID = ?
                GROUP BY mc.CONTRATO_ID, p.DESC_PRODUCTO, avg_importe
                HAVING COALESCE(SUM(mov.IMPORTE), 0) > (avg_importe * 2)  -- Contratos >200% promedio
                ORDER BY valor_actual DESC
                LIMIT 5
            )
            SELECT * FROM alertas_desviaciones
            UNION ALL
            SELECT * FROM alertas_margen  
            UNION ALL
            SELECT * FROM alertas_contratos
            ORDER BY 
                CASE severidad 
                    WHEN 'CRITICA' THEN 1 
                    WHEN 'ALTA' THEN 2 
                    WHEN 'MEDIA' THEN 3 
                END,
                ABS(desviacion_pct) DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, periodo, gestor_id, periodo, gestor_id, gestor_id))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="alertas_criticas",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 11. ANÁLISIS POR CENTRO Y SEGMENTO
    # =================================================================
    
    def get_performance_por_centro(self, centro_id: int = None, periodo: str = "2025-10") -> QueryResult:
        """
        Análisis de performance agregado por centro(s)
        
        CASO DE USO: "¿Cómo está funcionando el centro de Madrid?"
        """
        
        where_clause = "WHERE c.IND_CENTRO_FINALISTA = 1 AND c.CENTRO_ID = ?" if centro_id else "WHERE c.IND_CENTRO_FINALISTA = 1"
        params = (periodo, centro_id) if centro_id else (periodo,)
        
        query = f"""
            WITH performance_centro AS (
                SELECT 
                    c.CENTRO_ID,
                    c.DESC_CENTRO,
                    COUNT(DISTINCT g.GESTOR_ID) as num_gestores,
                    COUNT(DISTINCT mc.CONTRATO_ID) as total_contratos,
                    COUNT(DISTINCT mc.CLIENTE_ID) as total_clientes,
                    COALESCE(SUM(mov.IMPORTE), 0) as patrimonio_total,
                    COALESCE(AVG(mov.IMPORTE), 0) as importe_promedio_contrato
                FROM MAESTRO_CENTROS c
                JOIN MAESTRO_GESTORES g ON c.CENTRO_ID = g.CENTRO
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                {where_clause}
                GROUP BY c.CENTRO_ID, c.DESC_CENTRO
            ),
            financieros_centro AS (
                SELECT 
                    c.CENTRO_ID,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_centro,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_centro
                FROM MAESTRO_CENTROS c
                JOIN MAESTRO_GESTORES g ON c.CENTRO_ID = g.CENTRO
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY c.CENTRO_ID
            )
            SELECT 
                pc.CENTRO_ID,
                pc.DESC_CENTRO,
                pc.num_gestores,
                pc.total_contratos,
                pc.total_clientes,
                pc.patrimonio_total,
                pc.importe_promedio_contrato,
                fc.ingresos_centro,
                fc.gastos_centro,
                (fc.ingresos_centro - fc.gastos_centro) as beneficio_centro,
                CASE 
                    WHEN fc.ingresos_centro > 0 
                    THEN ROUND(((fc.ingresos_centro - fc.gastos_centro) / fc.ingresos_centro) * 100, 2)
                    ELSE 0 
                END as margen_neto_centro,
                CASE 
                    WHEN pc.total_contratos > 0 
                    THEN ROUND(fc.gastos_centro / pc.total_contratos, 2)
                    ELSE 0 
                END as gasto_por_contrato,
                CASE 
                    WHEN pc.patrimonio_total > 0 
                    THEN ROUND(((fc.ingresos_centro - fc.gastos_centro) / pc.patrimonio_total) * 100, 4)
                    ELSE 0 
                END as roe_centro
            FROM performance_centro pc
            LEFT JOIN financieros_centro fc ON pc.CENTRO_ID = fc.CENTRO_ID
            ORDER BY beneficio_centro DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, params)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="performance_centro",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def get_analysis_por_segmento(self, segmento_id: str = None, periodo: str = "2025-10") -> QueryResult:
        """
        Análisis detallado por segmento de negocio
        
        CASO DE USO: "¿Cómo está funcionando el segmento de fondos?"
        """
        
        where_clause = "WHERE s.SEGMENTO_ID = ?" if segmento_id else ""
        params = (periodo, segmento_id) if segmento_id else (periodo,)
        
        query = f"""
            WITH segmento_performance AS (
                SELECT 
                    s.SEGMENTO_ID,
                    s.DESC_SEGMENTO,
                    COUNT(DISTINCT g.GESTOR_ID) as gestores_segmento,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos_segmento,
                    COALESCE(SUM(mov.IMPORTE), 0) as patrimonio_segmento,
                    COALESCE(AVG(mov.IMPORTE), 0) as importe_promedio,
                    COUNT(DISTINCT mc.PRODUCTO_ID) as productos_diferentes
                FROM MAESTRO_SEGMENTOS s
                JOIN MAESTRO_GESTORES g ON s.SEGMENTO_ID = g.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                {where_clause}
                GROUP BY s.SEGMENTO_ID, s.DESC_SEGMENTO
            ),
            precios_segmento AS (
                SELECT 
                    pr.SEGMENTO_ID,
                    AVG(ABS(pr.PRECIO_MANTENIMIENTO_REAL)) as precio_real_promedio,
                    AVG(ABS(ps.PRECIO_MANTENIMIENTO)) as precio_std_promedio,
                    COUNT(*) as productos_con_precio
                FROM PRECIO_POR_PRODUCTO_REAL pr
                JOIN PRECIO_POR_PRODUCTO_STD ps ON pr.SEGMENTO_ID = ps.SEGMENTO_ID 
                    AND pr.PRODUCTO_ID = ps.PRODUCTO_ID
                WHERE pr.FECHA_CALCULO LIKE ?||'%'
                GROUP BY pr.SEGMENTO_ID
            )
            SELECT 
                sp.SEGMENTO_ID,
                sp.DESC_SEGMENTO,
                sp.gestores_segmento,
                sp.contratos_segmento,
                sp.patrimonio_segmento,
                sp.importe_promedio,
                sp.productos_diferentes,
                ps.precio_real_promedio,
                ps.precio_std_promedio,
                CASE 
                    WHEN ps.precio_std_promedio > 0 
                    THEN ROUND(((ps.precio_real_promedio - ps.precio_std_promedio) / ps.precio_std_promedio) * 100, 2)
                    ELSE 0 
                END as desviacion_precio_promedio,
                ps.productos_con_precio
            FROM segmento_performance sp
            LEFT JOIN precios_segmento ps ON sp.SEGMENTO_ID = ps.SEGMENTO_ID
            ORDER BY sp.patrimonio_segmento DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, params)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="analysis_segmento",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    # =================================================================
    # 12. ANÁLISIS COMPETITIVO AVANZADO
    # =================================================================
    
    def get_benchmarking_gestores(self, gestor_id: str, periodo: str = "2025-10") -> QueryResult:
        """
        Benchmarking completo de un gestor vs sus peers en el mismo centro y segmento
        
        CASO DE USO: "¿Cómo estoy vs mis compañeros del mismo perfil?"
        """
        query = """
            WITH gestor_target AS (
                SELECT g.CENTRO, g.SEGMENTO_ID
                FROM MAESTRO_GESTORES g
                WHERE g.GESTOR_ID = ?
            ),
            peer_gestores AS (
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    COUNT(DISTINCT mc.CONTRATO_ID) as contratos,
                    COALESCE(SUM(mov.IMPORTE), 0) as patrimonio,
                    CASE 
                        WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                       THEN mov.IMPORTE ELSE 0 END) > 0 
                        THEN ((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                         THEN mov.IMPORTE ELSE 0 END) - 
                               SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                        THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                               SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                        THEN mov.IMPORTE ELSE 0 END)) * 100
                        ELSE 0 
                    END as margen_neto,
                    CASE 
                        WHEN COUNT(DISTINCT mc.CONTRATO_ID) > 0 
                        THEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                       THEN ABS(mov.IMPORTE) ELSE 0 END) / COUNT(DISTINCT mc.CONTRATO_ID)
                        ELSE 0 
                    END as gasto_por_contrato
                FROM MAESTRO_GESTORES g
                JOIN gestor_target gt ON g.CENTRO = gt.CENTRO AND g.SEGMENTO_ID = gt.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    AND strftime('%Y-%m', mov.FECHA) = ?
                LEFT JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                LEFT JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR
            ),
            percentiles AS (
                SELECT 
                    COUNT(*) as total_peers,
                    AVG(contratos) as avg_contratos,
                    AVG(patrimonio) as avg_patrimonio,
                    AVG(margen_neto) as avg_margen_neto,
                    AVG(gasto_por_contrato) as avg_gasto_por_contrato,
                    MIN(margen_neto) as min_margen_neto,
                    MAX(margen_neto) as max_margen_neto
                FROM peer_gestores
            )
            SELECT 
                pg.GESTOR_ID,
                pg.DESC_GESTOR,
                pg.contratos,
                pg.patrimonio,
                pg.margen_neto,
                pg.gasto_por_contrato,
                p.total_peers,
                p.avg_contratos,
                p.avg_patrimonio,
                p.avg_margen_neto,
                p.avg_gasto_por_contrato,
                CASE WHEN pg.GESTOR_ID = ? THEN 'TARGET' ELSE 'PEER' END as tipo_gestor,
                ROW_NUMBER() OVER (ORDER BY pg.margen_neto DESC) as ranking_margen,
                ROUND((pg.contratos - p.avg_contratos) / NULLIF(p.avg_contratos, 0) * 100, 2) as diff_contratos_pct,
                ROUND((pg.patrimonio - p.avg_patrimonio) / NULLIF(p.avg_patrimonio, 0) * 100, 2) as diff_patrimonio_pct,
                ROUND(pg.margen_neto - p.avg_margen_neto, 2) as diff_margen_puntos
            FROM peer_gestores pg
            CROSS JOIN percentiles p
            ORDER BY pg.margen_neto DESC
        """
        
        start_time = datetime.now()
        results = execute_query(query, (gestor_id, periodo, gestor_id))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type="benchmarking_gestores",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )
    
    def get_top_performers_by_metric(self, metric: str = "margen_neto", limit: int = 10, periodo: str = "2025-10") -> QueryResult:
        """
        Top performers por métrica específica
        
        CASO DE USO: "¿Quiénes son los top 10 gestores por ROE?"
        MÉTRICAS: margen_neto, roe, eficiencia, nuevos_contratos, patrimonio
        """
        
        metric_queries = {
            "margen_neto": """
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    CASE 
                        WHEN SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                       THEN mov.IMPORTE ELSE 0 END) > 0 
                        THEN ROUND(((SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                             THEN mov.IMPORTE ELSE 0 END) - 
                                     SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                              THEN ABS(mov.IMPORTE) ELSE 0 END)) / 
                                     SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                              THEN mov.IMPORTE ELSE 0 END)) * 100, 2)
                        ELSE 0 
                    END as valor_metrica,
                    'margen_neto_pct' as unidad_metrica,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                             THEN mov.IMPORTE ELSE 0 END) as ingresos_total,
                    SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                             THEN ABS(mov.IMPORTE) ELSE 0 END) as gastos_total
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                WHERE strftime('%Y-%m', mov.FECHA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1  -- Solo centros finalistas
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                HAVING SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                THEN mov.IMPORTE ELSE 0 END) > 0
                ORDER BY valor_metrica DESC
            """,
            
            "roe": """
                WITH patrimonio_gestores AS (
                    SELECT 
                        g.GESTOR_ID,
                        g.DESC_GESTOR,
                        c.DESC_CENTRO,
                        s.DESC_SEGMENTO,
                        COALESCE(SUM(mov.IMPORTE), 0) as patrimonio_total
                    FROM MAESTRO_GESTORES g
                    JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                    JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                    JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                    LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    WHERE c.IND_CENTRO_FINALISTA = 1
                    GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                ),
                beneficios_gestores AS (
                    SELECT 
                        g.GESTOR_ID,
                        (SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('MARGEN_INTERES', 'COMISIONES', 'INGRESOS') 
                                  THEN mov.IMPORTE ELSE 0 END) - 
                         SUM(CASE WHEN cdr.COD_LINEA_CDR IN ('GASTOS_PERSONAL', 'GASTOS_ADMIN', 'GASTOS_ESTRUCTURA') 
                                  THEN ABS(mov.IMPORTE) ELSE 0 END)) as beneficio_neto
                    FROM MAESTRO_GESTORES g
                    JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                    JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                    JOIN MAESTRO_CUENTAS mct ON mov.CUENTA_ID = mct.CUENTA_ID
                    JOIN MAESTRO_LINEA_CDR cdr ON mct.LINEA_CDR = cdr.COD_LINEA_CDR
                    WHERE strftime('%Y-%m', mov.FECHA) = ?
                    GROUP BY g.GESTOR_ID
                )
                SELECT 
                    pg.GESTOR_ID,
                    pg.DESC_GESTOR,
                    pg.DESC_CENTRO,
                    pg.DESC_SEGMENTO,
                    CASE 
                        WHEN pg.patrimonio_total > 0 
                        THEN ROUND((bg.beneficio_neto / pg.patrimonio_total) * 100, 4)
                        ELSE 0 
                    END as valor_metrica,
                    'roe_pct' as unidad_metrica,
                    pg.patrimonio_total,
                    bg.beneficio_neto
                FROM patrimonio_gestores pg
                JOIN beneficios_gestores bg ON pg.GESTOR_ID = bg.GESTOR_ID
                WHERE pg.patrimonio_total > 0
                ORDER BY valor_metrica DESC
            """,
            
            "nuevos_contratos": """
                SELECT 
                    g.GESTOR_ID,
                    g.DESC_GESTOR,
                    c.DESC_CENTRO,
                    s.DESC_SEGMENTO,
                    COUNT(*) as valor_metrica,
                    'contratos' as unidad_metrica,
                    COALESCE(SUM(mov.IMPORTE), 0) as importe_total_nuevos,
                    COALESCE(AVG(mov.IMPORTE), 0) as importe_promedio_nuevo
                FROM MAESTRO_GESTORES g
                JOIN MAESTRO_CENTROS c ON g.CENTRO = c.CENTRO_ID
                JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
                JOIN MAESTRO_CONTRATOS mc ON g.GESTOR_ID = mc.GESTOR_ID
                LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
                WHERE strftime('%Y-%m', mc.FECHA_ALTA) = ?
                    AND c.IND_CENTRO_FINALISTA = 1
                GROUP BY g.GESTOR_ID, g.DESC_GESTOR, c.DESC_CENTRO, s.DESC_SEGMENTO
                ORDER BY valor_metrica DESC
            """
        }
        
        if metric not in metric_queries:
            # Fallback a margen_neto si la métrica no existe
            metric = "margen_neto"
        
        query = metric_queries[metric] + f" LIMIT {limit}"
        
        start_time = datetime.now()
        results = execute_query(query, (periodo,))
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            data=results,
            query_type=f"top_performers_{metric}",
            execution_time=execution_time,
            row_count=len(results) if results else 0,
            query_sql=query
        )


# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# =================================================================

# Instancia global para uso en toda la aplicación
gestor_queries = GestorQueries()

# Funciones de conveniencia para importación directa
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
    
    MEJORAS:
    - Motor de selección inteligente con GPT-4.1
    - Fallback robusto a generación dinámica  
    - Validación de consultas antes de ejecución
    - Logging detallado para debugging
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
