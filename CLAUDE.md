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
AZURE_OPENAI_DEPLOYMENT_ID=gpt-5.4
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
