# CLAUDE.md — Agente Control de Gestión (CDG)
> Este archivo es el contexto maestro para Claude Code. Léelo completo antes de escribir cualquier línea de código.

---

## ⚠️ ADVERTENCIAS CRÍTICAS ANTES DE EMPEZAR

### 1. LLM: Azure OpenAI — NO Anthropic API
Este proyecto usa **Azure OpenAI**, no la API de Anthropic directamente. Toda integración LLM debe hacerse mediante el cliente de Azure OpenAI con las credenciales del `.env`. No uses `anthropic` SDK ni `claude` como modelo en ningún punto del código.

### 2. El código existente en el repositorio contiene errores
El código que pueda existir en el repo clonado (Azure DevOps / GitHub) **NO es de confianza**. Contiene queries SQL incorrectas, fórmulas de negocio mal implementadas y arquitectura deficiente.
- **No reutilices ningún archivo existente sin validarlo explícitamente primero.**
- Trata el repo como una referencia de estructura, nunca como código funcional.
- Ante cualquier duda: reescribe desde cero siguiendo este CLAUDE.md.

---

## 1. VISIÓN GENERAL DEL PROYECTO

El **Agente CDG** es un copiloto de negocio basado en LLM para **Banca March** que permite a gestores comerciales y al equipo de Control de Gestión analizar resultados financieros, detectar desviaciones, evaluar incentivos y preparar Business Reviews, todo desde dashboards interactivos con capacidad conversacional.

**Dos perfiles de usuario con acceso diferenciado:**

| Perfil | Descripción | Acceso a datos |
|---|---|---|
| **Gestor Comercial** | Ve solo su propia cartera. No puede ver datos de otros gestores. | Limitado a su cartera |
| **Control de Gestión / Dirección** | Visión global, todos los gestores y centros | Sin restricciones |

---

## 2. STACK TECNOLÓGICO

### Backend
- **Python 3.11+** con **FastAPI** para la API REST
- **SQLite** — base de datos `BM_CONTABILIDAD_CDG.db`
- **LangChain / LangGraph** para los agentes LLM
- **Azure OpenAI** como LLM principal — ver credenciales en sección 11
- **Pandas** para procesamiento de datos y cálculo de KPIs
- **Pydantic** para validación de modelos

### Frontend
- **React** (Create React App o Vite)
- **Ant Design (AntD)** para componentes UI empresariales
- **Recharts** para gráficos estándar
- **D3.js** para visualizaciones avanzadas personalizadas

### Patrones Agenticos
- **Tool Pattern**: cada funcionalidad como `@tool` decorado, reutilizable entre agentes
- **Reflection Pattern**: autoevaluación antes de presentar respuestas, mejora continua con feedback (👍👎)
- **Agentic Pattern**: el agente decide autónomamente qué herramientas usar
- **Multiagent Pattern** (fase futura): agentes especializados coordinados por agente principal

---

## 3. ESTRUCTURA DE CARPETAS OBJETIVO

```
agente-cdg/
├── backend/
│   ├── src/
│   │   ├── database/
│   │   │   ├── BM_CONTABILIDAD_CDG.db        # Base de datos SQLite
│   │   │   └── db_connection.py              # Conexión y queries base
│   │   ├── agents/
│   │   │   ├── gestor_agent.py               # Agente del gestor comercial
│   │   │   ├── cdg_agent.py                  # Agente de control de gestión
│   │   │   └── chat_agent.py                 # Conversación interactiva
│   │   ├── tools/
│   │   │   ├── sql_tools.py                  # Herramientas SQL (con guard por perfil)
│   │   │   ├── kpi_calculator.py             # Cálculos financieros
│   │   │   ├── chart_generator.py            # Generación de gráficos
│   │   │   └── report_generator.py           # Business Reviews automáticos
│   │   ├── queries/
│   │   │   ├── basic_queries.py              # Consultas base
│   │   │   ├── period_queries.py             # Consultas temporales
│   │   │   ├── gestor_queries.py             # Consultas por gestor
│   │   │   ├── comparative_queries.py        # Comparativas peer/temporal
│   │   │   ├── deviation_queries.py          # Análisis de desviaciones
│   │   │   └── incentive_queries.py          # Evaluación de incentivos
│   │   ├── prompts/
│   │   │   ├── system_prompts.py             # System prompts por agente
│   │   │   ├── user_prompts.py               # Templates de prompts
│   │   │   └── chart_prompts.py              # Prompts para gráficos
│   │   └── utils/
│   │       ├── reflection_pattern.py         # Sistema de aprendizaje continuo
│   │       └── auth.py                       # Control de acceso por perfil
│   ├── tests/
│   ├── main.py                               # FastAPI entry point
│   ├── config.py                             # Configuración Azure OpenAI
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── TopBar.jsx
│   │   │   │   ├── Card.jsx
│   │   │   │   ├── Loader.jsx
│   │   │   │   └── ErrorState.jsx
│   │   │   └── Dashboard/
│   │   │       ├── KPICards.jsx
│   │   │       ├── InteractiveCharts.jsx
│   │   │       ├── DeviationAnalysis.jsx
│   │   │       ├── DrillDownView.jsx
│   │   │       ├── ChatInterface.jsx
│   │   │       └── ConversationalPivot.jsx
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx
│   │   │   ├── GestorView.jsx
│   │   │   └── DireccionView.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── chatService.js
│   │   │   ├── analyticsService.js
│   │   │   └── reportService.js
│   │   └── styles/
│   │       └── theme.js
│   └── package.json
├── data/
├── CLAUDE.md
├── .env
└── .gitignore
```

