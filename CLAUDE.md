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
> Última actualización: 2026-03-15

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
- `accdb8e` — InteractiveCharts stale-closure fix + ConversationalPivot localStorage isolation
- `74cdb71` — Loop infinito backend + pivot success wrapper
- `b82260e` — analyticsService: ?? + || mixing syntax error (missing parens)
- `41f37ef` — InteractiveCharts: ESLint cleanup (ref values copied to local vars)

**Bugs corregidos (sesión de continuación 2):**

Bug 1 — Loop infinito en backend ("Maximum request limit exceeded"):
- Root cause: `filters = {}` default prop en `InteractiveCharts` crea nuevo objeto cada render → `filters` estaba en deps de `loadChartData` → callback se recreaba cada render → `loadAllCharts` se recreaba → `useEffect` se re-disparaba → `setLoadingStates` → re-render → loop infinito → cientos de llamadas a `/basic/gestores/by-segmento` y `/deviations/pricing`
- Fix: `filtersRef` (useRef) almacena el valor actual de `filters`; `loadChartData` lee `filtersRef.current`; `filters` eliminado de deps del useCallback

Bug 2 — Pivot "Muéstrame ingresos por cliente" → "No se pudo completar":
- Root cause: en `pivotChart()`, el path de fallback local (cuando backend falla) devolvía `pivotedData` directamente (objeto con `labels/datasets`). `ConversationalPivot` comprueba `pivotResult.success` → `undefined` → falsy → lanzaba el error genérico
- Fix: fallback local ahora devuelve `{success: true, data: pivotedData, newConfig, changesMade, interpretation}` igual que el path del backend
- También: `transformPivotableData` usa `??` (nullish) para mapear `ingresos_cliente` preservando 0 como valor válido

**Bug corregido (sesión de continuación 3):**

Bug — Pivot "Muéstrame los ingresos por cliente" → metric=CLIENTES dimension=CLIENTES (incorrecto):
- Root cause 1 (`chart_prompts.py`): `CONFIDENTIALITY_RULES['GESTOR']['allowed_dimensions']` no incluía `cliente`. El prompt enviado a Azure OpenAI listaba como dimensiones válidas solo `periodo, producto, contrato`. El modelo no podía usar `cliente` como dimensión → lo mapeaba a la métrica `CLIENTES` en su lugar.
- Root cause 2: El `CHART_PIVOT_SYSTEM_PROMPT` tampoco listaba `cliente` en las dimensiones del ROL GESTOR. No había ejemplos de "ingresos por cliente" ni "margen por cliente".
- Fix `chart_prompts.py`: añadido `cliente` a `allowed_dimensions` del GESTOR; añadido `cliente` al bloque ROL GESTOR del system prompt; añadidos ejemplos explícitos ("ingresos por cliente" → metric:INGRESOS dimension:cliente, etc.); añadida regla explícita: "NUNCA uses CLIENTES como valor de metric — cliente es una DIMENSIÓN"
- Fix `analyticsService.js` (fallback de seguridad): en `pivotChart()`, si Azure devuelve `metric='CLIENTES'` o `'clientes'` mapear a `CONTRATOS`; si devuelve `dimension='clientes'` mapear a `cliente` — aplicado en path principal y path fallback local. Commit: `7000c99`

**Bugs corregidos (sesión de continuación 1):**

Bug 1 — `InteractiveCharts.jsx` gráficos vacíos (stale closure race condition):
- Root cause: `loadChartData` tenía `loadingStates` en sus deps → al cambiar el estado de carga, el callback se recreaba → `loadAllCharts` se recreaba → pero el loading `useEffect` tenía deps `[periodo, mode, gestorId]` sin `loadAllCharts`, así que usaba la versión stale donde `chartConfigs = {}` → `if (!config) return` → ningún gráfico se cargaba nunca
- Fix: `loadingRef.current` (useRef) reemplaza `loadingStates` como guard de carga concurrente; eliminado `loadingStates` de deps de `loadChartData`; loading `useEffect` ahora incluye `[..., loadAllCharts, chartConfigs]` con guard `if (Object.keys(chartConfigs).length === 0) return` para esperar la inicialización

