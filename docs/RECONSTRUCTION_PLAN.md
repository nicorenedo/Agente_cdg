# RECONSTRUCTION_PLAN.md — Plan de reconstrucción CDG Intelligence v2

> Fecha: 2026-05-08 · Documento 3 de 3
> Acompaña a `RECONSTRUCTION_AUDIT.md` (qué hay) y `ARCHITECTURE_V2.md` (qué construimos).

---

## 0. Principio guía

**De dentro hacia fuera.** Construir primero la infraestructura (estado, BD, config), luego los agentes uno a uno (data → cálculo → respuesta), luego knowledge base, luego frontend, luego mejoras del cliente, finalmente QA.

**Dos criterios de no-regresión obligatorios:**

1. Las **48 preguntas funcionales de S77** deben pasar al final de Fase 1.
2. La **batería cualitativa de S88 (21 preguntas)** debe alcanzar ≥4.5/5 al final de Fase 2.

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

**Objetivo:** crear el repo `cdg-intelligence-v2` listo para programar.

| Paso | Acción | Validación |
|---|---|---|
| F0.1 | Crear repo `cdg-intelligence-v2` (copia de v1 como punto de partida) | `git log` muestra commit inicial |
| F0.2 | Crear estructura de directorios completa según `ARCHITECTURE_V2.md` §2 | `tree backend/ frontend/` coincide con la spec |
| F0.3 | Mover `BM_CONTABILIDAD_CDG.db` activa + datos Prophet (intactos) | `sqlite3 ... ".tables"` lista 14 tablas |
| F0.4 | **Eliminar 7 `.db` de backup** (`pre_s76` … `pre_s84` + `pre_expansion` + `backup_20260315`) | `ls backend/data/` solo muestra 1 `.db` |
| F0.5 | Eliminar `cdg_agent_v6_backup.py` (dead code) | `find . -name "*backup*"` vacío |
| F0.6 | Crear `pyproject.toml` con dependencias: `langgraph`, `langchain`, `langchain-openai`, `chromadb`, `pypdf`, `python-docx`, `jinja2`, `pydantic`, `fastapi`, `prophet`, `pandas`, `sqlalchemy`, `alembic`, `pytest` | `pip install -e .` sin errores |
| F0.7 | Setup Alembic con migración inicial reflejando schema BD actual | `alembic upgrade head` aplica migración 0 sin cambios |
| F0.8 | Crear `CLAUDE.md` y `SESSIONS.md` v2 (referencias actualizadas) | Docs presentes y consistentes |
| F0.9 | Copiar los 3 docs de planificación (`RECONSTRUCTION_AUDIT.md`, `ARCHITECTURE_V2.md`, `RECONSTRUCTION_PLAN.md`) a `docs/` del repo v2 | Archivos presentes |
| F0.10 | Copiar también `AGENT_CONTRACTS.md` (esqueleto vacío) | Archivo presente con plantilla |

**Criterio de paso:** repo v2 levanta `python main.py` y devuelve 200 OK en `/health`. BD conectada. No hay código de v1 todavía (solo estructura + dependencias).

---

### FASE 1 — Core agéntico (3-4 sesiones)

**Objetivo:** infraestructura LangGraph + agentes Data + Calculation + Permission funcionando, batería S77 pasa.

| Paso | Acción | Sesión |
|---|---|---|
| F1.1 | `core/state.py` — `CDGState(MessagesState)` completo según spec §3 ARCHITECTURE_V2 | S+1 |
| F1.2 | `config/data_config.py`, `business_rules.py`, `brand_config.py`, `settings.py` | S+1 |
| F1.3 | `core/graph/orchestrator.py` — entry point + clasificador de intención (1 LLM call) | S+1 |
| F1.4 | `core/agents/base_agent.py` + `react_agent.py` (clase abstracta común) | S+1 |
| F1.5 | `core/graph/nodes/permission_agent.py` + `utils/auth.py` (transversal) | S+2 |
| F1.6 | `data/database.py` (connection mgmt) + `data/queries/*.py` (SQL puro, refactor de v1) | S+2 |
| F1.7 | `core/graph/nodes/data_agent.py` + `core/tools/sql_tools.py` (atómicas) | S+2 |
| F1.8 | `data/calculator.py` — funciones `calc_margen_neto`, `calc_redistribucion`, `calc_semaforo`, `calc_kpis_gestor`, etc. | S+3 |
| F1.9 | `core/graph/nodes/calculation_agent.py` (sin LLM, determinista) | S+3 |
| F1.10 | `core/graph/edges.py` — routing simple → data → calculation → narrator (placeholder) | S+3 |
| F1.11 | `core/prompts/*.j2` — plantillas Jinja2 con variables de config | S+3 |
| F1.12 | Tests S77 (48 preguntas) — script automático que ejecuta y valida | S+4 |

