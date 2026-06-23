# RECONSTRUCTION_PLAN.md — Plan de reconstrucción CDG Intelligence v2

> Fecha: 2026-06-08 · Revisión 2 (incorpora pata AI Act, Query Rewriter y sistema de feedback)
> Acompaña a `RECONSTRUCTION_AUDIT.md`, `ARCHITECTURE_V2.md` y `AI_ACT_MAPPING.md`.

---

## 0. Principio guía

**De dentro hacia fuera.** Construir primero la infraestructura (estado, BD, config), luego los agentes uno a uno (data → cálculo → respuesta), luego knowledge base, luego frontend mínimo (sin tocar diseño visual existente, ya consolidado), finalmente QA y readiness AI Act.

**Tres patas se desarrollan en paralelo en cada fase, no en serie:**

1. **Pata agéntica** — agentes especializados con LangGraph + Orchestrator + Query Rewriter.
2. **Pata de observabilidad** — LangSmith tracing técnico + Decision Logger persistente para compliance.
3. **Pata AI Act** — linaje del dato, descomposición de efectos, confidence score, HITL, documentación Art. 11.

**Tres criterios de no-regresión obligatorios:**

1. Las **48 preguntas funcionales de S77** deben pasar al final de Fase 1.
2. La **batería cualitativa de S88 (21 preguntas)** debe alcanzar ≥4.5/5 al final de Fase 2.
3. La **batería de compliance** (nueva, en `evals/compliance_eval.py`) debe pasar al final de Fase 2.

Sin estos checks, no se avanza a la siguiente fase.

---

## 1. Snapshot de inicio

Al arrancar Fase 0, el repo v1 está en:

| Variable | Valor |
|---|---|
| Último commit | `045522d` (S89-F3 ForecastAgent shocks) |
| Branch | `main` |
| Tests funcional | 48/48 ✅ S78a |
| Tests no-regresión | 20/20 ✅ S84 |
| Calidad cualitativa | 4.4/5 S88 → CDG 4.6 · Gestor 4.7 · Forecast 4.8 post S89 |
| Margen entidad | 48.6% |
| Dispersión gestores | 45.1pp |
| Datos | sep-2024 a abr-2026 (20 meses limpios) |
| Proyecciones | recalibradas S86-S87 (Prophet cap=1.10, no_yearly, cp=0.005) |

---

## 2. Las 6 fases

### FASE 0 — Setup (1 sesión)

**Objetivo:** crear el repo `cdg-intelligence-v2` listo para programar, con base de datos AI Act-ready.

| Paso | Acción | Validación |
|---|---|---|
| F0.1 | Crear repo `cdg-intelligence-v2` (copia de v1 como punto de partida) | `git log` muestra commit inicial |
| F0.2 | Crear estructura de directorios completa según `ARCHITECTURE_V2.md` §2 (incluye `observability/`, `evals/`, `compliance/`) | `tree backend/ frontend/` coincide con spec |
| F0.3 | Mover `BM_CONTABILIDAD_CDG.db` activa + datos Prophet (intactos) | `sqlite3 ... ".tables"` lista 14 tablas |
| F0.4 | **Eliminar 7 `.db` de backup** | `ls backend/data/` solo muestra 1 `.db` |
| F0.5 | Eliminar `cdg_agent_v6_backup.py` (dead code) | `find . -name "*backup*"` vacío |
| F0.6 | Crear `pyproject.toml` con dependencias: `langgraph`, `langchain`, `langchain-openai`, `chromadb`, `pypdf`, `python-docx`, `jinja2`, `pydantic`, `fastapi`, `prophet`, `pandas`, `sqlalchemy`, `alembic`, `langsmith`, `pytest`, `uuid` | `pip install -e .` sin errores |
| F0.7 | Setup Alembic con migración inicial reflejando schema BD actual | `alembic upgrade head` aplica migración 0 sin cambios |
| F0.8 | **Crear migración Alembic con tablas AI Act:** `decision_logs`, `user_feedback`, `hitl_overrides`, `data_sources` (schema en `ARCHITECTURE_V2.md` §3.bis) | `alembic upgrade head` crea tablas; `sqlite3 ... ".schema decision_logs"` válido |
| F0.9 | Crear `CLAUDE.md` y `SESSIONS.md` v2 (referencias actualizadas incluyendo `AI_ACT_MAPPING.md`) | Docs presentes y consistentes |
| F0.10 | Copiar los 4 docs de planificación (`RECONSTRUCTION_AUDIT.md`, `ARCHITECTURE_V2.md`, `RECONSTRUCTION_PLAN.md`, `AI_ACT_MAPPING.md`) a `docs/` del repo v2 | Archivos presentes |
| F0.11 | Copiar también `AGENT_CONTRACTS.md` (esqueleto con agentes nuevos incluidos: `QueryRewriter`, `HITLValidator`) | Archivo presente con plantilla |
| F0.12 | Crear carpetas `observability/`, `evals/`, `compliance/` con esqueletos según `ARCHITECTURE_V2.md` §8 | Carpetas presentes con `__init__.py` |
| F0.13 | **Carpetas `compliance/`** con esqueletos para `art11_doc_generator.py`, `decision_logger.py`, `lineage_tracker.py`, `policy_enforcer.py` | Archivos placeholder con docstrings que apuntan a `AI_ACT_MAPPING.md` |