Bug 2 — `ConversationalPivot.jsx` historial persiste entre sesiones:
- Root cause: localStorage key era `conversational-pivot-history-${mode}` — misma key para todos los gestores y períodos
- Fix: key cambiada a `...-${mode}-${gestorId}-${periodo}`; useEffect de carga incluye `gestorId` y `periodo` en deps; al cambiar key sin datos previos, limpia el estado

**Dashboard de Dirección (CDG) — sesión 9 — completado:**

**Diagnóstico previo (endpoints verificados):**
- `GET /charts/gestores-ranking?metric=CONTRATOS` → 15 gestores, conteos reales ✓
- `GET /charts/centros-distribution` → 5 centros con contratos reales ✓
- `GET /charts/productos-popularity` → 3 productos con popularidad real ✓
- `GET /charts/gestores-ranking?metric=INGRESOS/MARGEN_NETO/ROE` → NO funcionaba (solo CONTRATOS/CLIENTES)

**Bugs encontrados y corregidos:**

Bug 1 — `gestores-ranking` no soportaba INGRESOS/MARGEN_NETO/ROE:
- Root cause: endpoint tenía enum `["CONTRATOS","CLIENTES"]`; sin parámetro `periodo`; delegaba todo a `QueryIntegratedChartGenerator` que solo manejaba conteos
- Fix: endpoint reescrito en `main.py` con routing por métrica: INGRESOS/MARGEN_NETO → `comparative_queries.ranking_gestores_por_margen_enhanced(periodo)`; ROE → `compare_roe_gestores_enhanced(periodo)`
- Commit: `9911aa5`

Bug 2 — Pivot Dirección nunca renderizaba en InteractiveCharts:
- Root cause: `DireccionView.jsx` pasaba `externalChartConfig` (incorrecto) en lugar de `externalChartData`; `handleConversationalChartUpdate` solo aceptaba un arg; no existía estado `pivotedChartData`
- Fix: añadido estado `pivotedChartData`; handler acepta `(chartData, newConfig)`; prop corregida a `externalChartData={pivotedChartData}`
- Commit: `9911aa5`

Bug 3 — `PIVOTABLE_CONFIG` sin endpoints para INGRESOS+producto/ranking (Dirección):
- Root cause: validación rechazaba combinaciones INGRESOS+gestor/centro/producto para modo Dirección por falta de endpoints
- Fix: añadidos `producto: 'charts.productosPopularity'` y `ranking: 'charts.gestoresRanking'` a INGRESOS y MARGEN_NETO en PIVOTABLE_CONFIG
- Commit: `9911aa5`

Bug 4 — `getPivotableChartData` fallaba para Dirección (gestorId=null) con dimension=gestor/centro/producto:
- Root cause: path normal llamaba `analyticsAPI.gestorMetricasCompletas(undefined, periodo)` → 422 error
- Fix: early-return special cases para dimension=gestor/centro/producto sin gestorId → llaman `chartsAPI.gestoresRanking/centrosDistribution/productosPopularity`
- Commit: `9911aa5`

**Chat CDG (sesión 10 — completado):**

Bug 5 — Chat CDG (`/chat/message` con `user_role: control_gestion`) retornaba DYNAMIC_SQL con "Consulta no procesable":
- Root cause 1: Routing: `cdg_intents` solo incluía `business_review/executive_summary/deviation_detection`. Queries comparativas (`comparative_analysis`, `performance_analysis`) iban a REGLA 3 (SQL) antes de REGLA 3 CDG. REGLA 3 buscaba predefined query → no encontraba → DYNAMIC_SQL
- Root cause 2: `BankingResponseFormatter.format_response()` llamada con kwargs no definidos: `cdg_analysis=True, preferences=, user_role=, gestor_id=, is_personal=` → `TypeError` → fallback a DYNAMIC_SQL
- Fix 1: Expandidos `cdg_intents` a incluir `comparative_analysis`, `performance_analysis`, `ranking_analysis`, `global_analysis`, `incentive_analysis`
- Fix 2: Añadida REGLA 2b: si `user_role=control_gestion AND requires_sql AND not is_personal` → CDG_AGENT (catch-all para CDG)
- Fix 3: `format_response()` ahora recibe los kwargs en el dict `context={}` estándar
- Commit: `a96db0e`

