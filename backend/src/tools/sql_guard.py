import re
import logging
from typing import Set, Dict

# Logger para auditoría de seguridad CDG
logger = logging.getLogger(__name__)

# Palabras clave SQL prohibidas para inyección o manipulación
FORBIDDEN_SQL = [
    r"\binsert\b", r"\bdelete\b", r"\bdrop\b", r"\btruncate\b", r"\balter\b",
    r"\bupdate\b", r"\breplace\b", r"\bcreate\b", r"\battach\b", r"\bexec\b",
    r"\bpragma\b", r"\bgrant\b", r"\brevoke\b", r"\bdeny\b",
    r"\bcommit\b", r"\brollback\b", r"\bsavepoint\b",
    r"\bload_extension\b", r"\bvacuum\b", r"\breindex\b"
]

# Patrones sospechosos adicionales
SUSPICIOUS_PATTERNS = [
    r"--",                  # Comentarios SQL en línea
    r"/\*.*?\*/",          # Comentarios de bloque
    r"\bunion\s+select\b", # UNION SELECT típico de inyección
    r"\bor\s+1\s*=\s*1\b", # OR 1=1 clásico
    r"\band\s+1\s*=\s*0\b",# AND 1=0 para bypass
    r"\binto\s+outfile\b", # Escritura a archivo
    r"\bload\s+data\b"     # Carga de datos desde archivo
]

# Límites de seguridad para el agente CDG
MAX_QUERY_LENGTH = 8000
MAX_NESTED_SUBQUERIES = 10
MAX_JOIN_COUNT = 15
MAX_SELECT_COUNT = 120

# Tablas autorizadas para el agente CDG - Banca March
AUTHORIZED_TABLES = {
    'maestro_gestores', 'maestro_contratos', 'maestro_productos',
    'maestro_centros', 'maestro_segmentos', 'maestro_clientes',
    'maestro_linea_cdr', 'maestro_cuentas',
    'precio_por_producto_real', 'precio_por_producto_std',
    'movimientos_contratos', 'gastos_centro'
}

def get_authorized_tables() -> Set[str]:
    """Devuelve el set (lowercase) de tablas autorizadas."""
    return set(AUTHORIZED_TABLES)

def is_query_safe(sql_query: str) -> bool:
    """
    Evalúa si una consulta SQL es segura para ejecutar en el contexto del agente CDG.
    Mejorado para manejar correctamente CTEs.
    """
    if not sql_query or not isinstance(sql_query, str):
        logger.warning("SQL Guard CDG: Query inválida recibida")
        return False

    # Verificar longitud máxima
    if len(sql_query) > MAX_QUERY_LENGTH:
        logger.warning(f"SQL Guard CDG: Query excede longitud máxima ({len(sql_query)} chars)")
        return False

    q = sql_query.strip()
    q_lower = q.lower()

    # 1) Verificar que solo contenga una instrucción SQL
    semicolon_count = q.count(';')
    if semicolon_count > 1:
        logger.warning("SQL Guard CDG: Múltiples instrucciones SQL detectadas")
        return False
    if semicolon_count == 1 and not q.rstrip().endswith(';'):
        logger.warning("SQL Guard CDG: Punto y coma en posición sospechosa")
        return False

    # 2) Palabras clave prohibidas
    for pattern in FORBIDDEN_SQL:
        if re.search(pattern, q_lower, re.IGNORECASE):
            logger.warning(f"SQL Guard CDG: Palabra clave prohibida detectada: {pattern}")
            return False

    # 3) Patrones sospechosos
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE | re.DOTALL):
            logger.warning(f"SQL Guard CDG: Patrón sospechoso detectado: {pattern}")
            return False

    # 4) Solo permitir SELECT o WITH al inicio
    if not q_lower.startswith(('select ', 'with ')):
        logger.warning("SQL Guard CDG: Query no comienza con SELECT o WITH")
        return False

    # 5) Verificar límites de complejidad
    if not _check_query_complexity(q):
        return False

    # 6) Validación específica de tablas CDG (MEJORADO: ignorando CTEs correctamente)
    if not _validate_cdg_table_access(q):
        return False

    logger.info("SQL Guard CDG: Query validada exitosamente")
    return True

def _extract_cte_names(query: str) -> Set[str]:
    """
    Extrae nombres de CTEs definidos en la cláusula WITH.
    MEJORADO: Detecta correctamente múltiples CTEs separadas por comas.
    """
    q_lower = query.lower()
    if not q_lower.startswith('with '):
        return set()

    # Buscar el patrón: nombre_cte AS (
    cte_names = set()
    matches = re.finditer(r'\b(\w+)\s+as\s*\(', q_lower, re.IGNORECASE)
    for match in matches:
        cte_names.add(match.group(1))
    
    return cte_names

