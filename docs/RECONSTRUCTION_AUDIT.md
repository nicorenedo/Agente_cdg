# RECONSTRUCTION_AUDIT.md — Audit crítico CDG Intelligence v1

> Fecha: 2026-05-08 · Sesión de planificación previa al rebuild Kutxabank
> Documento 1 de 3. Acompaña a `ARCHITECTURE_V2.md` y `RECONSTRUCTION_PLAN.md`.

---

## 0. Resumen ejecutivo

**v1 funciona.** A día de hoy:

| Métrica | Valor | Sesión |
|---|---|---|
| Tests funcionales (60 preguntas en 5 grupos) | **48/48** ✅ | S78a |
| Tests de no-regresión (post limpieza datos) | **20/20** ✅ | S84 |
| Calidad cualitativa (21 preguntas, escala 1-5) | **4.4/5** | S88 |
| Calidad post fixes finales | CDG 4.6 · Gestor 4.7 · Forecast 4.8 | S89 |
| Margen entidad | 48.6% | S84 |
| Dispersión gestores | 45.1pp | S84 |
| Datos limpios | sep-2024 a abr-2026 (20 meses) | S76-S84 |
| Proyecciones Prophet | recalibradas, defendibles | S86-S87 |

**v1 no escala.** La arquitectura es frágil para el siguiente cliente:

- Un monolito de 2.342 líneas concentra el 80% del flujo (`chat_agent.py`).
- 4 archivos discrepan sobre el rango de período soportado.
- Las reglas de negocio (márgenes 29%/36%/97%, semáforos, redistribución 85/15) están **cosidas a system prompts** en lugar de configuración.
- El frontend lleva 3.426 líneas de lógica de negocio en `analyticsService.js` que pertenecen al backend.
- Hay **anti-patrones de retry manual** (`S46-retry`) que parchean fallos de diseño ReAct en lugar de corregirlos.

**Decisión:** rebuild con LangGraph, agentes especializados, configuración centralizada y prompts plantillados. Plan completo en `RECONSTRUCTION_PLAN.md`.

---

## 1. Audit Backend / Agents

| Archivo | Líneas | Responsabilidades mezcladas | Problemas críticos | Decisión |
|---|---|---|---|---|
| `chat_agent.py` | **2.342** | 10 (permisos, clasificación, predefined exec, schema inspection, SQL generation, formateo, sesión, agente core, routing CDG/Forecast, prompts) | Monolito god-object · 4-5 LLM calls secuenciales por request · imports directos a queries/tools/db/prompts · `flow_type` con 4 ramas dispatcher | **RECONSTRUIR** |
| `cdg_agent.py` | 477 | 4 (ReAct setup, tools, prompt, request handling) | System prompt 91 líneas con valores hardcoded (centros, márgenes 29/36/97%, narrativa de lanzamiento sep-oct 2024) · retry manual líneas 440-456 (S46) | **REFACTORIZAR** |
| `gestor_agent.py` | 684 | 5 (prompt builder 183 líneas, tool factory 240 líneas, agente, caching, wrappers) | Período "sep-2025 a abr-2026" **contradice** cdg_agent ("sep-2024 a abr-2026") · S46-retry líneas 586-615 · prompt builder embebido | **REFACTORIZAR** |
| `forecast_agent.py` | 321 | 4 (ReAct, tools, prompt, processing) | Cifras hardcoded en prompt ("660k oct-2025", "40k → 660k") · default `'2026-04'` · sin retry (limpio) | **REFACTORIZAR** (extraer cifras) |
| `query_router.py` | 268 | 2 (keyword routing, parameter binding) | Diseño determinista (S40), 0 LLM calls. Mantenible. Default `'2025-10'` línea 254 a actualizar. | **MANTENER** |
| `cdg_agent_v6_backup.py` | ~1.500 | dead code | Dispatcher antiguo a base de keywords, ya superado | **ELIMINAR** |

### Problemas detectados (cita literal)

**Inconsistencia de períodos** — un mismo dato dicho de tres formas:

```python
# cdg_agent.py línea 136
"Periodos con datos financieros: sep-2024 a abr-2026 (20 meses)"

# gestor_agent.py línea 114
"Datos financieros desde sep-2025 hasta abr-2026"

# chat_agent.py líneas 708, 1183, 1187
periodo = '2025-10'  # default repetido 3 veces

# forecast_agent.py línea 305
periodo: str = '2026-04'  # default
```

**Reglas de negocio cosidas al prompt** — `cdg_agent.py` líneas 161-167:

