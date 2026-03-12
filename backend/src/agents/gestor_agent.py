"""
gestor_agent.py — Copiloto personal del Gestor Comercial

Agente LangChain + Azure OpenAI especializado en la cartera de UN gestor concreto.
Acceso estrictamente limitado: solo puede consultar datos de su propio gestor_id.

Patrón: Tool Pattern + Agentic Pattern (decide qué herramientas usar)
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Resolver paths ──────────────────────────────────────────────────
_current = Path(__file__).resolve()
_src_dir = _current.parent.parent      # backend/src/
_backend_dir = _src_dir.parent         # backend/

for _p in [str(_src_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Imports con fallbacks ───────────────────────────────────────────
try:
    from config import settings
except ImportError:
    class _MockSettings:
        AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
        AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        AZURE_OPENAI_DEPLOYMENT_ID = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4")
        AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    settings = _MockSettings()

try:
    from langchain_openai import AzureChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain no disponible -- GestorAgent funcionara en modo degradado")

try:
    from queries.basic_queries import basic_queries
    from queries.gestor_queries import gestor_queries
    from queries.deviation_queries import deviation_queries
    from queries.period_queries import period_queries
except ImportError:
    try:
        from src.queries.basic_queries import basic_queries
        from src.queries.gestor_queries import gestor_queries
        from src.queries.deviation_queries import deviation_queries
        from src.queries.period_queries import period_queries
    except ImportError:
        basic_queries = None
        gestor_queries = None
        deviation_queries = None
        period_queries = None
        logger.warning("⚠️ Queries no disponibles — GestorAgent en modo mock")

try:
    from utils.auth import UserRole, access_guard
except ImportError:
    from src.utils.auth import UserRole, access_guard


# ═══════════════════════════════════════════════════════════════════
# System prompt del gestor (sección 8 del CLAUDE.md)
# ═══════════════════════════════════════════════════════════════════

def _build_system_prompt(
    gestor_id: str,
    nombre: str,
    segmento: str,
    centro: str,
    periodo: str = "2025-10",
) -> str:
    return f"""Eres el copiloto personal de {nombre}, gestor comercial de Banca March.

PERFIL DEL GESTOR:
- ID: {gestor_id}
- Segmento: {segmento}
- Centro: {centro}
- Período de análisis por defecto: {periodo}

REGLAS DE ACCESO CRÍTICAS:
1. Solo puedes acceder a los datos del gestor ID {gestor_id}.
2. Si el usuario pregunta por otro gestor o por datos globales de otros gestores, rechaza SIEMPRE con: "No puedo acceder a datos de otros gestores por política de confidencialidad bancaria."
3. Cuando hagas comparativas, usa solo benchmarks anónimos del centro o segmento, nunca datos identificados de otros gestores.

COMPORTAMIENTO:
- Responde siempre en español con tono profesional bancario.
- Antes de responder, usa las herramientas disponibles para obtener datos reales.
- Si no tienes datos suficientes, indícalo claramente en lugar de inventar.
- Estructura las respuestas con encabezados cuando sean análisis extensos.
- Destaca desviaciones importantes (>15%) con alertas claras.

