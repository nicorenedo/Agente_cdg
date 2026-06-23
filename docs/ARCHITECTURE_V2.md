# ARCHITECTURE_V2.md — Arquitectura objetivo CDG Intelligence v2

> Fecha: 2026-06-08 · Revisión 2 (incorpora pata AI Act, Query Rewriter, Decision Logger persistente)
> Acompaña a `RECONSTRUCTION_AUDIT.md`, `RECONSTRUCTION_PLAN.md` y `AI_ACT_MAPPING.md`.

---

## 0. Visión general

CDG Intelligence v2 es un sistema agéntico construido sobre **LangGraph** con un único punto de entrada (Query Rewriter → Orchestrator) y **agentes especializados activados selectivamente** según la intención de la consulta. La arquitectura se organiza en **cuatro capas**:

1. **Capa de experiencia** — UI, frontend, endpoints conversacionales.
2. **Capa de gobernanza AI Act** — linaje del dato, descomposición de efectos, confidence scoring, policy enforcement, HITL, registro auditable de decisiones, documentación Art. 11.
3. **Capa de core agéntico** — Query Rewriter, Orchestrator, agentes especializados, tools.
4. **Capa de datos y conocimiento** — BD, queries, knowledge base.

La capa de gobernanza **no es un parche encima del core**: vive entre el core y la experiencia, interceptando cada output antes de que llegue al usuario, y persistiendo evidencia auditable.

### Diferencias clave vs v1

| Aspecto | v1 | v2 |
|---|---|---|
| Punto de entrada | `chat_agent.py` (2.342 líneas, 10 concerns) | `QueryRewriter` → `Orchestrator` (~250 líneas combinadas) |
| Lógica de negocio | Dispersa en queries + prompts + frontend | Centralizada en `CalculationAgent` y `config/` |
| Reglas de banco | Hardcoded en system prompts | `config/business_rules.py` + plantillas Jinja2 |
| Permisos | Acoplados a `chat_agent` | `PermissionAgent` + `PolicyEnforcer` transversales |
| ReAct | Con retry manual S46 | ReAct puro, tool-calling forzado en prompt |
| LLM calls por request | 4-8 secuenciales | 2-4 según tipo de consulta (Query Rewriter añade 1) |
| Prompt caching | No | Sí (Azure OpenAI ≥1024 tokens) |
| Knowledge base | No existe | ChromaDB + multi-formato + citaciones |
| Frontend rebranding | Parcial | Strings hardcoded eliminados |
| **Trazabilidad técnica** | No existe | **LangSmith end-to-end** |
| **Linaje del dato** | No existe | **`DataLineageTracker` middleware** |
| **Registro de decisiones** | No existe | **`DecisionLogger` con persistencia BD** |
| **Descomposición de efectos** | No existe | **`EffectDecomposer` con método fijo** |
| **Confidence scoring** | No existe | **`ConfidenceScorer` por output** |
| **Supervisión humana** | No existe | **`HITLValidator` con flujo formal** |
| **Documentación Art. 11** | No aplica | **`Art11DocGenerator` generador automático** |
| **Feedback de usuario** | No existe | **`FeedbackCollector` → LangSmith Datasets** |
| **Query rewriting** | No existe | **`QueryRewriter` pre-Orchestrator** |
| **Compliance evals** | No existe | **`compliance_eval.py` + `robustness_eval.py`** |

### Diagrama global

```
                         ┌─────────────────────────────┐
                         │       Usuario (Web UI)      │
                         │  + FeedbackWidget           │
                         │  + DataLineagePopover       │
                         │  + ConfidenceBadge          │
                         │  + EffectBreakdown          │
                         │  + HITLConsole (validators) │
                         └────────────┬────────────────┘
                                      │ POST /chat
                                      ▼
                         ┌─────────────────────────────┐
                         │      QueryRewriter          │
                         │  Normaliza, expande, sanea  │
                         │  1 LLM call (small)         │
                         └────────────┬────────────────┘
                                      ▼
                         ┌─────────────────────────────┐
                         │   Orchestrator (LangGraph)  │
                         │   1 LLM call: clasifica     │
                         │   construye grafo dinámico  │
                         └────────────┬────────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
        ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
        │ Grafo A      │     │ Grafo B      │     │ Grafo C/D    │
        │ Simple       │     │ Compleja     │     │ Forecast/KB  │
        └──────────────┘     └──────────────┘     └──────────────┘
                │                     │                     │
                └─────────────────────┼─────────────────────┘
                                      ▼
                         ┌─────────────────────────────┐
                         │ Capa de gobernanza AI Act:  │
                         │  · DataLineageTracker       │
                         │  · EffectDecomposer         │
                         │  · ConfidenceScorer         │
                         │  · PolicyEnforcer           │
                         │  · HITLValidator            │
                         │  · DecisionLogger ──→ BD    │
                         └────────────┬────────────────┘
                                      ▼
                         ┌─────────────────────────────┐
                         │   NarratorAgent             │
                         │   Construye respuesta final │
                         │   con lineage + confidence  │
                         │   + effect breakdown        │
                         └────────────┬────────────────┘
                                      ▼
                              Respuesta + charts + sources
                              + lineage + confidence
                              + (opcional) HITL pending flag
```

