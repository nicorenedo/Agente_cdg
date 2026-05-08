# ARCHITECTURE_V2.md — Arquitectura objetivo CDG Intelligence v2

> Fecha: 2026-05-08 · Documento 2 de 3
> Acompaña a `RECONSTRUCTION_AUDIT.md` (qué hay) y `RECONSTRUCTION_PLAN.md` (cómo construir).

---

## 0. Visión general

CDG Intelligence v2 es un sistema agéntico construido sobre **LangGraph** con un único punto de entrada (Orchestrator) y **agentes especializados activados selectivamente** según la intención de la consulta.

### Diferencias clave vs v1

| Aspecto | v1 | v2 |
|---|---|---|
| Punto de entrada | `chat_agent.py` (2.342 líneas, 10 concerns) | Orchestrator (~150 líneas, solo routing) |
| Lógica de negocio | Dispersa en queries + prompts + frontend | Centralizada en `CalculationAgent` y `config/` |
| Reglas de banco | Hardcoded en system prompts | `config/business_rules.py` + plantillas Jinja2 |
| Permisos | Acoplados a `chat_agent` | `PermissionAgent` transversal |
| ReAct | Con retry manual S46 | ReAct puro, tool-calling forzado en prompt |
| LLM calls por request | 4-8 secuenciales | 1-3 según tipo de consulta |
| Prompt caching | No | Sí (Azure OpenAI ≥1024 tokens) |
| Knowledge base | No existe | ChromaDB + multi-formato + citaciones |
| Frontend rebranding | Parcial (theme.js OK, strings sueltos) | `BRAND_CONFIG` total |
| Etiquetas dinámicas en gráficos | Hardcoded | Configurable via NarratorAgent |
| Export HTML/email | No existe | Endpoint dedicado |

### Diagrama global

```
                         ┌─────────────────────────────┐
                         │       Usuario (Web UI)      │
                         └────────────┬────────────────┘
                                      │ POST /chat
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
                         │   NarratorAgent              │
                         │   Construye respuesta final  │
                         └────────────┬────────────────┘
                                      │
                                      ▼
                              Respuesta + charts + sources
```

---

## 1. Arquitectura de agentes

### 1.1 Orchestrator (coordinador)

- Único entry point: `POST /chat`
- **1 LLM call** para clasificar intención (`simple`, `compleja`, `forecast`, `knowledge`).
- Construye dinámicamente el grafo LangGraph según intención.
- **No ejecuta lógica de negocio.** Solo enruta.

### 1.2 Los 8 agentes especializados

| # | Agente | Propósito | LLM calls | Activación |
|---|---|---|---|---|
| 1 | `ContextEnricher` | Enriquece prompt con periodo activo, rol, datos del gestor (si aplica), histórico de la sesión | 0 (determinista) | Consultas complejas y forecast |
| 2 | `PermissionAgent` | Valida permisos según `user_role` + `gestor_id`. Bloquea consultas fuera de scope | 0 (reglas) | **Siempre activo** (transversal) |
| 3 | `DataAgent` | Ejecuta queries SQL atómicas. Devuelve datos estructurados (DataFrame, dict) | 1 (selección de query) | Consultas con datos |
| 4 | `CalculationAgent` | Aplica reglas de negocio sobre los datos: margen, redistribución, KPIs, semáforos | 0 (determinista) | Consultas con datos |
| 5 | `ForecastAgent` | Prophet base + what-if + comparar escenarios. Hereda motor v1 | 1 (selección de tool) | Consultas forecast |
| 6 | `InsightAgent` | Genera análisis cualitativo: "el gestor X retrocede por…", "el centro Y mejora porque…" | 1 | Consultas con interpretación |
| 7 | `NarratorAgent` | Construye la respuesta final en lenguaje natural según perfil (ejecutivo vs gestor) | 1 | **Siempre último** |
| 8 | `KnowledgeAgent` | RAG sobre ChromaDB con multi-formato + metadata + citaciones | 1 (síntesis) | Consultas knowledge |

### 1.3 Principio de activación selectiva

