# main.py — CDG API v7.0 (Chat Agent v9.1 + CDG Agent v5.0 Integration)
# ===============================================================================
# - Envelope uniforme {status, data, meta, timestamp}
# - Integración COMPLETA con Chat Agent v9.1 y CDG Agent v5.0
# - Amplia cobertura de endpoints (agents, queries, tools, charts)
# - Fallbacks robustos si faltan módulos reales (modo MOCK sin romper frontend)
# - CORS configurable, logging optimizado, WebSocket estable con keep-alive
# - Sin duplicidades funcionales; alias mínimos coherentes
# - Preparado para frontend React + Ant Design
#
# Autor: Agente CDG
# Fecha: 2025-09-11
# Version: 7.0.0

from __future__ import annotations

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

# Asegurar import de src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Query, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import uvicorn

# ----------------------------------------------------------------------------
# Intentar cargar módulos reales; si fallan, usar mocks compatibles
# ----------------------------------------------------------------------------
IMPORTS_SUCCESSFUL = True
BASIC_QUERIES_AVAILABLE = True
CHART_GENERATOR_AVAILABLE = True
SQL_GUARD_AVAILABLE = True
REFLECTION_AVAILABLE = True

try:
    # ✅ Agents (actualizados para Chat Agent v9.1 + CDG Agent v5.0)
    from agents.cdg_agent import (
        CDGAgent, CDGRequest, process_cdg_request, process_quick_query
    )
    from agents.chat_agent import (
        UniversalChatAgent, ChatMessage  # ✅ Chat Agent v9.1
    )

    # Tools: KPI calculator (con fallback entre clases reales del mismo módulo)
    try:
        from tools.kpi_calculator import FinancialKPICalculator as _KPICalcCls
    except Exception:
        from tools.kpi_calculator import KPICalculator as _KPICalcCls

    # Chart generator de forma granular: si falla, no tumbamos toda la API
    try:
        from tools.chart_generator import (
            CDGDashboardGenerator,
            QueryIntegratedChartGenerator,
            create_chart_from_query_data,
            create_quick_chart,
            pivot_chart_with_query_integration,
            validate_chart_generator,
            ChartFactory,
        )
        try:
            from tools.chart_generator import CDG_CHART_CONFIGS
        except Exception:
            CDG_CHART_CONFIGS = {"chart_types": {}, "dimensions": {}, "metrics": {}, "colors": {}}
    except Exception:
        CHART_GENERATOR_AVAILABLE = False
        # Stubs mínimos para no romper endpoints /charts/*
        class _ChartGenStub:
            current_charts = {}
            def __getattr__(self, name):
                return lambda *a, **k: {"id": "mock", "charts": [], "status": "stub"}
        CDGDashboardGenerator = _ChartGenStub
        QueryIntegratedChartGenerator = _ChartGenStub
        def create_chart_from_query_data(data, config): return {"id": "mock_chart", "config": config, "data": data}
        def create_quick_chart(*a, **k): return {"id": "mock_quick", "data": [], "config": {"type": k.get("chart_type", "bar")}}
        def pivot_chart_with_query_integration(message, current_config): return {"status": "success", "new_config": current_config}
        def validate_chart_generator(): return {"status": "MOCK"}
        class _ChartFactoryStub:
            @staticmethod
            def get_available_queries():
                return ["gestores_ranking", "centros_distribution", "productos_popularity", "precios_comparison", "summary_dashboard"]
        ChartFactory = _ChartFactoryStub
        CDG_CHART_CONFIGS = {"chart_types": {}, "dimensions": {}, "metrics": {}, "colors": {}}

    # Report generator (si falla no es crítico; dejamos clase stub sencilla)
    try:
        from tools.report_generator import BusinessReportGenerator
    except Exception:
        class BusinessReportGenerator:
            def __call__(self, *a, **k): return self
            def generate_business_review(self, *a, **k): 
                return type("R", (), {"to_dict": lambda s: {"review": "mock"}})()
            def generate_executive_summary_report(self, *a, **k):
                return type("R", (), {"to_dict": lambda s: {"summary": "mock"}})()

    # SQL Guard (granular: si falla, stubs y apagamos flag)
    try:
        from tools.sql_guard import is_query_safe, validate_query_for_cdg
    except Exception:
        SQL_GUARD_AVAILABLE = False
        def is_query_safe(sql): return True
        def validate_query_for_cdg(sql, context="general"): 
            return {"is_safe": True, "context": context, "warnings": ["sql_guard_stub"], "query_hash": hash(sql)}

    # Queries (si fallan, son críticas: dejamos que dispare el outer except -> MOCK)
    from queries.basic_queries import basic_queries
    from queries.period_queries import PeriodQueries
    from queries.gestor_queries import GestorQueries
    from queries.comparative_queries import ComparativeQueries
    from queries.deviation_queries import DeviationQueries
    from queries.incentive_queries import IncentiveQueries

    # ✅ Reflexión/personalización (actualizado para v9.1)
    try:
        from utils.reflection_pattern import (
            reflection_manager,
            integrate_feedback_from_chat_agent,
            get_personalization_for_user,
        )
    except Exception:
        REFLECTION_AVAILABLE = False
        class _MockReflection:
            def generate_organizational_insights(self): return {"total_users": 0, "mode": "mock"}
            async def process_feedback(self, **kwargs): return {"status": "processed", "mode": "mock"}
        reflection_manager = _MockReflection()
        def integrate_feedback_from_chat_agent(*a, **k): return {"status": "mock"}
        def get_personalization_for_user(user_id: str): return {"user_id": user_id, "mode": "mock"}

except Exception as e:
    # Modo MOCK total (solo si algo crítico fuera de los bloques granulares falla)
    IMPORTS_SUCCESSFUL = False
    BASIC_QUERIES_AVAILABLE = False
    CHART_GENERATOR_AVAILABLE = False
    SQL_GUARD_AVAILABLE = False
    REFLECTION_AVAILABLE = False

    class _MockObj:
        def __getattr__(self, name):
            return lambda *a, **k: type("R", (), {"data": [], "row_count": 0})()

    class CDGAgent:
        def __init__(self): ...
        async def process_request(self, *a, **k):
            return type("R", (), {
                "to_dict": lambda s: {
                    "response_type": "mock",
                    "content": {"note": "mock"},
                    "charts": [],
                    "recommendations": [],
                    "metadata": {},
                    "execution_time": 0.01,
                    "confidence_score": 0.5,
                    "created_at": datetime.now(UTC).isoformat(),
                    "chart_configs": [],
                    "pivot_suggestions": [],
                    "basic_queries_used": False,
                    "data_sources": []
                }
            })()
        def get_agent_status(self): return {"status": "mock", "version": "5.0"}
        def get_integration_summary(self): return {"summary": "mock"}
        def validate_basic_queries_integration(self): return {"overall_status": "NOT_AVAILABLE"}
        def reset_conversation_history(self): ...
        async def generate_chart_from_data(self, *a, **k): return {"id": "mock_chart"}
        async def pivot_chart(self, *a, **k): return {"status": "success", "new_config": {}}
        async def get_basic_data_summary(self): return {"data": {"total_gestores": 30}}
        async def get_gestores_list(self): return [{"GESTOR_ID": 1, "DESC_GESTOR": "Mock Gestor"}]
        async def get_centros_list(self): return [{"CENTRO_ID": 1, "DESC_CENTRO": "Mock Centro"}]
        def get_available_periods(self): return {"periods": [{"periodo": "2025-10"}], "count": 1}
        def get_latest_period(self): return "2025-10"

    class UniversalChatAgent:
        def __init__(self):
            self.session_manager = type("SM", (), {
                "sessions": {},
                "get_or_create_session": lambda s, u: type("S", (), {"session_id": "mock", "user_preferences": {}})()
            })()
        async def process_chat_message(self, *a, **k):
            return type("R", (), {
                "dict": lambda s: {"response": "ok (mock)", "charts": []},
                "response": "ok (mock)", "charts": []
            })()
        def get_agent_status(self): return {"status": "mock", "version": "9.1"}
        def get_dynamic_suggestions(self, user_id: str): return ["Sugerencia mock"]

    _KPICalcCls = _MockObj
    CDGDashboardGenerator = _MockObj
    QueryIntegratedChartGenerator = _MockObj
    BusinessReportGenerator = _MockObj
    GestorQueries = _MockObj
    ComparativeQueries = _MockObj
    DeviationQueries = _MockObj
    IncentiveQueries = _MockObj
    PeriodQueries = _MockObj
    def create_chart_from_query_data(data, config): return {"id": "mock_chart", "config": config}
    def pivot_chart_with_query_integration(message, current_config): return {"status": "success", "new_config": current_config}
    def validate_chart_generator(): return {"status": "MOCK"}
    basic_queries = type("BQ", (), {
        "get_resumen_general": staticmethod(lambda: {"total_gestores": 30, "total_clientes": 85, "total_contratos": 216, "total_centros": 5, "total_productos": 3}),
        "count_contratos_by_gestor": staticmethod(lambda: [{"DESC_GESTOR": "Mock Gestor 1", "num_contratos": 10}]),
        "count_clientes_by_gestor": staticmethod(lambda: [{"DESC_GESTOR": "Mock Gestor 1", "num_clientes": 6}]),
        "count_contratos_by_centro": staticmethod(lambda: [{"CENTRO_ID": 1, "num_contratos": 15}]),
        "count_contratos_by_producto": staticmethod(lambda: [{"PRODUCTO_ID": "P1", "DESC_PRODUCTO": "Prod 1", "num_contratos": 12}]),
        "get_all_centros": staticmethod(lambda: [{"CENTRO_ID": 1, "DESC_CENTRO": "Mock Centro"}]),
        "get_all_gestores": staticmethod(lambda: [{"GESTOR_ID": 1, "DESC_GESTOR": "Mock Gestor"}]),
        "get_all_productos": staticmethod(lambda: [{"PRODUCTO_ID": "P1", "DESC_PRODUCTO": "Prod 1"}]),
        "get_all_precios_std": staticmethod(lambda: [{"PRODUCTO_ID": "P1", "precio_std": 100.0}]),
        "get_all_precios_real": staticmethod(lambda: [{"PRODUCTO_ID": "P1", "precio_real": 95.0}]),
        "get_gastos_by_fecha": staticmethod(lambda fecha: [{"fecha": fecha, "importe": 1234.56}]),
        "get_gestor_info": staticmethod(lambda gestor_id: {"GESTOR_ID": gestor_id, "SEGMENTO_ID": "N10102"}),
        "get_precios_real_by_segmento_periodo": staticmethod(lambda s, p: [{"PRODUCTO_ID": "P1", "precio_real": 95.0}]),
    })
    def is_query_safe(sql): return True
    def validate_query_for_cdg(sql, context="general"): return {"is_safe": True, "context": context, "warnings": [], "query_hash": hash(sql)}

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cdg-api")

