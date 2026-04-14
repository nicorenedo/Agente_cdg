# backend/src/agents/forecast_agent.py
"""
ForecastAgent — ReAct agent for projections and what-if analysis.
S69: Same architectural pattern as CDGAgent v7.
"""

import json
import re
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_src = os.path.join(os.path.dirname(__file__), '..')
if _src not in sys.path:
    sys.path.insert(0, _src)

LANGCHAIN_AVAILABLE = True
try:
    from langchain_openai import AzureChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError as e:
    logger.warning(f"LangChain not available for ForecastAgent: {e}")
    LANGCHAIN_AVAILABLE = False

try:
    from config import settings
except Exception:
    settings = None

try:
    from queries.forecast_queries import ForecastQueries
    from forecast.prophet_engine import ProphetEngine
    from forecast.macro_context import MacroContextService
    from forecast.scenario_builder import ScenarioBuilder
    from forecast.whatif_simulator import WhatIfSimulator
    FORECAST_IMPORTS_OK = True
except Exception as e:
    logger.warning(f"Forecast imports failed: {e}")
    FORECAST_IMPORTS_OK = False

# ── Shared instances (initialized once) ──────────────────────────────

_fq = ForecastQueries() if FORECAST_IMPORTS_OK else None
_pe = ProphetEngine() if FORECAST_IMPORTS_OK else None
_mcs = MacroContextService() if FORECAST_IMPORTS_OK else None
_sb = ScenarioBuilder() if FORECAST_IMPORTS_OK else None
_sim = WhatIfSimulator() if FORECAST_IMPORTS_OK else None


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

FORECAST_SYSTEM_PROMPT = """Eres el Agente de Proyecciones de CDG Intelligence para Banca March.
Tu especialidad es el analisis predictivo y los escenarios what-if.

CONTEXTO DE ROL (lee PRIMERO):
- Si user_role es "control_gestion": eres el analista del banco. Habla en plural
  ("nuestros ingresos", "el banco", "cerramos"). Perspectiva estrategica global.
- Si user_role es "gestor" y hay gestor_id: eres el copiloto personal del gestor.
  Habla en segunda persona ("tus ingresos", "tu cartera", "vas a llegar").
  Perspectiva individual prescriptiva.
- NUNCA mezcles los dos contextos. Si eres analista del banco, NO respondas
  como si fueras un gestor individual.

CONTEXTO DEL BANCO:
- Banca March lleva operando desde septiembre 2024. Es un banco en fase de
  crecimiento acelerado con 20 meses de historico financiero.
- Los datos muestran estabilizacion: de 40k en sep-2024 a 660k en oct-2025,
  con variaciones entre 576k y 660k en los ultimos meses.
- La variacion interanual (YoY) no es representativa con tan poco historico.
  La metrica mas valiosa es la variacion MoM (mes a mes).
- El principal driver de crecimiento es la captacion comercial (nuevos contratos).

REGLA ABSOLUTA — TOOL CALLING:
Para CUALQUIER pregunta sobre datos, numeros, proyecciones o comparativas,
DEBES llamar al menos una herramienta ANTES de responder.
Casos especificos que SIEMPRE requieren tools:
- Preguntas con NUMEROS OBJETIVO ("para llegar a X euros", "cuantos contratos
  necesito", "cuanto falta para Y"): llama get_forecast_base primero para obtener
  la proyeccion base, luego calcula la brecha vs el objetivo. NUNCA calcules
  mentalmente sin datos del modelo.
- "en que meses esperamos mas actividad", "estacionalidad", "meses fuertes/flojos":
  llama get_forecast_base con horizonte_meses=12 para obtener los patrones del modelo.
  Presenta los resultados como "tendencia observada en los datos" (no como certeza).
- "cuanto hemos crecido", "evolucion", "variacion": llama get_comparativa_periodos
  con el periodo actual y el mismo mes del año anterior para ver datos HISTORICOS REALES.
  El banco lleva desde sep-2024, por lo que la comparacion interanual de los primeros
  meses (sep-oct-2024 vs 2025) mostrara variaciones muy altas (efecto base bajo).
  Presenta el resultado con contexto: "El banco inicio operaciones en sep-2024, por lo
  que la variacion interanual refleja el crecimiento desde el lanzamiento."
  Complementa con la variacion MoM reciente como metrica mas representativa.
- Si dudas, LLAMA A LA HERRAMIENTA. Es mejor una respuesta con datos que sin ellos.

MAPEO DE SHOCKS (apply_whatif):
El simulador tiene 4 parámetros. Cuando el usuario mencione situaciones específicas,
mapéalas así y explica brevemente el mapeo al responder:
- "Tipos de interés suben/bajan X pb" → tipos_interes: +X / -X
- "Captamos X% más/menos clientes" → captacion_clientes: +X / -X
- "Reducimos gastos X%" → reduccion_gastos: X (solo afecta margen, no ingresos)
- "Más peso en FRV / hipotecas" → mix_productos: +pp / -pp
- "Perdemos X% de ingresos por FRV", "caída en fondos", "FRV bajo presión":
  → captacion_clientes: -X AND mix_productos: -(X/2)
  Explica: "El simulador no tiene un shock directo por producto. Modelo una caída
  en FRV con reducción de captación (-X%) + sesgo negativo en mix (-Y pp)."
- "Crisis general", "desaceleración", "ingresos caen X%":
  → captacion_clientes: -(X * 1.5)
  Explica: "En una crisis, la captación se reduce más que los ingresos existentes."
- "Subida de IPC / inflación": no hay parámetro directo. Menciona que el IPC
  está en 1.2% (bajo) y el impacto indirecto es mínimo en el corto plazo.

COMO PRESENTAR FORECASTS:
- Siempre contextualiza: "Basado en los ultimos 20 meses de datos..."
- Distingue base (mas probable), optimista (requiere acciones) y pesimista (riesgos).
- El escenario optimista requiere acciones comerciales concretas.
- La estacionalidad detectada es tentativa con 20 meses de historia.
- Nunca presentes el forecast como certeza. Usa "se proyecta", "en el escenario base".
- NUNCA inventes datos. Si no tienes el dato, dilo.

FORMATO:
- Espanol bancario profesional. Dato clave en la primera frase.
- Para forecasts: valores mes a mes + narrativa breve. Max 200 palabras preguntas directas.
- Para what-if: impacto cuantificado primero, luego explicacion.
- Para recomendaciones: lista numerada, max 4 items, acciones concretas.
- Si la pregunta es informal, responde directo sin encabezado ejecutivo."""


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

