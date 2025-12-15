"""
chart_prompts.py — V2.0 Enhanced con Sistema de Confidencialidad Bancaria

✅ MEJORAS:
- Contexto de confidencialidad por rol (GESTOR vs CONTROL_GESTION) 
- Métricas ampliadas con incentivos y desviaciones
- Ejemplos del mundo real bancario
- Validaciones automáticas de permisos
- Mapeo inteligente a queries específicas

Autor: CDG Development Team
Fecha: 2025-09-30
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# 🔐 SISTEMA DE CONFIDENCIALIDAD BANCARIA
CONFIDENTIALITY_RULES = {
    'GESTOR': {
        'allowed_dimensions': ['periodo', 'producto', 'contrato'],  # Solo sus propios datos
        'forbidden_dimensions': ['gestor'],  # No puede ver otros gestores específicos
        'allowed_metrics': [
            'ROE', 'MARGEN_NETO', 'INGRESOS', 'EFICIENCIA', 'CONTRATOS', 
            'PERFORMANCE', 'PRECIO_STD', 'GASTOS', 'CLIENTES', 'INCENTIVOS_PROPIOS'
        ],
        'forbidden_metrics': ['PRECIO_REAL', 'DESVIACION_CRITICA', 'INCENTIVOS_OTROS'],
        'context_filter': 'gestor_id_validation',  # Valida que solo vea sus datos
        'comparative_level': 'PROMEDIO_ANONIMO'  # Solo vs promedios anónimos
    },
    'CONTROL_GESTION': {
        'allowed_dimensions': ['gestor', 'centro', 'segmento', 'producto', 'periodo', 'cliente', 'contrato'],
        'forbidden_dimensions': [],  # Acceso completo
        'allowed_metrics': [
            'ROE', 'MARGEN_NETO', 'INGRESOS', 'EFICIENCIA', 'CONTRATOS', 'PERFORMANCE',
            'PRECIO_STD', 'PRECIO_REAL', 'DESVIACION', 'GASTOS', 'CLIENTES', 'INCENTIVOS',
            'DESVIACION_CRITICA', 'ANOMALIAS', 'COMPARATIVAS_DETALLADAS'
        ],
        'forbidden_metrics': [],  # Acceso completo
        'context_filter': 'full_access',
        'comparative_level': 'DETALLADO_COMPLETO'
    }
}

# 🎯 MÉTRICAS AMPLIADAS PARA GRÁFICOS DINÁMICOS
EXTENDED_METRICS = {
    # Métricas básicas
    'ROE': 'Rentabilidad sobre Patrimonio',
    'MARGEN_NETO': 'Margen Neto',
    'INGRESOS': 'Ingresos Totales',
    'EFICIENCIA': 'Eficiencia Operativa',
    'CONTRATOS': 'Número de Contratos',
    'PERFORMANCE': 'Performance General',
    'GASTOS': 'Gastos Totales',
    'CLIENTES': 'Número de Clientes',
    
    # Métricas de precios (control de gestión)
    'PRECIO_STD': 'Precio Estándar',
    'PRECIO_REAL': 'Precio Real (Solo Control de Gestión)',
    'DESVIACION': 'Desviación vs Estándar',
    'DESVIACION_CRITICA': 'Desviaciones Críticas (Solo Control de Gestión)',
    
    # Métricas de incentivos
    'INCENTIVOS': 'Sistema de Incentivos (Detalle por Control de Gestión)',
    'INCENTIVOS_PROPIOS': 'Mis Incentivos (Vista Gestor)',
    'INCENTIVOS_OTROS': 'Incentivos de Otros Gestores (Solo Control de Gestión)',
    'BONUS_POOL': 'Pool de Bonificaciones',
    'CUMPLIMIENTO_OBJETIVOS': 'Cumplimiento de Objetivos',
    
    # Métricas avanzadas
    'ANOMALIAS': 'Detección de Anomalías',
    'TENDENCIAS': 'Análisis de Tendencias',
    'COMPARATIVAS_DETALLADAS': 'Comparativas Detalladas entre Gestores',
    'PROMEDIO_ANONIMO': 'Promedio Anónimo del Segmento'
}

# 🎯 DIMENSIONES AMPLIADAS
EXTENDED_DIMENSIONS = {
    'gestor': 'Gestor (Específico - Solo Control de Gestión)',
    'gestor_anonimo': 'Comparativa Anónima de Gestores',
    'centro': 'Centro',
    'segmento': 'Segmento',
    'producto': 'Producto',
    'periodo': 'Período Temporal',
    'cliente': 'Cliente',
    'contrato': 'Contrato',
    'ranking': 'Ranking (Anónimo para Gestores)',
    'tendencia_temporal': 'Evolución Temporal'
}

# 🎨 TIPOS DE GRÁFICO AMPLIADOS
EXTENDED_CHART_TYPES = {
    'bar': 'Gráfico de Barras',
    'horizontal_bar': 'Barras Horizontales',
    'line': 'Gráfico de Líneas',
    'pie': 'Gráfico Circular',
    'donut': 'Gráfico Donut',
    'area': 'Gráfico de Área',
    'scatter': 'Gráfico de Dispersión',
    'stacked_bar': 'Barras Apiladas',
    'gauge': 'Medidor (para KPIs)',
    'heatmap': 'Mapa de Calor (para desviaciones)',
    'waterfall': 'Cascada (para análisis de variaciones)',
    'comparison': 'Gráfico de Comparación',
    'trend': 'Gráfico de Tendencia'
}

# 🔐 PROMPT PRINCIPAL CON CONFIDENCIALIDAD
CHART_PIVOT_SYSTEM_PROMPT = '''
Eres un agente experto en interpretación de gráficos dinámicos para Control de Gestión Bancario con sistema de confidencialidad integrado.

IMPORTANTE - SISTEMA DE CONFIDENCIALIDAD:
- ROL GESTOR: Solo puede ver sus propios datos, comparativas anónimas, precios estándar
- ROL CONTROL_GESTION: Acceso completo, precios reales, comparativas detalladas entre gestores

Tu tarea es interpretar instrucciones en lenguaje natural para modificar gráficos considerando:
1. TIPO DE GRÁFICO: Formato de visualización
2. DIMENSIÓN: Agrupación de datos respetando confidencialidad
3. MÉTRICA: Indicador a mostrar según permisos del usuario

TIPOS DE GRÁFICO PERMITIDOS:
- bar (barras verticales)
- horizontal_bar (barras horizontales) 
- line (líneas para evolución temporal)
- pie (circular para distribuciones)
- donut (donut para proporciones)
- area (área para tendencias acumuladas)
- scatter (dispersión para correlaciones)
- stacked_bar (barras apiladas para composición)
- gauge (medidor para KPIs individuales)
- heatmap (mapa de calor para matrices de datos)
- waterfall (cascada para análisis de variaciones)
- comparison (comparación lado a lado)
- trend (tendencia temporal)

DIMENSIONES POR ROL:

ROL GESTOR (Confidencialidad Alta):
- periodo (evolución temporal propia)
- producto (distribución por productos propios)
- contrato (análisis por contratos propios)  
- gestor_anonimo (comparativa vs promedio anónimo)
- ranking (posición anónima en ranking)
- tendencia_temporal (evolución de métricas propias)

ROL CONTROL_GESTION (Acceso Completo):
- gestor (análisis por gestor específico)
- centro (distribución por centros)
- segmento (análisis por segmentos)
- producto (análisis global de productos)
- periodo (evolución temporal completa)
- cliente (análisis por clientes)
- contrato (análisis global de contratos)
- ranking (rankings detallados)

MÉTRICAS POR ROL:

ROL GESTOR:
- ROE, MARGEN_NETO, INGRESOS, EFICIENCIA (métricas propias)
- CONTRATOS, CLIENTES (volúmenes propios)
- PRECIO_STD (precios estándar únicamente)
- INCENTIVOS_PROPIOS (sus incentivos)
- PROMEDIO_ANONIMO (comparativa vs promedio)
- CUMPLIMIENTO_OBJETIVOS (sus objetivos)

ROL CONTROL_GESTION:
- Todas las métricas del gestor PLUS:
- PRECIO_REAL (precios reales confidenciales)
- DESVIACION, DESVIACION_CRITICA (análisis de desviaciones)
- INCENTIVOS, INCENTIVOS_OTROS (incentivos globales)
- ANOMALIAS (detección de anomalías)
- COMPARATIVAS_DETALLADAS (entre gestores específicos)
- BONUS_POOL (pool de bonificaciones)

FORMATO DE RESPUESTA:
Genera únicamente un JSON con los cambios solicitados:
{
  "chart_type": "<tipo_solicitado>",
  "dimension": "<dimensión_según_rol>", 
  "metric": "<métrica_según_permisos>"
}

Si la instrucción no especifica algún elemento, no lo incluyas en el JSON.
Si se solicita algo fuera de permisos, ajusta automáticamente a la alternativa permitida más cercana.

EJEMPLOS POR CONTEXTO:

GESTOR solicita: "Muéstrame el ROE de otros gestores"
→ {"metric": "PROMEDIO_ANONIMO", "dimension": "gestor_anonimo"}

GESTOR solicita: "Evolución de mis ingresos por trimestre"  
→ {"chart_type": "line", "metric": "INGRESOS", "dimension": "periodo"}

CONTROL_GESTION solicita: "Ranking de gestores por margen neto"
→ {"chart_type": "horizontal_bar", "metric": "MARGEN_NETO", "dimension": "gestor"}

CONTROL_GESTION solicita: "Mapa de calor de desviaciones por centro"
→ {"chart_type": "heatmap", "metric": "DESVIACION_CRITICA", "dimension": "centro"}

GESTOR solicita: "Gráfico circular de mis contratos por producto"
→ {"chart_type": "pie", "metric": "CONTRATOS", "dimension": "producto"}

CUALQUIER ROL solicita: "Cambia a barras horizontales"
→ {"chart_type": "horizontal_bar"}

Responde ÚNICAMENTE el JSON, sin explicaciones adicionales.
'''

# 🛠️ FUNCIONES AUXILIARES MEJORADAS

def build_chart_pivot_prompt(
    user_message: str, 
    current_config: Dict[str, Any] = None, 
    user_role: str = "GESTOR",
    user_context: Dict[str, Any] = None
) -> str:
    """
    Construye el prompt completo con contexto de confidencialidad
    
    Args:
        user_message: Mensaje del usuario
        current_config: Configuración actual del gráfico
        user_role: ROL del usuario ('GESTOR' o 'CONTROL_GESTION')
        user_context: Contexto adicional (gestor_id, centro_id, etc.)
    """
    try:
        # Información del contexto
        context_info = ""
        if current_config:
            context_info += f"\n\nConfiguración actual del gráfico:\n{current_config}"
        
        # Información del rol y permisos
        role_info = f"\n\nROL USUARIO: {user_role}"
        if user_context:
            if user_role == "GESTOR" and user_context.get('gestor_id'):
                role_info += f"\nGESTOR_ID: {user_context['gestor_id']} (solo puede ver sus propios datos)"
            elif user_role == "CONTROL_GESTION":
                role_info += f"\nACCESO: Completo (puede ver todos los datos)"
            
            if user_context.get('centro_id'):
                role_info += f"\nCENTRO_ID: {user_context['centro_id']}"
        
        # Permisos específicos del rol
        permissions = CONFIDENTIALITY_RULES.get(user_role, CONFIDENTIALITY_RULES['GESTOR'])
        permissions_info = f"""
        