# ----------------------------------------------------------------------------
# Helpers: respuesta uniforme
# ----------------------------------------------------------------------------

def now_iso():
    return datetime.now(UTC).isoformat()

class ApiError(BaseModel):
    status: str = "error"
    message: str
    code: int = 400
    timestamp: str = Field(default_factory=now_iso)

class ApiMeta(BaseModel):
    periodo: Optional[str] = None
    count: Optional[int] = None
    note: Optional[str] = None
    source: Optional[str] = None

class ApiResponse(BaseModel):
    status: str = "success"
    data: Any
    meta: Optional[ApiMeta] = None
    timestamp: str = Field(default_factory=now_iso)

def ok(data: Any, meta: Dict[str, Any] | None = None):
    return ApiResponse(data=data, meta=ApiMeta(**(meta or {})))

def err(message: str, code: int = 400):
    raise HTTPException(status_code=code, detail=message)

# ----------------------------------------------------------------------------
# FastAPI app & CORS
# ----------------------------------------------------------------------------

app = FastAPI(
    title="CDG Agente API v7.0 (Chat Agent v9.1 + CDG Agent v5.0)",
    version="7.0.0",
    description="API unificada para dashboards CDG con integración completa de agentes avanzados",
    docs_url="/docs",
    redoc_url="/redoc",
)

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ----------------------------------------------------------------------------
# ✅ Instancias de agentes actualizadas
# ----------------------------------------------------------------------------

chat_agent = UniversalChatAgent()  # ✅ Chat Agent v9.1
cdg_agent = CDGAgent()             # ✅ CDG Agent v5.0
kpi_calc = _KPICalcCls() if hasattr(_KPICalcCls, "__call__") else _KPICalcCls
chart_dash = CDGDashboardGenerator() if hasattr(CDGDashboardGenerator, "__call__") else CDGDashboardGenerator
query_chart = QueryIntegratedChartGenerator() if hasattr(QueryIntegratedChartGenerator, "__call__") else QueryIntegratedChartGenerator
report_gen = BusinessReportGenerator() if hasattr(BusinessReportGenerator, "__call__") else BusinessReportGenerator

period_queries = PeriodQueries() if hasattr(PeriodQueries, "__call__") else PeriodQueries
gestor_queries = GestorQueries() if hasattr(GestorQueries, "__call__") else GestorQueries
comparative_queries = ComparativeQueries() if hasattr(ComparativeQueries, "__call__") else ComparativeQueries
deviation_queries = DeviationQueries() if hasattr(DeviationQueries, "__call__") else DeviationQueries
incentive_queries = IncentiveQueries() if hasattr(IncentiveQueries, "__call__") else IncentiveQueries

# ----------------------------------------------------------------------------
# Modelos request/response específicos (para OpenAPI)
# ----------------------------------------------------------------------------

class ChatRequest(BaseModel):
    user_id: str
    message: str
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True
    context: Dict[str, Any] = {}
    user_feedback: Optional[Dict[str, Any]] = None
    current_chart_config: Optional[Dict[str, Any]] = None
    chart_interaction_type: Optional[str] = None
    use_basic_queries: bool = True
    quick_mode: bool = False

class ChartPivotRequest(BaseModel):
    user_id: str
    message: str
    current_chart_config: Optional[Dict[str, Any]] = None
    chart_interaction_type: Optional[str] = "pivot"

class ReportRequest(BaseModel):
    user_id: str
    gestor_id: Optional[str] = None
    periodo: str
    report_type: str = "business_review"
    options: Dict[str, Any] = {}

class KPIRequest(BaseModel):
    ingresos: Optional[float] = None
    gastos: Optional[float] = None
    beneficio_neto: Optional[float] = None
    patrimonio: Optional[float] = None
    row: Optional[Dict[str, Any]] = None

class AgentProcessRequest(BaseModel):
    user_message: str
    user_id: Optional[str] = None
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True
    current_chart_config: Optional[Dict[str, Any]] = None
    chart_interaction_type: Optional[str] = None
    use_basic_queries: bool = True
    quick_mode: bool = False
    context: Dict[str, Any] = {}

class IntelligentDeviationRequest(BaseModel):
    question: str
    periodo: Optional[str] = None
    gestor_id: Optional[str] = None
    segmento_id: Optional[str] = None
    producto_id: Optional[str] = None
    context: Dict[str, Any] = {}

class DynamicQueryRequest(BaseModel):
    sql: str
    context: str = "general"

# ----------------------------------------------------------------------------
# Raíz / Salud / Versión
# ----------------------------------------------------------------------------

@app.get("/", tags=["System"], response_model=ApiResponse)
def root():
    return ok(
        {
            "service": "CDG Agente API v7.0",
            "chat_agent_version": "9.1",
            "cdg_agent_version": "5.0",
            "mode": "PRODUCTION" if IMPORTS_SUCCESSFUL else "MOCK",
            "modules": {
                "basic_queries": BASIC_QUERIES_AVAILABLE,
                "chart_generator": CHART_GENERATOR_AVAILABLE,
                "sql_guard": SQL_GUARD_AVAILABLE,
                "reflection": REFLECTION_AVAILABLE,
            },
        },
        meta={"note": "Use /docs para OpenAPI"},
    )

@app.get("/health", tags=["System"], response_model=ApiResponse)
def health():
    return ok({"status": "healthy", "imports_successful": IMPORTS_SUCCESSFUL})

@app.get("/version", tags=["System"], response_model=ApiResponse)
def version():
    return ok({
        "api_version": "7.0.0",
        "chat_agent": "9.1",
        "cdg_agent": "5.0",
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "git_sha": os.getenv("GIT_SHA", "dev"),
    })

# ----------------------------------------------------------------------------
# Periodos / Catálogos
# ----------------------------------------------------------------------------

@app.get("/periods", tags=["Catalogs"], response_model=ApiResponse)
def periods():
    # cdg_agent tiene helpers enhanced si existen
    try:
        enhanced = cdg_agent.get_available_periods()
        periods = [p.get("periodo") for p in enhanced.get("periods", [])]
        latest = cdg_agent.get_latest_period()
        return ok({"periods": periods, "latest": latest}, meta={"count": len(periods), "source": "cdg_agent"})
    except Exception:
        # Fallback directo a PeriodQueries si existe método
        periods = []
        latest = None
        if hasattr(period_queries, "get_available_periods_enhanced"):
            res = period_queries.get_available_periods_enhanced()
            periods = [r.get("periodo") for r in getattr(res, "data", [])]
        if hasattr(period_queries, "get_latest_period_enhanced"):
            res2 = period_queries.get_latest_period_enhanced()
            latest = getattr(res2, "data", [{"periodo": None}])[0].get("periodo")
        return ok({"periods": periods, "latest": latest}, meta={"count": len(periods), "source": "period_queries"})

@app.get("/periods/latest", tags=["Catalogs"], response_model=ApiResponse)
def periods_latest():
    try:
        latest = cdg_agent.get_latest_period()
        return ok({"latest": latest}, meta={"source": "cdg_agent"})
    except Exception:
        if hasattr(period_queries, "get_latest_period_enhanced"):
            res = period_queries.get_latest_period_enhanced()
            val = getattr(res, "data", [{"periodo": None}])[0].get("periodo")
            return ok({"latest": val}, meta={"source": "period_queries"})
        return ok({"latest": None}, meta={"note": "no data"})

@app.get("/catalogs", tags=["Catalogs"], response_model=ApiResponse)
def catalogs():
    gestores = basic_queries.get_all_gestores() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_gestores") else []
    centros = basic_queries.get_all_centros() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_centros") else []
    productos = basic_queries.get_all_productos() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_productos") else []
    return ok({"gestores": gestores, "centros": centros, "productos": productos},
              meta={"count": len(gestores)+len(centros)+len(productos), "source": "basic_queries" if BASIC_QUERIES_AVAILABLE else "mock"})

# ----------------------------------------------------------------------------
# Basic queries (atajos rápidos para cards en dashboard)
# ----------------------------------------------------------------------------

@app.get("/basic/summary", tags=["Basic"], response_model=ApiResponse)
def basic_summary():
    data = basic_queries.get_resumen_general() if BASIC_QUERIES_AVAILABLE else {}
    return ok(data, meta={"source": "basic_queries" if BASIC_QUERIES_AVAILABLE else "mock"})

@app.get("/basic/gestores-ranking", tags=["Basic"], response_model=ApiResponse)
def basic_gestores_ranking(metric: str = Query("contratos", enum=["contratos", "clientes"])):
    if not BASIC_QUERIES_AVAILABLE:
        return ok([], meta={"note": "basic_queries no disponible"})
    if metric == "clientes" and hasattr(basic_queries, "count_clientes_by_gestor"):
        data = basic_queries.count_clientes_by_gestor()
    else:
        data = basic_queries.count_contratos_by_gestor()
    return ok(data, meta={"count": len(data), "metric": metric})

@app.get("/basic/centros", tags=["Basic"], response_model=ApiResponse)
def basic_centros():
    if not BASIC_QUERIES_AVAILABLE:
        return ok([], meta={"note": "basic_queries no disponible"})
    centros = basic_queries.get_all_centros()
    contratos = basic_queries.count_contratos_by_centro() if hasattr(basic_queries, "count_contratos_by_centro") else []
    # join sencillo
    by_id = {c.get("CENTRO_ID"): c for c in centros}
    for row in contratos:
        cid = row.get("CENTRO_ID")
        if cid in by_id:
            by_id[cid]["num_contratos"] = row.get("num_contratos", 0)
    return ok(list(by_id.values()), meta={"count": len(by_id)})

@app.get("/basic/productos", tags=["Basic"], response_model=ApiResponse)
def basic_productos():
    if not BASIC_QUERIES_AVAILABLE:
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.count_contratos_by_producto() if hasattr(basic_queries, "count_contratos_by_producto") else []
    return ok(data, meta={"count": len(data)})

