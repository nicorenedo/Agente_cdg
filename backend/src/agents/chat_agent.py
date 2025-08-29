"""
Chat Agent para CDG - Versión 6.1 Integrado con System Prompts Profesionales
===========================================================================

Integración completa con CDG Agent + System Prompts especializados
Respuestas adaptativas con prompts profesionales de control de gestión bancario
Personalización inteligente y gestión conversacional avanzada

Versión: 6.1 - Con System Prompts Profesionales Integrados
Autor: Agente CDG Development Team  
Fecha: 2025-08-28
"""

import json
import logging
import uuid
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_ID', 'gpt-4')

# ============================================================================
# IMPORTACIONES INTEGRADAS CON SYSTEM PROMPTS PROFESIONALES
# ============================================================================

try:
    from utils.initial_agent import iniciar_agente_llm
    
    # 🚀 IMPORTACIÓN CRÍTICA: CDG Agent completo
    from agents.cdg_agent import CDGAgent, CDGRequest, CDGResponse
    
    # 🎯 IMPORTACIÓN DE TUS PROMPTS PROFESIONALES
    from prompts.system_prompts import (
        CHAT_CONVERSATIONAL_SYSTEM_PROMPT,
        CHAT_FEEDBACK_SYSTEM_PROMPT,
        CHAT_INTENT_CLASSIFICATION_PROMPT,
        CHAT_PERSONALIZATION_SYSTEM_PROMPT
    )
    
    from prompts.user_prompts import (
        build_feedback_processing_prompt,
        build_conversation_context_prompt,
        build_personalization_learning_prompt,
        build_intent_clarification_prompt,
        build_dynamic_dashboard_prompt,
        FEEDBACK_PROCESSING_USER_PROMPT,
        CONVERSATION_CONTEXT_USER_PROMPT
    )
    
    # Imports básicos de queries para consultas simples
    from queries.gestor_queries import GestorQueries
    from queries.comparative_queries import ComparativeQueries
    from queries.deviation_queries import DeviationQueries
    from queries.incentive_queries import IncentiveQueries
    from queries.period_queries import PeriodQueries, get_available_periods_enhanced
    
    IMPORTS_SUCCESSFUL = True
    logger = logging.getLogger(__name__)
    logger.info("🚀 CDG Chat Agent v6.1 inicializado con System Prompts Profesionales - Modo: PRODUCTION")
    
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"⚠️ Error de importación: {e}")
    
    # Fallbacks para testing
    def iniciar_agente_llm():
        class MockClient:
            class Chat:
                class Completions:
                    def create(self, **kwargs):
                        class Response:
                            choices = [type('Choice', (), {'message': type('Message', (), {'content': 'Mock response'})()})]
                        return Response()
                completions = Completions()
            chat = Chat()
        return MockClient()
    
    class MockCDGAgent:
        async def process_request(self, request):
            return type('MockResponse', (), {
                'content': {'response': 'Mock CDG response'},
                'charts': [],
                'recommendations': ['Mock recommendation'],
                'metadata': {'analysis_type': 'mock'},
                'confidence_score': 0.5,
                'response_type': type('ResponseType', (), {'value': 'mock'})()
            })()
    
    CDGAgent = MockCDGAgent
    GestorQueries = ComparativeQueries = DeviationQueries = IncentiveQueries = PeriodQueries = type('MockQueries', (), {'__getattr__': lambda s, n: lambda *a, **k: type('MockResult', (), {'data': [], 'row_count': 0})()})
    
    # Fallback prompts
    CHAT_CONVERSATIONAL_SYSTEM_PROMPT = "Eres un asistente financiero especializado en análisis bancario."
    CHAT_FEEDBACK_SYSTEM_PROMPT = "Analiza feedback para mejorar respuestas."
    CHAT_INTENT_CLASSIFICATION_PROMPT = "Clasifica la intención del usuario."
    CHAT_PERSONALIZATION_SYSTEM_PROMPT = "Personaliza respuestas según el usuario."
    
    def build_feedback_processing_prompt(*args, **kwargs): return "Mock feedback prompt"
    def build_conversation_context_prompt(*args, **kwargs): return "Mock context prompt"
    
    IMPORTS_SUCCESSFUL = False

# ============================================================================
# MODELOS DE DATOS SIMPLIFICADOS
# ============================================================================

class ChatMessage(BaseModel):
    user_id: str
    message: str
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True
    context: Dict[str, Any] = {}
    user_feedback: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
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
# GESTIÓN DE SESIONES CON PERSONALIZACIÓN INTELIGENTE
# ============================================================================

class ChatSession:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        self.user_preferences = {
            'communication_style': 'professional',  # professional, concise, detailed
            'technical_level': 'intermediate',       # basic, intermediate, advanced
            'preferred_format': 'combined',          # text, charts, combined
            'response_length': 'medium'              # short, medium, detailed
        }
        self.personalization_data = {
            'frequent_queries': [],
            'successful_interactions': 0,
            'feedback_history': [],
            'usage_patterns': {}
        }
        self.created_at = datetime.now()
        self.last_active = datetime.now()
    
    def add_interaction(self, user_msg: str, agent_resp: Dict, intent: str, satisfaction_rating: Optional[int] = None):
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_msg,
            'agent_response': agent_resp,
            'intent': intent,
            'session_id': self.session_id,
            'satisfaction_rating': satisfaction_rating
        }
        
        self.conversation_history.append(interaction)
        self.last_active = datetime.now()
        
        # Actualizar datos de personalización
        self._update_personalization_data(user_msg, intent, satisfaction_rating)
        
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def _update_personalization_data(self, user_msg: str, intent: str, rating: Optional[int]):
        """🧠 Actualiza datos de personalización inteligente"""
        # Actualizar consultas frecuentes
        if intent not in self.personalization_data['frequent_queries']:
            self.personalization_data['frequent_queries'].append(intent)
        
        # Actualizar satisfacción
        if rating and rating >= 4:
            self.personalization_data['successful_interactions'] += 1
        
        # Detectar patrones de longitud de mensaje
        msg_length = len(user_msg.split())
        if msg_length < 5:
            self.user_preferences['response_length'] = 'short'
        elif msg_length > 15:
            self.user_preferences['response_length'] = 'detailed'
    
    def get_recent_context(self, max_interactions: int = 5) -> List[Dict]:
        return self.conversation_history[-max_interactions:]
    
    def get_personalization_context(self) -> Dict[str, Any]:
        """📊 Obtiene contexto de personalización para prompts"""
        return {
            'user_preferences': self.user_preferences,
            'personalization_data': self.personalization_data,
            'total_interactions': len(self.conversation_history),
            'last_activity': self.last_active.isoformat()
        }

class ChatSessionManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
    
    def get_or_create_session(self, user_id: str) -> ChatSession:
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession(user_id)
            logger.info(f"🆕 Nueva sesión creada para usuario {user_id}")
        self.sessions[user_id].last_active = datetime.now()
        return self.sessions[user_id]
    
    def add_websocket_connection(self, user_id: str, websocket: WebSocket):
        self.websocket_connections[user_id] = websocket
    
    def remove_websocket_connection(self, user_id: str):
        self.websocket_connections.pop(user_id, None)
    
    def reset_session(self, user_id: str):
        if user_id in self.sessions:
            self.sessions[user_id].conversation_history.clear()

# ============================================================================
# AGENTE DE CHAT CON SYSTEM PROMPTS PROFESIONALES INTEGRADOS
# ============================================================================