El Orchestrator **no enciende todos los agentes en cada query.** Cada tipo de consulta activa solo los agentes necesarios:

```
A. Consulta simple ("¿cuáles son mis ingresos de abril?")
   Orchestrator → PermissionAgent → DataAgent → CalculationAgent → NarratorAgent
   = 3 LLM calls (orchestrator clasifica + DataAgent selecciona query + NarratorAgent narra)

B. Consulta compleja ("¿por qué cae el margen del centro Madrid?")
   Orchestrator → ContextEnricher → PermissionAgent → DataAgent
   → CalculationAgent → InsightAgent → NarratorAgent
   = 4 LLM calls

C. Consulta forecast ("proyecta mis ingresos a 6 meses con captación +20%")
   Orchestrator → ContextEnricher → PermissionAgent → ForecastAgent → NarratorAgent
   = 3 LLM calls

D. Consulta knowledge ("¿qué dice la circular Y sobre IFRS17?")
   Orchestrator → KnowledgeAgent → InsightAgent → NarratorAgent
   = 3 LLM calls
```

Comparado con v1 (CDG path con 8 LLM calls), v2 reduce a **3-4 calls por request**, además de aplicar prompt caching.

---

## 2. Estructura de directorios

```
cdg-intelligence-v2/
├── backend/
│   ├── core/
│   │   ├── graph/
│   │   │   ├── orchestrator.py      # Entry point + routing
│   │   │   ├── nodes/               # Un archivo por agente
│   │   │   │   ├── context_enricher.py
│   │   │   │   ├── permission_agent.py
│   │   │   │   ├── data_agent.py
│   │   │   │   ├── calculation_agent.py
│   │   │   │   ├── forecast_agent.py
│   │   │   │   ├── insight_agent.py
│   │   │   │   ├── narrator_agent.py
│   │   │   │   └── knowledge_agent.py
│   │   │   └── edges.py             # Routing logic entre nodos
│   │   ├── agents/                  # Implementaciones base
│   │   │   ├── base_agent.py        # Clase abstracta
│   │   │   └── react_agent.py       # ReAct wrapper común
│   │   ├── tools/                   # Tools atómicas (una por archivo)
│   │   │   ├── sql_tools.py
│   │   │   ├── calculation_tools.py
│   │   │   ├── forecast_tools.py
│   │   │   ├── chart_config_tools.py
│   │   │   ├── export_tools.py
│   │   │   └── knowledge_tools.py
│   │   ├── prompts/                 # Plantillas Jinja2
│   │   │   ├── orchestrator.j2
│   │   │   ├── data_agent.j2
│   │   │   ├── calculation_agent.j2
│   │   │   ├── forecast_agent.j2
│   │   │   ├── insight_agent.j2
│   │   │   ├── narrator_executive.j2
│   │   │   ├── narrator_gestor.j2
│   │   │   └── knowledge_agent.j2
│   │   └── state.py                 # CDGState (TypedDict)
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
│   │   ├── loader.py                # PDF / DOCX / TXT / MD
│   │   ├── retriever.py             # ChromaDB + filtros metadata
│   │   ├── citator.py               # Genera citaciones [Fuente: ...]
│   │   ├── documents/               # Storage local de originales
│   │   └── embeddings/              # ChromaDB persistence
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── kpis.py
│   │   │   ├── analytics.py
│   │   │   ├── forecast.py
│   │   │   ├── export.py
│   │   │   ├── knowledge.py
│   │   │   └── admin.py
│   │   └── schemas.py               # Pydantic models
│   ├── config/
│   │   ├── data_config.py           # Periodos, rangos
│   │   ├── business_rules.py        # Márgenes, splits, thresholds
│   │   ├── brand_config.py          # Branding
│   │   └── settings.py              # Env vars (Azure, DB path)
│   └── main.py                      # FastAPI app (~50 líneas)
├── frontend/
│   ├── src/
│   │   ├── theme/
│   │   │   ├── default.js           # Accenture
│   │   │   ├── kutxabank.js         # Cliente actual
│   │   │   └── index.js             # Selector según BRAND_CONFIG
│   │   ├── components/
│   │   │   ├── charts/              # Gráficos configurables
│   │   │   │   ├── ConfigurableChart.jsx
│   │   │   │   └── chart-config-context.js
│   │   │   ├── dashboard/
│   │   │   └── export/              # Componentes de exportación
│   │   ├── pages/
│   │   └── services/
│   └── public/
│       └── brand/                   # Logos por marca
└── docs/
    ├── ARCHITECTURE.md              # Versión final tras Fase 5
    ├── RECONSTRUCTION_AUDIT.md      # (heredado de v1 planning)
    ├── RECONSTRUCTION_PLAN.md       # (heredado de v1 planning)
    └── AGENT_CONTRACTS.md           # Contrato I/O/tools por agente
```

