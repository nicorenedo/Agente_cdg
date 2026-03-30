# backend/src/agents/cdg_agent.py
"""
CDG Agent v7.0 — ReAct Agent with Tool Calling (LangGraph)
==========================================================
Replaces the keyword-based dispatcher (v6.0) with a pure ReAct agent.
The LLM decides which tools to call based on the user's question.

S52: Complete rewrite. Preserves CDGRequest/CDGResponse/AnalysisType interfaces.
"""

import json
import re
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Dynamic path setup ──────────────────────────────────────────────
_src = os.path.join(os.path.dirname(__file__), '..')
if _src not in sys.path:
    sys.path.insert(0, _src)

# ── Imports with fallbacks ──────────────────────────────────────────
IMPORTS_SUCCESSFUL = True
LANGCHAIN_AVAILABLE = True

try:
    from langchain_openai import AzureChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError as e:
    logger.warning(f"LangChain/LangGraph not available: {e}")
    LANGCHAIN_AVAILABLE = False

try:
    from config import settings
except Exception:
    settings = None

try:
    from queries.basic_queries import basic_queries
    from queries.comparative_queries import comparative_queries
    from queries.period_queries import period_queries
    from queries.deviation_queries import deviation_queries
except Exception as e:
    logger.warning(f"Query imports failed: {e}")
    IMPORTS_SUCCESSFUL = False
    basic_queries = None
    comparative_queries = None
    period_queries = None
    deviation_queries = None


# ============================================================================
# ENUMS Y DATACLASSES — PRESERVED FROM v6.0 FOR COMPATIBILITY
# ============================================================================

class AnalysisType(Enum):
    """Kept for backward compatibility with main.py /agent/specializations"""
    DEEP_GESTOR_ANALYSIS = "deep_gestor_analysis"
    COMPARATIVE_PERFORMANCE = "comparative_performance"
    DEVIATION_DETECTION = "deviation_detection"
    INCENTIVE_CALCULATION = "incentive_calculation"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    EXECUTIVE_REPORTING = "executive_reporting"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    CHART_ADVANCED_GENERATION = "chart_advanced_generation"
    GLOBAL_KPI = "global_kpi"
    EVOLUCION_GESTORES = "evolucion_gestores"
    GENERAL_QUERY = "general_query"
    CENTRO_ANALYSIS = "centro_analysis"
    PRODUCTO_ANALYSIS = "producto_analysis"


@dataclass
class CDGRequest:
    """Request para el CDG Agent — Compatible con chat_agent v11.0"""
    user_message: str
    user_id: Optional[str] = None
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    include_charts: bool = True
    include_recommendations: bool = True
    current_chart_config: Optional[Dict[str, Any]] = None
    chart_interaction_type: Optional[str] = None
    analysis_depth: str = "standard"
    user_role: Optional[str] = None


@dataclass
class CDGResponse:
    """Response del CDG Agent — Compatible con chat_agent v10.0"""
    content: Dict[str, Any]
    charts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'charts': self.charts,
            'recommendations': self.recommendations,
            'metadata': self.metadata,
            'execution_time': self.execution_time,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

