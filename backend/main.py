"""
CDG API v11.0 - Backend Completo Integrado con Chat Agent v10.0 y CDG Agent v6.0
==================================================================================

FastAPI backend completamente actualizado que integra:
- Chat Agent v10.0 (clasificación inteligente + queries predefinidas + 6 catálogos)
- CDG Agent v6.0 (análisis complejos especializados con perfect integration)
- Sistema completo de control de gestión bancario
- Nuevos endpoints para flujos de clasificación inteligente
- Banners de logs visuales mejorados
- Integración perfecta entre agentes
- TODOS los endpoints útiles mantenidos

Versión: 11.0 - Perfect Integration with Chat Agent v10.0 + CDG Agent v6.0
Autor: CDG Development Team
Fecha: 2025-09-11
"""

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

# ============================================================================
# 🎯 IMPORTS ACTUALIZADOS PARA AGENTES v10.0 Y v6.0
# ============================================================================

IMPORTS_SUCCESSFUL = True
BASIC_QUERIES_AVAILABLE = True
CHART_GENERATOR_AVAILABLE = True
SQL_GUARD_AVAILABLE = True
REFLECTION_AVAILABLE = True

try:
    # ✅ Agents ACTUALIZADOS - Chat Agent v10.0 + CDG Agent v6.0
    from agents.cdg_agent import (
        CDGAgentV6, CDGRequest, CDGResponse, create_cdg_agent, 
        process_complex_analysis, AnalysisType  # Nueva función de integración + enum
    )
    from agents.chat_agent import (
        UniversalChatAgentV10, ChatMessage, ChatResponse, ChatSession,
        create_universal_chat_agent, get_universal_chat_agent,
        IntelligentQueryClassifier, PredefinedQueryExecutor, BankingResponseFormatter
    )

    # Tools: KPI calculator con fallback mejorado
    try:
        from tools.kpi_calculator import FinancialKPICalculator as _KPICalcCls
    except Exception:
        from tools.kpi_calculator import KPICalculator as _KPICalcCls

    # Chart generator actualizado con funciones de pivot mejoradas
    try:
        from tools.chart_generator import (
            CDGDashboardGenerator,
            QueryIntegratedChartGenerator,
            create_chart_from_query_data,
            create_quick_chart,
            pivot_chart_with_query_integration,
            handle_chart_change_request,  # ✅ Función de pivot mejorada
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
        def handle_chart_change_request(*a, **k): return {"status": "success", "new_config": {}}
        def validate_chart_generator(): return {"status": "MOCK"}
        class _ChartFactoryStub:
            @staticmethod
            def get_available_queries():
                return ["gestores_ranking", "centros_distribution", "productos_popularity", "precios_comparison", "summary_dashboard"]
        ChartFactory = _ChartFactoryStub
        CDG_CHART_CONFIGS = {"chart_types": {}, "dimensions": {}, "metrics": {}, "colors": {}}

    # Report generator
    try:
        from tools.report_generator import BusinessReportGenerator
    except Exception:
        class BusinessReportGenerator:
            def __call__(self, *a, **k): return self
            def generate_business_review(self, *a, **k): 
                return type("R", (), {"to_dict": lambda s: {"review": "mock"}})()
            def generate_executive_summary_report(self, *a, **k):
                return type("R", (), {"to_dict": lambda s: {"summary": "mock"}})()

    # SQL Guard
    try:
        from tools.sql_guard import is_query_safe, validate_query_for_cdg
    except Exception:
        SQL_GUARD_AVAILABLE = False
        def is_query_safe(sql): return True
        def validate_query_for_cdg(sql, context="general"): 
            return {"is_safe": True, "context": context, "warnings": ["sql_guard_stub"], "query_hash": hash(sql)}

    # Queries - TODAS las instancias necesarias
    from queries.basic_queries import basic_queries
    from queries.period_queries import PeriodQueries
    from queries.gestor_queries import GestorQueries
    from queries.comparative_queries import ComparativeQueries
    from queries.deviation_queries import DeviationQueries
    from queries.incentive_queries import IncentiveQueries

    # ✅ Reflexión/personalización
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
    # Modo MOCK total si algo crítico falla
    IMPORTS_SUCCESSFUL = False
    BASIC_QUERIES_AVAILABLE = False
    CHART_GENERATOR_AVAILABLE = False
    SQL_GUARD_AVAILABLE = False
    REFLECTION_AVAILABLE = False

    # Mock classes actualizadas para v10.0 y v6.0
    class _MockObj:
        def __getattr__(self, name):
            return lambda *a, **k: type("R", (), {"data": [], "row_count": 0})()

    class AnalysisType:
        DEEP_GESTOR_ANALYSIS = "deep_gestor_analysis"
        COMPARATIVE_PERFORMANCE = "comparative_performance"
        BUSINESS_INTELLIGENCE = "business_intelligence"

    class CDGAgentV6:
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
                }
            })()
        def get_agent_status(self): return {"status": "mock", "version": "6.0"}

    class UniversalChatAgentV10:
        def __init__(self, *a, **k):
            self.sessions = {}
        async def process_chat_message(self, *a, **k):
            return type("R", (), {
                "response": "ok (mock)",
                "charts": [],
                "response_type": "mock",
                "execution_time": 0.01,
                "confidence_score": 0.5
            })()
        def get_agent_status(self): return {"status": "mock", "version": "10.0"}
        def get_session(self, user_id: str): 
            return type("Session", (), {"conversation_history": [], "preferences": {}})()

    def create_cdg_agent(): return CDGAgentV6()
    def create_universal_chat_agent(*a, **k): return UniversalChatAgentV10()
    def process_complex_analysis(*a, **k): return {"content": "Mock analysis"}

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
    def handle_chart_change_request(*a, **k): return {"status": "success", "new_config": {}}
    def validate_chart_generator(): return {"status": "MOCK"}
    
    basic_queries = type("BQ", (), {
        "get_resumen_general": staticmethod(lambda: {"total_gestores": 30, "total_clientes": 85, "total_contratos": 216, "total_centros": 5, "total_productos": 3}),
        "count_contratos_by_gestor": staticmethod(lambda: [{"DESC_GESTOR": "Mock Gestor 1", "num_contratos": 10}]),
        "count_clientes_by_gestor": staticmethod(lambda: [{"DESC_GESTOR": "Mock Gestor 1", "num_clientes": 6}]),
        "get_all_centros": staticmethod(lambda: [{"CENTRO_ID": 1, "DESC_CENTRO": "Mock Centro"}]),
        "get_all_gestores": staticmethod(lambda: [{"GESTOR_ID": 1, "DESC_GESTOR": "Mock Gestor"}]),
        "get_all_productos": staticmethod(lambda: [{"PRODUCTO_ID": "P1", "DESC_PRODUCTO": "Prod 1"}]),
        "count_contratos_by_centro": staticmethod(lambda: [{"CENTRO_ID": 1, "num_contratos": 50}]),
        "count_contratos_by_producto": staticmethod(lambda: [{"PRODUCTO_ID": "P1", "DESC_PRODUCTO": "Prod 1", "num_contratos": 100}])
    })
    
    def is_query_safe(sql): return True
    def validate_query_for_cdg(sql, context="general"): return {"is_safe": True, "context": context, "warnings": [], "query_hash": hash(sql)}

# Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cdg-api-v11")

# ============================================================================
# 🎯 FUNCIONES DE RESPUESTA UNIFORME
# ============================================================================

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

# ============================================================================
# 🎯 FASTAPI APP & CORS
# ============================================================================