---

## 3. CDGState — estado compartido

`CDGState` es el TypedDict que fluye entre todos los agentes vía LangGraph. Hereda de `MessagesState` para integración nativa con LangChain.

```python
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import MessagesState


class CDGState(MessagesState):
    # ─── Input del usuario ───
    user_message: str
    user_role: str                       # "control_gestion" | "gestor"
    gestor_id: Optional[int]
    periodo: str                         # "2026-04" (default desde config)
    session_id: Optional[str]

    # ─── Contexto enriquecido ───
    intent: Optional[str]                # "simple"|"compleja"|"forecast"|"knowledge"
    requires_data: bool
    requires_forecast: bool
    requires_knowledge: bool
    enriched_context: Optional[Dict[str, Any]]

    # ─── Permisos ───
    permissions_validated: bool
    access_level: str                    # "read_own"|"read_all"|"denied"
    permission_denied_reason: Optional[str]

    # ─── Capa de datos ───
    raw_data: Optional[Dict[str, Any]]   # Output de DataAgent
    calculated_kpis: Optional[Dict[str, Any]]   # Output de CalculationAgent

    # ─── Capa de forecast ───
    forecast_data: Optional[Dict[str, Any]]
    scenarios: Optional[List[Dict[str, Any]]]
    whatif_params: Optional[Dict[str, Any]]

    # ─── Knowledge ───
    knowledge_context: Optional[str]
    knowledge_sources: Optional[List[Dict[str, Any]]]   # [{doc_id, page, score}, ...]

    # ─── Output ───
    insights: Optional[List[str]]
    charts: Optional[List[Dict[str, Any]]]
    chart_config: Optional[Dict[str, Any]]   # Para etiquetas dinámicas
    final_response: Optional[str]
    response_metadata: Optional[Dict[str, Any]]   # Tokens, latency, agents_used
```

Cada agente lee solo los campos que necesita y escribe solo los suyos. Los campos `Optional` permiten que el grafo dinámico active solo los nodos relevantes.

---

## 4. Configuración centralizada

Todos los valores hardcoded de v1 (auditados en sección 6 de `RECONSTRUCTION_AUDIT.md`) se extraen a tres módulos de configuración.

### `config/data_config.py`

```python
class DataConfig:
    DATA_RANGE_START = "2024-09"     # Banco lanzó sep-2024
    DATA_RANGE_END = "2026-04"       # Último mes con datos
    DEFAULT_PERIOD = "2026-04"       # Período por defecto en consultas
    LAUNCH_DATE = "2024-09"
    HISTORICAL_RANGE = "2024-09 → 2025-08"   # Sin datos financieros, solo FECHA_ALTA
    FINANCIAL_RANGE = "2025-09 → 2026-04"    # 20 meses con MOVIMIENTOS
```

### `config/business_rules.py`