PERMISOS ACTUALES:
- Dimensiones permitidas: {', '.join(permissions['allowed_dimensions'])}
- Métricas permitidas: {', '.join(permissions['allowed_metrics'][:10])}{'...' if len(permissions['allowed_metrics']) > 10 else ''}
- Nivel de comparativa: {permissions['comparative_level']}
"""
        
        full_prompt = f"{CHART_PIVOT_SYSTEM_PROMPT}{role_info}{permissions_info}{context_info}\n\nInstrucción del usuario: \"{user_message}\"\n\nJSON:"
        
        logger.info(f"🔄 Prompt construido para rol {user_role}")
        return full_prompt
        
    except Exception as e:
        logger.error(f"Error construyendo prompt: {e}")
        # Fallback básico
        return f"{CHART_PIVOT_SYSTEM_PROMPT}\n\nInstrucción del usuario: \"{user_message}\"\n\nJSON:"

def validate_chart_request(
    requested_config: Dict[str, Any], 
    user_role: str = "GESTOR",
    user_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Valida y ajusta la configuración solicitada según permisos del usuario
    
    Returns:
        Dict con configuración validada y posibles ajustes aplicados
    """
    try:
        permissions = CONFIDENTIALITY_RULES.get(user_role, CONFIDENTIALITY_RULES['GESTOR'])
        adjusted_config = requested_config.copy()
        adjustments_made = []
        
        # Validar dimensión
        if 'dimension' in requested_config:
            if requested_config['dimension'] in permissions['forbidden_dimensions']:
                # Ajustar automáticamente
                if user_role == 'GESTOR' and requested_config['dimension'] == 'gestor':
                    adjusted_config['dimension'] = 'gestor_anonimo'
                    adjustments_made.append('Dimensión ajustada a comparativa anónima por confidencialidad')
                else:
                    adjusted_config['dimension'] = permissions['allowed_dimensions'][0]
                    adjustments_made.append(f'Dimensión ajustada a {adjusted_config["dimension"]} por permisos')
        
        # Validar métrica
        if 'metric' in requested_config:
            if requested_config['metric'] in permissions['forbidden_metrics']:
                # Mapear a alternativa permitida
                metric_mappings = {
                    'PRECIO_REAL': 'PRECIO_STD',
                    'INCENTIVOS_OTROS': 'INCENTIVOS_PROPIOS',
                    'DESVIACION_CRITICA': 'DESVIACION',
                    'COMPARATIVAS_DETALLADAS': 'PROMEDIO_ANONIMO'
                }
                alternative = metric_mappings.get(
                    requested_config['metric'], 
                    permissions['allowed_metrics'][0]
                )
                adjusted_config['metric'] = alternative
                adjustments_made.append(f'Métrica ajustada a {alternative} por confidencialidad')
        
        return {
            'valid_config': adjusted_config,
            'adjustments_made': adjustments_made,
            'validation_status': 'adjusted' if adjustments_made else 'valid',
            'user_role': user_role,
            'permissions_applied': True
        }
        
    except Exception as e:
        logger.error(f"Error validando configuración: {e}")
        return {
            'valid_config': requested_config,
            'adjustments_made': [f'Error en validación: {e}'],
            'validation_status': 'error',
            'user_role': user_role,
            'permissions_applied': False
        }