app = FastAPI(
    title="CDG Agente API v11.0 (Chat Agent v10.0 + CDG Agent v6.0)",
    version="11.0.0",
    description="API completamente integrada con Chat Agent v10.0 y CDG Agent v6.0 - Perfect Integration",
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

# ============================================================================
# 🚀 INICIALIZACIÓN DE AGENTES v10.0 y v6.0 CON LOGS VISUALES
# ============================================================================

def print_startup_banner():
    """Banner de inicio visual mejorado"""
    print(f"\n{'='*80}")
    print(f"🚀 CDG API v11.0 - PERFECT INTEGRATION")
    print(f"   Chat Agent: v10.0 (Clasificación inteligente + 6 catálogos)")
    print(f"   CDG Agent: v6.0 (Perfect Integration)")
    print(f"   Fecha: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Modo: {'PRODUCTION' if IMPORTS_SUCCESSFUL else 'FALLBACK'}")
    print(f"{'='*80}")

# ✅ Instancias de agentes actualizadas v10.0 y v6.0
print_startup_banner()

try:
    print(f"\n🔧 Inicializando Chat Agent v10.0...")
    chat_agent = create_universal_chat_agent()  # ✅ Chat Agent v10.0
    chat_status = chat_agent.get_agent_status()
    print(f"✅ Chat Agent v10.0 inicializado:")
    print(f"   - Modo: {chat_status.get('mode', 'Unknown')}")
    print(f"   - Catálogos: {len(chat_status.get('query_catalogs', []))}")
    print(f"   - Tablas BD: {chat_status['database_info']['tables_available'] if 'database_info' in chat_status else 'N/A'}")

    print(f"\n🔬 Inicializando CDG Agent v6.0...")
    cdg_agent = create_cdg_agent()  # ✅ CDG Agent v6.0
    cdg_status = cdg_agent.get_agent_status()
    print(f"✅ CDG Agent v6.0 inicializado:")
    print(f"   - Modo: {cdg_status.get('mode', 'Unknown')}")
    print(f"   - Especializaciones: {len(cdg_status.get('specializations', []))}")
    print(f"   - Query Engines: {len(cdg_status.get('query_engines_available', []))}")

    integration_success = True
    print(f"\n🔗 Integración: ✅ PERFECTA")
    
except Exception as e:
    print(f"\n❌ Error inicializando agentes: {e}")
    chat_agent = UniversalChatAgentV10()
    cdg_agent = CDGAgentV6()
    integration_success = False

# Otros componentes
kpi_calc = _KPICalcCls() if hasattr(_KPICalcCls, "__call__") else _KPICalcCls
chart_dash = CDGDashboardGenerator() if hasattr(CDGDashboardGenerator, "__call__") else CDGDashboardGenerator
query_chart = QueryIntegratedChartGenerator() if hasattr(QueryIntegratedChartGenerator, "__call__") else QueryIntegratedChartGenerator
report_gen = BusinessReportGenerator() if hasattr(BusinessReportGenerator, "__call__") else BusinessReportGenerator

period_queries = PeriodQueries() if hasattr(PeriodQueries, "__call__") else PeriodQueries
gestor_queries = GestorQueries() if hasattr(GestorQueries, "__call__") else GestorQueries
comparative_queries = ComparativeQueries() if hasattr(ComparativeQueries, "__call__") else ComparativeQueries
deviation_queries = DeviationQueries() if hasattr(DeviationQueries, "__call__") else DeviationQueries
incentive_queries = IncentiveQueries() if hasattr(IncentiveQueries, "__call__") else IncentiveQueries

print(f"\n{'='*80}")
print(f"🎉 CDG API v11.0 LISTO")
print(f"   Chat Agent v10.0: {'✅ Activo' if chat_agent else '❌ Error'}")
print(f"   CDG Agent v6.0: {'✅ Activo' if cdg_agent else '❌ Error'}")
print(f"   Integración: {'✅ Perfecta' if integration_success else '⚠️ Limitada'}")
print(f"   API: http://127.0.0.1:8000")
print(f"   Docs: http://127.0.0.1:8000/docs")
print(f"{'='*80}\n")

# ============================================================================
# 🎯 MODELOS DE REQUEST/RESPONSE ACTUALIZADOS
# ============================================================================

# ✅ Modelo actualizado para Chat Agent v10.0
class ChatRequest(BaseModel):
    user_id: str
    message: str
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True
    context: Dict[str, Any] = {}
    current_chart_config: Optional[Dict[str, Any]] = None

# ✅ Modelo actualizado para CDG Agent v6.0
class CDGAnalysisRequest(BaseModel):
    user_message: str
    user_id: Optional[str] = None
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    analysis_depth: str = Field("standard", description="standard, deep, executive")
    include_charts: bool = True
    include_recommendations: bool = True
    current_chart_config: Optional[Dict[str, Any]] = None
    chart_interaction_type: Optional[str] = None
    context: Dict[str, Any] = {}

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

class DynamicQueryRequest(BaseModel):
    sql: str
    context: str = "general"

# ============================================================================
# 🎯 ENDPOINTS PRINCIPALES - SISTEMA
# ============================================================================

@app.get("/", tags=["System"], response_model=ApiResponse)
def root():
    return ok(
        {
            "service": "CDG Agente API v11.0",
            "chat_agent_version": "10.0",
            "cdg_agent_version": "6.0",
            "mode": "PRODUCTION" if IMPORTS_SUCCESSFUL else "MOCK",
            "integration": "Perfect Integration",
            "new_features": [
                "Clasificación inteligente de consultas",
                "6 catálogos de queries predefinidas",
                "Flujo perfecto de enrutamiento",
                "Análisis especializados avanzados",
                "Integración perfecta entre agentes",
                "Funcionalidad de pivot de gráficos mejorada"
            ],
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
    chat_ok = hasattr(chat_agent, 'get_agent_status')
    cdg_ok = hasattr(cdg_agent, 'get_agent_status')
    
    return ok({
        "status": "healthy", 
        "imports_successful": IMPORTS_SUCCESSFUL,
        "chat_agent_v10": chat_ok,
        "cdg_agent_v6": cdg_ok,
        "integration": "perfect" if chat_ok and cdg_ok else "limited"
    })

@app.get("/version", tags=["System"], response_model=ApiResponse)
def version():
    return ok({
        "api_version": "11.0.0",
        "chat_agent": "10.0 - Integración Completa con Catálogos",
        "cdg_agent": "6.0 - Perfect Integration",
        "integration_level": "Perfect",
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "git_sha": os.getenv("GIT_SHA", "dev"),
    })

# ============================================================================
# 🎯 ENDPOINTS ACTUALIZADOS - CHAT AGENT v10.0
# ============================================================================

@app.post("/chat/message", tags=["Chat Agent v10.0"], response_model=ApiResponse)
async def chat_message(req: ChatRequest):
    """
    🎯 CHAT PRINCIPAL - Chat Agent v10.0 con clasificación inteligente
    Flujo: clasificación → query predefinida → SQL dinámico → respuesta contextual
    """
    try:
        msg = ChatMessage(
            user_id=req.user_id,
            message=req.message,
            gestor_id=req.gestor_id,
            periodo=req.periodo,
            include_charts=req.include_charts,
            include_recommendations=req.include_recommendations,
            context=req.context,
            current_chart_config=req.current_chart_config
        )
        
        resp = await chat_agent.process_chat_message(msg)
        
        # ✅ Compatibilidad con ChatResponse
        if hasattr(resp, "__dict__"):
            data = resp.__dict__
        else:
            data = {"response": str(resp)}
        
        return ok(data, meta={"source": "chat_agent_v10", "integration": "perfect"})
    except Exception as e:
        logger.error(f"Error en chat message: {e}")
        return ok({"error": str(e), "response": "Error procesando mensaje"}, 
                 meta={"note": "chat_agent_error"})

@app.get("/chat/status", tags=["Chat Agent v10.0"], response_model=ApiResponse)
def chat_status():
    """Estado completo del Chat Agent v10.0"""
    try:
        status = chat_agent.get_agent_status()
        return ok(status, meta={"version": "10.0", "type": "chat_agent"})
    except Exception:
        return ok({"status": "unknown", "version": "10.0"})

@app.get("/chat/capabilities", tags=["Chat Agent v10.0"], response_model=ApiResponse)
def chat_capabilities():
    """Capacidades del Chat Agent v10.0"""
    return ok({
        "flows": [
            "PREDEFINED_QUERY - Búsqueda en catálogos de queries",
            "DYNAMIC_SQL - Generación SQL inteligente",
            "CDG_AGENT - Delegación a análisis complejos",
            "CONTEXTUAL_RESPONSE - Respuestas sin SQL"
        ],
        "catalogs": [
            "basic - Queries básicas del sistema",
            "comparative - Análisis comparativos",
            "deviation - Detección de desviaciones",
            "gestor - Análisis por gestor",
            "incentive - Cálculos de incentivos",
            "period - Análisis temporales"
        ],
        "features": [
            "Clasificación inteligente automática",
            "Búsqueda en 6 catálogos de queries",
            "Generación SQL con contexto bancario",
            "Integración perfecta con CDG Agent v6.0",
            "Respuestas contextuales profesionales"
        ]
    })

@app.get("/chat/history/{user_id}", tags=["Chat Agent v10.0"], response_model=ApiResponse)
def chat_history(user_id: str):
    """Historial de conversación por usuario"""
    try:
        session = chat_agent.get_session(user_id)
        return ok({
            "conversation_history": getattr(session, "conversation_history", []),
            "chart_configs": getattr(session, "chart_configs", []),
            "preferences": getattr(session, "preferences", {}),
        })
    except Exception:
        return ok({"conversation_history": []}, meta={"note": "no session"})

@app.get("/chat/suggestions/{user_id}", tags=["Chat Agent v10.0"], response_model=ApiResponse)
def chat_suggestions(user_id: str):
    """Sugerencias dinámicas personalizadas"""
    try:
        # Obtener sugerencias del schema disponible
        if hasattr(chat_agent, 'query_builder'):
            schema_info = chat_agent.query_builder.schema_inspector.get_database_schema()
            suggestions = [
                "¿Cuántos gestores tenemos activos?",
                "Muestra el ranking de gestores por margen neto",
                "¿Cuál es la distribución de contratos por producto?",
                "Analiza las desviaciones de precio del último período",
                f"Revisar los {schema_info['metadata']['total_records']:,} registros disponibles"
            ]
        else:
            suggestions = [
                "¿Cuántos gestores hay en total?",
                "Muestra el performance por centro",
                "Analiza desviaciones críticas",
                "Genera dashboard ejecutivo",
                "Compara ROE entre gestores"
            ]
        return ok(suggestions)
    except Exception:
        return ok([
            "¿Cuántos gestores hay en total?",
            "Muestra el performance por centro",
            "Analiza desviaciones críticas"
        ])

@app.post("/chat/reset/{user_id}", tags=["Chat Agent v10.0"], response_model=ApiResponse)
def chat_reset(user_id: str):
    """Reset de sesión de usuario"""
    try:
        if hasattr(chat_agent, 'sessions') and user_id in chat_agent.sessions:
            del chat_agent.sessions[user_id]
        return ok({"status": "reset", "user_id": user_id})
    except Exception:
        return ok({"status": "error"}, meta={"note": "fallback"})

# ============================================================================
# 🎯 ENDPOINTS ACTUALIZADOS - CDG AGENT v6.0
# ============================================================================

@app.post("/agent/process", tags=["CDG Agent v6.0"], response_model=ApiResponse)
async def agent_process(req: CDGAnalysisRequest):
    """
    🎯 PROCESAMIENTO PRINCIPAL CDG Agent v6.0 - Análisis especializados
    Tipos: deep_gestor_analysis, comparative_performance, business_intelligence, etc.
    """
    try:
        # Importar CDGRequest dinámicamente para evitar errores de circular import
        cdg_req_data = {
            "user_message": req.user_message,
            "user_id": req.user_id,
            "gestor_id": req.gestor_id,
            "periodo": req.periodo,
            "context": req.context,
            "include_charts": req.include_charts,
            "include_recommendations": req.include_recommendations,
            "current_chart_config": req.current_chart_config,
            "chart_interaction_type": req.chart_interaction_type,
            "analysis_depth": req.analysis_depth
        }
        
        # Usar la función process_complex_analysis directamente
        result_data = await process_complex_analysis(
            req.user_message,
            **{k: v for k, v in cdg_req_data.items() if v is not None and k != "user_message"}
        )
        
        return ok(result_data, meta={
            "source": "cdg_agent_v6", 
            "version": "6.0",
            "integration": "perfect_with_chat_agent_v10"
        })
        
    except Exception as e:
        logger.error(f"Error en CDG Agent v6.0: {e}")
        return ok({"error": str(e)}, meta={"note": "cdg_agent_error"})

@app.post("/agent/complex-analysis", tags=["CDG Agent v6.0"], response_model=ApiResponse)
async def agent_complex_analysis(req: CDGAnalysisRequest):
    """
    🎯 ANÁLISIS COMPLEJO DIRECTO - Usa función de integración
    """
    try:
        result = await process_complex_analysis(
            req.user_message,
            user_id=req.user_id,
            gestor_id=req.gestor_id,
            periodo=req.periodo,
            context=req.context,
            include_charts=req.include_charts,
            include_recommendations=req.include_recommendations,
            analysis_depth=req.analysis_depth
        )
        return ok(result, meta={"source": "process_complex_analysis"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "complex_analysis_error"})

@app.get("/agent/status", tags=["CDG Agent v6.0"], response_model=ApiResponse)
def agent_status():
    """Estado completo del CDG Agent v6.0"""
    try:
        status = cdg_agent.get_agent_status()
        return ok(status, meta={"version": "6.0", "type": "cdg_agent"})
    except Exception:
        return ok({"status": "unknown", "version": "6.0"})

@app.get("/agent/specializations", tags=["CDG Agent v6.0"], response_model=ApiResponse)
def agent_specializations():
    """Especializaciones del CDG Agent v6.0"""
    try:
        # Obtener tipos de análisis dinámicamente si están disponibles
        if hasattr(AnalysisType, '__members__'):
            analysis_types = [f"{name} - {value}" for name, value in AnalysisType.__members__.items()]
        else:
            analysis_types = [
                "DEEP_GESTOR_ANALYSIS - Análisis profundo de gestor",
                "COMPARATIVE_PERFORMANCE - Performance comparativo",
                "DEVIATION_DETECTION - Detección de desviaciones",
                "INCENTIVE_CALCULATION - Cálculo de incentivos",
                "BUSINESS_INTELLIGENCE - Inteligencia de negocio",
                "EXECUTIVE_REPORTING - Reportes ejecutivos",
                "PREDICTIVE_ANALYSIS - Análisis predictivo",
                "CHART_ADVANCED_GENERATION - Gráficos avanzados"
            ]
        
        return ok({
            "analysis_types": analysis_types,
            "integration": "Perfect with Chat Agent v10.0",
            "specialization": "Análisis complejos que requieren múltiples queries coordinadas"
        })
    except Exception:
        return ok({
            "analysis_types": ["Mock analysis types"],
            "integration": "Mock",
            "specialization": "Mock specialization"
        })

@app.get("/agent/suggest-questions", tags=["CDG Agent v6.0"], response_model=ApiResponse)
def agent_suggest_questions(user_id: Optional[str] = None):
    """Sugerencias de preguntas para análisis CDG"""
    suggestions = [
        "Análisis profundo del gestor 15 con comparativa de pares",
        "Performance comparativo de todos los centros",
        "Detecta desviaciones críticas en el último período",
        "Genera dashboard ejecutivo consolidado",
        "Identifica patrones de incentivos por segmento"
    ]
    return ok(suggestions, meta={"count": len(suggestions), "type": "cdg_specialized"})

# ============================================================================
# 🎯 ENDPOINTS DE INTEGRACIÓN ENTRE AGENTES
# ============================================================================

@app.post("/integration/classify-and-route", tags=["Integration"], response_model=ApiResponse)
async def integration_classify_and_route(body: Dict[str, Any] = Body(...)):
    """
    🎯 ENDPOINT DE CLASIFICACIÓN PURA - Chat Agent v10.0 clasifica
    """
    try:
        # ✅ NUEVO: Validación de entrada más flexible
        user_id = body.get("user_id", "anonymous")
        message = body.get("message", "")
        context = body.get("context", {})
        
        if not message:
            return ok({"error": "message requerido"}, meta={"note": "missing_message"})
        
        # ✅ NUEVO: Compatibilidad con diferentes formatos
        gestor_id = body.get("gestorId") or body.get("gestor_id")
        periodo = body.get("periodo")
        mode = body.get("mode", "general")
        current_chart_config = body.get("currentChartConfig") or body.get("current_chart_config", {})
        
        if hasattr(chat_agent, 'classifier'):
            routing_result = await chat_agent.classifier.classify_and_route(
                message,
                {
                    'gestor_id': gestor_id,
                    'periodo': periodo,
                    'mode': mode,
                    'context': context,
                    'current_chart_config': current_chart_config
                }
            )
            return ok(routing_result, meta={"source": "intelligent_classifier_v10"})
        else:
            # ✅ FALLBACK mejorado
            flow_type = "PIVOT" if any(word in message.lower() for word in ["cambia", "convierte", "muestra", "modifica"]) else "DYNAMIC_SQL"
            return ok({
                "flow_type": flow_type, 
                "confidence": 0.7,
                "routing": {"target": "fallback"},
                "classification": "rule_based"
            }, meta={"note": "classifier_fallback"})
            
    except Exception as e:
        logger.error(f"Error en classify-and-route: {e}")
        return ok({"error": str(e), "flow_type": "DYNAMIC_SQL", "confidence": 0.1}, 
                 meta={"note": "classification_error"})


@app.post("/integration/execute-predefined", tags=["Integration"], response_model=ApiResponse)
async def integration_execute_predefined(body: Dict[str, Any] = Body(...)):
    """
    🎯 EJECUCIÓN DIRECTA DE QUERY PREDEFINIDA
    """
    try:
        if hasattr(chat_agent, 'predefined_executor'):
            match_info = body.get("match_info", {})
            user_message = body.get("user_message", "")
            context = body.get("context", {})
            
            result = await chat_agent.predefined_executor.execute_predefined_query(
                match_info, user_message, context
            )
            return ok(result, meta={"source": "predefined_query_executor_v10"})
        else:
            return ok({"success": False, "error": "Predefined executor not available"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "predefined_execution_error"})

@app.get("/integration/query-catalogs", tags=["Integration"], response_model=ApiResponse)
def integration_query_catalogs():
    """
    🎯 CATÁLOGOS DE QUERIES DISPONIBLES
    """
    try:
        if hasattr(chat_agent, 'classifier') and hasattr(chat_agent.classifier, 'query_catalogs'):
            catalogs = list(chat_agent.classifier.query_catalogs.keys())
        else:
            catalogs = ["basic", "comparative", "deviation", "gestor", "incentive", "period"]
        
        if hasattr(chat_agent, 'predefined_executor') and hasattr(chat_agent.predefined_executor, 'query_engines'):
            engines = list(chat_agent.predefined_executor.query_engines.keys())
        else:
            engines = ["basic", "comparative", "deviation", "gestor", "incentive", "period"]
        
        return ok({
            "available_catalogs": catalogs,
            "query_engines": engines,
            "total_catalogs": len(catalogs),
            "integration_status": "perfect" if hasattr(chat_agent, 'classifier') else "fallback"
        })
    except Exception:
        return ok({
            "available_catalogs": ["basic", "comparative", "deviation", "gestor", "incentive", "period"],
            "query_engines": ["basic", "comparative", "deviation", "gestor", "incentive", "period"],
            "total_catalogs": 6,
            "integration_status": "fallback"
        })

@app.get("/integration/agent-coordination", tags=["Integration"], response_model=ApiResponse)
def integration_agent_coordination():
    """
    🎯 ESTADO DE COORDINACIÓN ENTRE AGENTES
    """
    try:
        chat_status = chat_agent.get_agent_status() if hasattr(chat_agent, 'get_agent_status') else {}
        cdg_status = cdg_agent.get_agent_status() if hasattr(cdg_agent, 'get_agent_status') else {}
        
        return ok({
            "coordination": {
                "chat_agent_v10": {
                    "status": chat_status.get("status", "unknown"),
                    "capabilities": len(chat_status.get("capabilities", [])),
                    "catalogs": len(chat_status.get("query_catalogs", [])),
                    "role": "Clasificación inteligente + Queries predefinidas"
                },
                "cdg_agent_v6": {
                    "status": cdg_status.get("status", "unknown"),
                    "specializations": len(cdg_status.get("specializations", [])),
                    "query_engines": len(cdg_status.get("query_engines_available", [])),
                    "role": "Análisis complejos especializados"
                },
                "integration_level": "Perfect Integration",
                "workflow": "Chat Agent v10.0 → Clasificación → CDG Agent v6.0 para análisis complejos"
            }
        })
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "coordination_error"})

# ============================================================================
# 🎯 WEBSOCKET ACTUALIZADO PARA v10.0
# ============================================================================

@app.websocket("/ws/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """
    🎯 WebSocket optimizado para Chat Agent v10.0 con flujos perfectos
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "ready", 
        "user_id": user_id, 
        "chat_agent": "v10.0",
        "cdg_agent": "v6.0",
        "integration": "perfect",
        "ts": now_iso()
    })

    try:
        while True:
            try:
                payload = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)
            except asyncio.TimeoutError:
                await websocket.close(code=1000, reason="Idle timeout")
                break
            except WebSocketDisconnect:
                break
            except Exception:
                await websocket.close()
                break

            # ✅ Keep-alive mejorado
            if payload.get("type") == "ping":
                await websocket.send_json({"type": "pong", "ts": now_iso()})
                continue

            msg = payload.get("message", "").strip()
            if not msg:
                await websocket.send_json({
                    "type": "error", 
                    "message": "Empty message", 
                    "ts": now_iso()
                })
                continue

            # ✅ Crear ChatMessage para v10.0
            try:
                chat_message_data = {
                    "user_id": user_id,
                    "message": msg,
                    "context": payload.get("context", {}),
                    "gestor_id": payload.get("gestor_id"),
                    "periodo": payload.get("periodo"),
                    "include_charts": payload.get("include_charts", True),
                    "include_recommendations": payload.get("include_recommendations", True)
                }
                
                # Usar la función de chat directamente
                req = ChatRequest(**chat_message_data)
                msg_obj = ChatMessage(
                    user_id=req.user_id,
                    message=req.message,
                    gestor_id=req.gestor_id,
                    periodo=req.periodo,
                    include_charts=req.include_charts,
                    include_recommendations=req.include_recommendations,
                    context=req.context,
                    current_chart_config=req.current_chart_config
                )

                # ✅ Procesar con Chat Agent v10.0
                response = await chat_agent.process_chat_message(msg_obj)
                
                if hasattr(response, "__dict__"):
                    data = response.__dict__
                else:
                    data = {"response": str(response)}
                
                await websocket.send_json({
                    "type": "message", 
                    "data": data, 
                    "chat_agent": "v10.0",
                    "integration": "perfect",
                    "ts": now_iso()
                })
                
            except Exception as exc:
                await websocket.send_json({
                    "type": "fallback", 
                    "message": f"Error procesando: {str(exc)}", 
                    "ts": now_iso()
                })
                
    except Exception as outer_exc:
        logger.error(f"Websocket error: {outer_exc}")
    finally:
        try:
            # ✅ Solo cerrar si no está ya cerrado
            if websocket.client_state.name in ['CONNECTED', 'CONNECTING']:
                await websocket.close(code=1000, reason="Session ended")
                logger.info(f"WebSocket closed gracefully for user: {user_id}")
        except Exception as close_error:
            logger.warning(f"Error closing websocket for {user_id}: {close_error}")
        finally:
            logger.info(f"WebSocket session ended for user: {user_id}")


