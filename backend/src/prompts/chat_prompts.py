"""
chat_prompts.py — Catálogos de queries para ChatAgent/clasificador
===================================================================
S43: Catálogos extraídos de system_prompts.py y acortados.
El DeterministicQueryRouter (S40) reemplazó el uso de estos catálogos
para routing real, pero se mantienen por compatibilidad y documentación.

Regla SQL del schema real (BM_CONTABILIDAD_CDG.db):
  Ingresos  : CUENTA_ID LIKE '76%'
  Gastos dir: SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69') AND CONTRATO_ID IS NOT NULL
  Gastos cen: SUBSTR(CUENTA_ID,1,2) IN ('62','64','66','68','69') AND CONTRATO_ID IS NULL
  Tabla      : MOVIMIENTOS_CONTRATOS
  Siempre    : ABS(SUM(IMPORTE)) para gastos (importes negativos en BD)
"""

# ── Catálogo basic_queries.py ─────────────────────────────────────────────────
BASIC_QUERIES_CATALOG_PROMPT = """
Catálogo basic_queries.py — consultas de datos maestros y métricas financieras:

GESTORES / CENTROS / CONTRATOS:
- get_gestor_info(gestor_id) — perfil completo: nombre, centro, segmento
- get_all_gestores() — los 30 gestores con centro y segmento
- get_gestor_metricas_completas(gestor_id, periodo) — ingresos, gastos, margen, contratos, clientes del gestor
- get_centro_metricas_financieras(centro_id, periodo) — métricas financieras agregadas del centro
- get_centro_gestores_con_metricas(centro_id, periodo) — gestores del centro con KPIs financieros

CLIENTES / CONTRATOS:
- get_gestor_clientes_con_metricas(gestor_id, periodo) — clientes del gestor con ingresos, margen, contratos
- count_contratos_by_gestor() — ranking gestores por número de contratos
- get_contratos_nuevos_periodo(periodo) — contratos firmados en el período (formato YYYY-MM)

RESUMEN:
- get_resumen_general() — resumen global: total gestores, contratos, clientes, productos
"""

# ── Catálogo comparative_queries.py ──────────────────────────────────────────
COMPARATIVE_QUERIES_CATALOG_PROMPT = """
Catálogo comparative_queries.py — comparativas y rankings entre gestores/centros:

- ranking_gestores_por_margen_enhanced(periodo) — todos los gestores ordenados por margen neto, con ingresos, gastos, ROE
- compare_roe_gestores_enhanced(periodo) — ROE comparativo de los 30 gestores
- compare_eficiencia_centro_enhanced(periodo) — eficiencia operativa por centro comercial
- get_evolucion_gestores_sep_oct() — variación sep→oct de cada gestor: clasificacion mejora/estable/retroceso
"""

# ── Catálogo deviation_queries.py ─────────────────────────────────────────────
DEVIATION_QUERIES_CATALOG_PROMPT = """
Catálogo deviation_queries.py — detección de desviaciones precio real vs estándar:

- detect_precio_desviaciones_criticas_enhanced(periodo, threshold=15.0) — productos/segmentos con precio real vs STD fuera de umbral
- detect_patron_temporal_anomalias_enhanced() — anomalías en la evolución temporal sep→oct
- get_desviaciones_precio_gestor_enhanced(gestor_id, periodo, threshold=15.0) — desviaciones de precio del gestor específico
"""

# ── Catálogo gestor_queries.py ────────────────────────────────────────────────
GESTOR_QUERIES_CATALOG_PROMPT = """
Catálogo gestor_queries.py — KPIs y análisis personal del gestor (requiere gestor_id):

- get_gestor_performance_enhanced(gestor_id, periodo) — KPIs completos: ingresos, gastos directos, gastos redistribuidos, margen, contratos, clientes
- calculate_roe_gestor_enhanced(gestor_id, periodo) — ROE del gestor: beneficio_neto / ingresos × 100; incluye gastos directos + redistribuidos
- compare_gestor_septiembre_octubre(gestor_id) — evolución sep→oct: variación en ingresos, gastos, margen, contratos
- get_cartera_completa_gestor_enhanced(gestor_id, fecha) — cartera completa: contratos activos con productos, clientes, métricas
- get_alertas_criticas_gestor(gestor_id, periodo) — alertas: MARGEN_BAJO, BAJA_DIVERSIFICACION, desviaciones
"""

# ── Catálogo incentive_queries.py ─────────────────────────────────────────────
INCENTIVE_QUERIES_CATALOG_PROMPT = """
Catálogo incentive_queries.py — cálculo de incentivos y cumplimiento de objetivos:

- calculate_incentivo_cumplimiento_objetivos_enhanced(periodo) — incentivo de todos los gestores basado en margen neto pct:
  >15% → 2% bonus | 10-15% → 1.5% | <10% → 0%
"""

# ── Catálogo period_queries.py ────────────────────────────────────────────────
PERIOD_QUERIES_CATALOG_PROMPT = """
Catálogo period_queries.py — métricas financieras consolidadas del grupo por período:

- get_periodo_metricas_financieras(periodo) — KPIs consolidados del banco: ingresos totales, gastos directos, gastos centrales,
  beneficio neto, margen neto pct, ROE grupo, total gestores activos, total contratos activos
- get_periodo_analisis_gastos(periodo) — desglose de gastos: directos por contrato + centrales redistribuidos por gestor
"""
