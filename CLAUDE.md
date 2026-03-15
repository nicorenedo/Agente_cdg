# CLAUDE.md — Agente Control de Gestión (CDG)
> Este archivo es el contexto maestro para Claude Code. Léelo completo antes de escribir cualquier línea de código.

---

## ⚠️ ADVERTENCIAS CRÍTICAS ANTES DE EMPEZAR

### 1. LLM: Azure OpenAI — NO Anthropic API
Este proyecto usa **Azure OpenAI**, no la API de Anthropic directamente. Toda integración LLM debe hacerse mediante el cliente de Azure OpenAI con las credenciales del `.env`. No uses `anthropic` SDK ni `claude` como modelo en ningún punto del código.

### 2. El código existente en el repositorio contiene errores
El código que pueda existir en el repo clonado **NO es de confianza**. Contiene queries SQL incorrectas, fórmulas de negocio mal implementadas y arquitectura deficiente.
- **No reutilices ningún archivo existente sin validarlo explícitamente primero.**
- Ante cualquier duda: reescribe desde cero siguiendo este CLAUDE.md.

---

## 1. VISIÓN GENERAL DEL PROYECTO

**Agente CDG** — copiloto de negocio LLM para análisis de resultados financieros, detección de desviaciones, evaluación de incentivos y Business Reviews, con dashboards interactivos y chat conversacional.

| Perfil | Acceso a datos |
|---|---|
| **Gestor Comercial** | Solo su cartera — filtrar siempre `WHERE GESTOR_ID = {id}` |
| **Control de Gestión / Dirección** | Sin restricciones |

---

## 2. STACK TECNOLÓGICO

**Backend:** Python 3.11+, FastAPI, SQLite (`BM_CONTABILIDAD_CDG.db`), LangChain/LangGraph, Azure OpenAI, Pandas, Pydantic.
**Frontend:** React, Ant Design (AntD), Recharts, D3.js.
**Patrones:** Tool Pattern, Reflection Pattern, Agentic Pattern, Multiagent (fase futura).

---

## 3. ESTRUCTURA DE CARPETAS

```
backend/src/
  database/  BM_CONTABILIDAD_CDG.db, db_connection.py
  agents/    gestor_agent.py, cdg_agent.py, chat_agent.py
  tools/     sql_tools.py, kpi_calculator.py, chart_generator.py, report_generator.py
  queries/   basic_queries.py, period_queries.py, gestor_queries.py,
             comparative_queries.py, deviation_queries.py, incentive_queries.py
  prompts/   system_prompts.py, user_prompts.py, chart_prompts.py
  utils/     reflection_pattern.py, auth.py
backend/  main.py, config.py, requirements.txt
frontend/src/
  components/common/     TopBar.jsx, Card.jsx, Loader.jsx, ErrorState.jsx
  components/Dashboard/  KPICards.jsx, InteractiveCharts.jsx, DeviationAnalysis.jsx,
                         DrillDownView.jsx, ChatInterface.jsx, ConversationalPivot.jsx
  pages/    LandingPage.jsx, GestorView.jsx, DireccionView.jsx
  services/ api.js, chatService.js, analyticsService.js, reportService.js
  styles/   theme.js
```

---

## 4. BASE DE DATOS — `BM_CONTABILIDAD_CDG.db`

SQLite, 14 tablas, UTF-8. Períodos: **sep-2025** y **oct-2025**. Al leer CSVs usar `encoding='latin-1'`.

**Tablas maestras:**
- `MAESTRO_CENTROS`: Finalistas (1-5): MADRID, PALMA, BARCELONA, MALAGA, BILBAO. Soporte (6-8): RRHH, DIR.FINANCIERA, TECNOLOGÍA.
- `MAESTRO_GESTORES`: 30 gestores. Centro 1 (IDs 1-8), C2 (9-16), C3 (17-21), C4 (22-26), C5 (27-30).
- `MAESTRO_CONTRATOS`: **220 contratos** (216 originales + 4 nuevos oct-2025). Series: 1001-1076 (hip), 2001-2071 (dep), 3001-3073 (fondos).
- `MAESTRO_PRODUCTOS`: `100100100100` Hipotecario (100% banco) | `400200100100` Depósito (100% banco) | `600100300300` Fondo March (85% gestora / 15% banco).
- `MAESTRO_SEGMENTOS`: N10101=Minorista | N10102=Privada | N10103=Empresas | N10104=Personal | N20301=Fondos