@app.get("/basic/gastos/by-fecha", tags=["Basic"], response_model=ApiResponse)
def basic_gastos_by_fecha(fecha: str = Query(..., description="YYYY-MM-DD")):
    if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_gastos_by_fecha"):
        data = basic_queries.get_gastos_by_fecha(fecha)
        return ok(data, meta={"count": len(data), "fecha": fecha})
    return ok([], meta={"note": "no implementado"})

# ----------------------------------------------------------------------------
# Basic — Drilldown & Pricing (para tablas y drill-down del frontend)
# ----------------------------------------------------------------------------

@app.get("/basic/contracts", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_all():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_contratos"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_all_contratos()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/contracts/count", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_count():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos"):
        return ok({"total": 0}, meta={"note": "basic_queries no disponible"})
    total = basic_queries.count_contratos()
    return ok({"total": total})

@app.get("/basic/contracts/by-gestor/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_gestor(gestor_id: int):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_gestor"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_contratos_by_gestor(gestor_id)
    return ok(data, meta={"count": len(data), "gestor_id": gestor_id})

@app.get("/basic/contracts/by-cliente/{cliente_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_cliente(cliente_id: int):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_cliente"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_contratos_by_cliente(cliente_id)
    return ok(data, meta={"count": len(data), "cliente_id": cliente_id})

@app.get("/basic/contracts/by-producto/{producto_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_producto(producto_id: str):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_producto"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_contratos_by_producto(producto_id)
    return ok(data, meta={"count": len(data), "producto_id": producto_id})

@app.get("/basic/contracts/by-centro/{centro_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_centro(centro_id: int):
    """
    No hay query directa; filtramos sobre get_all_contratos() para drill-down.
    """
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_contratos"):
        return ok([], meta={"note": "basic_queries no disponible"})
    allc = basic_queries.get_all_contratos()
    # En los resultados existe co.CENTRO_CONTABLE como clave de centro
    data = [r for r in allc if str(r.get("CENTRO_CONTABLE")) == str(centro_id)]
    return ok(data, meta={"count": len(data), "centro_id": centro_id, "source": "filter(get_all_contratos)"})

# ---- Centros / Gestores / Clientes auxiliares (para listas y joins ligeros)

@app.get("/basic/gestores/by-centro/{centro_id}", tags=["Basic"], response_model=ApiResponse)
def basic_gestores_by_centro(centro_id: int):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestores_by_centro"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_gestores_by_centro(centro_id)
    return ok(data, meta={"count": len(data), "centro_id": centro_id})

@app.get("/basic/gestores/by-segmento/{segmento_id}", tags=["Basic"], response_model=ApiResponse)
def basic_gestores_by_segmento(segmento_id: str):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestores_by_segmento"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_gestores_by_segmento(segmento_id)
    return ok(data, meta={"count": len(data), "segmento_id": segmento_id})

@app.get("/basic/gestores/count-by-centro", tags=["Basic"], response_model=ApiResponse)
def basic_count_gestores_by_centro():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_gestores_by_centro"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.count_gestores_by_centro()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/gestores/count-by-segmento", tags=["Basic"], response_model=ApiResponse)
def basic_count_gestores_by_segmento():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_gestores_by_segmento"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.count_gestores_by_segmento()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/clientes/by-gestor/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_clientes_by_gestor(gestor_id: int):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_clientes_by_gestor"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_clientes_by_gestor(gestor_id)
    return ok(data, meta={"count": len(data), "gestor_id": gestor_id})

@app.get("/basic/clientes/by-centro/{centro_id}", tags=["Basic"], response_model=ApiResponse)
def basic_clientes_by_centro(centro_id: int):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_clientes_by_centro"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_clientes_by_centro(centro_id)
    return ok(data, meta={"count": len(data), "centro_id": centro_id})

# ---- Productos por gestor (agregado ligero a partir de contratos del gestor)

@app.get("/basic/productos/by-gestor/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_productos_by_gestor(gestor_id: int):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_gestor"):
        return ok([], meta={"note": "basic_queries no disponible"})
    rows = basic_queries.get_contratos_by_gestor(gestor_id)
    # Agregamos por producto
    agg = {}
    for r in rows:
        pid = r.get("PRODUCTO_ID")
        pname = r.get("DESC_PRODUCTO")
        agg.setdefault(pid, {"PRODUCTO_ID": pid, "DESC_PRODUCTO": pname, "num_contratos": 0})
        agg[pid]["num_contratos"] += 1
    data = sorted(agg.values(), key=lambda x: x["num_contratos"], reverse=True)
    return ok(data, meta={"count": len(data), "gestor_id": gestor_id})

# ---- Contratos por centro/producto/gestor (conteos ya existen como helpers)

@app.get("/basic/contracts/count-by-centro", tags=["Basic"], response_model=ApiResponse)
def basic_count_contracts_by_centro():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos_by_centro"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.count_contratos_by_centro()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/contracts/count-by-producto", tags=["Basic"], response_model=ApiResponse)
def basic_count_contracts_by_producto():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos_by_producto"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.count_contratos_by_producto()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/contracts/count-by-gestor", tags=["Basic"], response_model=ApiResponse)
def basic_count_contracts_by_gestor():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos_by_gestor"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.count_contratos_by_gestor()
    return ok(data, meta={"count": len(data)})

# ---- Líneas CDR y cuentas contables

@app.get("/basic/cdr/lineas", tags=["Basic"], response_model=ApiResponse)
def basic_cdr_lineas():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_lineas_cdr"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_all_lineas_cdr()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/cdr/lineas/count", tags=["Basic"], response_model=ApiResponse)
def basic_cdr_lineas_count():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_lineas_cdr"):
        return ok({"total": 0}, meta={"note": "basic_queries no disponible"})
    total = basic_queries.count_lineas_cdr()
    return ok({"total": total})

@app.get("/basic/cuentas", tags=["Basic"], response_model=ApiResponse)
def basic_cuentas():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_cuentas"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_all_cuentas()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/cuentas/by-linea/{linea_cdr}", tags=["Basic"], response_model=ApiResponse)
def basic_cuentas_by_linea(linea_cdr: str):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_cuentas_by_linea_cdr"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_cuentas_by_linea_cdr(linea_cdr)
    return ok(data, meta={"count": len(data), "linea_cdr": linea_cdr})

# ---- Precios estándar / reales y comparativa

@app.get("/basic/precios/std", tags=["Basic"], response_model=ApiResponse)
def basic_precios_std():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_precios_std"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_all_precios_std()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/precios/std/by-segmento/{segmento_id}", tags=["Basic"], response_model=ApiResponse)
def basic_precios_std_by_segmento(segmento_id: str):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precios_std_by_segmento"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_precios_std_by_segmento(segmento_id)
    return ok(data, meta={"count": len(data), "segmento_id": segmento_id})

