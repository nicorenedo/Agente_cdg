"""
Chat Agent para CDG - Interfaz Conversacional para Control de Gestión Banca March
================================================================================

Módulo que gestiona la interacción conversacional con usuarios (gestores) a través 
del agente CDG. Implementa manejo de contexto, sesiones, clasificación de intenciones,
procesamiento de feedback y orquestación con el agente coordinador principal.

Autor: Agente CDG Development Team
Fecha: 2025-08-01
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass, field

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importar módulos CDG y prompts específicos
try:
    from ..agents.cdg_agent import CDGAgent, CDGRequest, ResponseFormat
    from ..utils.initial_agent import iniciar_agente_llm
    
    # Importar prompts específicos del chat agent
    from ..prompts.system_prompts import (
        CHAT_CONVERSATIONAL_SYSTEM_PROMPT,
        CHAT_FEEDBACK_SYSTEM_PROMPT,
        CHAT_INTENT_CLASSIFICATION_PROMPT,
        CHAT_PERSONALIZATION_SYSTEM_PROMPT
    )
    from ..prompts.user_prompts import (
        FEEDBACK_PROCESSING_USER_PROMPT,
        CONVERSATION_CONTEXT_USER_PROMPT,
        PERSONALIZATION_LEARNING_USER_PROMPT,
        INTENT_CLARIFICATION_USER_PROMPT,
        DYNAMIC_DASHBOARD_USER_PROMPT,
        build_feedback_processing_prompt,
        build_conversation_context_prompt,
        build_personalization_learning_prompt
    )
except ImportError:
    from agents.cdg_agent import CDGAgent, CDGRequest, ResponseFormat
    from utils.initial_agent import iniciar_agente_llm
    
    from prompts.system_prompts import (
        CHAT_CONVERSATIONAL_SYSTEM_PROMPT,
        CHAT_FEEDBACK_SYSTEM_PROMPT,
        CHAT_INTENT_CLASSIFICATION_PROMPT,
        CHAT_PERSONALIZATION_SYSTEM_PROMPT
    )
    from prompts.user_prompts import (
        FEEDBACK_PROCESSING_USER_PROMPT,
        CONVERSATION_CONTEXT_USER_PROMPT,
        PERSONALIZATION_LEARNING_USER_PROMPT,
        INTENT_CLARIFICATION_USER_PROMPT,
        DYNAMIC_DASHBOARD_USER_PROMPT,
        build_feedback_processing_prompt,
        build_conversation_context_prompt,
        build_personalization_learning_prompt
    )

# Logger para auditoría completa
logger = logging.getLogger(__name__)

# ============================================================================
# MODELOS DE DATOS PARA LA API DE CHAT
# ============================================================================

class ChatMessage(BaseModel):
    """Modelo para mensajes de chat entrantes"""
    user_id: str
    message: str
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True
    context: Dict[str, Any] = {}
    user_feedback: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Modelo para respuestas de chat"""
    response: str
    response_type: str
    charts: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    metadata: Dict[str, Any] = {}
    execution_time: float
    confidence_score: float
    timestamp: str
    session_id: str

# ============================================================================
# GESTIÓN AVANZADA DE SESIONES DE CHAT
# ============================================================================