**Criterio de paso:** **48/48 tests S77** pasan en v2. Si no, no se avanza a Fase 2.

---

### FASE 2 — Agentes de respuesta (2-3 sesiones)

**Objetivo:** cerrar el flujo end-to-end con calidad cualitativa ≥4.5/5.

| Paso | Acción | Sesión |
|---|---|---|
| F2.1 | `core/graph/nodes/insight_agent.py` (1 LLM call, contexto = raw_data + calculated_kpis) | S+5 |
| F2.2 | `core/graph/nodes/narrator_agent.py` con plantillas separadas `narrator_executive.j2` y `narrator_gestor.j2` | S+5 |
| F2.3 | `core/graph/nodes/forecast_agent.py` integrado al grafo LangGraph (heredando motor v1 de `forecast/`) | S+6 |
| F2.4 | `core/graph/nodes/context_enricher.py` (sin LLM, datos del periodo + rol) | S+6 |
| F2.5 | Activar **prompt caching Azure OpenAI** en system prompts + tool definitions | S+6 |
| F2.6 | `core/tools/chart_config_tools.py` — `configure_chart_labels()` para etiquetas dinámicas | S+7 |
| F2.7 | Batería S88 cualitativa (21 preguntas) — script automático con scoring | S+7 |

**Criterio de paso:** **score cualitativo ≥4.5/5** en batería S88. Idealmente igualar o superar v1 (4.6-4.8). Si no llega, iterar prompts antes de Fase 3.

---

### FASE 3 — Knowledge base producción (2 sesiones)

**Objetivo:** RAG con multi-formato + metadata + citaciones operativo.

| Paso | Acción | Sesión |
|---|---|---|
| F3.1 | Setup ChromaDB local. Si falla en Windows: pivote a LanceDB o FAISS+SQLite | S+8 |
| F3.2 | `knowledge/loader.py` con parsers PDF (pypdf), DOCX (python-docx), TXT, MD | S+8 |
| F3.3 | Schema `DocumentMetadata` (Pydantic) + chunking estrategia (~500 tokens) | S+8 |
| F3.4 | `knowledge/retriever.py` — RAG con top-k similitud + filtros metadata ChromaDB | S+9 |
| F3.5 | `knowledge/citator.py` — inyección `[Fuente: titulo, p.X]` en respuestas | S+9 |
| F3.6 | `core/graph/nodes/knowledge_agent.py` integrado al grafo | S+9 |
| F3.7 | Endpoint `POST /knowledge/upload` para carga admin de documentos | S+9 |
| F3.8 | Cargar 5-10 documentos de prueba (informes banco, normativa muestra) y validar retrieval | S+9 |

**Criterio de paso:** consultar "¿qué dice la circular X sobre Y?" devuelve respuesta con cita explícita y enlace a documento fuente.

---

### FASE 4 — Frontend v2 (3-4 sesiones)

**Objetivo:** UI con branding Kutxabank + componentes data-driven + export HTML/email.