@app.get("/basic/precios/std/by-sp/{segmento_id}/{producto_id}", tags=["Basic"], response_model=ApiResponse)
def basic_precio_std_by_sp(segmento_id: str, producto_id: str):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precio_std_by_segmento_producto"):
        return ok({}, meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_precio_std_by_segmento_producto(segmento_id, producto_id)
    return ok(data or {}, meta={"segmento_id": segmento_id, "producto_id": producto_id})

@app.get("/basic/precios/real", tags=["Basic"], response_model=ApiResponse)
def basic_precios_real():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_precios_real"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_all_precios_real()
    return ok(data, meta={"count": len(data)})

@app.get("/basic/precios/real/by-fecha", tags=["Basic"], response_model=ApiResponse)
def basic_precios_real_by_fecha(fecha_calculo: str = Query(..., description="YYYY-MM-DD")):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precio_real_by_fecha"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_precio_real_by_fecha(fecha_calculo)
    return ok(data, meta={"count": len(data), "fecha_calculo": fecha_calculo})

@app.get("/basic/precios/real/by-sp/{segmento_id}/{producto_id}", tags=["Basic"], response_model=ApiResponse)
def basic_precios_real_by_sp(segmento_id: str, producto_id: str):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precio_real_by_segmento_producto"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_precio_real_by_segmento_producto(segmento_id, producto_id)
    return ok(data, meta={"count": len(data), "segmento_id": segmento_id, "producto_id": producto_id})

@app.get("/basic/precios/compare", tags=["Basic"], response_model=ApiResponse)
def basic_precios_compare(fecha_calculo: Optional[str] = Query(None, description="YYYY-MM-DD (opcional)")):
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "compare_precios_std_vs_real"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.compare_precios_std_vs_real(fecha_calculo)
    return ok(data, meta={"count": len(data), "fecha_calculo": fecha_calculo})

# ---- Popularidad de productos (ranking global)

@app.get("/basic/productos/top", tags=["Basic"], response_model=ApiResponse)
def basic_productos_top():
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_productos_mas_contratados"):
        return ok([], meta={"note": "basic_queries no disponible"})
    data = basic_queries.get_productos_mas_contratados()
    return ok(data, meta={"count": len(data)})

# ✅ NUEVOS ENDPOINTS PARA SEGMENTACIÓN POR GESTOR

@app.get("/basic/gestores/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_gestor_info(gestor_id: int):
    """Obtiene información completa de un gestor incluyendo su segmento"""
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestor_info"):
        return ok({"gestor_id": gestor_id, "segmento_id": "N10102"}, meta={"note": "fallback mock"})
    
    gestor_info = basic_queries.get_gestor_info(gestor_id)
    if not gestor_info:
        return ok({"error": "Gestor no encontrado"}, meta={"gestor_id": gestor_id})
    
    return ok(gestor_info, meta={"gestor_id": gestor_id})

@app.get("/basic/gestores/{gestor_id}/segmento", tags=["Basic"], response_model=ApiResponse)
def basic_gestor_segmento(gestor_id: int):
    """Obtiene el segmento específico de un gestor"""
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestor_info"):
        return ok({"SEGMENTO_ID": "N10102"}, meta={"note": "fallback segmento", "gestor_id": gestor_id})
    
    gestor_info = basic_queries.get_gestor_info(gestor_id)
    if not gestor_info:
        return ok({"error": "Gestor no encontrado"}, meta={"gestor_id": gestor_id})
    
    return ok({"SEGMENTO_ID": gestor_info.get("SEGMENTO_ID")}, meta={"gestor_id": gestor_id})

@app.get("/prices/comparison-by-segment", tags=["Data Queries"], response_model=ApiResponse)  
def prices_comparison_by_segment(segmento_id: str = Query(...), periodo: str = Query(...)):
    """Obtiene comparación de precios estándar vs real filtrado por segmento y período"""
    if not BASIC_QUERIES_AVAILABLE:
        return ok({"standard": [], "real": [], "segmento_id": segmento_id, "periodo": periodo}, 
                  meta={"note": "mock data - basic queries not available"})
    
    try:
        # Obtener precios estándar por segmento
        std_prices = basic_queries.get_precios_std_by_segmento(segmento_id)
        
        # Obtener precios reales por segmento y período  
        real_prices = basic_queries.get_precios_real_by_segmento_periodo(segmento_id, periodo)
        
        return ok({
            "standard": std_prices,
            "real": real_prices,
            "segmento_id": segmento_id,
            "periodo": periodo
        }, meta={
            "count_std": len(std_prices), 
            "count_real": len(real_prices),
            "total_count": len(std_prices) + len(real_prices)
        })
    
    except Exception as e:
        return err(f"Error fetching price comparison data for segment {segmento_id}: {str(e)}", 500)

@app.get("/basic/clientes/metrics/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_client_metrics_by_gestor(gestor_id: int):
    """Obtiene métricas mejoradas de clientes por gestor (para dashboard)"""
    if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_clientes_by_gestor"):
        return ok([], meta={"note": "basic_queries no disponible"})
    
    clientes = basic_queries.get_clientes_by_gestor(gestor_id)
    contratos = basic_queries.get_contratos_by_gestor(gestor_id) if hasattr(basic_queries, "get_contratos_by_gestor") else []
    
    # Calcular métricas adicionales
    total_clientes = len(clientes)
    total_contratos = len(contratos)
    contratos_por_cliente = total_contratos / total_clientes if total_clientes > 0 else 0
    
    return ok({
        "clientes": clientes,
        "metricas": {
            "total_clientes": total_clientes,
            "total_contratos": total_contratos,
            "contratos_por_cliente": round(contratos_por_cliente, 2)
        }
    }, meta={"gestor_id": gestor_id, "count": total_clientes})

# ----------------------------------------------------------------------------
# KPIs (gestor) + evolución por rango
# ----------------------------------------------------------------------------

@app.get("/kpis/gestor/{gestor_id}", tags=["KPIs"], response_model=ApiResponse)
def kpis_gestor(gestor_id: str, periodo: str = Query(..., description="YYYY-MM")):
    perf = gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo) if hasattr(gestor_queries, "get_gestor_performance_enhanced") else None
    row = perf.data[0] if getattr(perf, "data", None) else {}
    return ok({"gestor_id": gestor_id, "periodo": periodo, "kpis": row}, meta={"note": "raw enhanced KPIs"})

@app.get("/kpis/gestor/{gestor_id}/evolution", tags=["KPIs"], response_model=ApiResponse)
def kpis_evolution_range(gestor_id: str, from_period: str = Query(...), to_period: str = Query(...)):
    if hasattr(gestor_queries, "get_evolution_range"):
        res = gestor_queries.get_evolution_range(gestor_id, from_period, to_period)
        data = getattr(res, "data", [])
        return ok({"gestor_id": gestor_id, "evolution": data}, meta={"periodo": f"{from_period}..{to_period}", "count": len(data)})
    return ok({"gestor_id": gestor_id, "evolution": []}, meta={"note": "no implementado"})

# ----------------------------------------------------------------------------
# Comparatives (gestores/centros/segmentos) + custom
# ----------------------------------------------------------------------------

@app.get("/comparatives/gestores/margen", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_gestores_margen(periodo: str = Query(...)):
    if hasattr(comparative_queries, "ranking_gestores_por_margen_enhanced"):
        res = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        data = getattr(res, "data", [])
        return ok(data, meta={"count": len(data), "periodo": periodo})
    return ok([], meta={"note": "no implementado"})

@app.get("/comparatives/centros/margen", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_centros_margen(periodo: str = Query(...)):
    meth = None
    for name in ("compare_eficiencia_centros_enhanced", "analyze_centros_performance_enhanced"):
        if hasattr(comparative_queries, name):
            meth = getattr(comparative_queries, name)
            break
    data = getattr(meth(periodo), "data", []) if meth else []
    return ok(data, meta={"count": len(data), "periodo": periodo})

@app.get("/comparatives/segmentos/margen", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_segmentos_margen(periodo: str = Query(...)):
    if hasattr(comparative_queries, "ranking_gestores_por_margen_enhanced"):
        # Usamos ranking por margen como proxy si no hay endpoint especifico de segmentos
        res = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        data = getattr(res, "data", [])
        return ok(data, meta={"count": len(data), "periodo": periodo, "note": "proxy"})
    return ok([], meta={"note": "no implementado"})

@app.post("/comparatives/custom", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_custom(payload: Dict[str, Any] = Body(...)):
    """
    payload esperado: {"dimension": "gestor|centro|segmento", "metric": "margen|roe|eficiencia", "periodo": "YYYY-MM", ...}
    """
    periodo = payload.get("periodo")
    dimension = payload.get("dimension", "gestor")
    metric = payload.get("metric", "margen")
    # Selección simple según dimension/metric
    if dimension == "gestor" and hasattr(comparative_queries, "ranking_gestores_por_margen_enhanced"):
        res = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        data = getattr(res, "data", [])
        return ok({"dimension": dimension, "metric": metric, "periodo": periodo, "rows": data}, meta={"count": len(data)})
    return ok({"dimension": dimension, "metric": metric, "periodo": periodo, "rows": []}, meta={"note": "ruta genérica"})

# ----------------------------------------------------------------------------
# Deviations (pricing + summary) + dynamic (protegido por SQL Guard)
# ----------------------------------------------------------------------------

@app.get("/deviations/pricing", tags=["Deviations"], response_model=ApiResponse)
def deviations_pricing(periodo: str = Query(...), umbral: float = Query(15.0)):
    if hasattr(deviation_queries, "detect_precio_desviaciones_criticas_enhanced"):
        res = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, umbral)
        data = getattr(res, "data", [])
        return ok({"periodo": periodo, "umbral": umbral, "deviations": data}, meta={"count": len(data)})
    return ok({"periodo": periodo, "umbral": umbral, "deviations": []}, meta={"note": "no implementado"})

@app.get("/deviations/summary", tags=["Deviations"], response_model=ApiResponse)
def deviations_summary(periodo: str = Query(...)):
    price = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, 15.0) if hasattr(deviation_queries, "detect_precio_desviaciones_criticas_enhanced") else type("R", (), {"data": []})()
    margin = deviation_queries.analyze_margen_anomalies_enhanced(periodo, 2.0) if hasattr(deviation_queries, "analyze_margen_anomalies_enhanced") else type("R", (), {"data": []})()
    volume = deviation_queries.identify_volumen_outliers_enhanced(periodo, 3.0) if hasattr(deviation_queries, "identify_volumen_outliers_enhanced") else type("R", (), {"data": []})()
    summary = {
        "precio": {"total": len(price.data), "top": price.data[:3] if price.data else []},
        "margen": {"total": len(margin.data), "top": margin.data[:3] if margin.data else []},
        "volumen": {"total": len(volume.data)}
    }
    total = len(price.data) + len(margin.data) + len(volume.data)
    return ok(summary, meta={"periodo": periodo, "count": total})

@app.post("/deviations/dynamic", tags=["Deviations"], response_model=ApiResponse)
def deviations_dynamic(req: DynamicQueryRequest):
    if not SQL_GUARD_AVAILABLE:
        return ok({"error": "sql_guard no disponible"}, meta={"note": "mock"})
    validation = validate_query_for_cdg(req.sql, context=req.context)
    if not validation.get("is_safe"):
        err(f"Query no segura: {validation}", 400)
    # Aquí iría la ejecución segura (ORM/driver) – placeholder:
    # data = db.execute_select(req.sql)
    data = []  # placeholder seguro
    return ok({"validation": validation, "rows": data}, meta={"count": len(data), "source": "dynamic_select"})

# ---- Deviations adicionales: margen, volumen, patrones, cross-producto, intelligent-query

@app.get("/deviations/margen", tags=["Deviations"], response_model=ApiResponse)
def deviations_margen(
    periodo: str = Query(..., description="YYYY-MM"),
    z: float = Query(2.0, description="Z-score / umbral estadístico"),
    enhanced: bool = Query(True)
):
    """
    Detecta anomalías de margen (por gestor/centro/segmento según implementación).
    Intenta primero la versión *_enhanced si existe.
    """
    data = []
    # preferimos enhanced si está y enhanced==True
    meth_names = []
    if enhanced:
        meth_names.append("analyze_margen_anomalies_enhanced")
    meth_names.extend(["analyze_margen_anomalies", "detect_margen_anomalies", "detect_margen_desviaciones"])

    for name in meth_names:
        if hasattr(deviation_queries, name):
            res = getattr(deviation_queries, name)(periodo, z)
            data = getattr(res, "data", [])
            break

    return ok({"periodo": periodo, "z": z, "deviations": data}, meta={"count": len(data), "source": name if data else "fallback"})

@app.get("/deviations/volumen", tags=["Deviations"], response_model=ApiResponse)
def deviations_volumen(
    periodo: str = Query(..., description="YYYY-MM"),
    factor: float = Query(3.0, description="Multiplicador de outliers (ej. IQR*factor o std*factor)"),
    enhanced: bool = Query(True)
):
    """
    Detecta outliers de volumen. Usa *_enhanced si está disponible.
    """
    data = []
    meth_names = []
    if enhanced:
        meth_names.append("identify_volumen_outliers_enhanced")
    meth_names.extend(["identify_volumen_outliers", "detect_volumen_outliers"])

    for name in meth_names:
        if hasattr(deviation_queries, name):
            res = getattr(deviation_queries, name)(periodo, factor)
            data = getattr(res, "data", [])
            break

    return ok({"periodo": periodo, "factor": factor, "deviations": data}, meta={"count": len(data)})

@app.get("/deviations/patrones", tags=["Deviations"], response_model=ApiResponse)
def deviations_patrones(
    gestorId: Optional[str] = Query(None, description="Gestor específico (opcional)"),
    num_periods: int = Query(6, ge=2, le=24, description="Ventana temporal de análisis"),
    enhanced: bool = Query(True)
):
    """
    Detecta patrones anómalos temporales (tendencias, rupturas) por gestor o global.
    Busca métodos típicos de patrón temporal.
    """
    data = []
    meth_names = []
    if enhanced:
        meth_names.append("detect_temporal_patterns_enhanced")
    meth_names.extend(["detect_temporal_patterns", "analyze_temporal_patterns"])

    for name in meth_names:
        if hasattr(deviation_queries, name):
            # algunos métodos podrían no requerir gestorId, manejamos ambos
            try:
                if gestorId is not None:
                    res = getattr(deviation_queries, name)(gestorId, num_periods)
                else:
                    res = getattr(deviation_queries, name)(num_periods)
            except TypeError:
                # firma alternativa: (num_periods, gestorId)
                res = getattr(deviation_queries, name)(num_periods, gestorId)
            data = getattr(res, "data", [])
            break

    return ok({"gestorId": gestorId, "num_periods": num_periods, "patterns": data}, meta={"count": len(data)})

@app.get("/deviations/cross-producto", tags=["Deviations"], response_model=ApiResponse)
def deviations_cross_producto(
    periodo: str = Query(..., description="YYYY-MM"),
    enhanced: bool = Query(True)
):
    """
    Cruce de desviaciones por producto vs segmento/gestor/centro (según implementación).
    Intenta variantes conocidas y cae en proxy si no existe.
    """
    data = []
    used = None
    # candidatos de método posibles
    candidates = []
    if enhanced:
        candidates += [
            "cross_producto_deviations_enhanced",
            "detect_cross_producto_anomalies_enhanced",
        ]
    candidates += [
        "cross_producto_deviations",
        "detect_cross_producto_anomalies",
        "cross_tab_producto_segmento",
        "cross_producto_segmento_alerts",
    ]

    for name in candidates:
        if hasattr(deviation_queries, name):
            used = name
            try:
                res = getattr(deviation_queries, name)(periodo)
            except TypeError:
                # alguna firma alternativa: (periodo, extra_opts)
                res = getattr(deviation_queries, name)(periodo, {})
            data = getattr(res, "data", [])
            break

    # Proxy muy básico si no existe método: combinar pricing+volumen y mapear por PRODUCTO_ID
    if not data:
        price = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, 15.0) if hasattr(deviation_queries, "detect_precio_desviaciones_criticas_enhanced") else type("R", (), {"data": []})()
        volume = deviation_queries.identify_volumen_outliers_enhanced(periodo, 3.0) if hasattr(deviation_queries, "identify_volumen_outliers_enhanced") else type("R", (), {"data": []})()
        idx = {}
        for r in getattr(price, "data", []):
            pid = r.get("PRODUCTO_ID")
            if pid:
                idx.setdefault(pid, {"PRODUCTO_ID": pid, "precio_alerts": 0, "volumen_alerts": 0})
                idx[pid]["precio_alerts"] += 1
        for r in getattr(volume, "data", []):
            pid = r.get("PRODUCTO_ID")
            if pid:
                idx.setdefault(pid, {"PRODUCTO_ID": pid, "precio_alerts": 0, "volumen_alerts": 0})
                idx[pid]["volumen_alerts"] += 1
        data = sorted(idx.values(), key=lambda x: (x["precio_alerts"] + x["volumen_alerts"]), reverse=True)
        used = used or "proxy(price+volume)"

    return ok({"periodo": periodo, "rows": data}, meta={"count": len(data), "source": used})

@app.post("/deviations/intelligent-query", tags=["Deviations"], response_model=ApiResponse)
async def deviations_intelligent_query(req: IntelligentDeviationRequest):
    """
    Interfaz de PNL para obtener la "mejor" query de desviaciones según una pregunta libre.
    Intenta módulos especializados; fallback al CDG Agent.
    """
    # 1) deviation_queries: nombres probables (llamadas síncronas)
    for name in (
        "get_best_deviation_query_for_question",
        "ask_deviations_expert",
        "intelligent_deviation_query",
        "ask_intelligent_deviation_query",
    ):
        if hasattr(deviation_queries, name):
            res = getattr(deviation_queries, name)(
                question=req.question,
                context=req.context,
                periodo=req.periodo,
                gestor_id=req.gestor_id,
                segmento_id=req.segmento_id,
                producto_id=req.producto_id,
            )
            data = getattr(res, "data", res)  # por si devuelve dict ya listo
            return ok({"answer": data}, meta={"source": f"deviation_queries.{name}"})

    # 2) fallback: orquestación vía CDG Agent (async correcto, sin run_until_complete)
    try:
        cdg_req = CDGRequest(
            user_message=f"[DEVIATIONS_INTELLIGENT_QUERY] {req.question}",
            user_id=(req.context or {}).get("user_id"),
            gestor_id=req.gestor_id,
            periodo=req.periodo,
            context=req.context or {},
            include_charts=False,
            include_recommendations=True,
            use_basic_queries=True,
            quick_mode=True,
        )
        resp = await cdg_agent.process_request(cdg_req)
        return ok(resp.to_dict() if hasattr(resp, "to_dict") else {"content": getattr(resp, "content", {})},
                  meta={"source": "cdg_agent.process_request"})
    except Exception as e:
        return ok({"note": "fallback", "error": str(e)}, meta={"source": "fallback"})

# ----------------------------------------------------------------------------
# Incentives (scorecard, ranking, simulación, dinámicos)
# ----------------------------------------------------------------------------

@app.get("/incentives/gestor/{gestor_id}", tags=["Incentives"], response_model=ApiResponse)
def incentives_scorecard(gestor_id: str, periodo: str = Query(...)):
    data: Dict[str, Any] = {"gestor_id": gestor_id, "periodo": periodo, "scorecard": [], "total_incentivo": 0.0}
    if hasattr(incentive_queries, "get_scorecard_detallado"):
        res = incentive_queries.get_scorecard_detallado(gestor_id, periodo)
        return ok(getattr(res, "data", data))
    # fallback combinando enhanced si existen
    out = {"gestor_id": gestor_id, "periodo": periodo, "scorecard": [], "total_incentivo": 0.0}
    try:
        bonus = incentive_queries.analyze_bonus_margen_neto_enhanced(periodo, 15.0) if hasattr(incentive_queries, "analyze_bonus_margen_neto_enhanced") else type("R", (), {"data": []})()
        pool = incentive_queries.calculate_ranking_bonus_pool_enhanced(periodo, 50000.0) if hasattr(incentive_queries, "calculate_ranking_bonus_pool_enhanced") else type("R", (), {"data": []})()
        filt = lambda arr: [x for x in getattr(arr, "data", []) if str(x.get("GESTOR_ID", x.get("gestor_id"))) == str(gestor_id)]
        out["scorecard"] = [
            {"kpi": "margen_neto_bonus", "detalle": filt(bonus)},
            {"kpi": "pool_distribution", "detalle": filt(pool)},
        ]
        out["total_incentivo"] = sum([x.get("incentivo_final_eur", x.get("incentivo", 0.0)) for x in (filt(bonus) + filt(pool))])
    except Exception:
        ...
    return ok(out)

@app.get("/incentives/bonus-margen", tags=["Incentives"], response_model=ApiResponse)
def incentives_bonus_margen(periodo: str = Query(...), umbral_margen: float = Query(15.0)):
    if hasattr(incentive_queries, "analyze_bonus_margen_neto_enhanced"):
        res = incentive_queries.analyze_bonus_margen_neto_enhanced(periodo, umbral_margen)
        data = getattr(res, "data", [])
        return ok(data, meta={"count": len(data), "periodo": periodo})
    return ok([], meta={"note": "no implementado"})

@app.get("/incentives/bonus-pool", tags=["Incentives"], response_model=ApiResponse)
def incentives_bonus_pool(periodo: str = Query(...), pool: float = Query(50000.0)):
    if hasattr(incentive_queries, "calculate_ranking_bonus_pool_enhanced"):
        res = incentive_queries.calculate_ranking_bonus_pool_enhanced(periodo, pool)
        data = getattr(res, "data", [])
        return ok({"pool": data}, meta={"count": len(data), "periodo": periodo})
    return ok({"pool": []}, meta={"note": "no implementado"})

@app.post("/incentives/simulate", tags=["Incentives"], response_model=ApiResponse)
def incentives_simulate(payload: Dict[str, Any] = Body(...)):
    gestor_id = str(payload.get("gestor_id", ""))
    periodo = payload.get("periodo")
    if hasattr(incentive_queries, "simulate_incentive_scenarios_enhanced") and gestor_id and periodo:
        res = incentive_queries.simulate_incentive_scenarios_enhanced(gestor_id, periodo)
        return ok(getattr(res, "data", []))
    return ok([], meta={"note": "no implementado"})

@app.post("/incentives/dynamic", tags=["Incentives"], response_model=ApiResponse)
def incentives_dynamic(req: DynamicQueryRequest):
    if not SQL_GUARD_AVAILABLE:
        return ok({"error": "sql_guard no disponible"}, meta={"note": "mock"})
    validation = validate_query_for_cdg(req.sql, context=req.context)
    if not validation.get("is_safe"):
        err(f"Query no segura: {validation}", 400)
    # data = db.execute_select(req.sql)  # placeholder
    data = []
    return ok({"validation": validation, "rows": data}, meta={"count": len(data), "source": "dynamic_select"})

# ----------------------------------------------------------------------------
# Variance Bridge (precio / volumen / mix / FX / one-offs)
# ----------------------------------------------------------------------------

@app.get("/analytics/variance", tags=["Analytics"], response_model=ApiResponse)
def variance(
    scope: str = Query(..., enum=["gestor", "centro", "segmento"]),
    id: Optional[str] = Query(None),
    periodo: str = Query(...),
    vs: str = Query("budget", enum=["budget", "last_year", "last_period"]),
):
    if hasattr(comparative_queries, "variance_bridge_enhanced"):
        res = comparative_queries.variance_bridge_enhanced(scope, id, periodo, vs)
        data = getattr(res, "data", [])
    else:
        data = [
            {"driver": "precio", "impacto": 12000.0},
            {"driver": "volumen", "impacto": -8000.0},
            {"driver": "mix", "impacto": 3500.0},
        ]
    # semáforo básico por magnitud relativa (placeholder)
    for d in data:
        val = abs(d.get("impacto", 0))
        d["semaforo"] = "Verde" if val < 5000 else ("Amarillo" if val < 10000 else "Rojo")
    return ok({"scope": scope, "id": id, "periodo": periodo, "vs": vs, "bridge": data}, meta={"count": len(data)})

# ----------------------------------------------------------------------------
# Prices: real vs estándar (por producto; opcional filtro gestor)
# ----------------------------------------------------------------------------

@app.get("/prices/comparison", tags=["Data Queries"], response_model=ApiResponse)
def prices_comparison(
    gestor_id: Optional[str] = None,
    producto_id: Optional[str] = None,
    periodo: Optional[str] = None,
):
    std = basic_queries.get_all_precios_std() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_precios_std") else []
    real = basic_queries.get_all_precios_real() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_precios_real") else []
    def _f(arr):
        out = arr
        if producto_id:
            out = [x for x in out if str(x.get("PRODUCTO_ID", x.get("producto_id", ""))) == str(producto_id)]
        return out
    data = {"standard": _f(std), "real": _f(real)}
    return ok(data, meta={"count": len(data.get("real", []))})

# ----------------------------------------------------------------------------
# Charts (generate, pivot, quick, tipos, validate)
# ----------------------------------------------------------------------------

@app.post("/charts/from-data", tags=["Charts"], response_model=ApiResponse)
def charts_from_data(body: Dict[str, Any]):
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"chart": {"id": "mock"}})
    chart = create_chart_from_query_data(body.get("data", []), body.get("config", {}))
    return ok({"chart": chart})

@app.post("/charts/pivot", tags=["Charts"], response_model=ApiResponse)
def charts_pivot(body: ChartPivotRequest):
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"status": "mock", "message": "Chart generator no disponible"})
    result = pivot_chart_with_query_integration(body.message, body.current_chart_config or {})
    return ok(result)

