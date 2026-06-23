# AGENT_CONTRACTS.md — Contratos de agentes CDG Intelligence v2

> Fecha: 2026-06-08 · Revisión 2 (incorpora `QueryRewriter`, `HITLValidator` y hooks AI Act)
> Cada agente declara su contrato: inputs, outputs, tools, activación, LLM calls, hooks compliance.
> Se actualiza al implementar cada agente durante la reconstrucción.
> Referencia: `docs/ARCHITECTURE_V2.md` §1 y `docs/AI_ACT_MAPPING.md` §3.

---

## Formato de contrato

```yaml
NombreAgente:
  inputs:               # campos de CDGState que lee
  outputs:              # campos de CDGState que escribe
  tools:                # tools que puede invocar
  activates_when:       # condición sobre state
  llm_calls: N          # 0, 1 o 2 (auditoría de coste)
  compliance_hooks:     # qué componentes AI Act intervienen
  ai_act_articles:      # artículos del AI Act que satisface
  errors:               # qué hacer si falla
  langsmith_tags:       # tags para filtrar en LangSmith
```

---

## QueryRewriter 🆕

```yaml
QueryRewriter:
  inputs:
    - user_message       # original
    - user_role
    - session_id          # para contexto conversacional
  outputs:
    - original_query     # = user_message
    - rewritten_query    # versión normalizada/expandida
    - query_rewriter_metadata:
        confidence: float
        changes: List[str]
        reasoning: str
    - intent (preliminar) # "in_scope" | "out_of_scope" | "ambiguous"
  tools: []
  activates_when: siempre (primer nodo del grafo, antes del Orchestrator)
  llm_calls: 1
  compliance_hooks:
    - sanitize_input         # heurísticas anti prompt-injection
  ai_act_articles:
    - Art. 12   # registro de original_query
    - Art. 15   # robustez (sanitización)
  langsmith_tags: ["query_rewriter", "preprocessing"]
  errors:
    - LLM timeout → usar user_message original como rewritten_query, log warning
    - input detectado como adversarial → marcar query_rewriter_metadata.flag="suspicious"
                                          y dejar que PolicyEnforcer decida
    - intent="out_of_scope" → grafo salta directo a NarratorAgent con mensaje educado
```

**Prompt:** `core/prompts/query_rewriter.j2`
**Archivo:** `core/graph/nodes/query_rewriter.py`

**Ejemplo de transformación:**

```
original_query:  "que tal va mi margen vs el mes pasado en abril"
rewritten_query: "¿Cuál es el margen neto del gestor en abril 2026 y cómo
                  se compara con marzo 2026?"
metadata:
  changes: ["expandido referencia temporal", "convertido a pregunta formal"]
  confidence: 0.92
```

---

## Orchestrator

```yaml
Orchestrator:
  inputs:
    - rewritten_query     # 🆕 ahora viene del QueryRewriter
    - user_role
    - gestor_id
    - periodo
  outputs:
    - intent              # "simple" | "compleja" | "forecast" | "knowledge"
    - requires_data       # bool
    - requires_forecast   # bool
    - requires_knowledge  # bool
    - trace_id            # LangSmith run_id
  tools: []
  activates_when: siempre tras QueryRewriter (intent != "out_of_scope")
  llm_calls: 1
  compliance_hooks: []
  ai_act_articles:
    - Art. 12             # categorización registrada
  langsmith_tags: ["orchestrator", "classification"]
  errors:
    - clasificación ambigua → default intent="simple", requires_data=True
    - LLM timeout → retry 1 vez, si falla → intent="simple" con log de warning
```

**Prompt:** `core/prompts/orchestrator.j2`
**Archivo:** `core/graph/orchestrator.py`

---

## PermissionAgent