| Paso | Acción | Sesión |
|---|---|---|
| F4.1 | `frontend/src/theme/{default.js, kutxabank.js, index.js}` + variables CSS | S+10 |
| F4.2 | Eliminar `sistemas@bancamarch.es` y demás strings hardcoded; toda referencia vía `BRAND_CONFIG` | S+10 |
| F4.3 | `components/charts/ConfigurableChart.jsx` con props `format` (€/%/raw), `showValues`, `showPercentages`, `showLegend` | S+10 |
| F4.4 | Frontend consume `state.chart_config` y reconfigura gráficos runtime | S+11 |
| F4.5 | Refactor `analyticsService.js` → cliente HTTP fino. Definiciones de métrica desde backend | S+11 |
| F4.6 | Refactor `KPICards`, `InteractiveCharts`, `DeviationAnalysis`, `DrillDownView` para que sean data-driven (lista de KPIs viene del backend, drill paths configurables) | S+11 |
| F4.7 | Split `GestorView` y `DireccionView` en sub-contenedores (`<XxxMetrics>`, `<XxxAnalytics>`, `<XxxChat>`) | S+12 |
| F4.8 | `components/export/DashboardExporter.jsx` + endpoint `POST /export/snapshot` | S+12 |
| F4.9 | Templates HTML/email con Jinja2: inline-CSS, max-width 600px, SVG inline para gráficos | S+12 |
| F4.10 | Tabla de preferencias de usuario (BD) + endpoint `GET/PUT /users/{id}/preferences` (layout dashboard, charts seleccionados) | S+13 |

**Criterio de paso:** demo Kutxabank visualmente listo (logo, colores, sin "BancaMarch" residual). Export a email funciona en Outlook/Gmail.

---

### FASE 5 — QA y pulido (1-2 sesiones)

**Objetivo:** sistema demo-ready con calidad equivalente o superior a v1.

| Paso | Acción | Sesión |
|---|---|---|
| F5.1 | Batería completa: 48 funcional (S77) + 21 cualitativo (S88) + tests forecast (5/5 S87) + tests knowledge (5 nuevos) | S+14 |
| F5.2 | Performance: latencia por tipo de consulta. Objetivo: simple <2s, compleja <5s, forecast <3s, knowledge <4s | S+14 |
| F5.3 | Edge cases: gestor sin datos, periodo fuera de rango, permisos denegados, ChromaDB vacío, Prophet con <3 meses datos | S+14 |
| F5.4 | Observabilidad: dashboard de tokens/latency/agents_used desde `response_metadata` | S+15 |
| F5.5 | Docs final: `CLAUDE.md` v2 actualizado · `ARCHITECTURE.md` con diagramas reales · `AGENT_CONTRACTS.md` completo con todos los agentes | S+15 |
| F5.6 | Tag `v2.0.0` + release notes | S+15 |

**Criterio de paso:** todos los tests verdes. Score cualitativo ≥ v1 final (4.6-4.8). Latencias dentro de objetivo. Demo Kutxabank firmado.

---

## 3. Criterios de calidad transversales (todas las fases)

| # | Regla | Cómo se verifica |
|---|---|---|
| 1 | Cada agente tiene contrato definido en `AGENT_CONTRACTS.md` | Inspección manual al cerrar fase |
| 2 | Cero hardcoding de valores de negocio en código de agentes/queries | `grep` por cifras conocidas (29, 36, 97, 0.85, 0.15, "2026-04", "100100100100") fuera de `config/` |
| 3 | Toda tool atómica y testeable de forma independiente | `pytest backend/tests/tools/` con coverage ≥80% |
| 4 | Sistema de permisos transversal, no acoplado a agente concreto | `PermissionAgent` invocado desde el grafo, no desde lógica de otros agentes |
| 5 | System prompts como plantillas Jinja2 con variables | `ls core/prompts/*.j2` y ausencia de strings de prompt en código Python |
| 6 | Tests S77 (48 preguntas) pasan al final de Fase 1 | Script automático |
| 7 | Score cualitativo S88 (21 preguntas) ≥4.5/5 al final de Fase 2 | Script automático con LLM judge |
| 8 | Prompt caching Azure OpenAI activo en Fase 2+ | Métrica de tokens cacheados en logs |
| 9 | KnowledgeAgent cita fuentes en cada respuesta de knowledge | Test específico de citaciones |
| 10 | Frontend rebrand Kutxabank sin residuos "BancaMarch" | `grep -r "bancamarch\|banca march" frontend/src/` vacío |

---

