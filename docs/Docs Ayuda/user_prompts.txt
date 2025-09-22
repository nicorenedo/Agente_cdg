BUSINESS_REVIEW_USER_PROMPT = """
Genera un Business Review completo para el gestor {gestor_name} correspondiente al período {periodo}.

## DATOS DISPONIBLES:

**KPIs Principales:**
{kpis}

**Alertas de Desviaciones:**
{alertas}

**Análisis Comparativo:**
{comparativa}

**Tendencias Históricas:**
{tendencias}

**Contexto Adicional:**
- Centro: {centro}
- Segmento: {segmento}
- Contratos gestionados: {total_contratos}

## ESTRUCTURA REQUERIDA:

### 1. RESUMEN EJECUTIVO
Síntesis de 150-200 palabras con situación actual, principales logros/alertas y conclusiones clave para decisiones inmediatas.

### 2. ANÁLISIS DE KPIS
Para cada KPI proporcionado:
- Valor actual y variación vs período anterior
- Posicionamiento vs benchmarks (centro/objetivo/promedio)
- Interpretación en contexto bancario

### 3. GESTIÓN DE ALERTAS
Si existen alertas de desviaciones:
- Clasificación por criticidad y impacto
- Análisis de causas probables
- Estimación de impacto económico

### 4. BENCHMARKING INTERNO
Análisis comparativo con pares:
- Posición relativa en rankings internos
- Identificación de gaps vs mejores prácticas
- Análisis de factores diferenciadores

### 5. EVOLUCIÓN TEMPORAL
Si hay datos de tendencias:
- Análisis de trayectoria de KPIs clave
- Identificación de patrones o cambios estructurales
- Proyección de tendencias actuales

### 6. RECOMENDACIONES ESTRATÉGICAS
Máximo 5 acciones priorizadas por impacto:
- Medidas comerciales específicas
- Optimizaciones operativas
- Objetivos para próximo período

Utiliza terminología bancaria precisa y lenguaje ejecutivo apropiado para directivos de Banca March. Si alguna sección carece de datos, indícalo claramente.
"""

EXECUTIVE_SUMMARY_USER_PROMPT = """
Elabora un Executive Summary para el Comité de Dirección sobre la situación de {num_gestores} gestores durante {periodo}.

## DATOS CONSOLIDADOS:
{datos_consolidados}

## FORMATO EJECUTIVO:

### SITUACIÓN GENERAL
Una frase síntesis del estado global

### PERFORMANCE DESTACADA
2-3 logros o tendencias positivas del período

### ALERTAS CRÍTICAS
Máximo 2 situaciones que requieren atención inmediata de la dirección

### OUTLOOK Y RECOMENDACIONES
Expectativas próximo período y acciones estratégicas prioritarias

Máximo 250 palabras. Lenguaje conciso para alta dirección, foco en decisiones estratégicas.
"""

DEVIATION_ANALYSIS_USER_PROMPT = """
Analiza la desviación crítica detectada en {contexto_desviacion} durante {periodo}.

## DATOS DE LA DESVIACIÓN:
{datos_desviacion}

## ANÁLISIS REQUERIDO:

### 1. DIAGNÓSTICO DE CAUSAS
Identifica las 2-3 causas más probables basándote en los datos proporcionados

### 2. CUANTIFICACIÓN DE IMPACTO
- Impacto mensual actual
- Proyección si persiste la tendencia
- Efecto en objetivos anuales

### 3. PLAN DE CORRECCIÓN
Propuesta de acciones inmediatas con:
- Medidas específicas
- Responsables sugeridos
- Timeline de implementación
- Métricas de seguimiento

Proporciona análisis técnico riguroso que permita decisiones correctivas inmediatas.
"""

COMPARATIVE_ANALYSIS_USER_PROMPT = """
Genera análisis comparativo entre gestores de {contexto_comparativo} durante {periodo}.

## DATOS PARA COMPARACIÓN:
{datos_comparativos}

## ANÁLISIS ESTRUCTURADO:

### 1. RANKING Y DISPERSIÓN
- Posiciones relativas por métrica principal
- Análisis de dispersión del grupo
- Identificación de outliers

### 2. FACTORES DIFERENCIADORES
Análisis top performers vs bottom performers:
- Patrones comerciales distintivos
- Eficiencias operativas diferenciales
- Factores de éxito replicables

### 3. MEJORES PRÁCTICAS
Del análisis de top performers:
- Estrategias comerciales exitosas
- Prácticas operativas destacadas
- Elementos replicables en el grupo

### 4. PLAN DE DESARROLLO
Para gestores con performance inferior:
- Acciones específicas de mejora
- Objetivos intermedios realizables
- Seguimiento y mentoring requerido

Identifica insights accionables para elevar la performance global mediante replicación de mejores prácticas.
"""