**Resultado validado:**
- `/chat/message` con `user_role: control_gestion` + "Que gestor tiene el mejor margen en octubre?" → flow_type=CDG_AGENT → respuesta con datos reales: Javier Fernández, margen 526%, ranking completo ✓
- `/charts/gestores-ranking?metric=INGRESOS&periodo=2025-10` → Francisco Martínez €30,417 (real) ✓
- `/charts/gestores-ranking?metric=MARGEN_NETO` → beneficio_neto real ✓
- `/charts/gestores-ranking?metric=ROE` → Luis Pérez 95.05% ✓
- `/charts/centros-distribution` → MADRID=58, PALMA=58, BARCELONA=36, MALAGA=35, BILBAO=29 ✓
- `/charts/productos-popularity` → Hipotecario=75, Fondos=72, Depósito=69 ✓

**Bug fix — Pivot no cambia a gráfico circular (sesión 11 — completado):**
- Root cause 1: `analyticsService.pivotChart()` leía `newConfig.chartType` (camelCase) pero backend devuelve `new_config.chart_type` (snake_case) → chartType ignorado, siempre usaba `currentChartConfig.chartType` como fallback
- Fix: `newConfig.chartType || newConfig.chart_type || currentChartConfig.chartType || 'horizontal_bar'`
- Root cause 2: `chart_prompts.py` no tenía ejemplos para cambio puro de tipo ("gráfico circular", "tarta", "donut", "vuelve a barras") → Azure OpenAI no devolvía `{"chart_type": "pie"}` de forma fiable
- Fix: añadidos 6 ejemplos de cambio puro de tipo en `CHART_PIVOT_SYSTEM_PROMPT`
- Commit: `fd328a3`

**Rediseño UI profesional (sesión 11 — completado):**
- `theme.js`: `borderRadius: 8` (era 6), espaciados como números (4/8/16/24/32/40), objeto `shadows` (card/elevated/overlay), transición `normal: '0.2s ease'`
- `index.css`: CSS custom properties para sistema de 8px grid (`--spacing-*`, `--radius-*`, `--shadow-*`, `--color-*`), estilos base de `.ant-card` (8px radius, shadow, hover), transiciones suaves, media query `min-width: 1280px`
- `GestorView`: eliminado wrapper Card doble alrededor de ConversationalPivot (causaba height mismatch y doble encabezado), ConversationalPivot recibe `height={520}` directamente; InteractiveCharts también `height={520}` para alineación
- `DireccionView`: ConversationalPivot movido de fila full-width inferior a panel lateral derecho sticky (`lg:8, position:sticky, top:88px`); columna izquierda (`lg:16`) tiene InteractiveCharts + DeviationAnalysis apilados; se eliminó layoutConfig.analysis separado
- Commit: `d3c2969`

**Paleta de colores Accenture (sesión 12 — completado):**
- `analyticsService.js`: `PRODUCT_COLORS`, `CLIENT_COLORS`, `DIRECTION_COLORS` → `ACCENTURE_CHART_PALETTE` (8 tonos de púrpura). Sin cyan (`#00B8F5`, `#0087C8`, `#00D4E8`) en ninguna serie de gráficos. `SEMAPHORE_COLORS` (Verde/Amarillo/Rojo funcional) intacto.
- `theme.js`: `chart.secondary`, `chart.accent1`, `chart.accent4` actualizados a púrpura. Commit: `9c44f31`

**Seguridad: ocultar precios reales en GestorView (sesión 12 — completado):**
- `GESTOR_PRESET_CHARTS`: eliminada entrada `'precios-comparison'` — gestores no pueden ver `PRECIO_POR_PRODUCTO_REAL` (solo CDG/Dirección). `DIRECTION_PRESET_CHARTS` sin cambios. Commit: `15f1366`

**Mejora de prompts (sesión 12 — completado):**
- `gestor_agent.py` `_build_system_prompt()`: reescrito con enfoque de negocio — copiloto que explica el "por qué" detrás de KPIs, sitúa al gestor vs centro, prepara argumentos para Business Review. Eliminadas referencias técnicas a cuentas contables y "Banca March".
- `cdg_agent.py`: "Banca March" → "CDG Intelligence" en `_generate_ai_insights`.
- `system_prompts.py` `FINANCIAL_ANALYST_SYSTEM_PROMPT`: reescrito con rol CDG orientado a detección de desvíos, rankings, preparación de Business Review y acceso a precio real. Commit: `cb7b222`