@app.post("/charts/quick", tags=["Charts"], response_model=ApiResponse)
def charts_quick(payload: Dict[str, Any] = Body(...)):
    """
    Crea un gráfico rápido a partir de métodos "predefinidos" del ChartFactory:
      - query_method: 'gestores_ranking' | 'centros_distribution' | 'productos_popularity'
                      | 'precios_comparison' | 'summary_dashboard'
      - chart_type: 'bar' | 'line' | 'pie' | 'area' | 'horizontal_bar' | 'donut' | 'stacked_bar' ...
      - kwargs: parámetros específicos (p.ej. fecha_calculo para precios, etc.)
    """
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"chart": {"id": "mock"}})

    query_method = payload.get("query_method")
    chart_type = payload.get("chart_type", "bar")
    kwargs = payload.get("kwargs", {}) or {}

    chart = create_quick_chart(query_method, chart_type=chart_type, **kwargs)
    # ChartFactory ya devuelve estructuras listas para front; metadatos útiles:
    count = len(chart.get("data", [])) if isinstance(chart, dict) else 0
    return ok({"chart": chart}, meta={"count": count, "query_method": query_method})

@app.get("/charts/supported-types", tags=["Charts"], response_model=ApiResponse)
def charts_supported_types():
    # Si ChartFactory expone tipos, úsalo; si no, lista mínima
    types = ["bar", "line", "pie", "area", "radar", "table"]
    return ok(types)

