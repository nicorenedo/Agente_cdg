# SESSIONS.md — Historial de sesiones CDG Agent

> Historial completo de sesiones, valores de referencia, próximos pasos y pendientes.
> Ver CLAUDE.md para la parte operativa del proyecto.

---

## ✅ Completado (sesiones 1-17)

**S1 — Limpieza repo:** Eliminados archivos basura (DB duplicada, 23 scripts, tests frontend). `chore: limpieza pre-refactor`

**S2 — Reescritura `basic_queries.py`:** 4 bugs corregidos (PRECIO_STD como coste operativo, cuentas gasto incompletas, redistribución oct de GASTOS_CENTRO €0, bloque duplicado). Validado G1 oct: ingresos €32,560, beneficio €26,944, margen 82.75%.

**S3-S4 — Queries backend + agentes:** `period_queries.py`, `gestor_queries.py`, `comparative_queries.py`, `incentive_queries.py` reescritas con patrón correcto (MOVIMIENTOS, no PRECIO_STD como coste). `auth.py` + `gestor_agent.py` creados. Commits: `7fb5e0f`, `83d8db3`.

**S5-S6 — Integración + POC end-to-end:** `main.py` + `api.js` con endpoints chat gestor. Deployment corregido `gpt-5.4`→`gpt-4o`. LangChain migrado a LangGraph `create_react_agent`. POC validado con datos reales en ~7s.

**S7 — Ambos agentes validados:** GestorAgent 3/3, CDGAgent 2/2. Fixes routing `user_role` en `chat_agent.py`/`main.py`, keywords español en `cdg_agent.py`. Commit: `2590270`.

**S8 — Dashboard Gestor funcional:** 6 bugs en `analyticsService.js` (datos mock→reales, pivot dos pasos, endpoints 404). Wiring `GestorView.jsx` corregido (`externalChartData`). Commits: `50f92c2`→`41f37ef`. Bugs React posteriores: loop infinito (`filtersRef`), pivot fallback `success:true`, `chart_prompts.py` fix metric/dimensión CLIENTES. Commits: `74cdb71`, `7000c99`.

**S9 — Dashboard Dirección funcional:** `gestores-ranking` reescrito para INGRESOS/MARGEN_NETO/ROE. Pivot wiring fix. `PIVOTABLE_CONFIG` ampliada. Commit: `9911aa5`.

**S10 — Chat CDG:** Routing expandido (`cdg_intents` + REGLA 2b catch-all CDG), `format_response()` kwargs fix. Commit: `a96db0e`.

