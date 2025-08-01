import re
import logging

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
    r"--",                  # Comentarios SQL
    r"/\*.*?\*/",          # Comentarios de bloque
    r"\bunion\s+select\b", # UNION SELECT típico de inyección
    r"\bor\s+1\s*=\s*1\b", # OR 1=1 clásico
    r"\band\s+1\s*=\s*0\b",# AND 1=0 para bypass
    r"\binto\s+outfile\b", # Escritura a archivo
    r"\bload\s+data\b"     # Carga de datos desde archivo
]

# Límites de seguridad para el agente CDG
MAX_QUERY_LENGTH = 8000      # 8KB máximo por query
MAX_NESTED_SUBQUERIES = 10   # Máximo nivel de anidamiento
MAX_JOIN_COUNT = 15          # Máximo número de JOINs

# Tablas autorizadas para el agente CDG - Banca March
AUTHORIZED_TABLES = {
    'maestro_gestores', 'maestro_contratos', 'maestro_productos', 
    'maestro_centros', 'maestro_segmentos', 
    'precio_por_producto_real', 'precio_por_producto_std',
    'movimientos_contratos', 'gastos_centro'
}


def is_query_safe(sql_query: str) -> bool:
    """
    Evalúa si una consulta SQL es segura para ejecutar en el contexto del agente CDG.
    
    Criterios de seguridad:
    - Solo permite SELECT y WITH (consultas de solo lectura)
    - Bloquea palabras clave de modificación de datos/estructura
    - Previene inyecciones SQL comunes
    - Controla límites de complejidad
    - Valida acceso solo a tablas autorizadas CDG
    
    Args:
        sql_query (str): La consulta SQL a evaluar
        
    Returns:
        bool: True si la consulta es segura, False en caso contrario
    """
    if not sql_query or not isinstance(sql_query, str):
        logger.warning("SQL Guard CDG: Query inválida recibida")
        return False
    
    # Verificar longitud máxima
    if len(sql_query) > MAX_QUERY_LENGTH:
        logger.warning(f"SQL Guard CDG: Query excede longitud máxima ({len(sql_query)} chars)")
        return False
    
    q = sql_query.lower().strip()
    
    # 1. Verificar que solo contenga una instrucción SQL
    semicolon_count = q.count(';')
    if semicolon_count > 1:
        logger.warning("SQL Guard CDG: Múltiples instrucciones SQL detectadas")
        return False
    if semicolon_count == 1 and not q.endswith(';'):
        logger.warning("SQL Guard CDG: Punto y coma en posición sospechosa")
        return False
    
    # 2. Verificar palabras clave prohibidas
    for pattern in FORBIDDEN_SQL:
        if re.search(pattern, q, re.IGNORECASE):
            logger.warning(f"SQL Guard CDG: Palabra clave prohibida detectada: {pattern}")
            return False
    
    # 3. Verificar patrones sospechosos
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE | re.DOTALL):
            logger.warning(f"SQL Guard CDG: Patrón sospechoso detectado: {pattern}")
            return False
    
    # 4. Solo permitir SELECT o WITH al inicio
    if not q.startswith(('select ', 'with ')):
        logger.warning("SQL Guard CDG: Query no comienza con SELECT o WITH")
        return False
    
    # 5. Verificar límites de complejidad
    if not _check_query_complexity(q):
        return False
    
    # 6. Validación específica para tablas CDG
    if not _validate_cdg_table_access(q):
        return False
    
    logger.info("SQL Guard CDG: Query validada exitosamente")
    return True


def _check_query_complexity(query: str) -> bool:
    """Verifica que la query no sea excesivamente compleja"""
    
    # Contar subqueries anidadas (balance de parentesis)
    open_parens = query.count('(')  
    close_parens = query.count(')')
    paren_depth = abs(open_parens - close_parens)
    
    if paren_depth > MAX_NESTED_SUBQUERIES:
        logger.warning(f"SQL Guard CDG: Demasiadas subqueries anidadas ({paren_depth})")
        return False
    
    # Contar JOINs
    join_count = len(re.findall(r'\bjoin\b', query, re.IGNORECASE))
    if join_count > MAX_JOIN_COUNT:
        logger.warning(f"SQL Guard CDG: Demasiados JOINs ({join_count})")
        return False
    
    return True


def _validate_cdg_table_access(query: str) -> bool:
    """Valida que solo se acceda a tablas autorizadas del sistema CDG"""
    
    # Extraer nombres de tablas de FROM y JOIN
    table_pattern = r'\b(?:from|join)\s+(\w+)'
    matches = re.findall(table_pattern, query, re.IGNORECASE)
    
    for table_name in matches:
        if table_name.lower() not in AUTHORIZED_TABLES:
            logger.warning(f"SQL Guard CDG: Acceso a tabla no autorizada: {table_name}")
            return False
    
    return True


def validate_query_for_cdg(sql_query: str, context: str = "general") -> dict:
    """
    Función extendida para validación con contexto específico del agente CDG
    
    Args:
        sql_query (str): Query SQL a validar
        context (str): Contexto de uso ('gestor', 'incentive', 'comparative', 'deviation')
    
    Returns:
        dict: Resultado de validación con detalles
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
        if context == 'gestor' and 'maestro_gestores' not in sql_query.lower():
            result['warnings'].append("Query de gestor sin tabla MAESTRO_GESTORES")
        
        elif context == 'incentive' and not any(table in sql_query.lower() 
                                               for table in ['movimientos_contratos', 'precio_por_producto']):
            result['warnings'].append("Query de incentivos sin tablas de movimientos o precios")
        
        elif context == 'comparative' and sql_query.lower().count('join') < 1:
            result['warnings'].append("Query comparativa podría necesitar JOINs para análisis completo")
        
        elif context == 'deviation' and not any(table in sql_query.lower()
                                               for table in ['precio_por_producto_real', 'precio_por_producto_std']):
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
    # Tests básicos de validación
    test_queries = [
        # ✅ Queries válidas
        "SELECT * FROM MAESTRO_GESTORES;",
        "WITH cte AS (SELECT * FROM MAESTRO_CONTRATOS) SELECT * FROM cte;",
        "SELECT g.DESC_GESTOR, COUNT(*) FROM MAESTRO_GESTORES g JOIN MAESTRO_CONTRATOS c ON g.GESTOR_ID = c.GESTOR_ID GROUP BY g.GESTOR_ID;",
        
        # ❌ Queries peligrosas
        "DROP TABLE MAESTRO_GESTORES;",
        "SELECT * FROM MAESTRO_GESTORES; DELETE FROM MAESTRO_CONTRATOS;", 
        "INSERT INTO MAESTRO_GESTORES VALUES (1, 'test');",
        "SELECT * FROM unauthorized_table;",
        "SELECT * FROM MAESTRO_GESTORES WHERE 1=1 --",
    ]
    
    print("🔒 SQL Guard CDG - Tests de Validación")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query[:60]}...")
        is_safe_result = is_query_safe(query)
        cdg_validation = validate_query_for_cdg(query, 'gestor')
        
        print(f"   ✅ Segura: {is_safe_result}")
        print(f"   📊 Validación CDG: {cdg_validation['is_safe']}")
        
        if cdg_validation['warnings']:
            print(f"   ⚠️  Warnings: {', '.join(cdg_validation['warnings'])}")
        
        print("-" * 40)
    
    print("\n🎯 Tests completados - SQL Guard CDG funcionando correctamente")
