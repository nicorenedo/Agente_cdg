# CDG Intelligence v1

Copiloto de Control de Gestión bancario basado en IA agéntica.
Sistema conversacional para Controllers y Gestores comerciales.

## ¿Qué es esto?

- **Panel de Dirección:** visión global del banco (márgenes, gestores, centros, productos)
- **Panel de Gestor:** visión personal del gestor comercial (su cartera, ROE, incentivos)
- **Módulo de Proyecciones:** forecasting Prophet + simulación what-if

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`docs/RECONSTRUCTION_AUDIT.md`](docs/RECONSTRUCTION_AUDIT.md) | Audit de arquitectura v1 — problemas identificados |
| [`docs/ARCHITECTURE_V2.md`](docs/ARCHITECTURE_V2.md) | Arquitectura objetivo v2 |
| [`docs/RECONSTRUCTION_PLAN.md`](docs/RECONSTRUCTION_PLAN.md) | Plan de reconstrucción desde v1 |
| [`SESSIONS.md`](SESSIONS.md) | Historial completo de sesiones S1-S89 |

## Setup

```bash
# 1. Configurar entorno
cp .env.example .env
# Editar .env con tus credenciales de Azure OpenAI

# 2. Backend
cd backend
pip install -r requirements.txt
python main.py

# 3. Frontend (en otra terminal)
cd frontend
npm install
npm start
```

El frontend levanta en `http://localhost:3000` y consume la API en `http://localhost:8000`.

## Stack

| Capa | Tecnología |
|------|-----------|
| LLM | Azure OpenAI (gpt-4o) |
| Backend | FastAPI + Python 3.11+ |
| Agentes | LangChain + LangGraph |
| Forecast | Prophet |
| Frontend | React 18 + Ant Design 5 |
| Base de datos | SQLite — 14 tablas, ~19.000 movimientos |

## Estructura

```
backend/
  main.py, config.py
  src/
    agents/     gestor_agent.py, cdg_agent.py, chat_agent.py
    database/   BM_CONTABILIDAD_CDG.db, db_connection.py
    queries/    basic_queries.py, comparative_queries.py, ...
    tools/      kpi_calculator.py, chart_generator.py, ...
    prompts/    system_prompts.py, user_prompts.py
  data/seed/    CSVs semilla de la base de datos
frontend/
  src/
    components/ KPICards, InteractiveCharts, ChatInterface, ...
    pages/      LandingPage, GestorView, DireccionView
docs/
  RECONSTRUCTION_AUDIT.md
  ARCHITECTURE_V2.md
  RECONSTRUCTION_PLAN.md
  data_generation/  scripts de generación de datos sintéticos
```

## Estado

Versión 1 — snapshot histórico S1-S89.
Ver [`SESSIONS.md`](SESSIONS.md) para el historial completo de 89 sesiones de desarrollo.