**S11-S12 — UI completa + Rebrand:** Fix chart type snake_case. Rediseño UI (theme 8px, index.css). Rebrand "CDG Intelligence", paleta Accenture (#A100FF). Precios REAL ocultos para Gestor. Prompts reescritos (business focus). KPIs iconos, Skeleton loading, Chat header #1A0033. Commits: `fd328a3`, `d3c2969`, `b0baa97`, `9c44f31`, `15f1366`, `cb7b222`, `618348e`.

**S13-S14 — Animaciones + Fix CDG pivot:** framer-motion (stagger cards, fade charts). Botón Volver DireccionView. Fix pivot DireccionView: derivar `userRole` de `options.mode` → `CONTROL_GESTION`. Commits: `1d8e8bf`, `930e54c`, `f7d1925`, `4c90fc3`.

**S15-S16 — Auditoría + corrección BD:** 4 bugs críticos corregidos (gastos sep 12×oct, Bilbao €0, Privada<Minorista, Javier Fernández -201%). 220 contratos, ~2,900 mov. Backup: `BM_CONTABILIDAD_CDG_backup_20260315.db`. Commit: `25ba3c5`.

**S17 — Calidad + ROE grupo:** Hardcoded 216→220 en `cdg_agent.py` + `system_prompts.py`. ROE grupo 75%→36.77% (fondeo €180k + provisión €45k insertados). Commits: `cd63e7e`, `97fcaf8`.

**S18 — Compactación CLAUDE.md + tests + 2 fixes en main.py:**
- CLAUDE.md reducido 40.4k→12.8k chars (commit `73156c8`)
- Fix 1: `/charts/gestores-ranking` `rows[:15]` movido a post-sort → Privada gestores (Javier Fernández €42,995) lideran correctamente rankings INGRESOS/MARGEN_NETO
- Fix 2: `/chat/message` ignoraba `req.user_role` → CDG users ya no bloqueados por guardia de gestor (effective_context merge). Commit `bd8fab9`

**S19 — completada (commit `c857da7`):**
- FIX1 ✅ CDG ROE: `GET /kpis/consolidado` + GLOBAL_KPI type → responde 36.77% correctamente
- FIX2 ✅ CDG evolucion: `get_evolucion_gestores_sep_oct()` + EVOLUCION_GESTORES type → identifica 12 retrocesos
- FIX3 ✅ Margen unificado: `abs(gastos)` en `gestor_queries` y `comparative_queries` → margen consistente
- FILTER ✅ Añadido `'66'` al filtro gastos centrales en 4 archivos → ROE correcto 36.77% (sin él era 67%)
- NEW ✅ `GET /analytics/fabrica` + `FabricaModelSection.jsx` en DireccionView

**S20 — completada (commit `d3788f9` + `.env`):**
- CLAUDE.md: filtro 66 corregido en secciones 5.5 y 9
- Diagnóstico 404: puerto 8000 tiene procesos zombie con código pre-S19. Se creó `frontend/.env` apuntando a puerto 8004 (código S19 correcto)
- Verificados todos los endpoints DireccionView en 8004: 9/9 OK ✅
- Valores de referencia confirmados: gestor 1 margen 44.55% ✅, ROE grupo 36.77% ✅, fábrica cedida 83.98% ✅

**S21 — completada (commit `fe77403`):**
- FIX1: `total_contratos_activos` filtra por FECHA_ALTA≤último día del período. BD: 29 contratos con FECHA_ALTA incorrecto en oct → movidos a `2025-09-01`. Resultado: sep=216 ✓, oct=220 ✓.
- FIX3: `FabricaModelSection.jsx` compactado a banda ~140px. Eliminado gráfico de barras. Variación oct vs sep como texto ▲/▼.
- FIX4: `DeviationAnalysis.jsx` sin `height:'100vh'` ni `minHeight:'95vh'`. Altura adaptativa.

**S22 — YTD implementado y luego revertido:**
- YTD backend implementado en commit `510bb0a`, luego revertido con `git revert 510bb0a` (commit `36ac179`) — decisión: MoM es el modelo correcto.
- Bug fix ✅: `PercentageOutlined` → `EuroCircleOutlined` en FabricaModelSection (commit `d66933c`, NO revertido).

**S23 — completada (commits `36ac179`, `e7dbf08`, `4d8b534`):**
- REVERT ✅: `git revert 510bb0a` → MoM restaurado en los 6 archivos de queries + main.py
- DB scaling ✅: 825 rows `76%` oct-2025 × 1.052806 → oct €624k (+4.04% vs sep €599k ✓)
- Fábrica oct ✅: cedido €123,278 (84.01%), variación +4.54% vs sep
- Labels ✅: `ROE Grupo`, `Ingresos del Mes`, `Cartera Activa`, TopBar "Mes seleccionado"
- Prompts ✅: MoM model note en `gestor_agent._build_system_prompt` + `FINANCIAL_ANALYST_SYSTEM_PROMPT`

**S24 — completada (commits `5036b23`, `d5f8521`, `1e05f63`):**
- FIX ✅: `get_centro_metricas_financieras` aplica FECHA_ALTA. Sep 5 centros: 68+62+30+27+29=**216** ✓
- FIX ✅: `FabricaModelSection` usa período dinámico — sep muestra sep_2025, oct muestra oct_2025, títulos dinámicos
- FIX ✅: CDG agente: `get_contratos_nuevos_periodo` añadido. Agente responde "4 contratos nuevos en oct"

**S25 — completada:**
- Split CLAUDE.md → CLAUDE.md (operativo, <6k chars) + SESSIONS.md (historial completo)

**S26 — completada (commits `48465bc`, `13e1e89`, `229eee1`, `04b7a28`):**
- B1 ✅ App.jsx ConfigProvider: `colorLink:'#A100FF'`, Tabs tokens (inkBarColor/itemSelectedColor), Button colorPrimary explicit
- B2 ✅ KPICards: variation display as Tag (green #52c41a / red #E5002B), Tooltip per card with business descriptions, descriptions updated to spec
- B3 ✅ GestoresTable.jsx: new component with 7 cols, expandable drill-down (productos/by-gestor), seg/centro filters, sort, variation sep→oct Tag; added as "Tabla Detallada" tab in DireccionView
- B4 ✅ @ant-design/x@1.0.6 installed (antd 5.26.7 compatible); ChatInterface: Bubble.List (user #A100FF / assistant #F3E8FF+border) + Sender; markdown bold rendering; backend wiring unchanged

**S49 — completada (commits `0394cde`, `feea66a`..`f3e8a6e`):**

B1 ✅ Ranking por ingresos en COMPARATIVE_PERFORMANCE:
- NEW QUERY ✅ `basic_queries.ranking_gestores_por_ingresos(periodo, limit=15)`: SQL con JOIN MAESTRO_GESTORES/CENTROS/SEGMENTOS/CONTRATOS/MOVIMIENTOS. Filtra solo centros finalistas (IND_CENTRO_FINALISTA=1) y gestores con ingresos > 0. ORDER BY ingresos_total DESC. Validado: G1=Javier Fernández Sánchez €45,265.
- KEYWORDS ✅ BLOQUE 3 ampliado: `'gestores por ingreso'`, `'por ingresos'` → dispatch a COMPARATIVE_PERFORMANCE.
- HANDLER ✅ `_comparative_performance_analysis()`: detecta keywords de ingresos en el mensaje y añade `results['rankings']['ingresos']` con el ranking. Estructura bajo `rankings` dict para que el LLM formatter lo agregue junto con margen/roe/eficiencia.
- VERIFICADO ✅ "dame el top 5 gestores por ingresos en octubre" → flow=CDG_AGENT, analysis_type=comparative_performance, confidence=0.85. Top 3: Javier Fernández €45,265 / Rafael Jiménez €39,790 / Francisco Martínez €38,160.

B2 ✅ PRODUCTO_ANALYSIS handler para análisis global por tipo de producto:
- NEW ENUM ✅ `AnalysisType.PRODUCTO_ANALYSIS = "producto_analysis"` añadido en cdg_agent.py.
- NEW QUERY ✅ `basic_queries.get_producto_kpis_global(periodo)`: KPIs por producto (ingresos, gastos directos, beneficio_neto, margen_neto_pct, n_contratos, n_clientes). Validado: Fondo Renta Variable €302,355 margen 98.04%.
- BLOQUE 0b ✅ `_determine_analysis_type()`: detecta fondos/hipotecario/deposito/que producto/mix de productos → PRODUCTO_ANALYSIS. Antes de BLOQUE 3 para no caer en ranking gestores.
- HANDLER ✅ `_producto_analysis()`: llama `get_producto_kpis_global`, retorna `results.productos`, confidence=0.95.
- DISPATCH ✅ `AnalysisType.PRODUCTO_ANALYSIS: self._producto_analysis` en handlers dict.
- VERIFICADO ✅ "que producto genera mas margen en octubre" → analysis_type=producto_analysis, 3 productos con datos reales. LLM formatea tabla ordenada: Préstamo Hipotecario 98.85% / Fondo RV 98.04% / Depósito -254.64%.

B3 DYNAMIC_SQL — Veredicto: ❌ NO habilitar como fallback:
- Test1: "cuantos contratos nuevos en octubre 2025" → CDG_AGENT responde 220 (total, no los 4 nuevos). INCORRECTO.
- Test2: "cuantos gestores tienen mas de 10 contratos activos" → CDG_AGENT responde "ninguno". INCORRECTO (hay 3 con 12).
- Test3: "ingreso promedio por gestor en octubre" → CDG_AGENT responde €20,800 (€624k/30). PLAUSIBLE pero el sistema ya tiene esta info.
- Conclusión: estos queries caen al catch-all GENERAL_QUERY que no tiene contexto para responderlos con precisión. La solución correcta es añadir predefined handlers específicos (S50 o posterior), no DYNAMIC_SQL.

ROOT CAUSE FIX ⚠️: El backend llevaba corriendo con código anterior a S42 (AnalysisType sin CENTRO_ANALYSIS/PRODUCTO_ANALYSIS). El uvicorn reload=True no detectaba cambios de os.utime(). Solución: matar todos los procesos python3.13 y relanzar el backend. Verificado con `/agent/specializations`: ahora aparecen CENTRO_ANALYSIS y PRODUCTO_ANALYSIS.

ARCHIVOS TOCADOS: `basic_queries.py` (2 métodos nuevos), `cdg_agent.py` (enum + BLOQUE 0b + dispatch + handler + B1 keywords + setdefault).

**S66 — completada (solo diseño, sin cambios en código ni BD):**

Diseño completo del módulo de Proyecciones + ForecastAgent.

VIABILIDAD TÉCNICA:
- Prophet ✅ instala y funciona en Python 3.14. Fit+predict en 8s con 20 puntos.
- ⚠️ Prophet sobreestima sin cap (€1.3M vs €633k real). Fix: growth='logistic' con cap dinámico.
- BCE MIR ✅ tipos hipotecarios eurozona (3.41-3.50%). BCE Euribor 12m ❌ endpoint roto.
- INE IPC ✅ inflación España.
- 20 puntos históricos suficientes para yearly_seasonality.

ARQUITECTURA:
- backend/src/forecast/: prophet_engine.py, macro_context.py, scenario_builder.py, whatif_simulator.py
- agents/forecast_agent.py: ReAct con 5 tools (forecast_base, macro_context, whatif, recommendations, compare)
- queries/forecast_queries.py: series temporales para Prophet (ingresos, contratos, margen)
- 5 endpoints FastAPI: /forecast/base, /whatif, /macro-context, /recommendations, /chat

FRONTEND: ProjectionsPage con 6 componentes (ScenarioConfigurator, ForecastChart, KPICards, MacroPanel, ForecastChat).

PLAN: S67 (ProphetEngine) → S68 (Macro+Scenarios) → S69 (ForecastAgent+API) → S70 (Routing) → S71 (Frontend) → S72 (Tests).

---

**S65 — completada (commit `3480aba`):**

Hotfix: FabricaModelSection.jsx daba ReferenceError: isSep is not defined.
- S64 eliminó la definición de `isSep` pero quedó la referencia en línea 64 (`!isSep && varCedido`).
- Fix: reemplazado `isSep` → eliminado (varDisplay siempre disponible). Renombrado `varSepOct` → `varDisplay`. Label "Variación oct vs sep" → "Variación MoM".

---

**S64 — completada (commits `8b4a3e4`, `8e6fba6`):**

Revisión y corrección backend + frontend tras expansión de datos.

B1 ✅ Backend fix:
- `compare_periodos_metricas` en `period_queries.py` usaba key `gastos_productos` inexistente → fix con `.get()` safe access.
- Tests: CDG con periodo 2024-11 ✅, YoY nov-25 vs nov-24 ✅, MoM mar-26 vs feb-26 ✅, Gestor jun-2025 ✅.

B2 ✅ Frontend: 74 hardcodeos eliminados en 11 archivos:
- `analyticsService.js` (30 ocurrencias), `api.js` (29), `DireccionView.jsx` (3), `GestorView.jsx` (5)
- `KPICards.jsx`: cálculo dinámico de período anterior (reemplaza `=== '2025-10' ? '2025-09'`)
- `GestoresTable.jsx`: función `getPeriodoAnterior()` dinámica (reemplaza hardcode sep/oct)
- `FabricaModelSection.jsx`: período dinámico (reemplaza `isSep === '2025-09'`)
- Defaults cambiados de `'2025-10'` a `'2026-04'` en todos los archivos.
- 0 ocurrencias de `'2025-10'` o `'2025-09'` restantes en frontend/src/.

B4 ✅ Regresión: T8 Bilbao, T13 resumen, T1 gestor, YoY, MoM — todos con datos reales de abr-2026.

---

**S63 — completada (commit `8d18ac1`):**

Generación datos financieros sep-2024 a ago-2025. Script: `backend/scripts/generate_2024_months.py`.

12 meses generados (todos targets ±2%):
- sep-2024: €40k (14 contratos) → ago-2025: €456k (187 contratos)
- Total: ~7,200 movimientos nuevos, ~420 GASTOS_CENTRO, 180 PRECIO_REAL

BD final: 20 períodos con datos financieros (sep-2024 a abr-2026), 19,266 movimientos, 351 contratos, 142 clientes.

YoY contratos NUEVOS (la métrica de captación):
- nov-24→nov-25: 15→17 (+13%), dic-24→dic-25: 10→11 (+10%)
- ene-25→ene-26: 18→21 (+17%), feb-25→feb-26: 20→24 (+20%), mar-25→mar-26: 22→26 (+18%)

YoY ingresos totales (refleja crecimiento de cartera acumulada):
- sep-24→sep-25: €40k→€622k (+1446%) — banco en mes 1 vs mes 13 (esperado)
- abr-25→abr-26: €395k→€633k (+61%) — se normaliza a medida que la base crece

CDG system prompt actualizado con contexto YoY: "banco inició en sep-2024, primeros meses con base baja".

Tests: get_latest_period()→'2026-04' ✅, YoY nov-2025 datos reales ✅, CDG explica crecimiento alto ✅.

---

**S62 — completada (solo análisis, sin cambios en BD ni código):**

Plan generación datos financieros sep-2024 a ago-2025.

AUDITORÍA: cartera activa va de 14 (sep-2024) a 187 (ago-2025) contratos. Ingresos estimados: €40k (sep-24) a €454k (ago-25) usando promedios oct-2025 × 0.93 × estacionalidad.

PROBLEMA YoY: la distribución FECHA_ALTA simula un banco que arranca en sep-2024. Las comparativas interanuales serían +63% a +1459% en vez del +15-20% deseado. Causa: 14 contratos en sep-24 vs 216 en sep-25.

OPCIONES:
- A) Generar y aceptar hiper-crecimiento (1er año del banco). Rápido, narrativa "fase expansión".
- B) Redistribuir FECHA_ALTA a 2022-2023 para que sep-2024 tenga ~180 contratos. YoY realista pero requiere rehacer S60.
- C) Generar datos 2024 pero no usar YoY en demo. Solo MoM (ya funciona bien).

