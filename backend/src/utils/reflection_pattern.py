"""
Reflection Pattern para Agente CDG - Sistema de Aprendizaje Continuo
==================================================================

Implementa el patrón de reflexión y aprendizaje continuo para el agente CDG de Banca March.
Gestiona feedback de usuarios, personalización por gestor y memoria organizacional.

Según especificaciones del proyecto:
- Feedback Loop Integrado: Cada gráfico/respuesta incluye valoración del usuario
- Comentarios textuales específicos sobre áreas de mejora
- Incorporación automática de feedback en comportamiento futuro
- Personalización por Gestor: Adaptación al estilo comunicativo
- Memoria Organizacional: Patrones de uso y mejora iterativa

Autor: Agente CDG Development Team
Fecha: 2025-08-01
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum

# Importar módulos para integración con agentes existentes
try:
    from ..utils.initial_agent import iniciar_agente_llm
    from ..prompts.system_prompts import CHAT_PERSONALIZATION_SYSTEM_PROMPT
    from ..prompts.user_prompts import (
        build_feedback_processing_prompt,
        build_personalization_learning_prompt
    )
except ImportError:
    from utils.initial_agent import iniciar_agente_llm
    from prompts.system_prompts import CHAT_PERSONALIZATION_SYSTEM_PROMPT
    from prompts.user_prompts import (
        build_feedback_processing_prompt,
        build_personalization_learning_prompt
    )

# Logger para auditoría del sistema de aprendizaje
logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Tipos de feedback que puede proporcionar el usuario"""
    ACCURACY = "accuracy"           # Precisión del análisis
    CLARITY = "clarity"             # Claridad de la explicación
    USEFULNESS = "usefulness"       # Utilidad práctica
    FORMAT = "format"               # Preferencias de formato
    COMPLETENESS = "completeness"   # Completitud del análisis

class LearningSignal(Enum):
    """Señales de aprendizaje del sistema"""
    POSITIVE = "positive"           # Comportamiento a reforzar
    NEGATIVE = "negative"           # Comportamiento a corregir
    NEUTRAL = "neutral"             # Sin cambio significativo

@dataclass
class FeedbackEntry:
    """
    Representa una entrada de feedback proporcionada por un gestor
    """
    user_id: str
    query: str
    response: str
    response_type: str
    feedback_rating: Optional[int] = None  # 1-5 escala
    feedback_comments: Optional[str] = None
    feedback_categories: Dict[FeedbackType, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    charts_included: bool = False
    recommendations_included: bool = False
    
    def get_overall_sentiment(self) -> LearningSignal:
        """Determina el sentimiento general del feedback"""
        if self.feedback_rating:
            if self.feedback_rating >= 4:
                return LearningSignal.POSITIVE
            elif self.feedback_rating <= 2:
                return LearningSignal.NEGATIVE
        return LearningSignal.NEUTRAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'user_id': self.user_id,
            'query': self.query,
            'response': self.response[:200] + "..." if len(self.response) > 200 else self.response,
            'response_type': self.response_type,
            'feedback_rating': self.feedback_rating,
            'feedback_comments': self.feedback_comments,
            'feedback_categories': {k.value: v for k, v in self.feedback_categories.items()},
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id,
            'sentiment': self.get_overall_sentiment().value
        }