## 4. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| ChromaDB no compila en Windows (problemas con C extensions) | Media | Alto | Tener LanceDB o FAISS+SQLite metadata como plan B desde Fase 3.1 |
| Prompt caching Azure OpenAI requiere ≥1024 tokens | Cierta | Bajo | Diseñar system prompts con tools embebidas para superar el umbral; medir tokens al construir |
| Tests S77 dependen de detalles internos de v1 | Media | Medio | Documentar inputs/outputs esperados antes de Fase 0; ajustar tests si v2 cambia API legítimamente |
| Rebuild completo lleva 12-16 sesiones | Cierta | Medio | Si demo Kutxabank es urgente: priorizar Fases 0-2 + branding (F4.1-F4.2) como MVP, dejar Knowledge y export para después |
| Regresión cualitativa al cambiar prompts a Jinja2 | Media | Alto | Score S88 antes y después de cada migración de prompt. Si baja >0.3, revertir e iterar |
| LangGraph cambia API entre versiones | Baja | Medio | Pinear `langgraph` y `langchain` en `pyproject.toml`. Actualizar solo entre fases |
| Inconsistencia de períodos persiste tras refactor | Media | Bajo | `config/data_config.py` único source. Lint script: cualquier `"2025-09"`, `"2025-10"`, `"2026-04"` literal fuera de `data_config.py` falla CI |
| Carga inicial documentos knowledge es manual | Cierta | Bajo | UI admin para upload masivo en Fase 3.7. Backup: script CLI `python -m knowledge.bulk_upload` |
| Performance del grafo LangGraph (overhead) | Baja | Medio | Medir latencia desde Fase 1.12; si overhead >500ms vs llamada directa, considerar grafos pre-compilados |
| Gestor con preferencias guardadas tras update de schema | Baja | Bajo | Migración Alembic compatibilidad hacia atrás; default fallback si campo nuevo no existe |

---

## 5. Mapping v1 → v2 (qué se hereda, qué se reescribe)

| Componente v1 | Veredicto audit | Acción en v2 |
|---|---|---|
| `chat_agent.py` (2.342 líneas) | RECONSTRUIR | Sustituido por `Orchestrator` (~150 líneas) + grafo LangGraph |
| `cdg_agent.py` | REFACTORIZAR | Eliminado como agente independiente. Funcionalidad → `DataAgent` + `CalculationAgent` + `NarratorAgent (executive)` |
| `gestor_agent.py` | REFACTORIZAR | Eliminado como agente independiente. Funcionalidad → mismos agentes con plantilla `narrator_gestor.j2` |
| `forecast_agent.py` | REFACTORIZAR | Reintegrado como nodo `forecast_agent.py` en el grafo. Motor `forecast/` se hereda intacto |
| `query_router.py` | MANTENER | Lógica de keywords absorbida por `Orchestrator` clasificador (1 LLM call sustituye reglas hardcoded) |
| `gestor_queries.py` (2.189 líneas) | RECONSTRUIR | Split en `data/queries/{ingresos,gastos,contratos,gestores,centros,productos,desviaciones}.py` con SQL puro |
| `incentive_queries.py` | RECONSTRUIR | Idem |
| `basic_queries.py`, `comparative_queries.py`, `deviation_queries.py` | REFACTORIZAR | Funciones útiles migradas a `data/queries/`; cálculos extraídos a `data/calculator.py` |
| `period_queries.py` | MANTENER | Migrado tal cual a `data/queries/periodos.py` |
| `forecast_queries.py` | MANTENER | Migrado tal cual |
| `forecast/*.py` | MANTENER | Heredado intacto a `forecast/` v2 |
| `tools/kpi_calculator.py` | REFACTORIZAR | Funciones movidas a `data/calculator.py`; thresholds desde `config/business_rules.py` |
| `tools/chart_generator.py` | REFACTORIZAR | Split en `core/tools/chart_config_tools.py` (config) y `data/queries/charts.py` (datos) |
| `tools/report_generator.py` | REFACTORIZAR | Migrado a `core/tools/export_tools.py` con tool `export_dashboard_snapshot` |
| `tools/sql_guard.py`, `query_parser.py` | MANTENER | Migrados a `core/tools/` |
| `prompts/*.py` (todos) | RECONSTRUIR | Plantillas Jinja2 en `core/prompts/*.j2` |
| `database/db_connection.py` | MANTENER | Migrado a `data/database.py` |
| `config.py` | MANTENER | Ampliado y dividido en `config/{data_config, business_rules, brand_config, settings}.py` |
| `main.py` (3.491 líneas) | RECONSTRUIR | `main.py` queda en ~50 líneas. Endpoints en `api/routes/{chat, kpis, analytics, forecast, export, knowledge, admin}.py` |
| `frontend/src/styles/theme.js` | MANTENER | Migrado a `frontend/src/theme/default.js`. Nuevo `kutxabank.js` |
| `frontend/src/services/{api, chatService, adminService}.js` | MANTENER | Migrados intactos |
| `frontend/src/services/analyticsService.js` (3.426) | RECONSTRUIR | Cliente HTTP fino (~500 líneas), definiciones de métrica desde backend |
| `frontend/src/services/reportService.js` | REFACTORIZAR | Añadir `exportDashboardSnapshot()` con format html/email |
| `frontend/src/components/Chat/*.jsx` | MANTENER | Migrados intactos |
| `frontend/src/components/Dashboard/{KPICards, InteractiveCharts, DeviationAnalysis, DrillDownView}.jsx` | REFACTORIZAR | Data-driven; presets desde backend; formato configurable runtime |
| `frontend/src/components/Dashboard/{GestoresTable, FabricaModelSection}.jsx` | MANTENER | Migrados intactos |
| `frontend/src/pages/{LandingPage, ProjectionsPage, GestorProjectionsPage}.jsx` | MANTENER | Migrados |
| `frontend/src/pages/{GestorView, DireccionView}.jsx` | REFACTORIZAR | Split en sub-contenedores |
| `frontend/src/App.jsx` | REFACTORIZAR | Brand strings desde `BRAND_CONFIG` |