---

## 1. Arquitectura de agentes

### 1.1 QueryRewriter (preprocesador) — **NUEVO**

- Primer nodo del grafo. Procesa el `user_message` crudo antes del Orchestrator.
- **1 LLM call** pequeña: normaliza, expande abreviaturas, desambigua referencias temporales, detecta intent superficial.
- Guarda `original_query` y `rewritten_query` en estado — base para Art. 12 (registro) y Art. 13 (transparencia).
- Sanea inputs sospechosos: heurísticas anti prompt-injection (Art. 15 robustez).
- Si la pregunta es claramente fuera de scope, marca `intent="out_of_scope"` y corta el grafo.

### 1.2 Orchestrator (coordinador)

- Entry point del grafo principal: `POST /chat`
- **1 LLM call** para clasificar intención (`simple`, `compleja`, `forecast`, `knowledge`).
- Construye dinámicamente el grafo LangGraph según intención.
- **No ejecuta lógica de negocio.** Solo enruta.

### 1.3 Los 9 agentes especializados (1 nuevo)

| # | Agente | Propósito | LLM calls | Activación | Nuevo? |
|---|---|---|---|---|:-:|
| 1 | `QueryRewriter` | Normaliza y sanea la pregunta del usuario | 1 | **Siempre primero** | **🆕** |
| 2 | `Orchestrator` | Clasifica intent y construye grafo dinámico | 1 | Siempre tras `QueryRewriter` | |
| 3 | `ContextEnricher` | Enriquece prompt con periodo, rol, datos del gestor, histórico de sesión | 0 (determinista) | Consultas complejas y forecast | |
| 4 | `PermissionAgent` | Valida permisos según `user_role` + `gestor_id` | 0 (reglas) | **Siempre activo** (transversal) | |
| 5 | `DataAgent` | Ejecuta queries SQL atómicas. Devuelve datos + lineage | 1 (selección de query) | Consultas con datos | |
| 6 | `CalculationAgent` | Aplica reglas de negocio: margen, redistribución, KPIs, semáforos. Invoca `EffectDecomposer` cuando aplica | 0 (determinista) | Consultas con datos | |
| 7 | `ForecastAgent` | Prophet base + what-if + comparar escenarios. Hereda motor v1 | 1 (selección de tool) | Consultas forecast | |
| 8 | `InsightAgent` | Genera análisis cualitativo | 1 | Consultas con interpretación | |
| 9 | `NarratorAgent` | Construye la respuesta final con lineage, confidence, effect breakdown | 1 | **Siempre último** | |
| 10 | `KnowledgeAgent` | RAG sobre ChromaDB con metadata + citaciones (lineage unificado) | 1 (síntesis) | Consultas knowledge | |
| 11 | `HITLValidator` | Decide si activar HITL según confidence + policy violations | 0 (reglas) | **Siempre, antes de Narrator** | **🆕** |

### 1.4 Componentes de gobernanza AI Act (no son agentes — son servicios/middleware)

| Componente | Tipo | Rol |
|---|---|---|
| `DataLineageTracker` | Middleware | Envuelve `DataAgent` para anotar source en cada cifra |
| `EffectDecomposer` | Tool / sub-agente | Método fijo precio · volumen · mix · riesgo |
| `ConfidenceScorer` | Hook | Puntúa cada output del NarratorAgent (0.0-1.0) |
| `PolicyEnforcer` | Extensión `PermissionAgent` | Aplica políticas configurables del banco |
| `DecisionLogger` | Servicio persistente | Escribe cada request en tabla `decision_logs` |
| `Art11DocGenerator` | Meta-tool | Genera doc técnica AI Act |
| `FeedbackCollector` | API + storage | Recibe feedback de usuario, alimenta LangSmith Datasets |

### 1.5 Principio de activación selectiva

El Orchestrator **no enciende todos los agentes en cada query.** Cada tipo de consulta activa solo los agentes necesarios:

```
A. Consulta simple ("¿cuáles son mis ingresos de abril?")
   QueryRewriter → Orchestrator → PermissionAgent → DataAgent (con Lineage)
   → CalculationAgent → ConfidenceScorer → HITLValidator → NarratorAgent → DecisionLogger
   = 4 LLM calls (Rewriter + Orchestrator + DataAgent + NarratorAgent)

B. Consulta compleja ("¿por qué cae el margen del centro Madrid?")
   QueryRewriter → Orchestrator → ContextEnricher → PermissionAgent → DataAgent
   → CalculationAgent (con EffectDecomposer) → InsightAgent → ConfidenceScorer
   → HITLValidator → NarratorAgent → DecisionLogger
   = 5 LLM calls

C. Consulta forecast ("proyecta mis ingresos a 6 meses con captación +20%")
   QueryRewriter → Orchestrator → ContextEnricher → PermissionAgent
   → ForecastAgent (con Lineage) → ConfidenceScorer → HITLValidator
   → NarratorAgent → DecisionLogger
   = 4 LLM calls

D. Consulta knowledge ("¿qué dice la circular Y sobre IFRS17?")
   QueryRewriter → Orchestrator → KnowledgeAgent (con Lineage unificado)
   → InsightAgent → ConfidenceScorer → HITLValidator → NarratorAgent → DecisionLogger
   = 4 LLM calls
```