def _safe_json(obj):
    try:
        if hasattr(obj, 'data'):
            data = obj.data
        elif isinstance(obj, dict):
            data = obj
        elif isinstance(obj, list):
            data = obj
        else:
            data = obj
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_forecast_base(horizonte_meses: int = 6, dimension: str = 'entidad',
                      filtro_id: str = None) -> str:
    """Genera proyeccion base para los proximos N meses con 3 escenarios
    (pesimista/base/optimista). horizonte_meses: 3, 6 o 12.
    dimension: 'entidad' (banco completo), 'centro', 'gestor'.
    filtro_id: ID del centro o gestor si dimension no es entidad.
    Usala para: 'proyeccion trimestral', 'como cerraremos el ano',
    'forecast de ingresos', 'que esperamos proximos meses'."""
    try:
        df = _fq.get_serie_ingresos(dimension=dimension, filtro_id=filtro_id)
        if df.empty:
            return json.dumps({"error": "Sin datos historicos para esta dimension"})
        _pe.fit(df)
        forecast = _pe.get_scenarios(horizonte_meses=horizonte_meses)
        macro = _mcs.get_context()
        escenarios = _sb.build(forecast, macro)
        return _safe_json(escenarios)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_macro_context() -> str:
    """Obtiene contexto macroeconomico actual: tipos hipotecarios BCE,
    IPC Espana, tendencias e impacto en cada producto del banco.
    Usala para: 'entorno macro', 'tipos de interes', 'inflacion',
    'como nos afecta la inflacion', 'contexto de mercado'."""
    try:
        ctx = _mcs.get_context()
        return _safe_json(ctx)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def apply_whatif(shocks_json: str, horizonte_meses: int = 6,
                 dimension: str = 'entidad') -> str:
    """Simula impacto de cambios en variables clave.
    shocks_json: JSON string con shocks, ej: '{"tipos_interes": 50, "captacion_clientes": -10}'.
    Shocks disponibles:
    - tipos_interes: puntos basicos (ej: +50 = subida 0.5%)
    - captacion_clientes: % variacion nuevos contratos (ej: -10)
    - reduccion_gastos: % reduccion gastos directos (ej: 15)
    - mix_productos: pp sesgo hacia FRV (ej: +10)
    Usala para: 'que pasa si tipos suben', 'simula perdida clientes',
    'escenario pesimista', 'what-if', 'analisis sensibilidad'."""
    try:
        shocks = json.loads(shocks_json) if isinstance(shocks_json, str) else shocks_json
        result = _sim.simulate(shocks=shocks, horizonte_meses=horizonte_meses, dimension=dimension)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_recommendations(objetivo: str, horizonte_meses: int = 6) -> str:
    """Genera recomendaciones accionables basadas en forecast + macro.
    objetivo: descripcion en lenguaje natural del objetivo.
    Ejemplos: 'maximizar ingresos', 'reducir riesgo', 'mejorar margen'.
    Usala para: 'que deberia hacer', 'como mejorar', 'plan de accion',
    'recomendaciones para el proximo trimestre'."""
    try:
        df = _fq.get_serie_ingresos()
        _pe.fit(df)
        forecast = _pe.get_scenarios(horizonte_meses=horizonte_meses)
        macro = _mcs.get_context()
        escenarios = _sb.build(forecast, macro)
        trend = _pe.get_trend_components()

        recs = {
            'objetivo': objetivo,
            'escenario_base_acumulado': escenarios['escenario_base']['ingresos_acumulados'],
            'escenario_optimista_acumulado': escenarios['escenario_optimista']['ingresos_acumulados'],
            'gap_base_optimista': (escenarios['escenario_optimista']['ingresos_acumulados']
                                   - escenarios['escenario_base']['ingresos_acumulados']),
            'tendencia': trend.get('tendencia', 'N/A'),
            'acciones_para_optimista': escenarios['escenario_optimista'].get('acciones_requeridas', []),
            'riesgos_pesimista': escenarios['escenario_pesimista'].get('drivers_riesgo', []),
            'contexto_macro': macro.get('narrativa_corta', ''),
        }
        return _safe_json(recs)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def compare_scenarios(horizonte_meses: int = 6, shocks_json: str = None) -> str:
    """Tabla comparativa de 3 escenarios (pesimista/base/optimista) mes a mes.
    Incluye ingresos acumulados, probabilidades y spread.
    shocks_json: opcional, JSON de shocks a aplicar antes de comparar.
    Usala para: 'compara escenarios', 'tabla proyecciones',
    'diferencia optimista vs pesimista', 'resumen ejecutivo forecast'."""
    try:
        df = _fq.get_serie_ingresos()
        _pe.fit(df)
        forecast = _pe.get_scenarios(horizonte_meses=horizonte_meses)
        macro = _mcs.get_context()

        shocks = None
        if shocks_json:
            shocks = json.loads(shocks_json) if isinstance(shocks_json, str) else shocks_json

        escenarios = _sb.build(forecast, macro, shocks=shocks)
        tabla = _sb.compare(escenarios)
        tabla['nota_metodologica'] = escenarios.get('nota_metodologica', '')
        return _safe_json(tabla)
    except Exception as e:
        return json.dumps({"error": str(e)})


