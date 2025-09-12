"""
CDG Agent - Agente Principal de Control de Gestión - Banca March
==============================================================

🆕 INTEGRADO CON CHART_GENERATOR.PY Y BASIC_QUERIES.PY - VERSIÓN 4.0

Agente coordinador que orquesta todos los módulos del sistema CDG:
- Queries especializadas (gestor, comparative, deviation, incentive, period)
- Tools avanzados (kpi_calculator, chart_generator, report_generator)
- 🚀 NUEVO: Integración completa con basic_queries.py
- 🚀 NUEVO: QueryIntegratedChartGenerator
- 🚀 NUEVO: Pivoteo conversacional de gráficos dinámico
- Prompts contextualizados para análisis bancario
- Integración con Azure OpenAI para respuestas inteligentes
- QueryParser mejorado para entidades múltiples

Autor: Agente CDG Development Team
Fecha: 2025-09-01
Versión: 4.0 Enhanced con Basic Queries integrado
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# ✅ PATH RESOLUTION DEFINITIVO
import sys
import os
from pathlib import Path
import importlib.util
import importlib

# ✅ CORRECCIÓN CRÍTICA: Import de config settings para deployment dinámico
from backend.config import settings

# Configurar path
current_file = Path(__file__).resolve()
agents_dir = current_file.parent          
src_dir = agents_dir.parent               
backend_dir = src_dir.parent              

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

print("🔍 DEBUG CDG AGENT V4.0 - Implementando integración completa con Chart Generator y Basic Queries...")

# ✅ FUNCIÓN DE LIMPIEZA JSON CRÍTICA
def clean_llm_json_response(raw_response: str) -> str:
    """Elimina texto decorativo de la respuesta JSON de Azure OpenAI"""
    match = re.search(r'\{.*\}', raw_response, flags=re.DOTALL)
    if match:
        return match.group(0).strip()
    return raw_response.strip()

try:
    # ✅ INTEGRACIÓN COMPLETA: Cargar todos los módulos tools con correcciones
    
    # 1. 🚀 NUEVA INTEGRACIÓN: Basic Queries
    print("🔧 DEBUG: Cargando basic_queries...")
    from queries.basic_queries import basic_queries
    print("✅ DEBUG: Basic Queries cargado exitosamente")
    
    # 2. 🚀 NUEVA INTEGRACIÓN: Chart Generator con QueryIntegratedChartGenerator
    print("🔧 DEBUG: Cargando chart_generator con integración query...")
    chart_gen_path = src_dir / 'tools' / 'chart_generator.py'
    if not chart_gen_path.exists():
        raise FileNotFoundError(f"No se encuentra chart_generator.py en {chart_gen_path}")

    spec = importlib.util.spec_from_file_location("chart_generator", chart_gen_path)
    chart_gen_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chart_gen_module)
    sys.modules['chart_generator'] = chart_gen_module
    sys.modules['tools.chart_generator'] = chart_gen_module

    # 🚀 IMPORTAR FUNCIONES NUEVAS DEL CHART GENERATOR CON PROMPT INTEGRADO
    QueryIntegratedChartGenerator = chart_gen_module.QueryIntegratedChartGenerator
    create_chart_from_query_data = chart_gen_module.create_chart_from_query_data
    pivot_chart_with_query_integration = chart_gen_module.pivot_chart_with_query_integration

    # ✅ NUEVO: Importar función para cambios de gráficos con prompt del sistema
    handle_chart_change_request = chart_gen_module.handle_chart_change_request

    
    # Mantener compatibilidad con funciones existentes
    CDGDashboardGenerator = chart_gen_module.CDGDashboardGenerator if hasattr(chart_gen_module, 'CDGDashboardGenerator') else QueryIntegratedChartGenerator
    validate_chart_generator = chart_gen_module.validate_chart_generator if hasattr(chart_gen_module, 'validate_chart_generator') else lambda: {'status': 'OK'}
    
    print("✅ DEBUG: Chart Generator integrado con funciones de query")
    
    # 3. ✅ CORRECCIÓN CRÍTICA: FinancialKPICalculator en lugar de KPICalculator
    print("🔧 DEBUG: Cargando FinancialKPICalculator...")
    kpi_calc_path = src_dir / 'tools' / 'kpi_calculator.py'
    if not kpi_calc_path.exists():
        raise FileNotFoundError(f"No se encuentra kpi_calculator.py en {kpi_calc_path}")
    
    spec = importlib.util.spec_from_file_location("kpi_calculator", kpi_calc_path)
    kpi_calc_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kpi_calc_module)
    sys.modules['kpi_calculator'] = kpi_calc_module
    sys.modules['tools.kpi_calculator'] = kpi_calc_module
    
    # ✅ USAR FinancialKPICalculator CORRECTO
    FinancialKPICalculator = kpi_calc_module.FinancialKPICalculator
    print("✅ DEBUG: FinancialKPICalculator cargado y registrado")
    
    # 4. SQL Guard (funcionando)
    print("🔧 DEBUG: Cargando sql_guard...")
    sql_guard_path = src_dir / 'tools' / 'sql_guard.py'
    if not sql_guard_path.exists():
        raise FileNotFoundError(f"No se encuentra sql_guard.py en {sql_guard_path}")
    
    spec = importlib.util.spec_from_file_location("sql_guard", sql_guard_path)
    sql_guard_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sql_guard_module)
    sys.modules['sql_guard'] = sql_guard_module
    sys.modules['tools.sql_guard'] = sql_guard_module
    
    is_query_safe = sql_guard_module.is_query_safe
    print("✅ DEBUG: SQL Guard cargado y registrado")
    
    # 5. ✅ CORRECCIÓN CRÍTICA: BusinessReportGenerator compatible CORREGIDO
    print("🔧 DEBUG: Cargando BusinessReportGenerator...")
    try:
        # ruta relativa según tu layout (ajusta si usas package tools.*)
        from tools.report_generator import BusinessReportGenerator  # preferente
        print("✅ DEBUG: BusinessReportGenerator importado (versión completa)")
    except Exception as e:
        print(f"⚠️ DEBUG: No se pudo importar BusinessReportGenerator real ({e}). Usando versión compatible mínima.")
    
    class BusinessReportGenerator:
        """Versión compatible mínima (fallback)"""
        def __init__(self):
            print("✅ DEBUG: BusinessReportGenerator (fallback) inicializado")

        def generate_business_review(self, gestor_data=None, kpi_data=None, period=None, 
                                     deviation_alerts=None, comparative_data=None):
            data = {
                'report_id': f'br_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'gestor': (gestor_data or {}).get('desc_gestor', 'N/A'),
                'periodo': period or datetime.now().strftime('%Y-%m'),
                'kpis': kpi_data or {},
                'alertas': len(deviation_alerts) if deviation_alerts else 0,
                'comparativas': len(comparative_data) if comparative_data else 0,
                'generated_at': datetime.now().isoformat(),
                'status': 'generated'
            }
            class BR: 
                def __init__(self, d): self._d=d
                def to_dict(self): return self._d
            return BR(data)

        def generate_executive_summary_report(self, consolidated_data=None, periodo=None):
            data = {
                'summary_id': f'es_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'periodo': periodo or datetime.now().strftime('%Y-%m'),
                'data': consolidated_data or {},
                'generated_at': datetime.now().isoformat(),
                'status': 'generated'
            }
            class ES:
                def __init__(self, d): self._d=d
                def to_dict(self): return self._d
            return ES(data)
    
    print("✅ DEBUG: BusinessReportGenerator compatible creado y registrado")
    
    # 6. Verificar que chart_generator funciona
    print("🔧 DEBUG: Validando Chart Generator...")
    validation = validate_chart_generator()
    if validation.get('status') == 'OK':
        print("✅ DEBUG: Chart Generator validado exitosamente")
    else:
        raise ImportError(f"Chart Generator validation failed: {validation}")
    
    # 7. ✅ CARGAR QUERIES CON INTEGRACIÓN COMPLETA
    print("🔧 DEBUG: Cargando queries enhanced...")
    from queries.gestor_queries import GestorQueries
    from queries.comparative_queries import ComparativeQueries
    from queries.deviation_queries import DeviationQueries
    from queries.incentive_queries import IncentiveQueries
    
    # ✅ INTEGRAR PERIOD_QUERIES ACTUALIZADA
    print("🔧 DEBUG: Cargando period_queries enhanced...")
    try:
        from queries.period_queries import PeriodQueries
        PERIOD_QUERIES_ENHANCED = True
        print("✅ DEBUG: PeriodQueries enhanced cargado")
    except ImportError:
        print("⚠️ DEBUG: PeriodQueries enhanced no disponible, usando versión básica")
        # Crear versión compatible si no existe la enhanced
        class PeriodQueries:
            def get_available_periods_enhanced(self):
                return type('QueryResult', (), {
                    'data': [{'periodo': '2025-10'}, {'periodo': '2025-09'}],
                    'row_count': 2
                })()
            
            def get_latest_period_enhanced(self):
                return type('QueryResult', (), {
                    'data': [{'periodo': '2025-10'}],
                    'row_count': 1
                })()
        PERIOD_QUERIES_ENHANCED = False
    
    print("✅ DEBUG: Queries cargadas exitosamente")
    
    # 8. 🆕 NUEVO: Cargar QueryParser mejorado
    print("🔧 DEBUG: Cargando QueryParser mejorado...")
    try:
        from tools.query_parser import QueryParser, QueryIntent
        QUERY_PARSER_AVAILABLE = True
        print("✅ DEBUG: QueryParser mejorado cargado")
    except ImportError:
        print("⚠️ DEBUG: QueryParser no disponible, usando clasificación básica")
        class QueryParser:
            def parse_query(self, message, gestor_id=None, periodo=None):
                return {
                    'intent': type('QueryIntent', (), {'value': 'performance_analysis'})(),
                    'entities': {},
                    'filters': {'gestor_id': gestor_id, 'periodo': periodo},
                    'complexity': 'low',
                    'requires_ranking': False,
                    'requires_comparison': False,
                    'original_message': message
                }
        QUERY_PARSER_AVAILABLE = False
    
    # 9. Sistema de prompts y configuración
    print("🔧 DEBUG: Cargando prompts y utils...")
    from prompts.system_prompts import (
        FINANCIAL_ANALYST_SYSTEM_PROMPT,
        FINANCIAL_REPORT_SYSTEM_PROMPT,
        COMPARATIVE_ANALYSIS_SYSTEM_PROMPT,
        DEVIATION_ANALYSIS_SYSTEM_PROMPT
    )
    from utils.initial_agent import iniciar_agente_llm
    from utils.dynamic_config import DynamicBusinessConfig as ConfigManager
    print("✅ DEBUG: Prompts y utils cargados exitosamente")
    
    # ✅ IMPORTS EXITOSOS - MODO PRODUCTION ACTIVADO
    IMPORTS_SUCCESSFUL = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CDG Agent V4.0: Todos los módulos cargados con integración completa - MODO PRODUCTION")
    print("✅ DEBUG: IMPORTS_SUCCESSFUL establecido a True - MODO PRODUCTION ACTIVADO")
    
except Exception as e:
    print(f"❌ DEBUG: Error con integración completa: {e}")
    print(f"📍 DEBUG: Tipo de error: {type(e).__name__}")
    print(f"📋 DEBUG: Stack trace: {str(e)}")
    
    # Sistema de fallback MOCK completo
    class basic_queries:
        @staticmethod
        def get_resumen_general():
            return {
                'total_gestores': 30,
                'total_clientes': 85,
                'total_contratos': 216,
                'total_productos': 3,
                'total_centros': 5
            }
        
        @staticmethod
        def count_contratos_by_gestor():
            return [
                {'DESC_GESTOR': 'Mock Gestor 1', 'num_contratos': 10},
                {'DESC_GESTOR': 'Mock Gestor 2', 'num_contratos': 8}
            ]
        
        @staticmethod
        def count_clientes_by_gestor():
            return [
                {'DESC_GESTOR': 'Mock Gestor 1', 'num_clientes': 5},
                {'DESC_GESTOR': 'Mock Gestor 2', 'num_clientes': 4}
            ]
        
        @staticmethod
        def get_all_centros():
            return [
                {'CENTRO_ID': 1, 'DESC_CENTRO': 'MADRID-OFICINA PRINCIPAL'},
                {'CENTRO_ID': 2, 'DESC_CENTRO': 'PALMA-SANT MIQUEL'}
            ]
        
        @staticmethod
        def get_all_gestores():
            return [
                {'GESTOR_ID': 1, 'DESC_GESTOR': 'Mock Gestor 1'},
                {'GESTOR_ID': 2, 'DESC_GESTOR': 'Mock Gestor 2'}
            ]
        
        def __getattr__(self, name):
            return lambda *args, **kwargs: []
    
    class FinancialKPICalculator:
        def __init__(self): pass
        def calculate_kpis_from_data(self, data): 
            return {
                'resumen_performance': {'margen_neto_pct': 12.5, 'roe_pct': 8.3},
                'kpis_principales': {'eficiencia': 75.2}
            }
    
    class QueryIntegratedChartGenerator:
        def __init__(self): pass
        def generate_chart_from_data(self, *args, **kwargs): 
            return {'id': 'mock_chart', 'title': 'Gráfico Mock'}
        def interpret_chart_change(self, *args, **kwargs):
            return {'status': 'success', 'message': 'Cambio interpretado (mock)'}
    
    class CDGDashboardGenerator:
        def __init__(self): pass
        def generate_gestor_dashboard(self, *args, **kwargs): 
            return {'charts': []}
        def generate_comparative_dashboard(self, *args, **kwargs): 
            return {'id': 'mock_chart', 'title': 'Gráfico Mock'}
        def generate_trend_dashboard(self, *args, **kwargs): 
            return {'id': 'mock_trend', 'title': 'Tendencia Mock'}
    
    class BusinessReportGenerator:
        def __init__(self): pass
        def generate_business_review(self, *args, **kwargs): 
            return type('MockReport', (), {'to_dict': lambda: {'report_id': 'mock', 'status': 'mock_mode'}})()
        def generate_executive_summary_report(self, *args, **kwargs):
            return type('MockReport', (), {'to_dict': lambda: {'summary': 'Executive Summary Mock'}})()
    
    class MockQueries:
        def __init__(self): pass
        def __getattr__(self, name):
            return lambda *args, **kwargs: type('MockResult', (), {'data': [], 'row_count': 0})()
    
    class PeriodQueries(MockQueries): pass
    
    class QueryParser:
        def parse_query(self, message, gestor_id=None, periodo=None):
            return {
                'intent': type('QueryIntent', (), {'value': 'performance_analysis'})(),
                'entities': {},
                'filters': {'gestor_id': gestor_id, 'periodo': periodo},
                'complexity': 'low',
                'requires_ranking': False,
                'requires_comparison': False,
                'original_message': message
            }
    
    GestorQueries = ComparativeQueries = DeviationQueries = IncentiveQueries = MockQueries
    
    def is_query_safe(*args): return True
    def validate_chart_generator(): return {'status': 'MOCK', 'error': 'Modo fallback'}
    def iniciar_agente_llm(): 
        return type('MockClient', (), {
            'chat': type('Chat', (), {
                'completions': type('Completions', (), {
                    'create': lambda *args, **kwargs: type('Response', (), {
                        'choices': [type('Choice', (), {
                            'message': type('Message', (), {
                                'content': '{"type": "general_chat", "confidence": 0.5}'
                            })()
                        })()]
                    })()
                })()
            })()
        })()
    
    # 🚀 FUNCIONES MOCK DEL CHART GENERATOR
    def create_chart_from_query_data(query_data, config):
        return {'id': 'mock_chart', 'type': config.get('chart_type', 'bar'), 'title': 'Mock Chart'}
    
    def pivot_chart_with_query_integration(user_message, current_config):
        return {'status': 'success', 'new_config': current_config, 'message': 'Pivoteo mock'}
    
    class ConfigManager:
        def __init__(self): pass
    
    FINANCIAL_ANALYST_SYSTEM_PROMPT = "Mock Financial Analyst System Prompt"
    FINANCIAL_REPORT_SYSTEM_PROMPT = "Mock Financial Report System Prompt"
    COMPARATIVE_ANALYSIS_SYSTEM_PROMPT = "Mock Comparative Analysis System Prompt"
    DEVIATION_ANALYSIS_SYSTEM_PROMPT = "Mock Deviation Analysis System Prompt"
    
    # 🚀 CREAR basic_queries MOCK
    basic_queries = basic_queries()
    
    IMPORTS_SUCCESSFUL = False
    PERIOD_QUERIES_ENHANCED = False
    QUERY_PARSER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ CDG Agent ejecutándose en modo MOCK - integración completa falló")
    print("❌ DEBUG: IMPORTS_SUCCESSFUL establecido a False - MODO MOCK activado")

print("🔍 DEBUG CDG AGENT V4.0 - Fin del bloque de imports con integración completa")

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
    # 🆕 NUEVOS TIPOS DE CONSULTA
    MULTIPLE_GESTOR_ANALYSIS = "multiple_gestor_analysis"
    CENTRO_ANALYSIS = "centro_analysis"
    SEGMENTO_ANALYSIS = "segmento_analysis"
    PRODUCTO_ANALYSIS = "producto_analysis"
    # 🚀 NUEVOS TIPOS PARA GRÁFICOS
    CHART_PIVOT = "chart_pivot"
    CHART_GENERATION = "chart_generation"
    # 🆕 NUEVOS TIPOS PARA BASIC QUERIES
    QUICK_SUMMARY = "quick_summary"
    DATA_EXPLORATION = "data_exploration"

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
    # 🚀 NUEVOS CAMPOS PARA GRÁFICOS
    current_chart_config: Optional[Dict[str, Any]] = None
    chart_interaction_type: Optional[str] = None  # 'pivot', 'generate', 'modify'
    # 🆕 NUEVOS CAMPOS PARA BASIC QUERIES
    use_basic_queries: bool = True
    quick_mode: bool = False

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
    # 🚀 NUEVOS CAMPOS PARA GRÁFICOS
    chart_configs: List[Dict[str, Any]] = None
    pivot_suggestions: List[str] = None
    # 🆕 NUEVOS CAMPOS PARA BASIC QUERIES
    basic_queries_used: bool = False
    data_sources: List[str] = None

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
            'created_at': self.created_at.isoformat(),
            'chart_configs': self.chart_configs or [],
            'pivot_suggestions': self.pivot_suggestions or [],
            'basic_queries_used': self.basic_queries_used,
            'data_sources': self.data_sources or []
        }

class CDGAgent:
    """
    Agente Principal de Control de Gestión - Banca March
    
    🆕 VERSIÓN 4.0: Con integración completa de Chart Generator y Basic Queries
    - basic_queries.py integrado para consultas rápidas
    - QueryIntegratedChartGenerator integrado
    - Pivoteo conversacional de gráficos dinámico
    - Tools para generar gráficos desde query data
    - Capacidades avanzadas de entidades múltiples
    - Interpretación de cambios de visualización
    - Acceso directo a datos mediante basic_queries
    """
    
    def __init__(self):
        """Inicializa el agente CDG con todos los módulos especializados, Chart Generator y Basic Queries"""
        self.start_time = datetime.now()

        try:
            # ✅ CORRECCIÓN CRÍTICA: Usar FinancialKPICalculator
            self.kpi_calculator = FinancialKPICalculator()

            # 🚀 NUEVA INTEGRACIÓN: QueryIntegratedChartGenerator CON PROMPT INTEGRADO
            self.chart_generator = CDGDashboardGenerator()  # Mantener compatibilidad
            self.query_chart_generator = QueryIntegratedChartGenerator()  # Nueva funcionalidad CON PROMPT

            # ✅ NUEVO: Inicializar manejador de cambios de gráficos con prompt del sistema
            self.chart_change_handler = handle_chart_change_request

            
            self.report_generator = BusinessReportGenerator()
            
            # ✅ INTEGRACIÓN COMPLETA: Inicializar módulos de consultas enhanced
            self.gestor_queries = GestorQueries()
            self.comparative_queries = ComparativeQueries()
            self.deviation_queries = DeviationQueries()
            self.incentive_queries = IncentiveQueries()
            self.period_queries = PeriodQueries()  # ✅ INTEGRACIÓN PERIOD_QUERIES
            
            # 🆕 NUEVA INTEGRACIÓN: Basic Queries
            self.basic_queries = basic_queries
            
            # 🆕 NUEVO: Inicializar QueryParser mejorado
            self.query_parser = QueryParser()
            
            # Configuración y estado del agente
            self.config_manager = ConfigManager()
            self.conversation_history = []
            self.user_preferences = {}
            
            # Estado de importaciones
            self.imports_successful = IMPORTS_SUCCESSFUL
            self.period_queries_enhanced = PERIOD_QUERIES_ENHANCED
            self.query_parser_available = QUERY_PARSER_AVAILABLE
            self.basic_queries_available = True
            
            logger.info("🚀 CDG Agent V4.0 inicializado exitosamente con Chart Generator y Basic Queries integrados")
            if not IMPORTS_SUCCESSFUL:
                logger.warning("⚠️ CDG Agent iniciado en modo MOCK - funcionalidad limitada")
                
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando CDG Agent: {e}")
            raise RuntimeError(f"Fallo crítico en inicialización del CDG Agent: {e}")

    # 🆕 NUEVOS MÉTODOS ESPECÍFICOS PARA BASIC QUERIES

    async def get_quick_summary(self) -> Dict[str, Any]:
        """🚀 NUEVO: Obtiene resumen rápido usando basic_queries"""
        try:
            logger.info("📊 Obteniendo resumen rápido con basic_queries...")
            
            summary = self.basic_queries.get_resumen_general()
            
            return {
                'type': 'quick_summary',
                'data': summary,
                'source': 'basic_queries',
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen rápido: {e}")
            return {'error': str(e)}

    async def get_gestores_ranking_basic(self, metric: str = 'contratos') -> Dict[str, Any]:
        """🚀 NUEVO: Obtiene ranking de gestores usando basic_queries"""
        try:
            logger.info(f"🏆 Obteniendo ranking de gestores por {metric} con basic_queries...")
            
            if metric.lower() in ['contratos', 'contract', 'contracts']:
                data = self.basic_queries.count_contratos_by_gestor()
                metric_field = 'num_contratos'
            elif metric.lower() in ['clientes', 'clients', 'cliente']:
                data = self.basic_queries.count_clientes_by_gestor()
                metric_field = 'num_clientes'
            else:
                data = self.basic_queries.count_contratos_by_gestor()
                metric_field = 'num_contratos'
            
            # Procesar datos para respuesta
            processed_data = []
            for item in data[:15]:  # Top 15
                processed_data.append({
                    'gestor': item.get('DESC_GESTOR', 'N/A'),
                    'value': item.get(metric_field, 0),
                    'metric': metric,
                    'original_data': item
                })
            
            return {
                'type': 'gestores_ranking',
                'metric': metric,
                'data': processed_data,
                'source': 'basic_queries',
                'total_gestores': len(processed_data)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo ranking de gestores: {e}")
            return {'error': str(e)}

    async def get_centros_info_basic(self) -> Dict[str, Any]:
        """🚀 NUEVO: Obtiene información de centros usando basic_queries"""
        try:
            logger.info("🏢 Obteniendo información de centros con basic_queries...")
            
            centros_data = self.basic_queries.get_all_centros()
            contratos_by_centro = self.basic_queries.count_contratos_by_centro()
            
            # Combinar información
            centros_combined = []
            for centro in centros_data:
                centro_info = centro.copy()
                # Buscar contratos correspondientes
                for contrato_info in contratos_by_centro:
                    if contrato_info.get('CENTRO_ID') == centro.get('CENTRO_ID'):
                        centro_info['num_contratos'] = contrato_info.get('num_contratos', 0)
                        break
                else:
                    centro_info['num_contratos'] = 0
                
                centros_combined.append(centro_info)
            
            return {
                'type': 'centros_info',
                'data': centros_combined,
                'source': 'basic_queries',
                'total_centros': len(centros_combined)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información de centros: {e}")
            return {'error': str(e)}

    async def get_productos_popularity_basic(self) -> Dict[str, Any]:
        """🚀 NUEVO: Obtiene popularidad de productos usando basic_queries"""
        try:
            logger.info("📦 Obteniendo popularidad de productos con basic_queries...")
            
            productos_data = self.basic_queries.count_contratos_by_producto()
            
            processed_data = []
            for item in productos_data:
                processed_data.append({
                    'producto': item.get('DESC_PRODUCTO', 'N/A'),
                    'num_contratos': item.get('num_contratos', 0),
                    'producto_id': item.get('PRODUCTO_ID'),
                    'original_data': item
                })
            
            return {
                'type': 'productos_popularity',
                'data': processed_data,
                'source': 'basic_queries',
                'total_productos': len(processed_data)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo popularidad de productos: {e}")
            return {'error': str(e)}

    async def handle_basic_queries_request(self, request: CDGRequest) -> Dict[str, Any]:
        """🚀 NUEVO: Maneja solicitudes específicas para basic_queries"""
        try:
            message_lower = request.user_message.lower()
            
            # Detectar tipo de consulta básica
            if any(word in message_lower for word in ['resumen', 'summary', 'general', 'overview']):
                return await self.get_quick_summary()
            
            elif any(word in message_lower for word in ['ranking', 'top', 'mejor', 'gestores']):
                metric = 'contratos'
                if any(word in message_lower for word in ['clientes', 'clients']):
                    metric = 'clientes'
                return await self.get_gestores_ranking_basic(metric)
            
            elif any(word in message_lower for word in ['centros', 'oficinas', 'centers']):
                return await self.get_centros_info_basic()
            
            elif any(word in message_lower for word in ['productos', 'products', 'popularidad']):
                return await self.get_productos_popularity_basic()
            
            else:
                # Consulta genérica - devolver resumen
                return await self.get_quick_summary()
                
        except Exception as e:
            logger.error(f"Error manejando solicitud de basic_queries: {e}")
            return {'error': str(e)}

    # 🚀 MÉTODOS PRINCIPALES MEJORADOS

    async def process_request(self, request: CDGRequest) -> CDGResponse:
        """
        🚀 MEJORADO: Procesa solicitud con Chart Generator, Basic Queries integrados y pivoteo conversacional
        
        Args:
            request: Solicitud estructurada del usuario
            
        Returns:
            CDGResponse: Respuesta completa con análisis, gráficos y recomendaciones
        """
        start_time = datetime.now()
        
        try:
            # 1. 🆕 NUEVO: Detectar si es solicitud rápida de basic_queries
            if request.quick_mode or request.use_basic_queries and self._is_basic_query_request(request.user_message):
                basic_data = await self.handle_basic_queries_request(request)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return CDGResponse(
                    response_type=QueryType.QUICK_SUMMARY,
                    content=basic_data,
                    charts=[],
                    recommendations=[],
                    metadata={'basic_queries_direct': True},
                    execution_time=execution_time,
                    confidence_score=0.9,
                    created_at=datetime.now(),
                    chart_configs=[],
                    pivot_suggestions=[],
                    basic_queries_used=True,
                    data_sources=['basic_queries']
                )
            
            # 2. 🆕 NUEVO: Detectar si es interacción con gráfico
            if self._is_chart_interaction(request.user_message, request.current_chart_config):
                return await self._handle_chart_interaction(request, start_time)
            
            # 3. 🆕 NUEVO: Usar QueryParser para análisis completo
            if self.query_parser_available:
                parsed_query = self.query_parser.parse_query(
                    request.user_message, 
                    request.gestor_id, 
                    request.periodo
                )
                logger.info(f"🎯 QueryParser - Intent: {parsed_query['intent'].value}, Entidades: {parsed_query['entities']}")
            else:
                parsed_query = None
            
            # 4. Analizar la intención del usuario (mejorado con QueryParser)
            query_type, confidence = await self._classify_user_intent_enhanced(
                request.user_message, parsed_query
            )
            logger.info(f"💭 Intención clasificada: {query_type.value} (confianza: {confidence:.2f})")
            
            # 5. 🆕 NUEVO: Orquestar respuesta con entidades múltiples y basic_queries
            if query_type == QueryType.GESTOR_ANALYSIS:
                response_content = await self._handle_gestor_analysis_enhanced(request, parsed_query)
            elif query_type == QueryType.COMPARATIVE_ANALYSIS:
                response_content = await self._handle_comparative_analysis_enhanced(request, parsed_query)
            elif query_type == QueryType.MULTIPLE_GESTOR_ANALYSIS:
                response_content = await self._handle_multiple_gestor_analysis(request, parsed_query)
            elif query_type == QueryType.CENTRO_ANALYSIS:
                response_content = await self._handle_centro_analysis_enhanced(request, parsed_query)
            elif query_type == QueryType.SEGMENTO_ANALYSIS:
                response_content = await self._handle_segmento_analysis(request, parsed_query)
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                response_content = await self._handle_deviation_analysis(request)
            elif query_type == QueryType.INCENTIVE_ANALYSIS:
                response_content = await self._handle_incentive_analysis(request)
            elif query_type == QueryType.BUSINESS_REVIEW:
                response_content = await self._handle_business_review(request)
            elif query_type == QueryType.EXECUTIVE_SUMMARY:
                response_content = await self._handle_executive_summary(request)
            elif query_type == QueryType.DATA_EXPLORATION:
                response_content = await self.handle_basic_queries_request(request)
                response_content['analysis_type'] = 'data_exploration_enhanced'
            else:
                response_content = await self._handle_general_chat_enhanced(request, parsed_query)
            
            # 6. 🚀 MEJORADO: Generar gráficos usando nueva integración
            charts = []
            chart_configs = []
            if request.include_charts and 'kpi_data' in response_content:
                charts, chart_configs = await self._generate_charts_enhanced(response_content, query_type)
            
            # 7. Generar recomendaciones si se solicitan
            recommendations = []
            if request.include_recommendations:
                recommendations = await self._generate_recommendations(response_content, query_type)
            
            # 8. 🚀 NUEVO: Generar sugerencias de pivoteo
            pivot_suggestions = await self._generate_pivot_suggestions(response_content, query_type)
            
            # 9. Construir respuesta final
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
                    'data_sources': self._get_data_sources(query_type),
                    'imports_successful': self.imports_successful,
                    'period_queries_enhanced': self.period_queries_enhanced,
                    'query_parser_active': self.query_parser_available,
                    'parsed_entities': parsed_query['entities'] if parsed_query else {},
                    'chart_generator_integrated': True,
                    'basic_queries_available': self.basic_queries_available
                },
                execution_time=execution_time,
                confidence_score=confidence,
                created_at=datetime.now(),
                chart_configs=chart_configs,
                pivot_suggestions=pivot_suggestions,
                basic_queries_used=request.use_basic_queries and self.basic_queries_available,
                data_sources=self._get_data_sources(query_type)
            )
            
            # 10. Actualizar historial de conversación
            self._update_conversation_history(request, response)
            
            logger.info(f"✅ Solicitud procesada exitosamente en {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error procesando solicitud: {e}")
            return await self._create_error_response(request, str(e), start_time)

    def _is_basic_query_request(self, user_message: str) -> bool:
        """🆕 NUEVO: Detecta si es una consulta básica que puede usar basic_queries"""
        basic_keywords = [
            'resumen', 'summary', 'general', 'overview',
            'cuántos', 'total', 'cantidad', 'count',
            'ranking', 'top', 'mejor', 'peor',
            'centros', 'oficinas', 'gestores',
            'productos', 'contratos', 'clientes',
            'rápido', 'quick', 'fast',
            'lista', 'listar', 'mostrar'
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in basic_keywords)

    # 🆕 NUEVO: Método mejorado para análisis de centro usando basic_queries
    async def _handle_centro_analysis_enhanced(self, request: CDGRequest, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """🆕 MEJORADO: Análisis de centros con basic_queries integrado"""
        logger.info("🏢 Procesando análisis de centro con basic_queries...")
        
        try:
            # Obtener información de centros usando basic_queries
            centros_info = await self.get_centros_info_basic()
            
            if centros_info.get('error'):
                return centros_info
            
            # Obtener información adicional de gestores si es necesario
            try:
                gestores_data = self.basic_queries.get_all_gestores()
            except:
                gestores_data = []
            
            # Análisis específico Madrid vs Barcelona
            madrid_data = None
            barcelona_data = None
            
            for centro in centros_info['data']:
                centro_name = centro.get('DESC_CENTRO', '').upper()
                if 'MADRID' in centro_name:
                    madrid_data = centro
                elif 'BARCELONA' in centro_name:
                    barcelona_data = centro
            
            # Complementar con análisis tradicional si está disponible
            performance_data = []
            try:
                centro_performance = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
                performance_data = centro_performance.data if centro_performance and hasattr(centro_performance, 'data') else []
            except:
                pass
            
            return {
                'comparison_type': 'centros_analysis_enhanced',
                'basic_queries_data': centros_info,
                'madrid_data': madrid_data,
                'barcelona_data': barcelona_data,
                'gestores_data': gestores_data,
                'performance_general': performance_data,
                'kpi_data': {'centro_analysis': True},
                'analysis_type': 'centro_analysis_enhanced',
                'data_sources': ['basic_queries', 'comparative_queries']
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de centro enhanced: {e}")
            return {"error": f"Error procesando análisis de centro enhanced: {str(e)}"}

    # 🚀 MÉTODOS EXISTENTES MEJORADOS CON BASIC QUERIES

    def _is_chart_interaction(self, user_message: str, current_chart_config: Optional[Dict] = None) -> bool:
        """Detecta si el mensaje es una interacción con gráfico"""
        chart_keywords = [
            'cambia', 'cambiar', 'modifica', 'modificar', 'convierte', 'convertir',
            'gráfico', 'chart', 'barras', 'línea', 'circular', 'pie',
            'mostrar', 'visualizar', 'ver en', 'como'
        ]
        
        message_lower = user_message.lower()
        has_chart_keywords = any(keyword in message_lower for keyword in chart_keywords)
        has_current_chart = current_chart_config is not None
        
        return has_chart_keywords and has_current_chart

    async def _handle_chart_interaction(self, request: CDGRequest, start_time: datetime) -> CDGResponse:
        """Maneja interacciones específicas con gráficos (pivoteo conversacional CON PROMPT INTEGRADO)"""
        logger.info("📊 Procesando interacción con gráfico CON PROMPT DEL SISTEMA...")

        try:
            # ✅ NUEVO: Usar manejador de cambios con prompt integrado del sistema CDG
            pivot_result = self.chart_change_handler(
                user_message=request.user_message,
                current_chart_config=request.current_chart_config or {},
                context={'agente': 'CDG', 'usuario_id': request.user_id, 'gestor_id': request.gestor_id}
            )

            # Fallback al método tradicional si el nuevo no funciona
            if not pivot_result or pivot_result.get('status') != 'success':
                pivot_result = pivot_chart_with_query_integration(
                    request.user_message,
                    request.current_chart_config or {}
                )

            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CDGResponse(
                response_type=QueryType.CHART_PIVOT,
                content={
                    'pivot_result': pivot_result,
                    'original_message': request.user_message,
                    'chart_interaction': True
                },
                charts=[pivot_result] if pivot_result.get('status') == 'success' else [],
                recommendations=[pivot_result.get('message', 'Gráfico actualizado')],
                metadata={'chart_pivot': True, 'query_recommendation': pivot_result.get('query_recommendation')},
                execution_time=execution_time,
                confidence_score=0.9,
                created_at=datetime.now(),
                chart_configs=[pivot_result.get('new_config', {})] if pivot_result.get('status') == 'success' else [],
                pivot_suggestions=[],
                basic_queries_used=False,
                data_sources=['chart_generator']
            )
            
        except Exception as e:
            logger.error(f"Error en interacción con gráfico: {e}")
            return await self._create_error_response(request, f"Error en pivoteo de gráfico: {str(e)}", start_time)

    async def _generate_charts_enhanced(self, content_data: Dict[str, Any], query_type: QueryType) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        🚀 MEJORADO: Genera gráficos usando QueryIntegratedChartGenerator y datos de basic_queries
        
        Returns:
            Tuple[charts, chart_configs]: Lista de gráficos y sus configuraciones
        """
        charts = []
        chart_configs = []
        
        try:
            if query_type == QueryType.GESTOR_ANALYSIS and 'kpi_data' in content_data:
                # Usar nueva función para generar gráfico desde query data
                gestor_data = content_data.get('gestor_data', {})
                if gestor_data:
                    chart_config = {
                        'chart_type': 'bar',
                        'dimension': 'gestor', 
                        'metric': 'ROE',
                        'period': content_data.get('periodo', '2025-10'),
                        'context': {'agente': 'CDG', 'analysis_type': 'gestor_performance'}  # ✅ NUEVO
                    }

                    chart = create_chart_from_query_data([gestor_data], chart_config)
                    charts.append(chart)
                    chart_configs.append(chart_config)
            
            elif query_type in [QueryType.COMPARATIVE_ANALYSIS, QueryType.MULTIPLE_GESTOR_ANALYSIS]:
                if 'ranking_gestores' in content_data and content_data['ranking_gestores']:
                    chart_config = {
                        'chart_type': 'bar',
                        'dimension': 'gestor',
                        'metric': 'MARGEN_NETO',
                        'period': content_data.get('periodo', '2025-10')
                    }
                    
                    chart = create_chart_from_query_data(content_data['ranking_gestores'], chart_config)
                    charts.append(chart)
                    chart_configs.append(chart_config)
            
            elif query_type == QueryType.CENTRO_ANALYSIS:
                # 🆕 MEJORADO: Usar datos de basic_queries para gráficos
                if 'basic_queries_data' in content_data:
                    centros_data = content_data['basic_queries_data'].get('data', [])
                    if centros_data:
                        chart_config = {
                            'chart_type': 'pie',
                            'dimension': 'centro',
                            'metric': 'CONTRATOS',
                            'period': content_data.get('periodo', '2025-10')
                        }
                        
                        chart = create_chart_from_query_data(centros_data, chart_config)
                        charts.append(chart)
                        chart_configs.append(chart_config)
            
            elif query_type == QueryType.QUICK_SUMMARY:
                # 🆕 NUEVO: Gráfico de resumen usando basic_queries
                if 'data' in content_data:
                    summary_data = content_data['data']
                    chart_data = [
                        {'label': 'Gestores', 'value': summary_data.get('total_gestores', 0)},
                        {'label': 'Clientes', 'value': summary_data.get('total_clientes', 0)},
                        {'label': 'Contratos', 'value': summary_data.get('total_contratos', 0)},
                        {'label': 'Centros', 'value': summary_data.get('total_centros', 0)}
                    ]
                    
                    chart_config = {
                        'chart_type': 'bar',
                        'dimension': 'metric',
                        'metric': 'COUNT',
                        'period': datetime.now().strftime('%Y-%m')
                    }
                    
                    chart = create_chart_from_query_data(chart_data, chart_config)
                    charts.append(chart)
                    chart_configs.append(chart_config)
            
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                if content_data.get('desviaciones_precio'):
                    chart_config = {
                        'chart_type': 'line',
                        'dimension': 'period',
                        'metric': 'DEVIATION',
                        'period': content_data.get('periodo', '2025-10')
                    }
                    
                    chart = create_chart_from_query_data(content_data['desviaciones_precio'], chart_config)
                    charts.append(chart)
                    chart_configs.append(chart_config)
            
            # Mantener compatibilidad con método anterior si no hay datos para nuevo método
            if not charts:
                old_charts = await self._generate_charts_legacy(content_data, query_type)
                charts.extend(old_charts)
                
        except Exception as e:
            logger.warning(f"Error generando gráficos mejorados: {e}")
            # Fallback al método legacy
            try:
                charts = await self._generate_charts_legacy(content_data, query_type)
            except Exception as e2:
                logger.error(f"Error en fallback de gráficos: {e2}")
        
        return charts, chart_configs

    async def _generate_charts_legacy(self, content_data: Dict[str, Any], query_type: QueryType) -> List[Dict[str, Any]]:
        """Método legacy de generación de gráficos para compatibilidad"""
        charts = []
        
        try:
            if query_type == QueryType.GESTOR_ANALYSIS and 'kpi_data' in content_data:
                dashboard = self.chart_generator.generate_gestor_dashboard(
                    content_data.get('gestor_data', {}),
                    content_data['kpi_data'],
                    content_data.get('periodo')
                )
                charts.extend(dashboard.get('charts', []))
                
            elif query_type in [QueryType.COMPARATIVE_ANALYSIS, QueryType.MULTIPLE_GESTOR_ANALYSIS] and 'ranking_gestores' in content_data:
                comparative_chart = self.chart_generator.generate_comparative_dashboard(
                    content_data['ranking_gestores'],
                    metric='margen_neto',
                    titulo='Ranking de Gestores por Margen Neto'
                )
                charts.append(comparative_chart)
                
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                if 'desviaciones_precio' in content_data and content_data['desviaciones_precio']:
                    deviation_chart = self.chart_generator.generate_trend_dashboard(
                        content_data['desviaciones_precio'],
                        title='Evolución de Desviaciones de Precio'
                    )
                    charts.append(deviation_chart)
            
        except Exception as e:
            logger.warning(f"Error generando gráficos legacy: {e}")
        
        return charts

    async def _generate_pivot_suggestions(self, content_data: Dict[str, Any], query_type: QueryType) -> List[str]:
        """🚀 NUEVO: Genera sugerencias de pivoteo conversacional"""
        suggestions = []
        
        try:
            if query_type in [QueryType.GESTOR_ANALYSIS, QueryType.COMPARATIVE_ANALYSIS]:
                suggestions.extend([
                    "Cambiar a gráfico circular",
                    "Mostrar evolución temporal",
                    "Ver por centro",
                    "Comparar con margen neto"
                ])
                
            elif query_type == QueryType.CENTRO_ANALYSIS:
                suggestions.extend([
                    "Cambiar a gráfico de líneas",
                    "Ver distribución por gestor",
                    "Mostrar eficiencia por centro"
                ])
                
            elif query_type == QueryType.QUICK_SUMMARY:
                suggestions.extend([
                    "Ver como gráfico circular",
                    "Mostrar ranking de gestores",
                    "Comparar centros"
                ])
                
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                suggestions.extend([
                    "Ver como barras",
                    "Agrupar por gestor",
                    "Mostrar tendencia mensual"
                ])
            
        except Exception as e:
            logger.warning(f"Error generando sugerencias de pivoteo: {e}")
        
        return suggestions

    # 🚀 MÉTODOS MEJORADOS EXISTENTES (con integración basic_queries)

    async def _classify_user_intent_enhanced(self, user_message: str, parsed_query: Optional[Dict] = None) -> Tuple[QueryType, float]:
        """
        🚀 MEJORADO: Clasificación de intención con QueryParser y basic_queries integrados
        """
        try:
            # Detectar interacciones con gráficos primero
            if self._is_chart_interaction(user_message):
                return QueryType.CHART_PIVOT, 0.95
            
            # 🆕 NUEVO: Detectar consultas básicas que pueden usar basic_queries
            if self._is_basic_query_request(user_message):
                return QueryType.DATA_EXPLORATION, 0.88
            
            # Si tenemos QueryParser, usar su información
            if parsed_query and self.query_parser_available:
                entities = parsed_query.get('entities', {})
                
                # Detectar análisis de múltiples gestores
                if 'gestores_ids' in entities and len(entities['gestores_ids']) > 1:
                    return QueryType.MULTIPLE_GESTOR_ANALYSIS, 0.9
                
                # Detectar análisis de centros
                if 'centro_id' in entities or 'centros_ids' in entities:
                    return QueryType.CENTRO_ANALYSIS, 0.85
                
                # Detectar análisis de segmentos
                if 'segmento_id' in entities or 'segmentos_ids' in entities:
                    return QueryType.SEGMENTO_ANALYSIS, 0.85
                
                # Usar intención del QueryParser como base
                parser_intent = parsed_query['intent'].value
                if parser_intent == 'comparative_analysis':
                    return QueryType.COMPARATIVE_ANALYSIS, 0.9
                elif parser_intent == 'ranking_analysis':
                    return QueryType.COMPARATIVE_ANALYSIS, 0.85
                elif parser_intent == 'causal_analysis':
                    return QueryType.GESTOR_ANALYSIS, 0.8
                elif parser_intent == 'performance_analysis':
                    return QueryType.GESTOR_ANALYSIS, 0.8
                
            # Clasificación tradicional con Azure OpenAI
            classification_prompt = f"""
            Analiza el siguiente mensaje de un usuario de Control de Gestión de Banca March y clasifica su intención:

            Mensaje: "{user_message}"

            Tipos de consulta disponibles:
            - gestor_analysis: Análisis específico de un gestor (performance, KPIs individuales)
            - comparative_analysis: Comparaciones entre gestores, centros o períodos
            - multiple_gestor_analysis: Análisis de múltiples gestores específicos
            - centro_analysis: Análisis específico de centros
            - segmento_analysis: Análisis específico de segmentos
            - deviation_analysis: Análisis de desviaciones, alertas, anomalías
            - incentive_analysis: Análisis de incentivos, comisiones, bonus
            - business_review: Generación de Business Review completo
            - executive_summary: Resumen ejecutivo para directivos
            - chart_pivot: Cambio o modificación de gráficos existentes
            - data_exploration: Consultas básicas de exploración de datos
            - quick_summary: Resúmenes rápidos y consultas generales
            - general_chat: Conversación general o consultas no específicas

            Responde SOLO con el formato JSON:
            {{"type": "tipo_de_consulta", "confidence": 0.95}}
            """
            
            client = iniciar_agente_llm()
            deployment_id = settings.AZURE_OPENAI_DEPLOYMENT_ID
            
            response = client.chat.completions.create(
                model=deployment_id,
                messages=[
                    {"role": "system", "content": "Eres un clasificador experto de intenciones para el sistema CDG de Banca March. Responde SOLO con JSON válido."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            raw_content = response.choices[0].message.content
            cleaned_content = clean_llm_json_response(raw_content)
            
            try:
                result = json.loads(cleaned_content)
                query_type = QueryType(result['type'])
                confidence = float(result['confidence'])
                return query_type, confidence
            except (json.JSONDecodeError, KeyError, ValueError) as json_error:
                logger.warning(f"Error parsing JSON response: {json_error}. Response: {raw_content}")
                return self._fallback_classification(user_message)
                
        except Exception as e:
            logger.warning(f"Error en clasificación de intención: {e}")
            return QueryType.GENERAL_CHAT, 0.5

    def _fallback_classification(self, user_message: str) -> Tuple[QueryType, float]:
        """Clasificación fallback basada en palabras clave mejorada"""
        message_lower = user_message.lower()

        # Detectar interacciones con gráficos
        if any(word in message_lower for word in ['cambia', 'cambiar', 'gráfico', 'chart', 'barras', 'línea']):
            return QueryType.CHART_PIVOT, 0.8

        # Detectar consultas básicas
        if any(word in message_lower for word in ['resumen', 'cuántos', 'total', 'ranking', 'lista']):
            return QueryType.DATA_EXPLORATION, 0.75

        # Detectar múltiples gestores
        if re.search(r'gestores?\s+\d+.*\d+', message_lower) or 'y' in message_lower and 'gestor' in message_lower:
            return QueryType.MULTIPLE_GESTOR_ANALYSIS, 0.8
        
        # Detectar centros
        if any(word in message_lower for word in ['centro', 'oficina', 'madrid', 'barcelona', 'palma']):
            return QueryType.CENTRO_ANALYSIS, 0.7
        
        # Detectar segmentos
        if any(word in message_lower for word in ['segmento', 'banca privada', 'empresas', 'fondos']):
            return QueryType.SEGMENTO_ANALYSIS, 0.7

        if any(word in message_lower for word in ['gestor', 'performance', 'kpi']):
            return QueryType.GESTOR_ANALYSIS, 0.7
        elif any(word in message_lower for word in ['comparativa', 'ranking', 'versus', 'vs', 'comparar']):
            return QueryType.COMPARATIVE_ANALYSIS, 0.7
        elif any(word in message_lower for word in ['desviación', 'alerta', 'anomalía']):
            return QueryType.DEVIATION_ANALYSIS, 0.7
        elif any(word in message_lower for word in ['incentivo', 'bonus', 'comisión']):
            return QueryType.INCENTIVE_ANALYSIS, 0.7
        elif any(word in message_lower for word in ['business review', 'informe']):
            return QueryType.BUSINESS_REVIEW, 0.7
        elif any(word in message_lower for word in ['executive', 'resumen ejecutivo']):
            return QueryType.EXECUTIVE_SUMMARY, 0.7
        else:
            return QueryType.GENERAL_CHAT, 0.5

    # 🚀 HANDLERS EXISTENTES MEJORADOS CON BASIC QUERIES

    async def _handle_gestor_analysis_enhanced(self, request: CDGRequest, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """🚀 MEJORADO: Maneja análisis específico de gestores con QueryParser y basic_queries"""
        logger.info("🔍 Procesando análisis de gestor...")
        
        try:
            gestor_id = request.gestor_id
            
            # Extraer gestor_id del QueryParser si no se proporcionó
            if not gestor_id and parsed_query:
                entities = parsed_query.get('entities', {})
                gestor_id = entities.get('gestor_id_extracted')
            
            # 🆕 NUEVO: Intentar obtener información complementaria con basic_queries
            basic_gestor_info = None
            try:
                if request.use_basic_queries and self.basic_queries_available:
                    gestores_ranking = await self.get_gestores_ranking_basic('contratos')
                    for gestor in gestores_ranking.get('data', []):
                        if str(gestor_id) in gestor.get('gestor', '') or gestor.get('gestor_id') == gestor_id:
                            basic_gestor_info = gestor
                            break
            except Exception as e:
                logger.warning(f"Error obteniendo información básica del gestor: {e}")
            
            # Obtener datos del gestor
            if gestor_id:
                gestor_data = self.gestor_queries.get_gestor_performance_enhanced(gestor_id, request.periodo)
            else:
                # Inferir gestor del mensaje del usuario
                gestor_data = await self._infer_gestor_from_message(request.user_message)
            
            if not gestor_data or gestor_data.row_count == 0:
                return {"error": "No se encontraron datos para el gestor especificado"}
            
            # Usar método correcto del KPI calculator
            gestor_info = gestor_data.data[0]
            kpi_analysis = self.kpi_calculator.calculate_kpis_from_data(gestor_info)
            
            # Obtener datos adicionales
            try:
                incentivos = self.incentive_queries.calculate_incentive_impact_enhanced(gestor_info.get('gestor_id'), request.periodo)
            except AttributeError:
                try:
                    incentivos = self.incentive_queries.ranking_incentivos_periodo_enhanced(request.periodo)
                except AttributeError:
                    incentivos = type('EmptyResult', (), {'data': []})()
            
            comparativas = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
            
            return {
                'gestor_data': gestor_info,
                'kpi_data': kpi_analysis,
                'incentivos': incentivos.data if incentivos and hasattr(incentivos, 'data') else [],
                'comparativas': comparativas.data[:5] if comparativas and hasattr(comparativas, 'data') else [],
                'basic_gestor_info': basic_gestor_info,  # 🆕 NUEVO
                'analysis_type': 'gestor_performance_enhanced',
                'data_sources': ['gestor_queries', 'basic_queries'] if basic_gestor_info else ['gestor_queries']
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de gestor: {e}")
            return {"error": f"Error procesando análisis de gestor: {str(e)}"}

    # RESTO DE MÉTODOS EXISTENTES (mantienen funcionalidad original)
    # [Los demás métodos del cdg_agent.py original se mantienen igual...]

    async def _handle_comparative_analysis_enhanced(self, request: CDGRequest, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """🚀 MEJORADO: Maneja análisis comparativos con entidades múltiples"""
        logger.info("📊 Procesando análisis comparativo...")

        try:
            # Verificar si hay entidades específicas para comparar
            if parsed_query and parsed_query.get('entities', {}):
                entities = parsed_query['entities']
                
                # Si hay múltiples gestores, delegar al handler específico
                if 'gestores_ids' in entities:
                    return await self._handle_multiple_gestor_analysis(request, parsed_query)
                
                # Si hay centros específicos
                if 'centros_ids' in entities:
                    return await self._handle_centro_analysis_enhanced(request, parsed_query)
                
                # Si hay segmentos específicos
                if 'segmentos_ids' in entities:
                    return await self._handle_segmento_analysis(request, parsed_query)

            # Análisis comparativo general
            ranking_gestores = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)

            try:
                compare_centros = self.comparative_queries.compare_eficiencia_centros_enhanced(request.periodo)
            except AttributeError:
                try:
                    compare_centros = self.comparative_queries.analyze_centros_performance_enhanced(request.periodo)
                except AttributeError:
                    compare_centros = type('EmptyResult', (), {'data': []})()

            try:
                roe_analysis = self.comparative_queries.compare_roe_gestores_enhanced(request.periodo)
            except AttributeError:
                roe_analysis = type('EmptyResult', (), {'data': []})()

            return {
                'ranking_gestores': ranking_gestores.data if ranking_gestores and hasattr(ranking_gestores, 'data') else [],
                'eficiencia_centros': compare_centros.data if compare_centros and hasattr(compare_centros, 'data') else [],
                'roe_analysis': roe_analysis.data if roe_analysis and hasattr(roe_analysis, 'data') else [],
                'kpi_data': {'comparative_analysis': True},  # Para activar generación de gráficos
                'analysis_type': 'comparative_analysis',
                'periodo': request.periodo
            }

        except Exception as e:
            logger.error(f"Error en análisis comparativo: {e}")
            return {"error": f"Error procesando análisis comparativo: {str(e)}"}

    async def _handle_multiple_gestor_analysis(self, request: CDGRequest, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """🆕 NUEVO: Maneja análisis de múltiples gestores"""
        logger.info("👥 Procesando análisis de múltiples gestores...")
        
        try:
            gestores_ids = []
            
            # Extraer IDs de gestores del QueryParser o del contexto
            if parsed_query and 'gestores_ids' in parsed_query.get('entities', {}):
                gestores_ids = parsed_query['entities']['gestores_ids']
            elif request.context and 'gestores_ids' in request.context:
                gestores_ids = request.context['gestores_ids']
            
            if not gestores_ids:
                return {"error": "No se encontraron múltiples gestores para analizar"}
            
            # Obtener datos de cada gestor
            gestores_data = []
            kpis_comparativos = []
            
            for gestor_id in gestores_ids:
                gestor_data = self.gestor_queries.get_gestor_performance_enhanced(gestor_id, request.periodo)
                if gestor_data and gestor_data.row_count > 0:
                    gestor_info = gestor_data.data[0]
                    gestores_data.append(gestor_info)
                    
                    # Calcular KPIs para cada gestor
                    kpi_analysis = self.kpi_calculator.calculate_kpis_from_data(gestor_info)
                    kpis_comparativos.append({
                        'gestor_id': gestor_id,
                        'gestor_name': gestor_info.get('desc_gestor'),
                        'kpis': kpi_analysis
                    })
            
            return {
                'gestores_data': gestores_data,
                'kpis_comparativos': kpis_comparativos,
                'kpi_data': {'multiple_gestores': True},  # Para activar generación de gráficos
                'num_gestores_analizados': len(gestores_data),
                'analysis_type': 'multiple_gestor_analysis',
                'gestores_ids': gestores_ids
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de múltiples gestores: {e}")
            return {"error": f"Error procesando múltiples gestores: {str(e)}"}

    async def _handle_segmento_analysis(self, request: CDGRequest, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """🆕 NUEVO: Maneja análisis específico de segmentos"""
        logger.info("📊 Procesando análisis de segmento...")
        
        try:
            segmento_id = None
            segmento_name = None
            
            # Extraer información del segmento
            if parsed_query and parsed_query.get('entities', {}):
                entities = parsed_query['entities']
                segmento_id = entities.get('segmento_id')
                segmento_name = entities.get('segmento_name')
            
            if segmento_id:
                # Obtener gestores del segmento
                gestores_segmento = self.gestor_queries.get_gestores_by_segmento_enhanced(segmento_id, request.periodo)
                
                # Análisis del segmento
                segmento_kpis = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
                
                return {
                    'segmento_id': segmento_id,
                    'segmento_name': segmento_name,
                    'gestores_segmento': gestores_segmento.data if gestores_segmento and hasattr(gestores_segmento, 'data') else [],
                    'segmento_kpis': segmento_kpis.data if segmento_kpis and hasattr(segmento_kpis, 'data') else [],
                    'kpi_data': {'segmento_analysis': True},  # Para activar generación de gráficos
                    'analysis_type': 'segmento_analysis'
                }
            else:
                # Análisis general de segmentos
                segmentos_data = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
                return {
                    'segmentos_data': segmentos_data.data if segmentos_data and hasattr(segmentos_data, 'data') else [],
                    'kpi_data': {'segmentos_general': True},  # Para activar generación de gráficos
                    'analysis_type': 'segmentos_general_analysis'
                }
                
        except Exception as e:
            logger.error(f"Error en análisis de segmento: {e}")
            return {"error": f"Error procesando análisis de segmento: {str(e)}"}

    async def _handle_general_chat_enhanced(self, request: CDGRequest, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """🚀 MEJORADO: Maneja conversación general con contexto enriquecido y basic_queries"""
        logger.info("💬 Procesando conversación general...")
        
        try:
            # 🆕 NUEVO: Intentar usar basic_queries para contexto si está disponible
            basic_context = {}
            if request.use_basic_queries and self.basic_queries_available:
                try:
                    basic_context = await self.get_quick_summary()
                    logger.info("✅ Contexto básico obtenido de basic_queries")
                except Exception as e:
                    logger.warning(f"Error obteniendo contexto básico: {e}")
            
            # Obtener contexto relevante basado en el mensaje y entidades extraídas
            context_data = await self._get_relevant_context_enhanced(request.user_message, parsed_query)
            
            # Construir prompt contextualizado mejorado
            system_prompt = FINANCIAL_ANALYST_SYSTEM_PROMPT
            
            entities_info = ""
            if parsed_query and parsed_query.get('entities'):
                entities_info = f"\nEntidades detectadas: {json.dumps(parsed_query['entities'], ensure_ascii=False)}"
            
            basic_context_info = ""
            if basic_context and 'data' in basic_context:
                basic_context_info = f"\nInformación general del sistema: {json.dumps(basic_context['data'], ensure_ascii=False)}"
            
            user_prompt = f"""
            Usuario pregunta: {request.user_message}
            {entities_info}
            {basic_context_info}
            
            Contexto disponible:
            {json.dumps(context_data, indent=2, ensure_ascii=False)}
            
            Proporciona una respuesta útil y contextualizada para el usuario de Control de Gestión de Banca March.
            Si hay datos específicos disponibles, úsalos. Si no hay datos suficientes, explica qué información adicional sería útil.
            """
            
            # Llamar a Azure OpenAI con deployment correcto
            client = iniciar_agente_llm()
            deployment_id = settings.AZURE_OPENAI_DEPLOYMENT_ID
            
            response = client.chat.completions.create(
                model=deployment_id,
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
                'basic_context': basic_context,  # 🆕 NUEVO
                'entities_detected': parsed_query['entities'] if parsed_query else {},
                'analysis_type': 'general_chat_enhanced',
                'data_sources': ['azure_openai', 'basic_queries'] if basic_context else ['azure_openai']
            }
            
        except Exception as e:
            logger.error(f"Error en conversación general: {e}")
            return {"error": f"Error procesando conversación: {str(e)}"}

    async def _get_relevant_context_enhanced(self, user_message: str, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """🚀 MEJORADO: Obtiene contexto relevante usando entidades extraídas y basic_queries"""
        context = {}
        
        try:
            periodo_actual = datetime.now().strftime('%Y-%m')
            
            # Si hay entidades específicas, obtener contexto relacionado
            if parsed_query and parsed_query.get('entities'):
                entities = parsed_query['entities']
                
                # Contexto de gestor específico
                if 'gestor_id_extracted' in entities:
                    gestor_id = entities['gestor_id_extracted']
                    gestor_data = self.gestor_queries.get_gestor_performance_enhanced(gestor_id, periodo_actual)
                    if gestor_data and gestor_data.row_count > 0:
                        context['gestor_especifico'] = gestor_data.data[0]
                
                # Contexto de centro específico
                if 'centro_id' in entities:
                    centro_id = entities['centro_id']
                    gestores_centro = self.gestor_queries.get_gestores_by_centro_enhanced(centro_id, periodo_actual)
                    if gestores_centro and hasattr(gestores_centro, 'data'):
                        context['gestores_centro'] = gestores_centro.data[:3]  # Top 3
                
                # Contexto de segmento específico
                if 'segmento_id' in entities:
                    segmento_id = entities['segmento_id']
                    gestores_segmento = self.gestor_queries.get_gestores_by_segmento_enhanced(segmento_id, periodo_actual)
                    if gestores_segmento and hasattr(gestores_segmento, 'data'):
                        context['gestores_segmento'] = gestores_segmento.data[:3]  # Top 3
            
            # Contexto general
            ranking_general = self.comparative_queries.ranking_gestores_por_margen_enhanced(periodo_actual)
            if ranking_general and hasattr(ranking_general, 'data') and ranking_general.data:
                context['top_performers'] = ranking_general.data[:3]
            
            # Alertas recientes
            alertas_recientes = self.deviation_queries.detect_precio_desviaciones_criticas_enhanced(periodo_actual, 20.0)
            if alertas_recientes and hasattr(alertas_recientes, 'data') and alertas_recientes.data:
                context['alertas_activas'] = len(alertas_recientes.data)
                
        except Exception as e:
            logger.warning(f"Error obteniendo contexto mejorado: {e}")
        
        return context

    # RESTO DE MÉTODOS EXISTENTES (sin cambios)
    # [Mantener todos los demás métodos del cdg_agent.py original...]

    async def _handle_deviation_analysis(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja análisis de desviaciones"""
        logger.info("⚠️ Procesando análisis de desviaciones...")
        
        try:
            desviaciones_precio = self.deviation_queries.detect_precio_desviaciones_criticas_enhanced(request.periodo, 15.0)
            anomalias_margen = self.deviation_queries.analyze_margen_anomalies_enhanced(request.periodo, 2.0)
            outliers_volumen = self.deviation_queries.identify_volumen_outliers_enhanced(request.periodo, 3.0)
            patrones_temporales = self.deviation_queries.detect_patron_temporal_anomalias_enhanced(None, 6)
            
            return {
                'desviaciones_precio': desviaciones_precio.data if desviaciones_precio and hasattr(desviaciones_precio, 'data') else [],
                'anomalias_margen': anomalias_margen.data if anomalias_margen and hasattr(anomalias_margen, 'data') else [],
                'outliers_volumen': outliers_volumen.data if outliers_volumen and hasattr(outliers_volumen, 'data') else [],
                'patrones_temporales': patrones_temporales.data if patrones_temporales and hasattr(patrones_temporales, 'data') else [],
                'kpi_data': {'deviation_analysis': True},  # Para activar generación de gráficos
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
                try:
                    incentivos_gestor = self.incentive_queries.calculate_incentive_impact_enhanced(request.gestor_id, request.periodo)
                    simulacion = self.incentive_queries.simulate_incentive_scenarios_enhanced(request.gestor_id, request.periodo)
                except AttributeError:
                    incentivos_gestor = type('EmptyResult', (), {'data': []})()
                    simulacion = type('EmptyResult', (), {'data': []})()
                
                return {
                    'incentivos_gestor': incentivos_gestor.data if incentivos_gestor and hasattr(incentivos_gestor, 'data') else [],
                    'simulacion_escenarios': simulacion.data if simulacion and hasattr(simulacion, 'data') else [],
                    'kpi_data': {'incentive_individual': True},  # Para activar generación de gráficos
                    'analysis_type': 'incentive_analysis_individual',
                    'gestor_id': request.gestor_id
                }
            else:
                ranking_incentivos = self.incentive_queries.ranking_incentivos_periodo_enhanced(request.periodo)
                try:
                    impacto_desviaciones = self.incentive_queries.analyze_deviation_impact_on_incentives_enhanced(request.periodo)
                except AttributeError:
                    impacto_desviaciones = type('EmptyResult', (), {'data': []})()
                
                return {
                    'ranking_incentivos': ranking_incentivos.data if ranking_incentivos and hasattr(ranking_incentivos, 'data') else [],
                    'impacto_desviaciones': impacto_desviaciones.data if impacto_desviaciones and hasattr(impacto_desviaciones, 'data') else [],
                    'kpi_data': {'incentive_general': True},  # Para activar generación de gráficos
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
            
            gestor_data = self.gestor_queries.get_gestor_performance_enhanced(request.gestor_id, request.periodo)
            if not gestor_data or gestor_data.row_count == 0:
                return {"error": "No se encontraron datos para el gestor especificado"}
            
            gestor_info = gestor_data.data[0]
            kpi_analysis = self.kpi_calculator.calculate_kpis_from_data(gestor_info)
            deviation_alerts = self.deviation_queries.detect_precio_desviaciones_criticas_enhanced(request.periodo, 15.0)
            comparative_data = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
            
            business_review = self.report_generator.generate_business_review(
                gestor_data=gestor_info,
                kpi_data=kpi_analysis,
                period=request.periodo,
                deviation_alerts=deviation_alerts.data if deviation_alerts and hasattr(deviation_alerts, 'data') else None,
                comparative_data=comparative_data.data if comparative_data and hasattr(comparative_data, 'data') else None
            )
            
            return {
                'business_review': business_review.to_dict(),
                'kpi_data': kpi_analysis,  # Para activar generación de gráficos
                'analysis_type': 'business_review_complete'
            }
            
        except Exception as e:
            logger.error(f"Error generando Business Review: {e}")
            return {"error": f"Error generando Business Review: {str(e)}"}

    async def _handle_executive_summary(self, request: CDGRequest) -> Dict[str, Any]:
        """Maneja generación de Executive Summary"""
        logger.info("📈 Generando Executive Summary...")
        
        try:
            ranking_gestores = self.comparative_queries.ranking_gestores_por_margen_enhanced(request.periodo)
            desviaciones_criticas = self.deviation_queries.detect_precio_desviaciones_criticas_enhanced(request.periodo, 25.0)
            
            gestores_data = ranking_gestores.data if ranking_gestores and hasattr(ranking_gestores, 'data') else []
            desviaciones_data = desviaciones_criticas.data if desviaciones_criticas and hasattr(desviaciones_criticas, 'data') else []
            
            consolidated_data = {
                'num_gestores': len(gestores_data),
                'margen_promedio': sum(g.get('margen_neto_pct', 0) for g in gestores_data) / len(gestores_data) if gestores_data else 0,
                'alertas_criticas': len(desviaciones_data),
                'periodo': request.periodo
            }
            
            executive_summary = self.report_generator.generate_executive_summary_report(
                consolidated_data, request.periodo
            )
            
            return {
                'executive_summary': executive_summary.to_dict(),
                'consolidated_data': consolidated_data,
                'kpi_data': consolidated_data,  # Para activar generación de gráficos
                'analysis_type': 'executive_summary'
            }
            
        except Exception as e:
            logger.error(f"Error generando Executive Summary: {e}")
            return {"error": f"Error generando Executive Summary: {str(e)}"}

    async def _generate_recommendations(self, content_data: Dict[str, Any], query_type: QueryType) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        try:
            if query_type in [QueryType.GESTOR_ANALYSIS, QueryType.MULTIPLE_GESTOR_ANALYSIS]:
                kpi_data = content_data.get('kpi_data', {})
                resumen_performance = kpi_data.get('resumen_performance', {})
                margen = resumen_performance.get('margen_neto_pct', 0)
                roe = resumen_performance.get('roe_pct', 0)
                
                if margen < 10:
                    recommendations.append("Revisar estrategia de precios y estructura de costos para mejorar margen neto")
                if roe < 8:
                    recommendations.append("Optimizar rentabilidad mediante gestión más eficiente del capital")
                    
            elif query_type == QueryType.DEVIATION_ANALYSIS:
                if content_data.get('desviaciones_precio'):
                    recommendations.append("Atender prioritariamente las desviaciones de precio identificadas")
                if content_data.get('anomalias_margen'):
                    recommendations.append("Investigar causas de las anomalías en márgenes detectadas")
                    
            elif query_type in [QueryType.COMPARATIVE_ANALYSIS, QueryType.CENTRO_ANALYSIS, QueryType.SEGMENTO_ANALYSIS]:
                recommendations.append("Analizar mejores prácticas de los gestores top performer")
                recommendations.append("Implementar plan de mejora para gestores con performance inferior")
            
            elif query_type == QueryType.DATA_EXPLORATION:
                recommendations.append("Explorar datos específicos de gestores o centros para análisis detallado")
                recommendations.append("Considerar análisis temporal para identificar tendencias")
                
            elif query_type == QueryType.QUICK_SUMMARY:
                recommendations.append("Profundizar en análisis específicos de gestores con performance destacada")
                
            elif query_type == QueryType.CHART_PIVOT:
                recommendations.append("Gráfico actualizado según su solicitud")
            
            # Recomendación general si no hay específicas
            if not recommendations:
                recommendations.append("Continuar seguimiento de KPIs y mantener estrategia actual")
                
        except Exception as e:
            logger.warning(f"Error generando recomendaciones: {e}")
        
        return recommendations

    async def _infer_gestor_from_message(self, user_message: str) -> Any:
        """Infiere el gestor del mensaje del usuario usando basic_queries"""
        try:
            # 🆕 NUEVO: Usar basic_queries para obtener lista de gestores
            gestores_data = []
            if self.basic_queries_available:
                try:
                    gestores_data = self.basic_queries.get_all_gestores()
                    logger.info(f"✅ Obtenidos {len(gestores_data)} gestores de basic_queries")
                except Exception as e:
                    logger.warning(f"Error obteniendo gestores de basic_queries: {e}")
            
            # Fallback a queries tradicionales si basic_queries no está disponible
            if not gestores_data:
                try:
                    gestores_result = self.gestor_queries.get_all_gestores_enhanced()
                    if gestores_result and hasattr(gestores_result, 'data') and gestores_result.data:
                        gestores_data = gestores_result.data
                except Exception as e:
                    logger.warning(f"Error obteniendo gestores de queries tradicionales: {e}")
            
            # Buscar gestor por nombre en el mensaje
            if gestores_data:
                for gestor in gestores_data:
                    gestor_name = gestor.get('desc_gestor', '') or gestor.get('DESC_GESTOR', '')
                    if gestor_name and gestor_name.lower() in user_message.lower():
                        gestor_id = gestor.get('gestor_id') or gestor.get('GESTOR_ID')
                        if gestor_id:
                            return self.gestor_queries.get_gestor_performance_enhanced(gestor_id, None)
                
                # Si no se encuentra por nombre, usar el primer gestor disponible
                primer_gestor = gestores_data[0]
                primer_gestor_id = primer_gestor.get('gestor_id') or primer_gestor.get('GESTOR_ID')
                if primer_gestor_id:
                    return self.gestor_queries.get_gestor_performance_enhanced(primer_gestor_id, None)
                    
        except Exception as e:
            logger.warning(f"Error infiriendo gestor: {e}")
        
        return None

    def _get_modules_used(self, query_type: QueryType) -> List[str]:
        """Retorna los módulos utilizados para un tipo de consulta"""
        module_mapping = {
            QueryType.GESTOR_ANALYSIS: ['gestor_queries', 'kpi_calculator', 'incentive_queries', 'chart_generator', 'basic_queries'],
            QueryType.COMPARATIVE_ANALYSIS: ['comparative_queries', 'kpi_calculator', 'chart_generator', 'basic_queries'],
            QueryType.MULTIPLE_GESTOR_ANALYSIS: ['gestor_queries', 'kpi_calculator', 'comparative_queries', 'chart_generator', 'basic_queries'],
            QueryType.CENTRO_ANALYSIS: ['gestor_queries', 'comparative_queries', 'kpi_calculator', 'chart_generator', 'basic_queries'],
            QueryType.SEGMENTO_ANALYSIS: ['gestor_queries', 'comparative_queries', 'kpi_calculator', 'chart_generator', 'basic_queries'],
            QueryType.DEVIATION_ANALYSIS: ['deviation_queries', 'kpi_calculator', 'chart_generator'],
            QueryType.INCENTIVE_ANALYSIS: ['incentive_queries', 'kpi_calculator', 'chart_generator'],
            QueryType.BUSINESS_REVIEW: ['report_generator', 'chart_generator', 'kpi_calculator'],
            QueryType.EXECUTIVE_SUMMARY: ['report_generator', 'comparative_queries', 'deviation_queries', 'chart_generator'],
            QueryType.CHART_PIVOT: ['chart_generator', 'query_parser'],
            QueryType.QUICK_SUMMARY: ['basic_queries', 'chart_generator'],  # 🆕 NUEVO
            QueryType.DATA_EXPLORATION: ['basic_queries', 'chart_generator'],  # 🆕 NUEVO
            QueryType.GENERAL_CHAT: ['azure_openai', 'prompts', 'query_parser', 'basic_queries']
        }
        return module_mapping.get(query_type, [])

    def _get_data_sources(self, query_type: QueryType) -> List[str]:
        """Retorna las fuentes de datos utilizadas"""
        data_sources = ['BM_CONTABILIDAD_CDG.db']
        
        if query_type in [QueryType.BUSINESS_REVIEW, QueryType.EXECUTIVE_SUMMARY, QueryType.GENERAL_CHAT]:
            data_sources.append('Azure_OpenAI_GPT4')
        
        if query_type == QueryType.CHART_PIVOT:
            data_sources.append('QueryIntegratedChartGenerator')
        
        # 🆕 NUEVO: Agregar basic_queries como fuente de datos
        if query_type in [QueryType.QUICK_SUMMARY, QueryType.DATA_EXPLORATION, QueryType.CENTRO_ANALYSIS, 
                         QueryType.GESTOR_ANALYSIS, QueryType.COMPARATIVE_ANALYSIS, QueryType.MULTIPLE_GESTOR_ANALYSIS]:
            data_sources.append('basic_queries')
        
        return data_sources

    def _update_conversation_history(self, request: CDGRequest, response: CDGResponse):
        """Actualiza el historial de conversación para aprendizaje continuo"""
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': request.user_message,
            'response_type': response.response_type.value,
            'confidence': response.confidence_score,
            'execution_time': response.execution_time,
            'user_id': request.user_id,
            'charts_generated': len(response.charts),
            'chart_interaction': request.chart_interaction_type is not None,
            'basic_queries_used': response.basic_queries_used,  # 🆕 NUEVO
            'quick_mode': request.quick_mode  # 🆕 NUEVO
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
            created_at=datetime.now(),
            chart_configs=[],
            pivot_suggestions=[],
            basic_queries_used=False,
            data_sources=[]
        )

    # 🆕 NUEVOS MÉTODOS PÚBLICOS PARA BASIC QUERIES

    async def generate_chart_from_data(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Método público para generar gráficos desde datos"""
        try:
            return create_chart_from_query_data(data, config)
        except Exception as e:
            logger.error(f"Error generando gráfico desde datos: {e}")
            return {"error": str(e)}
        
    async def handle_chart_change_with_prompt(self, user_message: str, current_config: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """✅ NUEVO: Método público para cambios de gráfico usando el prompt integrado del sistema"""
        try:
            full_context = {
                'agente': 'CDG',
                'sistema': 'Control de Gestión Banca March',
                **(context or {})
            }
            
            return self.chart_change_handler(
                user_message=user_message,
                current_chart_config=current_config,
                context=full_context
            )
        except Exception as e:
            logger.error(f"Error en cambio de gráfico con prompt: {e}")
            # Fallback al método tradicional
            return await self.pivot_chart(user_message, current_config)


    async def pivot_chart(self, user_message: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Método público para pivoteo conversacional de gráficos"""
        try:
            return pivot_chart_with_query_integration(user_message, current_config)
        except Exception as e:
            logger.error(f"Error en pivoteo de gráfico: {e}")
            return {"status": "error", "message": str(e)}

    async def get_basic_data_summary(self) -> Dict[str, Any]:
        """🆕 NUEVO: Método público para obtener resumen de datos básicos"""
        if self.basic_queries_available:
            return await self.get_quick_summary()
        else:
            return {"error": "Basic queries no disponible"}

    async def get_gestores_list(self) -> List[Dict[str, Any]]:
        """🆕 NUEVO: Método público para obtener lista de gestores"""
        try:
            if self.basic_queries_available:
                return self.basic_queries.get_all_gestores()
            else:
                # Fallback a queries tradicionales
                result = self.gestor_queries.get_all_gestores_enhanced()
                return result.data if result and hasattr(result, 'data') else []
        except Exception as e:
            logger.error(f"Error obteniendo lista de gestores: {e}")
            return []

    async def get_centros_list(self) -> List[Dict[str, Any]]:
        """🆕 NUEVO: Método público para obtener lista de centros"""
        try:
            if self.basic_queries_available:
                return self.basic_queries.get_all_centros()
            else:
                return []
        except Exception as e:
            logger.error(f"Error obteniendo lista de centros: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente con información de basic_queries"""
        uptime = datetime.now() - self.start_time
        
        return {
            'status': 'active',
            'uptime_seconds': uptime.total_seconds(),
            'conversation_count': len(self.conversation_history),
            'modules_loaded': [
                'kpi_calculator', 'chart_generator', 'query_chart_generator', 'report_generator',
                'gestor_queries', 'comparative_queries', 'deviation_queries', 
                'incentive_queries', 'period_queries', 'query_parser', 'basic_queries'  # 🆕 NUEVO
            ],
            'imports_successful': self.imports_successful,
            'period_queries_enhanced': self.period_queries_enhanced,
            'query_parser_available': self.query_parser_available,
            'basic_queries_available': self.basic_queries_available,  # 🆕 NUEVO
            'chart_generator_integrated': True,
            'mode': 'PRODUCTION' if self.imports_successful else 'MOCK',
            'version': '4.0 - Basic Queries Integrated',  # 🆕 NUEVO
            'last_activity': self.conversation_history[-1]['timestamp'] if self.conversation_history else None
        }

    def reset_conversation_history(self):
        """Reinicia el historial de conversación"""
        self.conversation_history = []
        logger.info("🔄 Historial de conversación reiniciado")

    def get_available_periods(self) -> Dict[str, Any]:
        """Obtiene períodos disponibles usando period_queries"""
        try:
            if self.period_queries_enhanced:
                result = self.period_queries.get_available_periods_enhanced()
                return {
                    'periods': result.data if hasattr(result, 'data') else [],
                    'count': result.row_count if hasattr(result, 'row_count') else 0,
                    'enhanced': True
                }
            else:
                periods = ['2025-10', '2025-09', '2025-08']
                return {
                    'periods': [{'periodo': p} for p in periods],
                    'count': len(periods),
                    'enhanced': False
                }
        except Exception as e:
            logger.warning(f"Error obteniendo períodos: {e}")
            return {'periods': [], 'count': 0, 'enhanced': False}

    def get_latest_period(self) -> str:
        """Obtiene el período más reciente"""
        try:
            if self.period_queries_enhanced:
                result = self.period_queries.get_latest_period_enhanced()
                if hasattr(result, 'data') and result.data:
                    return result.data[0].get('periodo', '2025-10')
            return '2025-10'
        except Exception as e:
            logger.warning(f"Error obteniendo período más reciente: {e}")
            return '2025-10'

    # 🆕 NUEVOS MÉTODOS DE VALIDACIÓN Y DEBUG

    def validate_basic_queries_integration(self) -> Dict[str, Any]:
        """🆕 NUEVO: Valida la integración con basic_queries"""
        try:
            validation_results = {
                'basic_queries_available': self.basic_queries_available,
                'methods_tested': {},
                'overall_status': 'OK'
            }
            
            if self.basic_queries_available:
                # Test método get_resumen_general
                try:
                    resumen = self.basic_queries.get_resumen_general()
                    validation_results['methods_tested']['get_resumen_general'] = {
                        'status': 'OK',
                        'data_keys': list(resumen.keys()) if isinstance(resumen, dict) else 'Not dict'
                    }
                except Exception as e:
                    validation_results['methods_tested']['get_resumen_general'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                
                # Test método get_all_gestores
                try:
                    gestores = self.basic_queries.get_all_gestores()
                    validation_results['methods_tested']['get_all_gestores'] = {
                        'status': 'OK',
                        'count': len(gestores) if isinstance(gestores, list) else 'Not list'
                    }
                except Exception as e:
                    validation_results['methods_tested']['get_all_gestores'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                
                # Test método get_all_centros
                try:
                    centros = self.basic_queries.get_all_centros()
                    validation_results['methods_tested']['get_all_centros'] = {
                        'status': 'OK',
                        'count': len(centros) if isinstance(centros, list) else 'Not list'
                    }
                except Exception as e:
                    validation_results['methods_tested']['get_all_centros'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                
                # Verificar si hay errores
                errors = [test for test in validation_results['methods_tested'].values() 
                         if test.get('status') == 'ERROR']
                
                if errors:
                    validation_results['overall_status'] = 'PARTIAL'
                    if len(errors) == len(validation_results['methods_tested']):
                        validation_results['overall_status'] = 'ERROR'
            
            else:
                validation_results['overall_status'] = 'NOT_AVAILABLE'
                validation_results['message'] = 'Basic queries no está disponible'
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validando integración basic_queries: {e}")
            return {
                'basic_queries_available': False,
                'overall_status': 'ERROR',
                'error': str(e)
            }

    def get_integration_summary(self) -> Dict[str, Any]:
        """🆕 NUEVO: Obtiene resumen completo de integraciones"""
        return {
            'version': '4.0 - Basic Queries Integrated',
            'integrations': {
                'chart_generator': True,
                'basic_queries': self.basic_queries_available,
                'period_queries_enhanced': self.period_queries_enhanced,
                'query_parser': self.query_parser_available,
                'imports_successful': self.imports_successful
            },
            'capabilities': [
                'Análisis de gestores con basic_queries',
                'Gráficos integrados con QueryIntegratedChartGenerator',
                'Pivoteo conversacional de gráficos',
                'Consultas rápidas de exploración de datos',
                'Resúmenes automáticos del sistema',
                'Rankings de gestores por contratos/clientes',
                'Información de centros y distribución',
                'Análisis comparativos mejorados'
            ],
            'data_sources': [
                'BM_CONTABILIDAD_CDG.db',
                'basic_queries' if self.basic_queries_available else 'basic_queries (mock)',
                'Azure_OpenAI_GPT4',
                'QueryIntegratedChartGenerator'
            ]
        }

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
        include_recommendations=kwargs.get('include_recommendations', True),
        current_chart_config=kwargs.get('current_chart_config'),
        chart_interaction_type=kwargs.get('chart_interaction_type'),
        use_basic_queries=kwargs.get('use_basic_queries', True),  # 🆕 NUEVO
        quick_mode=kwargs.get('quick_mode', False)  # 🆕 NUEVO
    )
    
    response = await agent.process_request(request)
    return response.to_dict()

# 🆕 NUEVA FUNCIÓN: Procesamiento rápido con basic_queries
async def process_quick_query(user_message: str, **kwargs) -> Dict[str, Any]:
    """
    🆕 NUEVA: Función para procesamiento rápido usando basic_queries
    
    Args:
        user_message: Mensaje del usuario
        **kwargs: Parámetros adicionales
        
    Returns:
        Dict con respuesta rápida
    """
    return await process_cdg_request(
        user_message,
        quick_mode=True,
        use_basic_queries=True,
        include_charts=kwargs.get('include_charts', False),
        **kwargs
    )

if __name__ == "__main__":
    # Demo y tests básicos del agente CDG con basic_queries
    import asyncio
    
    async def demo_cdg_agent_with_basic_queries():
        """Demostración del agente CDG V4.0 con Chart Generator y Basic Queries integrados"""
        print("🚀 Iniciando demo del CDG Agent V4.0 con Chart Generator y Basic Queries...")
        
        agent = create_cdg_agent()
        
        # Mostrar estado de integraciones
        print(f"\n📊 Estado de integraciones:")
        integration_summary = agent.get_integration_summary()
        for key, value in integration_summary.items():
            print(f"  {key}: {value}")
        
        # Validar integración de basic_queries
        print(f"\n🔍 Validando integración de basic_queries:")
        validation = agent.validate_basic_queries_integration()
        print(f"  Estado general: {validation['overall_status']}")
        if 'methods_tested' in validation:
            for method, result in validation['methods_tested'].items():
                print(f"  {method}: {result['status']}")
        
        # Test casos de uso mejorados con basic_queries
        test_cases = [
            {
                "message": "Dame un resumen general del sistema",
                "description": "Test básico de resumen con basic_queries",
                "use_basic_queries": True,
                "quick_mode": True
            },
            {
                "message": "¿Cuántos gestores tenemos?",
                "description": "Test consulta rápida",
                "use_basic_queries": True,
                "quick_mode": True
            },
            {
                "message": "Ranking de gestores por contratos",
                "description": "Test ranking con basic_queries",
                "use_basic_queries": True
            },
            {
                "message": "¿Cómo está el performance del gestor 18?",
                "gestor_id": "18",
                "periodo": "2025-10",
                "description": "Test análisis tradicional de gestor"
            },
            {
                "message": "Información de centros",
                "description": "Test análisis de centros con basic_queries",
                "use_basic_queries": True
            },
            {
                "message": "Cambia el gráfico a barras horizontales",
                "current_chart_config": {"chart_type": "pie", "dimension": "gestor", "metric": "ROE"},
                "description": "Test pivoteo conversacional"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['description']} ---")
            print(f"📝 Mensaje: {test_case['message']}")
            
            request = CDGRequest(
                user_message=test_case["message"],
                gestor_id=test_case.get("gestor_id"),
                periodo=test_case.get("periodo"),
                user_id="demo_user",
                current_chart_config=test_case.get("current_chart_config"),
                use_basic_queries=test_case.get("use_basic_queries", True),
                quick_mode=test_case.get("quick_mode", False)
            )
            
            try:
                response = await agent.process_request(request)
                print(f"✅ Tipo: {response.response_type.value}")
                print(f"⏱️ Tiempo: {response.execution_time:.2f}s")
                print(f"🎯 Confianza: {response.confidence_score:.2f}")
                print(f"📊 Gráficos: {len(response.charts)}")
                print(f"🔧 Configuraciones: {len(response.chart_configs)}")
                print(f"💡 Recomendaciones: {len(response.recommendations)}")
                print(f"🔄 Sugerencias pivoteo: {len(response.pivot_suggestions)}")
                print(f"🚀 Basic queries usado: {response.basic_queries_used}")
                print(f"📚 Fuentes de datos: {response.data_sources}")
                
                if response.content.get('error'):
                    print(f"❌ Error: {response.content['error']}")
                elif response.basic_queries_used and 'data' in response.content:
                    print(f"📈 Datos obtenidos: {response.content.get('type', 'N/A')}")
                    
            except Exception as e:
                print(f"❌ Error en test case {i}: {e}")
        
        # Mostrar estado final del agente
        print(f"\n📊 Estado final del agente:")
        status = agent.get_agent_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\n🎯 Demo V4.0 completado exitosamente con Basic Queries integrado!")

    # Ejecutar demo
    asyncio.run(demo_cdg_agent_with_basic_queries())