@dataclass
class UserPersonalizationProfile:
    """
    Perfil de personalización dinámico por gestor
    """
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Preferencias de comunicación
    preferred_detail_level: str = "medium"  # low, medium, high
    preferred_chart_types: List[str] = field(default_factory=list)
    preferred_response_format: str = "mixed"  # text, charts, mixed
    
    # Patrones de uso
    frequent_query_types: Dict[str, int] = field(default_factory=dict)
    active_periods: List[str] = field(default_factory=list)  # periodos consultados frecuentemente
    favorite_gestores: List[str] = field(default_factory=list)  # gestores consultados frecuentemente
    
    # Métricas de satisfacción
    total_interactions: int = 0
    average_rating: float = 0.0
    feedback_history: deque = field(default_factory=lambda: deque(maxlen=50))
    
    # Adaptaciones específicas
    technical_level: str = "intermediate"  # basic, intermediate, advanced
    communication_style: str = "professional"  # concise, professional, detailed
    banking_terminology_comfort: str = "medium"  # low, medium, high
    
    def add_feedback(self, feedback: FeedbackEntry):
        """Añade feedback y actualiza métricas automáticamente"""
        self.feedback_history.append(feedback)
        self.total_interactions += 1
        self.last_updated = datetime.now()
        
        # Actualizar rating promedio
        ratings = [f.feedback_rating for f in self.feedback_history if f.feedback_rating]
        if ratings:
            self.average_rating = sum(ratings) / len(ratings)
        
        # Actualizar patrones de uso
        if feedback.response_type in self.frequent_query_types:
            self.frequent_query_types[feedback.response_type] += 1
        else:
            self.frequent_query_types[feedback.response_type] = 1
        
        logger.info(f"Feedback integrado para usuario {self.user_id}: rating {feedback.feedback_rating}")
    
    def update_preferences_from_feedback(self, feedback: FeedbackEntry):
        """Actualiza preferencias basándose en feedback específico"""
        # Analizar comentarios para extraer preferencias implícitas
        if feedback.feedback_comments:
            comments_lower = feedback.feedback_comments.lower()
            
            # Detectar preferencias de detalle
            if any(word in comments_lower for word in ["más detalle", "profundizar", "ampliar"]):
                if self.preferred_detail_level == "low":
                    self.preferred_detail_level = "medium"
                elif self.preferred_detail_level == "medium":
                    self.preferred_detail_level = "high"
            
            elif any(word in comments_lower for word in ["conciso", "resumir", "breve"]):
                if self.preferred_detail_level == "high":
                    self.preferred_detail_level = "medium"
                elif self.preferred_detail_level == "medium":
                    self.preferred_detail_level = "low"
            
            # Detectar preferencias de formato
            if any(word in comments_lower for word in ["gráfico", "visual", "chart"]):
                if "charts" not in self.preferred_response_format:
                    self.preferred_response_format = "charts"
            
            elif any(word in comments_lower for word in ["texto", "explicación", "narrativo"]):
                if self.preferred_response_format != "text":
                    self.preferred_response_format = "mixed"
    
    def get_personalization_summary(self) -> str:
        """Genera resumen para uso en prompts"""
        return f"""
        Usuario: {self.user_id}
        Nivel de detalle preferido: {self.preferred_detail_level}
        Formato preferido: {self.preferred_response_format}
        Nivel técnico: {self.technical_level}
        Estilo comunicativo: {self.communication_style}
        Interacciones totales: {self.total_interactions}
        Rating promedio: {self.average_rating:.2f}
        Consultas frecuentes: {', '.join(list(self.frequent_query_types.keys())[:3])}
        """
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'preferred_detail_level': self.preferred_detail_level,
            'preferred_chart_types': self.preferred_chart_types,
            'preferred_response_format': self.preferred_response_format,
            'frequent_query_types': self.frequent_query_types,
            'technical_level': self.technical_level,
            'communication_style': self.communication_style,
            'total_interactions': self.total_interactions,
            'average_rating': self.average_rating
        }

@dataclass
class OrganizationalMemory:
    """
    Memoria organizacional que captura patrones globales de uso
    """
    # Patrones de uso por tipo de gestor/área
    usage_patterns_by_role: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Consultas más frecuentes identificadas
    frequent_queries: List[Tuple[str, int]] = field(default_factory=list)
    
    # Mejores prácticas identificadas
    best_practices: Dict[str, List[str]] = field(default_factory=dict)
    
    # Terminología específica de Banca March aprendida
    domain_vocabulary: Dict[str, str] = field(default_factory=dict)
    
    # Métricas globales de calidad
    global_satisfaction_metrics: Dict[str, float] = field(default_factory=dict)
    
    def update_from_feedback(self, feedback: FeedbackEntry, user_profile: UserPersonalizationProfile):
        """Actualiza memoria organizacional basándose en feedback"""
        # Actualizar patrones por rol (inferido del user_id o contexto)
        role = self._infer_user_role(feedback.user_id)
        if role not in self.usage_patterns_by_role:
            self.usage_patterns_by_role[role] = {}
        
        if feedback.response_type in self.usage_patterns_by_role[role]:
            self.usage_patterns_by_role[role][feedback.response_type] += 1
        else:
            self.usage_patterns_by_role[role][feedback.response_type] = 1
        
        # Identificar mejores prácticas de respuestas bien valoradas
        if feedback.get_overall_sentiment() == LearningSignal.POSITIVE:
            if feedback.response_type not in self.best_practices:
                self.best_practices[feedback.response_type] = []
            
            # Extraer elementos exitosos de la respuesta
            if feedback.charts_included and len(self.best_practices[feedback.response_type]) < 10:
                self.best_practices[feedback.response_type].append("include_charts_positive_feedback")
    
    def _infer_user_role(self, user_id: str) -> str:
        """Infiere el rol del usuario basándose en patrones de ID"""
        # Lógica simple - en producción podría ser más sofisticada
        if user_id.startswith("gestor_"):
            return "gestor_comercial"
        elif user_id.startswith("control_"):
            return "control_gestion"
        elif user_id.startswith("direccion_"):
            return "direccion_financiera"
        else:
            return "usuario_general"