```yaml
PermissionAgent:
  inputs:
    - user_role
    - gestor_id
    - intent
  outputs:
    - permissions_validated  # bool
    - access_level           # "read_own" | "read_all" | "denied"
    - permission_denied_reason
  tools: []
  activates_when: siempre (segundo nodo tras Orchestrator)
  llm_calls: 0
  compliance_hooks:
    - PolicyEnforcer.enforce()    # 🆕 invocado tras validar permisos básicos
  ai_act_articles:
    - Art. 9                # gestión de riesgos
    - Art. 14               # supervisión (acceso por rol)
  langsmith_tags: ["permissions", "security"]
  errors:
    - user_role desconocido → access_level="denied", reason="rol no reconocido"
    - gestor_id no existe → access_level="denied", reason="gestor no encontrado"
    - access_level="denied" → grafo salta directo a NarratorAgent con mensaje de error
```

**Lógica:**
- `control_gestion` → `read_all`
- `gestor` + `gestor_id` válido → `read_own`
- `gestor` sin `gestor_id` → `denied`
- `validator` → `read_all` con privilegios HITL adicionales 🆕

**Archivo:** `core/graph/nodes/permission_agent.py`

---

## ContextEnricher

```yaml
ContextEnricher:
  inputs:
    - rewritten_query
    - user_role
    - gestor_id
    - periodo
    - intent
  outputs:
    - enriched_context:
        periodo_info: {start, end, is_last_month, months_available}
        gestor_info: {nombre, centro, segmento, n_contratos}
        macro_context: {tipos_hipotecarios, ipc, impacto_por_producto}
        session_history: [últimos 3 mensajes]
  tools: []
  activates_when: intent in ["compleja", "forecast"]
  llm_calls: 0
  compliance_hooks: []
  ai_act_articles: []
  langsmith_tags: ["enrichment", "context"]
  errors:
    - gestor_id no encontrado → enriched_context.gestor_info = null
    - periodo fuera de rango → usar DEFAULT_PERIOD con warning
```

**Archivo:** `core/graph/nodes/context_enricher.py`

---

## DataAgent

```yaml
DataAgent:
  inputs:
    - rewritten_query
    - user_role
    - gestor_id
    - periodo
    - intent
    - access_level
    - enriched_context
  outputs:
    - raw_data: Dict[str, Any]
    - data_lineage: List[Dict]   # 🆕 lista de LineageItem
  tools:
    - select_query
    - execute_query
    - get_period_metadata
  activates_when: requires_data == True
  llm_calls: 1
  compliance_hooks:
    - LineageTracker.annotate_query_result()   # 🆕
  ai_act_articles:
    - Art. 10               # gobernanza del dato (linaje)
    - Art. 12               # log de query ejecutada
  langsmith_tags: ["data", "sql"]
  errors:
    - query retorna vacío → raw_data={}, data_lineage=[{empty:true,reason:...}]
    - SQL falla → propagar error a NarratorAgent con contexto
    - access_level="read_own" → todas las queries filtran por gestor_id automáticamente
```

**Prompt:** `core/prompts/data_agent.j2`
**Archivo:** `core/graph/nodes/data_agent.py`

---

## CalculationAgent

```yaml
CalculationAgent:
  inputs:
    - raw_data
    - data_lineage              # 🆕
    - periodo
    - enriched_context
  outputs:
    - calculated_kpis:
        margen_neto, margen_neto_pct, roe, eficiencia, semaforo,
        redistribucion, ingresos, gastos_directos, gastos_redistribuidos,
        beneficio, n_contratos, variacion_mom
    - effect_decomposition: Dict   # 🆕 cuando aplique (variación temporal o comparativa)
    - data_lineage: List[Dict]     # 🆕 enriquecido con cálculos derivados
  tools:
    - calc_margen_neto
    - calc_redistribucion
    - calc_semaforo
    - calc_kpis_completos
    - calc_comparativa_mom
    - decompose_effects         # 🆕 EffectDecomposer
  activates_when: requires_data == True AND raw_data is not empty
  llm_calls: 0
  compliance_hooks:
    - EffectDecomposer.decompose_effects()   # 🆕 cuando intent="compleja" con comparativa
  ai_act_articles:
    - Art. 10               # lineage propagado
    - Art. 13               # transparencia (descomposición de efectos)
  langsmith_tags: ["calculation", "business_logic"]
  errors:
    - raw_data vacío → calculated_kpis={} flag "sin datos para período"
    - división por cero → safe_divide, devolver 0.0 con warning
    - decompose_effects falla con datos insuficientes → effect_decomposition=null, no error
```

