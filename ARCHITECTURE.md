# CDG Intelligence — Arquitectura del Sistema

**Versión:** post-S78a | **Tests:** 48/48 (100%) | **Fecha:** Abril 2026

---

## 1. Visión General

CDG Intelligence es un asistente de inteligencia artificial para Control de Gestión bancario, diseñado para Banca March. Permite al equipo de Dirección analizar resultados financieros en lenguaje natural (actuals, rankings, desviaciones) y a los gestores comerciales comprender y mejorar su cartera individual. Incorpora un módulo de proyecciones con IA predictiva (Prophet + GPT-4o) y análisis what-if con shocks paramétricos.

**Usuarios:** Control de Gestión (Dirección) · Gestores comerciales individuales
**Stack:** React 18 · FastAPI · LangGraph · Azure OpenAI GPT-4o · Prophet ML · SQLite · BCE MIR · INE IPC

---

## 2. Estructura del Repositorio

```
CDG Intelligence/
├── backend/
│   ├── main.py                          # FastAPI app + 137 endpoints
│   ├── requirements.txt                 # Dependencias Python
│   ├── .env                             # Credenciales Azure OpenAI
│   └── src/
│       ├── agents/                      # Agentes de IA (ReAct con LangGraph)
│       │   ├── chat_agent.py            # Router principal (2518 líneas)
│       │   ├── cdg_agent.py             # Agente Control de Gestión (555 líneas)
│       │   ├── gestor_agent.py          # Agente Gestor Individual (771 líneas)
│       │   ├── forecast_agent.py        # Agente Proyecciones (361 líneas)
│       │   └── query_router.py          # Router determinista S40 (304 líneas)
│       ├── forecast/                    # Módulo de Proyecciones
│       │   ├── prophet_engine.py        # Motor Prophet logístico (194 líneas)
│       │   ├── macro_context.py         # BCE MIR + INE IPC (181 líneas)
│       │   ├── scenario_builder.py      # 3 escenarios + narrativa (243 líneas)
│       │   └── whatif_simulator.py      # Shocks paramétricos (144 líneas)
│       ├── queries/                     # Acceso a BD — SQL puro
│       │   ├── basic_queries.py         # Catálogo básico (1292 líneas)
│       │   ├── comparative_queries.py   # Rankings y comparativas (1544 líneas)
│       │   ├── gestor_queries.py        # Queries personales gestor (2265 líneas)
│       │   ├── period_queries.py        # Métricas por período (410 líneas)
│       │   ├── deviation_queries.py     # Detección anomalías (1289 líneas)
│       │   ├── incentive_queries.py     # Cálculo incentivos (1398 líneas)
│       │   └── forecast_queries.py      # Series temporales Prophet (207 líneas)
│       ├── routers/
│       │   └── forecast_router.py       # Endpoints /forecast/* (184 líneas)
│       ├── tools/                       # Herramientas auxiliares
│       │   ├── chart_generator.py       # Generación gráficos (1204 líneas)
│       │   ├── kpi_calculator.py        # Cálculos KPI (406 líneas)
│       │   └── report_generator.py      # Generación informes (722 líneas)
│       ├── prompts/
│       │   └── system_prompts.py        # Prompts LLM (5990 líneas)
│       └── database/
│           └── BM_CONTABILIDAD_CDG.db   # SQLite (14 tablas, 20 meses)
└── frontend/
    └── src/
        ├── pages/                       # 5 páginas principales
        │   ├── LandingPage.jsx          # Selector de rol
        │   ├── DireccionView.jsx        # Dashboard Control de Gestión
        │   ├── GestorView.jsx           # Dashboard Gestor individual
        │   ├── ProjectionsPage.jsx      # Proyecciones Dirección
        │   └── GestorProjectionsPage.jsx # Proyecciones Gestor
        ├── components/
        │   ├── Dashboard/               # 8 componentes dashboard
        │   │   ├── KPICards.jsx         # Tarjetas KPI con variación
        │   │   ├── ChatInterface.jsx     # Chat principal
        │   │   ├── InteractiveCharts.jsx # Gráficos Recharts
        │   │   ├── GestoresTable.jsx    # Tabla detallada gestores
        │   │   ├── FabricaModelSection.jsx # Modelo Fábrica (FRV 85/15)
        │   │   ├── DeviationAnalysis.jsx # Análisis desviaciones precio
        │   │   ├── DrillDownView.jsx    # Drill-down gestor/centro
        │   │   └── ConversationalPivot.jsx # Pivot conversacional
        │   ├── Forecast/                # 5 componentes proyecciones
        │   │   ├── ForecastChart.jsx    # Recharts: actuals + 3 escenarios
        │   │   ├── ScenarioKPICards.jsx # Cards pes/base/opt
        │   │   ├── ScenarioConfigurator.jsx # Horizonte + dimensión + shocks
        │   │   ├── MacroContextPanel.jsx # BCE + INE tiempo real
        │   │   └── ForecastChat.jsx     # Chat con ForecastAgent
        │   └── common/                  # TopBar, Loader, ErrorState, etc.
        └── services/
            └── api.js                   # Cliente HTTP — 28 módulos
```