```python
class BusinessRules:
    # Márgenes de referencia por producto (usados en prompts y validaciones)
    PRODUCT_MARGINS = {
        "Hipoteca": 0.29,
        "Deposito": 0.36,
        "FondoRV": 0.97,
    }

    # Modelo Fábrica
    REDISTRIBUTION_SPLIT = {
        "Gestora": 0.85,
        "Banco": 0.15,
    }

    # Semáforos
    SEMAFORO_MARGEN_NETO = {
        "verde_min": 0.20,    # ≥20% margen
        "amarillo_min": 0.10,  # 10-20%
        "rojo_max": 0.0,      # <0% o beneficio<0
    }

    SEMAFORO_DESVIACION = {
        "verde_max": 0.05,    # <5%
        "amarillo_max": 0.15, # 5-15%
        "rojo_min": 0.15,     # >15%
    }

    UMBRAL_ROE_MINIMO = 0.08
    UMBRAL_EFICIENCIA_OBJETIVO = 0.65

    # IDs de producto (eliminan los 20+ hardcoded de v1)
    PRODUCT_IDS = {
        "HIPOTECA": "100100100100",
        "DEPOSITO": "400200100100",
        "FONDO_RV": "600100300300",
    }

    # Cuentas para filtros SQL
    INGRESO_PREFIX = "76"
    GASTO_DIRECTO_PREFIXES = ["62", "64", "68", "69"]
    GASTO_CENTRAL_PREFIXES = ["62", "64", "66", "68", "69"]   # incluye fondeo 660001
    FONDEO_ACCOUNT = "660001"
```

### `config/brand_config.py`

```python
class BrandConfig:
    BRAND_NAME = "Kutxabank"               # parametrizable
    BRAND_DISPLAY_NAME = "Kutxabank CDG"
    LOGO_PATH = "/brand/kutxabank.svg"
    SUPPORT_EMAIL = "soporte@kutxabank.es"
    PRIMARY_COLOR = "#0066B3"              # Azul Kutxabank
    SECONDARY_COLOR = "#003E7E"
    # Theme completo en frontend/src/theme/kutxabank.js
```

Cambiar de cliente = cambiar variables de entorno o un `brand_config.py`. Sin tocar agentes.

---

## 5. Mejoras del cliente — diseño técnico

### 5.1 Kutxabank branding

- `frontend/src/theme/kutxabank.js` y `theme/default.js`. Selector vía `BRAND_CONFIG`.
- Variables CSS centralizadas: `--color-primary`, `--color-secondary`, `--font-family`, etc.
- Logo configurable: `<img src={brandConfig.logoPath} />`.
- Email de soporte y nombre de marca también desde config (fin del `sistemas@bancamarch.es` hardcoded en `App.jsx:243`).

### 5.2 Etiquetas dinámicas en gráficos vía lenguaje natural

Nueva tool en `core/tools/chart_config_tools.py`:

```python
@tool
def configure_chart_labels(
    chart_id: str,
    format: Literal["euros", "percentage", "raw"],
    show_values: bool = True,
    show_percentages: bool = False,
    show_legend: bool = True,
) -> Dict:
    """Configura etiquetas y formato de un gráfico ya renderizado en el dashboard."""
```

- El `NarratorAgent` invoca esta tool cuando detecta lenguaje como "muéstrame en porcentaje" o "ocúltame los valores".
- El frontend consume `state.chart_config` y reconfigura el gráfico runtime.
- El componente `ConfigurableChart.jsx` expone props `format`, `showValues`, `showPercentages`, `showLegend`.

### 5.3 Exportación HTML / email

Nueva tool `core/tools/export_tools.py`:

```python
@tool
def export_dashboard_snapshot(
    user_id: str,
    periodo: str,
    format: Literal["html", "email"],
    sections: List[str] = ["kpis", "charts", "insights"],
) -> Dict:
    """Genera un snapshot del dashboard en HTML estático.
       format='email' usa inline-CSS compatible con Outlook/Gmail."""
```

- Endpoint dedicado: `POST /export/snapshot` recibe `{user_id, periodo, format, sections}` y devuelve el HTML.
- Usa Jinja2 para template del HTML; gráficos se serializan como SVG inline.
- Para `format='email'`: inline CSS, sin JS, max-width 600px, fonts seguras.

### 5.4 Knowledge base producción

ChromaDB local (sin servidor) con multi-formato y citaciones.

**`knowledge/loader.py`**