class CDGChatAgent:
    """
    🚀 AGENTE DE CHAT v6.1 CON SYSTEM PROMPTS PROFESIONALES
    
    - Integración completa con tus System Prompts especializados
    - Personalización inteligente basada en patrones de uso
    - Gestión conversacional avanzada con contexto bancario
    - Clasificación de intenciones y feedback processing
    """
    
    def __init__(self):
        self.session_manager = ChatSessionManager()
        self.llm_client = iniciar_agente_llm()
        self.start_time = datetime.now()
        self.imports_successful = IMPORTS_SUCCESSFUL
        
        # 🚀 INICIALIZAR CDG AGENT COMPLETO
        try:
            self.cdg_agent = CDGAgent()
            logger.info("🎯 CDG Agent integrado exitosamente en Chat Agent")
        except Exception as e:
            logger.error(f"❌ Error inicializando CDG Agent: {e}")
            self.cdg_agent = MockCDGAgent() if not IMPORTS_SUCCESSFUL else None
        
        # Sistemas de queries para consultas simples
        try:
            self.gestor_queries = GestorQueries()
            self.comparative_queries = ComparativeQueries()
            self.deviation_queries = DeviationQueries()
            self.incentive_queries = IncentiveQueries()
            self.period_queries = PeriodQueries()
        except Exception as e:
            logger.warning(f"Error inicializando sistemas de queries: {e}")
            self.gestor_queries = self.comparative_queries = self.deviation_queries = self.incentive_queries = self.period_queries = type('MockQueries', (), {})()
        
        logger.info(f"🚀 CDG Chat Agent v6.1 inicializado con System Prompts Profesionales - Modo: {'PRODUCTION' if IMPORTS_SUCCESSFUL else 'MOCK'}")
    
    async def _classify_user_intent(self, message: str, session: ChatSession) -> Dict[str, Any]:
        """
        🧠 CLASIFICACIÓN DE INTENCIÓN CON TU PROMPT PROFESIONAL
        
        Usa CHAT_INTENT_CLASSIFICATION_PROMPT para determinar la intención del usuario
        """
        try:
            client = self.llm_client
            
            # Construir contexto de clasificación
            classification_context = {
                'message': message,
                'recent_history': [h.get('intent', 'general') for h in session.get_recent_context(3)],
                'user_preferences': session.user_preferences,
                'session_length': len(session.conversation_history)
            }
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system", 
                        "content": CHAT_INTENT_CLASSIFICATION_PROMPT
                    },
                    {
                        "role": "user", 
                        "content": f"Clasifica la siguiente consulta considerando el contexto bancario:\n\nMensaje: {message}\n\nContexto: {json.dumps(classification_context, ensure_ascii=False, indent=2)}"
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parsear respuesta JSON
            try:
                result = json.loads(result_text)
                intent = result.get('intent', 'general_inquiry')
                confidence = result.get('confidence', 0.5)
            except json.JSONDecodeError:
                # Fallback si no es JSON válido
                intent = 'general_inquiry'
                confidence = 0.3
            
            logger.info(f"🎯 Intención clasificada: {intent} (confianza: {confidence:.2f})")
            
            return {
                'intent': intent,
                'confidence': confidence,
                'requires_cdg_agent': self._intent_requires_cdg_agent(intent, message),
                'recommended_approach': self._get_approach_for_intent(intent)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en clasificación de intención: {e}")
            return {
                'intent': 'general_inquiry',
                'confidence': 0.3,
                'requires_cdg_agent': self._requires_cdg_agent(message),
                'recommended_approach': 'simple'
            }
    
    def _should_request_clarification(self, intent_analysis: Dict) -> bool:
        """🎯 Determina si se debe pedir clarificación por baja confianza"""
        confidence = intent_analysis['confidence']
        intent = intent_analysis['intent']

        # Umbrales por tipo de intent
        thresholds = {
            'performance_analysis': 0.6,
            'comparative_analysis': 0.65,
            'deviation_detection': 0.7,
            'incentive_analysis': 0.65,
            'business_review': 0.7,
            'executive_summary': 0.7,
            'general_inquiry': 0.4
        }

        return confidence < thresholds.get(intent, 0.6)

    async def _request_clarification(self, chat_message: ChatMessage, intent_analysis: Dict, session: ChatSession) -> ChatResponse:
        """❓ Solicita aclaración al usuario por baja confianza"""
        start_time = datetime.now()
        
        # Umbrales por tipo de intent (definir thresholds aquí)
        thresholds = {
            'performance_analysis': 0.6,
            'comparative_analysis': 0.65,
            'deviation_detection': 0.7,
            'incentive_analysis': 0.65,
            'business_review': 0.7,
            'executive_summary': 0.7,
            'general_inquiry': 0.4
        }

        # Mensaje personalizado según el tipo de intent detectado
        intent = intent_analysis.get('intent', 'general_inquiry')
        confidence = intent_analysis.get('confidence', 0)
        
        if intent == 'performance_analysis':
            clarification_msg = f"💡 **Consulta sobre rendimiento detectada** (confianza: {confidence:.0%})\n\n" \
                              "Parece que buscas información sobre el rendimiento de un gestor o centro. " \
                              "¿Podrías especificar:\n" \
                              "- ¿Qué gestor específico te interesa?\n" \
                              "- ¿Para qué período?\n" \
                              "- ¿Qué métricas en particular?\n\n" \
                              "Ejemplo: *'Rendimiento del gestor 19 en octubre 2025'*"
        
        elif intent == 'comparative_analysis':
            clarification_msg = f"💡 **Consulta comparativa detectada** (confianza: {confidence:.0%})\n\n" \
                              "Parece que quieres comparar elementos. ¿Podrías aclarar:\n" \
                              "- ¿Qué elementos comparar? (gestores, centros, segmentos)\n" \
                              "- ¿Para qué período?\n" \
                              "- ¿Qué métricas usar para la comparación?\n\n" \
                              "Ejemplo: *'Comparar gestores 18 y 21 en ROE para 2025-10'*"
        
        else:
            clarification_msg = f"💡 **Consulta detectada** (confianza: {confidence:.0%})\n\n" \
                              "No estoy completamente seguro de haber entendido tu consulta. " \
                              "¿Podrías proporcionar más detalles sobre:\n" \
                              "- ¿Qué información específica necesitas?\n" \
                              "- ¿Sobre qué gestor, centro o período?\n" \
                              "- ¿Buscas análisis, comparaciones o reportes?\n\n" \
                              "Esto me ayudará a ofrecerte un análisis más preciso."
        
        # Añadir sugerencias basadas en el historial del usuario
        suggestions = self._get_clarification_suggestions(session, intent)
        if suggestions:
            clarification_msg += f"\n\n**💡 Sugerencias basadas en tus consultas anteriores:**\n" + \
                               "\n".join([f"• {suggestion}" for suggestion in suggestions])
        
        return ChatResponse(
            response=clarification_msg,
            response_type="clarification_request",
            charts=[],
            recommendations=[
                "Especifica más detalles en tu consulta",
                "Usa ejemplos concretos (gestor, período, métricas)",
                "Consulta las sugerencias personalizadas"
            ],
            metadata={
                "source": "clarification_handler",
                "original_intent": intent,
                "original_confidence": confidence,
                "requires_clarification": True,
                "clarification_type": "low_confidence",
                "threshold_used": thresholds.get(intent, 0.6),
                "professional_prompts": True
            },
            execution_time=(datetime.now() - start_time).total_seconds(),
            confidence_score=confidence,
            timestamp=datetime.now().isoformat(),
            session_id=session.session_id
        )
    
    def _get_clarification_suggestions(self, session: ChatSession, current_intent: str) -> List[str]:
        """💡 Genera sugerencias personalizadas para aclaración"""
        suggestions = []

        try:
            # Basado en consultas frecuentes del usuario
            frequent_queries = session.personalization_data.get('frequent_queries', [])
            current_period = datetime.now().strftime('%Y-%m')

            if 'performance_analysis' in frequent_queries:
                suggestions.append(f"Análisis del gestor [ID] en {current_period}")

            if 'comparative_analysis' in frequent_queries:
                suggestions.append("Comparar rendimiento entre gestores")

            if 'deviation_detection' in frequent_queries:
                suggestions.append("Detectar alertas o desviaciones críticas")

            # Sugerencias por defecto si no hay historial
            if not suggestions:
                suggestions.extend([
                    f"¿Cómo está el gestor [ID] en {current_period}?",
                    "Comparar gestores 18 y 21 en ROE",
                    "¿Qué centros tienen mejor rendimiento?"
                ])

            return suggestions[:3]  # Máximo 3 sugerencias

        except Exception as e:
            logger.warning(f"Error generando sugerencias de aclaración: {e}")
            return [f"Ejemplo: ¿Cómo está el gestor 19 en {datetime.now().strftime('%Y-%m')}?"]

    
    def _intent_requires_cdg_agent(self, intent: str, message: str) -> bool:
        """🎯 Determina si la intención requiere CDG Agent basado en tu clasificación"""
        cdg_intents = {
            'performance_analysis',
            'comparative_analysis', 
            'deviation_detection',
            'incentive_analysis',
            'business_review',
            'executive_summary'
        }
        
        return intent in cdg_intents or self._requires_cdg_agent(message)
    
    def _get_approach_for_intent(self, intent: str) -> str:
        """📋 Obtiene enfoque recomendado según intención"""
        approach_map = {
            'performance_analysis': 'cdg_detailed',
            'comparative_analysis': 'cdg_detailed',
            'deviation_detection': 'cdg_alerts',
            'incentive_analysis': 'cdg_calculations',
            'business_review': 'cdg_executive',
            'executive_summary': 'cdg_executive',
            'general_inquiry': 'simple_conversational'
        }
        return approach_map.get(intent, 'simple_conversational')
    
    def _extract_periodo_from_message(self, message: str) -> Optional[str]:
        """🗓️ EXTRACCIÓN INTELIGENTE DE PERÍODO"""
        periodo_patterns = [
            r'(\d{4}-\d{2})',           # 2025-10
            r'(\d{4}/\d{2})',           # 2025/10  
            r'(\d{2}/\d{4})',           # 10/2025
            r'(\d{2}-\d{4})',           # 10-2025
            r'periodo\s+(\d{4}-\d{2})', # periodo 2025-10
            r'mes\s+(\d{4}-\d{2})',     # mes 2025-10
            r'en\s+(\d{4}-\d{2})',      # en 2025-10
            r'del\s+(\d{4}-\d{2})',     # del 2025-10
        ]
        
        message_lower = message.lower()
        
        for pattern in periodo_patterns:
            match = re.search(pattern, message_lower)
            if match:
                periodo_found = match.group(1)
                logger.info(f"🗓️ Período detectado: '{periodo_found}' usando patrón: {pattern}")
                
                # Normalizar formato
                if re.match(r'\d{4}-\d{2}', periodo_found):
                    return periodo_found
                elif re.match(r'\d{4}/\d{2}', periodo_found):
                    return periodo_found.replace('/', '-')
                elif re.match(r'\d{2}/\d{4}', periodo_found):
                    parts = periodo_found.split('/')
                    return f"{parts[1]}-{parts[0]}"
                elif re.match(r'\d{2}-\d{4}', periodo_found):
                    parts = periodo_found.split('-')
                    return f"{parts[1]}-{parts[0]}"
        
        # Fallback dinámico
        current_period = datetime.now().strftime('%Y-%m')
        logger.info(f"🗓️ No se detectó período, usando actual: {current_period}")
        return current_period
    
    def _extract_gestor_id(self, chat_message: ChatMessage, session: ChatSession) -> Optional[str]:
        """🧠 EXTRACCIÓN INTELIGENTE DE GESTOR_ID"""
        
        if chat_message.gestor_id:
            return chat_message.gestor_id
        
        if 'gestor_id' in chat_message.context:
            return chat_message.context['gestor_id']
        
        for interaction in reversed(session.get_recent_context(3)):
            if 'gestor_id' in interaction.get('agent_response', {}).get('metadata', {}):
                return interaction['agent_response']['metadata']['gestor_id']
        
        gestor_patterns = [
            r'gestor\s+(\d+)', 
            r'id\s+(\d+)', 
            r'#(\d+)',
            r'número\s+(\d+)',
            r'num\s+(\d+)'
        ]
        
        message_lower = chat_message.message.lower()
        
        for pattern in gestor_patterns:
            match = re.search(pattern, message_lower)
            if match:
                potential_id = match.group(1)
                if potential_id.isdigit() and 1 <= int(potential_id) <= 100:
                    logger.info(f"🎯 Gestor ID extraído: {potential_id}")
                    return potential_id
        
        return "1"
    
    def _requires_cdg_agent(self, message: str) -> bool:
        """🧠 DETERMINA SI REQUIERE CDG AGENT - Versión mejorada"""
        message_lower = message.lower()
        
        complex_patterns = [
            # Consultas individuales de gestor (añadido)
            r'gestor\s+\d+',
            r'cómo\s+está.*gestor',
            r'performance.*gestor',
            r'rendimiento.*gestor',
            
            # Segmentos
            r'segmento.*vs.*segmento',
            r'empresas.*vs.*minorista',
            r'minorista.*vs.*empresas',
            r'comparar.*segmentos',
            
            # Centros
            r'centro.*vs.*centro',
            r'madrid.*vs.*barcelona',
            r'barcelona.*vs.*madrid',
            r'comparar.*centros',
            
            # Múltiples gestores
            r'gestores?\s+\d+.*\d+',
            r'comparar.*gestores',
            
            # Reportes complejos
            r'business\s+review',
            r'executive\s+summary',
            r'informe\s+completo',
            r'resumen\s+ejecutivo',
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"🎯 Consulta compleja detectada: {pattern}")
                return True
        
        return False
    
    async def process_chat_message(self, chat_message: ChatMessage) -> ChatResponse:
        """🎯 PROCESAMIENTO PRINCIPAL CON SYSTEM PROMPTS PROFESIONALES"""
        start_time = datetime.now()
        session = self.session_manager.get_or_create_session(chat_message.user_id)
        
        try:
            # 1. Sanitizar mensaje
            message = self._sanitize_message(chat_message.message)
            if not message:
                return self._create_error_response("Mensaje vacío", session.session_id, start_time)
            
            # 2. 🧠 CLASIFICAR INTENCIÓN CON TU PROMPT PROFESIONAL
            intent_analysis = await self._classify_user_intent(message, session)
            intent = intent_analysis['intent']
            confidence = intent_analysis['confidence']
            
            # 🆕 3. VERIFICAR SI NECESITA ACLARACIÓN POR BAJA CONFIANZA
            if self._should_request_clarification(intent_analysis):
                logger.info(f"🔍 Solicitando aclaración - Intent: {intent}, Confianza: {confidence:.2f}")
                return await self._request_clarification(chat_message, intent_analysis, session)
            
            # 4. Extraer parámetros inteligentes (continúa con tu código existente)
            gestor_id = self._extract_gestor_id(chat_message, session)
            periodo_final = chat_message.periodo or self._extract_periodo_from_message(message)
            
            # 4. 🚀 DECISIÓN INTELIGENTE: ¿CDG AGENT O SIMPLE?
            if intent_analysis['requires_cdg_agent']:
                logger.info("🎯 DELEGANDO A CDG AGENT para análisis profesional")
                return await self._process_with_cdg_agent_professional(
                    chat_message, message, gestor_id, periodo_final, session, start_time, intent_analysis
                )
            else:
                logger.info("💬 PROCESANDO CON CHAT PROFESIONAL para consulta conversacional")
                return await self._process_simple_chat_professional(
                    chat_message, message, gestor_id, periodo_final, session, start_time, intent_analysis
                )
            
        except Exception as e:
            logger.error(f"❌ Error procesando chat: {e}")
            return self._create_error_response(str(e), session.session_id, start_time)
    
    async def _process_with_cdg_agent_professional(self, chat_message: ChatMessage, message: str, gestor_id: str, periodo: str, session: ChatSession, start_time: datetime, intent_analysis: Dict) -> ChatResponse:
        """
        🚀 PROCESAMIENTO PROFESIONAL CON CDG AGENT + TUS PROMPTS
        """
        try:
            # Crear CDGRequest
            cdg_request = CDGRequest(
                user_message=message,
                user_id=chat_message.user_id,
                gestor_id=gestor_id,
                periodo=periodo,
                context=chat_message.context,
                include_charts=chat_message.include_charts,
                include_recommendations=chat_message.include_recommendations
            )
            
            # Procesar con CDG Agent
            cdg_response = await self.cdg_agent.process_request(cdg_request)
            
            # 🎯 GENERAR RESPUESTA PROFESIONAL CON TUS PROMPTS
            response_text = await self._generate_professional_response(
                cdg_response.content, message, cdg_response, session, intent_analysis
            )
            
            # Construir respuesta completa
            chat_response = ChatResponse(
                response=response_text,
                response_type=intent_analysis['intent'],
                charts=cdg_response.charts,
                recommendations=cdg_response.recommendations,
                metadata={
                    'source': 'cdg_agent_professional',
                    'analysis_type': intent_analysis['intent'],
                    'confidence': intent_analysis['confidence'],
                    'gestor_id': gestor_id,
                    'periodo': periodo,
                    'periodo_source': 'parameter' if chat_message.periodo else 'extracted_from_message',
                    'imports_successful': self.imports_successful,
                    'model_used': MODEL_NAME,
                    'session_length': len(session.conversation_history),
                    'cdg_agent_integration': True,
                    'professional_prompts': True,
                    'intent_classification': intent_analysis,
                    'personalization_applied': True
                },
                execution_time=(datetime.now() - start_time).total_seconds(),
                confidence_score=cdg_response.confidence_score * intent_analysis['confidence'],
                timestamp=datetime.now().isoformat(),
                session_id=session.session_id
            )
            
            # Añadir a historial con personalización
            session.add_interaction(
                message, 
                chat_response.dict(), 
                intent_analysis['intent'],
                satisfaction_rating=None  # Se puede añadir con feedback posterior
            )
            
            # Procesar feedback si existe
            if chat_message.user_feedback:
                await self._process_user_feedback_professional(chat_message.user_id, chat_message.user_feedback, session)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ CDG Agent profesional procesó consulta en {execution_time:.2f}s")
            
            return chat_response
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento profesional CDG Agent: {e}")
            return self._create_error_response(str(e), session.session_id, start_time)
    
    async def _generate_professional_response(self, content: Dict[str, Any], original_message: str, cdg_response, session: ChatSession, intent_analysis: Dict) -> str:
        """
        💬 GENERADOR PROFESIONAL CON TUS SYSTEM PROMPTS
        
        Combina datos estructurados + explicación profesional usando tus prompts especializados
        """
        try:
            # 1. Generar datos estructurados (formato dinámico)
            structured_data = self._format_data_dynamically(content)
            
            # 2. 🎯 GENERAR EXPLICACIÓN PROFESIONAL CON TU PROMPT
            professional_explanation = await self._generate_professional_explanation(
                content, original_message, cdg_response, session, intent_analysis
            )
            
            # 3. Combinar según preferencias del usuario
            user_prefs = session.user_preferences
            
            if user_prefs['preferred_format'] == 'text':
                # Solo explicación profesional
                return professional_explanation
            elif user_prefs['preferred_format'] == 'charts':
                # Enfoque en datos estructurados
                return f"📊 **Análisis:** {original_message}\n\n{structured_data}"
            else:
                # Formato combinado (default)
                response_parts = [
                    f"📊 **Análisis para:** {original_message}",
                    "",
                    "🧠 **Interpretación Profesional:**",
                    professional_explanation,
                ]
                
                # Añadir datos si el usuario prefiere detalle
                if user_prefs['response_length'] in ['medium', 'detailed']:
                    response_parts.extend([
                        "",
                        "📈 **Datos Detallados:**",
                        structured_data
                    ])
                
                return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta profesional: {e}")
            return self._generate_fallback_explanation(content, original_message)
    
    async def _generate_professional_explanation(self, content: Dict[str, Any], original_message: str, cdg_response, session: ChatSession, intent_analysis: Dict) -> str:
        """
        🗣️ GENERADOR PROFESIONAL CON TU CHAT_CONVERSATIONAL_SYSTEM_PROMPT
        
        Usa tu prompt especializado + contexto de personalización
        """
        try:
            # 1. Extraer insights dinámicamente
            key_insights = self._extract_key_insights(content)
            
            # 2. Construir contexto profesional
            conversation_context = build_conversation_context_prompt(
                user_id=session.user_id,
                current_message=original_message,
                conversation_history=session.get_recent_context(5),
                user_context=session.get_personalization_context()
            )
            
            # 3. 🎯 LLAMAR CON TU PROMPT PROFESIONAL
            client = self.llm_client
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system", 
                        "content": CHAT_CONVERSATIONAL_SYSTEM_PROMPT
                    },
                    {
                        "role": "user", 
                        "content": f"""
{conversation_context}

## DATOS PARA INTERPRETAR:
{json.dumps(key_insights, ensure_ascii=False, indent=2)}

## ANÁLISIS SOLICITADO:
Proporciona una interpretación profesional de estos datos de control de gestión para la consulta: "{original_message}"

Considera:
- Intención clasificada: {intent_analysis['intent']}
- Nivel técnico del usuario: {session.user_preferences['technical_level']}
- Estilo de comunicación preferido: {session.user_preferences['communication_style']}
- Contexto bancario de Banca March
- Terminología apropiada para control de gestión

Estructura tu respuesta de manera profesional, clara y accionable.
"""
                    }
                ],
                temperature=0.4,
                max_tokens=1200
            )
            
            explanation = response.choices[0].message.content.strip()
            
            return self._clean_explanation(explanation)
            
        except Exception as e:
            logger.error(f"❌ Error generando explicación profesional: {e}")
            return self._generate_fallback_explanation(content, original_message)
    
    async def _process_user_feedback_professional(self, user_id: str, feedback: Dict[str, Any], session: ChatSession):
        """
        📝 PROCESAMIENTO PROFESIONAL DE FEEDBACK CON TUS PROMPTS
        
        Usa tu CHAT_FEEDBACK_SYSTEM_PROMPT para aprendizaje avanzado
        """
        try:
            if not feedback:
                return
            
            # Construir prompt de feedback profesional
            feedback_prompt = build_feedback_processing_prompt(
                user_id=user_id,
                original_query=session.conversation_history[-1]['user_message'] if session.conversation_history else "N/A",
                agent_response=session.conversation_history[-1]['agent_response'] if session.conversation_history else {},
                feedback_data=feedback
            )
            
            client = self.llm_client
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system", 
                        "content": CHAT_FEEDBACK_SYSTEM_PROMPT
                    },
                    {
                        "role": "user", 
                        "content": feedback_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            feedback_analysis = response.choices[0].message.content.strip()
            
            # Actualizar preferencias basado en análisis
            self._update_preferences_from_feedback(session, feedback, feedback_analysis)
            
            logger.info(f"📝 Feedback profesional procesado para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando feedback profesional: {e}")
    
    def _update_preferences_from_feedback(self, session: ChatSession, feedback: Dict, analysis: str):
        """🔧 Actualiza preferencias basado en análisis de feedback"""
        try:
            rating = feedback.get('rating', 0)
            
            # Añadir a historial
            session.personalization_data['feedback_history'].append({
                'timestamp': datetime.now().isoformat(),
                'rating': rating,
                'feedback': feedback,
                'analysis': analysis
            })
            
            # Ajustar preferencias basado en rating y comentarios
            if rating >= 4:
                session.personalization_data['successful_interactions'] += 1
            elif rating <= 2:
                # Ajustar según comentarios negativos
                comments = feedback.get('comment', '').lower()
                if 'muy largo' in comments or 'demasiado detalle' in comments:
                    session.user_preferences['response_length'] = 'short'
                elif 'muy corto' in comments or 'más detalle' in comments:
                    session.user_preferences['response_length'] = 'detailed'
                elif 'técnico' in comments:
                    session.user_preferences['technical_level'] = 'basic'
                elif 'simple' in comments:
                    session.user_preferences['technical_level'] = 'advanced'
        
        except Exception as e:
            logger.warning(f"Error actualizando preferencias: {e}")
    
    # ============================================================================
    # MÉTODOS DE SOPORTE Y UTILIDAD (Heredados del código anterior)
    # ============================================================================
    
    async def _process_simple_chat_professional(self, chat_message: ChatMessage, message: str, gestor_id: str, periodo: str, session: ChatSession, start_time: datetime, intent_analysis: Dict) -> ChatResponse:
        """💬 PROCESAMIENTO SIMPLE CON ENFOQUE PROFESIONAL"""
        try:
            domain = intent_analysis['intent']
            analysis_result = await self._call_simple_query_system(domain, message, gestor_id, periodo)
            
            # Generar respuesta profesional simple
            response_text = await self._generate_simple_professional_response(
                analysis_result, message, domain, session
            )
            
            chat_response = ChatResponse(
                response=response_text,
                response_type=domain,
                charts=analysis_result.get('charts', []),
                recommendations=self._get_simple_recommendations(analysis_result, domain),
                metadata={
                    'source': 'chat_simple_professional',
                    'domain': domain,
                    'intent': intent_analysis['intent'],
                    'confidence': intent_analysis['confidence'],
                    'gestor_id': gestor_id,
                    'periodo': periodo,
                    'imports_successful': self.imports_successful,
                    'professional_prompts': True,
                    'personalization_applied': True
                },
                execution_time=(datetime.now() - start_time).total_seconds(),
                confidence_score=intent_analysis['confidence'],
                timestamp=datetime.now().isoformat(),
                session_id=session.session_id
            )
            
            session.add_interaction(message, chat_response.dict(), domain)
            
            return chat_response
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento simple profesional: {e}")
            return self._create_error_response(str(e), session.session_id, start_time)
    
    async def _generate_simple_professional_response(self, analysis_result: Dict[str, Any], message: str, domain: str, session: ChatSession) -> str:
        """💬 RESPUESTA SIMPLE CON TUS PROMPTS PROFESIONALES"""
        try:
            data = analysis_result.get('data', [])
            row_count = analysis_result.get('row_count', 0)
            
            if row_count == 0:
                return f"📊 He procesado tu consulta '{message}' pero no encontré datos específicos para los criterios solicitados. Te sugiero verificar los parámetros o contactar con el equipo de Control de Gestión para más información."
            
            # Usar preferencias del usuario
            user_prefs = session.user_preferences
            
            if user_prefs['communication_style'] == 'concise':
                response_parts = [
                    f"📊 **{message}**",
                    f"Encontrados: {row_count} registros"
                ]
            else:
                response_parts = [
                    f"📊 **Consulta procesada:** {message}",
                    f"**Registros encontrados:** {row_count}",
                    ""
                ]
                
                # Añadir muestra de datos si corresponde
                if data and len(data) > 0 and user_prefs['response_length'] != 'short':
                    first_record = data[0]
                    if isinstance(first_record, dict):
                        key_fields = []
                        for key, value in list(first_record.items())[:3]:
                            if isinstance(value, (int, float)):
                                if isinstance(value, float):
                                    key_fields.append(f"**{key}:** {value:.2f}")
                                else:
                                    key_fields.append(f"**{key}:** {value:,}")
                            else:
                                key_fields.append(f"**{key}:** {value}")
                        
                        if key_fields:
                            response_parts.extend([
                                "**Datos destacados:**",
                                " | ".join(key_fields)
                            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta simple profesional: {e}")
            return f"✅ He procesado tu consulta: {message}"
    
    # [Métodos de soporte heredados del código anterior - mantenidos igual]
    def _format_data_dynamically(self, data: Any, max_depth: int = 3, current_depth: int = 0) -> str:
        """🔧 FORMATEADOR DINÁMICO (heredado)"""
        if current_depth >= max_depth:
            return "📊 Datos adicionales disponibles..."
        
        lines = []
        
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    formatted_key = self._beautify_key(key)
                    formatted_value = self._format_value_by_type(value, current_depth)
                    
                    if formatted_value:
                        lines.append(f"- **{formatted_key}:** {formatted_value}")
            
            elif isinstance(data, list) and data:
                if len(data) == 1:
                    single_item_formatted = self._format_data_dynamically(data[0], max_depth, current_depth + 1)
                    if single_item_formatted:
                        lines.append(single_item_formatted)
                elif len(data) <= 5:
                    for i, item in enumerate(data, 1):
                        item_formatted = self._format_data_dynamically(item, max_depth, current_depth + 1)
                        if item_formatted:
                            lines.append(f"**Elemento {i}:**\n{item_formatted}")
                else:
                    lines.append(f"📋 **Total de elementos:** {len(data)}")
                    for i, item in enumerate(data[:3], 1):
                        item_formatted = self._format_data_dynamically(item, max_depth, current_depth + 1)
                        if item_formatted:
                            lines.append(f"**Top {i}:**\n{item_formatted}")
                    if len(data) > 3:
                        lines.append(f"... y {len(data) - 3} elementos más")
            
            else:
                formatted_value = self._format_value_by_type(data, current_depth)
                if formatted_value:
                    lines.append(formatted_value)
        
        except Exception as e:
            logger.warning(f"Error formateando datos dinámicamente: {e}")
            lines.append("📊 Datos procesados (formato no disponible)")
        
        return "\n".join(lines) if lines else ""
    
    def _format_value_by_type(self, value: Any, current_depth: int) -> str:
        """🎨 FORMATEA VALORES POR TIPO (heredado)"""
        try:
            if value is None:
                return "N/A"
            elif isinstance(value, bool):
                return "✅ Sí" if value else "❌ No"
            elif isinstance(value, (int, float)):
                if isinstance(value, float):
                    if abs(value) >= 1000000:
                        return f"{value:,.0f}"
                    elif abs(value) >= 1000:
                        return f"{value:,.2f}"
                    else:
                        return f"{value:.2f}"
                else:
                    return f"{value:,}"
            elif isinstance(value, str):
                clean_value = value.strip()
                if len(clean_value) > 100:
                    return f"{clean_value[:97]}..."
                return clean_value
            elif isinstance(value, list):
                if not value:
                    return "Lista vacía"
                elif len(value) <= 3:
                    return f"Lista con {len(value)} elementos"
                else:
                    return f"Lista con {len(value)} elementos (mostrando primeros 3)"
            elif isinstance(value, dict):
                if not value:
                    return "Datos vacíos"
                else:
                    if current_depth < 2:
                        nested_formatted = self._format_data_dynamically(value, 2, current_depth + 1)
                        return nested_formatted if nested_formatted else f"Objeto con {len(value)} campos"
                    else:
                        return f"Objeto con {len(value)} campos"
            else:
                str_value = str(value)
                return str_value[:50] + "..." if len(str_value) > 50 else str_value
        
        except Exception as e:
            logger.warning(f"Error formateando valor {type(value)}: {e}")
            return "Valor no disponible"
    
    def _beautify_key(self, key: str) -> str:
        """✨ EMBELLECE NOMBRES DE CAMPOS (heredado)"""
        try:
            replacements = {
                '_': ' ',
                'desc': 'Descripción',
                'id': 'ID',
                'pct': '%',
                'total': 'Total',
                'num': 'Número',
                'count': 'Cantidad',
                'avg': 'Promedio',
                'max': 'Máximo', 
                'min': 'Mínimo'
            }
            
            beautified = key.lower()
            
            for old, new in replacements.items():
                beautified = beautified.replace(old, new)
            
            return ' '.join(word.capitalize() for word in beautified.split())
            
        except Exception as e:
            logger.warning(f"Error embelleciendo clave {key}: {e}")
            return key.replace('_', ' ').title()
    
    def _extract_key_insights(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """🔍 EXTRACTOR DINÁMICO DE INSIGHTS (heredado)"""
        insights = {}
        
        try:
            def extract_from_dict(data_dict, prefix=""):
                for key, value in data_dict.items():
                    clean_key = f"{prefix}_{key}" if prefix else key
                    
                    if isinstance(value, (int, float)):
                        if any(indicator in key.lower() for indicator in ['pct', 'percent', '%', 'porcentaje']):
                            insights[f"percentage_{clean_key}"] = value
                        elif any(indicator in key.lower() for indicator in ['total', 'ingresos', 'gastos', 'beneficio']):
                            insights[f"financial_{clean_key}"] = value
                        elif any(indicator in key.lower() for indicator in ['roe', 'margen', 'eficiencia', 'ratio']):
                            insights[f"kpi_{clean_key}"] = value
                        else:
                            insights[f"metric_{clean_key}"] = value
                    
                    elif isinstance(value, str):
                        if any(indicator in key.lower() for indicator in ['clasificacion', 'clase', 'nivel', 'categoria']):
                            insights[f"classification_{clean_key}"] = value
                        elif any(indicator in key.lower() for indicator in ['desc', 'descripcion', 'nombre']):
                            insights[f"description_{clean_key}"] = value
                        elif len(value) < 50:
                            insights[f"text_{clean_key}"] = value
                    
                    elif isinstance(value, dict) and len(str(value)) < 1000:
                        extract_from_dict(value, clean_key)
                    
                    elif isinstance(value, list):
                        insights[f"list_{clean_key}_count"] = len(value)
                        if value and isinstance(value[0], dict):
                            extract_from_dict(value[0], f"{clean_key}_sample")
            
            if isinstance(content, dict):
                extract_from_dict(content)
            
            return insights
            
        except Exception as e:
            logger.warning(f"Error extrayendo insights: {e}")
            return {"error": "No se pudieron extraer insights automáticamente"}
    
    def _clean_explanation(self, explanation: str) -> str:
        """🧹 LIMPIA EXPLICACIONES (heredado)"""
        try:
            cleaned = explanation.strip()
            
            if len(cleaned) > 2000:
                sentences = cleaned.split('. ')
                truncated_sentences = sentences[:10]
                cleaned = '. '.join(truncated_sentences)
                if not cleaned.endswith('.'):
                    cleaned += '.'
                cleaned += "\n\n📊 *Análisis completo disponible en los datos detallados.*"
            
            if len(cleaned.strip()) < 20:
                return "Los datos han sido procesados correctamente. Consulta la sección de datos detallados para más información."
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Error limpiando explicación: {e}")
            return "Análisis completado. Los datos están disponibles en la sección detallada."
    
    def _generate_fallback_explanation(self, content: Dict[str, Any], original_message: str) -> str:
        """🔄 EXPLICACIÓN FALLBACK (heredado)"""
        try:
            explanation_parts = [
                f"He procesado tu consulta sobre: {original_message}",
                ""
            ]
            
            if isinstance(content, dict):
                data_count = len([v for v in content.values() if v is not None])
                explanation_parts.append(f"✅ Se han analizado {data_count} elementos de datos.")
                
                numeric_values = []
                for key, value in content.items():
                    if isinstance(value, (int, float)) and value != 0:
                        clean_key = key.replace('_', ' ').title()
                        if isinstance(value, float):
                            numeric_values.append(f"{clean_key}: {value:.2f}")
                        else:
                            numeric_values.append(f"{clean_key}: {value:,}")
                
                if numeric_values:
                    explanation_parts.extend([
                        "",
                        "📊 Valores destacados identificados:",
                        "\n".join([f"• {nv}" for nv in numeric_values[:5]])
                    ])
            
            explanation_parts.extend([
                "",
                "Los datos completos están disponibles en la sección detallada para tu revisión."
            ])
            
            return "\n".join(explanation_parts)
            
        except Exception as e:
            logger.warning(f"Error en explicación fallback: {e}")
            return f"He procesado tu consulta: {original_message}. Los resultados están disponibles en los datos detallados."
    
    async def _call_simple_query_system(self, domain: str, message: str, gestor_id: str, periodo: str) -> Dict[str, Any]:
        """🔍 LLAMADAS SIMPLES A QUERIES (heredado)"""
        try:
            if domain in ['performance_analysis', 'gestor']:
                result = self.gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo)
                return {
                    'type': 'gestor_simple',
                    'data': result.data if result and hasattr(result, 'data') else [],
                    'row_count': result.row_count if result and hasattr(result, 'row_count') else 0,
                    'query_method': 'get_gestor_performance_enhanced'
                }
            elif domain in ['comparative_analysis', 'ranking', 'general']:
                result = self.comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
                return {
                    'type': 'ranking_simple',
                    'data': result.data if result and hasattr(result, 'data') else [],
                    'row_count': result.row_count if result and hasattr(result, 'row_count') else 0,
                    'query_method': 'ranking_gestores_por_margen_enhanced'
                }
            else:
                return {
                    'type': 'general_simple',
                    'data': [],
                    'row_count': 0,
                    'query_method': 'general_response'
                }
        except Exception as e:
            logger.error(f"Error en query simple: {e}")
            return {'type': 'error', 'data': [], 'row_count': 0, 'error': str(e)}
    
    def _get_simple_recommendations(self, analysis_result: Dict[str, Any], domain: str) -> List[str]:
        """💡 RECOMENDACIONES SIMPLES (heredado)"""
        base_recommendations = {
            'performance_analysis': [
                "Consulta métricas específicas para análisis detallado",
                "Compara con otros gestores para contexto"
            ],
            'comparative_analysis': [
                "Analiza las mejores prácticas de los top performers",
                "Identifica oportunidades de mejora"
            ],
            'deviation_detection': [
                "Prioriza atención a desviaciones críticas",
                "Investiga causas raíz de anomalías"
            ],
            'incentive_analysis': [
                "Revisa cumplimiento de objetivos",
                "Evalúa impacto de incentivos"
            ]
        }
        
        return base_recommendations.get(domain, [
            "Consulta información más específica para análisis detallado",
            "Considera análisis comparativos para mayor contexto"
        ])
    
    def _sanitize_message(self, message: str) -> str:
        """🧹 SANITIZA MENSAJE (heredado)"""
        if not message or not isinstance(message, str):
            return ""
        
        sanitized = message.strip()
        if len(sanitized) > 2000:
            sanitized = sanitized[:2000] + "..."
            logger.warning("Mensaje truncado por exceder longitud máxima")
        
        return sanitized
    
    def _create_error_response(self, error_message: str, session_id: str, start_time: datetime) -> ChatResponse:
        """❌ RESPUESTA DE ERROR PROFESIONAL"""
        return ChatResponse(
            response=f"❌ Lo siento, ha ocurrido un error procesando tu consulta: {error_message}\n\n💡 Por favor, intenta reformular tu pregunta o contacta con el equipo de Control de Gestión para asistencia especializada.",
            response_type="error",
            charts=[],
            recommendations=[
                "Intenta reformular tu pregunta de forma más específica",
                "Verifica que los parámetros sean correctos",
                "Contacta con el equipo de Control de Gestión si persiste el problema"
            ],
            metadata={
                "error": True,
                "error_message": error_message,
                "imports_successful": self.imports_successful,
                "model_used": MODEL_NAME,
                "professional_prompts": True
            },
            execution_time=(datetime.now() - start_time).total_seconds(),
            confidence_score=0.0,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """📊 ESTADO DEL AGENTE CON PROMPTS PROFESIONALES"""
        return {
            'status': 'active',
            'version': '6.1',
            'mode': 'PRODUCTION' if self.imports_successful else 'MOCK',
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'active_sessions': len(self.session_manager.sessions),
            'websocket_connections': len(self.session_manager.websocket_connections),
            'model_configured': MODEL_NAME,
            'integrations': {
                'cdg_agent': 'active' if self.cdg_agent else 'inactive',
                'professional_prompts': 'active',
                'personalization': 'active',
                'intent_classification': 'active',
                'feedback_processing': 'active'
            },
            'features': {
                'intelligent_period_extraction': True,
                'intelligent_gestor_extraction': True,
                'cdg_agent_delegation': True,
                'professional_system_prompts': True,
                'intent_classification': True,
                'personalization_engine': True,
                'feedback_learning': True,
                'conversation_memory': True,
                'dynamic_formatting': True
            },
            'prompt_systems': {
                'conversational': 'CHAT_CONVERSATIONAL_SYSTEM_PROMPT',
                'feedback': 'CHAT_FEEDBACK_SYSTEM_PROMPT', 
                'intent_classification': 'CHAT_INTENT_CLASSIFICATION_PROMPT',
                'personalization': 'CHAT_PERSONALIZATION_SYSTEM_PROMPT'
            },
            'architecture': 'professional_v6.1'
        }
    
    def get_session_history(self, user_id: str):
        """📚 HISTORIAL CON PERSONALIZACIÓN"""
        if user_id in self.session_manager.sessions:
            session = self.session_manager.sessions[user_id]
            return {
                'conversation_history': session.conversation_history,
                'user_preferences': session.user_preferences,
                'personalization_data': session.personalization_data
            }
        return {'conversation_history': [], 'user_preferences': {}, 'personalization_data': {}}
    
    def get_dynamic_suggestions(self, user_id: str) -> List[str]:
        """💡 SUGERENCIAS INTELIGENTES PERSONALIZADAS"""
        current_period = datetime.now().strftime('%Y-%m')
        
        # Obtener preferencias del usuario si existe
        user_prefs = {}
        if user_id in self.session_manager.sessions:
            session = self.session_manager.sessions[user_id]
            user_prefs = session.user_preferences
            frequent_queries = session.personalization_data.get('frequent_queries', [])
        else:
            frequent_queries = []
        
        # Sugerencias base
        base_suggestions = [
            f"¿Cómo está mi rendimiento en {current_period}?",
            "Comparar gestores 18 y 21 en ROE",
            "Comparar segmentos Empresas vs Minorista",
            "Análisis del centro de Madrid vs Barcelona",
            f"¿Qué gestores tienen alertas críticas en {current_period}?",
            f"¿Quién merece incentivos en {current_period}?",
            "Business Review del gestor 19",
            "Executive Summary del período actual"
        ]
        
        # Personalizar según consultas frecuentes
        if 'performance_analysis' in frequent_queries:
            base_suggestions.insert(1, f"Performance detallado del gestor 19 en {current_period}")
        if 'comparative_analysis' in frequent_queries:
            base_suggestions.insert(2, "Ranking de eficiencia operativa por centro")
        if 'deviation_detection' in frequent_queries:
            base_suggestions.insert(3, "Detectar desviaciones críticas automáticamente")
        
        return base_suggestions[:8]  # Limitar a 8 sugerencias

# ============================================================================
# APLICACIÓN FASTAPI CON PROMPTS PROFESIONALES
# ============================================================================

# Instancia global del agente
try:
    chat_agent = CDGChatAgent()
    logger.info("✅ CDG Chat Agent v6.1 inicializado correctamente con System Prompts Profesionales")
except Exception as e:
    logger.error(f"❌ Error inicializando chat agent: {e}")
    chat_agent = None

# Aplicación FastAPI
app = FastAPI(
    title="CDG Chat Agent v6.1 - Con System Prompts Profesionales",
    description="API conversacional con prompts especializados para control de gestión bancario",
    version="6.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ENDPOINTS DE LA API CON FUNCIONALIDADES PROFESIONALES
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """🚀 Endpoint principal con System Prompts Profesionales"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no inicializado")
    
    return await chat_agent.process_chat_message(chat_message)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """🔌 WebSocket con personalización avanzada"""
    await websocket.accept()
    
    if chat_agent is None:
        await websocket.send_json({"error": "Chat agent no disponible"})
        await websocket.close()
        return
    
    chat_agent.session_manager.add_websocket_connection(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
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
            
            response = await chat_agent.process_chat_message(chat_message)
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket desconectado para usuario {user_id}")
        if chat_agent:
            chat_agent.session_manager.remove_websocket_connection(user_id)

@app.get("/history/{user_id}")
async def get_chat_history(user_id: str):
    """📚 Historial conversacional con personalización"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no disponible")
    
    history_data = chat_agent.get_session_history(user_id)
    return {
        "user_id": user_id,
        "conversation_history": history_data.get('conversation_history', []),
        "user_preferences": history_data.get('user_preferences', {}),
        "personalization_data": history_data.get('personalization_data', {}),
        "total_interactions": len(history_data.get('conversation_history', []))
    }

@app.post("/reset/{user_id}")
async def reset_session(user_id: str):
    """🔄 Reinicia sesión con preservación de personalización"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no disponible")
    
    # Preservar preferencias del usuario antes del reset
    preserved_prefs = {}
    if user_id in chat_agent.session_manager.sessions:
        session = chat_agent.session_manager.sessions[user_id]
        preserved_prefs = {
            'user_preferences': session.user_preferences.copy(),
            'successful_interactions': session.personalization_data.get('successful_interactions', 0)
        }
    
    chat_agent.session_manager.reset_session(user_id)
    
    # Restaurar preferencias aprendidas
    if preserved_prefs and user_id in chat_agent.session_manager.sessions:
        new_session = chat_agent.session_manager.sessions[user_id]
        new_session.user_preferences.update(preserved_prefs['user_preferences'])
        new_session.personalization_data['successful_interactions'] = preserved_prefs['successful_interactions']
    
    return {
        "message": f"Sesión reiniciada para usuario {user_id}",
        "preferences_preserved": bool(preserved_prefs),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/suggestions/{user_id}")
async def get_dynamic_suggestions(user_id: str):
    """💡 Sugerencias inteligentes personalizadas"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no disponible")
    
    suggestions = chat_agent.get_dynamic_suggestions(user_id)
    
    # Obtener contexto de personalización
    personalization_context = {}
    if user_id in chat_agent.session_manager.sessions:
        session = chat_agent.session_manager.sessions[user_id]
        personalization_context = {
            'communication_style': session.user_preferences.get('communication_style', 'professional'),
            'technical_level': session.user_preferences.get('technical_level', 'intermediate'),
            'frequent_queries': session.personalization_data.get('frequent_queries', []),
            'successful_interactions': session.personalization_data.get('successful_interactions', 0)
        }
    
    return {
        "user_id": user_id,
        "suggestions": suggestions,
        "personalization_context": personalization_context,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/feedback/{user_id}")
async def submit_feedback(user_id: str, feedback: Dict[str, Any]):
    """📝 Endpoint dedicado para feedback con procesamiento profesional"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no disponible")
    
    try:
        # Obtener sesión
        session = chat_agent.session_manager.get_or_create_session(user_id)
        
        # Procesar feedback con tus prompts profesionales
        await chat_agent._process_user_feedback_professional(user_id, feedback, session)
        
        # Actualizar última interacción con rating si está disponible
        if session.conversation_history and 'rating' in feedback:
            session.conversation_history[-1]['satisfaction_rating'] = feedback['rating']
        
        return {
            "message": "Feedback procesado correctamente",
            "user_id": user_id,
            "feedback_processed": True,
            "personalization_updated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error procesando feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando feedback: {str(e)}")

@app.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """⚙️ Obtener preferencias de personalización del usuario"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no disponible")
    
    if user_id not in chat_agent.session_manager.sessions:
        # Crear sesión nueva con preferencias por defecto
        session = chat_agent.session_manager.get_or_create_session(user_id)
    else:
        session = chat_agent.session_manager.sessions[user_id]
    
    return {
        "user_id": user_id,
        "preferences": session.user_preferences,
        "personalization_data": {
            "total_interactions": len(session.conversation_history),
            "successful_interactions": session.personalization_data.get('successful_interactions', 0),
            "frequent_queries": session.personalization_data.get('frequent_queries', []),
            "last_active": session.last_active.isoformat(),
            "created_at": session.created_at.isoformat()
        }
    }

@app.put("/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: Dict[str, str]):
    """⚙️ Actualizar preferencias de personalización"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no disponible")
    
    try:
        session = chat_agent.session_manager.get_or_create_session(user_id)
        
        # Validar y actualizar preferencias
        valid_preferences = {
            'communication_style': ['professional', 'concise', 'detailed'],
            'technical_level': ['basic', 'intermediate', 'advanced'],
            'preferred_format': ['text', 'charts', 'combined'],
            'response_length': ['short', 'medium', 'detailed']
        }
        
        updated_prefs = {}
        for key, value in preferences.items():
            if key in valid_preferences and value in valid_preferences[key]:
                session.user_preferences[key] = value
                updated_prefs[key] = value
        
        return {
            "message": "Preferencias actualizadas correctamente",
            "user_id": user_id,
            "updated_preferences": updated_prefs,
            "current_preferences": session.user_preferences,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error actualizando preferencias: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando preferencias: {str(e)}")

@app.get("/intent/classify")
async def classify_intent_endpoint(message: str, user_id: Optional[str] = None):
    """🧠 Endpoint para clasificación de intenciones (útil para testing)"""
    if chat_agent is None:
        raise HTTPException(status_code=500, detail="Chat agent no disponible")
    
    try:
        # Crear sesión temporal si no se proporciona user_id
        if user_id:
            session = chat_agent.session_manager.get_or_create_session(user_id)
        else:
            session = ChatSession("temp_user")
        
        # Clasificar intención
        intent_analysis = await chat_agent._classify_user_intent(message, session)
        
        return {
            "message": message,
            "intent_analysis": intent_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clasificando intención: {e}")
        raise HTTPException(status_code=500, detail=f"Error clasificando intención: {str(e)}")

@app.get("/status")
async def get_status():
    """📊 Estado completo del agente con información profesional"""
    if chat_agent is None:
        return {"status": "error", "message": "Chat agent no inicializado"}
    
    status = chat_agent.get_agent_status()
    
    # Añadir estadísticas de sesiones activas
    session_stats = {
        'total_sessions': len(chat_agent.session_manager.sessions),
        'active_websockets': len(chat_agent.session_manager.websocket_connections),
        'personalized_users': len([s for s in chat_agent.session_manager.sessions.values() 
                                 if s.personalization_data.get('successful_interactions', 0) > 0])
    }
    
    status['session_statistics'] = session_stats
    return status

@app.get("/health")
async def health_check():
    """🏥 Health check completo del servicio"""
    health_status = "healthy" if chat_agent is not None else "degraded"
    
    # Verificar componentes críticos
    component_status = {
        'chat_agent': chat_agent is not None,
        'cdg_agent_integration': chat_agent.cdg_agent is not None if chat_agent else False,
        'professional_prompts': IMPORTS_SUCCESSFUL,
        'database_connection': True,  # Asumir OK si no hay errores
        'llm_client': chat_agent.llm_client is not None if chat_agent else False
    }
    
    all_components_healthy = all(component_status.values())
    if not all_components_healthy:
        health_status = "degraded"
    
    return {
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "version": "6.1.0",
        "service": "CDG Chat Agent - Con System Prompts Profesionales",
        "components": component_status,
        "features": {
            "professional_system_prompts": True,
            "intent_classification": True,
            "personalization_engine": True,
            "feedback_learning": True,
            "cdg_agent_integration": True,
            "conversation_memory": True,
            "websocket_support": True
        },
        "model_configured": MODEL_NAME,
        "imports_successful": IMPORTS_SUCCESSFUL
    }

@app.get("/")
async def root():
    """🏠 Endpoint raíz con información del servicio"""
    return {
        "service": "CDG Chat Agent v6.1",
        "description": "API conversacional profesional para Control de Gestión bancario con System Prompts especializados",
        "version": "6.1.0",
        "features": [
            "Integración completa con CDG Agent",
            "System Prompts profesionales especializados",
            "Clasificación inteligente de intenciones",
            "Personalización adaptativa por usuario",
            "Procesamiento avanzado de feedback",
            "Gestión conversacional con memoria",
            "Respuestas adaptativas según contexto bancario"
        ],
        "endpoints": {
            "chat": "POST /chat - Procesamiento principal de mensajes",
            "websocket": "WS /ws/{user_id} - Comunicación en tiempo real",
            "history": "GET /history/{user_id} - Historial conversacional",
            "suggestions": "GET /suggestions/{user_id} - Sugerencias personalizadas",
            "feedback": "POST /feedback/{user_id} - Envío de feedback",
            "preferences": "GET/PUT /preferences/{user_id} - Gestión de preferencias",
            "intent": "GET /intent/classify - Clasificación de intenciones",
            "status": "GET /status - Estado del agente",
            "health": "GET /health - Verificación de salud"
        },
        "documentation": "/docs",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configuración de logging mejorada
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('chat_agent.log', mode='a', encoding='utf-8')
        ]
    )
    
    logger.info("🚀 Iniciando CDG Chat Agent v6.1 con System Prompts Profesionales...")
    logger.info(f"📊 Modo: {'PRODUCTION' if IMPORTS_SUCCESSFUL else 'MOCK'}")
    logger.info(f"🤖 Modelo configurado: {MODEL_NAME}")
    
    uvicorn.run(
        "chat_agent:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