Comparado con v1 (CDG path con 8 LLM calls), v2 sigue siendo más eficiente (**4-5 calls por request**) además de aplicar prompt caching. El Query Rewriter añade 1 call pero es muy pequeña (~200 tokens) y aporta valor regulatorio sustancial.

---

## 2. Estructura de directorios

```
cdg-intelligence-v2/
├── backend/
│   ├── core/
│   │   ├── graph/
│   │   │   ├── orchestrator.py      # Entry point + routing
│   │   │   ├── nodes/               # Un archivo por agente
│   │   │   │   ├── query_rewriter.py        # 🆕
│   │   │   │   ├── context_enricher.py
│   │   │   │   ├── permission_agent.py
│   │   │   │   ├── data_agent.py
│   │   │   │   ├── calculation_agent.py
│   │   │   │   ├── forecast_agent.py
│   │   │   │   ├── insight_agent.py
│   │   │   │   ├── narrator_agent.py
│   │   │   │   ├── knowledge_agent.py
│   │   │   │   └── hitl_validator.py        # 🆕
│   │   │   └── edges.py             # Routing logic entre nodos
│   │   ├── agents/                  # Implementaciones base
│   │   │   ├── base_agent.py        # Clase abstracta con hooks compliance
│   │   │   └── react_agent.py       # ReAct wrapper común
│   │   ├── tools/                   # Tools atómicas (una por archivo)
│   │   │   ├── sql_tools.py
│   │   │   ├── calculation_tools.py
│   │   │   ├── forecast_tools.py
│   │   │   ├── chart_config_tools.py
│   │   │   ├── export_tools.py
│   │   │   ├── knowledge_tools.py
│   │   │   └── effect_decomposer.py         # 🆕
│   │   ├── prompts/                 # Plantillas Jinja2
│   │   │   ├── query_rewriter.j2            # 🆕
│   │   │   ├── orchestrator.j2
│   │   │   ├── data_agent.j2
│   │   │   ├── calculation_agent.j2
│   │   │   ├── forecast_agent.j2
│   │   │   ├── insight_agent.j2
│   │   │   ├── narrator_executive.j2
│   │   │   ├── narrator_gestor.j2
│   │   │   └── knowledge_agent.j2
│   │   └── state.py                 # CDGState (TypedDict) — extendido con AI Act
│   ├── compliance/                  # 🆕 Capa de gobernanza AI Act
│   │   ├── __init__.py
│   │   ├── decision_logger.py       # Persistencia de decision_logs
│   │   ├── lineage_tracker.py       # Middleware anotación de source
│   │   ├── confidence_scorer.py     # Scoring 0.0-1.0 por output
│   │   ├── policy_enforcer.py       # Políticas configurables del banco
│   │   ├── art11_doc_generator.py   # Meta-tool generador de doc Art. 11
│   │   └── schemas.py               # Pydantic schemas: DecisionLog, LineageItem, etc.
│   ├── data/
│   │   ├── queries/                 # SQL puro, sin business logic
│   │   │   ├── ingresos.py
│   │   │   ├── gastos.py
│   │   │   ├── contratos.py
│   │   │   ├── gestores.py
│   │   │   ├── centros.py
│   │   │   ├── productos.py
│   │   │   └── desviaciones.py
│   │   ├── calculator.py            # Lógica de negocio centralizada
│   │   └── database.py              # Connection management
│   ├── forecast/                    # Heredado v1 (mantener intacto)
│   │   ├── prophet_engine.py
│   │   ├── scenario_builder.py
│   │   ├── macro_context.py
│   │   └── whatif_simulator.py
│   ├── knowledge/                   # Knowledge base producción
│   │   ├── loader.py
│   │   ├── retriever.py
│   │   ├── citator.py               # Genera lineage items unificados
│   │   ├── documents/
│   │   └── embeddings/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── kpis.py
│   │   │   ├── analytics.py
│   │   │   ├── forecast.py
│   │   │   ├── export.py
│   │   │   ├── knowledge.py
│   │   │   ├── admin.py
│   │   │   ├── feedback.py          # 🆕 POST /chat/feedback
│   │   │   ├── hitl.py              # 🆕 /hitl/validate, /hitl/reject, /hitl/override
│   │   │   ├── decision_log.py      # 🆕 GET /decision-log/{id}, /decision-log/search
│   │   │   └── compliance.py        # 🆕 GET /compliance/metrics, /compliance/art11-doc
│   │   └── schemas.py
│   ├── config/
│   │   ├── data_config.py
│   │   ├── business_rules.py
│   │   ├── brand_config.py
│   │   ├── compliance_config.py     # 🆕 Umbrales HITL, retención logs, policies
│   │   └── settings.py
│   ├── observability/
│   │   ├── langsmith_config.py      # Setup LangSmith tracing
│   │   ├── langsmith_tags.py        # 🆕 Tags compliance:* estandarizados
│   │   ├── callbacks.py             # Custom callbacks para métricas
│   │   └── dashboard.py             # Endpoint /observability/metrics
│   ├── evals/
│   │   ├── s77_functional.py        # 48 tests funcionales heredados v1
│   │   ├── s88_qualitative.py       # 21 tests cualitativos con LLM judge
│   │   ├── knowledge_eval.py
│   │   ├── latency_eval.py
│   │   ├── compliance_eval.py       # 🆕 Verifica decision_log, lineage, confidence, hitl
│   │   ├── robustness_eval.py       # 🆕 Tests adversariales (prompt injection, edge)
│   │   ├── risk_register.json       # 🆕 Registro de riesgos vivo
│   │   └── datasets/
│   │       ├── s77_battery.json
│   │       ├── s88_battery.json
│   │       ├── compliance_battery.json   # 🆕
│   │       └── robustness_battery.json   # 🆕
│   └── main.py                      # FastAPI app (~50 líneas)
├── frontend/
│   ├── src/
│   │   ├── theme/                   # Heredado intacto — no se toca
│   │   ├── components/
│   │   │   ├── Chat/                # Heredado intacto
│   │   │   ├── Dashboard/           # Heredado intacto (visual)
│   │   │   ├── compliance/                  # 🆕 Componentes AI Act
│   │   │   │   ├── FeedbackWidget.jsx
│   │   │   │   ├── DataLineagePopover.jsx
│   │   │   │   ├── ConfidenceBadge.jsx
│   │   │   │   ├── EffectBreakdown.jsx
│   │   │   │   └── HITLConsole.jsx
│   │   │   └── export/
│   │   ├── pages/
│   │   └── services/
│   │       ├── analyticsService.js  # Reescrito: cliente HTTP fino
│   │       ├── feedbackService.js   # 🆕
│   │       ├── hitlService.js       # 🆕
│   │       └── lineageService.js    # 🆕
│   └── public/
└── docs/
    ├── RECONSTRUCTION_AUDIT.md
    ├── ARCHITECTURE_V2.md           # Este documento
    ├── RECONSTRUCTION_PLAN.md
    ├── AGENT_CONTRACTS.md
    ├── AI_ACT_MAPPING.md            # 🆕
    ├── ART11_TECHNICAL_DOC.md       # 🆕 Generado en F5
    ├── USER_MANUAL.md               # 🆕 Manual del desplegador
    ├── QMS.md                       # 🆕 Sistema de gestión de calidad
    ├── RISK_REGISTER.md             # 🆕 Vista humana del risk_register.json
    └── data_generation/
```