@dataclass
class ChatSession:
    """Gestiona el estado de una sesión de chat individual con contexto y personalización"""
    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    personalization_profile: Dict[str, Any] = field(default_factory=dict)
    
    def add_interaction(self, user_message: str, agent_response: Dict[str, Any], intent: str = "general"):
        """Añade una interacción al historial con metadatos de personalización"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'agent_response': agent_response,
            'intent': intent,
            'session_id': self.session_id
        })
        self.last_active = datetime.now()
        
        # Mantener solo las últimas 50 interacciones
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_recent_context(self, max_interactions: int = 10) -> List[Dict[str, Any]]:
        """Obtiene las interacciones más recientes para contexto conversacional"""
        return self.conversation_history[-max_interactions:]
    
    def update_preferences(self, new_preferences: Dict[str, Any]):
        """Actualiza las preferencias del usuario"""
        self.user_preferences.update(new_preferences)
        logger.info(f"Preferencias actualizadas para usuario {self.user_id}")
    
    def clear_history(self):
        """Limpia el historial de conversación manteniendo preferencias"""
        self.conversation_history.clear()
        logger.info(f"Historial limpiado para sesión {self.session_id}")

class ChatSessionManager:
    """Gestor centralizado de sesiones de chat con capacidades avanzadas"""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
    
    def get_or_create_session(self, user_id: str) -> ChatSession:
        """Obtiene sesión existente o crea nueva con inicialización de preferencias"""
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession(user_id=user_id)
            logger.info(f"🆕 Nueva sesión de chat creada para usuario {user_id}")
        
        # Actualizar última actividad
        self.sessions[user_id].last_active = datetime.now()
        return self.sessions[user_id]
    
    def add_websocket_connection(self, user_id: str, websocket: WebSocket):
        """Registra conexión WebSocket para comunicación en tiempo real"""
        self.websocket_connections[user_id] = websocket
        logger.info(f"🔌 Conexión WebSocket registrada para usuario {user_id}")
    
    def remove_websocket_connection(self, user_id: str):
        """Elimina conexión WebSocket"""
        if user_id in self.websocket_connections:
            del self.websocket_connections[user_id]
            logger.info(f"🔌 Conexión WebSocket eliminada para usuario {user_id}")
    
    def reset_session(self, user_id: str):
        """Reinicia la sesión conservando el perfil de personalización"""
        if user_id in self.sessions:
            self.sessions[user_id].clear_history()
    
    def cleanup_inactive_sessions(self, max_inactive_hours: int = 24):
        """Limpia sesiones inactivas"""
        cutoff_time = datetime.now() - timedelta(hours=max_inactive_hours)
        inactive_users = [
            user_id for user_id, session in self.sessions.items()
            if session.last_active < cutoff_time
        ]
        
        for user_id in inactive_users:
            del self.sessions[user_id]
            logger.info(f"🧹 Sesión inactiva eliminada para usuario {user_id}")

# ============================================================================
# AGENTE DE CHAT PRINCIPAL CON INTEGRACIÓN DE PROMPTS
# ============================================================================

class CDGChatAgent:
    """
    Agente de chat inteligente que orquesta conversaciones con el agente CDG principal.
    Integra clasificación de intenciones, procesamiento de feedback y personalización.
    """
    
    def __init__(self):
        """Inicializa el agente de chat con todos los módulos y prompts integrados"""
        self.cdg_agent = CDGAgent()
        self.session_manager = ChatSessionManager()
        self.llm_client = iniciar_agente_llm()
        self.start_time = datetime.now()
        
        # Configurar prompts específicos del chat
        self.conversation_system_prompt = CHAT_CONVERSATIONAL_SYSTEM_PROMPT
        self.feedback_system_prompt = CHAT_FEEDBACK_SYSTEM_PROMPT
        self.intent_classification_prompt = CHAT_INTENT_CLASSIFICATION_PROMPT
        self.personalization_system_prompt = CHAT_PERSONALIZATION_SYSTEM_PROMPT
        
        logger.info("🚀 CDG Chat Agent inicializado con prompts integrados")

    async def process_chat_message(self, chat_message: ChatMessage) -> ChatResponse:
        """
        Procesa un mensaje de chat con clasificación de intención y personalización
        
        Args:
            chat_message: Mensaje de chat estructurado del usuario
            
        Returns:
            ChatResponse: Respuesta completa con análisis, gráficos y recomendaciones
        """
        start_time = datetime.now()
        session = self.session_manager.get_or_create_session(chat_message.user_id)
        
        try:
            # 1. Sanitización y validación del mensaje
            sanitized_message = self._sanitize_message(chat_message.message)
            if not sanitized_message:
                raise ValueError("Mensaje vacío o inválido")
            
            # 2. Clasificación de intención usando prompts específicos
            intent, confidence = await self._classify_user_intent(sanitized_message, session)
            
            # 3. Construir contexto conversacional
            conversation_context = self._build_conversation_context(session, sanitized_message)
            
            # 4. Crear request para el agente CDG con contexto enriquecido
            cdg_request = CDGRequest(
                user_message=sanitized_message,
                user_id=chat_message.user_id,
                gestor_id=chat_message.gestor_id,
                periodo=chat_message.periodo,
                context={**chat_message.context, **conversation_context},
                response_format=ResponseFormat.JSON,
                include_charts=chat_message.include_charts,
                include_recommendations=chat_message.include_recommendations
            )
            
            # 5. Procesar con el agente CDG coordinador
            cdg_response = await self.cdg_agent.process_request(cdg_request)
            
            # 6. Formatear respuesta para interfaz conversacional
            formatted_response = self._format_response_for_chat(cdg_response, session.user_preferences)
            
            # 7. Crear respuesta de chat estructurada
            chat_response = ChatResponse(
                response=formatted_response,
                response_type=cdg_response.response_type.value,
                charts=cdg_response.charts,
                recommendations=cdg_response.recommendations,
                metadata={
                    **cdg_response.metadata,
                    'intent': intent,
                    'conversation_context': len(session.conversation_history)
                },
                execution_time=cdg_response.execution_time,
                confidence_score=confidence,
                timestamp=cdg_response.created_at.isoformat(),
                session_id=session.session_id
            )
            
            # 8. Añadir interacción al historial de sesión
            session.add_interaction(sanitized_message, chat_response.dict(), intent)
            
            # 9. Procesar feedback si está presente
            if chat_message.user_feedback:
                await self._process_user_feedback_with_prompts(
                    chat_message.user_id, 
                    chat_message.user_feedback, 
                    sanitized_message,
                    cdg_response
                )
            
            # 10. Actualizar perfil de personalización
            await self._update_personalization_profile(session, intent, chat_response)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Chat procesado para usuario {chat_message.user_id} en {execution_time:.2f}s")
            
            return chat_response
            
        except Exception as e:
            logger.error(f"❌ Error procesando chat para usuario {chat_message.user_id}: {e}")
            return self._create_error_response(str(e), session.session_id, start_time)

    async def _classify_user_intent(self, message: str, session: ChatSession) -> Tuple[str, float]:
        """
        Clasifica la intención del usuario usando el prompt específico de clasificación
        
        Args:
            message: Mensaje del usuario
            session: Sesión actual del usuario
            
        Returns:
            Tuple[str, float]: Intención clasificada y nivel de confianza
        """
        try:
            # Construir prompt de clasificación con contexto
            classification_user_prompt = f"""
            Mensaje del usuario: "{message}"
            
            Contexto de la conversación:
            - Interacciones previas: {len(session.conversation_history)}
            - Último análisis: {session.conversation_history[-1].get('intent', 'ninguno') if session.conversation_history else 'ninguno'}
            
            Clasifica la intención según las categorías disponibles.
            """
            
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.intent_classification_prompt},
                    {"role": "user", "content": classification_user_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content)
            intent = result.get('intent', 'general_inquiry')
            confidence = float(result.get('confidence', 0.5))
            
            logger.info(f"🎯 Intención clasificada: {intent} (confianza: {confidence:.2f})")
            return intent, confidence
            
        except Exception as e:
            logger.warning(f"Error en clasificación de intención: {e}")
            return 'general_inquiry', 0.5

    def _build_conversation_context(self, session: ChatSession, current_message: str) -> Dict[str, Any]:
        """
        Construye contexto conversacional usando el prompt específico
        
        Args:
            session: Sesión actual del usuario
            current_message: Mensaje actual del usuario
            
        Returns:
            Dict con contexto conversacional enriquecido
        """
        recent_history = session.get_recent_context(5)
        
        context = {
            'conversation_length': len(session.conversation_history),
            'recent_intents': [h.get('intent', 'general') for h in recent_history],
            'user_preferences': session.user_preferences,
            'session_duration': (datetime.now() - session.created_at).total_seconds(),
            'personalization_profile': session.personalization_profile
        }
        
        return context

    async def _process_user_feedback_with_prompts(
        self, 
        user_id: str, 
        feedback: Dict[str, Any], 
        original_query: str,
        agent_response: Any
    ):
        """
        Procesa feedback del usuario usando el prompt específico de feedback
        
        Args:
            user_id: ID del usuario
            feedback: Feedback estructurado del usuario
            original_query: Consulta original del usuario
            agent_response: Respuesta que proporcionó el agente
        """
        try:
            # Construir prompt de procesamiento de feedback
            feedback_prompt = build_feedback_processing_prompt(
                user_id=user_id,
                original_query=original_query,
                agent_response=str(agent_response.content),
                feedback_data=feedback
            )
            
            # Procesar feedback con LLM usando prompt específico
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.feedback_system_prompt},
                    {"role": "user", "content": feedback_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            feedback_analysis = response.choices[0].message.content
            
            # Actualizar preferencias basadas en feedback
            session = self.session_manager.get_or_create_session(user_id)
            self._extract_preferences_from_feedback(session, feedback, feedback_analysis)
            
            logger.info(f"📝 Feedback procesado para usuario {user_id}")
            
        except Exception as e:
            logger.warning(f"Error procesando feedback: {e}")

    def _extract_preferences_from_feedback(self, session: ChatSession, feedback: Dict[str, Any], analysis: str):
        """Extrae preferencias del análisis de feedback y las actualiza en la sesión"""
        try:
            # Extraer preferencias básicas del feedback directo
            if 'format_preference' in feedback:
                session.user_preferences['preferred_format'] = feedback['format_preference']
            
            if 'detail_level' in feedback:
                session.user_preferences['detail_level'] = feedback['detail_level']
            
            if 'chart_type_preference' in feedback:
                session.user_preferences['chart_preference'] = feedback['chart_type_preference']
            
            # Aquí se podría integrar análisis más sofisticado del texto de feedback
            # usando el análisis generado por el LLM
            
        except Exception as e:
            logger.warning(f"Error extrayendo preferencias de feedback: {e}")

    async def _update_personalization_profile(self, session: ChatSession, intent: str, response: ChatResponse):
        """
        Actualiza el perfil de personalización del usuario
        
        Args:
            session: Sesión del usuario
            intent: Intención clasificada
            response: Respuesta generada
        """
        try:
            # Actualizar estadísticas de uso
            if 'intent_frequency' not in session.personalization_profile:
                session.personalization_profile['intent_frequency'] = {}
            
            if intent not in session.personalization_profile['intent_frequency']:
                session.personalization_profile['intent_frequency'][intent] = 0
            
            session.personalization_profile['intent_frequency'][intent] += 1
            
            # Actualizar preferencias de formato basadas en uso
            if response.charts:
                if 'chart_usage' not in session.personalization_profile:
                    session.personalization_profile['chart_usage'] = 0
                session.personalization_profile['chart_usage'] += 1
            
            session.personalization_profile['last_updated'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.warning(f"Error actualizando perfil de personalización: {e}")

    def _sanitize_message(self, message: str) -> str:
        """Sanitiza y valida el mensaje del usuario"""
        if not message or not isinstance(message, str):
            return ""
        
        # Limpiar espacios y caracteres problemáticos
        sanitized = message.strip()
        
        # Limitar longitud del mensaje
        if len(sanitized) > 2000:
            sanitized = sanitized[:2000] + "..."
            logger.warning("Mensaje truncado por exceder longitud máxima")
        
        return sanitized

    def _format_response_for_chat(self, cdg_response: Any, user_preferences: Dict[str, Any]) -> str:
        """
        Formatea la respuesta del agente CDG para presentación en chat
        
        Args:
            cdg_response: Respuesta del agente CDG
            user_preferences: Preferencias del usuario para personalización
            
        Returns:
            str: Respuesta formateada para chat
        """
        if 'response' in cdg_response.content:
            return cdg_response.content['response']
        elif 'business_review' in cdg_response.content:
            return "📋 Business Review generado exitosamente. Revisa los gráficos y recomendaciones adjuntas."
        elif 'executive_summary' in cdg_response.content:
            return "📊 Executive Summary generado exitosamente para revisión directiva."
        elif 'error' in cdg_response.content:
            return f"❌ Error: {cdg_response.content['error']}"
        else:
            return self._format_structured_content_for_chat(cdg_response.content, user_preferences)

    def _format_structured_content_for_chat(self, content: Dict[str, Any], user_preferences: Dict[str, Any]) -> str:
        """Formatea contenido estructurado para presentación conversacional"""
        formatted_lines = []
        
        # Personalizar formato según preferencias del usuario
        detail_level = user_preferences.get('detail_level', 'medium')
        max_items = {'high': 5, 'medium': 3, 'low': 2}.get(detail_level, 3)
        
        for key, value in content.items():
            if key == 'analysis_type':
                continue
            
            if isinstance(value, list) and value:
                formatted_lines.append(f"**{key.replace('_', ' ').title()}:**")
                for item in value[:max_items]:
                    if isinstance(item, dict):
                        name = item.get('desc_gestor') or item.get('nombre') or 'Item'
                        metric = item.get('margen_neto') or item.get('valor') or 'N/A'
                        formatted_lines.append(f"• {name}: {metric}")
                if len(value) > max_items:
                    formatted_lines.append(f"... y {len(value) - max_items} elementos más")
                formatted_lines.append("")
            
            elif isinstance(value, dict) and detail_level == 'high':
                formatted_lines.append(f"**{key.replace('_', ' ').title()}:**")
                formatted_lines.append(f"``````")
            
            elif value and detail_level in ['medium', 'high']:
                formatted_lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(formatted_lines) if formatted_lines else "✅ Análisis completado satisfactoriamente."

    def _create_error_response(self, error_message: str, session_id: str, start_time: datetime) -> ChatResponse:
        """Crea una respuesta de error estándar para el chat"""
        return ChatResponse(
            response=f"❌ Lo siento, ha ocurrido un error: {error_message}",
            response_type="error",
            charts=[],
            recommendations=["Intenta reformular tu pregunta o contacta con soporte técnico"],
            metadata={"error": True, "error_message": error_message},
            execution_time=(datetime.now() - start_time).total_seconds(),
            confidence_score=0.0,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )

    def get_session_history(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Obtiene el historial de conversación de un usuario"""
        if user_id in self.session_manager.sessions:
            return self.session_manager.sessions[user_id].conversation_history
        return None

    def get_agent_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del agente de chat"""
        return {
            'status': 'active',
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'active_sessions': len(self.session_manager.sessions),
            'websocket_connections': len(self.session_manager.websocket_connections),
            'cdg_agent_status': self.cdg_agent.get_agent_status(),
            'prompts_loaded': {
                'conversation': bool(self.conversation_system_prompt),
                'feedback': bool(self.feedback_system_prompt),
                'intent_classification': bool(self.intent_classification_prompt),
                'personalization': bool(self.personalization_system_prompt)
            }
        }

# ============================================================================
# APLICACIÓN FASTAPI CON WEBSOCKET Y REST
# ============================================================================

# Instancia global del agente de chat
chat_agent = CDGChatAgent()

# Aplicación FastAPI
app = FastAPI(
    title="CDG Chat Agent API",
    description="API conversacional inteligente para el agente de Control de Gestión - Banca March",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3001",
        "https://app.bancamarch.es"  # Producción
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ============================================================================
# ENDPOINTS DE LA API
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """
    Endpoint principal para procesar mensajes de chat con inteligencia conversacional
    
    Args:
        chat_message: Mensaje estructurado del usuario con contexto y preferencias
        
    Returns:
        ChatResponse: Respuesta completa con análisis, gráficos y recomendaciones personalizadas
    """
    return await chat_agent.process_chat_message(chat_message)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Endpoint WebSocket para comunicación conversacional en tiempo real
    
    Args:
        websocket: Conexión WebSocket
        user_id: ID único del usuario
    """
    await websocket.accept()
    chat_agent.session_manager.add_websocket_connection(user_id, websocket)
    
    try:
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_json()
            
            # Crear ChatMessage desde los datos recibidos
            chat_message = ChatMessage(
                user_id=user_id,
                message=data.get("message", ""),
                gestor_id=data.get("gestor_id"),
                periodo=data.get("periodo"),
                include_charts=data.get("include_charts", True),
                include_recommendations=data.get("include_recommendations", True),
                context=data.get("context", {}),
                user_feedback=data.get("user_feedback")
            )
            
            # Procesar mensaje con el agente de chat
            response = await chat_agent.process_chat_message(chat_message)
            
            # Enviar respuesta al cliente
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket desconectado para usuario {user_id}")
        chat_agent.session_manager.remove_websocket_connection(user_id)

