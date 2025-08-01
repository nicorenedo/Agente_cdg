"""
CDG Agent - Agente Principal de Control de Gestión - Banca March
==============================================================

Agente coordinador que orquesta todos los módulos del sistema CDG:
- Queries especializadas (gestor, comparative, deviation, incentive)
- Tools avanzados (kpi_calculator, chart_generator, report_generator)
- Prompts contextualizados para análisis bancario
- Integración con Azure OpenAI para respuestas inteligentes

Autor: Agente CDG Development Team
Fecha: 2025-08-01
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Importar módulos especializados del sistema CDG
try:
    # Tools especializados
    from ..tools.kpi_calculator import KPICalculator
    from ..tools.chart_generator import CDGDashboardGenerator
    from ..tools.report_generator import BusinessReportGenerator
    from ..tools.sql_guard import is_query_safe
    
    # Módulos de consultas especializadas
    from ..queries.gestor_queries import GestorQueries
    from ..queries.comparative_queries import ComparativeQueries
    from ..queries.deviation_queries import DeviationQueries
    from ..queries.incentive_queries import IncentiveQueries
    
    # Sistema de prompts y configuración
    from ..prompts.system_prompts import (
        FINANCIAL_ANALYST_SYSTEM_PROMPT,
        FINANCIAL_REPORT_SYSTEM_PROMPT,
        COMPARATIVE_ANALYSIS_SYSTEM_PROMPT,
        DEVIATION_ANALYSIS_SYSTEM_PROMPT
    )
    from ..utils.initial_agent import iniciar_agente_llm
    from ..utils.dynamic_config import ConfigManager
    
except ImportError:
    # Fallback para imports relativos
    from tools.kpi_calculator import KPICalculator
    from tools.chart_generator import CDGDashboardGenerator
    from tools.report_generator import BusinessReportGenerator
    from tools.sql_guard import is_query_safe
    
    from queries.gestor_queries import GestorQueries
    from queries.comparative_queries import ComparativeQueries
    from queries.deviation_queries import DeviationQueries
    from queries.incentive_queries import IncentiveQueries
    
    from prompts.system_prompts import (
        FINANCIAL_ANALYST_SYSTEM_PROMPT,
        FINANCIAL_REPORT_SYSTEM_PROMPT,
        COMPARATIVE_ANALYSIS_SYSTEM_PROMPT,
        DEVIATION_ANALYSIS_SYSTEM_PROMPT
    )
    from utils.initial_agent import iniciar_agente_llm
    from utils.dynamic_config import ConfigManager

# Logger para auditoría completa
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Tipos de consultas que puede manejar el agente CDG"""
    GESTOR_ANALYSIS = "gestor_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    DEVIATION_ANALYSIS = "deviation_analysis"
    INCENTIVE_ANALYSIS = "incentive_analysis"
    BUSINESS_REVIEW = "business_review"
    EXECUTIVE_SUMMARY = "executive_summary"
    GENERAL_CHAT = "general_chat"

class ResponseFormat(Enum):
    """Formatos de respuesta disponibles"""
    JSON = "json"
    TEXT = "text"
    DASHBOARD = "dashboard"
    BUSINESS_REPORT = "business_report"

@dataclass
class CDGRequest:
    """Estructura de request para el agente CDG"""
    user_message: str
    user_id: Optional[str] = None
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    context: Dict[str, Any] = None
    response_format: ResponseFormat = ResponseFormat.JSON
    include_charts: bool = True
    include_recommendations: bool = True