**Criterio de paso:** repo v2 levanta `python main.py` y devuelve 200 OK en `/health`. BD conectada. Tablas AI Act creadas. No hay código de v1 todavía (solo estructura + dependencias + esqueletos).

---

### FASE 1 — Core agéntico + base AI Act (4-5 sesiones)

**Objetivo:** infraestructura LangGraph + agentes Data + Calculation + Permission funcionando, batería S77 pasa, **Query Rewriter operativo**, **Decision Logger persistiendo**, **Data Lineage Tracker funcionando**.

| Paso | Acción | Sesión |
|---|---|---|
| F1.1 | `core/state.py` — `CDGState(MessagesState)` completo según spec §3 ARCHITECTURE_V2 **incluyendo todos los campos AI Act** (`data_lineage`, `decision_log_id`, `confidence_score`, `original_query`, `rewritten_query`, `query_rewriter_metadata`, `hitl_status`, `hitl_metadata`, `user_feedback`, `policy_violations`, `model_version`, `effect_decomposition`, `confidence_breakdown`) | S+1 |
| F1.2 | `config/data_config.py`, `business_rules.py`, `brand_config.py`, `settings.py` (incluyendo LangSmith vars + flags de feature compliance) | S+1 |
| F1.3 | `config/compliance_config.py` *(nuevo)* — políticas configurables por cliente: umbrales de confidence, qué triggers activan HITL, retención de logs, etc. | S+1 |
| F1.4 | `observability/langsmith_config.py` — setup tracing + integración en arranque FastAPI · **Tags de compliance** definidos en `observability/langsmith_tags.py` | S+1 |
| F1.5 | `compliance/decision_logger.py` *(nuevo)* — servicio de persistencia que escribe en tabla `decision_logs` al final de cada request. Llamado como callback desde `NarratorAgent` y desde el grafo en errores | S+1 |
| F1.6 | `compliance/lineage_tracker.py` *(nuevo)* — middleware que envuelve `DataAgent` para anotar source en cada cifra | S+2 |
| F1.7 | `core/graph/nodes/query_rewriter.py` *(nuevo)* — primer nodo del grafo. Normaliza, expande abreviaturas, detecta ambigüedad. Guarda `original_query` y `rewritten_query` en estado | S+2 |
| F1.8 | `core/graph/orchestrator.py` — entry point + clasificador de intención (1 LLM call) · Recibe `rewritten_query` como input | S+2 |
| F1.9 | `core/agents/base_agent.py` + `react_agent.py` (clase abstracta común con hooks de compliance) | S+2 |
| F1.10 | `core/graph/nodes/permission_agent.py` + `utils/auth.py` (transversal) · **Hook al `PolicyEnforcer` ya preparado** (implementación completa en F2) | S+3 |
| F1.11 | `data/database.py` (connection mgmt) + `data/queries/*.py` (SQL puro, refactor de v1) | S+3 |
| F1.12 | `core/graph/nodes/data_agent.py` + `core/tools/sql_tools.py` (atómicas) · **Cada query devuelve dict con `value` + `lineage`** vía `LineageTracker` | S+3 |
| F1.13 | `data/calculator.py` — funciones `calc_margen_neto`, `calc_redistribucion`, `calc_semaforo`, `calc_kpis_gestor`, etc. · **Propagan lineage** | S+4 |
| F1.14 | `core/graph/nodes/calculation_agent.py` (sin LLM, determinista) · **Lee lineage del raw_data y lo propaga a calculated_kpis** | S+4 |
| F1.15 | `core/graph/edges.py` — routing query_rewriter → orchestrator → permission → data → calculation → narrator (placeholder) | S+4 |
| F1.16 | `core/prompts/*.j2` — plantillas Jinja2 con variables de config · Plantilla `query_rewriter.j2` incluida | S+4 |
| F1.17 | `evals/s77_functional.py` + `evals/datasets/s77_battery.json` — tests S77 (48 preguntas) migrados | S+5 |
| F1.18 | **`evals/compliance_eval.py` v0** — primera versión: verifica que cada respuesta tiene `decision_log_id` persistido y `data_lineage` no vacío | S+5 |
| F1.19 | Verificar trazas en LangSmith: cada request muestra Query Rewriter → Orchestrator → agentes → tools con tags `compliance:` correctas | S+5 |