**UI polish (sesión 12 — completado):**
- `KPICards.jsx`: icono decorativo en esquina superior-derecha de cada card (`RiseOutlined` para ROE, `GiftOutlined` para bonus, `AreaChartOutlined` para clientes, `ContainerOutlined` para contratos, `EuroCircleOutlined` para ingresos).
- `InteractiveCharts.jsx`: loading state usa `<Skeleton active paragraph={{ rows: 6 }}>` en lugar de `<Spin>`; CSS `@keyframes ic-fade-in` inyectado para transición 0.2s entre tabs; card shadow actualizado a purple-tinted.
- `ChatInterface.jsx`: header `background: '#1A0033'`, texto blanco, badges y botones adaptados al fondo oscuro. Título simplificado a "Copiloto CDG".
- `ConversationalPivot.jsx`: misma cabecera oscura `#1A0033` para coherencia visual con ChatInterface. Commit: `618348e`

**Corrección paleta completa — gráfico dinámico (sesión 13 — completado):**
- `analyticsService.js` `PIVOTABLE_CONFIG.metrics`: todos los colores de métrica reemplazados con ACCENTURE_CHART_PALETTE (CONTRATOS `#22c55e`→`A100FF`, CLIENTES `#3b82f6`→`CC66FF`, ROE `#f59e0b`→`5500AA`, MARGEN_NETO `#ef4444`→`7B00CC`, INGRESOS `#10b981`→`A100FF`, INCENTIVOS `#8b5cf6`→`E600C8`)
- `transformPivotableData`: eliminado el enfoque de opacidad variable (`baseColor + hexOpacity`), reemplazado por cycling sobre `ACCENTURE_CHART_PALETTE`
- `generateMockPivotableChart`: fallback ahora usa paleta array en lugar de `'#22c55e'`
- `transformPriceComparison`: colores STD `rgba(25,124,99)` → `#94a3b8`; Real `rgba(20,70,50)` → `#7B00CC`
- Colores de segmentos `#52c41a`, `#13c2c2`, `#722ed1` → colores ACCENTURE_CHART_PALETTE. Commit: `1d8e8bf`

**Botón Volver en DireccionView (sesión 13 — completado):**
- Añadidos `useNavigate` + `HomeOutlined` + `handleBackToLanding` (navega a `/`)
- Botón "Volver" en el header (Space superior derecho) idéntico al de GestorView
- FloatButton `HomeOutlined` añadido al grupo de botones flotantes
- Commit: `930e54c`

**Animaciones framer-motion (sesión 13 — completado):**
- `KPICards.jsx`: cada card monta con fade + slide-up (y:20→0, opacity:0→1, 0.3s), staggered 0.1s por índice. Aplica en GestorView y DireccionView
- `InteractiveCharts.jsx`: tab "Gráfico Dinámico" hace fade-in (opacity:0→1, 0.4s) al aparecer por primera vez
- No se animaron: tablas, listas, componentes de re-render frecuente
- Commit: `f7d1925`

**Bug crítico: pivoteo DireccionView ignoraba rol CDG (sesión 14 — completado):**

**Síntoma:** "Enséñame los top 10 gestores con mejores ingresos" → "No se pudo interpretar tu solicitud"

**Root cause (cadena completa):**
1. `ConversationalPivot` llama `analyticsService.pivotChart(..., { gestorId, periodo, mode })`
2. `pivotChart()` llamaba `chartsAPI.pivot({ userId, message, ... })` — sin pasar `userRole`
3. `api.js` `charts.pivot` tiene `userRole = "GESTOR"` como default
4. Backend recibe `user_role = "GESTOR"` → aplica reglas de confidencialidad → fuerza `dimension: "periodo"` (override por permisos)
5. `getPivotableChartData("INGRESOS", "periodo", ...)` → `PIVOTABLE_CONFIG.metrics.INGRESOS` no tiene endpoint `periodo` → lanza error
6. Fallback local activa `parsePivotIntent("top 10 gestores...")` → no reconoce la frase → devuelve null
7. → "No se pudo interpretar tu solicitud"