CDG_SYSTEM_PROMPT = """Eres el agente de Control de Gestión (CDG Intelligence) de una entidad bancaria.
Tu audiencia es el equipo de Dirección y Control de Gestión — profesionales senior
que necesitan análisis financiero preciso con datos reales.

PERFIL Y ACCESO:
- Tienes acceso completo a todos los datos de la entidad: centros, gestores, productos, contratos.
- Nunca digas que no tienes acceso o que los datos no están disponibles sin intentar obtenerlos primero.
- Si una pregunta requiere datos, LLAMA A LAS HERRAMIENTAS antes de responder.

DATOS DISPONIBLES:
- 5 centros finalistas: Madrid (ID=1), Palma (ID=2), Barcelona (ID=3), Málaga (ID=4), Bilbao (ID=5)
- 30 gestores distribuidos en 5 centros, 5 segmentos (Minorista, Privada, Empresas, Personal, Fondos)
- 3 productos: Préstamo Hipotecario, Depósito a Plazo Fijo, Fondo Renta Variable
- Períodos disponibles: sep-2025 (2025-09) y oct-2025 (2025-10)

MODELO TEMPORAL (MoM — Month-over-Month):
- Ingresos, gastos, ROE y margen son del MES SELECCIONADO, no acumulados YTD.
- Los contratos son acumulados históricos (FECHA_ALTA <= fin del período).
- Sep-2025: 216 contratos, ~600k ingresos. Oct-2025: 220 contratos, ~624k ingresos.

REGLAS DE NEGOCIO:
- Gastos redistribuidos = Gastos centrales x (contratos_gestor / total_contratos_finalistas)
- Semáforo desviaciones: verde <5% | amarillo 5-15% | rojo >15%
- Modelo Fábrica (solo Fondos): Gestora retiene 85%, Banco 15%
- El Depósito a Plazo Fijo tiene margen negativo (-254%) por diseño: es un producto de captación
  donde el banco paga intereses al cliente. Su valor está en la liquidez que financia hipotecas.

REGLA ABSOLUTA — TOOL CALLING:
Para CUALQUIER pregunta sobre datos financieros, resultados, métricas o rendimiento,
DEBES llamar al menos una herramienta ANTES de redactar tu respuesta.
- Si no sabes qué herramienta usar, usa get_metricas_periodo como punto de partida.
- Si la pregunta es compleja, puedes llamar MÚLTIPLES herramientas en secuencia.
- NUNCA respondas con cifras de memoria — los datos cambian cada mes.

COMBINACIONES FRECUENTES:
- "¿cómo estamos?" → get_metricas_periodo
- "¿cómo va [centro]?" → get_metricas_centro con el centro_id correspondiente
- "¿quiénes son los mejores?" → get_ranking_gestores_margen
- "¿qué producto da más?" → get_kpis_productos
- "evolución vs mes pasado" → get_evolucion_sep_oct O get_comparativa_periodos
- "¿hay alertas?" → get_desviaciones_precio + get_ranking_gestores_margen
- "resumen completo" → get_metricas_periodo + get_ranking_gestores_margen + get_kpis_productos
- "comparar dos centros" → get_metricas_centro(id1) + get_metricas_centro(id2)

FORMATO DE RESPUESTA:
- Español bancario profesional, dirigido a Dirección.
- Empieza por el dato principal, luego contexto, luego recomendación.
- Incluye SIEMPRE cifras concretas de las herramientas (euros, porcentajes, número de contratos).
- Si presentas rankings: tabla o lista numerada con cifras reales.
- Cierra con 2-3 recomendaciones accionables basadas en los datos."""


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

def _safe_json(obj):
    """Safely serialize query results to JSON string for the LLM."""
    try:
        if hasattr(obj, 'data'):
            data = obj.data
        elif isinstance(obj, dict) and 'data' in obj:
            data = obj['data']
        else:
            data = obj
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def get_resumen_entidad() -> str:
    """Resumen general de la entidad: total centros, gestores, clientes, contratos, productos, segmentos. Úsala para preguntas generales tipo 'cuántos gestores tenemos' o 'resumen del banco'."""
    try:
        result = basic_queries.get_resumen_general()
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_metricas_periodo(periodo: str) -> str:
    """Métricas financieras del período: ingresos totales, gastos directos, gastos centrales, beneficio neto, margen neto %, ROE grupo, contratos activos. Úsala para '¿cómo va el mes?', 'resultados del banco', 'margen del grupo', 'ROE consolidado', 'resumen del mes'."""
    try:
        result = period_queries.get_periodo_metricas_financieras(periodo)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_metricas_centro(centro_id: int, periodo: str) -> str:
    """Métricas financieras de un centro específico: ingresos, gastos, margen, contratos, gestores, clientes. Los centros son: 1=Madrid, 2=Palma, 3=Barcelona, 4=Málaga, 5=Bilbao. Úsala para '¿cómo va Madrid?', 'datos de Bilbao', comparaciones entre centros."""
    try:
        result = basic_queries.get_centro_metricas_financieras(centro_id, periodo)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_ranking_gestores_margen(periodo: str) -> str:
    """Ranking de los gestores ordenados por margen neto. Incluye nombre, centro, segmento, ingresos, gastos, margen %, beneficio neto, eficiencia. Úsala para '¿quiénes son los mejores gestores?', 'ranking', 'top performers', '¿hay algo que preocupar?' (busca outliers en el ranking)."""
    try:
        result = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_ranking_gestores_ingresos(periodo: str, limit: int = 15) -> str:
    """Ranking de gestores ordenados por ingresos totales. Úsala cuando la pregunta sea específicamente sobre ingresos o revenue, no margen."""
    try:
        result = basic_queries.ranking_gestores_por_ingresos(periodo, limit)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_evolucion_sep_oct() -> str:
    """Evolución de todos los gestores comparando septiembre con octubre 2025: variación de ingresos, gastos, margen, contratos. Clasifica cada gestor como mejora/estable/retroceso. Úsala para '¿cómo hemos evolucionado?', 'comparativa mes pasado', 'quién mejoró', 'tendencia mensual', 'evolución respecto al mes anterior'."""
    try:
        result = comparative_queries.get_evolucion_gestores_sep_oct()
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_kpis_productos(periodo: str) -> str:
    """KPIs globales por tipo de producto: ingresos, gastos directos, beneficio neto, margen %, contratos, clientes para cada producto. Úsala para '¿qué producto es más rentable?', 'mix de productos', 'margen por producto', '¿qué producto nos da más dinero?'."""
    try:
        result = basic_queries.get_producto_kpis_global(periodo)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_desviaciones_precio(periodo: str, threshold: float = 15.0) -> str:
    """Desviaciones críticas entre precio real y precio estándar. Incluye severidad y porcentaje de desviación. Úsala para 'alertas de precio', '¿hay algo que preocupar?', 'desviaciones', 'anomalías'."""
    try:
        result = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, threshold)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_comparativa_periodos(periodo_actual: str, periodo_anterior: str) -> str:
    """Comparación directa entre dos períodos con variaciones absolutas y porcentuales de ingresos, gastos, margen, contratos. Úsala para 'cómo va octubre vs septiembre', 'variación mensual', '¿ha mejorado el margen?'."""
    try:
        result = period_queries.compare_periodos_metricas(periodo_actual, periodo_anterior)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_metricas_gestor_individual(gestor_id: int, periodo: str) -> str:
    """Métricas completas de un gestor específico por nombre o ID. Incluye ingresos, gastos, margen, contratos, clientes. Solo para rol CDG/Dirección consultando un gestor concreto."""
    try:
        result = basic_queries.get_gestor_metricas_completas(gestor_id, periodo)
        return _safe_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