RECOMENDACIÓN: Opción A — generar + nota en prompt explicando el hiper-crecimiento como "primer año de operaciones".

PLAN TÉCNICO: Script S60 reutilizable. ~6,255 movimientos nuevos, ~420 GASTOS_CENTRO, 180 PRECIO_REAL. <30s ejecución. Backup obligatorio.

---

**S61 — completada (commits `ced28b6`, `df9fee6`, `b0c2cfc`, `5c9384a`):**

Generalización hardcodeos backend + conciencia temporal de agentes.

B1 ✅ Queries generalizadas:
- `get_evolucion_gestores(actual, anterior)` reemplaza `get_evolucion_gestores_sep_oct()` (alias mantenido)
- `compare_gestor_periodos(gestor_id, actual, anterior)` reemplaza `compare_gestor_septiembre_octubre()` (alias mantenido)

B2 ✅ CDGAgent actualizado:
- Tool `get_evolucion_sep_oct` → `get_evolucion_mensual(actual, anterior)` con períodos dinámicos
- System prompt: datos sep-2025 a abr-2026, lógica temporal MoM/YoY, default período dinámico vía get_latest_period()

B3 ✅ GestorAgent actualizado:
- Tool `get_evolucion_sep_oct` → `get_mi_evolucion_mensual()` calcula mes anterior automáticamente
- System prompt: períodos dinámicos, sin referencia a "sep-2025/oct-2025"

B4 ✅ CLAUDE.md actualizado con 8 períodos de referencia (sep-2025 a abr-2026, 351 contratos, 12k movimientos)

Tests verificación (5/5 ✅):
- get_latest_period() → '2026-04' ✅
- get_evolucion_gestores('2025-11','2025-10') → 30 gestores con variación ✅
- CDG MoM nov vs oct → get_evolucion_mensual llamada ✅
- CDG resumen abr-2026 → €633k, 351 contratos ✅
- CDG comparativa feb-2026 vs oct-2025 → get_comparativa_periodos + get_metricas_periodo ✅
- GestorAgent evolución mensual nov-2025 → get_mi_evolucion_mensual ✅

PENDIENTE S62: correcciones frontend defaults + batería tests completa.

---

**S60 — completada (commit `57502ad`):**

Generación datos históricos sep-2024 a abr-2026. Script: `backend/scripts/generate_months.py`.

BLOQUE 1 — Correcciones:
- B1.1 ✅ 8 contratos huérfanos corregidos (51 movimientos insertados)
- B1.2 ✅ 185 contratos redistribuidos a sep-2024→ago-2025 (64 Hip, 61 Dep, 60 FRV)
- B1.3 ✅ Oct-2025: +10 contratos (3 Hip, 3 Dep, 4 FRV) + 5 clientes nuevos
- CHECKPOINT: sep-2025=216 contratos ✅, oct-2025=230 contratos ✅

BLOQUE 2 — Nuevos meses (todos targets ±1%):
- nov-2025: €615k (+0.8% vs €610k target), 247 contratos, 17 nuevos
- dic-2025: €576k (-0.7% vs €580k), 258 contratos, 11 nuevos
- ene-2026: €594k (-0.2% vs €595k), 279 contratos, 21 nuevos
- feb-2026: €629k (-0.2% vs €630k), 303 contratos, 24 nuevos
- mar-2026: €646k (-0.2% vs €648k), 329 contratos, 26 nuevos
- abr-2026: €633k (-0.2% vs €635k), 351 contratos, 22 nuevos

TOTALES FINALES: 351 contratos, 142 clientes, 12,057 movimientos (antes: 220/85/2,172).
Crecimiento interanual contratos: +10-20% (nov-nov, dic-dic, ene-ene, feb-feb, mar-mar).
PRECIO_STD actualizado a 2026 (+2.5%). PRECIO_REAL: 120 rows (15/mes × 8 meses).
Backup pre-expansion: BM_CONTABILIDAD_CDG_pre_expansion.db.

NOTA: sep-2025 ingresos cambió de €599,759 a €621,729 (8 contratos huérfanos ahora tienen movimientos). Oct-2025 ingresos cambió de €624k a €660k (10 contratos nuevos). CLAUDE.md necesita actualización de valores referencia.

PENDIENTE S61: generalizar hardcodeos backend (funciones sep/oct, defaults "2025-10").

---

**S59 — completada (solo análisis, sin cambios en BD ni código):**

Plan revisado y definitivo de generación de datos históricos.

AUDITORÍA COMPLETA:
- FECHA_ALTA: 220 contratos concentrados en ene-may 2025 + sep 2025. Gap jun-ago. Necesita redistribuir a sep-2024→ago-2025.
- INTEGRIDAD: 8 contratos sin movimientos (1067,1074,1075,2066,3069,3070,3071,3072) — necesitan fix.
- COLUMNAS: 0 ALTER TABLE necesarios.
- HARDCODEOS BACKEND: 10 ocurrencias en 7 archivos. 3 funciones a renombrar (get_evolucion_gestores_sep_oct, compare_gestor_septiembre_octubre, tool get_evolucion_sep_oct).
- HARDCODEOS FRONTEND: ~50 defaults "2025-10" en analyticsService.js, api.js, DireccionView, GestorView, GestoresTable, FabricaModelSection.
- PRECIO_STD: falta ANNO=2026 (15 INSERTs preparados).

PLAN DEFINITIVO:
- 7a: Redistribuir FECHA_ALTA de 187 contratos a sep-2024→ago-2025 (UPDATE)
- 7b: Corregir oct-2025: +10 contratos + 5 clientes nuevos + movimientos para 8 huérfanos
- 7c: 0 ALTER TABLE
- 7d: Generar nov-2025 a abr-2026: ~68 contratos, ~22 clientes, ~6,430 movimientos
- 7e: Fix 8 contratos huérfanos
- 7f: Generalizar 3 funciones hardcodeadas a sep/oct
- 7g: Fix ~50 defaults frontend
- 7h: PRECIO_STD 2026 (15 INSERTs)

EJECUCIÓN: S60 (BD), S61 (backend), S62 (frontend + tests)

---

**S58 — completada (solo análisis, sin cambios en BD ni código):**

Análisis BD + plan de generación de datos históricos (nov-2025 a abr-2026).

AUDITORÍA:
- No hay scripts de generación en el repo — se crea desde cero
- BD actual: 2 períodos (sep/oct-2025), 220 contratos, 2,172 movimientos, 85 clientes
- CONTRATO_IDs: 1xxx=Hip, 2xxx=Dep, 3xxx=FRV. MAX=3073, MAX_MOV_ID=2800
- No hay FECHA_BAJA en contratos (no se gestionan bajas)
- Gastos centrales en MOVIMIENTOS (CONTRATO_ID NULL): fondeo 660001 ~€180k + provisión 690002 ~€45k
- PRECIO_STD solo para ANNO=2025 — necesita 2026

NARRATIVA 6 MESES APROBADA:
- Nov-2025: €610k (-2.2%), 3 contratos nuevos. Estacionalidad noviembre.
- Dic-2025: €580k (-4.9%), 1 contrato. Cierre de año, mínimo actividad.
- Ene-2026: €595k (+2.6%), 5 contratos. Arranque año + campaña Q1.
- Feb-2026: €630k (+5.9%), 4 contratos. Fondos Q1 rinden frutos.
- Mar-2026: €648k (+2.9%), 3 contratos. Cierre Q1, mejor mes.
- Abr-2026: €635k (-2.0%), 2 contratos. Corrección post-Q1 + Semana Santa.

PLAN TÉCNICO: Script Python, ~6,500 movimientos nuevos, ~18 contratos, ~10 clientes, 90 PRECIO_REAL, 210 GASTOS_CENTRO. Backup pre-expansion obligatorio.

IMPACTO CÓDIGO: tool get_evolucion_sep_oct necesita generalización para cualquier par de meses. PRECIO_STD necesita set ANNO=2026. Resto de queries/tools funciona sin cambios.

---

**S57 — completada (solo tests, sin cambios de código):**

Batería final de confirmación: 27 tests con evaluación DATOS + ROUTING + CALIDAD.

DATOS: 27/27 (100%) — todos los tests obtienen cifras reales. Cero invenciones.
ROUTING: 27/27 (100%) — todos llegan al agente correcto con tools correctas.
CALIDAD: 25/27 (93%) — 2 ⚠️ por limitaciones de GPT-4o (empatía inconsistente T3, verbosidad leve N9).