MONTHLY_CLOSING_USER_PROMPT = """
Genera el reporte de cierre mensual para {periodo} con foco en cumplimiento de objetivos presupuestarios anuales.

## DATOS DE CIERRE:
{datos_cierre}

**Contexto:** Mes {mes_numero}/12 del ejercicio {ejercicio}
**Objetivo Anual Pendiente:** {objetivo_pendiente}% sobre total anual
**Performance Acumulada:** {performance_acumulada}%

## ESTRUCTURA REQUERIDA:

### SITUACIÓN MENSUAL
- Resultados vs presupuesto mensual
- Principales desviaciones identificadas
- Factores explicativos de variaciones

### EVOLUCIÓN ACUMULADA
- Performance año vs objetivo anual
- Tendencia de convergencia/divergencia
- Análisis de estacionalidad

### PROYECCIÓN AL CIERRE
- Estimación de cierre del ejercicio
- Identificación de riesgos y oportunidades Q4
- Acciones correctivas recomendadas

Estructura el análisis con proyección al cierre del ejercicio y identificación de riesgos/oportunidades.
"""

# ============================================================================
# FUNCIÓN HELPER COMPLETA PARA CONSTRUCCIÓN DINÁMICA
# ============================================================================

def build_business_review_prompt(gestor_data: dict, kpi_data: dict, periodo: str, **kwargs) -> str:
    """
    Construye dinámicamente el prompt de Business Review con datos reales
    
    Args:
        gestor_data: Información del gestor
        kpi_data: KPIs calculados  
        periodo: Período del reporte
        **kwargs: Datos adicionales opcionales
        
    Returns:
        str: Prompt completo formateado
    """
    # Valores por defecto para evitar errores
    defaults = {
        'alertas': 'Sin alertas críticas detectadas',
        'comparativa': 'Datos comparativos no disponibles',
        'tendencias': 'Análisis de tendencias no disponible',
        'centro': gestor_data.get('desc_centro', 'Centro no especificado'),
        'segmento': gestor_data.get('desc_segmento', 'Segmento no especificado'),
        'total_contratos': kpi_data.get('total_contratos', 'No disponible')
    }
    
    # Combinar datos con defaults
    prompt_data = {
        'gestor_name': gestor_data.get('desc_gestor', 'Gestor'),
        'periodo': periodo,
        'kpis': _format_kpis_for_prompt(kpi_data),
        **defaults,
        **kwargs
    }
    
    return BUSINESS_REVIEW_USER_PROMPT.format(**prompt_data)

def build_executive_summary_prompt(datos_consolidados: dict, periodo: str, **kwargs) -> str:
    """Construye prompt para executive summary"""
    prompt_data = {
        'num_gestores': datos_consolidados.get('num_gestores', 'N/A'),
        'periodo': periodo,
        'datos_consolidados': _format_consolidated_data(datos_consolidados),
        **kwargs
    }
    
    return EXECUTIVE_SUMMARY_USER_PROMPT.format(**prompt_data)

def build_deviation_analysis_prompt(deviation_data: dict, periodo: str, **kwargs) -> str:
    """Construye prompt para análisis de desviaciones"""
    prompt_data = {
        'contexto_desviacion': deviation_data.get('contexto', 'desviación detectada'),
        'periodo': periodo,
        'datos_desviacion': _format_deviation_data(deviation_data),
        **kwargs
    }
    
    return DEVIATION_ANALYSIS_USER_PROMPT.format(**prompt_data)

def build_comparative_analysis_prompt(comparison_data: dict, periodo: str, **kwargs) -> str:
    """Construye prompt para análisis comparativo"""
    prompt_data = {
        'contexto_comparativo': comparison_data.get('contexto', 'gestores analizados'),
        'periodo': periodo,
        'datos_comparativos': _format_comparative_data(comparison_data),
        **kwargs
    }
    
    return COMPARATIVE_ANALYSIS_USER_PROMPT.format(**prompt_data)

def build_monthly_closing_prompt(datos_cierre: dict, periodo: str, **kwargs) -> str:
    """Construye prompt para cierre mensual"""
    mes_numero = periodo.split('-')[1] if '-' in periodo else '12'
    ejercicio = periodo.split('-')[0] if '-' in periodo else '2025'
    
    prompt_data = {
        'periodo': periodo,
        'mes_numero': mes_numero,
        'ejercicio': ejercicio,
        'datos_cierre': _format_closing_data(datos_cierre),
        'objetivo_pendiente': datos_cierre.get('objetivo_pendiente', 'N/A'),
        'performance_acumulada': datos_cierre.get('performance_acumulada', 'N/A'),
        **kwargs
    }
    
    return MONTHLY_CLOSING_USER_PROMPT.format(**prompt_data)