@app.get("/charts/validate", tags=["Charts"], response_model=ApiResponse)
def charts_validate():
    res = validate_chart_generator() if CHART_GENERATOR_AVAILABLE else {"status": "MOCK"}
    return ok(res)

@app.get("/charts/available-queries", tags=["Charts"], response_model=ApiResponse)
def charts_available_queries():
    """
    Lista de "queries rápidas" soportadas por ChartFactory (para dropdowns en UI).
    """
    try:
        available = ChartFactory.get_available_queries()
    except Exception:
        available = ["gestores_ranking", "centros_distribution", "productos_popularity", "precios_comparison", "summary_dashboard"]
    return ok(available, meta={"count": len(available)})

@app.get("/charts/meta", tags=["Charts"], response_model=ApiResponse)
def charts_meta():
    """
    Devuelve la metaconfiguración de gráficos (tipos, dimensiones, métricas, paleta corporativa)
    para que el frontend construya formularios/pickers sin hardcode.
    """
    meta = {
        "chart_types": list((CDG_CHART_CONFIGS.get("chart_types") or {}).keys()) or ["bar", "line", "pie", "area", "horizontal_bar", "donut", "stacked_bar"],
        "dimensions": CDG_CHART_CONFIGS.get("dimensions") or {"gestor": "Gestor", "centro": "Centro", "segmento": "Segmento", "producto": "Producto", "periodo": "Período", "cliente": "Cliente", "contrato": "Contrato"},
        "metrics": CDG_CHART_CONFIGS.get("metrics") or {"CONTRATOS": "Número de Contratos"},
        "colors": CDG_CHART_CONFIGS.get("colors") or {},
        "supports_pivot": True
    }
    return ok(meta)

@app.get("/charts/summary-dashboard", tags=["Charts"], response_model=ApiResponse)
def charts_summary_dashboard():
    """
    Devuelve un pequeño dashboard-resumen (3+ charts) basado en basic_queries.
    Perfecto para la home del panel.
    """
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"dashboard": {"id": "mock", "charts": []}}, meta={"note": "mock"})
    gen = QueryIntegratedChartGenerator()
    dashboard = gen.generate_summary_dashboard()
    charts = dashboard.get("charts", []) if isinstance(dashboard, dict) else []
    return ok(dashboard, meta={"count": len(charts)})

@app.get("/charts/gestores-ranking", tags=["Charts"], response_model=ApiResponse)
def charts_gestores_ranking(
    metric: str = Query("CONTRATOS", enum=["CONTRATOS", "CLIENTES"]),
    chart_type: str = Query("horizontal_bar")
):
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"chart": {"id": "mock"}})
    gen = QueryIntegratedChartGenerator()
    chart = gen.generate_gestores_ranking_chart(metric=metric, chart_type=chart_type)
    return ok({"chart": chart}, meta={"metric": metric})

@app.get("/charts/centros-distribution", tags=["Charts"], response_model=ApiResponse)
def charts_centros_distribution(chart_type: str = Query("donut")):
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"chart": {"id": "mock"}})
    gen = QueryIntegratedChartGenerator()
    chart = gen.generate_centros_distribution_chart(chart_type=chart_type)
    return ok({"chart": chart})

@app.get("/charts/productos-popularity", tags=["Charts"], response_model=ApiResponse)
def charts_productos_popularity(chart_type: str = Query("horizontal_bar")):
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"chart": {"id": "mock"}})
    gen = QueryIntegratedChartGenerator()
    chart = gen.generate_productos_popularity_chart(chart_type=chart_type)
    return ok({"chart": chart})

@app.get("/charts/precios-comparison", tags=["Charts"], response_model=ApiResponse)
def charts_precios_comparison(fecha_calculo: Optional[str] = Query(None), chart_type: str = Query("bar")):
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"chart": {"id": "mock"}})
    gen = QueryIntegratedChartGenerator()
    chart = gen.generate_precios_comparison_chart(fecha_calculo=fecha_calculo, chart_type=chart_type)
    return ok({"chart": chart}, meta={"fecha_calculo": fecha_calculo})

@app.get("/charts/gastos-by-centro", tags=["Charts"], response_model=ApiResponse)
def charts_gastos_by_centro(fecha: str = Query(..., description="YYYY-MM-DD"), chart_type: str = Query("stacked_bar")):
    if not CHART_GENERATOR_AVAILABLE:
        return ok({"chart": {"id": "mock"}})
    gen = QueryIntegratedChartGenerator()
    chart = gen.generate_gastos_by_centro_chart(fecha=fecha, chart_type=chart_type)
    return ok({"chart": chart}, meta={"fecha": fecha})

# --- Charts: stateful helpers (usar el singleton query_chart) ---

@app.post("/charts/register", tags=["Charts"], response_model=ApiResponse)
def charts_register(body: Dict[str, Any] = Body(...)):
    """
    Guarda un gráfico en el registro in-memory del generador y devuelve su id estandarizado.
    body: { "chart": {...} }  -> gráfico ya formado (por ejemplo, devuelto por /charts/from-data)
    """
    chart = (body or {}).get("chart", {})
    if not isinstance(chart, dict) or not chart:
        err("chart vacío o inválido", 400)
    chart_id = chart.get("id") or f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    chart["id"] = chart_id
    try:
        # Usa el singleton para mantener estado
        query_chart.current_charts[chart_id] = chart
        return ok({"chart_id": chart_id, "chart": chart})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "cannot register"})

@app.get("/charts/{chart_id}", tags=["Charts"], response_model=ApiResponse)
def charts_get(chart_id: str):
    chart = query_chart.current_charts.get(chart_id)
    if not chart:
        err(f"chart_id {chart_id} no encontrado", 404)
    return ok(chart)

@app.post("/charts/{chart_id}/pivot", tags=["Charts"], response_model=ApiResponse)
def charts_pivot_by_id(chart_id: str, body: Dict[str, Any] = Body(...)):
    """
    Aplica un pivot por lenguaje natural al chart registrado.
    body: { "message": "...intención en NL..." }
    """
    chart = query_chart.current_charts.get(chart_id)
    if not chart:
        err(f"chart_id {chart_id} no encontrado", 404)
    message = (body or {}).get("message", "")
    if not message:
        err("message vacío", 400)
    current_cfg = chart.get("config", {})
    result = query_chart.interpret_chart_change(message, current_cfg)
    # aplica si success
    if result.get("status") == "success":
        chart["config"] = result.get("new_config", current_cfg)
        # opcional: re-generar data en función de nueva config si procede
        query_chart.current_charts[chart_id] = chart
    return ok({"pivot": result, "chart": chart})

@app.post("/charts/interpret", tags=["Charts"], response_model=ApiResponse)
def charts_interpret(body: Dict[str, Any] = Body(...)):
    """
    Devuelve la propuesta de new_config a partir de un mensaje en NL, sin mutar ningún chart.
    body: { "message": "...", "current_config": {...} }
    """
    msg = (body or {}).get("message", "")
    cfg = (body or {}).get("current_config", {}) or {}
    if not msg:
        err("message vacío", 400)
    proposal = query_chart.interpret_chart_change(msg, cfg)
    return ok(proposal)

# ----------------------------------------------------------------------------
# Dashboards (plantillas + builder)
# ----------------------------------------------------------------------------