```python
REGLAS DE NEGOCIO:
- Gastos redistribuidos: el coste de fondeo (660001) se imputa solo a Hipotecas;
  otros gastos centrales se redistribuyen proporcionalmente a todos los contratos.
- Semáforo desviaciones: verde <5% | amarillo 5-15% | rojo >15%
- Modelo Fábrica (solo Fondos): Gestora retiene 85%, Banco 15%
- Hipoteca: producto con margen neto ~29% tras imputación de fondeo...
```

Estos valores deben vivir en `config/business_rules.py`, no en una cadena de texto.

**Anti-patrón S46-retry** — `gestor_agent.py` líneas 586-615:

```python
if not used_tools and not _is_casual_reply:
    _force_msg = "[INSTRUCCIÓN OBLIGATORIA DEL SISTEMA]..."
    _messages_retry = [HumanMessage(content=_force_msg)]
    _result_retry = await self._agent_executor.ainvoke({"messages": _messages_retry})
```

Patch sobre fallo de diseño ReAct: si el LLM no llama tools, se le fuerza una segunda llamada manual. La solución correcta es hacer el tool-calling **obligatorio en el system prompt**, no parchearlo a posteriori.

---

## 2. Audit Backend / Queries

| Archivo | Líneas | `def` count | Problema dominante | Decisión |
|---|---|---|---|---|
| `gestor_queries.py` | **2.189** | 310 | Lógica de negocio dispersa · `'100100100100'` (hipoteca) repetido 20+ veces · margen y ROE calculados dentro de la query | **RECONSTRUIR** |
| `comparative_queries.py` | 1.412 | — | Cálculos financieros dentro de queries (línea 187) · funciones delta similares sin abstraer | **REFACTORIZAR** |
| `basic_queries.py` | 1.326 | — | 20+ hardcoded de cuentas (62/64/68/69, 660001) · margen calculado en la query (línea 762, 808) · patrón `get_X_by_Y` repetido 15 veces | **REFACTORIZAR** |
| `incentive_queries.py` | 1.247 | 218 | Mismo caos que `gestor_queries` previsiblemente | **RECONSTRUIR** |
| `deviation_queries.py` | 1.171 | — | Cuentas '640001', '691001', '691002' hardcoded · threshold de desviación dentro de la query (debería ser business layer) | **REFACTORIZAR** |
| `period_queries.py` | 371 | — | Bien estructurada con `QueryResult` dataclass · margen calculado fuera de la query (línea 164) ✓ | **MANTENER** |
| `forecast_queries.py` | 182 | — | SQL pura · formato Prophet-ready (`ds`, `y`) · cálculo de margen post-query | **MANTENER** |

### Patrón duplicado más caro

`SUBSTR(CUENTA_ID, 1, 2) IN ('62','64','66','68','69')` aparece **40+ veces** en los 7 archivos. Debería ser una vista SQL o un constructor de filtros: `account_filter.expense_centrals()`.

`PRODUCTO_ID = '100100100100'` (hipoteca) aparece 20+ veces. Constante única: `PRODUCT_MORTGAGE_ID`.

`SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' ...)` aparece copiado con micro-variaciones — extraer helper de ingresos.

---

## 3. Audit Backend / Prompts

| Archivo | Problema dominante | Decisión |
|---|---|---|
| `system_prompts.py` | God-strings con datos del banco hardcoded ("220 contratos", "351 contratos" tras S84-B3, "48.6% margen") | **RECONSTRUIR** como Jinja2 |
| `cdg_prompts.py` | Mezcla instrucciones de comportamiento con cifras de referencia | **RECONSTRUIR** como Jinja2 |
| `gestor_prompts.py` | Idem; fórmula de redistribución como string en vez de variable | **RECONSTRUIR** como Jinja2 |
| `chat_prompts.py` | Múltiples prompts especializados (~200-300 líneas cada uno) sin templating | **RECONSTRUIR** como Jinja2 |
| `chart_prompts.py` | Prompts de gráficos con métricas hardcoded | **RECONSTRUIR** como Jinja2 |
| `user_prompts.py` | Plantillas de usuario | **REFACTORIZAR** (usable como base) |

**Patrón objetivo:** prompts en `core/prompts/*.j2` con variables `{{ data_range_start }}`, `{{ default_period }}`, `{{ semaforo_thresholds }}`, `{{ user_role }}`. La capa de prompts no debe saber cifras del banco.

---

## 4. Audit Backend / Tools + Forecast + Infra