```python
class KnowledgeLoader:
    SUPPORTED_FORMATS = [".pdf", ".docx", ".txt", ".md"]

    def load(self, file_path: str, metadata: DocumentMetadata) -> List[Chunk]:
        """Parsea el archivo, lo divide en chunks (~500 tokens),
           inyecta metadata y devuelve chunks listos para embeddings."""
```

**Schema de metadata:**

```python
class DocumentMetadata(BaseModel):
    autor: str
    fecha: date
    area: Literal["regulacion", "productos", "operaciones", "informes", "decisiones"]
    tipo: Literal["circular", "informe", "manual", "presentacion", "acta"]
    version: str
    titulo: str
    fuente: str   # URL o referencia interna
```

**`knowledge/retriever.py`**

```python
class KnowledgeRetriever:
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,   # ej: {"area": "regulacion"}
    ) -> List[RetrievedChunk]:
        """Búsqueda RAG con embeddings. Filtros por metadata ChromaDB."""
```

**`knowledge/citator.py`**

```python
def add_citations(response: str, sources: List[RetrievedChunk]) -> str:
    """Inyecta [Fuente: titulo, p.X] en la respuesta donde aplique."""
```

**`KnowledgeAgent` flujo:**

1. Recibe `state.user_message`.
2. Llama `retriever.search(query, filters)` para obtener top-k chunks.
3. Pasa chunks como contexto al LLM (1 call).
4. LLM sintetiza respuesta.
5. `citator.add_citations()` inyecta fuentes.
6. Escribe `state.knowledge_context`, `state.knowledge_sources`.

**Endpoint admin:** `POST /knowledge/upload` recibe archivo + metadata, lo procesa y lo añade a ChromaDB.

**Riesgo Windows:** ChromaDB requiere compilación C en Windows. Si falla la instalación, alternativas: LanceDB (Rust nativo) o FAISS + SQLite metadata.

---

## 6. Contratos de agentes

Detalle completo se mantiene en `docs/AGENT_CONTRACTS.md` (creado al final de Fase 1). Cada agente declara:

- **Inputs** — campos de `CDGState` que lee.
- **Outputs** — campos de `CDGState` que escribe.
- **Tools** — qué tools puede invocar.
- **Cuándo se activa** — condición sobre `state.intent` u otros flags.
- **LLM calls esperadas** — 0, 1, 2 (auditoría de coste).
- **Errores conocidos** — qué hacer si falta dato, si tool falla, etc.

Ejemplo (preview):

```yaml
DataAgent:
  inputs:
    - user_message
    - user_role
    - gestor_id
    - periodo
    - intent
  outputs:
    - raw_data: Dict (datos estructurados)
  tools:
    - select_query (LLM)
    - execute_query
    - get_period_metadata
  activates_when: state.requires_data == True
  llm_calls_expected: 1
  errors:
    - if query returns empty → set raw_data = {} and let CalculationAgent handle
    - if SQL fails → propagate to NarratorAgent with error context
```

---

## 7. Anti-patrones eliminados explícitamente

| ❌ v1 anti-pattern | ✅ v2 fix |
|---|---|
| S46-retry manual cuando el agente no llama tools | Tool-calling **obligatorio** en system prompt: "Antes de responder DEBES invocar al menos una tool" |
| Agentes anidados (chat_agent → cdg_agent → tools) | Máximo 1 ReAct por request. Orchestrator solo enruta, no anida |
| God-strings con cifras del banco en prompts | Plantillas Jinja2 con `{{ variables }}` desde `config/` |
| Lógica de negocio en queries SQL | SQL puro en `data/queries/`. Cálculo en `CalculationAgent` |
| Definiciones de métrica en frontend | Backend devuelve metadata (`{label, format, unit}`). Frontend solo renderiza |
| Reinjección de system prompt en cada request | **Prompt caching** Azure OpenAI: system prompt + tools cacheados (≥1024 tokens, 75-90% ahorro) |
| Permisos acoplados a `chat_agent` | `PermissionAgent` transversal, primer nodo del grafo tras Orchestrator |
| Defaults de período repartidos en 4 archivos | Único: `DataConfig.DEFAULT_PERIOD` |
| 7 `.db` de backup en source control | Alembic migrations + única `.db` activa |