@app.get("/history/{user_id}")
async def get_chat_history(user_id: str):
    """
    Obtiene el historial completo de conversación de un usuario
    
    Args:
        user_id: ID único del usuario
        
    Returns:
        Historial de conversación con metadatos de personalización
    """
    history = chat_agent.get_session_history(user_id)
    if history is None:
        raise HTTPException(status_code=404, detail="No se encontró historial para este usuario")
    
    return {
        "user_id": user_id, 
        "history": history,
        "session_info": {
            "total_interactions": len(history),
            "session_created": chat_agent.session_manager.sessions[user_id].created_at.isoformat() if user_id in chat_agent.session_manager.sessions else None
        }
    }

@app.post("/reset/{user_id}")
async def reset_session(user_id: str):
    """
    Reinicia la sesión de conversación conservando el perfil de personalización
    
    Args:
        user_id: ID único del usuario
        
    Returns:
        Confirmación de reset
    """
    chat_agent.session_manager.reset_session(user_id)
    return {"message": f"Sesión de chat reiniciada para usuario {user_id}"}

@app.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """
    Obtiene las preferencias y perfil de personalización del usuario
    
    Args:
        user_id: ID único del usuario
        
    Returns:
        Preferencias y perfil de personalización
    """
    if user_id not in chat_agent.session_manager.sessions:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    session = chat_agent.session_manager.sessions[user_id]
    return {
        "user_id": user_id,
        "preferences": session.user_preferences,
        "personalization_profile": session.personalization_profile
    }