| Archivo | Líneas | Problema | Decisión |
|---|---|---|---|
| `tools/kpi_calculator.py` | 393 | Thresholds hardcoded (20% excelente, 15% bueno, 8% aceptable líneas 57-62) que **no consultan** `config.py` (donde sí están definidos: `UMBRAL_MARGEN_NETO_MINIMO=12`, `UMBRAL_ROE_MINIMO=8`) | **REFACTORIZAR** |
| `tools/chart_generator.py` | 1.116 | Hace 3 cosas: query + LLM Azure + render. Colores hardcoded líneas 47-58. Violación SRP | **REFACTORIZAR** (split) |
| `tools/report_generator.py` | 679 | Wrapper razonable pero acopla estructura del report con ejecución; prompts importados hardcoded | **REFACTORIZAR** |
| `tools/query_parser.py` | 470 | Asumido SQL guard | **REFACTORIZAR** |
| `tools/sql_guard.py` | 204 | Pequeño y enfocado; security wrapper | **MANTENER** |
| `forecast/prophet_engine.py` | 165 | Wrapper Prophet limpio · cap_factor 1.10 documentado · cache por hash de datos · sin business logic | **MANTENER** ⭐ |
| `forecast/scenario_builder.py` | 208 | 3 escenarios + narrativas · clamp ±5% explícito · narrativas en español, no lógica | **MANTENER** ⭐ |
| `forecast/macro_context.py` | 154 | Pulls ECB + INE con fallbacks (euribor 2.5%, tipos 3.4%, IPC 2.8%) · cache 24h · sin business logic | **MANTENER** ⭐ |
| `forecast/whatif_simulator.py` | 120 | Orquestación limpia · shocks parametrizados · lazy imports anti circular | **MANTENER** ⭐ |
| `database/db_connection.py` | 235 | Wrapper SQLite con context manager · FK enforcement · sin schema hardcoded | **MANTENER** |
| `config.py` | 244 | Pydantic BaseSettings centralizada · constantes de tabla · **infrautilizada por tools/queries** | **MANTENER** (ampliar uso) |
| `main.py` | **3.491** | God file FastAPI · 15+ imports · routing + business logic · endpoints con stubs/fallbacks | **RECONSTRUIR** (split en `routers/`) |
| `database/*.db` (7 backups) | — | `pre_s76`, `pre_s81`, `pre_s83`, `pre_s84`, `pre_2024_expansion`, `pre_expansion`, `backup_20260315` en source control | **ELIMINAR** (todos menos el activo) |

**La capa `forecast/` es la mejor del repo.** Limpia, atómica, reutilizable. Se hereda íntegra a v2.

---

## 5. Audit Frontend