@dataclass
class CDGResponse:
    """Estructura de respuesta del agente CDG"""
    response_type: QueryType
    content: Dict[str, Any]
    charts: List[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any]
    execution_time: float
    confidence_score: float
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la respuesta a diccionario"""
        return {
            'response_type': self.response_type.value,
            'content': self.content,
            'charts': self.charts,
            'recommendations': self.recommendations,
            'metadata': self.metadata,
            'execution_time': self.execution_time,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat()
        }

class CDGAgent:
    """
    Agente Principal de Control de Gestión - Banca March
    
    Coordina todos los módulos especializados para proporcionar análisis
    financiero integral, detección de desviaciones, comparativas y 
    generación automática de Business Reviews.
    """
    
    def __init__(self):
        """Inicializa el agente CDG con todos los módulos especializados"""
        self.start_time = datetime.now()
        
        # Inicializar herramientas especializadas
        self.kpi_calculator = KPICalculator()
        self.chart_generator = CDGDashboardGenerator()
        self.report_generator = BusinessReportGenerator()
        
        # Inicializar módulos de consultas
        self.gestor_queries = GestorQueries()
        self.comparative_queries = ComparativeQueries()
        self.deviation_queries = DeviationQueries()
        self.incentive_queries = IncentiveQueries()
        
        # Configuración y estado del agente
        self.config_manager = ConfigManager()
        self.conversation_history = []
        self.user_preferences = {}
        
        logger.info("🚀 CDG Agent inicializado exitosamente con todos los módulos")

    async def process_request(self, request: CDGRequest) -> CDGResponse:
        """
        Procesa una solicitud del usuario y orquesta la respuesta apropiada
        
        Args:
            request: Solicitud estructurada del usuario
            
        Returns:
            CDGResponse: Respuesta completa con análisis, gráficos y recomendaciones
        """
        start_time = datetime.now()
        
        try:
            # 1. Analizar la intención del usuario
            query_type, confidence = await self._classify_user_intent(request.user_message)
            logger.info(f"💭 Intención clasificada: {query_type.value} (confianza: {confidence:.2f})")
            
            # 2. Orquestar la respuesta según el tipo de consulta
            if query_type == QueryType.GESTOR_ANALYSIS:
                response_content = await self._handle_gestor_analysis(request)
            elif query_type == QueryType.COMPARATIVE_ANALYSIS:
                response_content = await self._handle_comparative_analysis(request)
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                response_content = await self._handle_deviation_analysis(request)
            elif query_type == QueryType.INCENTIVE_ANALYSIS:
                response_content = await self._handle_incentive_analysis(request)
            elif query_type == QueryType.BUSINESS_REVIEW:
                response_content = await self._handle_business_review(request)
            elif query_type == QueryType.EXECUTIVE_SUMMARY:
                response_content = await self._handle_executive_summary(request)
            else:
                response_content = await self._handle_general_chat(request)
            
            # 3. Generar gráficos si se solicitan
            charts = []
            if request.include_charts and 'kpi_data' in response_content:
                charts = await self._generate_charts(response_content, query_type)
            
            # 4. Generar recomendaciones si se solicitan
            recommendations = []
            if request.include_recommendations:
                recommendations = await self._generate_recommendations(response_content, query_type)
            
            # 5. Construir respuesta final
            execution_time = (datetime.now() - start_time).total_seconds()
            
            response = CDGResponse(
                response_type=query_type,
                content=response_content,
                charts=charts,
                recommendations=recommendations,
                metadata={
                    'user_id': request.user_id,
                    'gestor_id': request.gestor_id,
                    'periodo': request.periodo,
                    'modules_used': self._get_modules_used(query_type),
                    'data_sources': self._get_data_sources(query_type)
                },
                execution_time=execution_time,
                confidence_score=confidence,
                created_at=datetime.now()
            )
            
            # 6. Actualizar historial de conversación
            self._update_conversation_history(request, response)
            
            logger.info(f"✅ Solicitud procesada exitosamente en {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error procesando solicitud: {e}")
            return await self._create_error_response(request, str(e), start_time)

    async def _classify_user_intent(self, user_message: str) -> Tuple[QueryType, float]:
        """
        Clasifica la intención del usuario usando Azure OpenAI
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Tuple[QueryType, float]: Tipo de consulta y nivel de confianza
        """
        classification_prompt = f"""
        Analiza el siguiente mensaje de un usuario de Control de Gestión de Banca March y clasifica su intención:

        Mensaje: "{user_message}"

        Tipos de consulta disponibles:
        - gestor_analysis: Análisis específico de un gestor (performance, KPIs individuales)
        - comparative_analysis: Comparaciones entre gestores, centros o períodos
        - deviation_analysis: Análisis de desviaciones, alertas, anomalías
        - incentive_analysis: Análisis de incentivos, comisiones, bonus
        - business_review: Generación de Business Review completo
        - executive_summary: Resumen ejecutivo para directivos
        - general_chat: Conversación general o consultas no específicas

        Responde SOLO con el formato JSON:
        {{"type": "tipo_de_consulta", "confidence": 0.95}}
        """
        
        try:
            client = iniciar_agente_llm()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un clasificador experto de intenciones para el sistema CDG de Banca March."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content)
            query_type = QueryType(result['type'])
            confidence = float(result['confidence'])
            
            return query_type, confidence
            
        except Exception as e:
            logger.warning(f"Error en clasificación de intención: {e}")
            return QueryType.GENERAL_CHAT, 0.5

    async def _handle_gestor_analysis(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja análisis específico de gestores"""
        logger.info("🔍 Procesando análisis de gestor...")
        
        try:
            # Obtener datos del gestor
            if request.gestor_id:
                gestor_data = self.gestor_queries.get_gestor_performance(request.gestor_id, request.periodo)
            else:
                # Inferir gestor del mensaje del usuario
                gestor_data = await self._infer_gestor_from_message(request.user_message)
            
            if not gestor_data or gestor_data.row_count == 0:
                return {"error": "No se encontraron datos para el gestor especificado"}
            
            # Calcular KPIs usando kpi_calculator
            gestor_info = gestor_data.data[0]
            kpi_analysis = self.kpi_calculator.analyze_gestor_performance(gestor_info)
            
            # Obtener análisis adicional
            incentivos = self.incentive_queries.calculate_gestor_incentives(gestor_info.get('gestor_id'), request.periodo)
            comparativas = self.comparative_queries.ranking_gestores_por_margen(request.periodo)
            
            return {
                'gestor_data': gestor_info,
                'kpi_data': kpi_analysis,
                'incentivos': incentivos.data if incentivos else [],
                'comparativas': comparativas.data[:5] if comparativas else [],  # Top 5
                'analysis_type': 'gestor_performance'
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de gestor: {e}")
            return {"error": f"Error procesando análisis de gestor: {str(e)}"}

    async def _handle_comparative_analysis(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja análisis comparativos"""
        logger.info("📊 Procesando análisis comparativo...")
        
        try:
            # Análisis comparativo general
            ranking_gestores = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
            compare_centros = self.comparative_queries.compare_eficiencia_centro_enhanced(request.periodo)
            
            # Análisis de ROE comparativo
            roe_analysis = self.comparative_queries.compare_roe_gestores_enhanced(request.periodo)
            
            return {
                'ranking_gestores': ranking_gestores.data if ranking_gestores else [],
                'eficiencia_centros': compare_centros.data if compare_centros else [],
                'roe_analysis': roe_analysis.data if roe_analysis else [],
                'analysis_type': 'comparative_analysis',
                'periodo': request.periodo
            }
            
        except Exception as e:
            logger.error(f"Error en análisis comparativo: {e}")
            return {"error": f"Error procesando análisis comparativo: {str(e)}"}

    async def _handle_deviation_analysis(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja análisis de desviaciones"""
        logger.info("⚠️ Procesando análisis de desviaciones...")
        
        try:
            # Detectar desviaciones críticas
            desviaciones_precio = self.deviation_queries.detect_precio_desviaciones_criticas_enhanced(request.periodo, 15.0)
            anomalias_margen = self.deviation_queries.analyze_margen_anomalies_enhanced(request.periodo, 2.0)
            outliers_volumen = self.deviation_queries.identify_volumen_outliers_enhanced(request.periodo, 3.0)
            
            # Análisis de patrones temporales
            patrones_temporales = self.deviation_queries.detect_patron_temporal_anomalias(None, 6)
            
            return {
                'desviaciones_precio': desviaciones_precio.data if desviaciones_precio else [],
                'anomalias_margen': anomalias_margen.data if anomalias_margen else [],
                'outliers_volumen': outliers_volumen.data if outliers_volumen else [],
                'patrones_temporales': patrones_temporales.data if patrones_temporales else [],
                'analysis_type': 'deviation_analysis',
                'periodo': request.periodo
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de desviaciones: {e}")
            return {"error": f"Error procesando análisis de desviaciones: {str(e)}"}

    async def _handle_incentive_analysis(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja análisis de incentivos"""
        logger.info("💰 Procesando análisis de incentivos...")
        
        try:
            if request.gestor_id:
                # Análisis específico de un gestor
                incentivos_gestor = self.incentive_queries.calculate_gestor_incentives_enhanced(request.gestor_id, request.periodo)
                simulacion = self.incentive_queries.simulate_incentive_scenarios_enhanced(request.gestor_id, request.periodo)
                
                return {
                    'incentivos_gestor': incentivos_gestor.data if incentivos_gestor else [],
                    'simulacion_escenarios': simulacion.data if simulacion else [],
                    'analysis_type': 'incentive_analysis_individual',
                    'gestor_id': request.gestor_id
                }
            else:
                # Análisis general de incentivos
                ranking_incentivos = self.incentive_queries.ranking_incentivos_periodo_enhanced(request.periodo)
                impacto_desviaciones = self.incentive_queries.analyze_deviation_impact_on_incentives_enhanced(request.periodo)
                
                return {
                    'ranking_incentivos': ranking_incentivos.data if ranking_incentivos else [],
                    'impacto_desviaciones': impacto_desviaciones.data if impacto_desviaciones else [],
                    'analysis_type': 'incentive_analysis_general',
                    'periodo': request.periodo
                }
                
        except Exception as e:
            logger.error(f"Error en análisis de incentivos: {e}")
            return {"error": f"Error procesando análisis de incentivos: {str(e)}"}

    async def _handle_business_review(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja generación de Business Review completo"""
        logger.info("📋 Generando Business Review completo...")
        
        try:
            if not request.gestor_id:
                return {"error": "Se requiere gestor_id para generar Business Review"}
            
            # Obtener datos completos del gestor
            gestor_data = self.gestor_queries.get_gestor_performance(request.gestor_id, request.periodo)
            if not gestor_data or gestor_data.row_count == 0:
                return {"error": "No se encontraron datos para el gestor especificado"}
            
            gestor_info = gestor_data.data[0]
            
            # Calcular KPIs completos
            kpi_analysis = self.kpi_calculator.analyze_gestor_performance(gestor_info)
            
            # Obtener datos adicionales
            deviation_alerts = self.deviation_queries.detect_precio_desviaciones_criticas_enhanced(request.periodo, 15.0)
            comparative_data = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
            
            # Generar Business Review usando report_generator
            business_review = self.report_generator.generate_business_review(
                gestor_data=gestor_info,
                kpi_data=kpi_analysis,
                period=request.periodo,
                deviation_alerts=deviation_alerts.data if deviation_alerts else None,
                comparative_data=comparative_data.data if comparative_data else None
            )
            
            return {
                'business_review': business_review.to_dict(),
                'analysis_type': 'business_review_complete'
            }
            
        except Exception as e:
            logger.error(f"Error generando Business Review: {e}")
            return {"error": f"Error generando Business Review: {str(e)}"}

    async def _handle_executive_summary(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja generación de Executive Summary"""
        logger.info("📈 Generando Executive Summary...")
        
        try:
            # Datos consolidados para executive summary
            ranking_gestores = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
            desviaciones_criticas = self.deviation_queries.detect_precio_desviaciones_criticas_enhanced(request.periodo, 25.0)
            
            consolidated_data = {
                'num_gestores': len(ranking_gestores.data) if ranking_gestores else 0,
                'margen_promedio': sum(g.get('margen_neto', 0) for g in ranking_gestores.data) / len(ranking_gestores.data) if ranking_gestores and ranking_gestores.data else 0,
                'alertas_criticas': len(desviaciones_criticas.data) if desviaciones_criticas else 0,
                'periodo': request.periodo
            }
            
            # Generar executive summary
            executive_summary = self.report_generator.generate_executive_summary_report(
                consolidated_data, request.periodo
            )
            
            return {
                'executive_summary': executive_summary.to_dict(),
                'consolidated_data': consolidated_data,
                'analysis_type': 'executive_summary'
            }
            
        except Exception as e:
            logger.error(f"Error generando Executive Summary: {e}")
            return {"error": f"Error generando Executive Summary: {str(e)}"}

    async def _handle_general_chat(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja conversación general usando Azure OpenAI"""
        logger.info("💬 Procesando conversación general...")
        
        try:
            # Obtener contexto relevante basado en el mensaje
            context_data = await self._get_relevant_context(request.user_message)
            
            # Construir prompt contextualizado
            system_prompt = FINANCIAL_ANALYST_SYSTEM_PROMPT
            user_prompt = f"""
            Usuario pregunta: {request.user_message}
            
            Contexto disponible:
            {json.dumps(context_data, indent=2, ensure_ascii=False)}
            
            Proporciona una respuesta útil y contextualizada para el usuario de Control de Gestión de Banca March.
            """
            
            # Llamar a Azure OpenAI
            client = iniciar_agente_llm()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return {
                'response': response.choices[0].message.content,
                'context_used': context_data,
                'analysis_type': 'general_chat'
            }
            
        except Exception as e:
            logger.error(f"Error en conversación general: {e}")
            return {"error": f"Error procesando conversación: {str(e)}"}

    async def _generate_charts(self, content_data: Dict[str, Any], query_type: QueryType) -> List[Dict[str, Any]]:
        """Genera gráficos apropiados según el tipo de análisis"""
        charts = []
        
        try:
            if query_type == QueryType.GESTOR_ANALYSIS and 'kpi_data' in content_data:
                # Dashboard de gestor
                dashboard = self.chart_generator.generate_gestor_dashboard(
                    content_data.get('gestor_data', {}),
                    content_data['kpi_data'],
                    content_data.get('periodo')
                )
                charts.extend(dashboard.get('charts', []))
                
            elif query_type == QueryType.COMPARATIVE_ANALYSIS and 'ranking_gestores' in content_data:
                # Gráfico comparativo
                comparative_chart = self.chart_generator.generate_comparative_dashboard(
                    content_data['ranking_gestores'],
                    metric='margen_neto',
                    titulo='Ranking de Gestores por Margen Neto'
                )
                charts.append(comparative_chart)
                
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                # Gráficos de desviaciones si hay datos
                if 'desviaciones_precio' in content_data and content_data['desviaciones_precio']:
                    deviation_chart = self.chart_generator.generate_trend_dashboard(
                        content_data['desviaciones_precio'],
                        title='Evolución de Desviaciones de Precio'
                    )
                    charts.append(deviation_chart)
            
        except Exception as e:
            logger.warning(f"Error generando gráficos: {e}")
        
        return charts

    async def _generate_recommendations(self, content_data: Dict[str, Any], query_type: QueryType) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        try:
            if query_type == QueryType.GESTOR_ANALYSIS:
                kpi_data = content_data.get('kpi_data', {})
                margen = kpi_data.get('margen_neto', 0)
                roe = kpi_data.get('roe', 0)
                
                if margen < 10:
                    recommendations.append("Revisar estrategia de precios y estructura de costos para mejorar margen neto")
                if roe < 8:
                    recommendations.append("Optimizar rentabilidad mediante gestión más eficiente del capital")
                    
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                if content_data.get('desviaciones_precio'):
                    recommendations.append("Atender prioritariamente las desviaciones de precio identificadas")
                if content_data.get('anomalias_margen'):
                    recommendations.append("Investigar causas de las anomalías en márgenes detectadas")
                    
            elif query_type == QueryType.COMPARATIVE_ANALYSIS:
                recommendations.append("Analizar mejores prácticas de los gestores top performer")
                recommendations.append("Implementar plan de mejora para gestores con performance inferior")
            
            # Recomendación general si no hay específicas
            if not recommendations:
                recommendations.append("Continuar seguimiento de KPIs y mantener estrategia actual")
                
        except Exception as e:
            logger.warning(f"Error generando recomendaciones: {e}")
        
        return recommendations

    async def _get_relevant_context(self, user_message: str) -> Dict[str, Any]:
        """Obtiene contexto relevante para conversación general"""
        context = {}
        
        try:
            # Obtener datos recientes para contexto
            periodo_actual = datetime.now().strftime('%Y-%m')
            
            # Datos generales de performance
            ranking_general = self.comparative_queries.ranking_gestores_por_margen(periodo_actual)
            if ranking_general and ranking_general.data:
                context['top_performers'] = ranking_general.data[:3]
            
            # Alertas recientes
            alertas_recientes = self.deviation_queries.detect_precio_desviaciones_criticas(periodo_actual, 20.0)
            if alertas_recientes and alertas_recientes.data:
                context['alertas_activas'] = len(alertas_recientes.data)
                
        except Exception as e:
            logger.warning(f"Error obteniendo contexto: {e}")
        
        return context

    async def _infer_gestor_from_message(self, user_message: str) -> Any:
        """Infiere el gestor del mensaje del usuario"""
        try:
            # Buscar patrones comunes de nombres o IDs de gestores
            # Esto es una implementación básica, se puede mejorar con NLP
            gestores_data = self.gestor_queries.get_all_gestores()
            if gestores_data and gestores_data.data:
                for gestor in gestores_data.data:
                    if gestor.get('desc_gestor', '').lower() in user_message.lower():
                        return self.gestor_queries.get_gestor_performance(gestor.get('gestor_id'))
            
            # Si no se encuentra, devolver el primer gestor como ejemplo
            if gestores_data and gestores_data.data:
                primer_gestor = gestores_data.data[0]
                return self.gestor_queries.get_gestor_performance(primer_gestor.get('gestor_id'))
                
        except Exception as e:
            logger.warning(f"Error infiriendo gestor: {e}")
        
        return None

    def _get_modules_used(self, query_type: QueryType) -> List[str]:
        """Retorna los módulos utilizados para un tipo de consulta"""
        module_mapping = {
            QueryType.GESTOR_ANALYSIS: ['gestor_queries', 'kpi_calculator', 'incentive_queries'],
            QueryType.COMPARATIVE_ANALYSIS: ['comparative_queries', 'kpi_calculator', 'chart_generator'],
            QueryType.DEVIATION_ANALYSIS: ['deviation_queries', 'kpi_calculator'],
            QueryType.INCENTIVE_ANALYSIS: ['incentive_queries', 'kpi_calculator'],
            QueryType.BUSINESS_REVIEW: ['report_generator', 'chart_generator', 'kpi_calculator'],
            QueryType.EXECUTIVE_SUMMARY: ['report_generator', 'comparative_queries', 'deviation_queries'],
            QueryType.GENERAL_CHAT: ['azure_openai', 'prompts']
        }
        return module_mapping.get(query_type, [])

    def _get_data_sources(self, query_type: QueryType) -> List[str]:
        """Retorna las fuentes de datos utilizadas"""
        data_sources = ['BM_CONTABILIDAD_CDG.db']
        if query_type in [QueryType.BUSINESS_REVIEW, QueryType.EXECUTIVE_SUMMARY, QueryType.GENERAL_CHAT]:
            data_sources.append('Azure_OpenAI_GPT4')
        return data_sources

    def _update_conversation_history(self, request: CDGRequest, response: CDGResponse):
        """Actualiza el historial de conversación para aprendizaje continuo"""
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': request.user_message,
            'response_type': response.response_type.value,
            'confidence': response.confidence_score,
            'execution_time': response.execution_time,
            'user_id': request.user_id
        }
        
        self.conversation_history.append(conversation_entry)
        
        # Mantener solo los últimos 100 intercambios
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]

    async def _create_error_response(self, request: CDGRequest, error_message: str, start_time: datetime) -> CDGResponse:
        """Crea una respuesta de error estándar"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return CDGResponse(
            response_type=QueryType.GENERAL_CHAT,
            content={"error": error_message, "status": "error"},
            charts=[],
            recommendations=["Revisar la consulta y intentar nuevamente"],
            metadata={"error_occurred": True, "user_id": request.user_id},
            execution_time=execution_time,
            confidence_score=0.0,
            created_at=datetime.now()
        )

    def get_agent_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente"""
        uptime = datetime.now() - self.start_time
        
        return {
            'status': 'active',
            'uptime_seconds': uptime.total_seconds(),
            'conversation_count': len(self.conversation_history),
            'modules_loaded': [
                'kpi_calculator', 'chart_generator', 'report_generator',
                'gestor_queries', 'comparative_queries', 'deviation_queries', 'incentive_queries'
            ],
            'last_activity': self.conversation_history[-1]['timestamp'] if self.conversation_history else None
        }

    def reset_conversation_history(self):
        """Reinicia el historial de conversación"""
        self.conversation_history = []
        logger.info("🔄 Historial de conversación reiniciado")

# Función de conveniencia para crear instancia del agente
def create_cdg_agent() -> CDGAgent:
    """Crea y retorna una instancia del agente CDG"""
    return CDGAgent()

# Función asíncrona de conveniencia para procesamiento rápido
async def process_cdg_request(user_message: str, **kwargs) -> Dict[str, Any]:
    """
    Función de conveniencia para procesar una solicitud rápida
    
    Args:
        user_message: Mensaje del usuario
        **kwargs: Parámetros adicionales (gestor_id, periodo, etc.)
        
    Returns:
        Dict con la respuesta procesada
    """
    agent = create_cdg_agent()
    
    request = CDGRequest(
        user_message=user_message,
        gestor_id=kwargs.get('gestor_id'),
        periodo=kwargs.get('periodo'),
        user_id=kwargs.get('user_id'),
        include_charts=kwargs.get('include_charts', True),
        include_recommendations=kwargs.get('include_recommendations', True)
    )
    
    response = await agent.process_request(request)
    return response.to_dict()

if __name__ == "__main__":
    # Demo y tests básicos del agente CDG
    import asyncio
    
    async def demo_cdg_agent():
        """Demostración del agente CDG"""
        print("🚀 Iniciando demo del CDG Agent...")
        
        agent = create_cdg_agent()
        
        # Test casos de uso típicos
        test_cases = [
            {
                "message": "¿Cómo está el performance del gestor Juan Pérez en octubre?",
                "gestor_id": "1",
                "periodo": "2025-10"
            },
            {
                "message": "Muéstrame una comparativa de gestores por margen neto",
                "periodo": "2025-10"
            },
            {
                "message": "¿Hay alguna desviación crítica en los precios este mes?",
                "periodo": "2025-10"
            },
            {
                "message": "Genera un Business Review completo para el gestor ID 1",
                "gestor_id": "1",
                "periodo": "2025-10"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i} ---")
            print(f"📝 Mensaje: {test_case['message']}")
            
            request = CDGRequest(
                user_message=test_case["message"],
                gestor_id=test_case.get("gestor_id"),
                periodo=test_case.get("periodo"),
                user_id="demo_user"
            )
            
            try:
                response = await agent.process_request(request)
                print(f"✅ Tipo: {response.response_type.value}")
                print(f"⏱️ Tiempo: {response.execution_time:.2f}s")
                print(f"🎯 Confianza: {response.confidence_score:.2f}")
                print(f"📊 Gráficos: {len(response.charts)}")
                print(f"💡 Recomendaciones: {len(response.recommendations)}")
                
                if response.content.get('error'):
                    print(f"❌ Error: {response.content['error']}")
                    
            except Exception as e:
                print(f"❌ Error en test case {i}: {e}")
        
        # Mostrar estado del agente
        print(f"\n📊 Estado del agente:")
        status = agent.get_agent_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\n🎯 Demo completado exitosamente!")

    # Ejecutar demo
    asyncio.run(demo_cdg_agent())