Comparativa evolutiva:
- S50: DATOS 67%, ROUTING 73%, 15 tests
- S54: DATOS 100%, ROUTING 100%, CALIDAD 67%, 27 tests
- S57: DATOS 100%, ROUTING 100%, CALIDAD 93%, 27 tests

Highlights de calidad post-S56:
- T8 Bilbao: 125w sin 📊 (antes 400w con 📊)
- T9 Madrid vs Bilbao: 141w tabla directa (antes 500w+)
- T15 ingresos oficinas: 90w lista de 5 centros (antes datos parciales)
- N7 dónde enfocar: 149w, recomienda Málaga con datos de 5 centros
- N4 por qué margen 40%: 187w, combina 2 tools (periodo+productos), causa basada en datos

VEREDICTO: Sistema listo para vídeo de demo. Tests recomendados para demo: T1, T2, T5, T6, T7, T8, T9, T13, T14, T15, N1, N5, N7.

---

**S56 — completada (commit `0e51920`):**

Fix quirúrgico al BankingResponseFormatter en chat_agent.py.

DIAGNÓSTICO: El CDG ReAct agent (v7) produce respuestas concisas y bien formateadas, pero el BankingResponseFormatter las re-escribe con su propio LLM call, añadiendo 📊, headers ###, y expandiendo a 300-500 palabras. El formatter recibe el `response_text` del agente como "DATOS REALES" y genera una respuesta NUEVA desde cero.

FIX 1 ✅ Bypass formatter para CDG ReAct: en `_execute_cdg_agent_flow()`, si `cdg_response.content.results.response_text` existe y contiene cifras concretas (`_has_concrete_numbers`), se usa directamente sin pasar por el formatter. Fallback al formatter si el texto está vacío o sin datos.

FIX 2 ✅ Reglas de brevedad en formatter prompt: para rutas no-CDG (PREDEFINED_QUERY, etc.), añadidas reglas de longitud (max 150w directas, max 300w análisis, max 3 recomendaciones) y tono adaptativo al `banking_prompt` del formatter.

Resultados 5 tests problemáticos (antes ⚠️):
- T8 Bilbao: 122w sin 📊, dato al inicio → ✅ (antes 237-400w)
- T9 Madrid vs Bilbao: 134w con tabla comparativa → ✅ (antes 330-500w)
- T12 Evolución: 174w, top mejoradores concisos → ✅ (antes 297-400w)
- N10 Coloquial: 104w sin 📊, directo → ✅ (antes 220-280w)
- N12 Centros: 183w, lista compacta 5 centros → ✅ (antes 341w)

No-regresión ✅: EXEC 178w con 3 tools (completo), causa-efecto 192w (análisis correcto).

CALIDAD estimada: 27/27 (100%) en los tests de S55 que antes fallaban. Global: ~25-26/27 (93-96%).
Latencia reducida: bypass elimina 1 LLM call (~5-8s menos por request CDG).

---

**S55 — completada (commits `e61f03a`, `ce3d377`):**

System prompt refinements para mejorar calidad de respuesta.

B1 ✅ CDGAgent (`cdg_agent.py` CDG_SYSTEM_PROMPT):
- Añadida sección LONGITUD Y FORMATO: max 150w preguntas directas, max 300w análisis profundo, max 3 recomendaciones, sin ### para respuestas cortas.
- Añadida sección TONO ADAPTATIVO: sin 📊 ni encabezado ejecutivo para preguntas informales.
- EFECTO LIMITADO: la respuesta pasa por BankingResponseFormatter en chat_agent.py que sobreescribe el tono. Fix completo requiere ajustar prompt del formatter en S56.

B2 ✅ GestorAgent (`gestor_agent.py` _build_system_prompt):
- Fix Q3: DETECCION DE TONO OBLIGATORIA — primer párrafo empático para frustración/confusión.
- Fix Q4: Añadido mapeo "mejorar/recomendar" → get_mis_productos_detalle + get_mis_kpis. Recomendaciones deben mencionar productos específicos.
- Max 200 palabras, nunca sugerir "optimizar gastos redistribuidos" (gestor no los controla).

Mini-batería 10 tests: 4/9 mejoraron de ⚠️ a ✅ (T11, N3, N9, EXEC). 5 siguen ⚠️ (T8, T9, T12, N10, N12 = todos CDG path, causa: BankingResponseFormatter).

CALIDAD estimada: 22/27 (81%) vs 18/27 (67%) en S54.
DATOS + ROUTING: siguen 27/27 (100%).

PARA S56: ajustar prompt del BankingResponseFormatter en chat_agent.py para que respete brevedad/tono. También: T3 empático solo parcial (GPT-4o inconsistente en detección frustración).

---

**S54 — completada (solo tests, sin cambios de código):**

Batería exhaustiva: 27 tests (15 retest S50 + 12 nuevos). Evalúa DATOS + ROUTING + CALIDAD.

DATOS: 27/27 (100%) — todos los tests obtienen cifras reales de la BD. Cero invenciones.
ROUTING: 27/27 (100%) — todos llegan al agente correcto con las tools adecuadas.
CALIDAD: 18/27 (67%) — problema exclusivamente de verbosidad/formato LLM.

Retest T1-T15: 15/15 DATOS ✅, 15/15 ROUTING ✅. T15 corregido (ReAct llama get_metricas_centro x5 = datos 5 centros completos, antes parcial).

Tests nuevos N1-N12 — todos DATOS ✅ ROUTING ✅. Destacan:
- N1 ✅ Bilbao sep→oct: 2 calls get_metricas_centro(5) con periodo distinto, variaciones % reales
- N5 ✅ "por qué Madrid < Bilbao": explica gastos redistribuidos Madrid €86k (52.6%) vs Bilbao €36k (33.9%)
- N7 ✅ "dónde enfocar esfuerzo": 5 centros consultados, recomienda Palma y Málaga con datos
- N12 ✅ "los demás centros": 5 calls get_metricas_centro, todos los datos completos

Problemas de calidad para S55 (solo system prompt):
- Q1: respuestas 400-800 palabras para preguntas directas (T8/T9/T11/T12/N3/N10/N12)
- Q2: exceso headers ### para preguntas simples
- Q3: apertura empática inconsistente en GestorAgent (T3)
- Q4: recomendaciones genéricas en N9 (falta llamar get_mis_productos_detalle)
- Q5: CDG responde formal cuando la pregunta es coloquial (N10)

---

**S53 — completada (commits `dd4b255`, `3f36d2c`):**

B1 ✅ Fix T14 — routing alertas al CDGAgent:
- REGLA 0 ✅ en `chat_agent.py` `classify_and_route()`: keyword override para CDG users con 'preocupar', 'alertas', 'riesgo', 'desviación', etc. → fuerza CDG_AGENT antes de RULE 1.
- CAUSA RAÍZ: LLM clasificador devolvía `requires_sql=False` o `is_personal=True` para preguntas de alertas, impidiendo que RULE 2b las enviara al CDGAgent.
- VERIFICADO ✅ T14 "hay algo que me deba preocupar" → CDG_AGENT, tools: `get_desviaciones_precio` + `get_ranking_gestores_margen`. Desviaciones reales (Hip 17%, FRV 16.4%, Dep 15.8%) + gestores en pérdidas.
- VARIANTES ✅ "qué alertas hay", "hay desviaciones importantes" → CDG_AGENT correctamente.

B2 ✅ Fix T6 — benchmark gestor vs centro:
- TOOL REWRITE ✅ `get_mi_centro_benchmark` en `gestor_agent.py`: retorno reestructurado con etiquetas explícitas ("Contratos TOTALES del centro", "Media de contratos POR gestor", "TU CARTERA PERSONAL tiene X contratos").
- PROMPT ✅ Añadida regla en RESTRICCIÓN COMPARATIVAS: "los datos de get_mi_centro_benchmark son del CENTRO COMPLETO, NO de tu cartera".
- VERIFICADO ✅ T6: LLM distingue "Tienes 12 contratos" (gestor) vs "media 8.8 por gestor" (centro). Tools: `get_mi_centro_benchmark` + `get_mis_kpis`.

B3 — tool_choice="any": NO implementado.
- `bind_tools` soporta `tool_choice` pero es incompatible con `create_react_agent`: el loop ReAct necesita que el LLM pueda elegir "responder" (sin tool) tras obtener datos. Con `tool_choice="any"` el agente entra en loop infinito de tool calls.
- El retry S46 sigue activo como safety net — funciona correctamente.

REGRESIONES ✅: T12 (evolución), T8 (Bilbao) — sin regresiones.

ARCHIVOS TOCADOS: `chat_agent.py` (REGLA 0 routing), `gestor_agent.py` (benchmark tool + prompt).

---

**S52 — completada (commit `34c880e`):**