class ReflectionPatternManager:
    """
    Gestor central del sistema de aprendizaje continuo para el agente CDG
    """
    
    def __init__(self, enable_llm_analysis: bool = True):
        """
        Inicializa el gestor de reflection pattern
        
        Args:
            enable_llm_analysis: Si habilitar análisis avanzado con LLM
        """
        self.user_profiles: Dict[str, UserPersonalizationProfile] = {}
        self.organizational_memory = OrganizationalMemory()
        self.enable_llm_analysis = enable_llm_analysis
        self.llm_client = iniciar_agente_llm(CHAT_PERSONALIZATION_SYSTEM_PROMPT) if enable_llm_analysis else None
        
        # Configuración de persistencia (en producción usar base de datos)
        self.persistence_enabled = False
        
        logger.info("🧠 Reflection Pattern Manager inicializado")
    
    def get_user_profile(self, user_id: str) -> UserPersonalizationProfile:
        """Obtiene o crea el perfil de personalización del usuario"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserPersonalizationProfile(user_id=user_id)
            logger.info(f"📋 Nuevo perfil de personalización creado para usuario {user_id}")
        
        return self.user_profiles[user_id]
    
    async def process_feedback(
        self,
        user_id: str,
        query: str,
        response: str,
        response_type: str,
        feedback_rating: Optional[int] = None,
        feedback_comments: Optional[str] = None,
        feedback_categories: Optional[Dict[FeedbackType, int]] = None,
        session_id: Optional[str] = None,
        charts_included: bool = False,
        recommendations_included: bool = False
    ) -> Dict[str, Any]:
        """
        Procesa feedback del usuario e integra aprendizajes
        
        Args:
            user_id: ID del usuario
            query: Consulta original del usuario
            response: Respuesta proporcionada por el agente
            response_type: Tipo de análisis realizado
            feedback_rating: Calificación 1-5
            feedback_comments: Comentarios textuales
            feedback_categories: Feedback por categorías específicas
            session_id: ID de la sesión
            charts_included: Si la respuesta incluyó gráficos
            recommendations_included: Si incluyó recomendaciones
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Crear entrada de feedback
            feedback_entry = FeedbackEntry(
                user_id=user_id,
                query=query,
                response=response,
                response_type=response_type,
                feedback_rating=feedback_rating,
                feedback_comments=feedback_comments,
                feedback_categories=feedback_categories or {},
                session_id=session_id,
                charts_included=charts_included,
                recommendations_included=recommendations_included
            )
            
            # Obtener perfil del usuario
            user_profile = self.get_user_profile(user_id)
            
            # Integrar feedback en el perfil
            user_profile.add_feedback(feedback_entry)
            user_profile.update_preferences_from_feedback(feedback_entry)
            
            # Actualizar memoria organizacional
            self.organizational_memory.update_from_feedback(feedback_entry, user_profile)
            
            # Análisis avanzado con LLM si está habilitado
            llm_insights = None
            if self.enable_llm_analysis and feedback_comments:
                llm_insights = await self._analyze_feedback_with_llm(feedback_entry, user_profile)
            
            # Generar recomendaciones de mejora
            improvement_recommendations = self._generate_improvement_recommendations(
                feedback_entry, user_profile, llm_insights
            )
            
            processing_result = {
                'status': 'processed',
                'user_profile_updated': True,
                'learning_signal': feedback_entry.get_overall_sentiment().value,
                'improvement_recommendations': improvement_recommendations,
                'llm_insights': llm_insights,
                'personalization_summary': user_profile.get_personalization_summary()
            }
            
            logger.info(f"✅ Feedback procesado exitosamente para usuario {user_id}")
            return processing_result
            
        except Exception as e:
            logger.error(f"❌ Error procesando feedback para usuario {user_id}: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'user_profile_updated': False
            }
    
    async def _analyze_feedback_with_llm(
        self, 
        feedback: FeedbackEntry, 
        user_profile: UserPersonalizationProfile
    ) -> Optional[Dict[str, Any]]:
        """
        Analiza feedback usando LLM para extraer insights profundos
        
        Args:
            feedback: Entrada de feedback a analizar
            user_profile: Perfil actual del usuario
            
        Returns:
            Insights del análisis con LLM
        """
        try:
            # Construir prompt para análisis de feedback
            feedback_prompt = build_feedback_processing_prompt(
                user_id=feedback.user_id,
                original_query=feedback.query,
                agent_response=feedback.response,
                feedback_data={
                    'rating': feedback.feedback_rating,
                    'comments': feedback.feedback_comments,
                    'response_type': feedback.response_type
                }
            )
            
            # Llamar al LLM para análisis
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": CHAT_PERSONALIZATION_SYSTEM_PROMPT},
                    {"role": "user", "content": feedback_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            analysis_content = response.choices[0].message.content
            
            # Extraer insights estructurados del análisis
            insights = {
                'analysis_content': analysis_content,
                'extracted_preferences': self._extract_preferences_from_analysis(analysis_content),
                'improvement_areas': self._extract_improvement_areas(analysis_content),
                'personalization_adjustments': self._extract_personalization_adjustments(analysis_content)
            }
            
            logger.info(f"🔍 Análisis LLM completado para usuario {feedback.user_id}")
            return insights
            
        except Exception as e:
            logger.warning(f"Error en análisis LLM: {e}")
            return None
    
    def _extract_preferences_from_analysis(self, analysis: str) -> Dict[str, str]:
        """Extrae preferencias del análisis del LLM"""
        preferences = {}
        analysis_lower = analysis.lower()
        
        # Lógica simple de extracción - en producción sería más sofisticada
        if 'detalle' in analysis_lower or 'profundidad' in analysis_lower:
            preferences['detail_preference'] = 'high'
        elif 'conciso' in analysis_lower or 'breve' in analysis_lower:
            preferences['detail_preference'] = 'low'
        
        if 'gráfico' in analysis_lower or 'visual' in analysis_lower:
            preferences['format_preference'] = 'visual'
        
        return preferences
    
    def _extract_improvement_areas(self, analysis: str) -> List[str]:
        """Extrae áreas de mejora del análisis del LLM"""
        # Lógica simplificada - en producción sería más sofisticada
        improvement_areas = []
        analysis_lower = analysis.lower()
        
        if 'claridad' in analysis_lower:
            improvement_areas.append('Mejorar claridad de explicaciones')
        if 'precision' in analysis_lower:
            improvement_areas.append('Aumentar precisión de análisis')
        if 'útil' in analysis_lower and 'más' in analysis_lower:
            improvement_areas.append('Incrementar utilidad práctica')
        
        return improvement_areas
    
    def _extract_personalization_adjustments(self, analysis: str) -> Dict[str, str]:
        """Extrae ajustes de personalización del análisis del LLM"""
        adjustments = {}
        
        # Lógica simplificada para extraer ajustes específicos
        if 'técnico' in analysis.lower():
            adjustments['technical_level'] = 'advanced'
        elif 'básico' in analysis.lower():
            adjustments['technical_level'] = 'basic'
        
        return adjustments
    
    def _generate_improvement_recommendations(
        self,
        feedback: FeedbackEntry,
        user_profile: UserPersonalizationProfile,
        llm_insights: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Genera recomendaciones específicas de mejora
        
        Args:
            feedback: Feedback recibido
            user_profile: Perfil del usuario
            llm_insights: Insights del análisis LLM
            
        Returns:
            Lista de recomendaciones específicas
        """
        recommendations = []
        
        # Recomendaciones basadas en rating
        if feedback.feedback_rating and feedback.feedback_rating <= 2:
            recommendations.append("Revisar enfoque de respuesta para este tipo de consulta")
            recommendations.append("Considerar formato alternativo de presentación")
        
        # Recomendaciones basadas en comentarios
        if feedback.feedback_comments:
            comments_lower = feedback.feedback_comments.lower()
            if 'confuso' in comments_lower:
                recommendations.append("Mejorar claridad en explicaciones futuras")
            if 'incompleto' in comments_lower:
                recommendations.append("Incluir más detalles en análisis similares")
        
        # Recomendaciones basadas en insights del LLM
        if llm_insights and llm_insights.get('improvement_areas'):
            recommendations.extend(llm_insights['improvement_areas'])
        
        # Recomendaciones basadas en patrones del perfil
        if user_profile.average_rating < 3.0 and user_profile.total_interactions > 5:
            recommendations.append("Reevaluar enfoque general para este usuario")
        
        return recommendations[:5]  # Limitar a 5 recomendaciones máximo
    
    def get_personalization_context(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene contexto de personalización para usar en respuestas
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Contexto de personalización para el agente
        """
        user_profile = self.get_user_profile(user_id)
        
        return {
            'preferred_detail_level': user_profile.preferred_detail_level,
            'preferred_response_format': user_profile.preferred_response_format,
            'technical_level': user_profile.technical_level,
            'communication_style': user_profile.communication_style,
            'frequent_query_types': list(user_profile.frequent_query_types.keys())[:3],
            'personalization_summary': user_profile.get_personalization_summary()
        }
    
    def generate_organizational_insights(self) -> Dict[str, Any]:
        """
        Genera insights organizacionales para mejora del sistema
        
        Returns:
            Insights agregados de toda la organización
        """
        total_users = len(self.user_profiles)
        
        if total_users == 0:
            return {'status': 'insufficient_data', 'users_count': 0}
        
        # Calcular métricas agregadas
        avg_satisfaction = sum(p.average_rating for p in self.user_profiles.values()) / total_users
        total_interactions = sum(p.total_interactions for p in self.user_profiles.values())
        
        # Identificar consultas más frecuentes
        all_query_types = defaultdict(int)
        for profile in self.user_profiles.values():
            for query_type, count in profile.frequent_query_types.items():
                all_query_types[query_type] += count
        
        top_queries = sorted(all_query_types.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Identificar usuarios más activos
        active_users = sorted(
            [(uid, p.total_interactions) for uid, p in self.user_profiles.items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        return {
            'status': 'success',
            'total_users': total_users,
            'total_interactions': total_interactions,
            'average_satisfaction': round(avg_satisfaction, 2),
            'top_query_types': top_queries,
            'most_active_users': active_users,
            'usage_patterns': dict(self.organizational_memory.usage_patterns_by_role),
            'best_practices': dict(self.organizational_memory.best_practices)
        }
    
    def reset_user_profile(self, user_id: str) -> bool:
        """
        Reinicia el perfil de un usuario manteniendo métricas históricas básicas
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se reinició exitosamente
        """
        if user_id in self.user_profiles:
            old_profile = self.user_profiles[user_id]
            
            # Crear nuevo perfil manteniendo algunas métricas históricas
            new_profile = UserPersonalizationProfile(user_id=user_id)
            new_profile.total_interactions = old_profile.total_interactions
            new_profile.average_rating = old_profile.average_rating
            
            self.user_profiles[user_id] = new_profile
            logger.info(f"🔄 Perfil reiniciado para usuario {user_id}")
            return True
        
        return False
    
    def export_learning_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporta datos de aprendizaje para análisis o backup
        
        Args:
            user_id: ID específico del usuario, None para todos
            
        Returns:
            Datos de aprendizaje exportados
        """
        if user_id and user_id in self.user_profiles:
            return {
                'user_profile': self.user_profiles[user_id].to_dict(),
                'feedback_history': [f.to_dict() for f in self.user_profiles[user_id].feedback_history]
            }
        else:
            return {
                'all_user_profiles': {uid: p.to_dict() for uid, p in self.user_profiles.items()},
                'organizational_memory': asdict(self.organizational_memory),
                'export_timestamp': datetime.now().isoformat()
            }

# ============================================================================
# FUNCIONES DE INTEGRACIÓN CON AGENTES EXISTENTES
# ============================================================================

# Instancia global del manager de reflection pattern
reflection_manager = ReflectionPatternManager()

async def integrate_feedback_from_chat_agent(
    user_id: str,
    chat_message: str,
    chat_response: Dict[str, Any],
    feedback_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Función de integración para chat_agent.py
    
    Args:
        user_id: ID del usuario
        chat_message: Mensaje original del usuario
        chat_response: Respuesta del chat agent
        feedback_data: Feedback opcional del usuario
        
    Returns:
        Resultado del procesamiento
    """
    if feedback_data:
        return await reflection_manager.process_feedback(
            user_id=user_id,
            query=chat_message,
            response=str(chat_response.get('response', '')),
            response_type=chat_response.get('response_type', 'general'),
            feedback_rating=feedback_data.get('rating'),
            feedback_comments=feedback_data.get('comments'),
            session_id=chat_response.get('session_id'),
            charts_included=bool(chat_response.get('charts', [])),
            recommendations_included=bool(chat_response.get('recommendations', []))
        )
    else:
        # Solo actualizar patrones de uso sin feedback explícito
        user_profile = reflection_manager.get_user_profile(user_id)
        response_type = chat_response.get('response_type', 'general')
        
        if response_type in user_profile.frequent_query_types:
            user_profile.frequent_query_types[response_type] += 1
        else:
            user_profile.frequent_query_types[response_type] = 1
        
        user_profile.total_interactions += 1
        user_profile.last_updated = datetime.now()
        
        return {'status': 'usage_tracked', 'explicit_feedback': False}

def get_personalization_for_user(user_id: str) -> Dict[str, Any]:
    """
    Función de integración para obtener personalización de un usuario
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Contexto de personalización
    """
    return reflection_manager.get_personalization_context(user_id)

async def analyze_feedback_batch(feedback_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Procesa un lote de feedback para análisis agregado
    
    Args:
        feedback_batch: Lista de entradas de feedback
        
    Returns:
        Análisis agregado del lote
    """
    results = []
    
    for feedback_item in feedback_batch:
        result = await reflection_manager.process_feedback(**feedback_item)
        results.append(result)
    
    return {
        'batch_size': len(feedback_batch),
        'processed_successfully': len([r for r in results if r['status'] == 'processed']),
        'processing_errors': len([r for r in results if r['status'] == 'error']),
        'organizational_insights': reflection_manager.generate_organizational_insights()
    }

# ============================================================================
# PUNTO DE ENTRADA PARA TESTING Y DEMOSTRACIÓN
# ============================================================================

if __name__ == "__main__":
    async def demo_reflection_pattern():
        """Demostración del sistema de reflection pattern"""
        print("🧠 Iniciando demo del Reflection Pattern...")
        
        # Test de procesamiento de feedback
        feedback_result = await reflection_manager.process_feedback(
            user_id='gestor_001',
            query='¿Cuál es mi ROE del último trimestre?',
            response='Su ROE del último trimestre es 12.5%, un 15% superior al período anterior.',
            response_type='gestor_analysis',
            feedback_rating=4,
            feedback_comments='Muy útil, pero me gustaría más detalles sobre el cálculo.',
            charts_included=True,
            recommendations_included=True
        )
        
        print("✅ Feedback procesado:")
        print(f"   Estado: {feedback_result['status']}")
        print(f"   Señal de aprendizaje: {feedback_result['learning_signal']}")
        
        # Test de personalización
        personalization = reflection_manager.get_personalization_context('gestor_001')
        print(f"\n📋 Personalización para gestor_001:")
        print(f"   Nivel de detalle preferido: {personalization['preferred_detail_level']}")
        print(f"   Formato preferido: {personalization['preferred_response_format']}")
        
        # Test de insights organizacionales
        insights = reflection_manager.generate_organizational_insights()
        print(f"\n📊 Insights organizacionales:")
        print(f"   Total usuarios: {insights['total_users']}")
        print(f"   Satisfacción promedio: {insights['average_satisfaction']}")
        
        print("\n🎯 Demo completado exitosamente!")
    
    # Ejecutar demo
    import asyncio
    asyncio.run(demo_reflection_pattern())