---

## 4. BASE DE DATOS — `BM_CONTABILIDAD_CDG.db`

SQLite con **14 tablas**. Encoding: **UTF-8**. Períodos de datos: **septiembre y octubre 2025**.

> ⚠️ Al leer CSVs originales usar `encoding='latin-1'` para evitar problemas con caracteres especiales.

### 4.1 Tablas Maestras

#### `MAESTRO_CENTROS`
Centros Finalistas (1-5): MADRID, PALMA, BARCELONA, MALAGA, BILBAO
Centros de Soporte (6-8): RRHH, DIRECCIÓN FINANCIERA, TECNOLOGÍA — sus gastos se redistribuyen a los finalistas.

#### `MAESTRO_GESTORES`
30 gestores. Centro 1 (IDs 1-8), Centro 2 (9-16), Centro 3 (17-21), Centro 4 (22-26), Centro 5 (27-30).

#### `MAESTRO_CONTRATOS` ← Tabla central
216 contratos activos. Series: 1001-1075 (hipotecas), 2001-2069 (depósitos), 3001-3072 (fondos).

#### `MAESTRO_PRODUCTOS`
- `100100100100`: Préstamo Hipotecario (100% banco)
- `400200100100`: Depósito a Plazo Fijo (100% banco)
- `600100300300`: Fondo Banca March (85% gestora / 15% banco) ← modelo fábrica

#### `MAESTRO_SEGMENTOS`
N10101=Minorista | N10102=Privada | N10103=Empresas | N10104=Personal | N20301=Fondos

### 4.2 Tablas Transaccionales

#### `MOVIMIENTOS_CONTRATOS`
2.100 registros. `CONTRATO_ID` puede ser NULL (gastos centrales sin contrato específico — es intencionado).
- Ingresos: cuentas `76xxxx` — Gastos: `62xxxx`, `64xxxx`, `68xxxx`, `69xxxx`
- Cuentas clave: `760024` banco 15%, `760025` gestora 85% (modelo fábrica fondos)

#### `GASTOS_CENTRO`
Sep-2025: €455,000 | Oct-2025: €222,718

#### `PRECIO_POR_PRODUCTO_REAL`
30 registros. Solo visible para CDG/Dirección.

#### `PRECIO_POR_PRODUCTO_STD`
15 registros. Visible para ambos perfiles.

### 4.3 P&L (MAESTRO_LINEA_CDR)
```
CR0001 Ingresos financieros → CR0007 MARGEN FINANCIERO
→ CR0008 Comisiones → CR0012 MARGEN BRUTO
→ CR0013-CR0017 Gastos → CR0018 MARGEN EXPLOTACIÓN
→ CR0029 Coste capital → CR0030 MARGEN APORTADO
```

---

## 5. REGLAS DE NEGOCIO CRÍTICAS

### 5.1 Redistribución de Gastos Centrales
```
Gasto_Redistribuido_Centro_i = Gasto_Central_Total × (Contratos_Centro_i / Total_Contratos_Finalistas)
```

