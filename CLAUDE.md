# CLAUDE.md — Agente Control de Gestión (CDG)
> Contexto maestro operativo. Léelo completo antes de escribir código. Historial en SESSIONS.md.

---

## ⚠️ ADVERTENCIAS CRÍTICAS

### 1. LLM: Azure OpenAI — NO Anthropic API
Usa **Azure OpenAI** con credenciales del `.env`. No uses `anthropic` SDK ni `claude` como modelo.

### 2. El código existente puede contener errores
**No reutilices ningún archivo sin validarlo.** Ante cualquier duda: reescribe desde cero.

---

## 1. VISIÓN GENERAL

**Agente CDG** — copiloto LLM para análisis financiero, desviaciones, incentivos y Business Reviews.

| Perfil | Acceso |
|---|---|
| **Gestor Comercial** | Solo su cartera — `WHERE GESTOR_ID = {id}` |
| **Control de Gestión / Dirección** | Sin restricciones |

---

## 2. STACK

**Backend:** Python 3.11+, FastAPI, SQLite, LangChain/LangGraph, Azure OpenAI, Pandas.
**Frontend:** React, Ant Design, Recharts, D3.js.

---

## 3. ESTRUCTURA

```
backend/src/
  database/  BM_CONTABILIDAD_CDG.db, db_connection.py
  agents/    gestor_agent.py, cdg_agent.py, chat_agent.py
  tools/     kpi_calculator.py, chart_generator.py, report_generator.py
  queries/   basic_queries.py, gestor_queries.py, comparative_queries.py, deviation_queries.py
  prompts/   system_prompts.py, user_prompts.py, chart_prompts.py
  utils/     auth.py
backend/  main.py, config.py
frontend/src/
  components/Dashboard/  KPICards.jsx, InteractiveCharts.jsx, FabricaModelSection.jsx,
                         DrillDownView.jsx, ChatInterface.jsx
  pages/    LandingPage.jsx, GestorView.jsx, DireccionView.jsx
  services/ api.js, chatService.js, analyticsService.js
```

---

## 4. BASE DE DATOS — `BM_CONTABILIDAD_CDG.db`

SQLite, 14 tablas, UTF-8. Períodos: **sep-2025** y **oct-2025**.

**Tablas maestras:**
- `MAESTRO_CENTROS`: Finalistas (1-5): MADRID, PALMA, BARCELONA, MALAGA, BILBAO. Soporte (6-8).
- `MAESTRO_GESTORES`: 30 gestores. C1 (1-8), C2 (9-16), C3 (17-21), C4 (22-26), C5 (27-30).
- `MAESTRO_CONTRATOS`: **220 contratos** (216 sep + 4 nuevos oct-2025).
- `MAESTRO_PRODUCTOS`: `100100100100` Hip (100% banco) | `400200100100` Dep (100% banco) | `600100300300` Fondo (85% gestora/15% banco).
- `MAESTRO_SEGMENTOS`: N10101=Minorista | N10102=Privada | N10103=Empresas | N10104=Personal | N20301=Fondos

**Tablas transaccionales:**
- `MOVIMIENTOS_CONTRATOS`: ~2,900+ registros. CONTRATO_ID NULL = gastos centrales. Ingresos: `76xxxx`. Gastos: `62/64/68/69xxxx`. Fábrica: `760024` banco / `760025` gestora.
- `GASTOS_CENTRO`: Sep €455k | Oct €222k. ⚠️ Gastos oct reales en MOVIMIENTOS (CONTRATO_ID IS NULL).
- `PRECIO_POR_PRODUCTO_REAL`: Solo CDG. `PRECIO_POR_PRODUCTO_STD`: Todos.

**P&L:** CR0001→CR0007 MARGEN FINANCIERO → CR0012 MARGEN BRUTO → CR0018 MARGEN EXPLOTACIÓN → CR0030 MARGEN APORTADO.

---

## 5. MODELO TEMPORAL — MoM + Cartera Acumulada