MÉTRICAS CLAVE A PRIORIZAR:
- Margen aportado (ingresos cuentas 76xxxx + gastos directos cuentas 62/64/68/69)
- Número de contratos y clientes activos
- Evolución mensual Sep-2025 vs Oct-2025
- Desviaciones vs precio estándar (STD)
"""


# ═══════════════════════════════════════════════════════════════════
# Herramientas (Tools) — cada una filtra por gestor_id
# ═══════════════════════════════════════════════════════════════════

def _extract(result):
    """Extrae los datos de un QueryResult, dict o list."""
    if result is None:
        return None
    if hasattr(result, "data"):
        return result.data
    return result  # dict o list directo


def _make_tools(gestor_id: str, periodo: str = "2025-10"):
    """Construye las herramientas del agente ya vinculadas al gestor_id."""

    gestor_id_int = int(gestor_id)

    @tool
    def get_mis_kpis(periodo_consulta: str = periodo) -> str:
        """
        Devuelve los KPIs principales del gestor: ingresos, gastos, margen aportado,
        número de contratos y clientes para el período indicado.
        Usa formato YYYY-MM, por ejemplo '2025-10'.
        """
        try:
            result = gestor_queries.get_gestor_performance_enhanced(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            )
            if result and result.data:
                return f"KPIs del gestor {gestor_id_int} ({periodo_consulta}):\n{result.data}"
            return f"Sin datos de KPIs para el período {periodo_consulta}."
        except Exception as e:
            logger.error(f"get_mis_kpis error: {e}")
            return f"Error obteniendo KPIs: {e}"

    @tool
    def get_mi_cartera(periodo_consulta: str = periodo) -> str:
        """
        Resumen de la cartera del gestor: número de contratos, clientes,
        ingresos, gastos y margen para el período indicado.
        """
        try:
            result = basic_queries.get_gestor_metricas_completas(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            )
            data = _extract(result)
            if data:
                return f"Resumen de cartera del gestor {gestor_id_int} ({periodo_consulta}):\n{data}"
            return "Sin datos de cartera disponibles."
        except Exception as e:
            logger.error(f"get_mi_cartera error: {e}")
            return f"Error obteniendo cartera: {e}"

    @tool
    def get_mis_desviaciones(periodo_consulta: str = periodo) -> str:
        """
        Analiza las desviaciones del coste efectivo real vs precio estándar (STD)
        por producto en la cartera del gestor.
        Semáforo: ROJO >15%, AMARILLO 5-15%, VERDE <5%.
        """
        try:
            result = gestor_queries.get_desviaciones_precio_gestor_enhanced(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            )
            data = _extract(result)
            if data:
                return f"Desviaciones del gestor {gestor_id_int} ({periodo_consulta}):\n{data}"
            return "Sin desviaciones significativas (todas dentro del umbral del 15%)."
        except Exception as e:
            logger.error(f"get_mis_desviaciones error: {e}")
            return f"Error obteniendo desviaciones: {e}"

    @tool
    def get_evolucion_sep_oct() -> str:
        """
        Compara el rendimiento del gestor entre septiembre y octubre 2025.
        Muestra variación en ingresos, gastos, margen y contratos.
        """
        try:
            result = gestor_queries.compare_gestor_septiembre_octubre(
                gestor_id=str(gestor_id_int)
            )
            data = _extract(result)
            if data:
                return f"Evolucion Sep-Oct del gestor {gestor_id_int}:\n{data}"
            return "Sin datos de evolucion disponibles."
        except Exception as e:
            logger.error(f"get_evolucion_sep_oct error: {e}")
            return f"Error obteniendo evolucion: {e}"

    @tool
    def get_mis_clientes(periodo_consulta: str = periodo) -> str:
        """
        Lista los clientes del gestor con sus métricas financieras:
        ingresos, gastos, beneficio neto y número de contratos por cliente.
        """
        try:
            result = basic_queries.get_gestor_clientes_con_metricas(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            )
            data = _extract(result)
            if data:
                return f"Clientes del gestor {gestor_id_int} ({periodo_consulta}):\n{data}"
            return "Sin datos de clientes disponibles."
        except Exception as e:
            logger.error(f"get_mis_clientes error: {e}")
            return f"Error obteniendo clientes: {e}"

    @tool
    def get_resumen_periodo(periodo_consulta: str = periodo) -> str:
        """
        Obtiene el resumen financiero consolidado del período indicado para el gestor.
        Incluye totales de ingresos, gastos directos y beneficio neto.
        """
        try:
            result = period_queries.get_periodo_metricas_financieras(
                periodo=periodo_consulta
            )
            data = _extract(result)
            if data:
                return f"Resumen financiero del periodo {periodo_consulta}:\n{data}"
            return f"Sin datos para el periodo {periodo_consulta}."
        except Exception as e:
            logger.error(f"get_resumen_periodo error: {e}")
            return f"Error obteniendo resumen: {e}"

    return [
        get_mis_kpis,
        get_mi_cartera,
        get_mis_desviaciones,
        get_evolucion_sep_oct,
        get_mis_clientes,
        get_resumen_periodo,
    ]


# ═══════════════════════════════════════════════════════════════════
# GestorAgent
# ═══════════════════════════════════════════════════════════════════

class GestorAgent:
    """
    Copiloto personal del Gestor Comercial.

    Uso:
        agent = GestorAgent(gestor_id="18", nombre="Laia Vila Costa",
                            segmento="Banca Personal", centro="BARCELONA-BALMES")
        response = await agent.process_message("¿Cuál es mi margen este mes?")
    """

    def __init__(
        self,
        gestor_id: str,
        nombre: str = "Gestor",
        segmento: str = "No especificado",
        centro: str = "No especificado",
        periodo_default: str = "2025-10",
    ):
        self.gestor_id = str(gestor_id)
        self.nombre = nombre
        self.segmento = segmento
        self.centro = centro
        self.periodo_default = periodo_default
        self.conversation_history: List[Dict[str, str]] = []
        self._agent_executor: Optional[Any] = None
        self._initialized = False

        self._init_agent()

    def _init_agent(self) -> None:
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain no disponible -- GestorAgent en modo fallback")
            return

        try:
            llm = AzureChatOpenAI(
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                temperature=0,
            )

            tools = _make_tools(self.gestor_id, self.periodo_default)

            self._system_prompt = _build_system_prompt(
                gestor_id=self.gestor_id,
                nombre=self.nombre,
                segmento=self.segmento,
                centro=self.centro,
                periodo=self.periodo_default,
            )

            # LangChain 1.x / LangGraph API
            self._agent_executor = create_react_agent(
                llm,
                tools,
                prompt=self._system_prompt,
            )
            self._initialized = True
            logger.info(f"GestorAgent inicializado para gestor {self.gestor_id} ({self.nombre})")

        except Exception as e:
            logger.error(f"Error inicializando GestorAgent: {e}")
            self._initialized = False

    # ── Procesamiento de mensajes ────────────────────────────────────

    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del gestor y devuelve la respuesta del copiloto.

        Returns dict con:
            response: str — respuesta en lenguaje natural
            used_tools: list — herramientas usadas
            execution_time: float
            gestor_id: str
        """
        start = datetime.now()

        # Guardia de acceso: detectar intento cross-gestor
        perm = access_guard.check_message_permission(
            message, UserRole.GESTOR, self.gestor_id
        )
        if not perm["allowed"]:
            target = perm.get("target_gestor")
            return {
                "response": (
                    f"🔐 **Acceso restringido**\n\n"
                    f"No puedo acceder a los datos del gestor {target}. "
                    f"Por política de confidencialidad bancaria, solo tengo acceso "
                    f"a tu propia cartera (gestor {self.gestor_id}).\n\n"
                    f"💡 Puedes consultarme sobre:\n"
                    f"- Tus KPIs y métricas personales\n"
                    f"- Tu cartera de contratos y clientes\n"
                    f"- Tus desviaciones vs precio estándar\n"
                    f"- Tu evolución Sep-Oct 2025"
                ),
                "used_tools": [],
                "execution_time": 0.0,
                "gestor_id": self.gestor_id,
                "blocked": True,
            }

        # ── LangGraph path ───────────────────────────────────────────
        if self._initialized and self._agent_executor is not None:
            try:
                # Construir historial: LangGraph recibe lista de mensajes
                messages = []
                for turn in self.conversation_history[-10:]:
                    if turn["role"] == "user":
                        messages.append(HumanMessage(content=turn["content"]))
                    else:
                        messages.append(AIMessage(content=turn["content"]))
                messages.append(HumanMessage(content=message))

                result = await self._agent_executor.ainvoke({"messages": messages})

                # LangGraph devuelve {"messages": [...]}, último mensaje es la respuesta
                last_msg = result["messages"][-1]
                response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

                # Herramientas usadas: mensajes de tipo ToolMessage
                used_tools = [
                    m.name for m in result["messages"]
                    if hasattr(m, "name") and m.name and m.__class__.__name__ == "ToolMessage"
                ]

                # Actualizar historial
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": response_text})

                return {
                    "response": response_text,
                    "used_tools": used_tools,
                    "execution_time": round((datetime.now() - start).total_seconds(), 3),
                    "gestor_id": self.gestor_id,
                    "blocked": False,
                }

            except Exception as e:
                logger.error(f"GestorAgent LangGraph error: {e}")
                # Fall through al modo degradado

        # ── Fallback sin LangChain ───────────────────────────────────
        return self._fallback_response(message, start)

    def _fallback_response(self, message: str, start: datetime) -> Dict[str, Any]:
        """Respuesta básica cuando LangChain no está disponible."""
        msg_lower = message.lower()

        if any(k in msg_lower for k in ["kpi", "margen", "resultado", "ingresos"]):
            note = "Para ver tus KPIs, el sistema LangChain necesita estar configurado. Contacta al administrador."
        elif any(k in msg_lower for k in ["cartera", "contrato", "cliente"]):
            note = "Para ver tu cartera, el sistema LangChain necesita estar configurado."
        else:
            note = f"Hola {self.nombre}, soy tu copiloto CDG. El sistema de análisis avanzado no está disponible en este momento. Contacta al administrador para activar el servicio completo."

        return {
            "response": note,
            "used_tools": [],
            "execution_time": round((datetime.now() - start).total_seconds(), 3),
            "gestor_id": self.gestor_id,
            "blocked": False,
            "fallback": True,
        }

    # ── Estado del agente ────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "gestor_id": self.gestor_id,
            "nombre": self.nombre,
            "segmento": self.segmento,
            "centro": self.centro,
            "periodo_default": self.periodo_default,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "initialized": self._initialized,
            "conversation_turns": len(self.conversation_history) // 2,
        }

    def reset_conversation(self) -> None:
        """Limpia el historial de conversación."""
        self.conversation_history = []
        logger.info(f"Historial del gestor {self.gestor_id} reiniciado")