**Criterio de paso:**
- **48/48 tests S77** pasan en v2.
- Trazas LangSmith visibles para cada test con dimensión compliance.
- `compliance_eval.py` v0 pasa: cada request persiste decision log con linaje.

Si no, no se avanza a Fase 2.

---

### FASE 2 — Agentes de respuesta + capa de explicabilidad (3-4 sesiones)

**Objetivo:** cerrar el flujo end-to-end con calidad cualitativa ≥4.5/5 y capa AI Act de explicabilidad funcionando (Effect Decomposer, Confidence Scorer, Policy Enforcer, HITL Validator backend).

| Paso | Acción | Sesión |
|---|---|---|
| F2.1 | `core/graph/nodes/insight_agent.py` (1 LLM call, contexto = raw_data + calculated_kpis + lineage) | S+6 |
| F2.2 | `core/tools/effect_decomposer.py` *(nuevo)* — método fijo de descomposición precio · volumen · mix · riesgo. Tool invocable desde `CalculationAgent` o como nodo independiente | S+6 |
| F2.3 | `core/graph/nodes/calculation_agent.py` ampliado — invoca `EffectDecomposer` cuando la query implica variación temporal o comparación. Escribe `state.effect_decomposition` | S+6 |
| F2.4 | `core/graph/nodes/narrator_agent.py` con plantillas separadas `narrator_executive.j2` y `narrator_gestor.j2` · **Las plantillas reciben `effect_decomposition` y `data_lineage` y los renderizan en la respuesta** | S+6 |
| F2.5 | `compliance/confidence_scorer.py` *(nuevo)* — hook al final del `NarratorAgent`. Puntúa output 0.0–1.0 según breakdown: calidad del dato · cobertura histórico · ajuste a precedentes · presencia de lineage · presencia de descomposición | S+7 |
| F2.6 | `compliance/policy_enforcer.py` *(nuevo)* — implementación completa. Extensión de `PermissionAgent`. Lee `config/compliance_config.py` y aplica políticas: rangos permitidos, datos accesibles, acciones bloqueadas. Escribe `state.policy_violations` | S+7 |
| F2.7 | `core/graph/nodes/hitl_validator.py` *(nuevo)* — agente que decide si activar HITL según `confidence_score`, `policy_violations` y configuración. Escribe `state.hitl_status="pending"` cuando aplica. UI llega en F4; el backend ya queda preparado | S+7 |
| F2.8 | `core/graph/nodes/forecast_agent.py` integrado al grafo LangGraph (heredando motor v1) · **Propaga lineage de los datos de entrada al output del forecast** | S+8 |
| F2.9 | `core/graph/nodes/context_enricher.py` (sin LLM, datos del periodo + rol) | S+8 |
| F2.10 | Activar **prompt caching Azure OpenAI** en system prompts + tool definitions | S+8 |
| F2.11 | `core/tools/chart_config_tools.py` — `configure_chart_labels()` para etiquetas dinámicas | S+8 |
| F2.12 | `evals/s88_qualitative.py` — batería S88 con LangSmith datasets + LLM judge automático · **Criterios de evaluación incluyen presencia de descomposición y citación de lineage** | S+9 |
| F2.13 | `evals/compliance_eval.py` v1 — ampliado: verifica `confidence_score` poblado, `effect_decomposition` cuando aplica, `policy_violations` correctamente disparado, `hitl_status` poblado | S+9 |
| F2.14 | `evals/latency_eval.py` — benchmark de latencias por tipo de consulta. **Incluye overhead añadido por Query Rewriter, Lineage Tracker y Confidence Scorer** | S+9 |

**Criterio de paso:**
- **Score cualitativo ≥4.5/5** en batería S88 (idealmente igualar o superar v1 4.6-4.8).
- **`compliance_eval.py` v1 pasa al 100%**.
- **Latencia** dentro de objetivo (simple <2.5s, compleja <5.5s, forecast <3.5s — incrementos vs v1 absorben overhead AI Act).