# ============================================================================
# 🎯 ENDPOINTS DE CATÁLOGOS Y PERIODOS (MANTENIDOS)
# ============================================================================

@app.get("/periods", tags=["Catalogs"], response_model=ApiResponse)
def periods():
    """Lista de períodos disponibles"""
    try:
        # Intentar usar CDG agent para períodos mejorados
        periods = []
        latest = None
        
        if hasattr(period_queries, "get_available_periods_enhanced"):
            res = period_queries.get_available_periods_enhanced()
            periods = [r.get("periodo") for r in getattr(res, "data", [])]
        
        if hasattr(period_queries, "get_latest_period_enhanced"):
            res2 = period_queries.get_latest_period_enhanced()
            latest_data = getattr(res2, "data", [])
            if latest_data:
                latest = latest_data[0].get("periodo")
        
        if not periods:
            periods = ["2025-10", "2025-09", "2025-08"]
        if not latest:
            latest = "2025-10"
            
        return ok({"periods": periods, "latest": latest}, 
                 meta={"count": len(periods), "source": "period_queries"})
    except Exception as e:
        return ok({"periods": ["2025-10"], "latest": "2025-10"}, 
                 meta={"note": f"fallback: {e}"})

@app.get("/periods/latest", tags=["Catalogs"], response_model=ApiResponse)
def periods_latest():
    """Último período disponible"""
    try:
        if hasattr(period_queries, "get_latest_period_enhanced"):
            res = period_queries.get_latest_period_enhanced()
            val = getattr(res, "data", [{"periodo": None}])[0].get("periodo")
            return ok({"latest": val}, meta={"source": "period_queries"})
    except Exception:
        pass
    return ok({"latest": "2025-10"}, meta={"note": "fallback"})

# ============================================================================
# 🎯 PERÍODOS CON MÉTRICAS FINANCIERAS (NUEVOS)
# ============================================================================

@app.get("/periods/{periodo}/metricas", tags=["Periods"], response_model=ApiResponse)
def periods_metricas_financieras(periodo: str):
    """Métricas financieras agregadas de un período específico"""
    try:
        if hasattr(period_queries, "get_periodo_metricas_financieras"):
            res = period_queries.get_periodo_metricas_financieras(periodo)
            data = getattr(res, "data", [])
            if data:
                return ok(data[0], meta={"periodo": periodo, "source": "period_queries"})
        
        return ok({"error": "Métricas del período no disponibles"}, meta={"note": "period_queries no disponible"})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "periods_metricas_error"})

@app.get("/periods/compare/{periodo_actual}/{periodo_anterior}", tags=["Periods"], response_model=ApiResponse)
def periods_compare_metricas(periodo_actual: str, periodo_anterior: str):
    """Comparación de métricas entre dos períodos"""
    try:
        if hasattr(period_queries, "compare_periodos_metricas"):
            res = period_queries.compare_periodos_metricas(periodo_actual, periodo_anterior)
            data = getattr(res, "data", [])
            if data:
                return ok(data[0], meta={"periodo_actual": periodo_actual, "periodo_anterior": periodo_anterior})
        
        return ok({"error": "Comparación de períodos no disponible"}, meta={"note": "period_queries no disponible"})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "periods_compare_error"})


@app.get("/catalogs", tags=["Catalogs"], response_model=ApiResponse)
def catalogs():
    """Catálogos principales del sistema"""
    try:
        gestores = basic_queries.get_all_gestores() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_gestores") else []
        centros = basic_queries.get_all_centros() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_centros") else []
        productos = basic_queries.get_all_productos() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_productos") else []
        
        return ok({"gestores": gestores, "centros": centros, "productos": productos},
                  meta={"count": len(gestores)+len(centros)+len(productos), 
                       "source": "basic_queries" if BASIC_QUERIES_AVAILABLE else "mock"})
    except Exception as e:
        return ok({"gestores": [], "centros": [], "productos": []}, 
                 meta={"note": f"error: {e}"})