---

## 8. Stack técnico v2

| Capa | Tecnologías |
|---|---|
| Backend core | Python 3.11+, FastAPI, LangGraph, LangChain |
| Estado / orquestación | LangGraph `StateGraph` + `MessagesState` |
| LLM | Azure OpenAI (gpt-4o, gpt-5.4 Q3-2026) con prompt caching |
| Templating prompts | Jinja2 |
| Datos | SQLite (heredado v1) + Pandas |
| Forecast | Prophet (heredado v1) + APIs ECB/INE (macro_context) |
| Knowledge base | ChromaDB local · pypdf · python-docx · sentence-transformers |
| Validación | Pydantic v2 |
| Migraciones BD | Alembic |
| Frontend | React 18, Ant Design 5, Recharts, D3 |
| Theming | CSS variables + theme objects |
| Build | Vite (sustituye Create React App si latency build es alta) |
| Tests | pytest (backend) · vitest (frontend) |

---

## 9. Flujos end-to-end (ejemplos)

### 9.1 Gestor pregunta "¿cómo va mi margen este mes?"

```
1. Frontend POST /chat con {user_message, user_role: "gestor", gestor_id: 1, periodo: "2026-04"}
2. Orchestrator clasifica → intent="simple", requires_data=True
3. PermissionAgent valida → access_level="read_own" (gestor solo su cartera)
4. DataAgent selecciona query "get_gestor_metricas" (1 LLM call) y ejecuta
5. CalculationAgent aplica fórmula margen y compara con threshold (0 LLM)
6. NarratorAgent (perfil gestor: tono empático, datos concretos) genera respuesta (1 LLM)
7. Frontend renderiza respuesta + chart embebido
```

LLM calls totales: **3** (Orchestrator + DataAgent + NarratorAgent).

### 9.2 Dirección pregunta "¿qué pasaría si bajan los tipos 25pb?"

```
1. Frontend POST /chat con user_role="control_gestion", periodo="2026-04"
2. Orchestrator clasifica → intent="forecast", requires_forecast=True
3. ContextEnricher añade datos macro actuales del estado (0 LLM)
4. PermissionAgent valida → access_level="read_all"
5. ForecastAgent invoca apply_whatif(tipos_interes=-25) con motor v1 (1 LLM para seleccionar tool)
6. NarratorAgent genera respuesta perfil ejecutivo + 3 escenarios (1 LLM)
7. Frontend renderiza tabla + chart escenarios
```

LLM calls totales: **3**.

### 9.3 Dirección pregunta "¿qué dice la circular SBC-2025-12 sobre IFRS17?"

```
1. Frontend POST /chat
2. Orchestrator clasifica → intent="knowledge", requires_knowledge=True
3. KnowledgeAgent ejecuta retriever.search("IFRS17 circular SBC-2025-12", filters={"area": "regulacion"})
4. RAG devuelve top-5 chunks con metadata
5. KnowledgeAgent sintetiza respuesta con LLM (1 LLM call)
6. citator añade [Fuente: SBC-2025-12, p.4]
7. NarratorAgent ajusta tono ejecutivo (1 LLM call)
8. Frontend renderiza respuesta + lista de fuentes clickeables
```

LLM calls totales: **3**.

---

## 10. Resumen

v2 es un sistema agéntico **modular, configurable y observable**:

- **Modular** — cada agente vive en su archivo, con contrato I/O explícito.
- **Configurable** — sin tocar código se cambian: cliente (brand), períodos, márgenes de referencia, thresholds, productos, segmentos.
- **Observable** — `response_metadata` registra tokens, latency y agents_used por request → dashboard de coste y performance.

La superficie de cambio futuro (rebrand, nuevas reglas, nuevos KPIs) se reduce a archivos de configuración. La lógica agéntica permanece estable.

---

**Próximo documento:** `RECONSTRUCTION_PLAN.md` — fases, sesiones, criterios de paso.