**Fix:** En `pivotChart()`, derivar `userRole` de `options.mode`:
- `mode === 'direccion'` → `'CONTROL_GESTION'` (acceso completo)
- else → `'GESTOR'`
Pasar `userRole` a `chartsAPI.pivot()`. El backend devuelve `dimension: "gestor"` sin restricciones.

**Verificado con curl:** `user_role: CONTROL_GESTION` → `new_config: { metric: INGRESOS, dimension: gestor, chartType: horizontal_bar }`, `adjustments_made: []` ✓

**Commit:** `4c90fc3`

**Corrección de datos BD — auditoría y normalización (sesiones 15-16 — completado):**

**Sesión 15 — Auditoría read-only:**
- Identificados 4 problemas críticos: gastos centrales sep 12× oct, Bilbao gastos=0, Privada<Minorista, Javier Fernández margen -201%
- Identificados 2 menores: ratio fábrica 5.40 vs 5.667 (14 huérfanos), cuenta 66 excluida del filtro
- Backup creado antes de cualquier cambio: `BM_CONTABILIDAD_CDG_backup_20260315.db`

**Sesión 16 — Corrección ejecutada (7/7 checks OK):**
- **P1 (175 UPDATEs):** Gastos centrales sep escalados ×0.07534 → sep -€41,103 vs oct -€45,677 (ratio 0.90 ✓)
- **P2 (44 INSERTs):** Gastos directos 620001 añadidos a gestores 27/28/29 en sep+oct (ratio 15% ✓)
- **P4 (3 INSERTs):** Movimientos huérfanos de Javier Fernández oct-2025 restaurados → margen +€39,942 ✓
- **P5 (370 UPDATEs + 4 contratos nuevos):** Ingresos Banca Privada escalados → avg €37,656 = 2.01× Minorista; 4 contratos nuevos oct-2025 (1076 hip/G6, 2070 dep/G16, 2071 dep/G22, 3073 fondo/G5)
- **P6 (107 INSERTs+UPDATEs):** 125 pares 760024/760025 corregidos a ratio exacto 5.6667 ±0.02 ✓
- **P7 (335 UPDATEs):** Narrativa sep→oct ajustada → 96.7% gestores en rango [-15%,+20%]
- **Commit:** `25ba3c5`

**Valores de referencia actualizados (post-corrección):**
- Total contratos: 220 (antes 216) — 4 nuevos en oct-2025
- Total movimientos: ~2,900+ (antes 2,100)
- Gastos centrales sep: -€41,103 | oct: -€45,677
- Avg Privada oct: €37,656 (2.01× Minorista €19,697)
- Gestor 1 (Antonio Rodríguez, oct): ingresos ~€32,238, gastos directos ~€3,079 (referencia de validación)
- Modelo fábrica: ratio 5.6667 exacto en todos los 125 pares contrato/período
- **1 outlier narrativo aceptado:** G8 (Pablo Moreno, -57.4%) — actividad de fondos lumpy en sep, no corregible sin romper P6

**Correcciones de calidad adicionales (sesión 17 — completado):**

**C1 — `_get_total_contratos_finalistas()` hardcoded 216:**
- `basic_queries.py` y `gestor_queries.py`: ambas funciones usan `COUNT(mc.CONTRATO_ID)` dinámico — sin cambio necesario
- `cdg_agent.py` líneas 883+885: fallback hardcodeado `216` → `220` (commit `cd63e7e`)
- `system_prompts.py`: 4 ocurrencias "216 contratos" → "220 contratos" (mismo commit)

**C2 — Cuenta 66xxxx en filtro de gastos directos:**
- Verificado: 669001 tiene 43 movimientos, todos con CONTRATO_ID IS NULL → ya incluidos en redistribución central
- Filtro `SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69')` para gastos directos es CORRECTO — sin cambio
- Los nuevos 660001 y 690002 insertados en C4 también tienen CONTRATO_ID IS NULL → se redistribuyen correctamente

**C3 — Redistribución de contratos por gestor:**
- Análisis: distribución actual 4-12 contratos, avg 7.33, StdDev 2.39
- Conclusión: distribución aceptable, riesgo alto (tocar P6/P7), beneficio bajo → **no se ejecutó**