# ============================================================================
# FUNCIONES AUXILIARES PARA FORMATEO DE DATOS
# ============================================================================

def _format_kpis_for_prompt(kpi_data: dict) -> str:
    """Formatea KPIs para incluir en el prompt"""
    if not kpi_data:
        return "No hay KPIs disponibles para este gestor."
    
    kpi_lines = []
    for kpi, value in kpi_data.items():
        if isinstance(value, (int, float)):
            kpi_lines.append(f"- {kpi.replace('_', ' ').title()}: {value:.2f}")
        else:
            kpi_lines.append(f"- {kpi.replace('_', ' ').title()}: {value}")
    
    return "\n".join(kpi_lines)

def _format_consolidated_data(datos_consolidados: dict) -> str:
    """Formatea datos consolidados para executive summary"""
    if not datos_consolidados:
        return "Datos consolidados no disponibles."
    
    formatted_lines = []
    for key, value in datos_consolidados.items():
        if isinstance(value, (int, float)):
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted_lines)

def _format_deviation_data(deviation_data: dict) -> str:
    """Formatea datos de desviación para análisis"""
    if not deviation_data:
        return "Datos de desviación no disponibles."
    
    formatted_lines = []
    for key, value in deviation_data.items():
        if isinstance(value, (int, float)):
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted_lines)

def _format_comparative_data(comparison_data: dict) -> str:
    """Formatea datos comparativos para análisis"""
    if not comparison_data:
        return "Datos comparativos no disponibles."
    
    formatted_lines = []
    for key, value in comparison_data.items():
        if isinstance(value, (int, float)):
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted_lines)

def _format_closing_data(datos_cierre: dict) -> str:
    """Formatea datos de cierre mensual"""
    if not datos_cierre:
        return "Datos de cierre no disponibles."
    
    formatted_lines = []
    for key, value in datos_cierre.items():
        if isinstance(value, (int, float)):
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            formatted_lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted_lines)


# ============================================================================
# USER PROMPTS ESPECÍFICOS PARA CHAT_AGENT.PY
# ============================================================================

FEEDBACK_PROCESSING_USER_PROMPT = """
Analiza el siguiente feedback del usuario sobre la respuesta del agente CDG y extrae aprendizajes para mejorar futuras interacciones.

## INFORMACIÓN DE LA INTERACCIÓN:

**Usuario:** {user_id}
**Consulta Original:** {original_query}
**Respuesta Proporcionada:** {agent_response}
**Tipo de Análisis:** {response_type}

## FEEDBACK DEL USUARIO:

**Valoración:** {rating} (escala 1-5)
**Comentarios:** {feedback_text}
**Aspectos Específicos:**
- Claridad: {clarity_feedback}
- Utilidad: {usefulness_feedback}
- Formato: {format_feedback}
- Nivel de detalle: {detail_feedback}

## ANÁLISIS REQUERIDO:

### 1. IDENTIFICACIÓN DE PATRONES
- ¿Qué aspectos específicos valora positivamente el usuario?
- ¿Qué elementos requieren mejora sistemática?
- ¿Hay preferencias particulares sobre formato o estilo?

### 2. CLASIFICACIÓN DEL FEEDBACK
- Tipo: [Técnico/Presentación/Contenido/Navegación]
- Prioridad: [Alta/Media/Baja] según impacto en experiencia
- Aplicabilidad: [Individual/Grupal/General]

### 3. RECOMENDACIONES DE MEJORA
- Ajustes inmediatos para este usuario específico
- Cambios generales aplicables a usuarios similares
- Optimizaciones del sistema de respuestas

### 4. APRENDIZAJES EXTRAÍBLES
- Preferencias de comunicación del usuario
- Patrones de uso identificados
- Oportunidades de personalización

Enfócate en extraer insights accionables que mejoren la calidad de futuras interacciones sin comprometer la objetividad del análisis financiero.
"""