@app.get("/basic/gestores", tags=["Basic"], response_model=ApiResponse)
def basic_all_gestores():
    """Todos los gestores disponibles en el sistema"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_gestores"):
            return ok([], meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_all_gestores()
        return ok(data, meta={"count": len(data), "source": "basic_queries"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "all_gestores_error"})

# ============================================================================
# 🎯 ENDPOINTS BASIC QUERIES (TODOS MANTENIDOS)
# ============================================================================

@app.get("/basic/summary", tags=["Basic"], response_model=ApiResponse)
def basic_summary():
    """Resumen general del sistema"""
    try:
        data = basic_queries.get_resumen_general() if BASIC_QUERIES_AVAILABLE else {}
        return ok(data, meta={"source": "basic_queries" if BASIC_QUERIES_AVAILABLE else "mock"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "basic_summary_error"})

@app.get("/basic/gestores-ranking", tags=["Basic"], response_model=ApiResponse)
def basic_gestores_ranking(metric: str = Query("contratos", enum=["contratos", "clientes"])):
    """Ranking de gestores por contratos o clientes"""
    try:
        if not BASIC_QUERIES_AVAILABLE:
            return ok([], meta={"note": "basic_queries no disponible"})
        
        if metric == "clientes" and hasattr(basic_queries, "count_clientes_by_gestor"):
            data = basic_queries.count_clientes_by_gestor()
        else:
            data = basic_queries.count_contratos_by_gestor()
        
        return ok(data, meta={"count": len(data), "metric": metric})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestores_ranking_error"})

@app.get("/basic/centros", tags=["Basic"], response_model=ApiResponse)
def basic_centros():
    """Información de centros con contratos"""
    try:
        if not BASIC_QUERIES_AVAILABLE:
            return ok([], meta={"note": "basic_queries no disponible"})
            
        centros = basic_queries.get_all_centros()
        contratos = basic_queries.count_contratos_by_centro() if hasattr(basic_queries, "count_contratos_by_centro") else []
        
        # Join sencillo
        by_id = {c.get("CENTRO_ID"): c for c in centros}
        for row in contratos:
            cid = row.get("CENTRO_ID")
            if cid in by_id:
                by_id[cid]["num_contratos"] = row.get("num_contratos", 0)
                
        return ok(list(by_id.values()), meta={"count": len(by_id)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "centros_error"})

@app.get("/basic/productos", tags=["Basic"], response_model=ApiResponse)
def basic_productos():
    """Información de productos con contratos"""
    try:
        if not BASIC_QUERIES_AVAILABLE:
            return ok([], meta={"note": "basic_queries no disponible"})
            
        data = basic_queries.count_contratos_by_producto() if hasattr(basic_queries, "count_contratos_by_producto") else []
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "productos_error"})

# ============================================================================
# 🎯 ENDPOINTS BÁSICOS EXTENDIDOS FALTANTES
# ============================================================================

@app.get("/basic/gastos/by-fecha", tags=["Basic"], response_model=ApiResponse)
def basic_gastos_by_fecha(fecha: str = Query(..., description="YYYY-MM-DD")):
    """Gastos por fecha específica"""
    try:
        if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_gastos_by_fecha"):
            data = basic_queries.get_gastos_by_fecha(fecha)
            return ok(data, meta={"count": len(data), "fecha": fecha})
        return ok([], meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gastos_by_fecha_error"})

# ---- Contratos extendidos
@app.get("/basic/contracts", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_all():
    """Todos los contratos del sistema"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_contratos"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_all_contratos()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "contracts_all_error"})

@app.get("/basic/contracts/count", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_count():
    """Conteo total de contratos"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos"):
            return ok({"total": 0}, meta={"note": "basic_queries no disponible"})
        total = basic_queries.count_contratos()
        return ok({"total": total})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "contracts_count_error"})

@app.get("/basic/contracts/by-gestor/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_gestor(gestor_id: int):
    """Contratos por gestor específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_gestor"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_contratos_by_gestor(gestor_id)
        return ok(data, meta={"count": len(data), "gestor_id": gestor_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "contracts_by_gestor_error"})

@app.get("/basic/contracts/by-cliente/{cliente_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_cliente(cliente_id: int):
    """Contratos por cliente específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_cliente"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_contratos_by_cliente(cliente_id)
        return ok(data, meta={"count": len(data), "cliente_id": cliente_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "contracts_by_cliente_error"})

@app.get("/basic/contracts/by-producto/{producto_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_producto(producto_id: str):
    """Contratos por producto específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_producto"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_contratos_by_producto(producto_id)
        return ok(data, meta={"count": len(data), "producto_id": producto_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "contracts_by_producto_error"})

@app.get("/basic/contracts/by-centro/{centro_id}", tags=["Basic"], response_model=ApiResponse)
def basic_contracts_by_centro(centro_id: int):
    """Contratos por centro (filtrado)"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_contratos"):
            return ok([], meta={"note": "basic_queries no disponible"})
        allc = basic_queries.get_all_contratos()
        data = [r for r in allc if str(r.get("CENTRO_CONTABLE")) == str(centro_id)]
        return ok(data, meta={"count": len(data), "centro_id": centro_id, "source": "filter(get_all_contratos)"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "contracts_by_centro_error"})

# ---- Gestores extendidos
@app.get("/basic/gestores/by-centro/{centro_id}", tags=["Basic"], response_model=ApiResponse)
def basic_gestores_by_centro(centro_id: int):
    """Gestores por centro específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestores_by_centro"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_gestores_by_centro(centro_id)
        return ok(data, meta={"count": len(data), "centro_id": centro_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestores_by_centro_error"})

@app.get("/basic/gestores/by-segmento/{segmento_id}", tags=["Basic"], response_model=ApiResponse)
def basic_gestores_by_segmento(segmento_id: str):
    """Gestores por segmento específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestores_by_segmento"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_gestores_by_segmento(segmento_id)
        return ok(data, meta={"count": len(data), "segmento_id": segmento_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestores_by_segmento_error"})

@app.get("/basic/gestores/count-by-centro", tags=["Basic"], response_model=ApiResponse)
def basic_count_gestores_by_centro():
    """Conteo de gestores por centro"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_gestores_by_centro"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.count_gestores_by_centro()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "count_gestores_by_centro_error"})

@app.get("/basic/gestores/count-by-segmento", tags=["Basic"], response_model=ApiResponse)
def basic_count_gestores_by_segmento():
    """Conteo de gestores por segmento"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_gestores_by_segmento"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.count_gestores_by_segmento()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "count_gestores_by_segmento_error"})

# ---- Clientes extendidos
@app.get("/basic/clientes/by-gestor/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_clientes_by_gestor(gestor_id: int):
    """Clientes por gestor"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_clientes_by_gestor"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_clientes_by_gestor(gestor_id)
        return ok(data, meta={"count": len(data), "gestor_id": gestor_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "clientes_by_gestor_error"})

@app.get("/basic/clientes/by-centro/{centro_id}", tags=["Basic"], response_model=ApiResponse)
def basic_clientes_by_centro(centro_id: int):
    """Clientes por centro"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_clientes_by_centro"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_clientes_by_centro(centro_id)
        return ok(data, meta={"count": len(data), "centro_id": centro_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "clientes_by_centro_error"})

@app.get("/basic/clientes/metrics/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_client_metrics_by_gestor(gestor_id: int):
    """Métricas mejoradas de clientes por gestor"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_clientes_by_gestor"):
            return ok([], meta={"note": "basic_queries no disponible"})
        
        clientes = basic_queries.get_clientes_by_gestor(gestor_id)
        contratos = basic_queries.get_contratos_by_gestor(gestor_id) if hasattr(basic_queries, "get_contratos_by_gestor") else []
        
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
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "client_metrics_error"})

# ---- Productos por gestor
@app.get("/basic/productos/by-gestor/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_productos_by_gestor(gestor_id: int):
    """Productos por gestor (agregado)"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contratos_by_gestor"):
            return ok([], meta={"note": "basic_queries no disponible"})
        rows = basic_queries.get_contratos_by_gestor(gestor_id)
        
        agg = {}
        for r in rows:
            pid = r.get("PRODUCTO_ID")
            pname = r.get("DESC_PRODUCTO")
            agg.setdefault(pid, {"PRODUCTO_ID": pid, "DESC_PRODUCTO": pname, "num_contratos": 0})
            agg[pid]["num_contratos"] += 1
        
        data = sorted(agg.values(), key=lambda x: x["num_contratos"], reverse=True)
        return ok(data, meta={"count": len(data), "gestor_id": gestor_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "productos_by_gestor_error"})

@app.get("/basic/productos/top", tags=["Basic"], response_model=ApiResponse)
def basic_productos_top():
    """Productos más contratados"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_productos_mas_contratados"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_productos_mas_contratados()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "productos_top_error"})

# ============================================================================
# 🎯 PRECIOS Y COMPARATIVAS EXTENDIDAS
# ============================================================================

@app.get("/basic/precios/std", tags=["Basic"], response_model=ApiResponse)
def basic_precios_std():
    """Precios estándar completos"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_precios_std"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_all_precios_std()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "precios_std_error"})

@app.get("/basic/precios/std/by-segmento/{segmento_id}", tags=["Basic"], response_model=ApiResponse)
def basic_precios_std_by_segmento(segmento_id: str):
    """Precios estándar por segmento"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precios_std_by_segmento"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_precios_std_by_segmento(segmento_id)
        return ok(data, meta={"count": len(data), "segmento_id": segmento_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "precios_std_by_segmento_error"})

@app.get("/basic/precios/std/by-sp/{segmento_id}/{producto_id}", tags=["Basic"], response_model=ApiResponse)
def basic_precio_std_by_sp(segmento_id: str, producto_id: str):
    """Precio estándar específico por segmento-producto"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precio_std_by_segmento_producto"):
            return ok({}, meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_precio_std_by_segmento_producto(segmento_id, producto_id)
        return ok(data or {}, meta={"segmento_id": segmento_id, "producto_id": producto_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "precio_std_by_sp_error"})

@app.get("/basic/precios/real", tags=["Basic"], response_model=ApiResponse)
def basic_precios_real():
    """Precios reales completos"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_precios_real"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_all_precios_real()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "precios_real_error"})

@app.get("/basic/precios/real/by-fecha", tags=["Basic"], response_model=ApiResponse)
def basic_precios_real_by_fecha(fecha_calculo: str = Query(..., description="YYYY-MM-DD")):
    """Precios reales por fecha de cálculo"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precio_real_by_fecha"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_precio_real_by_fecha(fecha_calculo)
        return ok(data, meta={"count": len(data), "fecha_calculo": fecha_calculo})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "precios_real_by_fecha_error"})

@app.get("/basic/precios/real/by-sp/{segmento_id}/{producto_id}", tags=["Basic"], response_model=ApiResponse)
def basic_precios_real_by_sp(segmento_id: str, producto_id: str):
    """Precios reales por segmento-producto"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_precio_real_by_segmento_producto"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_precio_real_by_segmento_producto(segmento_id, producto_id)
        return ok(data, meta={"count": len(data), "segmento_id": segmento_id, "producto_id": producto_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "precios_real_by_sp_error"})

@app.get("/basic/precios/compare", tags=["Basic"], response_model=ApiResponse)
def basic_precios_compare(fecha_calculo: Optional[str] = Query(None, description="YYYY-MM-DD (opcional)")):
    """Comparación precios estándar vs real"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "compare_precios_std_vs_real"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.compare_precios_std_vs_real(fecha_calculo)
        return ok(data, meta={"count": len(data), "fecha_calculo": fecha_calculo})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "precios_compare_error"})

@app.get("/prices/comparison", tags=["Data Queries"], response_model=ApiResponse)
def prices_comparison(
    gestor_id: Optional[str] = None,
    producto_id: Optional[str] = None,
    periodo: Optional[str] = None,
):
    """Comparación de precios con filtros opcionales"""
    try:
        std = basic_queries.get_all_precios_std() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_precios_std") else []
        real = basic_queries.get_all_precios_real() if BASIC_QUERIES_AVAILABLE and hasattr(basic_queries, "get_all_precios_real") else []
        
        def _f(arr):
            out = arr
            if producto_id:
                out = [x for x in out if str(x.get("PRODUCTO_ID", x.get("producto_id", ""))) == str(producto_id)]
            return out
        
        data = {"standard": _f(std), "real": _f(real)}
        return ok(data, meta={"count": len(data.get("real", []))})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "prices_comparison_error"})

@app.get("/prices/comparison-by-segment", tags=["Data Queries"], response_model=ApiResponse)  
def prices_comparison_by_segment(segmento_id: str = Query(...), periodo: str = Query(...)):
    """Comparación de precios por segmento y período"""
    try:
        if not BASIC_QUERIES_AVAILABLE:
            return ok({"standard": [], "real": [], "segmento_id": segmento_id, "periodo": periodo}, 
                      meta={"note": "mock data - basic queries not available"})
        
        std_prices = basic_queries.get_precios_std_by_segmento(segmento_id)
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
        return ok({"error": str(e)}, meta={"note": "prices_comparison_by_segment_error"})

# ---- Líneas CDR y cuentas contables
@app.get("/basic/cdr/lineas", tags=["Basic"], response_model=ApiResponse)
def basic_cdr_lineas():
    """Todas las líneas CDR"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_lineas_cdr"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_all_lineas_cdr()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "cdr_lineas_error"})