### 5.2 Precio Real por Producto
```
Precio_Real = Gastos_Totales_Asignados / Num_Contratos_Base
```

### 5.3 Semáforo de Desviaciones vs STD
🟢 <5% | 🟡 5-15% | 🔴 >15%

### 5.4 Modelo Fábrica (Fondos)
Gestora 85% (`760025`) / Banco 15% (`760024`). Afecta a la rentabilidad real del gestor.

---

## 6. CONTROL DE ACCESO

### Gestor Comercial
- ✅ Su cartera, sus KPIs, precios STD, comparativa anónima vs centro
- ❌ Otros gestores, precios REAL, otros centros
- El agente debe RECHAZAR consultas sobre otros gestores. Siempre filtrar `WHERE GESTOR_ID = {gestor_id}`

### Control de Gestión / Dirección
- ✅ Acceso completo sin restricciones

---

## 7. ENDPOINTS FASTAPI

```
POST /api/chat/gestor | POST /api/chat/cdg
GET  /api/kpis/gestor/{id} | GET /api/kpis/consolidado
GET  /api/charts/gestor/{id} | GET /api/charts/cdg
GET  /api/deviations | GET /api/drilldown/{nivel}
POST /api/feedback | POST /api/charts/dynamic
```

---

## 8. SYSTEM PROMPTS BASE

**Gestor:** `Eres copiloto de {nombre_gestor}, segmento {segmento}, centro {centro}. Solo accedes a gestor ID: {gestor_id}. Rechaza consultas sobre otros gestores. Español, tono bancario profesional.`

**CDG:** `Eres agente de control de gestión con acceso completo a todos los datos. Análisis profundos, detección de desviaciones, insights estratégicos para dirección. Español técnico.`

---

## 9. CONSULTAS SQL DE REFERENCIA

### Margen aportado por gestor
```sql
SELECT mg.GESTOR_ID, mg.DESC_GESTOR, mg.CENTRO, mg.SEGMENTO_ID,
    SUM(CASE WHEN mc.IMPORTE > 0 THEN mc.IMPORTE ELSE 0 END) as INGRESOS,
    SUM(CASE WHEN mc.IMPORTE < 0 THEN mc.IMPORTE ELSE 0 END) as GASTOS,
    SUM(mc.IMPORTE) as MARGEN_APORTADO
FROM MAESTRO_GESTORES mg
JOIN MAESTRO_CONTRATOS mct ON mg.GESTOR_ID = mct.GESTOR_ID
JOIN MOVIMIENTOS_CONTRATOS mc ON mct.CONTRATO_ID = mc.CONTRATO_ID
WHERE mc.FECHA BETWEEN '2025-10-01' AND '2025-10-31'
GROUP BY mg.GESTOR_ID, mg.DESC_GESTOR, mg.CENTRO, mg.SEGMENTO_ID
ORDER BY MARGEN_APORTADO DESC;
```

### Desviaciones real vs estándar
```sql
SELECT r.SEGMENTO_ID, r.PRODUCTO_ID, r.FECHA_CALCULO,
    r.PRECIO_MANTENIMIENTO_REAL, s.PRECIO_MANTENIMIENTO as PRECIO_STD,
    ROUND((r.PRECIO_MANTENIMIENTO_REAL - s.PRECIO_MANTENIMIENTO) /
          s.PRECIO_MANTENIMIENTO * 100, 2) as DESVIACION_PCT
FROM PRECIO_POR_PRODUCTO_REAL r
JOIN PRECIO_POR_PRODUCTO_STD s ON r.SEGMENTO_ID = s.SEGMENTO_ID AND r.PRODUCTO_ID = s.PRODUCTO_ID
ORDER BY ABS(DESVIACION_PCT) DESC;
```

### Cartera completa de un gestor
```sql
SELECT mc.CONTRATO_ID, mc.FECHA_ALTA, cl.NOMBRE_CLIENTE,
    mp.DESC_PRODUCTO, ms.DESC_SEGMENTO, SUM(mov.IMPORTE) as RESULTADO_CONTRATO
FROM MAESTRO_CONTRATOS mc
JOIN MAESTRO_CLIENTES cl ON mc.CLIENTE_ID = cl.CLIENTE_ID
JOIN MAESTRO_PRODUCTOS mp ON mc.PRODUCTO_ID = mp.PRODUCTO_ID
JOIN MAESTRO_GESTORES mg ON mc.GESTOR_ID = mg.GESTOR_ID
JOIN MAESTRO_SEGMENTOS ms ON mg.SEGMENTO_ID = ms.SEGMENTO_ID
LEFT JOIN MOVIMIENTOS_CONTRATOS mov ON mc.CONTRATO_ID = mov.CONTRATO_ID
WHERE mc.GESTOR_ID = :gestor_id
GROUP BY mc.CONTRATO_ID, mc.FECHA_ALTA, cl.NOMBRE_CLIENTE, mp.DESC_PRODUCTO, ms.DESC_SEGMENTO
ORDER BY RESULTADO_CONTRATO DESC;
```