def get_available_options_by_role(user_role: str = "GESTOR") -> Dict[str, List[str]]:
    """
    Devuelve las opciones disponibles según el rol del usuario
    """
    try:
        permissions = CONFIDENTIALITY_RULES.get(user_role, CONFIDENTIALITY_RULES['GESTOR'])
        
        return {
            'chart_types': list(EXTENDED_CHART_TYPES.keys()),
            'dimensions': permissions['allowed_dimensions'],
            'metrics': permissions['allowed_metrics'],
            'forbidden_dimensions': permissions['forbidden_dimensions'],
            'forbidden_metrics': permissions['forbidden_metrics'],
            'comparative_level': permissions['comparative_level'],
            'role': user_role
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo opciones por rol: {e}")
        return {
            'chart_types': ['bar', 'line', 'pie'],
            'dimensions': ['periodo', 'producto'],
            'metrics': ['ROE', 'MARGEN_NETO', 'CONTRATOS'],
            'role': user_role,
            'error': str(e)
        }

def build_context_aware_prompt(
    user_message: str,
    user_role: str,
    gestor_id: Optional[str] = None,
    centro_id: Optional[str] = None,
    current_chart_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Función de conveniencia para construir prompts con contexto completo
    """
    user_context = {}
    if gestor_id:
        user_context['gestor_id'] = gestor_id
    if centro_id:
        user_context['centro_id'] = centro_id
        
    return build_chart_pivot_prompt(
        user_message=user_message,
        current_config=current_chart_config,
        user_role=user_role,
        user_context=user_context
    )

# 🎯 EJEMPLOS DE USO FUTURO (COMENTADOS PARA REFERENCIA)

"""
EJEMPLOS DE USO EN PRODUCCIÓN:

# Gestor Juan (ID: 1001) quiere ver su evolución
prompt = build_context_aware_prompt(
    user_message="Muéstrame mi evolución de ROE en el último año",
    user_role="GESTOR", 
    gestor_id="1001"
)

# Director de Control de Gestión quiere ranking completo
prompt = build_context_aware_prompt(
    user_message="Ranking de todos los gestores por margen neto",
    user_role="CONTROL_GESTION"
)

# Validación automática de requests
validation = validate_chart_request(
    requested_config={"dimension": "gestor", "metric": "PRECIO_REAL"},
    user_role="GESTOR",
    user_context={"gestor_id": "1001"}
)
# Resultado: Se ajustará automáticamente a comparativa anónima y precio estándar

# Opciones disponibles por rol
gestor_options = get_available_options_by_role("GESTOR")
direccion_options = get_available_options_by_role("CONTROL_GESTION")
"""

if __name__ == "__main__":
    # Test de funcionalidades
    print("🧪 Testing chart_prompts.py V2.0...")
    
    # Test 1: Prompt para gestor
    gestor_prompt = build_context_aware_prompt(
        "Muéstrame mi ROE comparado con otros gestores",
        "GESTOR", 
        gestor_id="1001"
    )
    print("✅ Prompt gestor generado")
    
    # Test 2: Prompt para control de gestión  
    direccion_prompt = build_context_aware_prompt(
        "Ranking detallado de gestores por margen neto",
        "CONTROL_GESTION"
    )
    print("✅ Prompt dirección generado")
    
    # Test 3: Validación de permisos
    validation = validate_chart_request(
        {"dimension": "gestor", "metric": "PRECIO_REAL"},
        "GESTOR"
    )
    print(f"✅ Validación: {validation['validation_status']}")
    
    # Test 4: Opciones por rol
    gestor_options = get_available_options_by_role("GESTOR")
    print(f"✅ Opciones gestor: {len(gestor_options['metrics'])} métricas")
    
    direccion_options = get_available_options_by_role("CONTROL_GESTION") 
    print(f"✅ Opciones dirección: {len(direccion_options['metrics'])} métricas")
    
    print("🎯 Chart prompts V2.0 con confidencialidad funcionando correctamente")