CONVERSATION_CONTEXT_USER_PROMPT = """
Mantén el contexto conversacional para proporcionar una respuesta coherente y contextualizada en esta interacción del sistema CDG.

## CONTEXTO DE LA CONVERSACIÓN:

**Usuario:** {user_id}
**Historial Reciente:**
{conversation_history}

**Consulta Actual:** {current_message}

## INFORMACIÓN CONTEXTUAL DISPONIBLE:

**Datos del Usuario:**
- Rol: {user_role}
- Preferencias conocidas: {user_preferences}
- Interacciones previas: {interaction_count}

**Contexto Financiero:**
- Último período consultado: {last_period}
- Gestor de interés: {current_gestor}
- Análisis previos: {previous_analyses}

## INSTRUCCIONES DE RESPUESTA:

### 1. CONTINUIDAD CONVERSACIONAL
- Referencia adecuadamente la información previa cuando sea relevante
- Mantén coherencia con análisis anteriores de la misma sesión
- Identifica si la consulta es continuación o nueva línea de análisis

### 2. ADAPTACIÓN CONTEXTUAL
- Ajusta el nivel de detalle según lo establecido en la conversación
- Utiliza la terminología que ha resultado más clara para este usuario
- Considera las preferencias de formato expresadas previamente

### 3. GESTIÓN DE INFORMACIÓN
- Si hay datos contradictorios con consultas anteriores, explícalo claramente
- Aprovecha información previamente calculada para agilizar respuestas
- Sugiere análisis complementarios basándote en el contexto

### 4. PERSONALIZACIÓN DINÁMICA
- Adapta el estilo comunicativo al demostrado por el usuario
- Incorpora las preferencias de visualización identificadas
- Mantén el nivel técnico apropiado establecido en la conversación

Proporciona una respuesta que se sienta natural como continuación de la conversación, aprovechando el contexto acumulado para añadir valor.
"""

PERSONALIZATION_LEARNING_USER_PROMPT = """
Analiza los patrones de interacción del usuario para identificar preferencias y optimizar la personalización del agente CDG.

## DATOS DE ANÁLISIS:

**Usuario:** {user_id}
**Período de Análisis:** {analysis_period}
**Total Interacciones:** {total_interactions}

## PATRONES DE USO IDENTIFICADOS:

**Consultas Frecuentes:**
{frequent_queries}

**Preferencias de Formato:**
{format_preferences}

**Nivel Técnico Demostrado:**
{technical_level}

**Horarios de Uso:**
{usage_patterns}

## MÉTRICAS DE SATISFACCIÓN:

**Valoraciones Promedio:** {average_rating}
**Feedback Recurrente:** {recurring_feedback}
**Tiempo de Interacción:** {interaction_duration}

## ANÁLISIS DE PERSONALIZACIÓN:

### 1. PERFIL DE USUARIO
- Nivel de experiencia en control de gestión: [Básico/Intermedio/Avanzado]
- Rol principal: [Gestor Comercial/Control Gestión/Directivo]
- Estilo comunicativo preferido: [Conciso/Detallado/Visual]

### 2. PREFERENCIAS IDENTIFICADAS
- **Visualización:** Tipos de gráficos más solicitados
- **Contenido:** Nivel de profundidad preferido en análisis
- **Formato:** Estructura de respuesta que genera mejor feedback
- **Timing:** Frecuencia y momentos preferidos de interacción

### 3. ÁREAS DE OPTIMIZACIÓN
- Ajustes en vocabulario técnico según nivel demostrado
- Modificaciones en formato de respuesta por defecto
- Personalización de dashboard inicial
- Adaptación de recomendaciones por rol

### 4. PLAN DE PERSONALIZACIÓN
- **Inmediato:** Ajustes aplicables desde la próxima interacción
- **Progresivo:** Mejoras graduales basadas en feedback continuo
- **Experimental:** Pruebas de nuevos enfoques según perfil

### 5. MÉTRICAS DE SEGUIMIENTO
- Indicadores para medir mejora en satisfacción
- Métricas de engagement y utilidad percibida
- Señales de éxito en personalización

Proporciona un plan de personalización específico que mejore la experiencia del usuario manteniendo la objetividad y calidad del análisis financiero.
"""

INTENT_CLARIFICATION_USER_PROMPT = """
El usuario ha enviado una consulta que requiere clarificación para proporcionar la respuesta más precisa y útil.

## CONSULTA ORIGINAL:
"{user_message}"

## CONTEXTO DISPONIBLE:
- Usuario: {user_id}
- Último análisis: {last_analysis_type}
- Datos disponibles: {available_data}

## POSIBLES INTERPRETACIONES IDENTIFICADAS:

{possible_interpretations}

## CLARIFICACIÓN REQUERIDA:

Solicita al usuario que especifique:

### 1. ALCANCE DEL ANÁLISIS
- ¿Se refiere a un gestor específico o análisis general?
- ¿Qué período temporal es de interés?
- ¿Busca datos actuales o comparativas históricas?

### 2. TIPO DE INFORMACIÓN
- ¿Requiere datos numéricos, análisis interpretativo o ambos?
- ¿Prefiere visualizaciones gráficas o formato texto?
- ¿Necesita nivel de detalle o resumen ejecutivo?

### 3. CONTEXTO DE USO
- ¿Es para análisis interno o presentación externa?
- ¿Requiere justificación técnica o conclusiones directas?
- ¿Hay deadline específico que condicione el formato?

Proporciona una respuesta amigable que guíe al usuario hacia una consulta más específica, ofreciendo opciones concretas basadas en las interpretaciones posibles y el contexto bancario de Banca March.
"""