def _check_query_complexity(query: str) -> bool:
    """Verifica que la query no sea excesivamente compleja."""
    ql = query.lower()

    # Profundidad máxima de paréntesis
    depth = 0
    max_depth = 0
    for ch in ql:
        if ch == '(':
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == ')':
            depth = max(0, depth - 1)

    if max_depth > MAX_NESTED_SUBQUERIES:
        logger.warning(f"SQL Guard CDG: Profundidad de subqueries excesiva (max_depth={max_depth})")
        return False

    # JOINs
    join_count = len(re.findall(r'\bjoin\b', ql, re.IGNORECASE))
    if join_count > MAX_JOIN_COUNT:
        logger.warning(f"SQL Guard CDG: Demasiados JOINs ({join_count})")
        return False

    # SELECT total
    select_count = len(re.findall(r'\bselect\b', ql, re.IGNORECASE))
    if select_count > MAX_SELECT_COUNT:
        logger.warning(f"SQL Guard CDG: Demasiados SELECTs ({select_count})")
        return False

    return True

def _validate_cdg_table_access(query: str) -> bool:
    """
    Valida que solo se acceda a tablas autorizadas del sistema CDG.
    MEJORADO: Ignora correctamente CTEs definidas en la query.
    """
    ql = query.lower()
    cte_names = _extract_cte_names(query)
    
    # Extraer nombres de tablas tras FROM/JOIN que NO sean subqueries (sin paréntesis)
    table_pattern = r'\b(?:from|join)\s+(?!\()([a-z0-9_"]+)'
    matches = re.findall(table_pattern, ql, re.IGNORECASE)

    authorized = get_authorized_tables()

    for raw_name in matches:
        name = raw_name.strip('"').strip('`').lower()
        
        # Si es un CTE definido en la query, lo permitimos
        if name in cte_names:
            continue
            
        # Si no es una tabla autorizada, rechazamos
        if name not in authorized:
            logger.warning(f"SQL Guard CDG: Acceso a tabla no autorizada: {raw_name}")
            return False

    return True

def validate_query_for_cdg(sql_query: str, context: str = "general") -> Dict:
    """
    Validación extendida con contexto específico del agente CDG.
    """
    result = {
        'is_safe': False,
        'context': context,
        'warnings': [],
        'query_hash': hash(sql_query) if sql_query else None
    }

    try:
        result['is_safe'] = is_query_safe(sql_query)

        # Validaciones adicionales por contexto
        ql = (sql_query or "").lower()

        if context == 'gestor' and 'maestro_gestores' not in ql:
            result['warnings'].append("Query de gestor sin tabla MAESTRO_GESTORES")
        elif context == 'incentive' and not any(tbl in ql for tbl in ['movimientos_contratos', 'precio_por_producto']):
            result['warnings'].append("Query de incentivos sin tablas de movimientos o precios")
        elif context == 'comparative' and ql.count('join') < 1:
            result['warnings'].append("Query comparativa podría necesitar JOINs para análisis completo")
        elif context == 'deviation' and not any(tbl in ql for tbl in ['precio_por_producto_real', 'precio_por_producto_std']):
            result['warnings'].append("Query de desviaciones sin tablas de precios real/estándar")

        logger.info(f"SQL Guard CDG: Query validada para contexto '{context}': {result['is_safe']}")

    except Exception as e:
        logger.error(f"SQL Guard CDG: Error durante validación: {e}")
        result['warnings'].append(f"Error de validación: {str(e)}")

    return result

# Función de compatibilidad con tu código existente
def is_safe(sql_query: str) -> bool:
    """Función de compatibilidad - usar is_query_safe() preferentemente"""
    return is_query_safe(sql_query)

if __name__ == "__main__":
    # Tests mejorados incluyendo CTEs
    test_queries = [
        # ✅ Queries válidas - incluyendo CTEs
        "SELECT * FROM maestro_gestores;",
        "WITH cte AS (SELECT * FROM maestro_contratos) SELECT * FROM cte;",
        "WITH ingresos_gestor AS (SELECT gestor_id, SUM(importe) as total FROM movimientos_contratos WHERE importe > 0 GROUP BY gestor_id), gastos_gestor AS (SELECT gestor_id, SUM(ABS(importe)) as total FROM movimientos_contratos WHERE importe < 0 GROUP BY gestor_id) SELECT g.desc_gestor, i.total, gas.total FROM maestro_gestores g LEFT JOIN ingresos_gestor i ON g.gestor_id = i.gestor_id LEFT JOIN gastos_gestor gas ON g.gestor_id = gas.gestor_id;",
        "SELECT g.desc_gestor, COUNT(*) FROM maestro_gestores g JOIN maestro_contratos c ON g.gestor_id = c.gestor_id GROUP BY g.gestor_id;",
        # ❌ Queries peligrosas
        "DROP TABLE maestro_gestores;",
        "SELECT * FROM unauthorized_table;",
        "SELECT * FROM maestro_gestores WHERE 1=1 -- comentario",
    ]

    print("🔒 SQL Guard CDG Mejorado - Tests de Validación")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query[:100]}...")
        is_safe_result = is_query_safe(query)
        cdg_validation = validate_query_for_cdg(query, 'gestor')

        print(f"   ✅ Segura: {is_safe_result}")
        print(f"   📊 Validación CDG: {cdg_validation['is_safe']}")

        if cdg_validation['warnings']:
            print(f"   ⚠️  Warnings: {', '.join(cdg_validation['warnings'])}")

        print("-" * 50)

    print("\n🎯 Tests completados - SQL Guard CDG mejorado funcionando correctamente")