Si no llega, iterar prompts y configuración antes de Fase 3.

---

### FASE 3 — Knowledge base producción (2 sesiones)

**Objetivo:** RAG con multi-formato + metadata + citaciones operativo. **El sistema de citación de KnowledgeAgent comparte infraestructura con `LineageTracker`** — un único modelo de linaje para datos y conocimiento.

| Paso | Acción | Sesión |
|---|---|---|
| F3.1 | Setup ChromaDB local. Si falla en Windows: pivote a LanceDB o FAISS+SQLite | S+10 |
| F3.2 | `knowledge/loader.py` con parsers PDF (pypdf), DOCX (python-docx), TXT, MD | S+10 |
| F3.3 | Schema `DocumentMetadata` (Pydantic) + chunking estrategia (~500 tokens) | S+10 |
| F3.4 | `knowledge/retriever.py` — RAG con top-k similitud + filtros metadata ChromaDB | S+10 |
| F3.5 | `knowledge/citator.py` — inyección `[Fuente: titulo, p.X]` · **Genera `lineage` items con el mismo schema que `LineageTracker`** y los escribe en `state.data_lineage` | S+11 |
| F3.6 | `core/graph/nodes/knowledge_agent.py` integrado al grafo · Propaga lineage al `NarratorAgent` | S+11 |
| F3.7 | Endpoint `POST /knowledge/upload` para carga admin de documentos · **Valida metadata obligatoria** (area, tipo, fuente) | S+11 |
| F3.8 | Cargar 5-10 documentos de prueba (informes banco, normativa muestra) y validar retrieval + citación + lineage unificado | S+11 |
| F3.9 | `evals/compliance_eval.py` v2 — añade tests específicos de KnowledgeAgent: ¿toda respuesta de knowledge cita fuente? ¿el lineage está poblado correctamente? | S+11 |

**Criterio de paso:**
- Consultar "¿qué dice la circular X sobre Y?" devuelve respuesta con cita explícita y enlace.
- `data_lineage` tiene items tanto de tipo `data_source` (queries) como `knowledge_source` (RAG).
- `compliance_eval.py` v2 pasa al 100%.

---

### FASE 4 — Frontend mínimo + capa de transparencia (2-3 sesiones)

**Objetivo:** **NO rehacer el frontend visual** (la calidad visual está consolidada y no se toca). Limpiar la lógica de negocio que vive en frontend (`analyticsService.js` god-object) **y añadir solo los componentes nuevos necesarios para AI Act y feedback de usuario**.

**Reducción intencionada vs revisión 1 del plan:** se eliminan los pasos de rework de theme (F4.1, F4.2 originales), split de Views (F4.7) y refactor de Dashboard components (F4.6) — esos se posponen como mantenimiento futuro si surge necesidad. La calidad visual actual se respeta.

| Paso | Acción | Sesión |
|---|---|---|
| F4.1 | Refactor `analyticsService.js` → cliente HTTP fino (~500 líneas). Definiciones de métrica desde backend. *Único refactor estructural retenido del plan original — necesario porque la lógica de negocio en frontend rompe la trazabilidad AI Act* | S+12 |
| F4.2 | Eliminar strings hardcoded de cliente (`sistemas@bancamarch.es`) — toda referencia via `BRAND_CONFIG` | S+12 |
| F4.3 | **`<FeedbackWidget>` *(nuevo)*** — botón 👍/👎 + textarea opcional debajo de cada respuesta del NarratorAgent. POST a `/chat/feedback` | S+12 |
| F4.4 | **`<DataLineagePopover>` *(nuevo)*** — al hacer click en una cifra del output, muestra popover con `{tabla, campo, periodo, validador, timestamp}`. Consume `state.data_lineage` | S+13 |
| F4.5 | **`<ConfidenceBadge>` *(nuevo)*** — badge discreto al pie de cada respuesta con el `confidence_score`. Tooltip muestra breakdown | S+13 |
| F4.6 | **`<EffectBreakdown>` *(nuevo)*** — componente colapsable que muestra la descomposición precio · volumen · mix · riesgo cuando aplica | S+13 |
| F4.7 | **`<HITLConsole>` *(nuevo)*** — vista solo accesible a usuarios con rol `validator`. Muestra queue de outputs con `hitl_status="pending"`. Permite validar / rechazar / override con motivo. Persiste en `hitl_overrides` | S+13 |
| F4.8 | `components/export/DashboardExporter.jsx` + endpoint `POST /export/snapshot` | S+14 |
| F4.9 | Templates HTML/email con Jinja2: inline-CSS, max-width 600px, SVG inline para gráficos | S+14 |
| F4.10 | Loop de feedback completo: feedback → endpoint → BD → LangSmith Datasets (para alimentar mejora continua) | S+14 |