# All tools in a single list
CDG_TOOLS = [
    get_resumen_entidad,
    get_metricas_periodo,
    get_metricas_centro,
    get_ranking_gestores_margen,
    get_ranking_gestores_ingresos,
    get_evolucion_sep_oct,
    get_kpis_productos,
    get_desviaciones_precio,
    get_comparativa_periodos,
    get_metricas_gestor_individual,
]


# ============================================================================
# CDG AGENT v7.0 — ReAct with LangGraph
# ============================================================================

class CDGAgentV6:
    """
    CDG Agent v7.0 — ReAct agent using LangGraph create_react_agent.
    Class name kept as CDGAgentV6 for backward compatibility with main.py imports.
    """

    def __init__(self):
        self.start_time = datetime.now()
        self.imports_successful = IMPORTS_SUCCESSFUL
        self._initialized = False
        self._agent = None
        self._conversation_history: Dict[str, list] = {}

        if LANGCHAIN_AVAILABLE and settings:
            try:
                self.llm = AzureChatOpenAI(
                    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    temperature=0,
                )
                self._agent = create_react_agent(self.llm, CDG_TOOLS)
                self._initialized = True
                logger.info("CDG Agent v7.0 (ReAct) initialized successfully")
            except Exception as e:
                logger.error(f"CDG Agent init error: {e}")
        else:
            logger.warning("CDG Agent: LangChain or settings not available")

        mode = "PRODUCTION" if self._initialized else "FALLBACK"
        print(f"\n{'='*60}")
        print(f"🚀 CDG AGENT v7.0 INICIALIZADO (ReAct)")
        print(f"   Modo: {mode}")
        print(f"   Azure OpenAI: {'✅ Conectado' if self._initialized else '❌ No disponible'}")
        print(f"   Tools: {len(CDG_TOOLS)} disponibles")
        print(f"   Queries: {'✅ Todas disponibles' if self.imports_successful else '⚠️ Fallback'}")
        print(f"{'='*60}\n")

    # ── Public interface ────────────────────────────────────────────

    async def process_request(self, request: CDGRequest) -> CDGResponse:
        """Main entry point — called by chat_agent._execute_cdg_agent_flow()"""
        start_time = datetime.now()
        periodo = request.periodo or "2025-10"

        try:
            if not self._initialized:
                return self._fallback_response(request, start_time)

            session_id = request.user_id or "default"
            history = self._conversation_history.get(session_id, [])

            # Build messages
            messages = [SystemMessage(content=CDG_SYSTEM_PROMPT)]
            messages += history[-6:]  # last 3 turns
            messages.append(HumanMessage(
                content=f"[Período activo: {periodo}] {request.user_message}"
            ))

            logger.info(f"[CDG ReAct] Invoking agent for: '{request.user_message[:80]}...'")

            # Invoke ReAct agent
            result = await self._agent.ainvoke({"messages": messages})

            last_msg = result["messages"][-1]
            response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

            # Extract tools used
            used_tools = [
                m.name for m in result["messages"]
                if hasattr(m, "name") and m.name and m.__class__.__name__ == "ToolMessage"
            ]
            logger.info(f"[CDG ReAct] Tools used: {used_tools}")

            # Retry if no concrete data in response but tools were called
            if not self._has_concrete_data(response_text) and used_tools:
                logger.info("[CDG ReAct] Response lacks concrete data — retrying")
                retry_messages = list(result["messages"])
                retry_messages.append(HumanMessage(
                    content="Tu respuesta anterior no incluye cifras concretas de la base de datos. "
                            "Por favor incluye los datos reales con euros, porcentajes y números de contratos."
                ))
                result2 = await self._agent.ainvoke({"messages": retry_messages})
                last2 = result2["messages"][-1]
                retry_text = last2.content if hasattr(last2, "content") else str(last2)
                if self._has_concrete_data(retry_text):
                    response_text = retry_text
                    extra_tools = [
                        m.name for m in result2["messages"]
                        if hasattr(m, "name") and m.name and m.__class__.__name__ == "ToolMessage"
                    ]
                    used_tools += extra_tools

            # Update conversation history
            history.append(HumanMessage(content=request.user_message))
            history.append(AIMessage(content=response_text))
            self._conversation_history[session_id] = history

            execution_time = (datetime.now() - start_time).total_seconds()

            return CDGResponse(
                content={
                    "analysis_type": "react_agent",
                    "periodo": periodo,
                    "results": {"response_text": response_text},
                    "data_sources": used_tools,
                    "confidence_score": 0.95 if used_tools else 0.5,
                },
                charts=[],
                recommendations=self._extract_recommendations(response_text),
                metadata={
                    "flow_type": "CDG_AGENT",
                    "agent_version": "7.0-react",
                    "tools_used": used_tools,
                    "tool_count": len(used_tools),
                },
                execution_time=execution_time,
                confidence_score=0.95 if used_tools else 0.5,
                created_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"CDG Agent error: {e}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            return CDGResponse(
                content={
                    "error": str(e),
                    "message": "Error en análisis. El sistema puede manejar consultas básicas.",
                },
                execution_time=execution_time,
                confidence_score=0.0,
                created_at=datetime.now(),
            )

    def get_agent_status(self) -> Dict[str, Any]:
        """Status endpoint — called by main.py"""
        uptime = datetime.now() - self.start_time
        return {
            'status': 'active' if self._initialized else 'fallback',
            'version': '7.0 - ReAct Agent',
            'mode': 'PRODUCTION' if self._initialized else 'FALLBACK',
            'uptime_seconds': uptime.total_seconds(),
            'specializations': [at.value for at in AnalysisType],
            'integration_mode': 'chat_agent_v10_compatible',
            'query_engines_available': [t.name for t in CDG_TOOLS],
            'ai_capabilities': self._initialized,
            'tool_count': len(CDG_TOOLS),
        }

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _has_concrete_data(text: str) -> bool:
        patterns = [r'\d+[.,]\d+', r'€', r'\d+\s*%', r'\d{4,}']
        return any(re.search(p, text) for p in patterns)

    @staticmethod
    def _extract_recommendations(text: str) -> List[str]:
        recs = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            low = line.lower()
            if any(kw in low for kw in ['recomend', 'acción', 'accion', 'oportunidad',
                                         'optimizar', 'priorizar', 'estrateg', 'mejorar']):
                clean = re.sub(r'^[\d\.\-\*\•]+\s*', '', line).strip()
                if len(clean) > 15:
                    recs.append(clean)
        return recs[:5]

    def _fallback_response(self, request: CDGRequest, start_time: datetime) -> CDGResponse:
        return CDGResponse(
            content={
                "error": "CDG Agent no inicializado",
                "message": "El sistema de análisis avanzado no está disponible.",
            },
            execution_time=(datetime.now() - start_time).total_seconds(),
            confidence_score=0.0,
            created_at=datetime.now(),
        )


# ============================================================================
# CONVENIENCE FUNCTIONS — PRESERVED FOR COMPATIBILITY
# ============================================================================

def create_cdg_agent() -> CDGAgentV6:
    """Factory — called by main.py and chat_agent.py"""
    return CDGAgentV6()


async def process_complex_analysis(user_message: str, **kwargs) -> Dict[str, Any]:
    """Async wrapper — called by main.py"""
    agent = create_cdg_agent()
    request = CDGRequest(user_message=user_message, **kwargs)
    response = await agent.process_request(request)
    return response.to_dict()