---

## 3. CDGState — estado compartido (extendido con AI Act)

`CDGState` es el TypedDict que fluye entre todos los agentes vía LangGraph. Hereda de `MessagesState` para integración nativa con LangChain.

```python
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import MessagesState


class CDGState(MessagesState):
    # ─── Input del usuario ───
    user_message: str                    # Original, conservado siempre
    user_role: str                       # "control_gestion" | "gestor" | "validator"
    gestor_id: Optional[int]
    periodo: str
    session_id: Optional[str]

    # ─── Query Rewriter ───                          🆕
    original_query: str                  # Igual a user_message, alias para claridad
    rewritten_query: Optional[str]       # Versión normalizada/expandida
    query_rewriter_metadata: Optional[Dict[str, Any]]  # {confidence, changes, reasoning}

    # ─── Contexto enriquecido ───
    intent: Optional[str]                # "simple"|"compleja"|"forecast"|"knowledge"|"out_of_scope"
    requires_data: bool
    requires_forecast: bool
    requires_knowledge: bool
    enriched_context: Optional[Dict[str, Any]]

    # ─── Permisos + Políticas ───
    permissions_validated: bool
    access_level: str                    # "read_own"|"read_all"|"denied"
    permission_denied_reason: Optional[str]
    policy_violations: Optional[List[Dict[str, Any]]]   # 🆕 [{policy_id, reason, severity}]

    # ─── Capa de datos ───
    raw_data: Optional[Dict[str, Any]]
    calculated_kpis: Optional[Dict[str, Any]]

    # ─── Capa de forecast ───
    forecast_data: Optional[Dict[str, Any]]
    scenarios: Optional[List[Dict[str, Any]]]
    whatif_params: Optional[Dict[str, Any]]

    # ─── Knowledge ───
    knowledge_context: Optional[str]
    knowledge_sources: Optional[List[Dict[str, Any]]]

    # ─── Linaje del dato (AI Act Art. 10) ───      🆕
    data_lineage: Optional[List[Dict[str, Any]]]
    # Cada item: {value_ref, source_type, table, field, period, validator, timestamp, query_id}

    # ─── Descomposición de efectos (AI Act Art. 13) ───   🆕
    effect_decomposition: Optional[Dict[str, Any]]
    # {dimensions: [{name, contribution_bps, source}], total_bps, method}

    # ─── Confidence scoring (AI Act Art. 13, 15) ───   🆕
    confidence_score: Optional[float]                # 0.0 - 1.0
    confidence_breakdown: Optional[Dict[str, float]]
    # {data_quality, historical_coverage, precedent_match, lineage_completeness}

    # ─── HITL (AI Act Art. 14) ───                  🆕
    hitl_status: Optional[str]
    # "not_required" | "pending" | "validated" | "rejected" | "overridden"
    hitl_metadata: Optional[Dict[str, Any]]
    # {validator_id, motivo, timestamp, override_reason}

    # ─── Decision log (AI Act Art. 12) ───          🆕
    decision_log_id: Optional[str]                   # UUID, persistido en BD

    # ─── Feedback del usuario ───                   🆕
    user_feedback: Optional[Dict[str, Any]]
    # {rating, comment, timestamp} — se rellena post-respuesta

    # ─── Output ───
    insights: Optional[List[str]]
    charts: Optional[List[Dict[str, Any]]]
    chart_config: Optional[Dict[str, Any]]
    final_response: Optional[str]
    response_metadata: Optional[Dict[str, Any]]
    # tokens, latency, agents_used, model_version  🆕 incluye model_version

    # ─── Observabilidad técnica (LangSmith) ───
    trace_id: Optional[str]                  # LangSmith run_id
    agents_invoked: Optional[List[str]]
    total_tokens: Optional[int]
    total_latency_ms: Optional[int]

    # ─── Metadatos AI Act adicionales ───            🆕
    model_version: Optional[str]                     # Versión exacta del LLM usado
    timestamp_request: Optional[str]                 # ISO 8601 inicio de request
    timestamp_response: Optional[str]                # ISO 8601 fin de request
```