**Tablas transaccionales:**
- `MOVIMIENTOS_CONTRATOS`: ~2,900+ registros. `CONTRATO_ID` puede ser NULL (gastos centrales — intencionado). Ingresos: `76xxxx`. Gastos directos: `62xxxx`, `64xxxx`, `68xxxx`, `69xxxx`. Modelo fábrica: `760024` banco 15% / `760025` gestora 85%.
- `GASTOS_CENTRO`: Sep €455k | Oct €222k. ⚠️ Gastos reales oct están en MOVIMIENTOS (CONTRATO_ID IS NULL), no aquí (muestra €0).
- `PRECIO_POR_PRODUCTO_REAL`: 30 registros. Solo CDG/Dirección.
- `PRECIO_POR_PRODUCTO_STD`: 15 registros. Ambos perfiles.

**P&L (MAESTRO_LINEA_CDR):** CR0001→CR0007 MARGEN FINANCIERO → CR0012 MARGEN BRUTO → CR0018 MARGEN EXPLOTACIÓN → CR0030 MARGEN APORTADO.

---

## 5. REGLAS DE NEGOCIO CRÍTICAS

**5.1 Redistribución gastos centrales:**
`Gasto_i = Gasto_Central_Total × (Contratos_Centro_i / Total_Contratos_Finalistas)`

**5.2 Precio Real por Producto:** `Precio_Real = Gastos_Totales_Asignados / Num_Contratos_Base`

**5.3 Semáforo desviaciones vs STD:** 🟢 <5% | 🟡 5-15% | 🔴 >15%

**5.4 Modelo Fábrica (Fondos):** Gestora 85% (`760025`) / Banco 15% (`760024`). Afecta rentabilidad real del gestor.

**5.5 Filtro gastos directos:** `SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69')` con `CONTRATO_ID IS NOT NULL`. Las cuentas 66xxxx tienen `CONTRATO_ID IS NULL` → van a redistribución central (correcto, no tocar).

---

## 6. CONTROL DE ACCESO

**Gestor:** ✅ Su cartera, KPIs propios, precios STD, comparativa anónima vs centro. ❌ Otros gestores, precios REAL. Filtrar siempre `WHERE GESTOR_ID = {gestor_id}`.
**CDG/Dirección:** ✅ Acceso completo sin restricciones.

---

## 7. ENDPOINTS FASTAPI (implementados en `main.py`)

```
POST /chat/gestor                          POST /chat/message (CDG)
GET  /chat/gestor/{id}/status              POST /chat/gestor/{id}/reset
GET  /kpis/gestor/{id}/roe                 GET  /kpis/consolidado
GET  /analytics/gestor/{id}/metricas-completas
GET  /analytics/gestor/{id}/clientes-con-metricas
GET  /charts/gestores-ranking?metric=CONTRATOS|CLIENTES|INGRESOS|MARGEN_NETO|ROE&periodo=
GET  /charts/centros-distribution          GET  /charts/productos-popularity
POST /charts/pivot
GET  /deviations/pricing                   GET  /incentives/gestor/{id}/detalle
GET  /basic/productos/by-gestor/{id}
```

---

## 8. SYSTEM PROMPTS BASE

**Gestor:** `Eres copiloto de {nombre_gestor}, segmento {segmento}, centro {centro}. Solo accedes a gestor ID: {gestor_id}. Rechaza consultas sobre otros gestores. Español, tono bancario profesional.`
**CDG:** `Eres agente CDG Intelligence con acceso completo. Análisis profundos, detección de desviaciones, insights estratégicos para dirección. Español técnico.`

---

## 9. CONSULTAS SQL DE REFERENCIA

Ver implementaciones validadas en `basic_queries.py`, `gestor_queries.py`, `comparative_queries.py`, `deviation_queries.py`.

Patrón estándar:
- **Ingresos:** `SUM(IMPORTE) WHERE CUENTA_ID LIKE '76%'`
- **Gastos directos:** `ABS(SUM(IMPORTE)) WHERE SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69') AND CONTRATO_ID IS NOT NULL`
- **Gastos redistribuidos:** `gastos_centrales_periodo × (n_contratos_gestor / 220)`
- **Gastos centrales:** `ABS(SUM(IMPORTE)) WHERE CONTRATO_ID IS NULL AND SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69')`

---

## 10. VARIABLES DE ENTORNO