CDGAgent v6 (keyword dispatcher) → v7 (ReAct agent con LangGraph `create_react_agent`).
- REWRITE ✅ `cdg_agent.py`: 1,540 → ~400 líneas. 10 tools con `@tool`, system prompt con reglas de negocio, LLM decide qué tools llamar.
- BACKUP ✅ `cdg_agent_v6_backup.py` preservado.
- INTERFACES ✅ CDGRequest/CDGResponse/AnalysisType/create_cdg_agent/process_complex_analysis preservadas.
- VALIDACIÓN POST-RESPUESTA ✅ `_has_concrete_data()` retry si respuesta sin cifras.
- HISTORIAL ✅ 3 últimos turnos por session_id.

Tools: get_resumen_entidad, get_metricas_periodo, get_metricas_centro, get_ranking_gestores_margen, get_ranking_gestores_ingresos, get_evolucion_sep_oct, get_kpis_productos, get_desviaciones_precio, get_comparativa_periodos, get_metricas_gestor_individual.

Tests S52 (7 CDG tests):
- T8 ✅ Bilbao → `get_metricas_centro(5)` → €105,364 / 57.18% margen
- T9 ✅ Madrid vs Bilbao → `get_metricas_centro` × 2 → comparativa completa
- T10 ✅ Productos → `get_kpis_productos` → FRV €302k / Hip €295k / Dep -254%
- T11 ✅ Ranking → `get_ranking_gestores_margen` → Javier Fernández 76.91% #1 (mejora vs S50 ⚠️)
- T12 ✅ Evolución → `get_evolucion_sep_oct` → 12 mejora, 8 estable, 10 retroceso (ANTES ❌ en S50)
- T13 ✅ Resumen → `get_metricas_periodo` → €624k / 39.96% / 220 contratos
- T14 ❌ Alertas → routing issue: chat_agent envía a DYNAMIC_SQL en vez de CDG_AGENT. El agente ReAct no recibe la pregunta. Pendiente para S53.

HALLAZGO: T14 es un problema del clasificador en `chat_agent.py` (IntelligentQueryClassifier no reconoce "hay algo que me deba preocupar" como intent CDG). Fix requiere ajuste en chat_agent, no en cdg_agent.

---

**S50 — completada (solo investigación + tests, sin commits de código):**

BLOQUE 1 — Diagnóstico margen Depósito -254.64%:
- Ingresos oct-2025: €26,518.72 (cuentas 760011+760012)
- Gastos directos: €94,046.42 — dominado por cuenta 640001 "Intereses pagados - Depósitos Plazo Fijo" (€91,888) → línea CDR CR0003 "Gastos Financieros"
- **Veredicto ✅ Dato correcto**: el Depósito es producto de captación (banco paga intereses al cliente). Coste de fondeo imputado directamente. El margen negativo es estructural por diseño del modelo contable — el beneficio real está en las hipotecas financiadas con ese dinero.
- Explicación demo: "El depósito capta liquidez para financiar hipotecas con margen. Visto en solitario es negativo, pero aporta valor al mix de productos."
- FIX INFRAESTRUCTURA: `pydantic-settings` no estaba instalado → Settings usaba clase dummy → GestorAgent no inicializaba → fallback en todos los tests Gestor. Instalado con `pip install pydantic-settings`.

BLOQUE 2 — Batería 15 tests lenguaje informal — **Tasa fiabilidad: 10/15 (67%)**

Tests ✅ (demo-ready): T1 (qué tal voy), T2 (por qué tantos gastos), T3 (no entiendo gastos), T4 (cómo estoy), T5 (qué cosas tengo), T7 (cuánto margen), T8 (cómo Bilbao), T9 (Madrid vs Bilbao), T10 (qué producto da más), T13 (resumen mes)

Tests ⚠️: T6 (benchmark correcto pero LLM confunde contratos gestor=12 con total centro=220), T11 (datos ranking correctos pero flow=general_query en vez de comparative_performance), T15 (detecta pivot centro/INGRESOS pero datos parciales — suma top10 gestores no todos los centros)

Tests ❌: T12 ("evolución respecto al mes pasado" no activa handler EVOLUCION_GESTORES), T14 ("algo que preocupar" cae en DYNAMIC_SQL con columna inexistente pr.CENTRO_CONTABLE)

HALLAZGOS PARA S51:
1. T12: Keywords "evolucionado respecto al mes pasado" no matchean el handler EVOLUCION_GESTORES → añadir keywords
2. T14: No hay handler predefinido para alertas/desviaciones → DYNAMIC_SQL con schema incorrecto
3. T6: LLM confunde contexto de benchmark (datos centro) con cartera propia del gestor
4. T15: Pivot por centros usa datos del top-10 ranking en lugar de query específica de ingresos por centro

## Plan de refactorización S40-S44 — COMPLETADO
- S40: Router determinista — 0 LLM calls en routing (antes hasta 6)
- S41: Caché GestorAgent — invalida automáticamente con período y prompt
- S42: Dispatcher CDG — sin overlaps, catch-all GENERAL_QUERY
- S43: Split system_prompts.py — prompts separados por agente, schema SQL corregido
- S44: Response validation — reintento si respuesta sin cifras concretas
Resultado: arquitectura más fiable, latencia reducida, respuestas con datos reales

---

**S46 — completada (commit `5bfaf27`):**

FIX 1 — GestorAgent no llama tools con lenguaje informal:
- REGLA ABSOLUTA ✅ Bloque explícito en `_build_system_prompt()` mapeando frases informales → tool concreta.
- RETRY ARQUITECTURAL ✅ `process_message()`: si `used_tools == []` y la pregunta no es una respuesta casual (len<8 / saludos), re-invoca LangGraph sin historial previo + instrucción de sistema forzada. Sin historial, el LLM no puede responder desde contexto y DEBE llamar tools.
- VERIFICADO ✅: "oye que tal voy este mes" (gestor 1) → tools=['get_mi_reporte_personal'], 14.4s (2 calls). "como me va el negocio" (gestor 3) → tools=['get_mi_reporte_personal'], 8.6s.
- CAUSA RAÍZ: conversation_history acumulado de sesiones previas hacía que el LLM respondiera sin tools incluso con instrucciones explícitas. Fix: retry con historial vacío.

FIX 2 — Pregunta en inglés no enrutaba al handler correcto:
- KEYWORDS INGLÉS ✅ `cdg_agent.py` BLOQUE 3: añadidos `'manager'`, `'by revenue'`, `'managers by'` (substrings que matchean "managers" en texto).
- KEYWORDS INGLÉS ✅ `query_router.py`: ranking route ampliada con mismas keywords.
- RESULTADO ⚠️: routing CDG_AGENT correcto + dispatch a COMPARATIVE_PERFORMANCE. Pero `ranking_gestores_por_margen_enhanced` es ranking por MARGEN, no por ingresos — el LLM responde honestamente "no tengo datos de revenue específico". Fix completo requeriría una nueva query `ranking_gestores_por_ingresos`.

FIX 3 — Recomendación de producto usa datos inventados:
- NEW TOOL ✅ `get_mis_productos_detalle`: combina `get_contratos_by_gestor` (mix real por producto) + `get_gestor_performance_enhanced` (KPIs). System prompt actualizado: "para preguntas de productos usa get_mis_productos_detalle (no get_mis_desviaciones)".
- RETRY APLICA ⚠️: el retry de FIX 1 también corre para preguntas de producto (13s = 2 calls). GPT-4o sigue respondiendo desde la historia de desviaciones para preguntas de estrategia. Limitación del modelo.
- NOTA: la tool existe y está disponible; el problema es que GPT-4o no la usa para preguntas de "recomendación estratégica" aunque sí para preguntas de "datos de mis productos".

ARCHIVOS TOCADOS: `gestor_agent.py`, `cdg_agent.py`, `query_router.py`.

**S45 — sesión de tests (solo diagnóstico, sin cambios de código):**
- 13 tests ejecutados: 3✅, 6⚠️, 4❌.
- Hallazgos clave: (1) A3 — LLM no llama tools con lenguaje informal (corregido en S46). (2) B2/B4 — CDGAgent sin query de KPIs por CENTRO_ID. (3) C2 — no hay contexto conversacional de charts en CDGAgent. (4) C1 — punto 5 (alertas precio) incorrecto: dice "sin alertas" cuando hay desviaciones >15%.
- Listo para demo: A1, A4, A5a, B5, C1 puntos 1-3.

**S44 — completada:**
- GUARDIA FORMAT_RESPONSE ✅ `BankingResponseFormatter._has_concrete_numbers()`: detecta €, %, o números de 4+ dígitos en la respuesta.
- GUARDIA FORMAT_RESPONSE ✅ `format_response()`: si la respuesta LLM no tiene cifras y hay datos reales, reintenta una vez con instrucción explícita. Temperature 0.2 en retry. Máximo 1 reintento — si el retry tampoco tiene cifras, devuelve igualmente sin bloquear.
- GUARDIA INSIGHTS ✅ `_generate_ai_insights()` en `cdg_agent.py`: si la respuesta del LLM no contiene cifras concretas, reintenta una vez con instrucción explícita antes de parsear los insights.
- LOGGING ✅ Ambas guardias loggean `[S44 GUARD]` con estado (activado/resultado del retry).
- VERIFICADO ✅ Pregunta "como esta la concentracion de riesgo en la cartera": respuesta con 220 contratos, 85 clientes, 11 gestores con margen bajo, cifras exactas.
- VERIFICADO ✅ 4 tests estándar: GestorAgent KPIs (€33,940), CDG ROE 39.96%, ranking gestores (Javier F. 76.91%), evolución sep→oct — todos con cifras concretas.
- ARCHIVOS TOCADOS: `chat_agent.py` (BankingResponseFormatter), `cdg_agent.py` (_generate_ai_insights).

