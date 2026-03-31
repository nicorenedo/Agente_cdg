# backend/src/routers/forecast_router.py
"""
FastAPI router for forecast endpoints.
S69: Exposes ProphetEngine, MacroContext, WhatIf, and ForecastAgent.
"""

import logging
from typing import Optional, Dict
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["Forecast"])


# ── Request models ───────────────────────────────────────────────────

class ForecastBaseRequest(BaseModel):
    horizonte_meses: int = 6
    dimension: str = 'entidad'
    filtro_id: Optional[str] = None

class WhatIfRequest(BaseModel):
    shocks: Dict
    horizonte_meses: int = 6
    dimension: str = 'entidad'
    filtro_id: Optional[str] = None

class ForecastChatRequest(BaseModel):
    message: str
    user_role: str = 'control_gestion'
    gestor_id: Optional[str] = None
    periodo_base: str = '2026-04'
    session_id: str = 'default'

class RecommendationsRequest(BaseModel):
    objetivo: str
    horizonte_meses: int = 6


# ── Lazy-loaded instances ────────────────────────────────────────────

_fq = None
_pe = None
_mcs = None
_sb = None
_sim = None
_agent = None


def _init():
    global _fq, _pe, _mcs, _sb, _sim, _agent
    if _fq is not None:
        return
    try:
        from queries.forecast_queries import ForecastQueries
        from forecast.prophet_engine import ProphetEngine
        from forecast.macro_context import MacroContextService
        from forecast.scenario_builder import ScenarioBuilder
        from forecast.whatif_simulator import WhatIfSimulator
        from agents.forecast_agent import get_forecast_agent
        _fq = ForecastQueries()
        _pe = ProphetEngine()
        _mcs = MacroContextService()
        _sb = ScenarioBuilder()
        _sim = WhatIfSimulator()
        _agent = get_forecast_agent()
        logger.info("Forecast router: all modules initialized")
    except Exception as e:
        logger.error(f"Forecast router init error: {e}")


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/base")
async def forecast_base(req: ForecastBaseRequest):
    """Proyección base con 3 escenarios."""
    _init()
    df = _fq.get_serie_ingresos(dimension=req.dimension, filtro_id=req.filtro_id)
    if df.empty:
        return {"error": "Sin datos historicos para esta dimension"}
    _pe.fit(df)
    forecast = _pe.get_scenarios(horizonte_meses=req.horizonte_meses)
    macro = _mcs.get_context()
    return _sb.build(forecast, macro)


@router.post("/whatif")
async def forecast_whatif(req: WhatIfRequest):
    """Simulación what-if con shocks paramétricos."""
    _init()
    return _sim.simulate(
        shocks=req.shocks,
        horizonte_meses=req.horizonte_meses,
        dimension=req.dimension,
        filtro_id=req.filtro_id,
    )


@router.get("/historicos")
async def historicos(dimension: str = 'entidad', filtro_id: str = None):
    """Serie temporal histórica de ingresos mensuales."""
    _init()
    df = _fq.get_serie_ingresos(dimension=dimension, filtro_id=filtro_id)
    return [{'periodo': row['ds'].strftime('%Y-%m'), 'valor': round(float(row['y']))}
            for _, row in df.iterrows()]


@router.get("/macro-context")
async def macro_context():
    """Contexto macroeconómico actual."""
    _init()
    return _mcs.get_context()


@router.post("/recommendations")
async def recommendations(req: RecommendationsRequest):
    """Recomendaciones accionables."""
    _init()
    df = _fq.get_serie_ingresos()
    _pe.fit(df)
    forecast = _pe.get_scenarios(horizonte_meses=req.horizonte_meses)
    macro = _mcs.get_context()
    escenarios = _sb.build(forecast, macro)
    trend = _pe.get_trend_components()
    return {
        'objetivo': req.objetivo,
        'escenario_base': escenarios['escenario_base'],
        'escenario_optimista': escenarios['escenario_optimista'],
        'tendencia': trend,
        'acciones': escenarios['escenario_optimista'].get('acciones_requeridas', []),
        'riesgos': escenarios['escenario_pesimista'].get('drivers_riesgo', []),
        'macro': macro.get('narrativa_corta', ''),
    }


@router.post("/chat")
async def forecast_chat(req: ForecastChatRequest):
    """Chat conversacional con ForecastAgent."""
    _init()
    return await _agent.process_message(
        message=req.message,
        user_role=req.user_role,
        gestor_id=req.gestor_id,
        periodo_base=req.periodo_base,
        session_id=req.session_id,
    )


@router.get("/dimensiones")
async def dimensiones():
    """Dimensiones disponibles para forecast."""
    _init()
    return _fq.get_dimensiones_disponibles()


@router.get("/shocks-disponibles")
async def shocks_disponibles():
    """Shocks disponibles con rangos."""
    _init()
    return _sim.get_shocks_disponibles()