---

## 6. Verificación de cierre de cada fase

Al cerrar una fase, ejecutar este checklist:

- [ ] Todos los pasos de la fase ✅
- [ ] Criterio de paso ✅ (test/score específico de la fase)
- [ ] `pytest` verde
- [ ] `grep` por hardcoding fuera de `config/` vacío
- [ ] `AGENT_CONTRACTS.md` actualizado con nuevos agentes
- [ ] Commit + tag (`v2.0.0-fase1`, `v2.0.0-fase2`, …)
- [ ] Entrada en `SESSIONS.md` de v2 con resumen y próxima fase

---

## 7. Cronograma estimado

| Fase | Sesiones | Acumulado |
|---|---|---|
| Fase 0 — Setup | 1 | 1 |
| Fase 1 — Core agéntico | 4 | 5 |
| Fase 2 — Agentes respuesta | 3 | 8 |
| Fase 3 — Knowledge | 2 | 10 |
| Fase 4 — Frontend | 4 | 14 |
| Fase 5 — QA + pulido | 2 | 16 |

**16 sesiones** para v2 completo. Camino crítico para demo Kutxabank: Fases 0-2 + F4.1-F4.2 (branding) ≈ **9-10 sesiones**.

---

## 8. Plan B: MVP demo Kutxabank acelerado

Si la demo es urgente y no hay tiempo para 16 sesiones, MVP con orden modificado:

```
Sesión 1: Fase 0 completa
Sesiones 2-5: Fase 1 (core agéntico + tests S77 verdes)
Sesiones 6-7: Fase 2 (parcial: solo NarratorAgent + ContextEnricher + ForecastAgent)
Sesión 8: F4.1 + F4.2 (branding Kutxabank)
Sesión 9: Smoke test + parche final
```

Este MVP entrega: arquitectura nueva + agentes core + branding Kutxabank. Deja para después: KnowledgeAgent, export HTML/email, dashboard personalizable.

---

## 9. Próximos pasos

1. Revisar este plan con el usuario.
2. Si aprobado: la **siguiente sesión** ejecuta **Fase 0** completa.
3. Cada sesión cierra con commit + entrada en `SESSIONS.md` de v2.

**Esta sesión NO ejecuta nada de la reconstrucción.** Solo deja los 3 documentos en `docs/`.

---

**Fin del plan.**