DYNAMIC_DASHBOARD_USER_PROMPT = """
El usuario ha solicitado modificaciones dinámicas en la visualización del dashboard. Procesa la solicitud y genera la configuración apropiada.

## SOLICITUD DEL USUARIO:
"{user_request}"

## ESTADO ACTUAL DEL DASHBOARD:
**Gráficos Visibles:** {current_charts}
**KPIs Mostrados:** {current_kpis}
**Período:** {current_period}
**Filtros Activos:** {active_filters}

## DATOS DISPONIBLES:
{available_data}

## PROCESAMIENTO DE LA SOLICITUD:

### 1. ANÁLISIS DE LA MODIFICACIÓN
- Tipo de cambio solicitado: [Nuevo gráfico/Modificar existente/Cambiar período/Añadir filtro]
- Factibilidad técnica: [Posible/Requiere datos adicionales/No disponible]
- Impacto en visualización actual: [Sustitución/Adición/Reorganización]

### 2. CONFIGURACIÓN DE GRÁFICO
Si se solicita nuevo gráfico o modificación:
- **Tipo:** [Barras/Líneas/Circular/Área/Combinado]
- **Datos:** [KPIs específicos/Comparativas/Evolución temporal]
- **Dimensiones:** [Por gestor/Por centro/Por producto/Temporal]
- **Filtros:** [Período/Segmento/Umbral]

### 3. RESPUESTA AL USUARIO
Confirma la modificación con:
- Descripción clara del cambio aplicado
- Explicación de los datos mostrados
- Opciones adicionales disponibles
- Sugerencias de análisis complementarios

### 4. PERSISTENCIA
- ¿Guardar configuración como preferencia personal?
- ¿Aplicar a futuras sesiones por defecto?
- ¿Crear vista personalizada nombrada?

Proporciona una respuesta que confirme la modificación, explique brevemente los datos mostrados y sugiera análisis complementarios que puedan ser de valor.
"""

ESCALATION_HANDLING_USER_PROMPT = """
El usuario ha expresado una necesidad que excede las capacidades actuales del agente CDG o requiere intervención humana especializada.

## SITUACIÓN IDENTIFICADA:
**Tipo de Escalación:** {escalation_type}
**Consulta Original:** {original_query}
**Motivo:** {escalation_reason}

## CONTEXTO DEL USUARIO:
- ID Usuario: {user_id}
- Rol: {user_role}
- Urgencia expresada: {urgency_level}

## TIPOS DE ESCALACIÓN DISPONIBLES:

### 1. TÉCNICA
- Problema con datos o cálculos específicos
- Solicitud de análisis no contemplado en el sistema
- Error en funcionalidad del agente

### 2. FUNCIONAL
- Necesidad de autorización para acceso a datos
- Solicitud de modificación de permisos
- Requerimiento de nueva funcionalidad

### 3. DE NEGOCIO
- Interpretación especializada requerida
- Decisión estratégica que excede capacidades del agente
- Análisis de impacto regulatorio o legal

## RESPUESTA DE ESCALACIÓN:

### 1. RECONOCIMIENTO
- Confirmación de que se entiende la necesidad
- Explicación clara de por qué requiere escalación
- Estimación de tiempo de respuesta esperado

### 2. INFORMACIÓN DE CONTACTO
- Departamento apropiado según tipo de consulta
- Persona de contacto si está identificada
- Canales alternativos de comunicación

### 3. ACCIONES INMEDIATAS
- Información parcial que sí puede proporcionar
- Análisis preparatorio para facilitar la consulta escalada
- Documentación de la consulta para seguimiento

### 4. SEGUIMIENTO
- Protocolo de seguimiento de la escalación
- Información que puede monitorear el agente
- Compromisos de actualización

Proporciona una respuesta empática que reconozca la limitación, dirija apropiadamente al usuario y ofrezca todo el soporte posible dentro de las capacidades disponibles.
"""

# ============================================================================
# FUNCIONES HELPER PARA CONSTRUCCIÓN DINÁMICA DE USER PROMPTS
# ============================================================================