Cada agente lee solo los campos que necesita y escribe solo los suyos. Los campos `Optional` permiten que el grafo dinámico active solo los nodos relevantes.

---

## 3.bis Tablas de persistencia (Alembic) — capa AI Act

### Tabla `decision_logs`

```sql
CREATE TABLE decision_logs (
    decision_log_id    TEXT PRIMARY KEY,           -- UUID
    timestamp_request  TEXT NOT NULL,              -- ISO 8601
    timestamp_response TEXT NOT NULL,
    user_id            TEXT NOT NULL,
    user_role          TEXT NOT NULL,
    gestor_id          INTEGER,
    session_id         TEXT,
    original_query     TEXT NOT NULL,
    rewritten_query    TEXT,
    intent             TEXT,
    agents_invoked     TEXT,                       -- JSON array
    tools_called       TEXT,                       -- JSON array
    final_response     TEXT NOT NULL,
    model_version      TEXT NOT NULL,
    confidence_score   REAL,
    confidence_breakdown TEXT,                     -- JSON
    effect_decomposition TEXT,                     -- JSON
    data_lineage       TEXT NOT NULL,              -- JSON array
    policy_violations  TEXT,                       -- JSON array
    hitl_status        TEXT NOT NULL,
    trace_id           TEXT,                       -- LangSmith run_id
    total_tokens       INTEGER,
    total_latency_ms   INTEGER
);

CREATE INDEX idx_decision_logs_user ON decision_logs(user_id, timestamp_request);
CREATE INDEX idx_decision_logs_session ON decision_logs(session_id);
CREATE INDEX idx_decision_logs_intent ON decision_logs(intent);
CREATE INDEX idx_decision_logs_hitl ON decision_logs(hitl_status);
```

### Tabla `user_feedback`

```sql
CREATE TABLE user_feedback (
    feedback_id        TEXT PRIMARY KEY,
    decision_log_id    TEXT NOT NULL,
    user_id            TEXT NOT NULL,
    timestamp          TEXT NOT NULL,
    rating             INTEGER NOT NULL,            -- -1, 0, +1
    comment            TEXT,
    action             TEXT,                        -- "approve" | "reject" | "request_revision"
    FOREIGN KEY (decision_log_id) REFERENCES decision_logs(decision_log_id)
);

CREATE INDEX idx_feedback_decision ON user_feedback(decision_log_id);
```

### Tabla `hitl_overrides`

```sql
CREATE TABLE hitl_overrides (
    override_id        TEXT PRIMARY KEY,
    decision_log_id    TEXT NOT NULL,
    validator_id       TEXT NOT NULL,
    timestamp          TEXT NOT NULL,
    action             TEXT NOT NULL,               -- "validate"|"reject"|"override"
    motivo             TEXT NOT NULL,
    new_response       TEXT,                        -- Si action="override"
    FOREIGN KEY (decision_log_id) REFERENCES decision_logs(decision_log_id)
);

CREATE INDEX idx_hitl_validator ON hitl_overrides(validator_id);
CREATE INDEX idx_hitl_action ON hitl_overrides(action);
```

### Tabla `data_sources`

```sql
CREATE TABLE data_sources (
    source_id          TEXT PRIMARY KEY,
    source_type        TEXT NOT NULL,               -- "table"|"query"|"document"
    name               TEXT NOT NULL,
    description        TEXT,
    owner              TEXT,                        -- responsable del dato
    last_validated     TEXT,
    last_updated       TEXT
);
```

Pre-poblada en F0 con las tablas y campos clave del dominio (gestores, contratos, movimientos, productos, etc.).

---

## 4. Configuración centralizada

Todos los valores hardcoded de v1 se extraen a cinco módulos de configuración:

- `config/data_config.py` — períodos, rangos, defaults
- `config/business_rules.py` — márgenes, splits, thresholds, IDs producto
- `config/brand_config.py` — branding (Accenture default, temable por cliente)
- `config/settings.py` — env vars (Azure, DB path, LangSmith)
- **`config/compliance_config.py` 🆕** — umbrales y políticas AI Act