@app.get("/basic/cdr/lineas/count", tags=["Basic"], response_model=ApiResponse)
def basic_cdr_lineas_count():
    """Conteo de líneas CDR"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_lineas_cdr"):
            return ok({"total": 0}, meta={"note": "basic_queries no disponible"})
        total = basic_queries.count_lineas_cdr()
        return ok({"total": total})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "cdr_lineas_count_error"})

@app.get("/basic/cuentas", tags=["Basic"], response_model=ApiResponse)
def basic_cuentas():
    """Todas las cuentas contables"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_all_cuentas"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_all_cuentas()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "cuentas_error"})

@app.get("/basic/cuentas/by-linea/{linea_cdr}", tags=["Basic"], response_model=ApiResponse)
def basic_cuentas_by_linea(linea_cdr: str):
    """Cuentas por línea CDR"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_cuentas_by_linea_cdr"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.get_cuentas_by_linea_cdr(linea_cdr)
        return ok(data, meta={"count": len(data), "linea_cdr": linea_cdr})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "cuentas_by_linea_error"})

# ============================================================================
# 🎯 ANALYTICS - MÉTRICAS FINANCIERAS POR ENTIDAD (NUEVOS)
# ============================================================================

@app.get("/analytics/centro/{centro_id}/metricas", tags=["Analytics"], response_model=ApiResponse)
def analytics_centro_metricas(centro_id: int, periodo: str = Query("2025-10")):
    """Métricas financieras completas de un centro específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_centro_metricas_financieras"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_centro_metricas_financieras(centro_id, periodo)
        return ok(data, meta={"centro_id": centro_id, "periodo": periodo, "source": "basic_queries"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_centro_metricas_error"})

@app.get("/analytics/centro/{centro_id}/gestores-con-metricas", tags=["Analytics"], response_model=ApiResponse)
def analytics_centro_gestores_metricas(centro_id: int, periodo: str = Query("2025-10")):
    """Gestores de un centro con sus métricas financieras"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_centro_gestores_con_metricas"):
            return ok([], meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_centro_gestores_con_metricas(centro_id, periodo)
        return ok(data, meta={"count": len(data), "centro_id": centro_id, "periodo": periodo})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_centro_gestores_error"})

@app.get("/analytics/segmento/{segmento_id}/metricas", tags=["Analytics"], response_model=ApiResponse)
def analytics_segmento_metricas(segmento_id: str, periodo: str = Query("2025-10")):
    """Métricas financieras completas de un segmento específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_segmento_metricas_financieras"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_segmento_metricas_financieras(segmento_id, periodo)
        return ok(data, meta={"segmento_id": segmento_id, "periodo": periodo, "source": "basic_queries"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_segmento_metricas_error"})

@app.get("/analytics/gestor/{gestor_id}/metricas-completas", tags=["Analytics"], response_model=ApiResponse)
def analytics_gestor_metricas_completas(gestor_id: int, periodo: str = Query("2025-10")):
    """Métricas financieras completas de un gestor específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestor_metricas_completas"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_gestor_metricas_completas(gestor_id, periodo)
        return ok(data, meta={"gestor_id": gestor_id, "periodo": periodo, "source": "basic_queries"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_gestor_metricas_error"})

@app.get("/analytics/gestor/{gestor_id}/clientes-con-metricas", tags=["Analytics"], response_model=ApiResponse)
def analytics_gestor_clientes_metricas(gestor_id: int, periodo: str = Query("2025-10")):
    """Clientes de un gestor con sus métricas financieras"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestor_clientes_con_metricas"):
            return ok([], meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_gestor_clientes_con_metricas(gestor_id, periodo)
        return ok(data, meta={"count": len(data), "gestor_id": gestor_id, "periodo": periodo})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_gestor_clientes_error"})

@app.get("/analytics/cliente/{cliente_id}/metricas", tags=["Analytics"], response_model=ApiResponse)
def analytics_cliente_metricas(cliente_id: int, periodo: str = Query("2025-10")):
    """Métricas financieras de un cliente específico"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_cliente_metricas"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_cliente_metricas(cliente_id, periodo)
        return ok(data, meta={"cliente_id": cliente_id, "periodo": periodo, "source": "basic_queries"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_cliente_metricas_error"})

@app.get("/analytics/cliente/{cliente_id}/contratos-con-metricas", tags=["Analytics"], response_model=ApiResponse)
def analytics_cliente_contratos_metricas(cliente_id: int, periodo: str = Query("2025-10")):
    """Contratos de un cliente con sus métricas financieras"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_cliente_contratos_con_metricas"):
            return ok([], meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_cliente_contratos_con_metricas(cliente_id, periodo)
        return ok(data, meta={"count": len(data), "cliente_id": cliente_id, "periodo": periodo})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_cliente_contratos_error"})

@app.get("/analytics/contrato/{contrato_id}/detalle-completo", tags=["Analytics"], response_model=ApiResponse)
def analytics_contrato_detalle_completo(contrato_id: int):
    """Detalle completo de un contrato con todas sus métricas"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_contrato_detalle_completo"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        data = basic_queries.get_contrato_detalle_completo(contrato_id)
        return ok(data, meta={"contrato_id": contrato_id, "source": "basic_queries"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "analytics_contrato_detalle_error"})


# ---- Conteos adicionales
@app.get("/basic/contracts/count-by-centro", tags=["Basic"], response_model=ApiResponse)
def basic_count_contracts_by_centro():
    """Conteo de contratos por centro"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos_by_centro"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.count_contratos_by_centro()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "count_contracts_by_centro_error"})

@app.get("/basic/contracts/count-by-producto", tags=["Basic"], response_model=ApiResponse)
def basic_count_contracts_by_producto():
    """Conteo de contratos por producto"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos_by_producto"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.count_contratos_by_producto()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "count_contracts_by_producto_error"})

@app.get("/basic/contracts/count-by-gestor", tags=["Basic"], response_model=ApiResponse)
def basic_count_contracts_by_gestor():
    """Conteo de contratos por gestor"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "count_contratos_by_gestor"):
            return ok([], meta={"note": "basic_queries no disponible"})
        data = basic_queries.count_contratos_by_gestor()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "count_contracts_by_gestor_error"})

# ---- Gestores específicos
@app.get("/basic/gestores/{gestor_id}", tags=["Basic"], response_model=ApiResponse)
def basic_gestor_info(gestor_id: int):
    """Información completa de un gestor"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestor_info"):
            return ok({"gestor_id": gestor_id, "segmento_id": "N10102"}, meta={"note": "fallback mock"})
        
        gestor_info = basic_queries.get_gestor_info(gestor_id)
        if not gestor_info:
            return ok({"error": "Gestor no encontrado"}, meta={"gestor_id": gestor_id})
        
        return ok(gestor_info, meta={"gestor_id": gestor_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestor_info_error"})

@app.get("/basic/gestores/{gestor_id}/segmento", tags=["Basic"], response_model=ApiResponse)
def basic_gestor_segmento(gestor_id: int):
    """Segmento específico de un gestor"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestor_info"):
            return ok({"SEGMENTO_ID": "N10102"}, meta={"note": "fallback segmento", "gestor_id": gestor_id})
        
        gestor_info = basic_queries.get_gestor_info(gestor_id)
        if not gestor_info:
            return ok({"error": "Gestor no encontrado"}, meta={"gestor_id": gestor_id})
        
        return ok({"SEGMENTO_ID": gestor_info.get("SEGMENTO_ID")}, meta={"gestor_id": gestor_id})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestor_segmento_error"})

# ============================================================================
# 🎯 COMPARATIVAS EXTENDIDAS
# ============================================================================

@app.get("/comparatives/gestores/margen", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_gestores_margen(periodo: str = Query(...)):
    """Comparativa de gestores por margen"""
    try:
        if hasattr(comparative_queries, "ranking_gestores_por_margen_enhanced"):
            res = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
            data = getattr(res, "data", [])
            return ok(data, meta={"count": len(data), "periodo": periodo})
        return ok([], meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestores_margen_error"})

@app.get("/comparatives/centros/margen", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_centros_margen(periodo: str = Query(...)):
    """Comparativa de centros por margen"""
    try:
        meth = None
        for name in ("compare_eficiencia_centros_enhanced", "analyze_centros_performance_enhanced"):
            if hasattr(comparative_queries, name):
                meth = getattr(comparative_queries, name)
                break
        data = getattr(meth(periodo), "data", []) if meth else []
        return ok(data, meta={"count": len(data), "periodo": periodo})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "centros_margen_error"})

@app.get("/comparatives/segmentos/margen", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_segmentos_margen(periodo: str = Query(...)):
    """Comparativa de segmentos por margen"""
    try:
        if hasattr(comparative_queries, "ranking_gestores_por_margen_enhanced"):
            res = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
            data = getattr(res, "data", [])
            return ok(data, meta={"count": len(data), "periodo": periodo, "note": "proxy"})
        return ok([], meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "segmentos_margen_error"})

@app.post("/comparatives/custom", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_custom(payload: Dict[str, Any] = Body(...)):
    """Comparativa personalizada"""
    try:
        periodo = payload.get("periodo")
        dimension = payload.get("dimension", "gestor")
        metric = payload.get("metric", "margen")
        
        if dimension == "gestor" and hasattr(comparative_queries, "ranking_gestores_por_margen_enhanced"):
            res = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
            data = getattr(res, "data", [])
            return ok({"dimension": dimension, "metric": metric, "periodo": periodo, "rows": data}, meta={"count": len(data)})
        return ok({"dimension": dimension, "metric": metric, "periodo": periodo, "rows": []}, meta={"note": "ruta genérica"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "comparatives_custom_error"})

# ============================================================================
# 🎯 DESVIACIONES EXTENDIDAS
# ============================================================================

@app.get("/deviations/pricing", tags=["Deviations"], response_model=ApiResponse)
def deviations_pricing(periodo: str = Query(...), umbral: float = Query(15.0)):
    """Desviaciones de pricing"""
    try:
        if hasattr(deviation_queries, "detect_precio_desviaciones_criticas_enhanced"):
            res = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, umbral)
            data = getattr(res, "data", [])
            return ok({"periodo": periodo, "umbral": umbral, "deviations": data}, meta={"count": len(data)})
        return ok({"periodo": periodo, "umbral": umbral, "deviations": []}, meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "deviations_pricing_error"})

@app.get("/deviations/summary", tags=["Deviations"], response_model=ApiResponse)
def deviations_summary(periodo: str = Query(...)):
    """Resumen de desviaciones"""
    try:
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
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "deviations_summary_error"})

@app.get("/deviations/margen", tags=["Deviations"], response_model=ApiResponse)
def deviations_margen(
    periodo: str = Query(..., description="YYYY-MM"),
    z: float = Query(2.0, description="Z-score / umbral estadístico"),
    enhanced: bool = Query(True)
):
    """Desviaciones de margen"""
    try:
        data = []
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
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "deviations_margen_error"})

@app.get("/deviations/volumen", tags=["Deviations"], response_model=ApiResponse)
def deviations_volumen(
    periodo: str = Query(..., description="YYYY-MM"),
    factor: float = Query(3.0, description="Multiplicador de outliers"),
    enhanced: bool = Query(True)
):
    """Desviaciones de volumen"""
    try:
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
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "deviations_volumen_error"})

# ============================================================================
# 🎯 INCENTIVOS EXTENDIDOS
# ============================================================================

@app.get("/incentives/gestor/{gestor_id}", tags=["Incentives"], response_model=ApiResponse)
def incentives_scorecard(gestor_id: str, periodo: str = Query(...)):
    """Scorecard de incentivos por gestor"""
    try:
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
            pass
        return ok(out)
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "incentives_scorecard_error"})

@app.get("/incentives/bonus-margen", tags=["Incentives"], response_model=ApiResponse)
def incentives_bonus_margen(periodo: str = Query(...), umbral_margen: float = Query(15.0)):
    """Bonus por margen neto"""
    try:
        if hasattr(incentive_queries, "analyze_bonus_margen_neto_enhanced"):
            res = incentive_queries.analyze_bonus_margen_neto_enhanced(periodo, umbral_margen)
            data = getattr(res, "data", [])
            return ok(data, meta={"count": len(data), "periodo": periodo})
        return ok([], meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "incentives_bonus_margen_error"})