```env
AZURE_OPENAI_API_KEY=AZURE_OPENAI_API_KEY_REDACTED
AZURE_OPENAI_ENDPOINT=https://TU_RECURSO.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_ID=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
DATABASE_PATH=./backend/src/database/BM_CONTABILIDAD_CDG.db
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

```python
from langchain_openai import AzureChatOpenAI
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_ID"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0,
)
```

---

## 11. ORDEN DE DESARROLLO

Fases 1-7: Base → Backend Core → Agentes → Frontend Base → Chat → Dinamismo → Avanzado (reflection, what-if, reportes). **Estado actual: Fase 6 completada, Fase 7 pendiente.**

---

## 12. ESTADO ACTUAL DEL PROYECTO

> ⚠️ Esta sección debe actualizarse al final de cada sesión de trabajo.
> Última actualización: 2026-03-15 (sesión 18)

### ✅ Completado (sesiones 1-17)

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

---

### 📊 Valores de referencia (post-sesión-17)

| Métrica | Valor |
|---|---|
| Total contratos | 220 (avg 7.33/gestor, StdDev 2.39, rango [4,12]) |
| Total movimientos | ~2,900+ |
| Gastos centrales sep / oct | -€41,103 / -€45,677 |
| ROE grupo oct-2025 | **36.77%** (ingresos €592,464 / gastos -€374,623 / margen €217,841) |
| Avg Privada oct | €37,656 (2.01× Minorista €19,697) |
| Gestor 1 oct (referencia) | ingresos ~€32,238, gastos directos ~€3,079 |
| Modelo fábrica | ratio 5.6667 exacto en 125 pares contrato/período |
| Margen por segmento oct | Privada 91.8% > Minorista 85.7% > Empresas 80.9% > Personal 72.4% > Fondos 66.0% |
| Outlier aceptado | G8 Pablo Moreno (-57.4% sep): fondos lumpy, no corregible sin romper modelo fábrica |

---

### ⏭️ Próximo paso exacto al retomar

**Tests de agente pendientes de mejora (sesión 18 — diagnóstico):**

| Test | Estado | Problema |
|---|---|---|
| Gestor Q1: 3 clientes más rentables | ✅ | Nombra clientes reales, cifras correctas |
| Gestor Q2: Evolución sep→oct | ⚠️ | Margen calculado diferente (gestor_queries vs basic_queries): tool devuelve ~104% vs endpoint 75.11% |
| Gestor Q3: Números no cuadran | ✅ | Empatía + ofrece revisar datos, no inventa |
| Gestor Q4: Acceso otros gestores | ✅ | Rechaza correctamente, ofrece benchmarks anónimos |
| Gestor Q5: Prompt injection | ✅ | Resiste, mantiene restricción |
| CDG Q1: Mejor margen | ⚠️ | Responde con datos reales, pero interpreta "margen" como % (Clara 227%) en lugar de € absolutos (Javier €48k). Aclarar pregunta. |
| CDG Q2: Desviaciones críticas por centro | ✅ | Identifica N20301/Fondos con alertas ALTA correctas |
| CDG Q3: ROE grupo | ❌ | No tiene endpoint/tool consolidado. Dice "datos no disponibles" en vez de calcular 36.77% |
| CDG Q4: Gestores empeorado sep→oct | ❌ | Confunde "empeorado" con "desvío vs media oct". No compara sep→oct |

**Siguientes fixes necesarios (por prioridad):**
1. **CDG ROE grupo**: Crear endpoint `/kpis/consolidado?periodo=` que calcule ROE total (ingresos - todos gastos) / patrimonio. O añadir tool en `cdg_agent.py` que llame a `period_queries.get_periodo_metricas_financieras()`
2. **CDG Q4 (sep→oct)**: Añadir tool `get_evolucion_gestores_sep_oct` en CDG agent usando `comparative_queries.compare_margen_segmento_periodos` o similar
3. **Gestor Q2 (inconsistencia margen)**: Unificar cálculo de margen_neto en todas las queries — todas deben usar `beneficio_neto / ingresos * 100` con gastos como negativos correctamente
4. **Prueba visual dashboards**: Verificar frontend con datos corregidos (rankings muestran Privada, pivoteo funciona, comparativa sep→oct en rango [-15%,+20%])

---

### ⚠️ Pendiente de decisión
- `MAESTRO_CONTRATOS_BACKUP_20250922_002703` — tabla basura en la BD, pendiente de `DROP TABLE`
- `backend/src/utils/initial_agent.py` — usa `openai` SDK directo en lugar de LangChain, pendiente de reescribir (no bloquea la POC)
- `GET /basic/precios-std` y `GET /prices/comparison` — devuelven 404; no se usan en ningún flujo activo
- `analyticsService.js:2857` — `.replace('Fondo Banca March', 'Fondos CDG')` mantiene el string del nombre real en BD (no es UI-visible, no se toca)
- `BM_CONTABILIDAD_CDG_backup_20260315.db` — backup de la BD pre-corrección, mantener hasta confirmar que el sistema arranca correctamente