**Criterio de paso:**
- Frontend funcionalmente completo con feedback + lineage + confidence + HITL + export.
- **Cero regresión visual** vs el estado actual.
- Export a email funciona en Outlook / Gmail.
- Un feedback de usuario aparece en LangSmith Dataset al cabo de pocos segundos.

---

### FASE 5 — QA + readiness AI Act completa (2 sesiones)

**Objetivo:** sistema demo-ready con calidad equivalente o superior a v1 **y** readiness AI Act demostrable: `Art11DocGenerator` funcionando, robustness eval pasando, documentos del proveedor redactados.

| Paso | Acción | Sesión |
|---|---|---|
| F5.1 | Batería completa: 48 funcional (S77) + 21 cualitativo (S88) + tests forecast (5/5 S87) + tests knowledge (5 nuevos) + `compliance_eval.py` v3 | S+15 |
| F5.2 | `evals/robustness_eval.py` *(nuevo)* — batería adversarial: prompt injection, queries ambiguas, datos vacíos, períodos fuera de rango. Soporta Art. 15 | S+15 |
| F5.3 | Performance: latencia por tipo de consulta. Objetivo final: simple <2.5s, compleja <5.5s, forecast <3.5s, knowledge <4.5s (incluye overhead AI Act) | S+15 |
| F5.4 | Edge cases: gestor sin datos, periodo fuera de rango, permisos denegados, ChromaDB vacío, Prophet con <3 meses datos, **HITL bypass intentado**, **prompt con injection conocida** | S+15 |
| F5.5 | **`compliance/art11_doc_generator.py` *(nuevo)*** — meta-tool que lee `AGENT_CONTRACTS.md` + `ARCHITECTURE_V2.md` + datasets de evals + métricas LangSmith y produce `docs/ART11_TECHNICAL_DOC.md` actualizado | S+16 |
| F5.6 | **`docs/USER_MANUAL.md` *(nuevo)*** — manual del desplegador. Propósito previsto, limitaciones, ejemplos de uso correcto/incorrecto, supervisión recomendada | S+16 |
| F5.7 | **`docs/QMS.md` *(nuevo)*** — sistema de gestión de calidad de Accenture como proveedor. Plantilla con procesos: gestión de cambios, gestión de incidentes, control de versiones, plan de retención de logs | S+16 |
| F5.8 | **`docs/RISK_REGISTER.md` *(nuevo)*** — registro de riesgos vivo con probabilidad, impacto, mitigación. Pre-poblado con los riesgos listados en `AI_ACT_MAPPING.md` §5 | S+16 |
| F5.9 | Observabilidad completa: dashboard `/observability/metrics` + verificar trazas LangSmith end-to-end para cada tipo de consulta | S+16 |
| F5.10 | **Compliance dashboard `/compliance/metrics`** *(nuevo)* — vista agregada: % requests con HITL · % outputs con confidence ≥ umbral · nº de overrides / mes · tasa de feedback negativo | S+16 |
| F5.11 | Docs final: `CLAUDE.md` v2 actualizado · `ARCHITECTURE.md` con diagramas reales · `AGENT_CONTRACTS.md` completo · `AI_ACT_MAPPING.md` §6 actualizado con cierre real | S+16 |
| F5.12 | Tag `v2.0.0` + release notes (incluyen sección "AI Act readiness") | S+16 |

**Criterio de paso:**
- Todos los tests verdes.
- Score cualitativo ≥ v1 final (4.6-4.8).
- `compliance_eval.py` v3 pasa al 100%.
- `robustness_eval.py` pasa al 100%.
- `ART11_TECHNICAL_DOC.md` generado y consistente.
- Latencias dentro de objetivo.
- Demo firmado.

---

## 3. Criterios de calidad transversales (todas las fases)