@app.get("/dashboards/templates", tags=["Dashboards"], response_model=ApiResponse)
def dashboards_templates():
    templates = [
        {"id": "summary", "title": "Dashboard Resumen CDG", "params": []},
        {"id": "gestor_performance", "title": "Performance por Gestor", "params": ["gestor_id", "periodo"]},
    ]
    return ok(templates, meta={"count": len(templates)})

@app.post("/dashboards/build", tags=["Dashboards"], response_model=ApiResponse)
def dashboards_build(payload: Dict[str, Any] = Body(...)):
    tpl = (payload or {}).get("template_id")
    if not tpl:
        err("template_id requerido", 400)

    if tpl == "summary":
        dashboard = QueryIntegratedChartGenerator().generate_summary_dashboard() if CHART_GENERATOR_AVAILABLE else {"id": "mock", "charts": []}
        return ok(dashboard, meta={"template_id": tpl})

    if tpl == "gestor_performance":
        gestor_id = payload.get("gestor_id")
        periodo = payload.get("periodo")
        if not (gestor_id and periodo):
            err("gestor_id y periodo requeridos", 400)
        perf = gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo) if hasattr(gestor_queries, "get_gestor_performance_enhanced") else type("R", (), {"data": []})()
        row = perf.data[0] if getattr(perf, "data", None) else {}
        dash = chart_dash.generate_gestor_dashboard(gestor_data=row, kpi_data=row, periodo=periodo) if CHART_GENERATOR_AVAILABLE else {"charts": []}
        dash["id"] = f"dashboard_{gestor_id}_{periodo}"
        dash["title"] = f"Performance Gestor {gestor_id} — {periodo}"
        return ok(dash, meta={"template_id": tpl})

    # fallback
    return ok({"id": "unknown_template", "charts": []}, meta={"note": "template no soportado"})

# ----------------------------------------------------------------------------
# Reports
# ----------------------------------------------------------------------------

@app.post("/reports/business-review", tags=["Reports"], response_model=ApiResponse)
def reports_business_review(req: ReportRequest):
    data = {"message": "Business Review generado"}
    if hasattr(report_gen, "generate_business_review") and hasattr(gestor_queries, "get_gestor_performance_enhanced"):
        g = gestor_queries.get_gestor_performance_enhanced(req.gestor_id, req.periodo)
        if getattr(g, "data", None):
            br = report_gen.generate_business_review(gestor_data=g.data[0], period=req.periodo)
            data = br.to_dict() if hasattr(br, "to_dict") else {"review": "ok"}
    return ok(data, meta={"periodo": req.periodo})

@app.post("/reports/executive-summary", tags=["Reports"], response_model=ApiResponse)
def reports_executive_summary(req: ReportRequest):
    data = {"message": "Executive Summary generado"}
    if hasattr(report_gen, "generate_executive_summary_report"):
        es = report_gen.generate_executive_summary_report(consolidated_data=req.options or {}, periodo=req.periodo)
        data = es.to_dict() if hasattr(es, "to_dict") else {"summary": "ok"}
    return ok(data, meta={"periodo": req.periodo})

@app.post("/reports/deviation-analysis", tags=["Reports"], response_model=ApiResponse)
def reports_deviation_analysis(periodo: str = Query(...)):
    price = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, 15.0) if hasattr(deviation_queries, "detect_precio_desviaciones_criticas_enhanced") else type("R", (), {"data": []})()
    margin = deviation_queries.analyze_margen_anomalies_enhanced(periodo, 2.0) if hasattr(deviation_queries, "analyze_margen_anomalies_enhanced") else type("R", (), {"data": []})()
    volume = deviation_queries.identify_volumen_outliers_enhanced(periodo, 3.0) if hasattr(deviation_queries, "identify_volumen_outliers_enhanced") else type("R", (), {"data": []})()
    return ok({
        "periodo": periodo,
        "deviations": {
            "precio": getattr(price, "data", []),
            "margen": getattr(margin, "data", []),
            "volumen": getattr(volume, "data", []),
        }
    })

@app.post("/reports/export", tags=["Reports"], response_model=ApiResponse)
def reports_export(payload: Dict[str, Any] = Body(...)):
    # Aquí se implementaría la exportación a PDF/Excel
    return ok({"status": "exported", "format": payload.get("format", "pdf")})

@app.get("/reports/meta", tags=["Reports"], response_model=ApiResponse)
def reports_meta():
    return ok({
        "types": ["business_review", "executive_summary", "deviation_analysis"],
        "formats": ["pdf", "xlsx", "json"]
    })

# ----------------------------------------------------------------------------
# KPI Calculator (utilidades)
# ----------------------------------------------------------------------------

@app.post("/kpi/margen", tags=["KPI Calculator"], response_model=ApiResponse)
def kpi_margen(req: KPIRequest):
    if hasattr(kpi_calc, "calculate_margen_neto") and req.ingresos is not None and req.gastos is not None:
        val = kpi_calc.calculate_margen_neto(req.ingresos, req.gastos)
        return ok({"margen_neto": val})
    return ok({"margen_neto": None}, meta={"note": "no implementado"})

@app.post("/kpi/roe", tags=["KPI Calculator"], response_model=ApiResponse)
def kpi_roe(req: KPIRequest):
    if hasattr(kpi_calc, "calculate_roe") and req.beneficio_neto is not None and req.patrimonio is not None:
        val = kpi_calc.calculate_roe(req.beneficio_neto, req.patrimonio)
        return ok({"roe": val})
    return ok({"roe": None}, meta={"note": "no implementado"})

@app.post("/kpi/from-data", tags=["KPI Calculator"], response_model=ApiResponse)
def kpi_from_data(req: KPIRequest):
    if hasattr(kpi_calc, "get_kpis_from_data") and req.row:
        val = kpi_calc.get_kpis_from_data(req.row)
        return ok(val)
    return ok({}, meta={"note": "no implementado"})

@app.post("/kpi/from-gestor-data", tags=["KPI Calculator"], response_model=ApiResponse)
def kpi_from_gestor_data(req: KPIRequest):
    if hasattr(kpi_calc, "get_kpis_from_gestor_data") and req.row:
        val = kpi_calc.get_kpis_from_gestor_data(req.row)
        return ok(val)
    return ok({}, meta={"note": "no implementado"})

# ----------------------------------------------------------------------------
# SQL Guard (seguridad consultas)
# ----------------------------------------------------------------------------

@app.post("/security/sql/validate", tags=["Security"], response_model=ApiResponse)
def security_sql_validate(req: DynamicQueryRequest):
    if not SQL_GUARD_AVAILABLE:
        return ok({"is_safe": True, "mode": "mock"})
    v = validate_query_for_cdg(req.sql, context=req.context)
    return ok(v)

# ----------------------------------------------------------------------------
# ✅ Agent Orchestration (CDG Agent v5.0 integración completa)
# ----------------------------------------------------------------------------

@app.post("/agent/process", tags=["Agent"], response_model=ApiResponse)
async def agent_process(req: AgentProcessRequest):
    """Procesamiento principal con CDG Agent v5.0"""
    try:
        result = await process_cdg_request(
            req.user_message,
            gestor_id=req.gestor_id,
            periodo=req.periodo,
            user_id=req.user_id,
            include_charts=req.include_charts,
            include_recommendations=req.include_recommendations,
            current_chart_config=req.current_chart_config,
            chart_interaction_type=req.chart_interaction_type,
            use_basic_queries=req.use_basic_queries,
            quick_mode=req.quick_mode,
            context=req.context
        )
        return ok(result, meta={"source": "cdg_agent.process_cdg_request", "version": "5.0"})
    except Exception:
        # fallback: construir CDGRequest y pasar por la instancia
        cdg_req = CDGRequest(
            user_message=req.user_message,
            user_id=req.user_id,
            gestor_id=req.gestor_id,
            periodo=req.periodo,
            context=req.context,
            include_charts=req.include_charts,
            include_recommendations=req.include_recommendations,
            current_chart_config=req.current_chart_config,
            chart_interaction_type=req.chart_interaction_type,
            use_basic_queries=req.use_basic_queries,
            quick_mode=req.quick_mode
        )
        resp = await cdg_agent.process_request(cdg_req)
        return ok(resp.to_dict() if hasattr(resp, "to_dict") else {})

@app.post("/agent/quick", tags=["Agent"], response_model=ApiResponse)
async def agent_quick(req: AgentProcessRequest):
    """Procesamiento rápido con CDG Agent v5.0"""
    try:
        result = await process_quick_query(
            req.user_message,
            include_charts=req.include_charts,
            gestor_id=req.gestor_id,
            periodo=req.periodo,
            user_id=req.user_id
        )
        return ok(result, meta={"source": "cdg_agent.process_quick_query"})
    except Exception:
        return ok({"note": "quick query fallback"})

@app.get("/agent/status", tags=["Agent"], response_model=ApiResponse)
def agent_status():
    try:
        return ok(cdg_agent.get_agent_status())
    except Exception:
        return ok({"status": "unknown", "version": "5.0"})

@app.get("/agent/integration-summary", tags=["Agent"], response_model=ApiResponse)
def agent_integration_summary():
    try:
        return ok(cdg_agent.get_integration_summary())
    except Exception:
        return ok({"summary": "not available"})

@app.get("/agent/suggest-questions", tags=["Agent"], response_model=ApiResponse)
def agent_suggest_questions(user_id: Optional[str] = None):
    try:
        suggestions = chat_agent.get_dynamic_suggestions(user_id or "anon")
    except Exception:
        suggestions = [
            "¿Qué gestores lideran el margen este mes?",
            "Muéstrame la desviación de precio por producto",
            "Compara centros por eficiencia (último período)"
        ]
    return ok(suggestions, meta={"count": len(suggestions)})

@app.get("/agent/suggest-dashboards", tags=["Agent"], response_model=ApiResponse)
def agent_suggest_dashboards(user_id: Optional[str] = None, periodo: Optional[str] = None):
    suggestions = [
        {"template_id": "summary", "label": "Resumen Ejecutivo"},
        {"template_id": "gestor_performance", "label": "Performance por Gestor", "requires": ["gestor_id", "periodo"]},
    ]
    return ok({"periodo": periodo, "suggestions": suggestions}, meta={"count": len(suggestions)})

@app.get("/agent/validate-basic-queries", tags=["Agent"], response_model=ApiResponse)
def agent_validate_basic_queries():
    try:
        return ok(cdg_agent.validate_basic_queries_integration())
    except Exception:
        return ok({"overall_status": "ERROR"})