### `config/compliance_config.py` — esquema

```python
class ComplianceConfig:
    # Umbrales para activar HITL
    HITL_CONFIDENCE_THRESHOLD = 0.7      # Confidence menor → HITL pending
    HITL_POLICY_VIOLATION_MIN_SEVERITY = "medium"  # "low"|"medium"|"high"
    HITL_ENABLED = True                  # Master switch

    # Retención de logs (Art. 12)
    DECISION_LOG_RETENTION_DAYS = 540    # 18 meses default
    USER_FEEDBACK_RETENTION_DAYS = 540
    HITL_OVERRIDE_RETENTION_DAYS = 1800  # 5 años (auditoría)

    # Políticas configurables por cliente
    POLICIES = {
        "no_personal_data_in_response": True,
        "block_predictions_beyond_horizon": True,
        "max_forecast_months": 24,
        "require_validator_for_what_if": False,
    }

    # Confidence scoring
    CONFIDENCE_DIMENSIONS = [
        "data_quality",          # ¿Datos completos y recientes?
        "historical_coverage",    # ¿Suficiente histórico?
        "precedent_match",        # ¿Hay precedentes similares?
        "lineage_completeness",   # ¿Linaje completo?
    ]

    # Umbrales para clasificar confidence en UI
    CONFIDENCE_BUCKETS = {
        "high": 0.85,
        "medium": 0.6,
        "low": 0.0,
    }
```

---

## 5. Mejoras del cliente — diseño técnico

### 5.1 Sistema de temas (branding)

**Sin cambios respecto al estado actual** — la calidad visual del frontend está consolidada y no se rehace. Solo se eliminan strings hardcoded de cliente concreto (`sistemas@bancamarch.es`) y se centralizan en `BRAND_CONFIG`.

### 5.2 Etiquetas dinámicas en gráficos vía lenguaje natural

Tool en `core/tools/chart_config_tools.py` (descripción heredada del plan original).

### 5.3 Exportación HTML / email

Tool `core/tools/export_tools.py` con `export_dashboard_snapshot()` (descripción heredada).

### 5.4 Knowledge base producción

ChromaDB local con multi-formato y citaciones. **El `citator.py` genera lineage items con el mismo schema que `LineageTracker`** — un único modelo de linaje para datos y conocimiento.

### 5.5 Capa AI Act — componentes nuevos

#### EffectDecomposer

```python
# core/tools/effect_decomposer.py

@tool
def decompose_effects(
    actual: Dict[str, float],
    reference: Dict[str, float],
    dimensions: List[str] = ["precio", "volumen", "mix", "riesgo"],
) -> Dict[str, Any]:
    """Descompone una variación financiera en sus efectos componentes.

    Método fijo:
    - precio: variación de tarifa/spread por contrato
    - volumen: variación del número de contratos
    - mix: variación por cambio de composición de producto/segmento
    - riesgo: variación por cambio en provisiones/coste de riesgo

    Devuelve contribución en puntos básicos por dimensión.
    """
```

#### ConfidenceScorer

```python
# compliance/confidence_scorer.py

def score_confidence(state: CDGState) -> Dict[str, float]:
    """Puntúa 0.0-1.0 cada dimensión configurada en ComplianceConfig.CONFIDENCE_DIMENSIONS.

    Resultado:
        {
            "overall": 0.82,
            "data_quality": 0.95,
            "historical_coverage": 0.78,
            "precedent_match": 0.70,
            "lineage_completeness": 0.85
        }
    """
```

#### DecisionLogger

```python
# compliance/decision_logger.py

class DecisionLogger:
    def log(self, state: CDGState) -> str:
        """Persiste el estado completo de un request en tabla decision_logs.
        Devuelve decision_log_id (UUID).
        Idempotente: si decision_log_id ya existe, hace update."""
```

#### LineageTracker

```python
# compliance/lineage_tracker.py

class LineageTracker:
    def annotate_query_result(
        self, result: Any, query_metadata: Dict
    ) -> Tuple[Any, List[Dict]]:
        """Envuelve resultado de query con metadata de linaje.

        Item de linaje:
            {
                "value_ref": "ingresos_q1",
                "source_type": "table",
                "table": "movimientos",
                "field": "importe",
                "period": "2026-04",
                "validator": "system_auto",
                "timestamp": "2026-06-08T10:30:00Z",
                "query_id": "get_ingresos_gestor_v1"
            }
        """
```

#### PolicyEnforcer

```python
# compliance/policy_enforcer.py

class PolicyEnforcer:
    def enforce(self, state: CDGState) -> List[Dict]:
        """Aplica políticas de ComplianceConfig.POLICIES.
        Devuelve lista de violaciones (vacía si OK).

        Cada violación:
            {policy_id, reason, severity, suggested_action}

        Severity = "high" puede bloquear; "medium" activa HITL;
        "low" se loga pero no detiene el flujo.
        """
```

#### HITLValidator