**S43 — completada (commit `14eae5f`):**
- NUEVOS ARCHIVOS ✅ `cdg_prompts.py`: 4 prompts del CDGAgent extraídos de system_prompts (FINANCIAL_ANALYST, FINANCIAL_REPORT, COMPARATIVE_ANALYSIS, DEVIATION_ANALYSIS).
- NUEVOS ARCHIVOS ✅ `chat_prompts.py`: 6 CATALOG_PROMPTS acortados de ~1,220 líneas a ~50 (desde S40 el DeterministicQueryRouter reemplazó el uso LLM de estos catálogos; se mantienen por compatibilidad).
- NUEVOS ARCHIVOS ✅ `gestor_prompts.py`: placeholder que documenta el schema SQL correcto para queries de gestor.
- SQL SCHEMA FIX ✅ `CHAT_SQL_GENERATION_SYSTEM_PROMPT` (prompt activamente usado en flujo DYNAMIC_SQL):
  - `PRECIO_POR_PRODUCTO_STD` como proxy de gastos → correcto: `SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69') AND CONTRATO_ID IS NOT NULL`
  - Gastos centrales: añadir cuenta '66' + `CONTRATO_ID IS NULL`
  - `ABS(SUM(IMPORTE))` documentado (importes negativos en BD)
- SQL SCHEMA FIX ✅ 3 ocurrencias de `LINEA_CDR IN ('MARGEN_INTERES'...)` en prompts huérfanos → `CUENTA_ID LIKE '76%'`
- SHIM ✅ `system_prompts.py`: añadidos re-exports al final del archivo — imports de cdg_prompts y chat_prompts sobreescriben las definiciones originales sin romper los imports existentes de los agentes.
- IMPORTS ✅ `cdg_agent.py`: ahora importa los 4 prompts CDG desde `cdg_prompts.py` directamente.
- VERIFICADO ✅ Los 3 agentes importan en PRODUCTION mode (real DB + Azure OpenAI conectado).
- ARCHIVOS NO TOCADOS: `chat_agent.py` (sigue importando desde `system_prompts.py` que shimmea todo), `gestor_agent.py` (nunca importó de system_prompts).

**S42 — completada (commit `c876d91`):**
- DISPATCHER ✅ `_determine_analysis_type()` reescrito: 9 bloques ordenados de más a menos específico, sin overlaps. Antes: orden frágil con `elif` mezclados e `if` independientes.
- BUG FIX ✅ Patterns regex usados como substrings: `'sep.*oct'` y `'septiembre.*octubre'` nunca matcheaban en el original (`in` es substring, no regex). Reemplazados por frases literales explícitas.
- BUG FIX ✅ `'roe'` removido de GLOBAL_KPI: era demasiado genérico. Reemplazado por `'roe del grupo'`, `'roe global'`, `'roe consolidado'`. "roe" a secas ya no captura queries personales o ambiguas.
- BUG FIX ✅ `'evoluci'` y `'variaci'` (truncaciones) removidos: demasiado anchos — capturaban "variación de costes" como EVOLUCION. Reemplazados por frases completas.
- BUG FIX ✅ `'alert'` (inglés) removido de DEVIATION_DETECTION: overlapeaba con cualquier string que contenga "alert".
- NUEVO ✅ Keywords `'concentracion'`, `'riesgo de concentracion'`, `'riesgo cartera'` añadidas a COMPARATIVE_PERFORMANCE.
- NUEVO ✅ `AnalysisType.GENERAL_QUERY` añadido + `_general_query_analysis()`: catch-all que llama 3 engines (resumen_general + metricas_periodo + ranking_gestores) en lugar de fallar silenciosamente. Antes el fallback era BUSINESS_INTELLIGENCE que puede no tener el contexto correcto.
- VERIFICADO ✅ 6 tests: evolución gestores / concentración cartera / desviaciones precio / ROE grupo / ranking gestores / pregunta no prevista → todos al handler correcto.
- ARCHIVOS: solo `cdg_agent.py` modificado.

**S41 — completada (commit `fa8dfb8`):**
- CACHE KEY ✅ `gestor_agent.py`: nueva función `_compute_agent_key(gestor_id, nombre, segmento, centro, periodo)` → cache key = `f"{gestor_id}:{md5(nombre|segmento|centro|periodo)[:8]}"`. Antes: key era solo `str(gestor_id)` → el período pasado en cada request era ignorado si el gestor ya estaba en caché. Ahora: período diferente = hash diferente = nueva instancia con tools correctamente bakeados.
- TRACEBACK ✅ `process_message()`: exception handler ahora incluye `exc_info=True` → el traceback completo aparece en los logs cuando LangGraph lanza una excepción. Antes: solo el mensaje de error, sin stack trace.
- BACKWARD COMPAT ✅ `get_gestor_agent(gestor_id)`: actualizado para buscar por prefijo `f"{gestor_id}:"` en lugar de exact match. Devuelve la instancia más reciente para ese gestor_id. Usado por endpoints de status/reset en main.py.
- ARCHIVOS: solo `gestor_agent.py` modificado. `main.py` sin cambios (ya pasaba `periodo_default=req.periodo`).

**S40 — completada (commit `1318755`):**
- ROUTER ✅ `query_router.py`: nuevo `DeterministicQueryRouter` con 20 reglas keyword → (catalog, function, params). Reemplaza los 6 LLM calls secuenciales de `_find_predefined_query()` por matching determinista O(n). Unit tests: 7/7 OK.
- WIRING ✅ `chat_agent.py`: `_find_predefined_query()` reescrita — delega al router, elimina `_search_exclusive_catalog()` (que hacía hasta 6 LLM calls). Instancia `self.router` en `IntelligentQueryClassifier.__init__()`.
- FIX ✅ Key mismatch en `classify_and_route()`: `is_personal` leía `'is_personal'` pero el LLM devuelve `'is_personal_query'` → REGLA 1 nunca se disparaba. Corregido con fallback dual.
- VERIFICADO: 4 tests habituales pasan con datos reales — gastos G1 (€3,078 directos / €14,795 redistribuidos), ROE G1 47.34%, gestores que retroceden (9 identificados), desviaciones críticas precio.
- LATENCIA: `_find_predefined_query()` pasa de 0-6 LLM calls a 0 LLM calls (microsegundos). GestorAgent ~7.5s (LangGraph sin cambios), CDG queries ~25s (sin cambio — LLM calls restantes fuera de scope S40).
- ARCHIVOS: solo `chat_agent.py` modificado + `query_router.py` creado. Ningún otro archivo tocado.

**S38 — completada (commit `187d9ec`):**
- REVERT ✅ `kpi_calculator.py` restaurado al estado pre-S37: campos `clasificacion` y `benchmark_vs_sector` de vuelta en todos los métodos
- MOTIVO: `gestor_queries.py` accede a `.get('clasificacion')` en los resultados de `calculate_roe`/`calculate_margen_neto` — al eliminar el campo en S37, los tools del agente lanzaban `KeyError: 'clasificacion'`
- VERIFICADO: `/kpis/gestor/1/roe?periodo=2025-10` devuelve `clasificacion_roe: 'SOBRESALIENTE'`, directos €3,078 / redistribuidos €14,795 ✅
- Los commits de tono empático del agente (S37: `4194437`, `4685b41`) se mantienen intactos

**S37 — completada (commits `8028fe9`, `4194437`, `4685b41`):**
- BLOQUE 1 ✅ `kpi_calculator.py`: eliminadas todas las clasificaciones inventadas
  - `calculate_margen_neto`: eliminado campo `clasificacion` (EXCELENTE/BUENO/ACEPTABLE/BAJO/PERDIDAS)
  - `calculate_roe`: eliminados campos `clasificacion` (SOBRESALIENTE/BUENO/PROMEDIO/BAJO/NEGATIVO) y `benchmark_vs_sector`
  - `calculate_ratio_eficiencia`: eliminados campos `clasificacion` (MUY_EFICIENTE/EFICIENTE/EQUILIBRADO/INEFICIENTE) e `interpretacion` (strings descriptivos)
  - `calculate_crecimiento_captacion`: eliminado campo `clasificacion` (CRECIMIENTO_ALTO/MODERADO/LENTO/DECRECIMIENTO)
  - `_get_clasificacion_global` → `_get_nivel_global`: retorna `'alto'`/`'medio'`/`'bajo'` basado en umbrales numéricos internos. `clasificacion_global` → `nivel_global`
  - `analyze_desviacion_presupuestaria` sin cambios (nivel_alerta = severidad interna, no benchmark sectorial)