| # | Regla | Cómo se verifica |
|---|---|---|
| 1 | Cada agente tiene contrato definido en `AGENT_CONTRACTS.md` | Inspección manual al cerrar fase |
| 2 | Cero hardcoding de valores de negocio en código de agentes/queries | `grep` por cifras conocidas fuera de `config/` |
| 3 | Toda tool atómica y testeable de forma independiente | `pytest backend/tests/tools/` con coverage ≥80% |
| 4 | Sistema de permisos transversal, no acoplado a agente concreto | `PermissionAgent` + `PolicyEnforcer` invocados desde el grafo |
| 5 | System prompts como plantillas Jinja2 con variables | `ls core/prompts/*.j2` y ausencia de strings de prompt en código Python |
| 6 | Tests S77 (48 preguntas) pasan al final de Fase 1 | Script automático |
| 7 | Score cualitativo S88 (21 preguntas) ≥4.5/5 al final de Fase 2 | Script automático con LLM judge |
| 8 | Prompt caching Azure OpenAI activo en Fase 2+ | Métrica de tokens cacheados en logs |
| 9 | LangSmith trazando cada request end-to-end con tags de compliance | Dashboard LangSmith muestra runs con `compliance:*` tags |
| 10 | Evals automatizados en LangSmith | `evals/s77_functional.py`, `s88_qualitative.py`, `compliance_eval.py`, `robustness_eval.py` ejecutables |
| 11 | KnowledgeAgent cita fuentes en cada respuesta de knowledge | Test específico de citaciones |
| 12 | Frontend sin residuos "BancaMarch", calidad visual intacta vs v1 | `grep -r "bancamarch\|banca march" frontend/src/` vacío. **Diff visual comparado con screenshots de v1** |
| 13 | CLAUDE.md, SESSIONS.md, AI_ACT_MAPPING.md §6 actualizados al cierre de cada sesión | Inspección manual |
| 14 | **Cada request del agente produce un `decision_log` persistido con linaje** | Test automático: contar filas en `decision_logs` antes y después de un request |
| 15 | **Cada output tiene `confidence_score` y lo expone en UI vía `<ConfidenceBadge>`** | Test funcional E2E |
| 16 | **HITL queue funcional**: outputs con confidence bajo o policy violations llegan a `<HITLConsole>` | Test E2E con configuración que fuerza HITL |
| 17 | **Feedback de usuario llega a LangSmith Dataset** | Submit feedback de prueba y verificar aparición en dataset |
| 18 | **`ART11_TECHNICAL_DOC.md` se regenera correctamente al ejecutar `Art11DocGenerator`** | Smoke test del meta-tool |

---

## 4. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| ChromaDB no compila en Windows | Media | Alto | Plan B: LanceDB o FAISS+SQLite desde F3.1 |
| Prompt caching Azure OpenAI requiere ≥1024 tokens | Cierta | Bajo | Diseñar system prompts con tools embebidas para superar umbral |
| Tests S77 dependen de detalles internos de v1 | Media | Medio | Documentar inputs/outputs esperados antes de F0; ajustar tests si v2 cambia API legítimamente |
| Rebuild completo lleva 15-19 sesiones (vs 16 del plan original) | Cierta | Medio | Si demo urgente: priorizar F0-F2 + F4.3-F4.5 (feedback + lineage UI) como MVP; F5 readiness puede diferirse |
| Regresión cualitativa al cambiar prompts a Jinja2 | Media | Alto | Score S88 antes y después de cada migración. Si baja >0.3, revertir e iterar |
| LangGraph cambia API entre versiones | Baja | Medio | Pinear versiones en `pyproject.toml`. Actualizar solo entre fases |
| **Query Rewriter introduce regresión al cambiar la pregunta del usuario** | Media | Medio | Mantener `original_query` siempre accesible. Eval específico: comparar respuesta sobre `original` vs `rewritten` |
| **Overhead de Lineage Tracker eleva latencia** | Media | Medio | Lineage como dict ligero, no objeto pesado. Benchmark continuo en F2.14 |
| **Confidence scoring inconsistente entre runs** | Media | Alto | Calibrar contra batería S88 manualmente labeled. Documentar metodología en `compliance/confidence_scorer.py` |
| **Política HITL demasiado agresiva → fricción de usuario** | Media | Medio | Umbrales configurables en `config/compliance_config.py`. Default conservador para el cliente; ajustar tras feedback piloto |
| **Decision logs crecen demasiado en BD** | Cierta | Bajo | Política de retención en `compliance_config.py` (default 18 meses) + script de archive |
| **AI Act se actualiza con guidance nueva** | Cierta | Medio | `AI_ACT_MAPPING.md` se revisa trimestralmente. Cambios significativos disparan nuevo release |
| **Cliente solicita modificación de algún componente AI Act por su política interna** | Cierta | Bajo | `config/compliance_config.py` permite parametrizar la mayoría de comportamientos sin tocar código |
| Inconsistencia de períodos persiste tras refactor | Media | Bajo | `config/data_config.py` único source. Lint script en CI |
| Carga inicial de documentos knowledge es manual | Cierta | Bajo | UI admin para upload masivo en F3.7. Backup: script CLI |
| Performance del grafo LangGraph (overhead) | Baja | Medio | Medir latencia desde F1.15; si overhead >500ms vs llamada directa, considerar grafos pre-compilados |