**Todas las fórmulas leen de `config/business_rules.py`.** Sin hardcoding.

**Archivo:** `core/graph/nodes/calculation_agent.py`
**Lógica:** `data/calculator.py`
**Tool nueva:** `core/tools/effect_decomposer.py`

---

## ForecastAgent

```yaml
ForecastAgent:
  inputs:
    - rewritten_query
    - user_role
    - gestor_id
    - periodo
    - enriched_context
  outputs:
    - forecast_data: Dict
    - scenarios: List[Dict]
    - whatif_params: Dict
    - data_lineage: List[Dict]   # 🆕 propaga lineage de los datos de entrada
  tools:
    - get_forecast_base
    - apply_whatif
    - compare_scenarios
    - get_macro_context
    - get_recommendations
  activates_when: requires_forecast == True
  llm_calls: 1
  compliance_hooks:
    - LineageTracker.annotate_forecast_input()   # 🆕
  ai_act_articles:
    - Art. 10               # lineage del dato de entrada
    - Art. 13               # transparencia (escenarios, supuestos)
  langsmith_tags: ["forecast", "prophet", "what-if"]
  errors:
    - Prophet falla con pocos datos → fallback a media móvil 3 meses
    - Shock no mapeado → explicar al NarratorAgent que no hay parámetro exacto
```

**Motor heredado de v1:** `forecast/prophet_engine.py`, `scenario_builder.py`, `macro_context.py`, `whatif_simulator.py` — MANTENER INTACTOS.

**Prompt:** `core/prompts/forecast_agent.j2`
**Archivo:** `core/graph/nodes/forecast_agent.py`

---

## InsightAgent

```yaml
InsightAgent:
  inputs:
    - rewritten_query
    - raw_data
    - calculated_kpis
    - effect_decomposition       # 🆕 si existe, lo usa como input al análisis
    - data_lineage               # 🆕 lo cita en el insight cuando aplique
    - enriched_context
    - forecast_data
  outputs:
    - insights: List[str]
  tools: []
  activates_when: intent in ["compleja"] OR (intent == "forecast" AND whatif_params exists)
  llm_calls: 1
  compliance_hooks: []
  ai_act_articles:
    - Art. 13               # explicabilidad
  langsmith_tags: ["insight", "analysis"]
  errors:
    - datos insuficientes → insight genérico "los datos disponibles no permiten un análisis profundo"
```

**Prompt:** `core/prompts/insight_agent.j2`
**Archivo:** `core/graph/nodes/insight_agent.py`

---

## HITLValidator 🆕

```yaml
HITLValidator:
  inputs:
    - confidence_score
    - confidence_breakdown
    - policy_violations
    - intent
    - whatif_params (si existe)
    - user_role
  outputs:
    - hitl_status         # "not_required" | "pending"
    - hitl_metadata: Dict # se enriquece desde el endpoint cuando un humano interviene
  tools: []
  activates_when: siempre tras ConfidenceScorer y antes de NarratorAgent
  llm_calls: 0
  compliance_hooks:
    - HITLValidator.decide()   # implementación propia
  ai_act_articles:
    - Art. 14               # supervisión humana
    - Art. 9                # gestión de riesgos
  langsmith_tags: ["hitl", "supervision"]
  errors:
    - configuración HITL_ENABLED=False → hitl_status="not_required", log info
    - umbral de configuración mal formado → fallback a defaults conservadores
```

**Lógica de decisión:**

```python
def decide(state: CDGState) -> str:
    if not ComplianceConfig.HITL_ENABLED:
        return "not_required"
    if state["confidence_score"] < ComplianceConfig.HITL_CONFIDENCE_THRESHOLD:
        return "pending"
    if any(v["severity"] >= ComplianceConfig.HITL_POLICY_VIOLATION_MIN_SEVERITY
           for v in (state["policy_violations"] or [])):
        return "pending"
    if (state["intent"] == "forecast"
        and state["whatif_params"]
        and ComplianceConfig.POLICIES["require_validator_for_what_if"]):
        return "pending"
    return "not_required"
```

**Archivo:** `core/graph/nodes/hitl_validator.py`

---

## NarratorAgent