- BLOQUE 2 ✅ `gestor_agent.py`: tono adaptativo para gestores frustrados
  - Nueva sección `DETECCIÓN DE TONO Y RESPUESTA EMPÁTICA` en `_build_system_prompt`
  - Apertura empática obligatoria cuando detecta palabras de frustración/urgencia
  - CRÍTICO: siempre llama a herramientas aunque el mensaje sea emocional (anti-respuesta-genérica)
  - Lenguaje de negocio para gastos: prohibidos códigos de cuenta, prosa en lugar de ### headers
  - Cierre con acción concreta obligatorio en todas las respuestas
- PENDIENTE: Reiniciar backend para que el agente cacheado del gestor 1 tome el nuevo system prompt

**S36 — completada (commit `eff619d`):**
- RENAME ✅ "Fondo Banca March" → "Fondo Renta Variable" en toda la aplicación:
  - DB `MAESTRO_PRODUCTOS.DESC_PRODUCTO` (1 fila, PRODUCTO_ID 600100300300)
  - DB `MAESTRO_CUENTAS.DESC_CUENTA` (3 filas: cuentas 760021, 760022, 760023)
  - `backend/tests/test_comparative_queries.py` — comentario fixture
  - `backend/tests/test_deviation_queries.py` — comentario fixture
  - `backend/tests/test_dynamic_config.py` — mock data `DESC_PRODUCTO`
  - `frontend/src/services/analyticsService.js` — label mapping `.replace('Fondo Banca March', 'Fondos CDG')` → `.replace('Fondo Renta Variable', 'Fondo RV')`
- VERIFICADO ✅ API `/charts/productos-popularity?periodo=2025-10` devuelve `"Fondo Renta Variable"` correctamente
- NOTA: Backups preservados en `notebooks/old/`, `notebooks/backups/`, `docs/` y `SESSIONS.md` (historial) — no afectan producción

**S35 — completada (Gestor 1 demo validation):**
- FASE 1 ✅ KPIs G1 oct-2025 verificados contra BD (ver tabla informe abajo)
- FASE 2 ✅ KPI cards frontend mapeados correctamente: roe_gestor→roe_pct ✅, bonus_gestor→total_incentivos ✅, clientes_gestor→clientes.length (4) ✅, contratos_gestor→contratos.length (12) ✅
- FASE 3 ✅ Pivot gestor arreglado: `/chat/gestor` ahora detecta intención de pivot y retorna `chart_config: {dimension: "producto", metric: "INGRESOS", gestor_id: "1"}` — igual que S34 para CDG
- FASE 4 ✅ Desglose gastos correcto: valores exactos, sin "trimestre", tono comprensivo ante frustración

**S34 — completada (pre-demo fixes):**
- B1 ✅ Falsa alerta LOW_MARGIN corregida: en `cdg_agent.py` `_consolidate_key_metrics` y `_generate_business_alerts`, el campo `margen_neto_pct` no existía en los datos — el campo real es `margen_neto` (devuelto por `ranking_gestores_por_margen_enhanced`). Cambiado en ambos sitios. También corregidos los nombres de campo uppercase para gestores: `desc_gestor` → `DESC_GESTOR`. Resultado: alerta real "11 gestores con margen < 5%" con nombres correctos (antes era falsa "30/30").
- B2 ✅ Pivot `chart_config` corregido: en `main.py` handler `POST /chat/message`, después de obtener `data`, se detecta intención de pivot (keywords: "cambia el gr", "grafico a", "pivot", "muestra por", etc.) y se llama `handle_chart_pivot_request` inyectando el resultado en `data['chart_config']`. Verificado: `chart_config null: False`, devuelve `{dimension: "segmento", metric: "INGRESOS"}`.
- Verificaciones post-fix: margen_promedio = 39.96% ✅ | pivot chart_config no null ✅

**S33 — completada:**
- B1 ✅ Fix expand button: `ChatInterface` recibe `onToggleExpand` prop + `useEffect` sincroniza `isExpanded` con prop `expanded`. El botón llama `onToggleExpand` (padre) si existe, si no usa toggle interno. `DireccionView` pasa `onToggleExpand={() => setChatExpanded(prev => !prev)}`. `GestorView` pasa `onToggleExpand={handleChatToggleExpand}`. Al pulsar el botón, `chatConfig` del padre actualiza el contenedor a `80vw / 80vh`.
- B2 Tests demo ejecutados (G1 oct, CDG retrocesos, CDG riesgo, pivot):
  - TEST 1 ✅ Gastos G1: cifras exactas (directos €3,078.79 / redistribuidos €14,795.49 / total €17,874.28), explica prorratio centrales
  - TEST 2 ✅ Retrocesos: top 5 idéntico a BD (Pablo Moreno -55.18%, Francesca Costa -10.12%, Carlos García -7.44%, Jordi Torra/Antonio Torres -7.35%)
  - TEST 3 ⚠️ Concentración riesgo: macro correcto (85 clientes, 3 productos, 220 contratos), pero NO hace drill-down a G27 (3 clientes). Alerta falsa "30 gestores margen<5%" por bug en `key_metrics.margen_promedio=0` en backend
  - TEST 4 ⚠️ Pivot chat: `/charts/pivot` endpoint funciona y devuelve `dimension: segmento, metric: INGRESOS` correctamente. Pero `/chat/message` devuelve `chart_config: null` — la UI no recibe el config para actualizar el gráfico

**S32 — completada:**
- B1 ✅ `get_mi_centro_benchmark` corregido: `centro_id` ya no es parámetro externo — se auto-resuelve llamando `basic_queries.get_gestor_metricas_completas` y extrayendo `datos['CENTRO']`. El LLM nunca pedirá el centro al usuario.
- B2 ✅ `get_mi_reporte_personal` añadido: agrega KPIs (`calculate_roe_gestor_enhanced`), evolución (`compare_gestor_septiembre_octubre`), clientes (`get_gestor_clientes_con_metricas`) y desviaciones (`get_desviaciones_precio_gestor_enhanced`) en un único payload. El LLM presenta en 5 secciones (instrucción en system prompt).
- System prompt actualizado: `RESTRICCIÓN COMPARATIVAS` → clarifica que `get_mi_centro_benchmark` no requiere parámetros. Bloque `REPORTE PERSONAL` → instrucción explícita de formato 5 secciones.

**S31 — completada:**
- B1 ✅ Headers redundantes eliminados: `DireccionView.jsx` + `GestorView.jsx` — quitado el `<div>` header exterior del chat flotante ("🤖 Asistente CDG Dirección/Personal"). Solo queda el header del `ChatInterface` Card ("Copiloto CDG · Activo · [badge]").
- B2 ✅ `gestor_agent.py` — tres correcciones:
  1. `get_mi_roe` tool añadido → llama `gestor_queries.calculate_roe_gestor_enhanced(gestor_id, periodo)` (ROE personal real, nunca datos de grupo)
  2. `get_mi_centro_benchmark` tool añadido → llama `basic_queries.get_centro_metricas_financieras(centro_id, periodo)` (benchmark del centro anonimizado)
  3. `get_resumen_periodo` eliminado → era `period_queries.get_periodo_metricas_financieras` (global, sin filtro gestor_id → devolvía €623,999 del grupo en lugar de ~€36,010 personal)
  4. System prompt actualizado: bloque `ROE — CÓMO USARLO` + bloque `RESTRICCIÓN COMPARATIVAS`

**S30 — completada (commit `09da03f`):**
- FIX ✅ ChatInterface: Card `height: 85vh / maxHeight: 85vh / overflow: hidden`. Body `height: 100% / overflow: hidden`. Mensajes `flex:1 / overflowY:auto / minHeight:0` (crítico para flex scroll). `flexShrink:0` en header, accessDenied, suggestions y footer. `Empty` centrado con `height:100%`.

**S29 — completada (commits `0b41f73`, `86bef06`, `2a984a5`, `5bb50b1`):**
- B1 ✅ InteractiveCharts: Card fondo `#120020→white`, leyenda/ticks `#A87BC8→#666`, grid `rgba(161,0,255,0.08)→#e8e8e8`. Tooltip dark mantenido.
- B2 ✅ ChatInterface layout: `maxHeight`/`minHeight` eliminados del área de mensajes (`flex:1` controla), `flexShrink:0` en suggestions y footer, `padding 12px 16px` en mensajes. `maxWidth 75%/85%` en burbujas usuario/asistente.
- B3 ✅ ROE gestor: `calculate_roe_gestor_enhanced` corregido: `abs(gastos)` + denominador `ingresos` (no `patrimonio_total`). G27 oct: ~61.8% (22,245/36,010). También corregido en `get_gestor_performance_enhanced`.
- B4 ✅ Benchmarks eliminados: `kpi_calculator.py` strings "Top quartile sector bancario" → `'N/A'`. `gestor_agent.py` restricción explícita añadida: solo datos BD, sin clasificaciones externas.