def build_feedback_processing_prompt(
    user_id: str,
    original_query: str,
    agent_response: str,
    feedback_data: dict
) -> str:
    """
    Construye dinámicamente el prompt para procesamiento de feedback
    
    Args:
        user_id: ID del usuario que proporciona feedback
        original_query: Consulta original del usuario
        agent_response: Respuesta que proporcionó el agente
        feedback_data: Diccionario con el feedback estructurado
        
    Returns:
        str: Prompt completo formateado
    """
    defaults = {
        'rating': feedback_data.get('rating', 'No especificado'),
        'feedback_text': feedback_data.get('comments', 'Sin comentarios'),
        'clarity_feedback': feedback_data.get('clarity', 'No especificado'),
        'usefulness_feedback': feedback_data.get('usefulness', 'No especificado'),
        'format_feedback': feedback_data.get('format', 'No especificado'),
        'detail_feedback': feedback_data.get('detail_level', 'No especificado'),
        'response_type': feedback_data.get('response_type', 'general')
    }
    
    prompt_data = {
        'user_id': user_id,
        'original_query': original_query,
        'agent_response': agent_response,
        **defaults
    }
    
    return FEEDBACK_PROCESSING_USER_PROMPT.format(**prompt_data)

def build_conversation_context_prompt(
    user_id: str,
    current_message: str,
    conversation_history: list,
    user_context: dict
) -> str:
    """Construye prompt para mantener contexto conversacional"""
    context_data = {
        'user_id': user_id,
        'current_message': current_message,
        'conversation_history': _format_conversation_history(conversation_history),
        'user_role': user_context.get('role', 'Usuario'),
        'user_preferences': _format_user_preferences(user_context.get('preferences', {})),
        'interaction_count': len(conversation_history),
        'last_period': user_context.get('last_period', 'No especificado'),
        'current_gestor': user_context.get('current_gestor', 'No especificado'),
        'previous_analyses': _format_previous_analyses(conversation_history)
    }
    
    return CONVERSATION_CONTEXT_USER_PROMPT.format(**context_data)

def build_personalization_learning_prompt(
    user_id: str,
    analysis_period: str,
    user_analytics: dict
) -> str:
    """Construye prompt para análisis de personalización"""
    personalization_data = {
        'user_id': user_id,
        'analysis_period': analysis_period,
        'total_interactions': user_analytics.get('total_interactions', 0),
        'frequent_queries': _format_frequent_queries(user_analytics.get('queries', [])),
        'format_preferences': _format_preferences(user_analytics.get('formats', {})),
        'technical_level': user_analytics.get('technical_level', 'No determinado'),
        'usage_patterns': _format_usage_patterns(user_analytics.get('patterns', {})),
        'average_rating': user_analytics.get('average_rating', 'No disponible'),
        'recurring_feedback': _format_feedback(user_analytics.get('feedback', [])),
        'interaction_duration': user_analytics.get('avg_duration', 'No disponible')
    }
    
    return PERSONALIZATION_LEARNING_USER_PROMPT.format(**personalization_data)

def build_intent_clarification_prompt(
    user_message: str,
    user_id: str,
    context: dict
) -> str:
    """Construye prompt para clarificación de intenciones"""
    clarification_data = {
        'user_message': user_message,
        'user_id': user_id,
        'last_analysis_type': context.get('last_analysis', 'Ninguno'),
        'available_data': _format_available_data(context.get('data_sources', [])),
        'possible_interpretations': _format_interpretations(context.get('interpretations', []))
    }
    
    return INTENT_CLARIFICATION_USER_PROMPT.format(**clarification_data)

def build_dynamic_dashboard_prompt(
    user_request: str,
    current_state: dict,
    available_data: dict
) -> str:
    """Construye prompt para modificaciones dinámicas del dashboard"""
    dashboard_data = {
        'user_request': user_request,
        'current_charts': _format_current_charts(current_state.get('charts', [])),
        'current_kpis': _format_current_kpis(current_state.get('kpis', [])),
        'current_period': current_state.get('period', 'No especificado'),
        'active_filters': _format_active_filters(current_state.get('filters', {})),
        'available_data': _format_available_data_sources(available_data)
    }
    
    return DYNAMIC_DASHBOARD_USER_PROMPT.format(**dashboard_data)

# ============================================================================
# FUNCIONES AUXILIARES PARA FORMATEO DE DATOS
# ============================================================================

def _format_conversation_history(history: list) -> str:
    """Formatea el historial de conversación para el prompt"""
    if not history:
        return "No hay historial de conversación previo."
    
    formatted_history = []
    for i, interaction in enumerate(history[-5:], 1):  # Últimas 5 interacciones
        timestamp = interaction.get('timestamp', 'Sin fecha')
        user_msg = interaction.get('user_message', 'Sin mensaje')
        response_type = interaction.get('response_type', 'general')
        formatted_history.append(f"{i}. [{timestamp}] Usuario: {user_msg[:100]}... | Tipo respuesta: {response_type}")
    
    return "\n".join(formatted_history)

def _format_user_preferences(preferences: dict) -> str:
    """Formatea las preferencias del usuario"""
    if not preferences:
        return "No se han identificado preferencias específicas."
    
    pref_lines = []
    for key, value in preferences.items():
        pref_lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(pref_lines)