---

## 3. Capas del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND (React 18 · Ant Design 5 · Recharts)                      │
│  DireccionView / GestorView / ProjectionsPage / GestorProjPage       │
│  api.js → axios → 28 módulos API                                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP/REST (JSON)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI · Python 3.11+)                                    │
│                                                                      │
│  POST /chat/message ──► ChatAgent (router)                          │
│  POST /chat/gestor  ──► ChatAgent (router)                          │
│  POST /forecast/*   ──► forecast_router.py                          │
│                                                                      │
│  ChatAgent ──► CDGAgent (actuals Dirección)                         │
│            ──► GestorAgent (personal Gestor)                        │
│            ──► ForecastAgent (proyecciones)                         │
│                                                                      │
│  Agentes ──► Queries (SQL) ──► SQLite                               │
│          ──► Prophet Engine ──► Forecasts                           │
│          ──► MacroContext ──► BCE API + INE API                     │
│          ──► Azure OpenAI GPT-4o ──► Respuesta natural             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ SQL
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATOS (SQLite BM_CONTABILIDAD_CDG.db)                               │
│  14 tablas · 20 períodos (sep-2024 a abr-2026) · 19,266 movimientos │
│  351 contratos · 142 clientes · 30 gestores · 5 centros · 3 prods   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Agentes de IA

### 4.1 ChatAgent — Router Principal

**Archivo:** `chat_agent.py` (2518 líneas)
**Propósito:** Clasifica cada mensaje entrante y decide qué agente lo procesa. Es la única puerta de entrada para todos los chats.
**Tecnología:** LLM clasificador (GPT-4o) + 8 reglas deterministas en cascada

#### Sistema de clasificación LLM
Para cada mensaje, el LLM devuelve:
- `intent`: tipo de consulta (business_review, ranking_analysis, general_inquiry, etc.)
- `is_personal`: True si se refiere a datos de un gestor específico
- `requires_sql`: True si la respuesta necesita datos de la BD
- `confidence`: score 0-1

#### Reglas de routing (en orden de prioridad)

| Regla | Condición | Destino | Descripción |
|-------|-----------|---------|-------------|
| -1 (S69) | Keywords forecast/proyección | FORECAST_AGENT | "proyección", "what-if", "próximos meses", "simula"... |
| 0 (S53) | CDG + keywords alerta | CDG_AGENT | "preocupar", "alerta", "riesgo", "desviación"... |
| 1b (S78a) | CDG + is_personal + requires_sql | CDG_AGENT | CDG puede ver datos de cualquier gestor |
| 2 | intent in cdg_intents + !is_personal | CDG_AGENT | business_review, ranking_analysis, global_analysis... |
| 2b | CDG + requires_sql + !is_personal | CDG_AGENT | CDG con SQL no personal |
| 3 | requires_sql → predefined match | PREDEFINED_QUERY | Queries predefinidas en catálogos |
| 3c (S78a) | CDG + general_inquiry | CDG_AGENT | Override: CDG siempre va a CDGAgent |
| 4 | general_inquiry o !requires_sql | CONTEXTUAL_RESPONSE | Respuesta sin SQL |
| default | Sin match | DYNAMIC_SQL | SQL dinámico generado por LLM |

#### Flujos activados
- **ACCESS_DENIED**: Gestor intentando ver datos de otro gestor
- **CDG_AGENT**: Análisis para Control de Gestión
- **FORECAST_AGENT**: Proyecciones y what-if
- **PREDEFINED_QUERY**: Catálogos de queries predefinidas
- **DYNAMIC_SQL**: SQL generado dinámicamente
- **CONTEXTUAL_RESPONSE**: Respuesta sin acceso a BD

---

### 4.2 CDGAgent v7 — Control de Gestión

**Archivo:** `cdg_agent.py` (555 líneas)
**Propósito:** Análisis financiero completo del banco para el equipo de Control de Gestión. Responde preguntas sobre actuals, rankings, comparativas y desviaciones.
**Audiencia:** Controllers, Directores
**Arquitectura:** ReAct con LangGraph `create_react_agent` (sin keywords hardcodeadas — el LLM decide qué tools usar)
**Sistema prompt:** Español bancario profesional, datos MoM, reglas de concisión (≤150 palabras preguntas directas)

#### Tools disponibles (10)

| Tool | Query/Fuente | Úsala para |
|------|-------------|------------|
| `get_resumen_entidad` | basic_queries.get_resumen_general() | "cuántos gestores/contratos tenemos" |
| `get_metricas_periodo` | period_queries.get_periodo_metricas_financieras() | "resumen del mes", "ingresos totales" |
| `get_metricas_centro` | basic_queries.get_centro_metricas_financieras() | "cómo va Madrid/Bilbao/..." |
| `get_ranking_gestores_margen` | comparative_queries.ranking_gestores_por_margen_enhanced() | "mejores gestores", "ranking" |
| `get_ranking_gestores_ingresos` | basic_queries.ranking_gestores_por_ingresos() | "top por ingresos" |
| `get_evolucion_mensual` | comparative_queries.get_evolucion_gestores(actual, anterior) | "cómo evolucionamos vs mes pasado" |
| `get_kpis_productos` | basic_queries.get_producto_kpis_global() | "qué producto da más", "mix productos" |
| `get_desviaciones_precio` | deviation_queries.detect_precio_desviaciones_criticas_enhanced() | "hay alertas", "desviaciones precio" |
| `get_comparativa_periodos` | period_queries.compare_periodos_metricas() | "comparar dos períodos" |
| `get_metricas_gestor_individual` | basic_queries.get_gestor_metricas_completas() | "datos del gestor X" |

---

### 4.3 GestorAgent — Gestor Individual

**Archivo:** `gestor_agent.py` (771 líneas)
**Propósito:** Copiloto personal del gestor comercial. Responde en segunda persona sobre su cartera, clientes, productos y evolución.
**Audiencia:** 30 gestores comerciales
**Arquitectura:** ReAct con LangGraph + caché por session_id (reinicia con cada nueva sesión para evitar contexto stale)
**Restricción de acceso:** Solo puede acceder a su propio `gestor_id` (filtro WHERE GESTOR_ID = {id} en todas las queries)
**REGLA ABSOLUTA en prompt:** Siempre llama tools antes de responder. Mapeo de frases informales a tools específicas.
**Retry S46:** Si el LLM no llama tools, reintenta sin historial previo (fuerza tool call).

#### Tools disponibles (9)

| Tool | Query/Fuente | Úsala para |
|------|-------------|------------|
| `get_mis_kpis` | gestor_queries.get_gestor_performance_enhanced() | "cómo estoy", "cuánto ingresé" |
| `get_mi_cartera` | basic_queries.get_gestor_metricas_completas() | "resumen de mi cartera" |
| `get_mis_desviaciones` | gestor_queries.get_desviaciones_precio_gestor_enhanced() | "mis desviaciones de precio" |
| `get_mi_evolucion_mensual` | gestor_queries.compare_gestor_periodos(actual, anterior) | "evolución vs mes pasado" |
| `get_mis_clientes` | basic_queries.get_gestor_clientes_con_metricas() | "mis clientes", "quién genera más" |
| `get_mi_roe` | gestor_queries.calculate_roe_gestor_enhanced() | "mis gastos", "mi rentabilidad" |
| `get_mi_centro_benchmark` | basic_queries.get_centro_metricas_financieras() | "cómo me comparo con el centro" |
| `get_mi_reporte_personal` | Combina ROE + evolución + clientes + desviaciones | "dame mi reporte completo" |
| `get_mis_productos_detalle` | basic_queries.get_contratos_by_gestor() + get_gestor_performance_enhanced() | "mis productos", "qué tengo en cartera" |

---

### 4.4 ForecastAgent — Proyecciones y What-If

**Archivo:** `forecast_agent.py` (361 líneas)
**Propósito:** Análisis predictivo basado en Prophet ML. Genera proyecciones a 3/6/12 meses, simula shocks paramétricos y contextualiza con datos macro reales.
**Audiencia:** Control de Gestión (estratégico) y Gestores (prescriptivo personal)
**Arquitectura:** ReAct con LangGraph. Instancia singleton compartida (`get_forecast_agent()`).
**Contexto de rol en prompt:** Si user_role=gestor habla en 2ª persona; si control_gestion habla en plural.

#### Tools disponibles (5)

| Tool | Módulo backend | Úsala para |
|------|---------------|------------|
| `get_forecast_base` | ForecastQueries → ProphetEngine → ScenarioBuilder | "proyección trimestral", "cómo cerraremos el año" |
| `get_macro_context` | MacroContextService (BCE + INE, caché 24h) | "entorno de tipos", "cómo nos afecta la inflación" |
| `apply_whatif` | WhatIfSimulator | "qué pasa si tipos suben", "simula pérdida captación" |
| `get_recommendations` | ProphetEngine + ScenarioBuilder + MacroContext | "qué debemos priorizar", "plan de acción" |
| `compare_scenarios` | ScenarioBuilder.compare() | "tabla comparativa", "diferencia pesimista vs optimista" |

---

## 5. Flujos de Petición End-to-End

### Flujo 1: Consulta de actuals — Control de Gestión

```
1. Usuario (DireccionView) escribe en ChatInterface.jsx
2. POST /chat/message { message, user_role:"control_gestion", periodo:"2026-04", user_id }
3. main.py: determina user_role, construye effective_context, crea ChatMessage
4. ChatAgent.process_chat_message(msg)
   ↓
   classify_and_route():
   → S78a: user_role=CDG → bypasa confidentiality check
   → LLM clasifica: intent="ranking_analysis", is_personal=False, requires_sql=True
   → REGLA 2 → flow_type = CDG_AGENT
   ↓
5. _execute_cdg_agent_flow()
   → CDGAgent._agent.ainvoke({"messages": [SystemMessage, ...HumanMessage]})
   → LLM decide tool: get_ranking_gestores_margen("2026-04")
   → Tool ejecuta SQL → comparative_queries → SQLite → 30 gestores rankeados
   → LLM formatea respuesta en español bancario (<150 palabras)
   → S56: usa response_text del agente directamente (bypass BankingResponseFormatter)
6. ChatResponse → DireccionView → ChatInterface renderiza respuesta
```

### Flujo 2: Consulta personal — Gestor Individual

```
1. Gestor (GestorView) escribe en ChatInterface.jsx
2. POST /chat/gestor { message, gestor_id:"7", periodo:"2026-04", user_role:"gestor", session_id }
3. main.py: crea GestorAgent(gestor_id=7) — cacheado por session_id+hash(params)
4. GestorAgent.process_message(message, session_id)
   → S48: reset historial si cambia session_id
   → LangGraph ReAct invoca herramientas
   → LLM selecciona tool: get_mis_kpis("7", "2026-04")
   → Tool query SQLite WHERE GESTOR_ID=7 → KPIs individuales
   → S46 retry: si LLM no llama tools, reintenta sin historial
   → LLM formatea respuesta en 2ª persona (<200 palabras)
5. Respuesta con datos reales del gestor 7 (Javier Fernández Sánchez)
```

### Flujo 3: Proyección base — Módulo Forecast

```
1. Usuario (ProjectionsPage.jsx) configura horizonte=6, dimension="entidad"
2. calcular() → POST /forecast/base { horizonte_meses:6, dimension:"entidad" }
3. forecast_router.forecast_base()
   ↓
   ForecastQueries.get_serie_ingresos("entidad", None)
   → SQL: SELECT strftime('%Y-%m-01', FECHA) as ds, SUM(importe 76*) as y
   → DataFrame 20 puntos (sep-2024 a abr-2026)
   ↓
   ProphetEngine.fit(df)
   → growth='logistic', cap=max(y)×1.25=€825k
   → changepoint_prior_scale=0.05, seasonality_prior_scale=0.1
   → interval_width=0.80
   → fit en ~0.7 segundos
   ↓
   ProphetEngine.get_scenarios(horizonte=6)
   → predict() → 3 curvas: yhat, yhat_lower, yhat_upper
   → clip to [0, cap] (previene desbordamiento)
   → {base:[{periodo:"2026-05", valor:808689},...], optimista, pesimista}
   ↓
   MacroContextService.get_context()
   → BCE MIR API: tipos_hipotecas=3.47% (caché 24h)
   → INE IPC API: ipc_spain=1.2% (caché 24h)
   → Impacto calculado: Hip=MODERADO_POSITIVO, Dep=NEUTRAL, FRV=POSITIVO
   ↓
   ScenarioBuilder.build(forecast, macro)
   → 3 escenarios con ajuste macro ±5% + narrativa en español bancario
   → nota_metodologica: "banco inicio sep-2024, 20 meses histórico..."
4. Response: {escenario_pesimista:{valores,prob:0.20}, escenario_base:{0.60}, escenario_optimista:{0.20}}
5. ProjectionsPage renderiza:
   → ForecastChart (Recharts: actuals púrpura + 3 escenarios área)
   → ScenarioKPICards (3 cards con variación vs actual)
   → Tabla mes a mes
```

### Flujo 4: What-If — Simulación de shocks

```
1. Usuario mueve sliders (tipos_interes:+50, captacion_clientes:-10)
2. Pulsa "Calcular Proyección" → POST /forecast/whatif { shocks, horizonte_meses:6 }
3. WhatIfSimulator.simulate(shocks, horizonte=6)
   → ForecastQueries.get_serie_ingresos()
   → ProphetEngine.fit() + get_scenarios() → forecast base
   → ScenarioBuilder.build(forecast, macro, shocks=shocks)
      → _apply_shock(valores, shocks):
         tipos +50pb → adj += (50/10)×0.003 = +1.5% ingresos hip
                       adj += (50/10)×(-0.015) = -7.5% captación
         captación -10% → gradual: mes1=25%, mes4=100%
   → impacto_total = (base_con_shock - base_sin_shock) / base_sin_shock × 100
   → recomendaciones automáticas según shocks
4. Response: {escenarios completos, analisis_impacto:{impacto_total_pct:-12.2%, recomendaciones}}
5. ProjectionsPage actualiza gráfico con nuevas curvas
```

### Flujo 5: Chat conversacional con ForecastAgent

```
1. Usuario escribe en ForecastChat.jsx: "simula que los tipos suben 75pb"
2. POST /forecast/chat { message, user_role:"control_gestion", periodo_base:"2026-04", session_id }
3. ForecastAgent.process_message(message, ...)
   → Construye messages: [SystemMessage(FORECAST_SYSTEM_PROMPT), ...history, HumanMessage]
   → LangGraph ReAct: LLM decide llamar apply_whatif
   → apply_whatif('{"tipos_interes": 75}', horizonte_meses=6)
   → WhatIfSimulator.simulate({tipos_interes:75}, 6)
   → Response formateada: impacto -7.1%, escenarios, recomendaciones
4. ForecastChat renderiza respuesta con glassmorphism + animaciones CSS
```

---

## 6. Base de Datos

### Tablas Maestro (catálogos estáticos)

| Tabla | Filas | Descripción | Columnas principales |
|-------|-------|-------------|---------------------|
| MAESTRO_GESTORES | 30 | 30 gestores en 5 centros finalistas | GESTOR_ID, DESC_GESTOR, CENTRO, SEGMENTO_ID |
| MAESTRO_CLIENTES | 142 | Clientes con nombres regionales reales (S76) | CLIENTE_ID, NOMBRE_CLIENTE, GESTOR_ID |
| MAESTRO_CONTRATOS | 351 | Cartera acumulada sep-2024 a abr-2026 | CONTRATO_ID, FECHA_ALTA, CLIENTE_ID, GESTOR_ID, PRODUCTO_ID, CENTRO_CONTABLE |
| MAESTRO_CENTROS | 8 | 5 finalistas + 3 soporte | CENTRO_ID, DESC_CENTRO, IND_CENTRO_FINALISTA |
| MAESTRO_PRODUCTOS | 3 | Hip / Dep / FRV | PRODUCTO_ID, DESC_PRODUCTO, IND_FABRICA, FABRICA(%), BANCO(%) |
| MAESTRO_SEGMENTOS | 5 | Minorista / Privada / Empresas / Personal / Fondos | SEGMENTO_ID, DESC_SEGMENTO |
| MAESTRO_CUENTAS | 25 | Cuentas contables con línea CDR | CUENTA_ID, DESC_CUENTA, LINEA_CDR |
| MAESTRO_LINEA_CDR | 16 | Estructura P&L (CR0001→CR0030) | COD_LINEA_CDR, DES_LINEA_CDR |

### Tablas Transaccionales

| Tabla | Filas | Descripción | Columnas clave |
|-------|-------|-------------|---------------|
| MOVIMIENTOS_CONTRATOS | 19,266 | Todos los movimientos financieros | MOVIMIENTO_ID, FECHA, CONTRATO_ID, CUENTA_ID, IMPORTE |
| GASTOS_CENTRO | 789 | Gastos por centro de soporte | EMPRESA, CENTRO_CONTABLE, CONCEPTO_COSTE, FECHA, IMPORTE |
| PRECIO_POR_PRODUCTO_REAL | 300 | Costes reales por segmento-producto-mes | SEGMENTO_ID, PRODUCTO_ID, PRECIO_MANTENIMIENTO_REAL, FECHA_CALCULO |
| PRECIO_POR_PRODUCTO_STD | 15 | Precios estándar anuales (ANNO=2026) | SEGMENTO_ID, PRODUCTO_ID, PRECIO_MANTENIMIENTO, ANNO |

### Cobertura y volumen

- **Histórico financiero:** sep-2024 a abr-2026 (20 meses)
- **Historia de contratos (FECHA_ALTA):** sep-2024 → acumulación progresiva
- **Lógica de ingresos:** `CUENTA_ID LIKE '76%'` → ingresos (760001-760026)
- **Lógica de gastos directos:** `SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69') AND CONTRATO_ID IS NOT NULL`
- **Gastos centrales:** `CONTRATO_ID IS NULL` → fondeo (660001 ~€180k/mes) + provisión (690002 ~€45k)
- **Redistribución:** `Gasto_i = Gasto_Central × (Contratos_i / Total_contratos_finalistas)`

### Centros y productos

| Centros Finalistas | Centros Soporte | Productos |
|-------------------|-----------------|-----------|
| Madrid (ID=1) | RRHH (ID=6) | Préstamo Hipotecario — 100% banco |
| Palma (ID=2) | Dir. Financiera (ID=7) | Depósito Plazo Fijo — 100% banco |
| Barcelona (ID=3) | Tecnología (ID=8) | Fondo Renta Variable — 85% gestora / 15% banco |
| Málaga (ID=4) | | |
| Bilbao (ID=5) | | |

### P&L simplificado (líneas CDR)

```
CR0001 Ingresos financieros
CR0003 Gastos financieros (intereses pagados depósitos)
CR0007 MARGEN FINANCIERO
CR0008 Comisiones netas
CR0012 MARGEN BRUTO
CR0014 Gastos de personal
CR0016 Gastos de administración
CR0018 MARGEN DE EXPLOTACIÓN
CR0029 Coste de capital
CR0030 MARGEN APORTADO
```

---

## 7. Módulo de Proyecciones

### Arquitectura del módulo

```
POST /forecast/base          POST /forecast/whatif       GET /forecast/macro-context
         │                          │                            │
         ▼                          ▼                            ▼
ForecastQueries           WhatIfSimulator           MacroContextService
(series temporales)       (shocks paramétricos)     (BCE MIR + INE IPC)
         │                          │                            │
         ▼                          │                            │
ProphetEngine ◄────────────────────┘                            │
(ML logístico)                                                   │
         │                                                       │
         ▼                                                       │
ScenarioBuilder ◄───────────────────────────────────────────────┘
(3 escenarios + narrativa)
         │
         ▼
{pesimista/base/optimista + nota_metodologica}
```

### Motor Prophet

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| `growth` | `'logistic'` | Curva S: el banco llegará a una meseta natural |
| `cap` | `max(serie) × 1.25` | Permite 25% de crecimiento sobre el máximo histórico |
| `floor` | `0` | No puede haber ingresos negativos |
| `changepoint_prior_scale` | `0.05` | Conservador: evita extrapolar el ramp-up 2024 |
| `seasonality_prior_scale` | `0.1` | Amortigua estacionalidad con 20 meses de historia |
| `yearly_seasonality` | `True` | Detecta patrones anuales |
| `interval_width` | `0.80` | 3 escenarios al 80% de confianza |
| Fit time | ~0.7s | Con 20 puntos históricos |

### APIs Macroeconómicas

| API | URL | Dato | Comportamiento |
|-----|-----|------|----------------|
| **BCE MIR** | `data-api.ecb.europa.eu/service/data/MIR/M.U2.B.A2A...` | Tipos hipotecarios eurozona | Últimas 4 observaciones; valor actual ~3.47% |
| **INE IPC** | `servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC206449` | Inflación interanual España | Últimas 4 observaciones; valor actual ~1.2% |
| **Euribor 12m** | Fallback estático | 2.5% | Endpoint BCE roto desde S66 |
| **Caché** | 24h (86,400s) | Ambas APIs | Nunca bloquea — siempre hay fallback |

### Shocks disponibles

| Shock | Unidad | Rango | Impacto calculado |
|-------|--------|-------|-------------------|
| `tipos_interes` | pb | -100 a +200 | +10pb → +0.3% ingresos Hip existentes, -1.5% captación Hip |
| `captacion_clientes` | % | -50 a +50 | Efecto gradual: 25% mes1, 100% mes4 |
| `reduccion_gastos` | % | 0 a 30 | Solo afecta margen, no ingresos brutos |
| `mix_productos` | pp FRV | -20 a +20 | +1pp FRV → +0.8% margen (FRV tiene 98% margen) |

### Escenarios

| Escenario | Probabilidad | Origen |
|-----------|-------------|--------|
| Pesimista | 20% | `yhat_lower` (percentil 10) |
| Base | 60% | `yhat` (mediana) |
| Optimista | 20% | `yhat_upper` (percentil 90) |

---

## 8. Dashboards Frontend

### Rutas y acceso

| URL | Componente | Audiencia | Chat activado |
|-----|-----------|-----------|---------------|
| `/` | LandingPage | Todos | — |
| `/direccion-dashboard` | DireccionView | Control de Gestión | CDGAgent |
| `/gestor-dashboard` | GestorView | Gestores (param: ?gestor=ID) | GestorAgent |
| `/proyecciones/direccion` | ProjectionsPage | Control de Gestión | ForecastAgent |
| `/proyecciones/gestor/:id` | GestorProjectionsPage | Gestor individual | ForecastAgent prescriptivo |

### DireccionView — Dashboard Dirección

**Secciones:**
- KPICards: ingresos totales, beneficio neto, margen %, contratos activos
- InteractiveCharts: gráficos dinámicos por dimensión (centros, gestores, productos)
- GestoresTable: tabla detallada con drill-down por gestor
- FabricaModelSection: modelo 85/15 gestora/banco para FRV
- DeviationAnalysis: desviaciones precio real vs estándar
- ChatInterface: chat con CDGAgent (responde en <25s)
- Botón "Proyecciones" → navega a /proyecciones/direccion

### GestorView — Dashboard Gestor

**Secciones:**
- KPICards personalizadas (ingresos, gastos, margen, ROE del gestor)
- InteractiveCharts con datos del gestor filtrados
- DrillDownView: detalle de contratos y clientes
- ChatInterface: chat con GestorAgent (responde en <15s con tools)
- Botón "Proyecciones" → navega a /proyecciones/gestor/:id

### ProjectionsPage — Proyecciones Dirección

**Tema:** Oscuro (#0D0D1A) con grid sutil y glows púrpura/azul
**Layout:** 3 columnas (25% config / 50% gráfico / 25% chat)
**Componentes:**
- ScenarioConfigurator: horizonte 3/6/12m, dimensión (entidad/centro/gestor), sliders shocks
- ForecastChart: Recharts ComposedChart — actuals púrpura + 3 escenarios área
- ScenarioKPICards: 3 cards pes/base/opt con probabilidades y narrativa
- MacroContextPanel: BCE tipos + INE IPC en tiempo real con indicadores visuales
- ForecastChat: chat con ForecastAgent, sugerencias CDG específicas
- Tabla mes a mes: 3 escenarios en columnas

### GestorProjectionsPage — Proyecciones Gestor

**Enfoque:** Prescriptivo personal ("qué tengo que hacer YO")
**Layout:** 2 columnas (30% KPIs+escenarios / 70% gráfico+chat)
**Diferencias vs Dirección:**
- KPIs personales del gestor (€36,847 ingresos, media 6m, tendencia)
- Mini-cards escenarios con framing en 2ª persona
- Panel "Palancas" — 3 acciones recomendadas específicas
- Chat prescriptivo con sugerencias "¿voy a llegar a mis objetivos?"

---

## 9. Endpoints API

### Chat

| Método | Endpoint | Descripción | Agente |
|--------|----------|-------------|--------|
| POST | `/chat/message` | Chat Control de Gestión | ChatAgent → CDG/Forecast |
| POST | `/chat/gestor` | Chat Gestor individual | GestorAgent |
| GET | `/chat/gestor/:id/status` | Estado del agente del gestor | — |
| POST | `/chat/gestor/:id/reset` | Resetear historial | — |

### Forecast `/forecast/*`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/forecast/base` | Proyección base 3 escenarios |
| POST | `/forecast/whatif` | Simulación shocks |
| GET | `/forecast/historicos` | Serie temporal actuals |
| GET | `/forecast/macro-context` | BCE MIR + INE IPC (caché 24h) |
| POST | `/forecast/recommendations` | Recomendaciones accionables |
| POST | `/forecast/chat` | Chat ForecastAgent |
| GET | `/forecast/gestor/:id/contexto` | KPIs + forecast 3m gestor |
| GET | `/forecast/dimensiones` | Centros/gestores disponibles |
| GET | `/forecast/shocks-disponibles` | 4 shocks con rangos |

### Analítica y KPIs (selección principales)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/kpis/consolidado` | KPIs entidad (ROE, ingresos, margen) |
| GET | `/kpis/gestor/:id/roe` | ROE individual del gestor |
| GET | `/analytics/gestor/:id/metricas-completas` | Métricas completas gestor |
| GET | `/analytics/fabrica` | Modelo Fábrica (FRV 85/15) |
| GET | `/charts/gestores-ranking` | Ranking por INGRESOS/MARGEN/ROE |
| GET | `/charts/centros-distribution` | Distribución por centros |
| GET | `/charts/productos-popularity` | Popularidad de productos |
| POST | `/charts/pivot` | Gráfico pivot conversacional |
| GET | `/deviations/pricing` | Desviaciones precio real vs STD |
| GET | `/periods` | Períodos disponibles con datos |
| GET | `/periods/latest` | Último período con datos financieros |

---

## 10. Tecnologías y Dependencias

### Backend

| Librería | Versión | Uso principal |
|----------|---------|---------------|
| FastAPI | ≥0.115.0 | API REST, WebSockets |
| LangChain | ≥0.3.14 | Abstracción LLM + tools |
| LangGraph | integrado | Agentes ReAct (create_react_agent) |
| Azure OpenAI | GPT-4o | LLM de todos los agentes |
| Prophet | ≥1.3.0 | Forecasting logístico (Meta) |
| CmdStanPy | ≥1.3.0 | Backend probabilístico de Prophet |
| Pandas | ≥2.2.3 | Series temporales, DataFrames |
| NumPy | ≥2.0.0 | Cálculos numéricos |
| Pydantic | ≥2.9.2 | Validación modelos datos |
| pydantic-settings | ≥2.5.2 | Configuración desde .env |
| python-dotenv | ≥1.0.1 | Carga variables de entorno |
| SQLite | built-in | Base de datos |

### Frontend

| Librería | Versión | Uso principal |
|----------|---------|---------------|
| React | ^18.2.0 | Framework UI |
| Ant Design | ^5.12.0 | Componentes UI bancarios |
| Recharts | ^3.1.2 | Gráficos (charts, forecast) |
| React Router | ^6.8.0 | Navegación SPA |
| @ant-design/icons | ^5.2.0 | Iconografía |
| @ant-design/x | ^1.0.6 | Bubble.List para chat |
| Axios | ^1.11.0 | HTTP client |
| framer-motion | ^10+ | Animaciones entrada/salida |

### Infraestructura

| Componente | Detalle |
|-----------|---------|
| LLM | Azure OpenAI GPT-4o (endpoint corporativo Accenture) |
| API Macro 1 | BCE MIR — Banco Central Europeo (Real, REST JSON) |
| API Macro 2 | INE IPC — Instituto Nacional de Estadística (Real, REST JSON) |
| BD | SQLite local (BM_CONTABILIDAD_CDG.db, 1.4 MB) |
| Backend deploy | uvicorn en localhost:8000 |
| Frontend deploy | React Scripts en localhost:3000 |

---

## 11. Métricas de Calidad del Sistema

| Componente | Tests | Score | Sesión |
|-----------|-------|-------|--------|
| CDGAgent — actuals Dirección | 15 | 15/15 (100%) | S77 + S78a |
| GestorAgent — personal | 8 | 8/8 (100%) | S77 |
| ForecastAgent — Dirección | 12 | 12/12 (100%) | S77 + S78a |
| ForecastAgent — Gestor prescriptivo | 8 | 8/8 (100%) | S77 |
| Calidad de dato (clientes reales) | 5 | 5/5 (100%) | S77 |
| **Total end-to-end** | **48** | **48/48 (100%)** | **S78a** |

---

## 12. Decisiones de Diseño Clave

### 1. Prophet con growth='logistic' en lugar de lineal
La serie histórica tiene dos fases muy distintas (ramp-up explosivo 2024 + estabilización 2025-2026). Sin cap, Prophet extrapola el ramp-up y predice €1.3M cuando el techo real es ~€825k. El crecimiento logístico con `cap = max(serie) × 1.25` produce forecasts creíbles (~€800-815k/mes).

### 2. SQLite en lugar de PostgreSQL
El sistema es un POC bancario para demostración. SQLite es suficiente para 19k registros, sin infraestructura adicional, y portátil. La BD completa tiene 1.4 MB. Migrar a PostgreSQL sería trivial si se necesitara escalar.

### 3. ReAct (Razonamiento + Acción) en lugar de function calling simple
ReAct permite que el LLM encadene múltiples herramientas según la complejidad de la pregunta. Para "compara Madrid y Bilbao" el agente llama `get_metricas_centro(1)` y `get_metricas_centro(5)` en secuencia. Function calling simple requeriría hardcodear todos los casos.

### 4. ChatAgent como router centralizado
Un solo punto de entrada (`/chat/message` y `/chat/gestor`) simplifica el frontend y centraliza las reglas de confidencialidad. El ChatAgent clasifica antes de delegar, lo que permite auditar todas las peticiones en un único lugar.

### 5. Bypass del BankingResponseFormatter para CDGAgent (S56)
El CDGAgent ReAct produce respuestas bien formateadas. El BankingResponseFormatter las reformateaba añadiendo 📊, headers y 300-500 palabras. Al hacer bypass (usar directamente `response_text` del agente), la calidad CALIDAD subió del 67% al 93% y se eliminó 1 LLM call (~5-8s de latencia).

### 6. Datos MoM como métrica principal (no YoY)
El banco lleva operando desde sep-2024 (20 meses). Las comparativas interanuales muestran +100-1400% por efecto base bajo del primer año — visualmente impresionantes pero no representativas de la salud del banco. La variación MoM es la métrica significativa para el estadio actual.

### 7. Separación GestorAgent vs CDGAgent
Los gestores solo ven su propia cartera (filtro `WHERE GESTOR_ID = {id}`). El CDGAgent tiene acceso completo. Esta separación no es técnica (SQLite no tiene RLS) sino de prompt y routing: el GestorAgent inyecta el gestor_id en todas las queries, el CDGAgent no lo hace.

### 8. Nombres de clientes regionales (S76)
Los 52 clientes con nombres genéricos ("Cliente 91"…"Cliente 142") se renombraron con nombres reales según la ciudad del centro de su gestor (vascos para Bilbao, catalanes para Barcelona, etc.). Esto es crítico para credibilidad en demo ante un Director de banca.