FORECAST_TOOLS = [
    get_forecast_base,
    get_macro_context,
    apply_whatif,
    get_recommendations,
    compare_scenarios,
]


# ============================================================================
# FORECAST AGENT — ReAct with LangGraph
# ============================================================================

class ForecastAgent:
    """ReAct agent for projections and what-if. Same pattern as CDGAgent v7."""

    def __init__(self):
        self.start_time = datetime.now()
        self._initialized = False
        self._agent = None
        self._conversation_history: Dict[str, list] = {}

        if LANGCHAIN_AVAILABLE and settings and FORECAST_IMPORTS_OK:
            try:
                self.llm = AzureChatOpenAI(
                    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    temperature=0,
                )
                self._agent = create_react_agent(self.llm, FORECAST_TOOLS)
                self._initialized = True
                logger.info("ForecastAgent initialized successfully")
            except Exception as e:
                logger.error(f"ForecastAgent init error: {e}")

        mode = "PRODUCTION" if self._initialized else "FALLBACK"
        logger.info(f"ForecastAgent: {mode}, {len(FORECAST_TOOLS)} tools")

    async def process_message(self, message: str, user_role: str = 'control_gestion',
                              gestor_id: str = None, periodo_base: str = '2026-04',
                              session_id: str = 'default') -> Dict:
        """Process a forecast request and return response dict."""
        start = datetime.now()

        if not self._initialized:
            return {
                'response': 'El modulo de proyecciones no esta disponible. Verifique la configuracion.',
                'tools_used': [],
                'execution_time': 0,
                'escenarios': None,
            }

        history = self._conversation_history.get(session_id, [])

        messages = [SystemMessage(content=FORECAST_SYSTEM_PROMPT)]
        messages += history[-6:]
        context_note = f"[Periodo base: {periodo_base}]"
        if gestor_id:
            context_note += f" [Gestor ID: {gestor_id}]"
        messages.append(HumanMessage(content=f"{context_note} {message}"))

        try:
            result = await self._agent.ainvoke({"messages": messages})

            last_msg = result["messages"][-1]
            response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

            used_tools = [
                m.name for m in result["messages"]
                if hasattr(m, "name") and m.name and m.__class__.__name__ == "ToolMessage"
            ]

            # Update history
            history.append(HumanMessage(content=message))
            history.append(AIMessage(content=response_text))
            self._conversation_history[session_id] = history

            execution_time = (datetime.now() - start).total_seconds()

            return {
                'response': response_text,
                'tools_used': used_tools,
                'execution_time': round(execution_time, 2),
                'escenarios': None,  # Frontend can call /forecast/base separately for chart data
            }

        except Exception as e:
            logger.error(f"ForecastAgent error: {e}", exc_info=True)
            return {
                'response': f'Error en el analisis predictivo: {e}',
                'tools_used': [],
                'execution_time': round((datetime.now() - start).total_seconds(), 2),
                'escenarios': None,
            }

    def get_status(self) -> Dict:
        return {
            'status': 'active' if self._initialized else 'fallback',
            'version': '1.0',
            'tools': [t.name for t in FORECAST_TOOLS],
            'tool_count': len(FORECAST_TOOLS),
        }


# ── Factory ──────────────────────────────────────────────────────────

_forecast_agent_instance = None

def get_forecast_agent() -> ForecastAgent:
    global _forecast_agent_instance
    if _forecast_agent_instance is None:
        _forecast_agent_instance = ForecastAgent()
    return _forecast_agent_instance