**S28 — completada (commits `0d4ddb6`, `d7b9685`):**
- BLOQUE 1 ✅ Dark mode revertido en dashboards: `App.jsx` ConfigProvider tokens → claro (background/borderLight/textPrimary), `index.css` body sin background/color forzado. `DireccionView`+`GestorView` `backgroundColor` → `theme.colors.background`. `KPICards` card white + texto textPrimary/Secondary. `ChatInterface` área mensajes+input → fondo claro, burbujas asistente `#1A0033` mantenidas.
- BLOQUE 2 ✅ LandingPage: nodos Three.js `size 0.07→0.25`, `maxDist 3.2→4.2`, líneas `opacity 0.12→0.25`. Botón Actualizar movido al top-right absoluto (`position: absolute, top: 20, right: 24`).

**S27 — completada (WOW Visual Redesign):**
- FIX ✅ Tooltip Recharts/ChartJS: `context.parsed.y||context.parsed.x` → discriminación correcta por `chartType === 'horizontal_bar'` → `context.parsed.x`; valores reales en tooltips
- B1 ✅ Dark mode global: `theme.darkTheme` palette (#0A0014/#120020/#1A0033), `index.css` body dark + scrollbar + selection, `App.jsx` ConfigProvider tokens dark (colorBgContainer, colorBgLayout, colorBgElevated, colorBorder, colorText, Select/Table/Input/DatePicker/Dropdown/Tooltip/Tabs dark)
- B2 ✅ LandingPage v6: Three.js CDN neural-network canvas (80 nodos, r134), CSS fallback `@keyframes`, `framer-motion` fade-in estalonado, glassmorphism cards (rgba(161,0,255,0.08) + backdrop-filter), glow title `text-shadow`, botones glassmorphism
- B3 ✅ KPICards: `useCountUp` hook (rAF, ease-out cúbico), `IntersectionObserver` por card, dark glow style (rgba(18,0,32,0.85) + backdrop-filter, border rgba(161,0,255,0.25→0.5) hover, box-shadow glow), tags variación MoM en neón (#00FF88 positivo / #FF3366 negativo)
- B4 ✅ InteractiveCharts: tooltip dark (rgba(26,0,51,0.95)), grid rgba(161,0,255,0.08), ejes #A87BC8, leyenda #A87BC8, cards dark #120020
- B5 ✅ ChatInterface: pulsing green dot "Activo", typing dots CSS animation (3 spans bounce escalonado), mensajes asistente fondo #1A0033, área mensajes #0A0014, Sender dark border rgba(161,0,255,0.3), accessDenied banner dark red
- B6 ✅ Animaciones: DireccionView+GestorView layout #0A0014 + `motion.div` fade-in Content (opacity 0→1, 0.4s), GestoresTable `motion.tr` row stagger (opacity/x -20→0, delay index×0.04), TopBar `border-bottom: 1px solid rgba(161,0,255,0.5)` glow

---

## 📊 Valores de referencia definitivos (post-sesión-24)

| Métrica | Valor |
|---|---|
| Total contratos | 220 oct / 216 sep (cartera acumulada FECHA_ALTA) |
| Total movimientos | ~2,900+ |
| **Modelo temporal** | **MoM** ingresos/gastos/ROE + **cartera acumulada** contratos |
| Sep MoM ingresos | €599,759 / ROE 35.94% / 216 contratos |
| Oct MoM ingresos | **€624,000** / ROE **39.96%** / 220 contratos (+4.04% oct>sep ✓) |
| Gastos centrales MoM | sep -€278,410 / oct -€271,251 (incluye fondeo 660001 -€180k) |
| Modelo fábrica oct | cedido €123,278 (84.01%), retenido €23,471, desv -0.99% vs 85% |
| Fábrica oct vs sep | +4.54% variación cedido gestora (sep €117,926) |
| Margen por segmento oct | Privada 91.8% > Minorista 85.7% > Empresas 80.9% > Personal 72.4% > Fondos 66.0% |
| Evolucion gestores oct | 10 mejora / 8 estable / 12 retroceso (umbral ±5%) |
| Outlier aceptado | G8 Pablo Moreno (-57.4% sep): fondos lumpy |
| Gestor 1 oct margen | 44.55% (ingresos €32,238 / gastos directos -€3,079 / redistribuidos -€14,795) |
| Avg Privada oct | €37,656 (2.01× Minorista €19,697) |

---

## ⏭️ Próximo paso al retomar (post-S30)

**Para iniciar el sistema:**
```bash
cd backend && python main.py
# o: python -m uvicorn main:app --host 127.0.0.1 --port 8000
cd frontend && npm start
```

⚠️ Puerto: el backend arranca siempre en 8000 (definido en `.env` raíz y `main.py`).
`frontend/.env` debe apuntar a `http://localhost:8000`.

**Pendiente menor (no bloquea demo):**
- ROE KPICards = promedio aritmético de 5 centros (~32.6% sep) vs ROE grupo (35.94%). Diferencia por fórmula, no un error crítico
- `kpis_financieros.margen_neto_pct` en endpoint centro = 159% (bug fórmula, campo no usado en UI)
- Distribución contratos inconsistente entre `/kpis/centro/{id}/financieros` y `count_contratos_by_centro`

---

## ⚠️ Pendiente de decisión

- `MAESTRO_CONTRATOS_BACKUP_20250922_002703` — tabla basura en la BD, pendiente de `DROP TABLE`
- `backend/src/utils/initial_agent.py` — usa `openai` SDK directo en lugar de LangChain, pendiente de reescribir (no bloquea la POC)
- `GET /basic/precios-std` y `GET /prices/comparison` — devuelven 404; no se usan en ningún flujo activo
- `analyticsService.js:2857` — `.replace('Fondo Banca March', 'Fondos CDG')` mantiene el string del nombre real en BD (no es UI-visible, no se toca)
- `BM_CONTABILIDAD_CDG_backup_20260315.db` — backup de la BD pre-corrección, mantener hasta confirmar que el sistema arranca correctamente

---

## ✅ S48 — completada (commits `966984f`, `f33feb1`, `87d1dd6`)

**Objetivo:** Tres fixes de bajo riesgo aprobados en S47.

**B1 ✅ CENTRO_ANALYSIS handler en CDGAgent:**
- `AnalysisType.CENTRO_ANALYSIS` añadido al enum en `cdg_agent.py`
- BLOQUE 0 en `_determine_analysis_type()`: detecta 'bilbao', 'madrid', 'palma', 'barcelona', 'malaga', 'oficina de', 'centro de', etc. — ANTES que cualquier otro bloque
- Nuevo método `_centro_analysis()`: extrae centros del mensaje, llama `basic_queries.get_centro_metricas_financieras(centro_id, periodo)` para cada centro detectado. Si no hay centro específico → devuelve los 5 finalistas
- Reutiliza query existente (Bilbao: 29 contratos, €105k ingresos, margen 57.18% validado en Python)
- `_execute_specialized_analysis()` dispatch actualizado con `CENTRO_ANALYSIS: self._centro_analysis`
- No se añadió entrada en `query_router.py` (la función requiere `centro_id` que el router no puede extraer; las queries de centro llegan via CDG_AGENT, no via predefined query path)

**B2 ✅ Session TTL en GestorAgent:**
- `self._last_session_id: str = ""` añadido a `GestorAgent.__init__()`
- Al inicio de `process_message()`: si `session_id` cambia respecto a `_last_session_id`, resetea `conversation_history = []` y actualiza `_last_session_id`
- Protege contra historial contaminado entre sesiones de usuario distintas (bug raíz identificado en S47)
- `session_id` ya venía en `GestorChatRequest` y ya se pasaba a `process_message()` desde `main.py`

**B3 ✅ Keywords de productos en REGLA ABSOLUTA:**
- En `_build_system_prompt()` de `gestor_agent.py`: añadidos 6 ejemplos explícitos para products en REGLA ABSOLUTA:
  - "cuántas hipotecas tengo" → llama get_mis_productos_detalle
  - "cuántos depósitos tengo" → llama get_mis_productos_detalle
  - "qué productos tengo" → llama get_mis_productos_detalle
  - "mi mix de productos" → llama get_mis_productos_detalle
  - "qué producto priorizar" → llama get_mis_productos_detalle
  - "cuántos fondos gestiono" → llama get_mis_productos_detalle

**Verificación estática (Python):** BLOQUE 0 firma correctamente para "bilbao" y "centro de". `CENTRO_ANALYSIS` enum presente. `_centro_analysis()` devuelve datos reales (Bilbao: 29 contratos, €105,363, margen 57.18%).

**⚠️ Nota backend:** WatchFiles no detectó los cambios en `src/` durante la sesión. Los tests en caliente fallaron mostrando `analysis_type: business_intelligence` (código anterior en memoria). **Requiere reinicio manual del backend** para que B1 entre en efecto.

**Próxima sesión:** S49 — "Handlers Faltantes" (período ad-hoc, producto global CDG, gestor individual como CDG). Considerar si DYNAMIC_SQL puede habilitarse como fallback seguro post-S43.
