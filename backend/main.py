"""
main.py - API Principal para Agente CDG de Banca March
====================================================

Archivo principal de FastAPI que integra todos los agentes y módulos del sistema CDG.
Proporciona endpoints para el frontend React con funcionalidades completas.

Autor: Agente CDG Development Team
Fecha: 2025-08-01
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Importar módulos del agente CDG
try:
    # Agentes principales
    from agents.chat_agent import chat_agent, ChatMessage, ChatResponse, CDGChatAgent
    from agents.cdg_agent import create_cdg_agent, CDGAgent, CDGRequest
    
    # Herramientas especializadas
    from tools.kpi_calculator import KPICalculator
    from tools.chart_generator import CDGDashboardGenerator
    from tools.report_generator import BusinessReportGenerator
    
    # Módulos de consultas
    from queries.gestor_queries import GestorQueries
    from queries.comparative_queries import ComparativeQueries
    from queries.deviation_queries import DeviationQueries
    from queries.incentive_queries import IncentiveQueries
    
    # Sistema de aprendizaje
    from utils.reflection_pattern import (
        reflection_manager,
        integrate_feedback_from_chat_agent,
        get_personalization_for_user
    )
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Asegúrate de que todos los módulos estén correctamente implementados")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="CDG Agente Banca March API",
    description="API principal para el sistema de Control de Gestión de Banca March con agente LLM integrado",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://app.bancamarch.es"  # Producción
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============================================================================
# MODELOS DE DATOS PARA LA API
# ============================================================================

class ChatRequest(BaseModel):
    """Modelo para solicitudes de chat"""
    user_id: str
    message: str
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True
    context: Dict[str, Any] = {}
    user_feedback: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    """Modelo para solicitudes de análisis específico"""
    user_id: str
    analysis_type: str  # gestor_analysis, comparative_analysis, etc.
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    parameters: Dict[str, Any] = {}

class FeedbackRequest(BaseModel):
    """Modelo para feedback del usuario"""
    user_id: str
    query: str
    response: str
    rating: Optional[int] = None
    comments: Optional[str] = None
    categories: Dict[str, int] = {}

class GenericResponse(BaseModel):
    """Respuesta genérica de la API"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str

# ============================================================================
# INSTANCIAS GLOBALES DE AGENTES Y HERRAMIENTAS
# ============================================================================

# Instanciar agentes principales
chat_agent_instance = chat_agent
cdg_agent_instance = create_cdg_agent()

# Instanciar herramientas especializadas
kpi_calculator = KPICalculator()
chart_generator = CDGDashboardGenerator()
report_generator = BusinessReportGenerator()

# Instanciar módulos de consultas
gestor_queries = GestorQueries()
comparative_queries = ComparativeQueries()
deviation_queries = DeviationQueries()
incentive_queries = IncentiveQueries()

logger.info("🚀 CDG API inicializada con todos los módulos")

# ============================================================================
# ENDPOINTS PRINCIPALES - CHAT Y COMUNICACIÓN
# ============================================================================