---

## 10. VARIABLES DE ENTORNO

```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=AZURE_OPENAI_API_KEY_REDACTED
AZURE_OPENAI_ENDPOINT=https://TU_RECURSO.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_ID=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# App
DATABASE_PATH=./backend/src/database/BM_CONTABILIDAD_CDG.db
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

### Cliente LangChain para Azure OpenAI
```python
from langchain_openai import AzureChatOpenAI
import os

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

1. **Fase 1** — Base: setup proyecto, conexión BBDD, endpoints FastAPI básicos
2. **Fase 2** — Backend Core: queries SQL validadas, KPIs, redistribución de costes
3. **Fase 3** — Agentes: LangChain + Azure OpenAI, tools, system prompts, guards de acceso
4. **Fase 4** — Frontend Base: landing page, dashboards con KPIs y gráficos estáticos
5. **Fase 5** — Chat: integración conversacional en ambos dashboards
6. **Fase 6** — Dinamismo: pivoteo conversacional, gráficos dinámicos
7. **Fase 7** — Avanzado: reflection pattern, what-if, generación de reportes

---

## 12. ESTADO ACTUAL DEL PROYECTO

> ⚠️ Esta sección debe actualizarse al final de cada sesión de trabajo.
> Última actualización: 2026-03-13

### ✅ Completado

**Limpieza del repositorio (sesión 1):**
- Eliminados archivos basura: `BMCONTABILIDAD_CDG.db`, `BM_CONTABILIDAD_CDG.sqbpro`, `backend/scripts/` (23 archivos), `clear_cache.py`, `debug_import.py`, `frontend/src/components/__init__.py`, `frontend/tests/`
- Commit: `chore: limpieza pre-refactor - eliminados archivos obsoletos y basura`

**Validación de la base de datos:**
- Todas las tablas maestras verificadas y correctas contra CLAUDE.md
- 216 contratos, 30 gestores, 2100 movimientos, 15 registros STD, 30 registros REAL — todo cuadra
- Modelo fábrica confirmado: `760024` (banco 15%) y `760025` (gestora 85%) presentes
- Fechas en MOVIMIENTOS_CONTRATOS: solo `2025-09-01` y `2025-10-01` (fechas exactas del 1 de cada mes)
- Gastos centrales reales en octubre: -€45,676.97 en `MOVIMIENTOS_CONTRATOS WHERE CONTRATO_ID IS NULL` (NO en `GASTOS_CENTRO` que muestra €0 para oct)

**Reescritura de `backend/src/queries/basic_queries.py` (sesión 2 — completado):**
- Bug 1 corregido: funciones de métricas usaban `PRECIO_POR_PRODUCTO_STD` como coste operativo — **conceptualmente incorrecto** (STD es benchmark de desviaciones, no coste)
- Bug 2 corregido: solo capturaban 3 cuentas de gasto (`640001`, `691001`, `691002`) ignorando ~76% de los gastos reales
- Bug 3 corregido: redistribución de octubre tomaba de `GASTOS_CENTRO` (€0) en vez de `MOVIMIENTOS_CONTRATOS WHERE CONTRATO_ID IS NULL`
- Bug 4 corregido: bloque duplicado con implementaciones incorrectas (líneas 1022-1474) eliminado del archivo
- Funciones nuevas y validadas numéricamente:
  - `_get_gastos_centrales_periodo(periodo)` — suma `MOVIMIENTOS_CONTRATOS WHERE CONTRATO_ID IS NULL AND SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69')`
  - `_get_total_contratos_finalistas()` — denominador = 216 (todos los contratos están en centros finalistas)
  - `get_gestor_metricas_completas(gestor_id, periodo)` — ingresos 76xxxx + gastos directos 62/64/68/69xxxx + redistribuidos proporcionales
  - `get_gestor_clientes_con_metricas()`, `get_cliente_metricas()`, `get_cliente_contratos_con_metricas()`, `get_contrato_detalle_completo()`
  - `get_centro_metricas_financieras()`, `get_centro_gestores_con_metricas()`, `get_segmento_metricas_financieras()`