# ═══════════════════════════════════════════════════════════════════
# Caché de instancias por gestor_id
# ═══════════════════════════════════════════════════════════════════

_agent_cache: Dict[str, GestorAgent] = {}


def create_gestor_agent(
    gestor_id: str,
    nombre: str = "Gestor",
    segmento: str = "No especificado",
    centro: str = "No especificado",
    periodo_default: str = "2025-10",
    force_new: bool = False,
) -> GestorAgent:
    """
    Devuelve un GestorAgent para el gestor_id dado.
    Reutiliza instancia cacheada si ya existe (a menos que force_new=True).
    """
    key = str(gestor_id)
    if force_new or key not in _agent_cache:
        _agent_cache[key] = GestorAgent(
            gestor_id=key,
            nombre=nombre,
            segmento=segmento,
            centro=centro,
            periodo_default=periodo_default,
        )
    return _agent_cache[key]


def get_gestor_agent(gestor_id: str) -> Optional[GestorAgent]:
    """Devuelve el agente cacheado para gestor_id, o None si no existe."""
    return _agent_cache.get(str(gestor_id))


async def process_gestor_message(
    gestor_id: str,
    message: str,
    nombre: str = "Gestor",
    segmento: str = "No especificado",
    centro: str = "No especificado",
) -> Dict[str, Any]:
    """
    Función de conveniencia: obtiene (o crea) el agente del gestor
    y procesa el mensaje.
    """
    agent = create_gestor_agent(
        gestor_id=gestor_id,
        nombre=nombre,
        segmento=segmento,
        centro=centro,
    )
    return await agent.process_message(message)


__all__ = [
    "GestorAgent",
    "create_gestor_agent",
    "get_gestor_agent",
    "process_gestor_message",
]