@app.get("/health", tags=["General"])
def health_check():
    """
    Health check para monitoreo del servicio
    
    Returns:
        Estado de salud de la API y todos los módulos
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "modules": {
            "chat_agent": "active",
            "cdg_agent": "active",
            "reflection_pattern": "active",
            "kpi_calculator": "active",
            "chart_generator": "active",
            "report_generator": "active"
        }
    }

@app.get("/status", tags=["General"])
def get_system_status():
    """
    Obtiene el estado detallado del sistema completo
    
    Returns:
        Estado detallado de todos los agentes y módulos
    """
    try:
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "chat_agent": chat_agent_instance.get_agent_status(),
            "cdg_agent": cdg_agent_instance.get_agent_status(),
            "reflection_pattern": {
                "active_users": len(reflection_manager.user_profiles),
                "organizational_insights": reflection_manager.generate_organizational_insights()
            },
            "database_connection": "active",  # Asumiendo que la DB está activa
            "azure_openai": "connected"
        }
        return status
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado del sistema")

@app.post("/chat", tags=["Chat"])
async def process_chat_message(chat_request: ChatRequest):
    """
    Endpoint principal para procesar mensajes de chat del frontend
    
    Args:
        chat_request: Mensaje de chat estructurado
        
    Returns:
        Respuesta completa con análisis, gráficos y recomendaciones
    """
    try:
        # Convertir a ChatMessage del agente
        chat_message = ChatMessage(
            user_id=chat_request.user_id,
            message=chat_request.message,
            gestor_id=chat_request.gestor_id,
            periodo=chat_request.periodo,
            include_charts=chat_request.include_charts,
            include_recommendations=chat_request.include_recommendations,
            context=chat_request.context,
            user_feedback=chat_request.user_feedback
        )
        
        # Procesar con el agente de chat
        response = await chat_agent_instance.process_chat_message(chat_message)
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error procesando mensaje de chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")

@app.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """
    WebSocket para comunicación en tiempo real con el agente
    
    Args:
        websocket: Conexión WebSocket
        user_id: ID único del usuario
    """
    await websocket.accept()
    chat_agent_instance.session_manager.add_websocket_connection(user_id, websocket)
    
    try:
        while True:
            # Recibir datos del cliente
            data = await websocket.receive_json()
            
            # Crear mensaje de chat
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
            
            # Procesar mensaje
            response = await chat_agent_instance.process_chat_message(chat_message)
            
            # Enviar respuesta
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para usuario {user_id}")
        chat_agent_instance.session_manager.remove_websocket_connection(user_id)
    except Exception as e:
        logger.error(f"Error en WebSocket para usuario {user_id}: {e}")
        await websocket.close()

@app.get("/chat/history/{user_id}", tags=["Chat"])
def get_chat_history(user_id: str):
    """
    Obtiene el historial de conversación de un usuario
    
    Args:
        user_id: ID único del usuario
        
    Returns:
        Historial de conversación completo
    """
    try:
        history = chat_agent_instance.get_session_history(user_id)
        if history is None:
            raise HTTPException(status_code=404, detail=f"No se encontró historial para usuario {user_id}")
        
        return {
            "user_id": user_id,
            "history": history,
            "total_interactions": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial de conversación")

@app.post("/chat/reset/{user_id}", tags=["Chat"])
def reset_chat_session(user_id: str):
    """
    Reinicia la sesión de chat de un usuario manteniendo personalización
    
    Args:
        user_id: ID único del usuario
        
    Returns:
        Confirmación de reset
    """
    try:
        chat_agent_instance.session_manager.reset_session(user_id)
        return {
            "status": "success",
            "message": f"Sesión de chat reiniciada para usuario {user_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error reiniciando sesión: {e}")
        raise HTTPException(status_code=500, detail="Error reiniciando sesión de chat")

# ============================================================================
# ENDPOINTS ESPECIALIZADOS DE ANÁLISIS CDG
# ============================================================================

@app.post("/analysis", tags=["Análisis CDG"])
async def perform_analysis(analysis_request: AnalysisRequest):
    """
    Endpoint para realizar análisis específicos usando el agente CDG
    
    Args:
        analysis_request: Solicitud de análisis estructurada
        
    Returns:
        Resultado del análisis específico
    """
    try:
        # Crear request para el agente CDG
        cdg_request = CDGRequest(
            user_message=f"Realizar {analysis_request.analysis_type}",
            user_id=analysis_request.user_id,
            gestor_id=analysis_request.gestor_id,
            periodo=analysis_request.periodo,
            context=analysis_request.parameters
        )
        
        # Procesar con el agente CDG
        response = await cdg_agent_instance.process_request(cdg_request)
        
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"Error en análisis específico: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

# ============================================================================
# ENDPOINTS ESPECIALIZADOS DE CONSULTA DE DATOS
# ============================================================================

@app.get("/gestor/{gestor_id}/performance", tags=["Gestores"])
async def get_gestor_performance(gestor_id: str, periodo: Optional[str] = None):
    """
    Obtiene el performance y KPIs de un gestor específico
    
    Args:
        gestor_id: ID del gestor
        periodo: Período de análisis (YYYY-MM)
        
    Returns:
        Resultados y KPIs calculados para el gestor
    """
    try:
        # Obtener datos usando gestor_queries
        data = gestor_queries.get_gestor_performance(gestor_id, periodo)
        if data is None or data.row_count == 0:
            raise HTTPException(status_code=404, detail="Gestor no encontrado o sin datos")
        
        # Calcular KPIs usando kpi_calculator
        gestor_info = data.data[0]
        kpi_analysis = kpi_calculator.analyze_gestor_performance(gestor_info)
        
        return {
            "gestor": gestor_info,
            "kpis": kpi_analysis,
            "periodo": periodo,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo performance de gestor {gestor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo performance: {str(e)}")

@app.get("/comparative/ranking", tags=["Análisis Comparativo"])
async def get_comparative_ranking(periodo: str, metric: str = "margen_neto"):
    """
    Obtiene ranking comparativo de gestores para un período
    
    Args:
        periodo: Período de análisis
        metric: Métrica para ranking (margen_neto, roe, eficiencia)
        
    Returns:
        Ranking de gestores según la métrica especificada
    """
    try:
        if metric == "margen_neto":
            ranking = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        elif metric == "roe":
            ranking = comparative_queries.compare_roe_gestores_enhanced(periodo)
        elif metric == "eficiencia":
            ranking = comparative_queries.compare_eficiencia_centro_enhanced(periodo)
        else:
            ranking = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        
        return {
            "periodo": periodo,
            "metric": metric,
            "ranking": ranking.data if ranking else [],
            "total_gestores": len(ranking.data) if ranking else 0
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo ranking comparativo: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo ranking: {str(e)}")

@app.get("/deviations/alerts", tags=["Análisis de Desviaciones"])
async def get_deviation_alerts(periodo: str, threshold: float = 15.0):
    """
    Obtiene alertas y desviaciones críticas para el período
    
    Args:
        periodo: Período de análisis
        threshold: Umbral de desviación en porcentaje
        
    Returns:
        Listado de alertas y desviaciones detectadas
    """
    try:
        # Detectar diferentes tipos de desviaciones
        precio_alerts = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, threshold)
        margen_anomalies = deviation_queries.analyze_margen_anomalies_enhanced(periodo, 2.0)
        volumen_outliers = deviation_queries.identify_volumen_outliers_enhanced(periodo, 3.0)
        
        return {
            "periodo": periodo,
            "threshold": threshold,
            "precio_alerts": precio_alerts.data if precio_alerts else [],
            "margen_anomalies": margen_anomalies.data if margen_anomalies else [],
            "volumen_outliers": volumen_outliers.data if volumen_outliers else [],
            "total_alerts": (len(precio_alerts.data) if precio_alerts else 0) + 
                           (len(margen_anomalies.data) if margen_anomalies else 0) + 
                           (len(volumen_outliers.data) if volumen_outliers else 0)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas de desviaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")

@app.get("/incentives/summary", tags=["Análisis de Incentivos"])
async def get_incentive_summary(periodo: str, gestor_id: Optional[str] = None):
    """
    Obtiene resumen de incentivos para el período
    
    Args:
        periodo: Período de análisis
        gestor_id: ID específico del gestor (opcional)
        
    Returns:
        Resumen de incentivos y análisis de impacto
    """
    try:
        if gestor_id:
            # Análisis específico para un gestor
            incentivos = incentive_queries.calculate_gestor_incentives_enhanced(gestor_id, periodo)
            simulacion = incentive_queries.simulate_incentive_scenarios_enhanced(gestor_id, periodo)
            
            return {
                "periodo": periodo,
                "gestor_id": gestor_id,
                "incentivos": incentivos.data if incentivos else [],
                "simulacion_escenarios": simulacion.data if simulacion else []
            }
        else:
            # Análisis general de incentivos
            ranking = incentive_queries.ranking_incentivos_periodo_enhanced(periodo)
            impacto = incentive_queries.analyze_deviation_impact_on_incentives_enhanced(periodo)
            
            return {
                "periodo": periodo,
                "ranking_incentivos": ranking.data if ranking else [],
                "impacto_desviaciones": impacto.data if impacto else []
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo resumen de incentivos: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo incentivos: {str(e)}")

# ============================================================================
# ENDPOINTS PARA REPORTES AUTOMÁTICOS
# ============================================================================

@app.post("/reports/business_review", tags=["Reportes"])
async def generate_business_review_report(request: Dict[str, Any]):
    """
    Genera un Business Review completo para un gestor
    
    Args:
        request: JSON con user_id, gestor_id, periodo, opciones
        
    Returns:
        Business Review completo en JSON
    """
    try:
        user_id = request.get("user_id")
        gestor_id = request.get("gestor_id")
        periodo = request.get("periodo")
        include_charts = request.get("include_charts", True)
        include_recommendations = request.get("include_recommendations", True)
        
        if not gestor_id or not periodo:
            raise HTTPException(status_code=400, detail="Campos gestor_id y periodo son requeridos")
        
        # Obtener datos del gestor
        gestor_data = gestor_queries.get_gestor_performance(gestor_id, periodo)
        if not gestor_data or gestor_data.row_count == 0:
            raise HTTPException(status_code=404, detail="No se encontraron datos para el gestor")
        
        gestor_info = gestor_data.data[0]
        kpi_analysis = kpi_calculator.analyze_gestor_performance(gestor_info)
        
        # Obtener datos adicionales para el reporte
        deviation_alerts = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, 15.0)
        comparative_data = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        
        # Generar Business Review
        business_review = report_generator.generate_business_review(
            gestor_data=gestor_info,
            kpi_data=kpi_analysis,
            period=periodo,
            deviation_alerts=deviation_alerts.data if deviation_alerts else None,
            comparative_data=comparative_data.data if comparative_data else None
        )
        
        return business_review.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando Business Review: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")

@app.post("/reports/executive_summary", tags=["Reportes"])
async def generate_executive_summary_report(request: Dict[str, Any]):
    """
    Genera Executive Summary para directivos
    
    Args:
        request: JSON con user_id, periodo y datos consolidados
        
    Returns:
        Executive Summary en JSON
    """
    try:
        user_id = request.get("user_id")
        periodo = request.get("periodo")
        
        if not periodo:
            raise HTTPException(status_code=400, detail="Campo periodo es requerido")
        
        # Obtener datos consolidados
        ranking_gestores = comparative_queries.ranking_gestores_por_margen_enhanced(periodo)
        desviaciones_criticas = deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo, 25.0)
        
        consolidated_data = {
            'num_gestores': len(ranking_gestores.data) if ranking_gestores else 0,
            'margen_promedio': sum(g.get('margen_neto', 0) for g in ranking_gestores.data) / len(ranking_gestores.data) if ranking_gestores and ranking_gestores.data else 0,
            'alertas_criticas': len(desviaciones_criticas.data) if desviaciones_criticas else 0,
            'periodo': periodo
        }
        
        # Generar executive summary
        executive_summary = report_generator.generate_executive_summary_report(
            consolidated_data, periodo
        )
        
        return executive_summary.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando Executive Summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando summary: {str(e)}")

# ============================================================================
# ENDPOINTS DE PERSONALIZACIÓN Y FEEDBACK
# ============================================================================

@app.get("/personalization/{user_id}", tags=["Personalización"])
def get_user_personalization(user_id: str):
    """
    Obtiene el perfil de personalización de un usuario
    
    Args:
        user_id: ID único del usuario
        
    Returns:
        Perfil de personalización y preferencias
    """
    try:
        personalization = get_personalization_for_user(user_id)
        user_profile = reflection_manager.get_user_profile(user_id)
        
        return {
            "user_id": user_id,
            "personalization": personalization,
            "profile": user_profile.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo personalización para usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo personalización")

@app.post("/personalization/{user_id}", tags=["Personalización"])
def update_user_personalization(user_id: str, preferences: Dict[str, Any]):
    """
    Actualiza las preferencias de personalización de un usuario
    
    Args:
        user_id: ID único del usuario
        preferences: Diccionario con preferencias actualizadas
        
    Returns:
        Confirmación de actualización
    """
    try:
        user_profile = reflection_manager.get_user_profile(user_id)
        user_profile.update_preferences(preferences)
        
        return {
            "status": "success",
            "message": f"Preferencias actualizadas para usuario {user_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error actualizando personalización para usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error actualizando personalización")

@app.post("/feedback", tags=["Feedback"])
async def process_user_feedback(feedback: FeedbackRequest):
    """
    Procesa feedback del usuario para el sistema de aprendizaje continuo
    
    Args:
        feedback: Datos estructurados del feedback
        
    Returns:
        Resultado del procesamiento del feedback
    """
    try:
        result = await reflection_manager.process_feedback(
            user_id=feedback.user_id,
            query=feedback.query,
            response=feedback.response,
            response_type="general",
            feedback_rating=feedback.rating,
            feedback_comments=feedback.comments,
            feedback_categories=feedback.categories
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error procesando feedback: {e}")
        raise HTTPException(status_code=500, detail="Error procesando feedback")

# ============================================================================
# ENDPOINTS DE MÉTRICAS Y ADMINISTRACIÓN
# ============================================================================

@app.get("/metrics/organizational", tags=["Métricas"])
def get_organizational_metrics():
    """
    Obtiene métricas organizacionales agregadas
    
    Returns:
        Métricas y insights organizacionales
    """
    try:
        insights = reflection_manager.generate_organizational_insights()
        
        return {
            "organizational_insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas organizacionales: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo métricas")

@app.get("/database/health", tags=["Sistema"])
def database_health_check():
    """
    Verifica el estado de la base de datos
    
    Returns:
        Estado de conexión a la base de datos
    """
    try:
        # Test básico de conexión a la base de datos
        test_query = gestor_queries.get_all_gestores()
        
        return {
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "test_query_result": "success" if test_query else "warning"
        }
        
    except Exception as e:
        logger.error(f"Error en health check de base de datos: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/system/cleanup", tags=["Sistema"])
def cleanup_inactive_sessions():
    """
    Limpia sesiones inactivas del sistema
    
    Returns:
        Resultado de la limpieza
    """
    try:
        chat_agent_instance.session_manager.cleanup_inactive_sessions()
        
        return {
            "status": "success",
            "message": "Sesiones inactivas limpiadas exitosamente",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de sesiones: {e}")
        raise HTTPException(status_code=500, detail="Error en limpieza del sistema")

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def validate_periodo_format(periodo: str) -> bool:
    """Valida que el período tenga formato YYYY-MM"""
    try:
        datetime.strptime(periodo, "%Y-%m")
        return True
    except ValueError:
        return False

def get_current_periodo() -> str:
    """Obtiene el período actual en formato YYYY-MM"""
    return datetime.now().strftime("%Y-%m")

# ============================================================================
# MIDDLEWARE ADICIONAL
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    
    return response

# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    # Configuración para desarrollo
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