- Números validados (gestor 1, oct-2025): ingresos=32,560.15 | gastos directos=-3,078.79 | redistribuidos=-2,537.61 | beneficio=26,943.75 | margen=82.75%

**Corrección de queries restantes (sesión 3 — completado parcialmente):**
- `period_queries.py`: reescritas `get_periodo_metricas_financieras`, `get_periodo_analisis_gastos`, `get_periodo_evolucion_gastos` — eliminada dependencia de `PRECIO_POR_PRODUCTO_REAL`
- `gestor_queries.py`: añadidos helpers `_get_gastos_centrales()` + `_get_total_contratos_finalistas()`. Reescritas las 3 funciones críticas llamadas desde main.py/agentes: `get_gestor_performance_enhanced`, `calculate_eficiencia_operativa_gestor_enhanced`, `calculate_roe_gestor_enhanced`
- `comparative_queries.py`: reescritas las 4 funciones críticas llamadas desde main.py/cdg_agent: `ranking_gestores_por_margen_enhanced`, `compare_roe_gestores_enhanced`, `compare_eficiencia_centro_enhanced`
- `deviation_queries.py`: NO modificado — uso de PRECIO_STD/REAL es CORRECTO (análisis de desviaciones precio real vs benchmark)

**Corrección de `incentive_queries.py` (sesión 4 — completado):**
- 8 funciones corregidas: `calculate_incentivo_cumplimiento_objetivos_enhanced`, `calculate_incentivo_cumplimiento_objetivos`, `analyze_bonus_margen_neto_enhanced`, `analyze_bonus_margen_neto`, `calculate_ranking_bonus_pool_enhanced`, `calculate_ranking_bonus_pool`, `get_incentivos_por_centro`, `get_tendencia_incentivos`
- Patrón aplicado: `_enhanced` → SQL usa gastos_directos (62/64/68/69 + CONTRATO_ID IS NOT NULL) + redistribución Python inline; funciones non-enhanced pure SQL → ABS(SUM(gastos 62/64/68/69 CONTRATO_ID IS NOT NULL))
- `get_incentivos_por_centro` y `get_tendencia_incentivos` convertidas a patrón híbrido
- `calculate_margen_neto` y `calculate_ratio_eficiencia` reciben `abs(gastos)` (ambas esperan valor positivo)
- Prompt en `generate_dynamic_incentive_query` corregido para no sugerir PRECIO_REAL como gastos
- Commit: `7fb5e0f`

**Corrección de `gestor_queries.py` funciones con bug (sesión 5 — completado):**
- Revisión exhaustiva: solo 2 funciones usaban realmente PRECIO_REAL (no 12 como se estimó — resto ya usaban PRECIO_STD o MOVIMIENTOS)
- `get_alertas_criticas_gestor`: eliminada CTE `alertas_precio` que hacía JOIN a PRECIO_POR_PRODUCTO_REAL. Ahora solo genera `alertas_margen` con gastos operativos reales. Params reducidos de 9 a 7.
- `get_desviaciones_precio_gestor_enhanced`: reescrita para comparar coste efectivo real (gastos 62/64/68/69 de MOVIMIENTOS / nº contratos) vs PRECIO_STD. Eliminado JOIN a PRECIO_POR_PRODUCTO_REAL.
- Commit: pendiente (incluido en este commit)

**Creación de archivos nuevos (sesión 4 — completado):**
- `backend/src/utils/auth.py` — `AccessGuard` con `UserRole`, filtrado por perfil, detección cross-gestor en texto, inyección WHERE GESTOR_ID en SQL dinámico. Instancia global `access_guard`. Commit: `83d8db3`
- `backend/src/agents/gestor_agent.py` — `GestorAgent` con LangChain `create_tool_calling_agent` + Azure OpenAI. 6 tools (`get_mis_kpis`, `get_mi_cartera`, `get_mis_desviaciones`, `get_evolucion_sep_oct`, `get_mis_clientes`, `get_resumen_periodo`), caché por gestor_id, historial de conversación, guardia de acceso integrada. Funciones de conveniencia: `create_gestor_agent`, `process_gestor_message`. Commit: `83d8db3`