---

## 5. Mapping v1 → v2 (qué se hereda, qué se reescribe)

| Componente v1 | Veredicto audit | Acción en v2 |
|---|---|---|
| `chat_agent.py` (2.342 líneas) | RECONSTRUIR | Sustituido por `QueryRewriter` + `Orchestrator` (~250 líneas combinadas) + grafo LangGraph |
| `cdg_agent.py` | REFACTORIZAR | Eliminado como agente. Funcionalidad → `DataAgent` + `CalculationAgent` + `NarratorAgent (executive)` |
| `gestor_agent.py` | REFACTORIZAR | Eliminado como agente. Funcionalidad → mismos agentes con plantilla `narrator_gestor.j2` |
| `forecast_agent.py` | REFACTORIZAR | Reintegrado como nodo `forecast_agent.py`. Motor `forecast/` heredado intacto |
| `query_router.py` | REEMPLAZADO | Reemplazado por **`QueryRewriter` + `Orchestrator`** (clasificación LLM-based con normalización previa) |
| `gestor_queries.py` (2.189) | RECONSTRUIR | Split en `data/queries/{ingresos,gastos,contratos,gestores,centros,productos,desviaciones}.py` con SQL puro. **Cada query retorna `(data, lineage)`** |
| `incentive_queries.py` | RECONSTRUIR | Idem |
| `basic_queries.py`, `comparative_queries.py`, `deviation_queries.py` | REFACTORIZAR | Funciones útiles migradas; cálculos extraídos a `data/calculator.py` |
| `period_queries.py` | MANTENER | Migrado a `data/queries/periodos.py` |
| `forecast_queries.py` | MANTENER | Migrado tal cual |
| `forecast/*.py` | MANTENER | Heredado intacto a `forecast/` v2 |
| `tools/kpi_calculator.py` | REFACTORIZAR | Funciones a `data/calculator.py`; thresholds desde `config/business_rules.py` |
| `tools/chart_generator.py` | REFACTORIZAR | Split en `core/tools/chart_config_tools.py` y `data/queries/charts.py` |
| `tools/report_generator.py` | REFACTORIZAR | Migrado a `core/tools/export_tools.py` |
| `tools/sql_guard.py`, `query_parser.py` | MANTENER | Migrados a `core/tools/` |
| `prompts/*.py` (todos) | RECONSTRUIR | Plantillas Jinja2 en `core/prompts/*.j2` |
| `database/db_connection.py` | MANTENER | Migrado a `data/database.py` |
| `config.py` | MANTENER + AMPLIAR | Dividido en `config/{data_config, business_rules, brand_config, settings, compliance_config}.py` |
| `main.py` (3.491 líneas) | RECONSTRUIR | `main.py` queda en ~50 líneas. Endpoints en `api/routes/{chat, kpis, analytics, forecast, export, knowledge, admin, feedback, hitl, decision_log, compliance}.py` |
| `frontend/src/styles/theme.js` | MANTENER ⭐ | **Migrado tal cual. NO se toca la calidad visual** |
| `frontend/src/services/{api, chatService, adminService}.js` | MANTENER | Migrados intactos |
| `frontend/src/services/analyticsService.js` (3.426) | RECONSTRUIR | Cliente HTTP fino (~500 líneas) — único refactor estructural de frontend |
| `frontend/src/services/reportService.js` | REFACTORIZAR | Añadir `exportDashboardSnapshot()` |
| `frontend/src/components/Chat/*.jsx` | MANTENER | Migrados intactos |
| `frontend/src/components/Dashboard/*.jsx` | MANTENER (revisado) | **Ya no se refactorizan** — la calidad visual está y no se toca. Solo se ajusta `analyticsService` que les alimenta |
| `frontend/src/pages/*.jsx` | MANTENER (revisado) | **No se hacen splits**. La organización actual funciona |
| `frontend/src/App.jsx` | REFACTORIZAR (ligero) | Solo eliminar strings hardcoded (`sistemas@bancamarch.es`) |
| `frontend/src/components/` AI Act *(nuevo)* | CREAR | `<FeedbackWidget>`, `<DataLineagePopover>`, `<ConfidenceBadge>`, `<EffectBreakdown>`, `<HITLConsole>` — componentes nuevos sumados a la UI existente |

---

## 6. Verificación de cierre de cada fase