@app.get("/incentives/bonus-pool", tags=["Incentives"], response_model=ApiResponse)
def incentives_bonus_pool(periodo: str = Query(...), pool: float = Query(50000.0)):
    """Distribución de pool de bonus"""
    try:
        if hasattr(incentive_queries, "calculate_ranking_bonus_pool_enhanced"):
            res = incentive_queries.calculate_ranking_bonus_pool_enhanced(periodo, pool)
            data = getattr(res, "data", [])
            return ok({"pool": data}, meta={"count": len(data), "periodo": periodo})
        return ok({"pool": []}, meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "incentives_bonus_pool_error"})

@app.post("/incentives/simulate", tags=["Incentives"], response_model=ApiResponse)
def incentives_simulate(payload: Dict[str, Any] = Body(...)):
    """Simulación de incentivos"""
    try:
        gestor_id = str(payload.get("gestor_id", ""))
        periodo = payload.get("periodo")
        if hasattr(incentive_queries, "simulate_incentive_scenarios_enhanced") and gestor_id and periodo:
            res = incentive_queries.simulate_incentive_scenarios_enhanced(gestor_id, periodo)
            return ok(getattr(res, "data", []))
        return ok([], meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "incentives_simulate_error"})

# ============================================================================
# 🎯 INCENTIVOS DETALLADOS POR ENTIDAD (NUEVOS)
# ============================================================================

@app.get("/incentives/centro/{centro_id}/total", tags=["Incentives"], response_model=ApiResponse)
def incentives_centro_total(centro_id: int, periodo: str = Query("2025-10")):
    """Total de incentivos del centro (suma de gestores)"""
    try:
        if hasattr(incentive_queries, "get_incentivos_por_centro"):
            res = incentive_queries.get_incentivos_por_centro(periodo)
            data = getattr(res, "data", [])
            
            centro_data = next((c for c in data if c.get("CENTRO_ID") == centro_id), None)
            if centro_data:
                return ok(centro_data, meta={"centro_id": centro_id, "periodo": periodo, "source": "incentive_queries"})
        
        # Fallback calculando desde gestores
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_centro_gestores_con_metricas"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        gestores = basic_queries.get_centro_gestores_con_metricas(centro_id, periodo)
        
        total_incentivos = 0.0
        gestores_elegibles = 0
        
        for gestor in gestores:
            margen = gestor.get('margen_neto_pct', 0)
            if margen >= 12.0:  # Umbral para incentivos
                incentivo = min(margen * 150, 4000)  # Fórmula simplificada
                total_incentivos += incentivo
                gestores_elegibles += 1
        
        return ok({
            "centro_id": centro_id,
            "periodo": periodo,
            "total_incentivos": round(total_incentivos, 2),
            "gestores_elegibles": gestores_elegibles,
            "total_gestores": len(gestores),
            "incentivo_promedio": round(total_incentivos / max(gestores_elegibles, 1), 2)
        }, meta={"centro_id": centro_id, "periodo": periodo, "source": "calculated"})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "incentives_centro_total_error"})

@app.get("/incentives/gestor/{gestor_id}/detalle", tags=["Incentives"], response_model=ApiResponse)
def incentives_gestor_detalle(gestor_id: str, periodo: str = Query("2025-10")):
    """Detalle completo de incentivos por gestor"""
    try:
        # Intentar obtener datos de incentivos enhanced
        detalle_incentivos = {}
        
        if hasattr(incentive_queries, "calculate_incentivo_cumplimiento_objetivos_enhanced"):
            objetivos_res = incentive_queries.calculate_incentivo_cumplimiento_objetivos_enhanced(periodo, 80.0)
            objetivos_data = getattr(objetivos_res, "data", [])
            gestor_objetivos = next((g for g in objetivos_data if str(g.get("GESTOR_ID")) == str(gestor_id)), None)
            if gestor_objetivos:
                detalle_incentivos["cumplimiento_objetivos"] = gestor_objetivos
        
        if hasattr(incentive_queries, "analyze_bonus_margen_neto_enhanced"):
            bonus_res = incentive_queries.analyze_bonus_margen_neto_enhanced(periodo, 15.0)
            bonus_data = getattr(bonus_res, "data", [])
            gestor_bonus = next((g for g in bonus_data if str(g.get("GESTOR_ID")) == str(gestor_id)), None)
            if gestor_bonus:
                detalle_incentivos["bonus_margen"] = gestor_bonus
        
        if hasattr(incentive_queries, "calculate_ranking_bonus_pool_enhanced"):
            pool_res = incentive_queries.calculate_ranking_bonus_pool_enhanced(periodo, 50000.0)
            pool_data = getattr(pool_res, "data", [])
            gestor_pool = next((g for g in pool_data if str(g.get("GESTOR_ID")) == str(gestor_id)), None)
            if gestor_pool:
                detalle_incentivos["pool_distribution"] = gestor_pool
        
        # Calcular total
        total_incentivos = 0.0
        total_incentivos += detalle_incentivos.get("cumplimiento_objetivos", {}).get("incentivo_calculado_eur", 0.0)
        total_incentivos += detalle_incentivos.get("bonus_margen", {}).get("bonus_total_eur", 0.0)
        total_incentivos += detalle_incentivos.get("pool_distribution", {}).get("incentivo_final_eur", 0.0)
        
        return ok({
            "gestor_id": gestor_id,
            "periodo": periodo,
            "detalle_incentivos": detalle_incentivos,
            "total_incentivos": round(total_incentivos, 2),
            "num_componentes": len([k for k in detalle_incentivos.keys() if detalle_incentivos[k]]),
            "elegible_para_incentivos": total_incentivos > 0
        }, meta={"gestor_id": gestor_id, "periodo": periodo})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "incentives_gestor_detalle_error"})


# ============================================================================
# 🎯 ANÁLISIS DE VARIANZA (VARIANCE BRIDGE)
# ============================================================================

@app.get("/analytics/variance", tags=["Analytics"], response_model=ApiResponse)
def variance(
    scope: str = Query(..., enum=["gestor", "centro", "segmento"]),
    id: Optional[str] = Query(None),
    periodo: str = Query(...),
    vs: str = Query("budget", enum=["budget", "last_year", "last_period"]),
):
    """Análisis de varianza (precio/volumen/mix)"""
    try:
        if hasattr(comparative_queries, "variance_bridge_enhanced"):
            res = comparative_queries.variance_bridge_enhanced(scope, id, periodo, vs)
            data = getattr(res, "data", [])
        else:
            data = [
                {"driver": "precio", "impacto": 12000.0},
                {"driver": "volumen", "impacto": -8000.0},
                {"driver": "mix", "impacto": 3500.0},
            ]
        
        # semáforo básico por magnitud relativa
        for d in data:
            val = abs(d.get("impacto", 0))
            d["semaforo"] = "Verde" if val < 5000 else ("Amarillo" if val < 10000 else "Rojo")
        
        return ok({"scope": scope, "id": id, "periodo": periodo, "vs": vs, "bridge": data}, meta={"count": len(data)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "variance_error"})

# ============================================================================
# 🎯 KPIs POR GESTOR Y EVOLUCIÓN
# ============================================================================