**Integración en `main.py` y `api.js` (sesión 5 — completado):**
- `backend/main.py`: imports + mock fallbacks para `gestor_agent` y `auth`; modelo `GestorChatRequest`; 3 nuevos endpoints `POST /chat/gestor`, `GET /chat/gestor/{id}/status`, `POST /chat/gestor/{id}/reset`; `/health` y `root()` actualizados
- `frontend/src/services/api.js`: módulo `gestorCopilot` con métodos `chat`, `status`, `reset`; exportado en objeto `api` y exports individuales
- `frontend/src/components/Dashboard/ChatInterface.jsx`: cuando `scope === 'gestor'`, usa `gestorCopilot.chat()` en lugar del chat genérico

**POC funcional end-to-end (sesión 6 — completado):**
- Creados `.env` y `requirements.txt` (Python 3.13 + numpy 2.x compatible)
- Identificado y corregido deployment ID: `gpt-5.4` → `gpt-4o` (el que realmente existe en el Azure)
- `gestor_agent.py` migrado de LangChain 0.3.x a LangChain 1.x (reemplazado `AgentExecutor` + `create_tool_calling_agent` por `create_react_agent` de `langgraph.prebuilt`)
- Validado end-to-end: el agente usa `get_mis_kpis`, consulta la BD real, y responde con datos reales en ~7s
- Frontend arrancado en localhost:3000, backend en localhost:8000

**Validación completa de ambos agentes (sesión 7 — completado):**
- **GestorAgent 3/3** (tests ya validados sesión anterior): margen, contratos, clientes
- **CDGAgent 2/2** (sesión 7):
  - Test 1 "¿Qué gestor tiene el mejor margen en octubre?" → `comparative_performance` | Top: Javier Fernández (Banca Privada, margen 526%), seguido por Clara Calvet, María González. Confianza: 0.85
  - Test 2 "¿Qué centros tienen desviaciones críticas vs precio estándar?" → `deviation_detection` | 12 desviaciones ALTA: Préstamo Hipotecario/Fondos (+17%), Fondo Banca March (+16.4%), Depósito Plazo Fijo (+15.8%). Confianza: 0.85
- Fixes aplicados:
  - `chat_agent.py`: propagación de `user_role`/`scope` del request context al clasificador (fix ACCESS_DENIED para CDG)
  - `main.py`: `determine_user_role` recibe ahora `req.context` con `user_role`
  - `cdg_agent.py`: `_determine_analysis_type` mejorado con keywords en español (`desviaci`, `que gestor`, `ranking`, etc.)
  - `cdg_agent.py`: `_deviation_detection_analysis` implementada con datos reales de `deviation_queries`
- Commit: `2590270`

**Diagnóstico y corrección del dashboard del gestor (sesión 8 — completado):**

**Diagnóstico previo:**
- `GET /analytics/gestor/1/clientes-con-metricas?periodo=2025-10` → array con `beneficio_neto`, `margen_neto_pct` ✓
- `GET /analytics/gestor/1/metricas-completas?periodo=2025-10` → sumario completo del gestor ✓
- `GET /kpis/gestor/1/roe?periodo=2025-10` → `{roe_pct: 129.49}` ✓
- `GET /incentives/gestor/1/detalle?periodo=2025-10` → `{total_incentivos: 16406.84}` ✓
- `GET /basic/productos/by-gestor/1` → `[{PRODUCTO_ID, DESC_PRODUCTO, num_contratos}]` ✓
- `POST /charts/pivot` → devuelve `{new_config, changes_made}` (sin datos de gráfico — requería dos pasos)
- `GET /prices/comparison` → **404 Not Found** (endpoint roto)
- `GET /basic/precios-std` → **404 Not Found** (endpoint roto)
- `GET /deviations/pricing?periodo=2025-10&umbral=0` → 15 desviaciones reales STD vs REAL ✓