```python
# core/graph/nodes/hitl_validator.py

class HITLValidatorAgent:
    def decide(self, state: CDGState) -> str:
        """Decide hitl_status según:
        - confidence_score < HITL_CONFIDENCE_THRESHOLD → "pending"
        - policy_violations con severity ≥ HITL_POLICY_VIOLATION_MIN_SEVERITY → "pending"
        - intent="forecast" con whatif y require_validator_for_what_if → "pending"
        - sino → "not_required"
        """
```

#### Art11DocGenerator

```python
# compliance/art11_doc_generator.py

class Art11DocGenerator:
    def generate(self) -> str:
        """Genera el documento técnico Art. 11 a partir de:
        - AGENT_CONTRACTS.md (capacidades y limitaciones)
        - ARCHITECTURE_V2.md (descripción del sistema)
        - evals/risk_register.json (gestión de riesgos)
        - LangSmith metrics agregados (precisión, latencia)
        - decision_logs (estadísticas de uso)

        Output: markdown que se escribe en docs/ART11_TECHNICAL_DOC.md
        """
```

---

## 6. Contratos de agentes

Detalle completo en `docs/AGENT_CONTRACTS.md`.

---

## 7. Anti-patrones eliminados explícitamente

| ❌ v1 anti-pattern | ✅ v2 fix |
|---|---|
| S46-retry manual | Tool-calling **obligatorio** en system prompt |
| Agentes anidados | Máximo 1 ReAct por request. Orchestrator solo enruta |
| God-strings con cifras del banco en prompts | Plantillas Jinja2 con `{{ variables }}` desde `config/` |
| Lógica de negocio en queries SQL | SQL puro en `data/queries/`. Cálculo en `CalculationAgent` |
| Definiciones de métrica en frontend | Backend devuelve metadata; frontend solo renderiza |
| Reinjección de system prompt en cada request | **Prompt caching** Azure OpenAI |
| Permisos acoplados a `chat_agent` | `PermissionAgent` + `PolicyEnforcer` transversales |
| Defaults de período repartidos en 4 archivos | Único: `DataConfig.DEFAULT_PERIOD` |
| 7 `.db` de backup en source control | Alembic migrations + única `.db` activa |
| Sin observabilidad — debugging manual | **LangSmith tracing** end-to-end |
| **Sin trazabilidad regulatoria** 🆕 | **`DecisionLogger` + `LineageTracker` + `Art11DocGenerator`** |
| **Outputs sin explicabilidad estructurada** 🆕 | **`EffectDecomposer` + `ConfidenceScorer`** |
| **Sin supervisión humana formal** 🆕 | **`HITLValidator` + `<HITLConsole>` + `hitl_overrides` table** |
| **Sin loop de feedback** 🆕 | **`FeedbackCollector` → LangSmith Datasets** |
| **Inputs sin sanitización** 🆕 | **`QueryRewriter` + heurísticas anti prompt-injection** |

---

## 8. Observabilidad — dos capas complementarias

### 8.1 Por qué dos capas

**LangSmith** captura la dimensión **técnica** (prompts, tools, tokens, latency). Excelente para debugging y mejora del modelo.

**DecisionLogger** captura la dimensión **de negocio/regulatoria** (qué decisión informó el agente, con qué datos, qué confianza, quién validó). Es lo que el supervisor lee.

Ambas conviven y se referencian mutuamente vía `trace_id`.

### 8.2 LangSmith — integración

```python
# observability/langsmith_config.py
import os

def setup_langsmith():
    """Configurar LangSmith tracing. Se llama al arrancar FastAPI."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "cdg-intelligence-v2")
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
```

LangGraph + LangChain tracean automáticamente cada nodo, cada LLM call y cada tool invocation cuando `LANGCHAIN_TRACING_V2=true`.

### 8.3 Tags estandarizados de LangSmith (`observability/langsmith_tags.py`)

```python
LANGSMITH_TAGS = {
    "agent": ["query_rewriter", "orchestrator", "data_agent", ...],
    "intent": ["simple", "compleja", "forecast", "knowledge", "out_of_scope"],
    "compliance": [
        "hitl:pending", "hitl:validated", "hitl:rejected", "hitl:overridden",
        "confidence:high", "confidence:medium", "confidence:low",
        "policy_violation:detected", "policy_violation:blocked",
    ],
    "user_role": ["control_gestion", "gestor", "validator"],
}
```

### 8.4 LangSmith Evals

Datasets versionados para batería S77, S88, compliance_eval, robustness_eval. Cada release ejecuta todos automáticamente.

### 8.5 Endpoint de métricas técnicas

```
GET /observability/metrics?periodo=2026-04
→ {
    avg_latency_ms, avg_tokens_per_request, requests_last_24h,
    agents_distribution, error_rate
  }
```

### 8.6 Endpoint de métricas de compliance 🆕

```
GET /compliance/metrics?periodo=2026-04
→ {
    pct_requests_with_hitl: 0.12,
    pct_outputs_high_confidence: 0.78,
    pct_outputs_low_confidence: 0.08,
    n_overrides_last_30d: 7,
    pct_feedback_negative: 0.04,
    avg_lineage_completeness: 0.92,
    n_decision_logs_persisted: 1247,
    last_art11_doc_generated_at: "2026-06-01T10:00:00Z"
  }
```

---