def _format_previous_analyses(history: list) -> str:
    """Formatea análisis previos realizados"""
    if not history:
        return "No hay análisis previos en esta sesión."
    
    analyses = [interaction.get('response_type', 'general') for interaction in history[-3:]]
    return ", ".join(set(analyses))

def _format_frequent_queries(queries: list) -> str:
    """Formatea las consultas más frecuentes"""
    if not queries:
        return "No hay suficientes datos para identificar patrones."
    
    return "\n".join([f"- {query}" for query in queries[:5]])

def _format_preferences(preferences: dict) -> str:
    """Formatea preferencias de formato"""
    if not preferences:
        return "No se han identificado preferencias de formato."
    
    return "\n".join([f"- {k}: {v}" for k, v in preferences.items()])

def _format_usage_patterns(patterns: dict) -> str:
    """Formatea patrones de uso"""
    if not patterns:
        return "No hay patrones identificados."
    
    return "\n".join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in patterns.items()])

def _format_feedback(feedback_list: list) -> str:
    """Formatea feedback recurrente"""
    if not feedback_list:
        return "No hay feedback recurrente disponible."
    
    return "\n".join([f"- {feedback}" for feedback in feedback_list[:3]])

def _format_available_data(data_sources: list) -> str:
    """Formatea fuentes de datos disponibles"""
    if not data_sources:
        return "No hay datos específicos disponibles."
    
    return ", ".join(data_sources)

def _format_interpretations(interpretations: list) -> str:
    """Formatea posibles interpretaciones"""
    if not interpretations:
        return "No se identificaron interpretaciones alternativas."
    
    formatted = []
    for i, interp in enumerate(interpretations, 1):
        formatted.append(f"{i}. {interp}")
    
    return "\n".join(formatted)

def _format_current_charts(charts: list) -> str:
    """Formatea gráficos actuales del dashboard"""
    if not charts:
        return "No hay gráficos activos."
    
    return ", ".join([chart.get('title', f'Gráfico {i}') for i, chart in enumerate(charts, 1)])

def _format_current_kpis(kpis: list) -> str:
    """Formatea KPIs actuales mostrados"""
    if not kpis:
        return "No hay KPIs específicos mostrados."
    
    return ", ".join(kpis)

def _format_active_filters(filters: dict) -> str:
    """Formatea filtros activos"""
    if not filters:
        return "No hay filtros activos."
    
    return ", ".join([f"{k}: {v}" for k, v in filters.items()])

def _format_available_data_sources(data: dict) -> str:
    """Formatea fuentes de datos disponibles para dashboard"""
    if not data:
        return "No hay datos adicionales disponibles."
    
    return "\n".join([f"- {k}: {len(v) if isinstance(v, list) else 'Disponible'}" for k, v in data.items()])


# =================================================================
# FUNCIONES DE PROMPTS PARA CHAT_AGENT.PY
# =================================================================

def build_intent_classification_prompt(user_message: str, context: dict = None) -> str:
    """
    Construye prompt para clasificar la intención del usuario en chat
    
    Args:
        user_message: Mensaje del usuario
        context: Contexto adicional (gestor_id, periodo, etc.)
    """
    
    context_text = ""
    if context:
        context_text = f"""
CONTEXTO ADICIONAL:
- GESTOR_ID: {context.get('gestor_id', 'No especificado')}
- PERIODO: {context.get('periodo', 'No especificado')}  
- USUARIO_PREVIO: {context.get('user_history', 'Primera consulta')}
"""
    
    return f"""
Analiza este mensaje del usuario y clasifica su intención principal:

MENSAJE: "{user_message}"

{context_text}

CATEGORÍAS DISPONIBLES:
- performance_analysis: Análisis de rendimiento individual
- comparative_analysis: Comparativas y benchmarking  
- deviation_detection: Alertas y anomalías
- incentive_analysis: Cálculos de incentivos
- business_review: Reportes ejecutivos
- executive_summary: Resúmenes para dirección
- general_inquiry: Consultas generales

RESPUESTA REQUERIDA:
Formato JSON: {{"intent": "categoría", "confidence": 0.0-1.0}}
"""