**Bugs encontrados y corregidos en `analyticsService.js`:**
1. `getTopClientsChartData`: usaba `clientesByGestor` (solo nombres, sin métricas) → ahora usa `gestorClientesMetricas` (con `beneficio_neto`, `margen_neto_pct`)
2. `transformTopClients`: usaba `mockMetric: true` (datos aleatorios) → ahora usa `beneficio_neto` real
3. `getPriceComparisonChartData`: llamaba a `dataQueriesAPI.pricesComparison` (404) → ahora usa `deviationsAPI.pricing(periodo, 0)` con semáforo (ALTA=rojo, MEDIA=amarillo, BAJA=verde)
4. `pivotChart`: `/charts/pivot` solo devuelve nueva config (sin datos) → ahora hace dos pasos: Azure OpenAI interpreta intención → `getPivotableChartData` busca los datos → devuelve `{success, data, newConfig, changesMade}`
5. `getPivotableChartData`: para dimensión `cliente`, no había endpoint definido en PIVOTABLE_CONFIG → ahora detecta `dimension === 'cliente'` y llama directamente `gestorClientesMetricas`
6. `transformPivotableData`: campos `NOMBRE_CLIENTE`, `ingresos_cliente`, `beneficio_neto`, `num_contratos` no estaban en los fallbacks → añadidos

**Bug de wiring corregido en `GestorView.jsx`:**
- `handleConversationalChartUpdate` solo aceptaba un arg y ponía el chartData en `currentChartConfig` (equivocado)
- `InteractiveCharts` recibía `externalChartConfig` pero solo acepta `externalChartData` → el gráfico dinámico nunca se actualizaba
- Fix: nuevo estado `pivotedChartData`; `handleConversationalChartUpdate(chartData, newConfig)` setea ambos; InteractiveCharts recibe `externalChartData={pivotedChartData}`

**Endpoints y flujo de cada gráfico del gestor (después de los fixes):**
| Gráfico | Endpoint | Datos |
|---|---|---|
| Top Clientes por Margen | `GET /analytics/gestor/{id}/clientes-con-metricas?periodo=` | `beneficio_neto` real por cliente |
| Mix de Productos | `GET /basic/productos/by-gestor/{id}` | `num_contratos` por producto |
| Comparativa de Precios | `GET /deviations/pricing?periodo=&umbral=0` | STD vs Real con nivel_alerta |
| Gráfico Dinámico | `POST /charts/pivot` → Azure OpenAI → `getPivotableChartData` | Según combinación métrica/dimensión/tipo |

**Flujo del pivoteo:**
1. Usuario escribe en ConversationalPivot (panel derecho)
2. `analyticsService.pivotChart(userId, mensaje, config, 'pivot', {gestorId, periodo})` → POST `/charts/pivot`
3. Azure OpenAI interpreta la intención → devuelve `{new_config: {metric, dimension, chartType}, changes_made}`
4. `getPivotableChartData(metric, dimension, chartType, {gestorId, periodo})` → obtiene datos reales
5. Retorna `{success: true, data: {labels, datasets, meta}, newConfig, changesMade}`
6. ConversationalPivot llama `onChartUpdate(chartData, newConfig)` → `handleConversationalChartUpdate`
7. `setPivotedChartData(chartData)` → fluye a `InteractiveCharts` como `externalChartData`
8. `InteractiveCharts` detecta el cambio → activa tab "Gráfico Dinámico" y renderiza

**Commits de esta sesión:**
- `50f92c2` — KPICards variaciones reales sep→oct + debug mode off + encoding fix
- `1d1d63c` — analyticsService + GestorView: datos reales en todos los gráficos + pivot funcional

### ⏭️ Próximo paso exacto al retomar

**Siguiente: dashboard de Dirección (CDG)**
- Revisar `DireccionView.jsx` y sus gráficos (gestores-ranking, centros-distribution, productos-popularity)
- Verificar que los endpoints `GET /charts/gestores-ranking`, `GET /charts/centros-distribution`, `GET /charts/productos-popularity` devuelven datos reales
- Confirmar que el chat de Dirección funciona end-to-end en el frontend (usa `/chat/message` con `user_role: control_gestion`)
- Probar el pivoteo desde el dashboard de Dirección

### ⚠️ Pendiente de decisión
- `MAESTRO_CONTRATOS_BACKUP_20250922_002703` — tabla basura en la BD, pendiente de `DROP TABLE`
- `backend/src/utils/initial_agent.py` — usa `openai` SDK directo en lugar de LangChain, pendiente de reescribir (no bloquea la POC)
- `GET /basic/precios-std` y `GET /prices/comparison` — devuelven 404; no se usan en ningún flujo activo