## 9. Stack técnico v2

| Capa | Tecnologías |
|---|---|
| Backend core | Python 3.11+, FastAPI, LangGraph, LangChain |
| Estado / orquestación | LangGraph `StateGraph` + `MessagesState` |
| LLM | Azure OpenAI (gpt-4o) con prompt caching |
| Observabilidad técnica | **LangSmith** (tracing + evals + datasets) |
| Observabilidad regulatoria | **`DecisionLogger` + BD** |
| Templating prompts | Jinja2 |
| Datos | SQLite (heredado v1) + Pandas |
| Forecast | Prophet (heredado v1) + APIs ECB/INE |
| Knowledge base | ChromaDB · pypdf · python-docx · sentence-transformers |
| Validación | Pydantic v2 |
| Migraciones BD | Alembic |
| Frontend | React 18, Ant Design 5, Recharts, D3 (heredado v1) |
| Theming | CSS variables + theme objects (heredado v1) |
| Tests | pytest (backend) · vitest (frontend) · **LangSmith evals** (cualitativo + compliance + robustness) |

---

## 10. Flujos end-to-end (ejemplos)

### 10.1 Gestor pregunta "¿cómo va mi margen este mes?"

```
1. Frontend POST /chat con {user_message, user_role: "gestor", gestor_id: 1, periodo: "2026-04"}
2. QueryRewriter normaliza → rewritten_query, original_query persistido
3. Orchestrator clasifica → intent="simple", requires_data=True
4. PermissionAgent + PolicyEnforcer validan → access_level="read_own", policy_violations=[]
5. DataAgent selecciona query "get_gestor_metricas", ejecuta, LineageTracker anota source
6. CalculationAgent aplica fórmula margen, propaga lineage
7. ConfidenceScorer puntúa output → 0.91 (alto)
8. HITLValidator decide → hitl_status="not_required" (confidence alto, sin policy violations)
9. NarratorAgent (perfil gestor) genera respuesta con lineage embebido
10. DecisionLogger persiste todo en decision_logs
11. Frontend renderiza respuesta + ConfidenceBadge + DataLineagePopover + FeedbackWidget
```

LLM calls totales: **4** (Rewriter + Orchestrator + DataAgent + NarratorAgent).

### 10.2 Dirección pregunta "¿qué pasaría si bajan los tipos 25pb?"

```
1. Frontend POST /chat
2. QueryRewriter expande "25pb" → "25 puntos básicos", original conservado
3. Orchestrator → intent="forecast", requires_forecast=True
4. ContextEnricher añade macro context
5. PermissionAgent + PolicyEnforcer → access_level="read_all".
   Policy "require_validator_for_what_if" (si activa) → policy_violations añade flag
6. ForecastAgent invoca apply_whatif(tipos_interes=-25), propaga lineage del forecast
7. ConfidenceScorer → 0.76 (medio, what-if implica mayor incertidumbre)
8. HITLValidator → si policy_violations o confidence<umbral → hitl_status="pending"
9. NarratorAgent genera respuesta con escenarios + EffectBreakdown
10. DecisionLogger persiste
11. Frontend: si hitl_status="pending", mostrar badge "Pendiente de validación".
    Validator ve en su HITLConsole, decide → /hitl/validate o /hitl/override
```

LLM calls totales: **4**.

### 10.3 Dirección pregunta "¿qué dice la circular SBC-2025-12 sobre IFRS17?"

```
1. Frontend POST /chat
2. QueryRewriter detecta referencia documental, conserva exacta
3. Orchestrator → intent="knowledge"
4. KnowledgeAgent: retriever.search(filters={"area": "regulacion"})
5. RAG devuelve top-5 chunks con metadata
6. citator genera lineage items (mismo schema que LineageTracker)
7. KnowledgeAgent sintetiza con LLM
8. ConfidenceScorer puntúa según relevance de chunks
9. HITLValidator → "not_required" si confidence alto
10. NarratorAgent ajusta tono, conserva citaciones
11. DecisionLogger persiste
12. Frontend renderiza respuesta + DataLineagePopover muestra fuentes documentales
```

LLM calls totales: **4**.

---

## 11. Resumen

v2 es un sistema agéntico **modular, configurable, observable y AI Act-ready desde el origen**:

- **Modular** — cada agente vive en su archivo, con contrato I/O explícito.
- **Configurable** — sin tocar código se cambian cliente (brand), períodos, márgenes de referencia, thresholds, productos, **políticas AI Act**, **umbrales HITL**.
- **Observable en dos capas** — LangSmith para técnico, `DecisionLogger` para regulatorio.
- **Auditable** — cada cifra del output trazable hasta la fuente, cada decisión persistida con confidence, cada override de humano registrado con motivo.
- **Defendible** — `Art11DocGenerator` produce la doc técnica que se entrega al supervisor; `compliance_eval` + `robustness_eval` demuestran cumplimiento por release.

La superficie de cambio futuro (rebrand, nuevas reglas, nuevos KPIs, nuevas políticas AI Act) se reduce a archivos de configuración. La lógica agéntica permanece estable.

---

**Próximo documento:** `RECONSTRUCTION_PLAN.md` — fases, sesiones, criterios de paso (revisado).