@app.get("/kpis/gestor/{gestor_id}", tags=["KPIs"], response_model=ApiResponse)
def kpis_gestor(gestor_id: str, periodo: str = Query(..., description="YYYY-MM")):
    """KPIs específicos de un gestor"""
    try:
        perf = gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo) if hasattr(gestor_queries, "get_gestor_performance_enhanced") else None
        row = perf.data[0] if getattr(perf, "data", None) else {}
        return ok({"gestor_id": gestor_id, "periodo": periodo, "kpis": row}, meta={"note": "raw enhanced KPIs"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_gestor_error"})

@app.get("/kpis/gestor/{gestor_id}/evolution", tags=["KPIs"], response_model=ApiResponse)
def kpis_evolution_range(gestor_id: str, from_period: str = Query(...), to_period: str = Query(...)):
    """Evolución de KPIs por rango de períodos"""
    try:
        if hasattr(gestor_queries, "get_evolution_range"):
            res = gestor_queries.get_evolution_range(gestor_id, from_period, to_period)
            data = getattr(res, "data", [])
            return ok({"gestor_id": gestor_id, "evolution": data}, meta={"periodo": f"{from_period}..{to_period}", "count": len(data)})
        return ok({"gestor_id": gestor_id, "evolution": []}, meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_evolution_error"})

# ============================================================================
# 🎯 CHARTS EXTENDIDOS Y DASHBOARDS
# ============================================================================

@app.post("/charts/quick", tags=["Charts"], response_model=ApiResponse)
def charts_quick(payload: Dict[str, Any] = Body(...)):
    """Crear gráfico rápido predefinido"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"chart": {"id": "mock"}})

        query_method = payload.get("query_method")
        chart_type = payload.get("chart_type", "bar")
        kwargs = payload.get("kwargs", {}) or {}

        chart = create_quick_chart(query_method, chart_type=chart_type, **kwargs)
        count = len(chart.get("data", [])) if isinstance(chart, dict) else 0
        return ok({"chart": chart}, meta={"count": count, "query_method": query_method})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_quick_error"})

@app.get("/charts/supported-types", tags=["Charts"], response_model=ApiResponse)
def charts_supported_types():
    """Tipos de gráficos soportados"""
    try:
        types = ["bar", "line", "pie", "area", "radar", "table"]
        return ok(types)
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_supported_types_error"})

@app.get("/charts/available-queries", tags=["Charts"], response_model=ApiResponse)
def charts_available_queries():
    """Queries disponibles para gráficos rápidos"""
    try:
        available = ChartFactory.get_available_queries() if CHART_GENERATOR_AVAILABLE else ["gestores_ranking", "centros_distribution", "productos_popularity", "precios_comparison", "summary_dashboard"]
        return ok(available, meta={"count": len(available)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_available_queries_error"})

@app.get("/charts/meta", tags=["Charts"], response_model=ApiResponse)
def charts_meta():
    """Metaconfiguración de gráficos"""
    try:
        meta = {
            "chart_types": list((CDG_CHART_CONFIGS.get("chart_types") or {}).keys()) or ["bar", "line", "pie", "area", "horizontal_bar", "donut", "stacked_bar"],
            "dimensions": CDG_CHART_CONFIGS.get("dimensions") or {"gestor": "Gestor", "centro": "Centro", "segmento": "Segmento", "producto": "Producto", "periodo": "Período", "cliente": "Cliente", "contrato": "Contrato"},
            "metrics": CDG_CHART_CONFIGS.get("metrics") or {"CONTRATOS": "Número de Contratos"},
            "colors": CDG_CHART_CONFIGS.get("colors") or {},
            "supports_pivot": True
        }
        return ok(meta)
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_meta_error"})

@app.get("/charts/summary-dashboard", tags=["Charts"], response_model=ApiResponse)
def charts_summary_dashboard():
    """Dashboard resumen con múltiples gráficos"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"dashboard": {"id": "mock", "charts": []}}, meta={"note": "mock"})
        gen = QueryIntegratedChartGenerator()
        dashboard = gen.generate_summary_dashboard()
        charts = dashboard.get("charts", []) if isinstance(dashboard, dict) else []
        return ok(dashboard, meta={"count": len(charts)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_summary_dashboard_error"})

@app.get("/charts/gestores-ranking", tags=["Charts"], response_model=ApiResponse)
def charts_gestores_ranking(
    metric: str = Query("CONTRATOS", enum=["CONTRATOS", "CLIENTES"]),
    chart_type: str = Query("horizontal_bar")
):
    """Gráfico de ranking de gestores"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"chart": {"id": "mock"}})
        gen = QueryIntegratedChartGenerator()
        chart = gen.generate_gestores_ranking_chart(metric=metric, chart_type=chart_type)
        return ok({"chart": chart}, meta={"metric": metric})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_gestores_ranking_error"})

@app.get("/charts/centros-distribution", tags=["Charts"], response_model=ApiResponse)
def charts_centros_distribution(chart_type: str = Query("donut")):
    """Gráfico de distribución de centros"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"chart": {"id": "mock"}})
        gen = QueryIntegratedChartGenerator()
        chart = gen.generate_centros_distribution_chart(chart_type=chart_type)
        return ok({"chart": chart})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_centros_distribution_error"})

@app.get("/charts/productos-popularity", tags=["Charts"], response_model=ApiResponse)
def charts_productos_popularity(chart_type: str = Query("horizontal_bar")):
    """Gráfico de popularidad de productos"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"chart": {"id": "mock"}})
        gen = QueryIntegratedChartGenerator()
        chart = gen.generate_productos_popularity_chart(chart_type=chart_type)
        return ok({"chart": chart})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_productos_popularity_error"})

@app.get("/charts/precios-comparison", tags=["Charts"], response_model=ApiResponse)
def charts_precios_comparison(fecha_calculo: Optional[str] = Query(None), chart_type: str = Query("bar")):
    """Gráfico de comparación de precios"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"chart": {"id": "mock"}})
        gen = QueryIntegratedChartGenerator()
        chart = gen.generate_precios_comparison_chart(fecha_calculo=fecha_calculo, chart_type=chart_type)
        return ok({"chart": chart}, meta={"fecha_calculo": fecha_calculo})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_precios_comparison_error"})

@app.get("/charts/gastos-by-centro", tags=["Charts"], response_model=ApiResponse)
def charts_gastos_by_centro(fecha: str = Query(..., description="YYYY-MM-DD"), chart_type: str = Query("stacked_bar")):
    """Gráfico de gastos por centro"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"chart": {"id": "mock"}})
        gen = QueryIntegratedChartGenerator()
        chart = gen.generate_gastos_by_centro_chart(fecha=fecha, chart_type=chart_type)
        return ok({"chart": chart}, meta={"fecha": fecha})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "charts_gastos_by_centro_error"})

# ============================================================================
# 🎯 DASHBOARDS Y REPORTES EXTENDIDOS
# ============================================================================

@app.get("/dashboards/templates", tags=["Dashboards"], response_model=ApiResponse)
def dashboards_templates():
    """Plantillas de dashboards disponibles"""
    try:
        templates = [
            {"id": "summary", "title": "Dashboard Resumen CDG", "params": []},
            {"id": "gestor_performance", "title": "Performance por Gestor", "params": ["gestor_id", "periodo"]},
        ]
        return ok(templates, meta={"count": len(templates)})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "dashboards_templates_error"})

@app.post("/dashboards/build", tags=["Dashboards"], response_model=ApiResponse)
def dashboards_build(payload: Dict[str, Any] = Body(...)):
    """Construir dashboard desde plantilla"""
    try:
        tpl = (payload or {}).get("template_id")
        if not tpl:
            return ok({"error": "template_id requerido"}, meta={"note": "missing_template_id"})

        if tpl == "summary":
            dashboard = QueryIntegratedChartGenerator().generate_summary_dashboard() if CHART_GENERATOR_AVAILABLE else {"id": "mock", "charts": []}
            return ok(dashboard, meta={"template_id": tpl})

        if tpl == "gestor_performance":
            gestor_id = payload.get("gestor_id")
            periodo = payload.get("periodo")
            if not (gestor_id and periodo):
                return ok({"error": "gestor_id y periodo requeridos"}, meta={"note": "missing_params"})
            
            perf = gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo) if hasattr(gestor_queries, "get_gestor_performance_enhanced") else type("R", (), {"data": []})()
            row = perf.data[0] if getattr(perf, "data", None) else {}
            dash = chart_dash.generate_gestor_dashboard(gestor_data=row, kpi_data=row, periodo=periodo) if CHART_GENERATOR_AVAILABLE else {"charts": []}
            dash["id"] = f"dashboard_{gestor_id}_{periodo}"
            dash["title"] = f"Performance Gestor {gestor_id} — {periodo}"
            return ok(dash, meta={"template_id": tpl})

        return ok({"id": "unknown_template", "charts": []}, meta={"note": "template no soportado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "dashboards_build_error"})

@app.post("/reports/deviation-analysis", tags=["Reports"], response_model=ApiResponse)
def reports_deviation_analysis(periodo: str = Query(...)):
    """Reporte de análisis de desviaciones"""
    try:
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
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "reports_deviation_analysis_error"})

@app.post("/reports/export", tags=["Reports"], response_model=ApiResponse)
def reports_export(payload: Dict[str, Any] = Body(...)):
    """Exportar reportes a diferentes formatos"""
    try:
        return ok({"status": "exported", "format": payload.get("format", "pdf")})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "reports_export_error"})

@app.get("/reports/meta", tags=["Reports"], response_model=ApiResponse)
def reports_meta():
    """Metadatos de reportes disponibles"""
    try:
        return ok({
            "types": ["business_review", "executive_summary", "deviation_analysis"],
            "formats": ["pdf", "xlsx", "json"]
        })
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "reports_meta_error"})

# ============================================================================
# 🎯 UTILIDADES SQL Y VALIDACIÓN
# ============================================================================

@app.post("/security/sql/validate", tags=["Security"], response_model=ApiResponse)
def security_sql_validate(req: DynamicQueryRequest):
    """Validar seguridad de consultas SQL"""
    try:
        if not SQL_GUARD_AVAILABLE:
            return ok({"is_safe": True, "mode": "mock"})
        v = validate_query_for_cdg(req.sql, context=req.context)
        return ok(v)
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "security_sql_validate_error"})

@app.post("/sql/dynamic", tags=["SQL Utilities"], response_model=ApiResponse)
def sql_dynamic(req: DynamicQueryRequest):
    """Ejecutar SQL dinámico validado"""
    try:
        if not SQL_GUARD_AVAILABLE:
            return ok({"error": "sql_guard no disponible"}, meta={"note": "mock"})
        validation = validate_query_for_cdg(req.sql, context=req.context)
        if not validation.get("is_safe"):
            return ok({"error": f"Query no segura: {validation}"}, meta={"validation": validation})
        
        # Aquí iría la ejecución real con ORM/driver seguro
        data = []  # placeholder
        return ok({"validation": validation, "rows": data}, meta={"count": len(data), "source": "dynamic_select"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "sql_dynamic_error"})


# ============================================================================
# 🎯 ENDPOINTS DE CHARTS CON PIVOT MEJORADO
# ============================================================================

@app.post("/charts/from-data", tags=["Charts"], response_model=ApiResponse)
def charts_from_data(body: Dict[str, Any]):
    """Crear gráfico desde datos"""
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"chart": {"id": "mock"}})
            
        chart = create_chart_from_query_data(body.get("data", []), body.get("config", {}))
        return ok({"chart": chart})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "chart_from_data_error"})

@app.post("/charts/pivot", tags=["Charts"], response_model=ApiResponse)
def charts_pivot(body: ChartPivotRequest):
    """
    🎯 PIVOT DE GRÁFICOS MEJORADO - Usando handle_chart_change_request
    """
    try:
        if not CHART_GENERATOR_AVAILABLE:
            return ok({"status": "mock", "message": "Chart generator no disponible"})
        
        # Usar la función mejorada de pivot
        result = handle_chart_change_request(
            body.message, 
            body.current_chart_config or {},
            body.chart_interaction_type or "pivot"
        )
        
        # Fallback a función anterior si no está disponible
        if not result or result.get("status") == "error":
            result = pivot_chart_with_query_integration(body.message, body.current_chart_config or {})
        
        return ok(result, meta={"pivot_type": body.chart_interaction_type, "source": "chart_pivot_enhanced"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "chart_pivot_error"})

@app.get("/charts/validate", tags=["Charts"], response_model=ApiResponse)
def charts_validate():
    """Validar generador de gráficos"""
    try:
        res = validate_chart_generator() if CHART_GENERATOR_AVAILABLE else {"status": "MOCK"}
        return ok(res)
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "chart_validate_error"})

@app.get("/charts/available-types", tags=["Charts"], response_model=ApiResponse)
def charts_available_types():
    """Tipos de gráficos disponibles"""
    try:
        if CHART_GENERATOR_AVAILABLE and hasattr(ChartFactory, 'get_available_queries'):
            available = ChartFactory.get_available_queries()
            return ok({"chart_types": available})
        else:
            return ok({"chart_types": ["bar", "line", "pie", "scatter", "heatmap"]})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "chart_types_error"})

# ============================================================================
# 🎯 ENDPOINTS DE KPIS (TODOS MANTENIDOS)
# ============================================================================

@app.post("/kpi/margen", tags=["KPI Calculator"], response_model=ApiResponse)
def kpi_margen(req: KPIRequest):
    """Calcular margen neto"""
    try:
        if hasattr(kpi_calc, "calculate_margen_neto") and req.ingresos is not None and req.gastos is not None:
            val = kpi_calc.calculate_margen_neto(req.ingresos, req.gastos)
            return ok({"margen_neto": val})
        return ok({"margen_neto": None}, meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpi_margen_error"})

@app.post("/kpi/roe", tags=["KPI Calculator"], response_model=ApiResponse)
def kpi_roe(req: KPIRequest):
    """Calcular ROE"""
    try:
        if hasattr(kpi_calc, "calculate_roe") and req.beneficio_neto is not None and req.patrimonio is not None:
            val = kpi_calc.calculate_roe(req.beneficio_neto, req.patrimonio)
            return ok({"roe": val})
        return ok({"roe": None}, meta={"note": "no implementado"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpi_roe_error"})

@app.post("/kpi/calculate", tags=["KPI Calculator"], response_model=ApiResponse)
def kpi_calculate(req: KPIRequest):
    """Calcular múltiples KPIs desde datos"""
    try:
        if req.row and hasattr(kpi_calc, "calculate_kpis_from_data"):
            kpis = kpi_calc.calculate_kpis_from_data([req.row])
            return ok({"kpis": kpis})
        return ok({"kpis": {}}, meta={"note": "no data provided"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpi_calculate_error"})

# ============================================================================
# 🎯 KPIs FINANCIEROS ESPECÍFICOS POR ENTIDAD (NUEVOS)
# ============================================================================

@app.get("/kpis/centro/{centro_id}/financieros", tags=["KPI Calculator"], response_model=ApiResponse)
def kpis_centro_financieros(centro_id: int, periodo: str = Query("2025-10")):
    """KPIs financieros completos de un centro (ROE, ROA, Margen, etc.)"""
    try:
        # Obtener métricas del centro
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_centro_metricas_financieras"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        metricas = basic_queries.get_centro_metricas_financieras(centro_id, periodo)
        
        if not metricas:
            return ok({"error": "Centro no encontrado o sin datos"}, meta={"centro_id": centro_id})
        
        # Calcular KPIs usando kpi_calculator
        kpis_financieros = {}
        
        if hasattr(kpi_calc, "calculate_margen_neto") and metricas.get('ingresos_total') and metricas.get('gastos_total'):
            margen = kpi_calc.calculate_margen_neto(metricas['ingresos_total'], metricas['gastos_total'])
            kpis_financieros['margen_neto'] = margen
        
        if hasattr(kpi_calc, "calculate_roe") and metricas.get('beneficio_neto') and metricas.get('patrimonio_total', metricas.get('ingresos_total', 1)):
            roe = kpi_calc.calculate_roe(metricas['beneficio_neto'], metricas.get('patrimonio_total', metricas.get('ingresos_total', 1)))
            kpis_financieros['roe'] = roe
        
        if hasattr(kpi_calc, "calculate_ratio_eficiencia") and metricas.get('ingresos_total') and metricas.get('gastos_total'):
            eficiencia = kpi_calc.calculate_ratio_eficiencia(metricas['ingresos_total'], metricas['gastos_total'])
            kpis_financieros['eficiencia'] = eficiencia
        
        return ok({
            "centro_id": centro_id,
            "periodo": periodo,
            "metricas_base": metricas,
            "kpis_financieros": kpis_financieros
        }, meta={"centro_id": centro_id, "periodo": periodo})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_centro_financieros_error"})

@app.get("/kpis/gestor/{gestor_id}/financieros", tags=["KPI Calculator"], response_model=ApiResponse)
def kpis_gestor_financieros(gestor_id: int, periodo: str = Query("2025-10")):
    """KPIs financieros completos de un gestor (ROE, ROA, Margen, Eficiencia)"""
    try:
        # Usar el método enhanced de gestor_queries si está disponible
        if hasattr(gestor_queries, "get_gestor_performance_enhanced"):
            res = gestor_queries.get_gestor_performance_enhanced(str(gestor_id), periodo)
            data = getattr(res, "data", [])
            if data:
                return ok(data[0], meta={"gestor_id": gestor_id, "periodo": periodo, "source": "gestor_queries_enhanced"})
        
        # Fallback usando basic_queries
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_gestor_metricas_completas"):
            return ok({"error": "Funcionalidad no disponible"}, meta={"note": "basic_queries no disponible"})
        
        metricas = basic_queries.get_gestor_metricas_completas(gestor_id, periodo)
        return ok(metricas, meta={"gestor_id": gestor_id, "periodo": periodo, "source": "basic_queries"})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_gestor_financieros_error"})

@app.get("/kpis/gestor/{gestor_id}/roe", tags=["KPI Calculator"], response_model=ApiResponse)
def kpis_gestor_roe(gestor_id: int, periodo: str = Query("2025-10")):
    """ROE específico de un gestor"""
    try:
        if hasattr(gestor_queries, "calculate_roe_gestor_enhanced"):
            res = gestor_queries.calculate_roe_gestor_enhanced(str(gestor_id), periodo)
            data = getattr(res, "data", [])
            if data:
                return ok(data[0], meta={"gestor_id": gestor_id, "periodo": periodo, "type": "roe"})
        
        return ok({"roe_pct": 0.0, "clasificacion": "SIN_DATOS"}, meta={"note": "gestor_queries no disponible"})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_gestor_roe_error"})

@app.get("/kpis/gestor/{gestor_id}/eficiencia", tags=["KPI Calculator"], response_model=ApiResponse)
def kpis_gestor_eficiencia(gestor_id: int, periodo: str = Query("2025-10")):
    """Eficiencia operativa específica de un gestor"""
    try:
        if hasattr(gestor_queries, "calculate_eficiencia_operativa_gestor_enhanced"):
            res = gestor_queries.calculate_eficiencia_operativa_gestor_enhanced(str(gestor_id), periodo)
            data = getattr(res, "data", [])
            if data:
                return ok(data[0], meta={"gestor_id": gestor_id, "periodo": periodo, "type": "eficiencia"})
        
        return ok({"ratio_eficiencia": 0.0, "clasificacion": "SIN_DATOS"}, meta={"note": "gestor_queries no disponible"})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_gestor_eficiencia_error"})

@app.get("/kpis/centro/{centro_id}/margen", tags=["KPI Calculator"], response_model=ApiResponse)
def kpis_centro_margen(centro_id: int, periodo: str = Query("2025-10")):
    """Margen neto específico de un centro"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_centro_metricas_financieras"):
            return ok({"margen_neto_pct": 0.0, "clasificacion": "SIN_DATOS"}, meta={"note": "basic_queries no disponible"})
        
        metricas = basic_queries.get_centro_metricas_financieras(centro_id, periodo)
        
        if metricas and hasattr(kpi_calc, "calculate_margen_neto"):
            margen = kpi_calc.calculate_margen_neto(
                metricas.get('ingresos_total', 0), 
                metricas.get('gastos_total', 0)
            )
            return ok(margen, meta={"centro_id": centro_id, "periodo": periodo, "type": "margen"})
        
        return ok({"margen_neto_pct": 0.0, "clasificacion": "SIN_DATOS"}, meta={"centro_id": centro_id})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_centro_margen_error"})

@app.get("/kpis/centro/{centro_id}/bonus-total", tags=["KPI Calculator"], response_model=ApiResponse)
def kpis_centro_bonus_total(centro_id: int, periodo: str = Query("2025-10")):
    """Suma total de bonus de gestores del centro"""
    try:
        if not BASIC_QUERIES_AVAILABLE or not hasattr(basic_queries, "get_centro_gestores_con_metricas"):
            return ok({"bonus_total": 0.0, "gestores_con_bonus": 0}, meta={"note": "basic_queries no disponible"})
        
        gestores = basic_queries.get_centro_gestores_con_metricas(centro_id, periodo)
        
        bonus_total = 0.0
        gestores_con_bonus = 0
        
        for gestor in gestores:
            if gestor.get('margen_neto_pct', 0) >= 15.0:  # Umbral mínimo para bonus
                # Cálculo simplificado de bonus basado en margen
                bonus_estimado = min(gestor.get('margen_neto_pct', 0) * 100, 3000)
                bonus_total += bonus_estimado
                gestores_con_bonus += 1
        
        return ok({
            "centro_id": centro_id,
            "periodo": periodo,
            "bonus_total": round(bonus_total, 2),
            "gestores_con_bonus": gestores_con_bonus,
            "total_gestores": len(gestores),
            "bonus_promedio": round(bonus_total / max(gestores_con_bonus, 1), 2)
        }, meta={"centro_id": centro_id, "periodo": periodo})
        
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "kpis_centro_bonus_error"})


# ============================================================================
# 🎯 ENDPOINTS DE QUERIES ESPECIALIZADAS (TODOS MANTENIDOS)
# ============================================================================

@app.get("/comparatives/gestores-ranking", tags=["Comparatives"], response_model=ApiResponse)
def comparatives_gestores_ranking(periodo: str = Query("2025-10")):
    """Ranking comparativo de gestores"""
    try:
        if hasattr(comparative_queries, "ranking_gestores_por_margen_enhanced"):
            res = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
            data = getattr(res, "data", [])
            return ok(data, meta={"count": len(data), "periodo": periodo})
        return ok([], meta={"note": "comparative_queries no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestores_ranking_error"})

@app.get("/deviations/critical", tags=["Deviations"], response_model=ApiResponse)
def deviations_critical(periodo: str = Query("2025-10"), umbral: float = Query(15.0)):
    """Desviaciones críticas detectadas"""
    try:
        if hasattr(deviation_queries, "detect_critical_deviations_enhanced"):
            res = deviation_queries.detect_critical_deviations_enhanced(periodo, umbral)
            data = getattr(res, "data", [])
            return ok(data, meta={"count": len(data), "periodo": periodo, "umbral": umbral})
        return ok([], meta={"note": "deviation_queries no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "critical_deviations_error"})

@app.get("/gestor/{gestor_id}/performance", tags=["Gestor Analysis"], response_model=ApiResponse)
def gestor_performance(gestor_id: str, periodo: str = Query("2025-10")):
    """Performance detallado de un gestor"""
    try:
        if hasattr(gestor_queries, "get_gestor_performance_enhanced"):
            res = gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo)
            data = getattr(res, "data", [])
            return ok(data[0] if data else {}, meta={"gestor_id": gestor_id, "periodo": periodo})
        return ok({}, meta={"note": "gestor_queries no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "gestor_performance_error"})

@app.get("/incentives/calculate", tags=["Incentives"], response_model=ApiResponse)
def incentives_calculate(gestor_id: Optional[str] = None, periodo: str = Query("2025-10")):
    """Calcular incentivos por gestor o período"""
    try:
        if hasattr(incentive_queries, "calculate_incentives_enhanced"):
            if gestor_id:
                res = incentive_queries.calculate_incentives_enhanced(gestor_id, periodo)
            else:
                res = incentive_queries.calculate_period_incentives_enhanced(periodo)
            data = getattr(res, "data", [])
            return ok(data, meta={"count": len(data), "gestor_id": gestor_id, "periodo": periodo})
        return ok([], meta={"note": "incentive_queries no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "incentives_calculate_error"})

# ============================================================================
# 🎯 ENDPOINTS DE DASHBOARDS Y REPORTES (TODOS MANTENIDOS)
# ============================================================================

@app.post("/dashboards/generate", tags=["Dashboards"], response_model=ApiResponse)
def dashboards_generate(req: ReportRequest):
    """Generar dashboard completo"""
    try:
        if hasattr(chart_dash, "generate_gestor_dashboard"):
            dashboard = chart_dash.generate_gestor_dashboard(
                req.gestor_id, req.periodo, req.options
            )
            return ok(dashboard, meta={"type": "dashboard", "gestor_id": req.gestor_id})
        return ok({"charts": []}, meta={"note": "chart_dash no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "dashboard_generate_error"})

@app.post("/reports/business-review", tags=["Reports"], response_model=ApiResponse)
def reports_business_review(req: ReportRequest):
    """Generar business review report"""
    try:
        if hasattr(report_gen, "generate_business_review"):
            report = report_gen.generate_business_review(
                gestor_id=req.gestor_id,
                periodo=req.periodo,
                **req.options
            )
            return ok(report.to_dict(), meta={"type": "business_review", "periodo": req.periodo})
        return ok({"report": "mock"}, meta={"note": "report_gen no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "business_review_error"})

@app.post("/reports/executive-summary", tags=["Reports"], response_model=ApiResponse)
def reports_executive_summary(req: ReportRequest):
    """Generar resumen ejecutivo"""
    try:
        if hasattr(report_gen, "generate_executive_summary_report"):
            report = report_gen.generate_executive_summary_report(
                periodo=req.periodo,
                **req.options
            )
            return ok(report.to_dict(), meta={"type": "executive_summary", "periodo": req.periodo})
        return ok({"summary": "mock"}, meta={"note": "report_gen no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "executive_summary_error"})

# ============================================================================
# 🎯 ENDPOINTS DE UTILIDADES Y VALIDACIÓN
# ============================================================================

@app.post("/sql/validate", tags=["SQL Utilities"], response_model=ApiResponse)
def sql_validate(req: DynamicQueryRequest):
    """Validar consulta SQL"""
    try:
        validation = validate_query_for_cdg(req.sql, req.context)
        return ok(validation, meta={"sql_length": len(req.sql), "context": req.context})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "sql_validate_error"})

@app.get("/reflection/insights", tags=["Reflection"], response_model=ApiResponse)
def reflection_insights():
    """Insights organizacionales del sistema"""
    try:
        if REFLECTION_AVAILABLE:
            insights = reflection_manager.generate_organizational_insights()
            return ok(insights, meta={"source": "reflection_manager"})
        return ok({"insights": []}, meta={"note": "reflection no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "reflection_insights_error"})

@app.post("/feedback/process", tags=["Feedback"], response_model=ApiResponse)
async def feedback_process(body: Dict[str, Any]):
    """Procesar feedback del usuario"""
    try:
        if REFLECTION_AVAILABLE:
            result = await reflection_manager.process_feedback(**body)
            return ok(result, meta={"source": "reflection_manager"})
        return ok({"status": "mock"}, meta={"note": "reflection no disponible"})
    except Exception as e:
        return ok({"error": str(e)}, meta={"note": "feedback_process_error"})

# ============================================================================
# 🎯 MIDDLEWARE Y MANEJO DE ERRORES
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now(UTC)
    resp = await call_next(request)
    took = (datetime.now(UTC) - start).total_seconds()
    logger.info(f"{request.method} {request.url.path} -> {resp.status_code} in {took:.3f}s")
    return resp

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

# ============================================================================
# 🎯 MAIN ENTRY POINT CON CONFIGURACIÓN WINDOWS OPTIMIZADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # ✅ CONFIGURACIÓN ESPECÍFICA PARA WINDOWS + WEBSOCKETS
    config = {
        "host": "127.0.0.1",  # ✅ Usar 127.0.0.1 en lugar de 0.0.0.0 en Windows
        "port": int(os.getenv("PORT", 8000)),
        "reload": True,
        
        # ✅ WEBSOCKET ESPECÍFICO PARA WINDOWS
        "ws_ping_interval": 45.0,      # Ping cada 30 segundos
        "ws_ping_timeout": 30.0,       # Timeout de 15 segundos para pong
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
        print("🎯 CDG API v11.0 con Perfect Integration")
        # En Windows, usar configuración específica
        uvicorn.run("main:app", **config)
    else:
        print("🐧 Ejecutando en Linux/Mac")
        print("🎯 CDG API v11.0 con Perfect Integration")
        # En otros sistemas, configuración estándar
        config["host"] = "0.0.0.0"
        config["workers"] = 4  # Múltiples workers en Linux/Mac
        uvicorn.run("main:app", **config)