```yaml
NarratorAgent:
  inputs:
    - rewritten_query
    - user_role
    - raw_data
    - calculated_kpis
    - effect_decomposition       # 🆕 lo renderiza en la respuesta cuando aplique
    - data_lineage               # 🆕 lo embebe en la respuesta como referencias
    - forecast_data
    - scenarios
    - insights
    - knowledge_context
    - knowledge_sources
    - chart_config
    - permission_denied_reason
    - confidence_score           # 🆕
    - hitl_status                # 🆕 si "pending", incluye nota en la respuesta
    - policy_violations          # 🆕 si bloquean, los menciona
  outputs:
    - final_response: str
    - charts: List[Dict]
    - response_metadata:
        tokens_used: int
        latency_ms: int
        agents_invoked: List[str]
        intent: str
        trace_id: str
        model_version: str       # 🆕
  tools:
    - configure_chart_labels
    - export_dashboard_snapshot
  activates_when: siempre (penúltimo nodo del grafo; tras él va DecisionLogger)
  llm_calls: 1
  compliance_hooks:
    - ConfidenceScorer.score_confidence()   # 🆕 hook tras generar respuesta
  ai_act_articles:
    - Art. 13               # transparencia (linaje + descomposición en respuesta)
    - Art. 14               # respeta hitl_status
    - Art. 50               # respuesta etiqueta que es generada por IA
  langsmith_tags: ["narrator", "response"]
  errors:
    - permission_denied → respuesta educada explicando restricción
    - datos vacíos → respuesta indicando que no hay datos para período/gestor
    - hitl_status="pending" → respuesta incluye disclaimer "esta respuesta está pendiente
                              de validación humana antes de ser considerada definitiva"
```

**Plantillas según perfil:**
- `core/prompts/narrator_executive.j2` — tono ejecutivo, análisis profundo, cifras comparadas, **referencias a lineage embebidas como [1], [2]** que el frontend convierte en popovers.
- `core/prompts/narrator_gestor.j2` — tono empático, datos concretos, recomendaciones accionables, lineage embebido.

**Archivo:** `core/graph/nodes/narrator_agent.py`

---

## KnowledgeAgent

```yaml
KnowledgeAgent:
  inputs:
    - rewritten_query
    - user_role
  outputs:
    - knowledge_context: str
    - knowledge_sources: List[Dict]   # [{titulo, pagina, area, score, url}]
    - data_lineage: List[Dict]        # 🆕 unificado con LineageTracker schema
  tools:
    - search_knowledge_base
  activates_when: requires_knowledge == True
  llm_calls: 1
  compliance_hooks:
    - citator.add_citations()         # 🆕 ahora genera items lineage también
  ai_act_articles:
    - Art. 10               # gobernanza del dato (citaciones)
    - Art. 13               # transparencia (fuentes explícitas)
  langsmith_tags: ["knowledge", "rag", "chromadb"]
  errors:
    - ChromaDB vacío → respuesta "no hay documentos cargados en la knowledge base"
    - 0 resultados relevantes → respuesta "no se encontraron documentos sobre este tema"
    - Chunk sin metadata → citar como "[Fuente: documento sin clasificar]"
```

**Flujo:** query → `retriever.search()` → top-k chunks → LLM sintetiza → `citator` añade citaciones y genera lineage items → output

**Archivos:** `core/graph/nodes/knowledge_agent.py`, `knowledge/loader.py`, `knowledge/retriever.py`, `knowledge/citator.py`

---

## Componentes de gobernanza AI Act (servicios, no agentes del grafo)

Aunque no son nodos del grafo, conviene declarar sus contratos para que cada agente sepa qué pueden esperar.

### LineageTracker

```yaml
LineageTracker:
  invoked_from: [DataAgent, ForecastAgent, KnowledgeAgent (via citator)]
  inputs:
    - result: Any
    - query_metadata: Dict
  outputs:
    - annotated_result
    - lineage_items: List[Dict]
  schema_lineage_item:
    value_ref: str
    source_type: "table" | "query" | "document" | "calculation"
    table: Optional[str]
    field: Optional[str]
    period: Optional[str]
    validator: str        # "system_auto" | user_id
    timestamp: str (ISO 8601)
    query_id: Optional[str]
    document_ref: Optional[str]   # para knowledge
  ai_act_articles: [Art. 10]
```

