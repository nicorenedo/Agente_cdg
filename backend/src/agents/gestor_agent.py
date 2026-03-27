"""
gestor_agent.py — Copiloto personal del Gestor Comercial

Agente LangChain + Azure OpenAI especializado en la cartera de UN gestor concreto.
Acceso estrictamente limitado: solo puede consultar datos de su propio gestor_id.

Patrón: Tool Pattern + Agentic Pattern (decide qué herramientas usar)
"""

import hashlib
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
    return f"""Eres el copiloto de negocio de {nombre}, gestor comercial del segmento {segmento} en el centro {centro}.

Tu misión es ayudar a {nombre} a entender sus resultados, identificar qué los explica y prepararle para defender su gestión ante el equipo de Control de Gestión (CDG).

PERFIL:
- Gestor ID: {gestor_id} | Segmento: {segmento} | Centro: {centro}
- Período activo: {periodo}

CÓMO AYUDAS AL GESTOR:
1. Explicas el "por qué" detrás de sus KPIs — no solo el número, sino qué lo provoca.
2. Le sitúas vs su centro: ¿está por encima o por debajo de la media? ¿en qué métricas destaca?
3. Le preparas argumentos sólidos para el Business Review: qué ha funcionado bien, qué tiene justificación y qué requiere plan de acción.
4. Detectas alertas tempranas: clientes con caída de margen, productos con coste elevado, desviaciones respecto al precio estándar.
5. Comparas evolución mensual (sep vs oct) para mostrar tendencias.

CONFIDENCIALIDAD — REGLAS INAMOVIBLES:
- Solo tienes acceso a los datos del gestor ID {gestor_id}.
- Si preguntan por otro gestor o datos globales: "No puedo acceder a datos de otros gestores por política de confidencialidad."
- Las comparativas se hacen siempre con benchmarks anónimos del centro, nunca con nombres de otros gestores.

RESTRICCIÓN CRÍTICA — BENCHMARKS:
- NO uses clasificaciones externas como "Top Quartile", "sector bancario", "EXCELENTE", "SOBRESALIENTE" a menos que estén explícitamente en la base de datos.
- Si el gestor pregunta cómo se compara con otros gestores, SOLO usa datos reales de la BD: media del centro, ranking dentro del centro (posición sin revelar nombres ni datos individuales de otros gestores).
- Nunca inventes benchmarks sectoriales. Si no tienes el dato, dilo explícitamente: "No dispongo de datos comparativos externos."
- Las únicas clasificaciones válidas son las que devuelven las herramientas de la BD.

MODELO DE DATOS — IMPORTANTE:
- Ingresos, gastos y ROE son del mes seleccionado ({periodo}). No son acumulados YTD.
- La cartera de contratos es acumulada histórica (FECHA_ALTA <= fin del período).
- En sep-2025 hay 216 contratos activos; en oct-2025 hay 220 (4 contratos nuevos, +1.8%).

ROE — CÓMO USARLO:
- El ROE del gestor es: beneficio_neto / ingresos_totales × 100 (no sobre patrimonio).
- Usa siempre la herramienta get_mi_roe para obtenerlo. Nunca lo calcules manualmente.
- El ROE refleja la rentabilidad de la cartera del gestor en el período seleccionado.

RESTRICCIÓN COMPARATIVAS:
- Para comparar con el centro, usa ÚNICAMENTE get_mi_centro_benchmark — NO requiere parámetros, el centro se resuelve automáticamente. NUNCA pidas el centro_id al usuario.
- No uses datos globales ni datos de grupo (todos los gestores). Solo los tuyos y los de tu centro (anonimizados).
- Si no tienes el dato comparativo, di explícitamente: "No dispongo del dato comparativo para este período."

REPORTE PERSONAL:
- Cuando el gestor pida su reporte personal: usa SIEMPRE get_mi_reporte_personal y presenta los datos en formato estructurado con secciones: 1) KPIs del período, 2) Evolución MoM (sep→oct), 3) Top clientes, 4) Alertas y desviaciones, 5) Recomendaciones.

DETECCIÓN DE TONO Y RESPUESTA EMPÁTICA:
- Si el gestor usa palabras de frustración o urgencia ("no entiendo", "por qué", "explícamelo", "no tiene sentido", "demasiado alto", "injusto", "inaceptable", "ya"), PRIMERO valida su preocupación con una frase breve y empática antes de dar los datos.
- Ejemplos de apertura empática: "Entiendo tu preocupación, te lo explico con detalle." o "Tiene sentido que quieras claridad sobre esto, vamos paso a paso."
- NUNCA empieces directamente con datos o cifras cuando el mensaje tiene carga emocional. El primer párrafo es siempre de reconocimiento.
- CRÍTICO: Aunque el mensaje sea emocional, SIEMPRE llama a las herramientas para obtener los datos reales ANTES de redactar la respuesta. Nunca respondas con explicaciones genéricas sin cifras concretas. Si preguntan por gastos, llama a get_mi_roe. Si preguntan por cartera, llama a get_mi_cartera.
- Después de los datos, cierra SIEMPRE con una frase orientada a la acción: qué puede hacer el gestor con esa información.
- Tono: profesional pero cercano. No distante ni robótico.
- Para respuestas emocionales: usa párrafos fluidos con los datos integrados naturalmente. EVITA listas con ### headers y bullets — escribe en prosa continua.
- Cuando el gestor pregunta por sus gastos: explica en lenguaje de negocio, no técnico. No digas "cuentas 62xxxx" — di "costes operativos de tu cartera". No digas "CONTRATO_ID IS NULL" — di "gastos de estructura del centro que se reparten entre todos los gestores proporcionalmente a tu actividad".
- Los gastos distribuidos del centro NO son una penalización arbitraria: son el coste de los servicios compartidos (operaciones, back-office, tecnología) que soportan tu actividad comercial. Explícalo así cuando el gestor lo cuestione.

REGLA ABSOLUTA — TOOL CALLING:
Antes de responder CUALQUIER pregunta sobre tu cartera, resultados, gastos, ingresos, clientes o rendimiento,
DEBES llamar al menos una herramienta para obtener datos reales de la base de datos.
Esta regla aplica independientemente del tono o estilo de la pregunta:
- "oye que tal voy" → llama get_mis_kpis
- "estoy bien o mal" → llama get_mis_kpis
- "cómo me va" → llama get_mis_kpis
- "resúmeme todo" → llama get_mi_reporte_personal
- "qué tal el mes" → llama get_mis_kpis
Si no llamas una herramienta, tu respuesta será incorrecta porque no tendrás datos reales.
NUNCA respondas sobre métricas financieras usando solo el contexto conversacional — los números cambian
cada mes y solo la base de datos tiene los valores correctos.
- Cuando el gestor pregunte por productos o qué producto priorizar: usa get_mis_productos_detalle (no get_mis_desviaciones).

TONO Y ESTILO:
- Español profesional bancario. Directo y orientado a la acción.
- Primero el diagnóstico (¿qué está pasando?), luego la causa (¿por qué?), luego la recomendación (¿qué hacer?).
- Usa siempre datos reales de las herramientas disponibles. Nunca inventes cifras.
- Si algo no está disponible, dilo claramente.
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
    def get_mi_roe(periodo_consulta: str = periodo) -> str:
        """
        Devuelve el ROE del gestor: beneficio_neto / ingresos_totales × 100 del período.
        Incluye ingresos, gastos directos, gastos redistribuidos, beneficio neto y ROE%.
        Usa siempre esta herramienta cuando el gestor pregunte por su ROE o rentabilidad.
        """
        try:
            result = gestor_queries.calculate_roe_gestor_enhanced(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            )
            data = _extract(result)
            if data:
                return f"ROE del gestor {gestor_id_int} ({periodo_consulta}):\n{data}"
            return "Sin datos de ROE disponibles."
        except Exception as e:
            logger.error(f"get_mi_roe error: {e}")
            return f"Error obteniendo ROE: {e}"

    @tool
    def get_mi_centro_benchmark(periodo_consulta: str = periodo) -> str:
        """
        Devuelve las métricas financieras agregadas del centro al que pertenece este gestor.
        Útil para comparar la performance propia con la media del centro (sin revelar datos individuales).
        No requiere parámetros adicionales — el centro se obtiene automáticamente del perfil del gestor.
        """
        try:
            metricas = basic_queries.get_gestor_metricas_completas(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            )
            datos = _extract(metricas)
            centro_id = datos.get('CENTRO') if datos else None
            if not centro_id:
                return "No se pudo obtener el centro del gestor."
            result = basic_queries.get_centro_metricas_financieras(
                centro_id=int(centro_id), periodo=periodo_consulta
            )
            data = _extract(result)
            if data:
                return f"Métricas del centro {centro_id} ({periodo_consulta}):\n{data}"
            return f"Sin datos del centro para el período {periodo_consulta}."
        except Exception as e:
            logger.error(f"get_mi_centro_benchmark error: {e}")
            return f"Error obteniendo benchmark del centro: {e}"

    @tool
    def get_mi_reporte_personal(periodo_consulta: str = periodo) -> str:
        """
        Genera un reporte personal completo del gestor con: KPIs del período,
        evolución sep→oct, top clientes por margen, desviaciones de precio y datos del centro.
        Llama a esta herramienta cuando el gestor pida su reporte personal o resumen ejecutivo.
        """
        try:
            kpis = _extract(gestor_queries.calculate_roe_gestor_enhanced(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            ))
            evolucion = _extract(gestor_queries.compare_gestor_septiembre_octubre(
                gestor_id=str(gestor_id_int)
            ))
            clientes = _extract(basic_queries.get_gestor_clientes_con_metricas(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            ))
            desviaciones = _extract(gestor_queries.get_desviaciones_precio_gestor_enhanced(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            ))
            reporte = {
                'kpis_periodo': kpis,
                'evolucion_sep_oct': evolucion,
                'clientes': clientes,
                'desviaciones': desviaciones,
            }
            return f"Datos para reporte personal del gestor {gestor_id_int} ({periodo_consulta}):\n{reporte}"
        except Exception as e:
            logger.error(f"get_mi_reporte_personal error: {e}")
            return f"Error generando reporte: {e}"

    @tool
    def get_mis_productos_detalle(periodo_consulta: str = periodo) -> str:
        """
        Devuelve el mix de productos del gestor: qué productos tiene contratados,
        cuántos contratos por producto y los KPIs de rentabilidad del período.
        Usa esta herramienta cuando el gestor pregunte por productos, qué producto
        priorizar, mix de productos, o rendimiento por tipo de producto.
        No uses get_mis_desviaciones para preguntas de estrategia de producto.
        """
        try:
            contratos = basic_queries.get_contratos_by_gestor(gestor_id=gestor_id_int)
            contratos_data = _extract(contratos) or []
            # Agrupar por producto
            producto_counts: Dict[str, int] = {}
            for c in contratos_data:
                desc = c.get('DESC_PRODUCTO', c.get('PRODUCTO_ID', 'Desconocido'))
                producto_counts[desc] = producto_counts.get(desc, 0) + 1
            mix = [f"  - {prod}: {cnt} contratos" for prod, cnt in sorted(producto_counts.items(), key=lambda x: -x[1])]
            kpis = _extract(gestor_queries.get_gestor_performance_enhanced(
                gestor_id=str(gestor_id_int), periodo=periodo_consulta
            ))
            return (
                f"Mix de productos del gestor {gestor_id_int} (contratos acumulados):\n"
                + "\n".join(mix)
                + f"\n\nKPIs período {periodo_consulta}:\n{kpis}"
            )
        except Exception as e:
            logger.error(f"get_mis_productos_detalle error: {e}")
            return f"Error obteniendo detalle de productos: {e}"

    return [
        get_mis_kpis,
        get_mi_cartera,
        get_mis_desviaciones,
        get_evolucion_sep_oct,
        get_mis_clientes,
        get_mi_roe,
        get_mi_centro_benchmark,
        get_mi_reporte_personal,
        get_mis_productos_detalle,
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

                # S46 FIX1: si no se llamó ninguna tool y la pregunta parece financiera,
                # reintentar una vez con instrucción explícita para forzar el tool call.
                _NON_FINANCIAL = {"hola", "gracias", "ok", "vale", "bien", "sí", "no",
                                  "perfecto", "entendido", "de nada", "bye", "adios"}
                _msg_lower = message.lower().strip()
                _is_casual_reply = len(_msg_lower) < 8 or _msg_lower in _NON_FINANCIAL
                if not used_tools and not _is_casual_reply:
                    logger.info("[S46 RETRY] Sin tools en respuesta — reintentando sin historial para forzar tool call")
                    _force_msg = (
                        f"[INSTRUCCIÓN OBLIGATORIA DEL SISTEMA]: Para responder a la pregunta del gestor, "
                        f"DEBES llamar a al menos una herramienta ANTES de redactar cualquier respuesta. "
                        f"Empieza tu respuesta llamando a get_mis_kpis si la pregunta es sobre rendimiento, "
                        f"get_mis_productos_detalle si es sobre productos, o get_mi_reporte_personal para resúmenes.\n\n"
                        f"Pregunta del gestor: {message}"
                    )
                    # Sin historial previo: el LLM no tiene contexto y DEBE llamar tools
                    _messages_retry = [HumanMessage(content=_force_msg)]
                    _result_retry = await self._agent_executor.ainvoke({"messages": _messages_retry})
                    _last_retry = _result_retry["messages"][-1]
                    _response_retry = _last_retry.content if hasattr(_last_retry, "content") else str(_last_retry)
                    _tools_retry = [
                        m.name for m in _result_retry["messages"]
                        if hasattr(m, "name") and m.name and m.__class__.__name__ == "ToolMessage"
                    ]
                    if _tools_retry:
                        logger.info(f"[S46 RETRY] Reintento exitoso — tools: {_tools_retry}")
                        response_text = _response_retry
                        used_tools = _tools_retry
                    else:
                        logger.warning("[S46 RETRY] Reintento tampoco llamo tools — usando respuesta original")

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
                logger.error(
                    f"GestorAgent LangGraph error [{type(e).__name__}]: {e}",
                    exc_info=True,
                )
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
# Caché de instancias — key incluye hash de los params del system prompt
# ═══════════════════════════════════════════════════════════════════

_agent_cache: Dict[str, GestorAgent] = {}


def _compute_agent_key(
    gestor_id: str,
    nombre: str,
    segmento: str,
    centro: str,
    periodo: str,
) -> str:
    """
    S41: Cache key = gestor_id + hash(nombre, segmento, centro, periodo).

    Garantiza que cualquier cambio en el system prompt (nombre, centro, período)
    produce una nueva instancia en lugar de reutilizar la obsoleta.
    """
    payload = f"{nombre}|{segmento}|{centro}|{periodo}"
    h = hashlib.md5(payload.encode()).hexdigest()[:8]
    return f"{gestor_id}:{h}"


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
    Reutiliza instancia cacheada si los parámetros del system prompt no han cambiado.
    Invalida automáticamente cuando cambia el período, nombre, segmento o centro.
    """
    key = _compute_agent_key(gestor_id, nombre, segmento, centro, periodo_default)
    if force_new or key not in _agent_cache:
        logger.info(f"[CACHE MISS] Creando GestorAgent key={key} (gestor={gestor_id}, periodo={periodo_default})")
        _agent_cache[key] = GestorAgent(
            gestor_id=str(gestor_id),
            nombre=nombre,
            segmento=segmento,
            centro=centro,
            periodo_default=periodo_default,
        )
    else:
        logger.debug(f"[CACHE HIT] Reutilizando GestorAgent key={key}")
    return _agent_cache[key]


def get_gestor_agent(gestor_id: str) -> Optional[GestorAgent]:
    """
    Devuelve el agente cacheado más reciente para gestor_id.
    Busca por prefijo porque la key ahora incluye hash de parámetros.
    """
    prefix = f"{gestor_id}:"
    # Python 3.7+ dict preserva orden de inserción → último insertado = más reciente
    match = None
    for k, v in _agent_cache.items():
        if k.startswith(prefix):
            match = v
    return match


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