| Archivo / Componente | Líneas | Problema dominante | Decisión |
|---|---|---|---|
| `styles/theme.js` | 94 | **Single source of truth** de colores (#A100FF Accenture, #CC66FF light, #7B00CC dark). Rebrand Kutxabank en 3h cambiando este archivo | **MANTENER** ⭐ |
| `services/analyticsService.js` | **3.426** | God-object · definiciones de métrica que pertenecen a backend (líneas 139-172, 2478-2482) · z-score 2.0 y factor 3.0 hardcoded · fallback semáforo en frontend | **RECONSTRUIR** (cliente HTTP fino) |
| `services/chatService.js` | 995 | WebSocket streaming bien aislado | **MANTENER** |
| `services/api.js` | 854 | Axios con retry exponencial · envelope `{status, data, meta, ts}` · ApiClientError | **MANTENER** |
| `services/reportService.js` | 774 | PDF/XLSX/JSON exports OK · **falta** snapshot dashboard + email export | **REFACTORIZAR** (añadir export HTML/email) |
| `services/adminService.js` | 476 | Metadata aggregator | **MANTENER** |
| `components/Chat/ChatInterface.jsx` | 1.453 | Streaming + Bubble.List, relay limpio al backend | **MANTENER** |
| `components/Chat/ConversationalPivot.jsx` | 804 | Pivot por NLP, integración limpia | **MANTENER** |
| `components/Dashboard/DeviationAnalysis.jsx` | 1.103 | Lógica de semáforo en JS (línea 2936) cuando debería venir del backend · thresholds parametrizables pero defaults hardcoded | **REFACTORIZAR** |
| `components/Dashboard/DrillDownView.jsx` | 978 | Drill-paths Gestor→Cliente→Producto hardcoded (no reordenables) | **REFACTORIZAR** |
| `components/Dashboard/InteractiveCharts.jsx` | 781 | Preset configs (`DIRECTION_PRESET_CHARTS`, `GESTOR_PRESET_CHARTS`) hardcoded líneas 80-138 · `formatBankingValue()` línea 144 sin toggle €/% runtime | **REFACTORIZAR** |
| `components/Dashboard/KPICards.jsx` | 747 | Lista de KPIs hardcoded líneas 74-79 (ROE grupo, total clientes, total contratos, ingresos totales) | **REFACTORIZAR** |
| `components/Dashboard/GestoresTable.jsx` | 293 | Tabla de ranking — OK | **MANTENER** |
| `components/Dashboard/FabricaModelSection.jsx` | 128 | Banda compacta — OK | **MANTENER** |
| `pages/GestorView.jsx` | 917 | Componente fat: orquesta KPI + Charts + Pivot + DrillDown + Chat | **REFACTORIZAR** (split) |
| `pages/DireccionView.jsx` | 630 | Mismo patrón fat | **REFACTORIZAR** (split) |
| `pages/LandingPage.jsx` | 447 | Three.js + selector de gestor — limpio | **MANTENER** |
| `pages/ProjectionsPage.jsx` | 195 | Forecast view | **MANTENER** |
| `pages/GestorProjectionsPage.jsx` | 245 | Forecast gestor | **MANTENER** |
| `App.jsx` | 327 | Router + ConfigProvider antd · email `sistemas@bancamarch.es` hardcoded línea 243 · 8 ocurrencias de `#A100FF` en overrides antd | **REFACTORIZAR** ligero |

**Veredicto frontend:** la base es sólida. El rebrand Kutxabank es trivial (theme.js + 3 strings). El trabajo real está en (a) sacar lógica de negocio de `analyticsService.js` al backend y (b) hacer los componentes Dashboard data-driven en lugar de hardcoded.

---

## 6. Deuda técnica transversal — Top 8

1. **Monolito `chat_agent.py`** — 2.342 líneas, 10 concerns, 4-5 LLM calls secuenciales por request.
2. **Inconsistencia de períodos** — 4 archivos discrepan sobre el rango soportado (sep-2024 vs sep-2025; default 2025-10 vs 2026-04).
3. **Reglas de negocio en system prompts** — márgenes (29/36/97%), semáforos (5/15%), redistribución (85/15) cosidos a strings.
4. **Cadenas secuenciales de LLM calls** — S39 documentó hasta 8 calls en CDG path; `chat_agent` orquesta sin batching ni cache.
5. **Anti-patrón S46-retry** — `cdg_agent` y `gestor_agent` parchean fallos ReAct con retries manuales.
6. **Sin prompt caching** — Azure OpenAI permite cachear system prompt + tools (≥1024 tokens) y ahorrar 75-90% de tokens. No se está usando.
7. **7 `.db` de backup en git** — `pre_s76` a `pre_s84` viven en `database/`. Debería ser Alembic.
8. **`analyticsService.js` god-object** — 3.426 líneas con definiciones de métrica, defaults de threshold y fallbacks de semáforo que deberían vivir en backend.

---

## 7. Resumen ejecutivo final

### Por categoría

| Decisión | Backend | Frontend | Total líneas estimadas |
|---|---|---|---|
| **MANTENER** | forecast/ (4) · period_queries · forecast_queries · db_connection · config · sql_guard | theme · chatService · api · adminService · ChatInterface · ConversationalPivot · GestoresTable · FabricaModelSection · LandingPage · ProjectionsPage (×2) | ~6.000 |
| **REFACTORIZAR** | cdg_agent · gestor_agent · forecast_agent · query_router · basic_queries · comparative_queries · deviation_queries · kpi_calculator · chart_generator · report_generator · query_parser · todos los `prompts/*` | reportService · DeviationAnalysis · DrillDownView · InteractiveCharts · KPICards · GestorView · DireccionView · App | ~10.000 |
| **RECONSTRUIR** | chat_agent · gestor_queries · incentive_queries · main.py | analyticsService | ~9.000 |
| **ELIMINAR** | cdg_agent_v6_backup · 7 `.db` backups | — | ~1.500 |

### Veredicto

v1 alcanzó el listón funcional para una demo en Kutxabank (4.4/5 cualitativo, 48/48 funcional). Pero su **estructura interna no soporta el siguiente cliente** sin duplicar deuda técnica:

- Cada fix requiere tocar el monolito `chat_agent.py` y arriesgar regresiones cruzadas.
- Cualquier cambio de regla de negocio (margen, threshold) implica editar strings de prompts en 5 archivos.
- Rebranding parcial (Kutxabank) está bloqueado por lógica de banco mezclada con presentación.

**Rebuild justificado.** La capa de cálculo bancario (forecast, period_queries, forecast_queries) y la capa de presentación (theme, chatService, api) se heredan como están. El núcleo agéntico se rehace con LangGraph y agentes especializados según `ARCHITECTURE_V2.md`.

---

**Próximo documento:** `ARCHITECTURE_V2.md` — diseño de la arquitectura objetivo.