Al cerrar una fase, ejecutar este checklist:

- [ ] Todos los pasos de la fase ✅
- [ ] Criterio de paso ✅ (test/score específico de la fase)
- [ ] `pytest` verde
- [ ] `grep` por hardcoding fuera de `config/` vacío
- [ ] `AGENT_CONTRACTS.md` actualizado con nuevos agentes
- [ ] `AI_ACT_MAPPING.md` §6 actualizado con grado de cumplimiento por artículo
- [ ] Trazas LangSmith verificadas con tags compliance correctos
- [ ] `CLAUDE.md` actualizado si la estructura o estado cambió
- [ ] Entrada en `SESSIONS.md` con resumen detallado de la sesión
- [ ] Commit + tag (`v2.0.0-fase1`, `v2.0.0-fase2`, …)

---

## 7. Cronograma estimado

| Fase | Sesiones | Acumulado |
|---|---|---|
| Fase 0 — Setup + base AI Act | 1 | 1 |
| Fase 1 — Core agéntico + Query Rewriter + Lineage + Decision Logger | 5 | 6 |
| Fase 2 — Agentes respuesta + Effect Decomposer + Confidence + Policy + HITL backend | 4 | 10 |
| Fase 3 — Knowledge unificado con lineage | 2 | 12 |
| Fase 4 — Frontend mínimo + UI AI Act + feedback | 3 | 15 |
| Fase 5 — QA + readiness AI Act + docs proveedor | 2 | 17 |

**17 sesiones** para v2 completo. Camino crítico para demo: Fases 0-2 + F4.3-F4.5 (feedback + lineage UI) ≈ **12 sesiones**.

---

## 8. Plan B: MVP demo acelerado

Si la demo es urgente:

```
Sesión 1:    Fase 0 completa
Sesiones 2-6: Fase 1 (core + Query Rewriter + Lineage + Decision Logger + tests S77 verdes)
Sesiones 7-10: Fase 2 (parcial: hasta F2.7 — HITL Validator backend)
Sesiones 11-12: F4.3-F4.7 (feedback + lineage + confidence + HITL UI)
Sesión 13:    Smoke test + parche final
```

Este MVP entrega: arquitectura nueva + agentes core + capa AI Act funcional + UI mínima. Deja para después: KnowledgeAgent, export HTML/email, `Art11DocGenerator`, robustness eval, docs del proveedor.

---

## 9. Próximos pasos

1. Revisar este plan con María (idea ya aceptada).
2. Si aprobado: la **siguiente sesión** ejecuta **Fase 0** completa.
3. Cada sesión cierra con commit + entrada en `SESSIONS.md` + actualización de `AI_ACT_MAPPING.md` §6.

**Esta sesión NO ejecuta nada de la reconstrucción.** Solo deja los 5 documentos en `docs/` (4 originales + `AI_ACT_MAPPING.md`).

---

## 10. Cómo trabajar con Claude Code en cada sesión

**Modelo de trabajo paralelo:**

- **Claude Code (ejecutor)** — abre los docs de `docs/` al inicio de cada sesión, lee `CLAUDE.md` + el doc específico de la fase + `AI_ACT_MAPPING.md`. Ejecuta los pasos. Al cerrar la sesión actualiza `SESSIONS.md`, `AGENT_CONTRACTS.md` y `AI_ACT_MAPPING.md` §6.
- **Chat de contexto (este chat o sucesor)** — donde se construyen los prompts para cada sesión de Claude Code y se revisan los outputs antes de aceptar el commit.

**Estructura recomendada de prompt para sesión de Claude Code:**

```
SESIÓN [N] — [Fase X · Pasos Fx.y a Fx.z]

CONTEXTO: lee `docs/CLAUDE.md`, `docs/RECONSTRUCTION_PLAN.md` §2 (Fase X)
          y `docs/AI_ACT_MAPPING.md` §2 (artículos relacionados).

OBJETIVO: completar los pasos Fx.y a Fx.z según el plan.

RESTRICCIONES:
- No tocar frontend visual.
- Todo prompt en `core/prompts/*.j2`.
- Cada cambio en agentes debe actualizar `AGENT_CONTRACTS.md`.
- Cada request debe producir un `decision_log` persistido.

ENTREGABLES:
- Código en su sitio según ARCHITECTURE_V2.md §2.
- Tests específicos pasando.
- `SESSIONS.md` con bitácora.
- `AI_ACT_MAPPING.md` §6 actualizado.

ANTES DE CERRAR: ejecuta los criterios de paso de la fase.
```

---

**Fin del plan revisado.**