### EffectDecomposer

```yaml
EffectDecomposer:
  invoked_from: [CalculationAgent]
  inputs:
    - actual: Dict[str, float]
    - reference: Dict[str, float]
    - dimensions: List[str] (default precio/volumen/mix/riesgo)
  outputs:
    - decomposition:
        dimensions: List[{name, contribution_bps, source}]
        total_bps: float
        method: "dupont_adapted"
  ai_act_articles: [Art. 13]
```

### ConfidenceScorer

```yaml
ConfidenceScorer:
  invoked_from: [NarratorAgent (hook post-respuesta)]
  inputs:
    - state: CDGState (lee múltiples campos)
  outputs:
    - confidence_score: float (0.0-1.0)
    - confidence_breakdown: Dict[dimension, score]
  ai_act_articles: [Art. 9, Art. 13, Art. 15]
```

### PolicyEnforcer

```yaml
PolicyEnforcer:
  invoked_from: [PermissionAgent (hook post-validación)]
  inputs:
    - state: CDGState
    - policies: ComplianceConfig.POLICIES
  outputs:
    - policy_violations: List[{policy_id, reason, severity, suggested_action}]
  severities: ["low", "medium", "high", "critical"]
  ai_act_articles: [Art. 9, Art. 14, Art. 15]
```

### DecisionLogger

```yaml
DecisionLogger:
  invoked_from: [edge final del grafo, tras NarratorAgent]
  inputs:
    - state: CDGState completo
  outputs:
    - decision_log_id: str (UUID)
    - persisted_at: timestamp
  side_effect:
    - INSERT en tabla decision_logs
  ai_act_articles: [Art. 12]
  errors:
    - BD no disponible → buffer en memoria con flush periódico, log critical
    - estado inconsistente → persistir lo que se pueda, marcar log_incomplete=True
```

### Art11DocGenerator

```yaml
Art11DocGenerator:
  invoked_from: [endpoint POST /compliance/generate-art11-doc, scheduled monthly]
  inputs:
    - sources:
        - AGENT_CONTRACTS.md
        - ARCHITECTURE_V2.md
        - evals/risk_register.json
        - LangSmith metrics (last 30 days)
        - decision_logs (aggregated stats)
  outputs:
    - markdown_doc: str
  side_effect:
    - escribe docs/ART11_TECHNICAL_DOC.md
    - git tag versión del doc
  ai_act_articles: [Art. 11]
```

---

## Resumen de activación por tipo de consulta

| Tipo | QueryRewriter | Orchestrator | Permission | ContextEnricher | Data | Calculation | Forecast | Insight | HITLValidator | Narrator | Knowledge |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Simple | ✅ | ✅ | ✅ | | ✅ | ✅ | | | ✅ | ✅ | |
| Compleja | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | | ✅ | ✅ | ✅ | |
| Forecast | ✅ | ✅ | ✅ | ✅ | | | ✅ | | ✅ | ✅ | |
| Knowledge | ✅ | ✅ | ✅ | | | | | ✅ | ✅ | ✅ | ✅ |
| Out of scope | ✅ | | | | | | | | | ✅ | |

**LLM calls totales:** Simple=4, Compleja=5, Forecast=4, Knowledge=4, Out=2.

**Componentes compliance siempre activos:** `PolicyEnforcer` (en Permission), `LineageTracker` (en Data/Forecast/Knowledge), `ConfidenceScorer` (en Narrator), `DecisionLogger` (al cierre del grafo).

---

## Notas de implementación para Claude Code

Al implementar cada agente:

1. Leer este documento + `AI_ACT_MAPPING.md` §2 para los artículos relevantes.
2. Implementar siguiendo el contrato exacto (inputs/outputs/tools).
3. Activar los compliance hooks indicados.
4. Añadir tags LangSmith según `observability/langsmith_tags.py`.
5. Test específico del agente con casos felices y de error.
6. Actualizar este documento si el contrato cambia.
7. Actualizar `AI_ACT_MAPPING.md` §6 al cierre de la fase.