**C4 — ROE grupo consolidado (4 INSERTs + commit `97fcaf8`):**
- Antes: ROE 75% (implausible — gastos centrales insuficientes)
- Insertados IDs 2797-2800: 660001 Coste fondeo (-185k sep / -180k oct, CR0014) + 690002 Provisión riesgo (-46k sep / -45k oct, CR0029)
- Después: ROE oct **36.77%** (target ~37%) ✓
- Margen por segmento oct (con gastos directos): Privada 91.8% > Minorista 85.7% > Empresas 80.9% > Personal 72.4% > Fondos 66.0% ✓ (todos positivos)

**Valores de referencia (post-sesión-17):**
- ROE grupo oct-2025: **36.77%** (ingresos €592,464 / gastos -€374,623 / margen €217,841)
- Contratos: avg 7.33/gestor, StdDev 2.39, rango [4, 12], total 220
- Margen por segmento: Privada lidera (91.8%), todos positivos

### ⏭️ Próximo paso exacto al retomar

**Siguiente: prueba visual ambos dashboards con datos corregidos**
- Verificar que KPIs del gestor reflejan los nuevos valores (ingresos, márgenes)
- Verificar que comparativa sep→oct en gráficos muestra variaciones en rango [-15%,+20%]
- Verificar ranking CDG: Privada gestores deben liderar (avg €37k vs Minorista €19k)
- "Enséñame los top 10 gestores con mejores ingresos" → debe mostrar barras púrpura con datos reales
- "Cambia a ingresos por centro" → debe cambiar la dimensión
- "Ponlo en gráfico circular" → debe cambiar el tipo

**Rebrand a identidad Accenture (sesión 11 — completado):**
- Producto renombrado: "Banca March CDG" → **"CDG Intelligence"** (genérico, adaptable a cualquier banco cliente)
- `theme.js`: paleta completa reemplazada por identidad Accenture — primary `#A100FF`, primaryLight `#CC66FF`, primaryDark `#7B00CC`, accent `#00B8F5`, headerBg `#1A0033`, fondo `#F8F5FF`
- `analyticsService.js`: colores de gráficos `PRODUCT_COLORS/CLIENT_COLORS/DIRECTION_COLORS` → paleta 5 colores Accenture
- `TopBar.jsx`: gradiente `#1A0033→#A100FF`, logo tipográfico "> CDG Intelligence" en blanco, botones outline-blanco sobre fondo oscuro
- `LandingPage.jsx`: eliminado `BancaMarchLogo.png`, reemplazado por texto "> CDG Intelligence / POWERED BY ACCENTURE"; overlay del fondo actualizado a púrpura
- `KPICards.jsx`: borde superior 3px `#A100FF`, variación positiva en púrpura, shadow purple-tinted
- `ConversationalPivot.jsx`: burbuja usuario `#A100FF` fondo blanco, burbuja agente `#F3E8FF` con borde izquierdo `#A100FF`
- `public/index.html`: `<title>CDG Intelligence</title>`, meta description actualizada
- `backend/src/prompts/*.py`: 50+ ocurrencias de "Banca March" → "Agente CDG"
- Commit: `b0baa97`

### ⚠️ Pendiente de decisión
- `MAESTRO_CONTRATOS_BACKUP_20250922_002703` — tabla basura en la BD, pendiente de `DROP TABLE`
- `backend/src/utils/initial_agent.py` — usa `openai` SDK directo en lugar de LangChain, pendiente de reescribir (no bloquea la POC)
- `GET /basic/precios-std` y `GET /prices/comparison` — devuelven 404; no se usan en ningún flujo activo
- `analyticsService.js:2857` — `.replace('Fondo Banca March', 'Fondos CDG')` mantiene el string del nombre real en BD (no es UI-visible, no se toca)
- `BM_CONTABILIDAD_CDG_backup_20260315.db` — backup de la BD pre-corrección, mantener hasta confirmar que el sistema arranca correctamente
- ~~`basic_queries.py` línea con `_get_total_contratos_finalistas()`: el denominador hardcodeado era 216~~ → resuelto en sesión 17 (C1)