Ingresos/gastos/ROE = **mes seleccionado (MoM)**. Contratos = **acumulados históricos**.

| Período | Filtro ingresos/gastos | Contratos |
|---|---|---|
| sep-2025 | `strftime('%Y-%m', FECHA) = '2025-09'` | **216** |
| oct-2025 | `strftime('%Y-%m', FECHA) = '2025-10'` | **220** |

**Fórmula contratos activos:** `COUNT(DISTINCT CASE WHEN co.FECHA_ALTA <= date(? || '-01', '+1 month', '-1 day') THEN co.CONTRATO_ID END)`

**Ref (post-S24):** Sep €599,759 | ROE 35.94% | 216 contratos. Oct €624,000 | ROE 39.96% | 220 contratos (+4.04%). Fábrica oct: cedido €123,278 (84.01%).

---

## 6. REGLAS DE NEGOCIO

**Redistribución gastos centrales:** `Gasto_i = Gasto_Central × (Contratos_i / 220)`
**Semáforo:** 🟢 <5% | 🟡 5-15% | 🔴 >15%
**Modelo Fábrica:** Gestora 85% (`760025`) / Banco 15% (`760024`).

**Filtros de gastos:**
- **Directos** (CONTRATO_ID IS NOT NULL): `SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69')`
- **Centrales** (CONTRATO_ID IS NULL): `SUBSTR(CUENTA_ID,1,2) IN ('62','64','66','68','69')` — incluye '66' para fondeo (660001, -€180k/oct)

---

## 7. CONTROL DE ACCESO

**Gestor:** ✅ Su cartera, KPIs propios, precios STD. ❌ Otros gestores, precios REAL.
**CDG/Dirección:** ✅ Acceso completo.

---

## 8. ENDPOINTS FASTAPI

```
POST /chat/gestor                          POST /chat/message (CDG)
GET  /kpis/gestor/{id}/roe                 GET  /kpis/consolidado
GET  /analytics/gestor/{id}/metricas-completas
GET  /charts/gestores-ranking?metric=CONTRATOS|CLIENTES|INGRESOS|MARGEN_NETO|ROE
GET  /charts/centros-distribution          GET  /charts/productos-popularity
POST /charts/pivot
GET  /deviations/pricing                   GET  /incentives/gestor/{id}/detalle
GET  /basic/productos/by-gestor/{id}       GET  /analytics/fabrica
```

---

## 9. SYSTEM PROMPTS

**Gestor:** `Eres copiloto de {nombre_gestor}, centro {centro}. Solo accedes a gestor ID: {gestor_id}. Español bancario profesional.`
**CDG:** `Eres agente CDG Intelligence con acceso completo. Análisis profundos, insights estratégicos. Español técnico.`

---

## 10. CONSULTAS SQL

- **Ingresos:** `SUM(IMPORTE) WHERE CUENTA_ID LIKE '76%'`
- **Gastos directos:** `ABS(SUM(IMPORTE)) WHERE SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69') AND CONTRATO_ID IS NOT NULL`
- **Gastos redistribuidos:** `gastos_centrales × (n_contratos_gestor / 220)`
- **Gastos centrales:** `ABS(SUM(IMPORTE)) WHERE CONTRATO_ID IS NULL AND SUBSTR(CUENTA_ID,1,2) IN ('62','64','66','68','69')`

---

## 11. VARIABLES DE ENTORNO

```env
AZURE_OPENAI_API_KEY=AZURE_OPENAI_API_KEY_REDACTED
AZURE_OPENAI_ENDPOINT=https://TU_RECURSO.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_ID=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
DATABASE_PATH=./backend/src/database/BM_CONTABILIDAD_CDG.db
```

---

## 12. ESTADO + INICIO

Ver historial completo en **SESSIONS.md**.

**Para iniciar:**
```bash
cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8009
cd frontend && npm start
# frontend/.env: REACT_APP_API_BASE_URL=http://localhost:8009
```

**Fase actual:** Fase 6 completada. S25 completada. Ver SESSIONS.md para próximos pasos y pendientes.