@app.post("/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: Dict[str, Any]):
    """
    Actualiza las preferencias del usuario para personalización
    
    Args:
        user_id: ID único del usuario
        preferences: Nuevas preferencias a aplicar
        
    Returns:
        Confirmación de actualización
    """
    session = chat_agent.session_manager.get_or_create_session(user_id)
    session.update_preferences(preferences)
    return {"message": f"Preferencias actualizadas para usuario {user_id}"}

@app.get("/status")
async def get_status():
    """
    Obtiene el estado completo del agente de chat con métricas detalladas
    
    Returns:
        Estado del agente, estadísticas de uso y configuración de prompts
    """
    return chat_agent.get_agent_status()

@app.get("/health")
async def health_check():
    """
    Health check para monitoreo del servicio de chat
    
    Returns:
        Estado de salud del servicio
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "CDG Chat Agent"
    }

# ============================================================================
# FUNCIONES DE CONVENIENCIA PARA INTEGRACIÓN
# ============================================================================

async def send_message_to_cdg_chat(user_id: str, message: str, **kwargs) -> Dict[str, Any]:
    """
    Función de conveniencia para enviar mensaje al agente de chat CDG
    
    Args:
        user_id: ID del usuario
        message: Mensaje del usuario
        **kwargs: Parámetros adicionales (gestor_id, periodo, etc.)
        
    Returns:
        Respuesta del agente como diccionario
    """
    chat_message = ChatMessage(
        user_id=user_id,
        message=message,
        **kwargs
    )
    
    response = await chat_agent.process_chat_message(chat_message)
    return response.dict()

def create_cdg_chat_agent_instance() -> CDGChatAgent:
    """
    Crea una nueva instancia del agente de chat CDG
    
    Returns:
        Nueva instancia de CDGChatAgent
    """
    return CDGChatAgent()

# ============================================================================
# PUNTO DE ENTRADA PARA EJECUCIÓN STANDALONE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configuración para desarrollo
    uvicorn.run(
        "chat_agent:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