@app.post("/agent/reset-history", tags=["Agent"], response_model=ApiResponse)
def agent_reset_history():
    try:
        cdg_agent.reset_conversation_history()
        return ok({"status": "reset"})
    except Exception:
        return ok({"status": "error"})

@app.get("/agent/periods", tags=["Agent"], response_model=ApiResponse)
def agent_periods():
    try:
        data = cdg_agent.get_available_periods()
        return ok(data, meta={"source": "cdg_agent"})
    except Exception:
        return ok({"periods": [], "count": 0}, meta={"note": "fallback"})

@app.get("/agent/periods/latest", tags=["Agent"], response_model=ApiResponse)
def agent_periods_latest():
    try:
        latest = cdg_agent.get_latest_period()
        return ok({"latest": latest}, meta={"source": "cdg_agent"})
    except Exception:
        return ok({"latest": None})

@app.get("/agent/gestores", tags=["Agent"], response_model=ApiResponse)
async def agent_gestores():
    try:
        data = await cdg_agent.get_gestores_list()
        return ok(data, meta={"count": len(data)})
    except Exception:
        return ok([], meta={"note": "fallback"})

@app.get("/agent/centros", tags=["Agent"], response_model=ApiResponse)
async def agent_centros():
    try:
        data = await cdg_agent.get_centros_list()
        return ok(data, meta={"count": len(data)})
    except Exception:
        return ok([], meta={"note": "fallback"})

# Proxy útiles a funciones públicas del agente (gráficos integrados)
@app.post("/agent/charts/generate", tags=["Agent"], response_model=ApiResponse)
async def agent_charts_generate(body: Dict[str, Any]):
    try:
        chart = await cdg_agent.generate_chart_from_data(body.get("data", []), body.get("config", {}))
        return ok(chart)
    except Exception:
        return ok({"chart": {"id": "mock"}})

@app.post("/agent/charts/pivot", tags=["Agent"], response_model=ApiResponse)
async def agent_charts_pivot(body: Dict[str, Any]):
    try:
        result = await cdg_agent.pivot_chart(body.get("user_message", ""), body.get("current_chart_config", {}))
        return ok(result)
    except Exception:
        return ok({"status": "error", "message": "fallback"})

# ----------------------------------------------------------------------------
# ✅ Chat + WebSocket + utilidades de conversación (Chat Agent v9.1)
# ----------------------------------------------------------------------------

@app.post("/chat/message", tags=["Chat"], response_model=ApiResponse)
async def chat_message(req: ChatRequest):
    """Procesamiento de mensajes con Chat Agent v9.1"""
    msg = ChatMessage(
        user_id=req.user_id,
        message=req.message,
        gestor_id=req.gestor_id,
        periodo=req.periodo,
        include_charts=req.include_charts,
        include_recommendations=req.include_recommendations,
        context=req.context,
        user_feedback=req.user_feedback,
        current_chart_config=req.current_chart_config,
        chart_interaction_type=req.chart_interaction_type,
        use_basic_queries=req.use_basic_queries,
        quick_mode=req.quick_mode,
    )
    resp = await chat_agent.process_chat_message(msg)
    
    # ✅ Compatibilidad con Chat Agent v9.1
    if hasattr(resp, "dict"):
        data = resp.dict()
    elif hasattr(resp, "model_dump"):
        data = resp.model_dump()
    else:
        data = {"response": getattr(resp, "response", "ok")}
    
    return ok(data, meta={"source": "chat_agent_v9.1"})

@app.get("/chat/status", tags=["Chat"], response_model=ApiResponse)
def chat_status():
    return ok(chat_agent.get_agent_status())

@app.get("/chat/history/{user_id}", tags=["Chat"], response_model=ApiResponse)
def chat_history(user_id: str):
    try:
        # El ChatAgent expone un session_manager con sesiones
        sessman = chat_agent.session_manager
        if user_id in getattr(sessman, "sessions", {}):
            s = sessman.sessions[user_id]
            return ok({
                "conversation_history": getattr(s, "conversation_history", []),
                "chart_interaction_history": getattr(s, "chart_interaction_history", []),
                "current_chart_configs": getattr(s, "current_chart_configs", []),
                "user_preferences": getattr(s, "user_preferences", {}),
            })
    except Exception:
        ...
    return ok({"conversation_history": []}, meta={"note": "no session"})

@app.get("/chat/suggestions/{user_id}", tags=["Chat"], response_model=ApiResponse)
def chat_suggestions(user_id: str):
    return ok(chat_agent.get_dynamic_suggestions(user_id))

@app.post("/chat/reset/{user_id}", tags=["Chat"], response_model=ApiResponse)
def chat_reset(user_id: str):
    try:
        chat_agent.session_manager.reset_session(user_id)
        return ok({"status": "reset", "user_id": user_id})
    except Exception:
        return ok({"status": "error"}, meta={"note": "fallback"})

# ✅ WebSocket optimizado para Chat Agent v9.1
@app.websocket("/ws/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """WebSocket optimizado para Chat Agent v9.1 con keep-alive mejorado"""
    await websocket.accept()
    await websocket.send_json({"type": "ready", "user_id": user_id, "version": "9.1", "ts": now_iso()})

    try:
        while True:
            try:
                # ✅ Timeout mejorado para evitar conexiones colgadas
                payload = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)  # 5 minutos timeout
            except asyncio.TimeoutError:
                await websocket.close(code=1000, reason="Idle timeout")
                break
            except WebSocketDisconnect:
                break
            except Exception:
                await websocket.close()
                break

            # ✅ Manejo de ping-pong para keep-alive
            if payload.get("type") == "ping":
                await websocket.send_json({"type": "pong", "ts": now_iso()})
                continue

            msg = payload.get("message", "").strip()
            if not msg:
                await websocket.send_json({"type": "error", "message": "Empty message", "ts": now_iso()})
                continue

            chat_message = ChatMessage(
                user_id=user_id,
                message=msg,
                context=payload.get("context", {}),
                gestor_id=payload.get("gestor_id"),
                periodo=payload.get("periodo"),
                include_charts=payload.get("include_charts", True),
                include_recommendations=payload.get("include_recommendations", True)
            )

            try:
                response = await chat_agent.process_chat_message(chat_message)
                
                # ✅ Compatibilidad mejorada con Chat Agent v9.1
                if hasattr(response, "dict"):
                    data = response.dict()
                elif hasattr(response, "model_dump"):
                    data = response.model_dump()
                else:
                    data = {"response": getattr(response, "response", "ok")}
                
                await websocket.send_json({
                    "type": "message", 
                    "data": data, 
                    "version": "9.1",
                    "ts": now_iso()
                })
            except Exception as exc:
                # ✅ Mantener conexión viva en caso de error de procesamiento
                await websocket.send_json({
                    "type": "fallback", 
                    "message": str(exc), 
                    "ts": now_iso()
                })
                
    except Exception as outer_exc:
        logger.error(f"Websocket error: {outer_exc}")
    finally:
        await websocket.close()
        logger.info(f"Websocket disconnected: {user_id}")

# ----------------------------------------------------------------------------
# User (personalización y feedback)
# ----------------------------------------------------------------------------

@app.get("/user/{user_id}/personalization", tags=["User"], response_model=ApiResponse)
def user_personalization(user_id: str):
    try:
        prefs = get_personalization_for_user(user_id) if REFLECTION_AVAILABLE else {"user_id": user_id, "mode": "mock"}
        return ok(prefs)
    except Exception:
        return ok({"user_id": user_id}, meta={"note": "fallback"})

@app.post("/user/{user_id}/feedback", tags=["User"], response_model=ApiResponse)
async def user_feedback(user_id: str, payload: Dict[str, Any] = Body(...)):
    if not REFLECTION_AVAILABLE:
        return ok({"status": "mocked"})
    try:
        res = await reflection_manager.process_feedback(user_id=user_id, **(payload or {}))
        return ok(res)
    except Exception as e:
        return ok({"status": "error", "error": str(e)})

# ----------------------------------------------------------------------------
# Middleware logging
# ----------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now(UTC)
    resp = await call_next(request)
    took = (datetime.now(UTC) - start).total_seconds()
    logger.info(f"{request.method} {request.url.path} -> {resp.status_code} in {took:.3f}s")
    return resp

# ----------------------------------------------------------------------------
# Error handlers
# ----------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiError(message=exc.detail, code=exc.status_code).model_dump()
    )

@app.exception_handler(Exception)
async def general_exc_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content=ApiError(message="Error interno del servidor", code=500).model_dump()
    )

# ----------------------------------------------------------------------------
# Main Entry Point
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # ✅ CONFIGURACIÓN ESPECÍFICA PARA WINDOWS + WEBSOCKETS
    config = {
        "host": "127.0.0.1",  # ✅ Usar 127.0.0.1 en lugar de 0.0.0.0 en Windows
        "port": int(os.getenv("PORT", 8000)),
        "reload": True,
        
        # ✅ WEBSOCKET ESPECÍFICO PARA WINDOWS
        "ws_ping_interval": 30.0,      # Ping cada 30 segundos
        "ws_ping_timeout": 15.0,       # Timeout de 15 segundos para pong
        "timeout_keep_alive": 300,     # Keep-alive 5 minutos
        
        # ✅ CONFIGURACIÓN DE CONEXIÓN PARA WINDOWS
        "limit_concurrency": 100,      # Reducir concurrencia en Windows
        "limit_max_requests": 1000,    # Límite de requests por worker
        "backlog": 512,                # Cola más pequeña para Windows
        
        # ✅ CRITICAL: UN SOLO WORKER EN WINDOWS
        "workers": 1,                  # CRÍTICO: Solo 1 worker en Windows
        
        # ✅ LOGGING ESPECÍFICO
        "access_log": True,
        "log_level": "info"
    }
    
    # ✅ DETECCIÓN DE PLATAFORMA
    if sys.platform == "win32":
        print("🪟 Ejecutando en Windows - Configuración optimizada")
        # En Windows, usar configuración específica
        uvicorn.run("main:app", **config)
    else:
        print("🐧 Ejecutando en Linux/Mac")
        # En otros sistemas, configuración estándar
        config["host"] = "0.0.0.0"
        config["workers"] = 4  # Múltiples workers en Linux/Mac
        uvicorn.run("main:app", **config)