def build_natural_response_prompt(data_analysis: dict, user_context: dict) -> str:
    """
    Construye prompt para generar respuesta natural conversacional
    
    Args:
        data_analysis: Resultado del análisis de datos
        user_context: Contexto del usuario y conversación
    """
    
    user_level = user_context.get('user_level', 'intermedio')
    conversation_history = user_context.get('conversation_history', [])
    
    history_text = ""
    if conversation_history:
        recent_history = conversation_history[-3:]  # Últimas 3 interacciones
        history_text = f"""
HISTORIAL RECIENTE:
{chr(10).join([f"- {h.get('question', '')}: {h.get('summary', '')}" for h in recent_history])}
"""
    
    return f"""
Genera una respuesta conversacional natural basada en este análisis:

DATOS ANALIZADOS:
{data_analysis}

CONTEXTO DEL USUARIO:
- Nivel técnico: {user_level}
- Gestor ID: {user_context.get('gestor_id', 'No especificado')}
- Período de interés: {user_context.get('periodo', 'Actual')}

{history_text}

INSTRUCCIONES:
1. Responde de forma conversacional y profesional
2. Adapta el nivel técnico al usuario ({user_level})
3. Include insights accionables específicos
4. Mantén coherencia con el historial previo
5. Si hay desviaciones >15%, marca como críticas
6. Proporciona contexto bancario relevante

ESTRUCTURA SUGERIDA:
- Situación actual (qué está pasando)
- Análisis contextual (por qué es importante) 
- Recomendaciones específicas (qué hacer)

La respuesta debe ser directa, útil y orientada a la acción.
"""

def build_sql_generation_prompt(user_question: str, context: dict = None) -> str:
    """
    Construye prompt para generar SQL desde pregunta en lenguaje natural
    
    Args:
        user_question: Pregunta del usuario
        context: Contexto adicional para la query
    """
    
    context_filters = ""
    if context:
        if context.get('gestor_id'):
            context_filters += f"- Filtrar por GESTOR_ID = {context['gestor_id']}\n"
        if context.get('periodo'):
            context_filters += f"- Filtrar por período = '{context['periodo']}'\n"
        if context.get('centro'):
            context_filters += f"- Filtrar por centro = {context['centro']}\n"
    
    return f"""
Genera una consulta SQL para responder esta pregunta:

PREGUNTA: "{user_question}"

FILTROS DE CONTEXTO:
{context_filters if context_filters else "- Sin filtros específicos"}

ESQUEMA DE REFERENCIA:
- MAESTRO_GESTORES: GESTOR_ID, DESC_GESTOR, CENTRO, SEGMENTO_ID
- MAESTRO_CONTRATOS: CONTRATO_ID, GESTOR_ID, CLIENTE_ID, PRODUCTO_ID, FECHA_ALTA
- MOVIMIENTOS_CONTRATOS: FECHA, CONTRATO_ID, CUENTA_ID, IMPORTE, LINEA_CDR
- PRECIO_POR_PRODUCTO_REAL: SEGMENTO_ID, PRODUCTO_ID, PRECIO_MANTENIMIENTO_REAL
- PRECIO_POR_PRODUCTO_STD: SEGMENTO_ID, PRODUCTO_ID, PRECIO_MANTENIMIENTO

REGLAS IMPORTANTES:
1. Solo SQLite válido
2. Usar COALESCE() para valores NULL
3. ROUND(valor, 2) para decimales
4. Incluir campos descriptivos (DESC_GESTOR, DESC_CENTRO)
5. Para centros comerciales: IND_CENTRO_FINALISTA = 1

FORMATO DE RESPUESTA:
Devuelve ÚNICAMENTE la consulta SQL, sin explicaciones.
"""

def build_financial_explanation_prompt(sql_results: list, original_question: str, context: dict = None) -> str:
    """
    Construye prompt para explicar resultados financieros
    
    Args:
        sql_results: Resultados de la consulta SQL
        original_question: Pregunta original del usuario
        context: Contexto adicional
    """
    
    results_summary = f"Datos obtenidos: {len(sql_results)} registros" if sql_results else "Sin datos"
    
    context_text = ""
    if context:
        context_text = f"""
CONTEXTO DE NEGOCIO:
- Período analizado: {context.get('periodo', 'No especificado')}
- Alcance: {context.get('scope', 'General')}
- Usuario: {context.get('user_type', 'Gestor comercial')}
"""
    
    return f"""
Explica estos resultados financieros de forma clara y contextualizada:

PREGUNTA ORIGINAL: "{original_question}"

DATOS OBTENIDOS:
{sql_results}

{results_summary}

{context_text}

INSTRUCCIONES PARA LA EXPLICACIÓN:
1. **Interpretación**: Qué significan estos números
2. **Contexto bancario**: Por qué son importantes para Banca March  
3. **Comparación**: Cómo se sitúan vs objetivos/benchmarks
4. **Tendencias**: Si hay patrones o evoluciones relevantes
5. **Acciones**: Qué se puede hacer con esta información

CONSIDERACIONES ESPECIALES:
- ROE objetivo: 8-12% (sector bancario español)
- Margen neto objetivo: >15% 
- Desviaciones críticas: >15%
- Centros finalistas: 1-5 (comerciales)
- Segmentos prioritarios: Fondos (N20301), Personal (N10104)

Proporciona una explicación que un gestor comercial pueda entender y usar.
"""
