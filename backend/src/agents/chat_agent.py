"""
Chat Agent Universal v10.0 - Agente Conversacional CDG Completo
===============================================================

Agente completamente mejorado que maneja CUALQUIER consulta sobre control de gestión mediante:
- Sistema de clasificación inteligente con prompts catalogados  
- Búsqueda automática en queries predefinidas (6 catálogos)
- Generación SQL dinámica con contexto bancario completo
- Respuestas contextuales sin SQL para preguntas generales
- Integración completa con CDG Agent para análisis complejos
- Soporte completo para gráficos y visualizaciones

Versión: 10.0 - Integración Completa con Catálogos de Queries
Autor: CDG Development Team  
Fecha: 2025-09-11
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import asyncio

# Configuración
try:
    from config import settings
except ImportError:
    class MockSettings:
        DATABASE_PATH = "database/BM_CONTABILIDAD_CDG.db"
        AZURE_OPENAI_DEPLOYMENT_ID = "gpt-4"
        DATABASE_TIMEOUT = 30
    settings = MockSettings()

# Importaciones con fallbacks
try:
    from utils.initial_agent import iniciar_agente_llm
    from agents.cdg_agent import create_cdg_agent, CDGRequest
    from tools.sql_guard import is_query_safe
    from tools.chart_generator import (
        QueryIntegratedChartGenerator,
        handle_chart_change_request
    )
    from database.db_connection import query_executor
    from prompts.system_prompts import (
        CHAT_CONVERSATIONAL_SYSTEM_PROMPT,
        CHAT_INTENT_CLASSIFICATION_PROMPT,
        CHAT_NATURAL_RESPONSE_SYSTEM_PROMPT,
        CHAT_FINANCIAL_ANALYSIS_SYSTEM_PROMPT,
        CHAT_SQL_GENERATION_SYSTEM_PROMPT,
        # 🎯 NUEVOS CATÁLOGOS DE QUERIES INTEGRADOS
        BASIC_QUERIES_CATALOG_PROMPT,
        COMPARATIVE_QUERIES_CATALOG_PROMPT,
        DEVIATION_QUERIES_CATALOG_PROMPT,
        GESTOR_QUERIES_CATALOG_PROMPT,
        INCENTIVE_QUERIES_CATALOG_PROMPT,
        PERIOD_QUERIES_CATALOG_PROMPT
    )
    from prompts.user_prompts import (
        build_intent_classification_prompt,
        build_natural_response_prompt,
        build_sql_generation_prompt,
        build_financial_explanation_prompt
    )
    # 🎯 IMPORTACIÓN DE TODAS LAS QUERIES PREDEFINIDAS
    from queries.basic_queries import basic_queries
    from queries.comparative_queries import ComparativeQueries
    from queries.deviation_queries import DeviationQueries
    from queries.gestor_queries import GestorQueries
    from queries.incentive_queries import IncentiveQueries
    from queries.period_queries import PeriodQueries
    
    IMPORTS_SUCCESSFUL = True
    logger = logging.getLogger(__name__)
    mode = "PRODUCTION" if IMPORTS_SUCCESSFUL else "FALLBACK"
    print(f"\n{'='*60}")
    print(f"🚀 CHAT AGENT v10.0 INICIALIZADO")
    print(f"   Modo: {mode}")
    print(f"   Imports: {'✅ Exitosos' if IMPORTS_SUCCESSFUL else '⚠️ Fallback'}")
    print(f"   Catálogos: {'✅ 6 catálogos cargados' if IMPORTS_SUCCESSFUL else '⚠️ Mock'}")
    print(f"   Query Engines: {'✅ Disponibles' if IMPORTS_SUCCESSFUL else '⚠️ Mock'}")
    print(f"{'='*60}\n")
    logger.info(f"🚀 Chat Agent v10.0 inicializado - Modo: {mode}")

    
except ImportError as e:
    logging.warning(f"Modo fallback activado: {e}")
    IMPORTS_SUCCESSFUL = False
    
    # Fallbacks básicos necesarios...
    def iniciar_agente_llm():
        class MockLLM:
            class Chat:
                class Completions:
                    def create(self, **kwargs):
                        return type('Response', (), {
                            'choices': [type('Choice', (), {
                                'message': type('Message', (), {
                                    'content': '{"intent": "general_query", "requires_sql": true, "confidence": 0.8}'
                                })()
                            })()]
                        })()
                completions = Completions()
            chat = Chat()
        return MockLLM()
    
    def create_cdg_agent():
        class MockCDGAgent:
            async def process_request(self, req):
                return type('Response', (), {
                    'content': 'Mock CDG response',
                    'charts': [],
                    'recommendations': []
                })()
        return MockCDGAgent()
    
    class MockQueryExecutor:
        def execute_query(self, query, params=None, fetch_type="all"):
            return [{"mock": "data"}]
        def get_table_info(self, table_name):
            return [{'name': 'ID', 'type': 'INTEGER'}]
        def get_table_count(self, table_name):
            return 100
    
    query_executor = MockQueryExecutor()
    
    # Mock prompts y catálogos básicos
    CHAT_CONVERSATIONAL_SYSTEM_PROMPT = "Eres un asistente financiero especializado en Control de Gestión bancario."
    CHAT_INTENT_CLASSIFICATION_PROMPT = "Clasifica la intención del usuario en formato JSON."
    CHAT_NATURAL_RESPONSE_SYSTEM_PROMPT = "Genera respuestas naturales y profesionales."
    CHAT_SQL_GENERATION_SYSTEM_PROMPT = "Genera consultas SQL seguras para base de datos financiera."
    
    # Mock catálogos
    BASIC_QUERIES_CATALOG_PROMPT = "Catálogo básico de queries"
    COMPARATIVE_QUERIES_CATALOG_PROMPT = "Catálogo comparativo de queries"
    DEVIATION_QUERIES_CATALOG_PROMPT = "Catálogo de desviaciones"
    GESTOR_QUERIES_CATALOG_PROMPT = "Catálogo de gestores"
    INCENTIVE_QUERIES_CATALOG_PROMPT = "Catálogo de incentivos"
    PERIOD_QUERIES_CATALOG_PROMPT = "Catálogo de períodos"
    
    # Mock functions
    def build_intent_classification_prompt(message, context):
        return f"Clasifica: {message}"
    
    def build_natural_response_prompt(data, query, context):
        return f"Respuesta para: {query} con datos: {data}"
    
    def build_sql_generation_prompt(message, context):
        return f"SQL para: {message}"

logger = logging.getLogger(__name__)

# ============================================================================
# 🎯 CLASIFICADOR INTELIGENTE CON CATÁLOGOS INTEGRADOS
# ============================================================================

class IntelligentQueryClassifier:
    """
    🎯 CLASIFICADOR MEJORADO que decide el flujo óptimo:
    1. ¿Necesita SQL? 
    2. ¿Existe query predefinida?
    3. ¿Requiere análisis CDG?
    4. ¿Es respuesta contextual?
    """
    
    def __init__(self):
        self.llm_client = iniciar_agente_llm()
        # 🎯 CATÁLOGOS DE QUERIES INTEGRADOS
        self.query_catalogs = {
            'basic': BASIC_QUERIES_CATALOG_PROMPT,
            'comparative': COMPARATIVE_QUERIES_CATALOG_PROMPT,
            'deviation': DEVIATION_QUERIES_CATALOG_PROMPT,
            'gestor': GESTOR_QUERIES_CATALOG_PROMPT,
            'incentive': INCENTIVE_QUERIES_CATALOG_PROMPT,
            'period': PERIOD_QUERIES_CATALOG_PROMPT
        }
        
        # 🎯 INSTANCIAS DE QUERIES PREDEFINIDAS
        self.query_engines = {
            'basic': basic_queries if IMPORTS_SUCCESSFUL else None,
            'comparative': ComparativeQueries() if IMPORTS_SUCCESSFUL else None,
            'deviation': DeviationQueries() if IMPORTS_SUCCESSFUL else None,
            'gestor': GestorQueries() if IMPORTS_SUCCESSFUL else None,
            'incentive': IncentiveQueries() if IMPORTS_SUCCESSFUL else None,
            'period': PeriodQueries() if IMPORTS_SUCCESSFUL else None
        }

    
    async def classify_and_route(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """
        🎯 CLASIFICACIÓN Y ENRUTAMIENTO INTELIGENTE
        """
        try:
            # 1️⃣ CLASIFICACIÓN INICIAL: ¿Qué tipo de consulta es?
            initial_classification = await self._classify_query_type(user_message, context)
            
            if initial_classification['requires_sql']:
                # 2️⃣ BÚSQUEDA EN QUERIES PREDEFINIDAS
                predefined_match = await self._find_predefined_query(user_message, context)
                
                if predefined_match['found']:
                    return {
                        'flow_type': 'PREDEFINED_QUERY',
                        'classification': initial_classification,
                        'predefined_match': predefined_match,
                        'confidence': predefined_match['confidence']
                    }
                else:
                    return {
                        'flow_type': 'DYNAMIC_SQL',
                        'classification': initial_classification,
                        'confidence': initial_classification['confidence']
                    }
            
            elif initial_classification['requires_cdg_agent']:
                return {
                    'flow_type': 'CDG_AGENT',
                    'classification': initial_classification,
                    'confidence': initial_classification['confidence']
                }
            
            else:
                return {
                    'flow_type': 'CONTEXTUAL_RESPONSE',
                    'classification': initial_classification,
                    'confidence': initial_classification['confidence']
                }
                
        except Exception as e:
            logger.error(f"Error en clasificación: {e}")
            return {
                'flow_type': 'DYNAMIC_SQL',
                'classification': {'intent': 'fallback', 'requires_sql': True},
                'confidence': 0.3
            }
    
    async def _classify_query_type(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """
        🎯 CLASIFICACIÓN INICIAL: Determina si necesita SQL, CDG Agent o respuesta contextual
        """
        try:
            classification_prompt = f"""
            Analiza esta consulta de control de gestión bancario y clasifícala:

            CONSULTA: "{user_message}"

            Responde en JSON con esta estructura:
            {{
                "intent": "tipo_de_consulta",
                "requires_sql": true/false,
                "requires_cdg_agent": true/false,
                "complexity": "simple/medium/complex",
                "confidence": 0.0-1.0,
                "reasoning": "explicación"
            }}

            CRITERIOS:
            - requires_sql: true si necesita datos específicos de la BD
            - requires_cdg_agent: true si requiere análisis complejo/comparativo/explicativo
            - Si es pregunta conceptual/general → requires_sql: false

            EJEMPLOS:
            - "¿Cuántos gestores hay?" → requires_sql: true, requires_cdg_agent: false
            - "Analiza el performance del gestor 5" → requires_sql: true, requires_cdg_agent: true  
            - "¿Qué es el margen neto?" → requires_sql: false, requires_cdg_agent: false
            """
            
            if IMPORTS_SUCCESSFUL:
                response = self.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": CHAT_INTENT_CLASSIFICATION_PROMPT},
                        {"role": "user", "content": classification_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                
                result_text = response.choices[0].message.content.strip()
                return self._parse_classification_response(result_text)
            else:
                return self._fallback_classification(user_message)
                
        except Exception as e:
            logger.error(f"Error en clasificación inicial: {e}")
            return self._fallback_classification(user_message)
    
    async def _find_predefined_query(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """
        🎯 BÚSQUEDA INTELIGENTE EN QUERIES PREDEFINIDAS
        Busca en los 6 catálogos para encontrar la query más apropiada
        """
        try:
            # Construir prompt con todos los catálogos
            all_catalogs = "\n\n".join([
                f"=== {catalog_name.upper()} ===\n{catalog_content}"
                for catalog_name, catalog_content in self.query_catalogs.items()
            ])
            
            search_prompt = f"""
            Busca en estos catálogos la función más apropiada para esta consulta:

            CONSULTA: "{user_message}"

            CATÁLOGOS DISPONIBLES:
            {all_catalogs}

            Responde en JSON:
            {{
                "found": true/false,
                "catalog": "nombre_del_catalogo",
                "function_name": "nombre_funcion_exacto",
                "parameters": {{}},
                "confidence": 0.0-1.0,
                "reasoning": "explicación"
            }}

            IMPORTANTE:
            - Si encuentras una función que coincida ≥70%, found: true
            - Usa el nombre EXACTO de la función del catálogo
            - Si no hay coincidencia clara, found: false
            """
            
            if IMPORTS_SUCCESSFUL:
                response = self.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": "Eres un experto buscador de funciones en catálogos de queries."},
                        {"role": "user", "content": search_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=300
                )
                
                result_text = response.choices[0].message.content.strip()
                return self._parse_predefined_search_response(result_text)
            else:
                return {'found': False, 'confidence': 0.0}
                
        except Exception as e:
            logger.error(f"Error buscando query predefinida: {e}")
            return {'found': False, 'confidence': 0.0}
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea respuesta de clasificación inicial"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return {
                    'intent': result.get('intent', 'general_query'),
                    'requires_sql': result.get('requires_sql', True),
                    'requires_cdg_agent': result.get('requires_cdg_agent', False),
                    'complexity': result.get('complexity', 'medium'),
                    'confidence': float(result.get('confidence', 0.5)),
                    'reasoning': result.get('reasoning', 'Clasificación automática')
                }
        except:
            pass
        
        return self._fallback_classification("")
    
    def _parse_predefined_search_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea respuesta de búsqueda en catálogos"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # ✅ CORRECCIÓN: Limpiar nombre de catálogo
                catalog = result.get('catalog', '').lower()
                # Remover extensiones .py y limpiar
                if '.py' in catalog:
                    catalog = catalog.replace('_queries.py', '').replace('.py', '')
                if catalog.endswith('_queries'):
                    catalog = catalog.replace('_queries', '')
                
                return {
                    'found': result.get('found', False),
                    'catalog': catalog,  # ✅ Catálogo limpio
                    'function_name': result.get('function_name', ''),
                    'parameters': result.get('parameters', {}),
                    'confidence': float(result.get('confidence', 0.0)),
                    'reasoning': result.get('reasoning', '')
                }
        except:
            pass
        
        return {'found': False, 'confidence': 0.0}
    
    
    def _fallback_classification(self, user_message: str) -> Dict[str, Any]:
        """Clasificación fallback básica por palabras clave"""
        message_lower = user_message.lower() if user_message else ""
        
        if any(word in message_lower for word in ['gráfico', 'chart', 'cambia', 'modifica']):
            return {
                'intent': 'chart_modification',
                'requires_sql': False,
                'requires_cdg_agent': False,
                'complexity': 'simple',
                'confidence': 0.8,
                'reasoning': 'Modificación de gráfico detectada'
            }
        
        elif any(word in message_lower for word in ['análisis', 'explica', 'por qué', 'compara']):
            return {
                'intent': 'analysis_request',
                'requires_sql': True,
                'requires_cdg_agent': True,
                'complexity': 'complex',
                'confidence': 0.7,
                'reasoning': 'Análisis complejo detectado'
            }
        
        elif any(word in message_lower for word in ['qué es', 'define', 'concepto', 'significa']):
            return {
                'intent': 'conceptual_query',
                'requires_sql': False,
                'requires_cdg_agent': False,
                'complexity': 'simple',
                'confidence': 0.8,
                'reasoning': 'Pregunta conceptual detectada'
            }
        
        else:
            return {
                'intent': 'data_query',
                'requires_sql': True,
                'requires_cdg_agent': False,
                'complexity': 'medium',
                'confidence': 0.6,
                'reasoning': 'Consulta de datos general'
            }

# ============================================================================
# 🎯 EJECUTOR DE QUERIES PREDEFINIDAS
# ============================================================================

class PredefinedQueryExecutor:
    """
    🎯 EJECUTOR que puede llamar a CUALQUIER función de los 6 catálogos de queries
    """
    
    def __init__(self):
        self.query_engines = {
            'basic': basic_queries if IMPORTS_SUCCESSFUL else None,
            'comparative': ComparativeQueries() if IMPORTS_SUCCESSFUL else None,  # Con ()
            'deviation': DeviationQueries() if IMPORTS_SUCCESSFUL else None,      # Con ()
            'gestor': GestorQueries() if IMPORTS_SUCCESSFUL else None,            # Con ()
            'incentive': IncentiveQueries() if IMPORTS_SUCCESSFUL else None,      # Con ()
            'period': PeriodQueries() if IMPORTS_SUCCESSFUL else None             # Con ()
        }
    
    async def execute_predefined_query(self, match_info: Dict[str, Any], user_message: str, context: Dict = None) -> Dict[str, Any]:
        """
        🎯 EJECUTA la query predefinida identificada por el clasificador
        """
        try:
            catalog = match_info.get('catalog', '').lower()
            function_name = match_info.get('function_name', '')
            parameters = match_info.get('parameters', {})
            
            logger.info(f"🎯 Ejecutando query predefinida: {catalog}.{function_name}")
            
            # Obtener el engine correcto
            engine = self.query_engines.get(catalog)
            if not engine:
                logger.error(f"Engine no encontrado para catálogo: {catalog}")
                return {
                    'success': False,
                    'error': f'Catálogo {catalog} no disponible',
                    'data': None
                }
            
            # Obtener la función
            if not hasattr(engine, function_name):
                logger.error(f"Función no encontrada: {function_name} en {catalog}")
                return {
                    'success': False,
                    'error': f'Función {function_name} no existe en {catalog}',
                    'data': None
                }
            
            query_function = getattr(engine, function_name)
            
            # 🎯 PARÁMETROS INTELIGENTES basados en contexto
            enhanced_params = self._enhance_parameters(parameters, context, user_message)
            
            # Ejecutar la función
            if callable(query_function):
                if enhanced_params:
                    result = query_function(**enhanced_params)
                else:
                    result = query_function()
                
                return {
                    'success': True,
                    'data': result.data if hasattr(result, 'data') else result,
                    'metadata': {
                        'catalog': catalog,
                        'function': function_name,
                        'parameters_used': enhanced_params,
                        'execution_time': getattr(result, 'execution_time', 0),
                        'row_count': getattr(result, 'row_count', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'{function_name} no es ejecutable',
                    'data': None
                }
                
        except Exception as e:
            logger.error(f"Error ejecutando query predefinida: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def _enhance_parameters(self, base_params: Dict, context: Dict, user_message: str) -> Dict[str, Any]:
        """
        🎯 ENRIQUECE los parámetros con contexto inteligente
        """
        enhanced = base_params.copy()
        
        # Período inteligente
        if 'periodo' not in enhanced and context:
            enhanced['periodo'] = context.get('periodo') or self._extract_period_from_message(user_message)
        
        # Gestor ID
        if 'gestor_id' not in enhanced and context:
            enhanced['gestor_id'] = context.get('gestor_id')
        
        # Umbrales por defecto
        if 'umbral' not in enhanced and any(word in user_message.lower() for word in ['desviación', 'threshold']):
            enhanced['umbral'] = 15.0
        
        # Limpiar parámetros None
        return {k: v for k, v in enhanced.items() if v is not None}
    
    def _extract_period_from_message(self, user_message: str) -> Optional[str]:
        """Extrae período del mensaje del usuario"""
        import re
        
        # Buscar patrones YYYY-MM
        period_pattern = r'20\d{2}-\d{2}'
        match = re.search(period_pattern, user_message)
        if match:
            return match.group(0)
        
        # Palabras clave para períodos
        if 'octubre' in user_message.lower():
            return '2025-10'
        elif 'septiembre' in user_message.lower():
            return '2025-09'
        
        return '2025-10'  # Default actual

# ============================================================================
# INSPECTOR DINÁMICO DE ESQUEMA DE BASE DE DATOS (HEREDADO DEL V9.0)
# ============================================================================

class DatabaseSchemaInspector:
    """Inspector dinámico de esquema - heredado del v9.0"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.schema_cache = {}
        self.cache_timestamp = None
        self.cache_duration = 300  # 5 minutos
    
    def get_database_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Obtiene el esquema completo de la base de datos dinámicamente"""
        try:
            current_time = datetime.now()
            if (not force_refresh and 
                self.schema_cache and 
                self.cache_timestamp and 
                (current_time - self.cache_timestamp).seconds < self.cache_duration):
                return self.schema_cache
            
            logger.info("🔍 Inspeccionando esquema de base de datos...")
            
            schema = {
                'tables': {},
                'metadata': {
                    'last_updated': current_time.isoformat(),
                    'total_tables': 0,
                    'total_records': 0
                }
            }
            
            # Obtener todas las tablas
            tables_query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            
            if IMPORTS_SUCCESSFUL:
                tables = query_executor.execute_query(tables_query)
            else:
                tables = [
                    {'name': 'MAESTRO_GESTORES'},
                    {'name': 'MAESTRO_CONTRATOS'},
                    {'name': 'PRECIO_POR_PRODUCTO_REAL'},
                    {'name': 'PRECIO_POR_PRODUCTO_STD'}
                ]
            
            total_records = 0
            
            for table_info in tables:
                table_name = table_info['name']
                table_schema = self._get_table_schema(table_name)
                record_count = self._get_table_count(table_name)
                total_records += record_count
                
                schema['tables'][table_name] = {
                    'columns': table_schema,
                    'record_count': record_count,
                    'description': self._get_table_description(table_name)
                }
            
            schema['metadata']['total_tables'] = len(tables)
            schema['metadata']['total_records'] = total_records
            
            self.schema_cache = schema
            self.cache_timestamp = current_time
            
            logger.info(f"✅ Esquema cargado: {len(tables)} tablas, {total_records} registros totales")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Error inspeccionando esquema: {e}")
            return self._get_fallback_schema()
    
    def _get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        try:
            if IMPORTS_SUCCESSFUL:
                return query_executor.get_table_info(table_name)
            else:
                return [{'name': 'ID', 'type': 'INTEGER'}, {'name': 'DESC', 'type': 'TEXT'}]
        except Exception as e:
            logger.warning(f"Error obteniendo esquema de {table_name}: {e}")
            return []
    
    def _get_table_count(self, table_name: str) -> int:
        try:
            if IMPORTS_SUCCESSFUL:
                return query_executor.get_table_count(table_name)
            else:
                return 100
        except Exception as e:
            logger.warning(f"Error contando registros en {table_name}: {e}")
            return 0
    
    def _get_table_description(self, table_name: str) -> str:
        descriptions = {
            'MAESTRO_GESTORES': 'Catálogo del equipo comercial con especialización por segmento y ubicación',
            'MAESTRO_CONTRATOS': 'Registro central de contratos activos - núcleo del sistema de costes',
            'MAESTRO_CLIENTES': 'Base de datos de clientes activos con asignación comercial',
            'MAESTRO_PRODUCTOS': 'Catálogo de productos financieros con modelo de negocio',
            'MAESTRO_SEGMENTOS': 'Clasificación estratégica de cartera por tipología cliente',
            'MAESTRO_CENTROS': 'Estructura organizativa de centros operativos y de soporte',
            'PRECIO_POR_PRODUCTO_REAL': 'Precios reales mensuales calculados - núcleo control de gestión',
            'PRECIO_POR_PRODUCTO_STD': 'Precios estándar presupuestarios - referencia objetivos',
            'MOVIMIENTOS_CONTRATOS': 'Motor transaccional - registra operaciones financieras en tiempo real',
            'GASTOS_CENTRO': 'Registro mensual gastos directos por centro - base cálculo precios reales',
            'MAESTRO_CUENTAS': 'Plan contable específico para productos financieros',
            'MAESTRO_LINEA_CDR': 'Estructura del Cuadro de Resultados para reporting ejecutivo'
        }
        return descriptions.get(table_name, f'Tabla del sistema de control de gestión: {table_name}')
    
    def _get_fallback_schema(self) -> Dict[str, Any]:
        return {
            'tables': {
                'MAESTRO_GESTORES': {
                    'columns': [{'name': 'GESTOR_ID'}, {'name': 'DESC_GESTOR'}],
                    'record_count': 30,
                    'description': 'Gestores comerciales'
                }
            },
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'total_tables': 1,
                'total_records': 30
            }
        }

# ============================================================================
# QUERY BUILDER DINÁMICO (HEREDADO DEL V9.0 CON MEJORAS)
# ============================================================================

class EnhancedQueryBuilder:
    """Query Builder mejorado con contexto bancario completo"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.schema_inspector = DatabaseSchemaInspector(self.db_path)
        self.llm_client = iniciar_agente_llm()
    
    async def build_sql_for_any_query(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Construye SQL para CUALQUIER consulta con contexto bancario completo"""
        try:
            database_schema = self.schema_inspector.get_database_schema()
            schema_context = self._build_banking_schema_context(database_schema)
            
            sql_generation_prompt = f"""
            Eres un especialista en Control de Gestión de Banca March. Genera SQL considerando nuestra lógica de negocio:
            
            PREGUNTA: "{user_message}"
            
            {schema_context}
            
            🏦 LÓGICA DE NEGOCIO BANCA MARCH:
            
            📊 CÁLCULO DE GASTOS POR CENTRO:
            - USA PRECIO_POR_PRODUCTO_REAL (ya incluye redistribución automática)
            - Fórmula: GastoRedistribuido = GastoCentral × (Contratos_Centro_i / Total_Contratos_Finalistas)
            - Solo centros finalistas (IND_CENTRO_FINALISTA = 1, centros 1-5)
            - Centros soporte (6-8) se redistribuyen automáticamente
            
            💰 PRECIOS POR PRODUCTO:
            - PRECIO_POR_PRODUCTO_REAL: Costes reales mensuales (recalculados cada mes)
            - PRECIO_POR_PRODUCTO_STD: Estándares presupuestarios (fijos todo el año)
            - Desviación crítica: >15% entre real vs estándar
            - Valores NEGATIVOS = costes para el banco
            
            📈 MÁRGENES Y KPIs:
            - Margen Neto = (Ingresos - Gastos) / Ingresos × 100
            - ROE = Beneficio Neto / Patrimonio × 100
            - Eficiencia = Ingresos / Gastos
            
            🎯 ESTRUCTURA ORGANIZATIVA:
            - 5 centros finalistas (1-5) con contratos directos
            - 3 centros soporte (6-8) sin contratos, gastos se redistribuyen
            - 30 gestores especializados por segmento único
            - 5 segmentos: N10101(Minorista), N10102(Privada), N10103(Empresas), N10104(Personal), N20301(Fondos)
            
            📅 PERÍODOS:
            - Actual: 2025-10-01 (FECHA_CALCULO para precios reales)
            - Formato estándar: YYYY-MM
            
            ⚠️ CONSULTAS TÍPICAS:
            - "Gastos por centro" → Usar PRECIO_POR_PRODUCTO_REAL con JOINs correctos
            - "Centros con problemas" → Analizar DESVIACIONES, no valores absolutos
            - "Ranking gestores" → Incluir cálculo de margen real basado en ingresos-gastos
            
            RESPONDE EN JSON:
            {{
                "sql": "SELECT...",
                "explanation": "explicación de la lógica aplicada",
                "tables_used": ["TABLA1", "TABLA2"],
                "intent": "data_query",
                "confidence": 0.8
            }}

            
            IMPORTANTE:
            - SQL válido y ejecutable
            - Usa JOIN apropiados entre tablas relacionadas
            - LIMIT 20 por defecto para consultas exploratorias
            - Maneja casos NULL con COALESCE
            """
            
            if IMPORTS_SUCCESSFUL:
                response = self.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": CHAT_SQL_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": sql_generation_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=600
                )
                
                result_text = response.choices[0].message.content.strip()
                result = self._parse_llm_sql_response(result_text)
            else:
                result = self._generate_fallback_sql(user_message, database_schema)
            
            # Validar seguridad
            sql = result.get('sql', '')
            is_safe = is_query_safe(sql) if IMPORTS_SUCCESSFUL else True
            
            result.update({
                'is_safe': is_safe,
                'generated_at': datetime.now().isoformat(),
                'schema_version': database_schema['metadata']['last_updated']
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error construyendo SQL: {e}")
            return {
                'sql': 'SELECT "Error en construcción de query" as message',
                'explanation': f'Error: {str(e)}',
                'tables_used': [],
                'intent': 'error',
                'confidence': 0.0,
                'is_safe': True
            }
    
    def _build_banking_schema_context(self, schema: Dict[str, Any]) -> str:
        """Construye contexto completo del esquema con enfoque bancario"""
        context_lines = []
        context_lines.append("BASE DE DATOS BM_CONTABILIDAD_CDG - ESQUEMA BANCARIO:")
        context_lines.append(f"Total tablas: {schema['metadata']['total_tables']}")
        context_lines.append(f"Total registros: {schema['metadata']['total_records']}")
        context_lines.append("")
        
        for table_name, table_info in schema['tables'].items():
            columns = table_info.get('columns', [])
            record_count = table_info.get('record_count', 0)
            description = table_info.get('description', '')
            
            context_lines.append(f"TABLA: {table_name}")
            context_lines.append(f"Propósito: {description}")
            context_lines.append(f"Registros: {record_count:,}")
            
            col_info = [f"{col.get('name', 'unknown')} ({col.get('type', 'unknown')})" 
                       for col in columns[:8]]  # Limitar columnas mostradas
            context_lines.append(f"Columnas: {', '.join(col_info)}")
            context_lines.append("")
        
        return '\n'.join(context_lines)
    
    def _parse_llm_sql_response(self, llm_response: str) -> Dict[str, Any]:
        """Parsea respuesta del LLM extrayendo SQL válido"""
        try:
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                sql = result.get('sql', '').strip()
                
                if self._is_complete_sql(sql):
                    return {
                        'sql': sql,
                        'explanation': result.get('explanation', ''),
                        'tables_used': result.get('tables_used', []),
                        'intent': result.get('intent', 'data_query'),
                        'confidence': float(result.get('confidence', 0.8))
                    }
        except:
            pass
        
        return self._generate_fallback_sql("consulta general", {})
    
    def _is_complete_sql(self, sql: str) -> bool:
        """Valida que el SQL sea completo y ejecutable"""
        if not sql or len(sql.strip()) < 10:
            return False
        
        sql_upper = sql.upper().strip()
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            return False
        
        if sql_upper.startswith('SELECT') and 'FROM' not in sql_upper:
            return False
        
        return True
    
    def _generate_fallback_sql(self, user_message: str, schema: Dict) -> Dict[str, Any]:
        """SQL fallback inteligente"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['gestor', 'comercial']):
            return {
                'sql': 'SELECT GESTOR_ID, DESC_GESTOR, CENTRO FROM MAESTRO_GESTORES LIMIT 10',
                'explanation': 'Consulta básica de gestores',
                'tables_used': ['MAESTRO_GESTORES'],
                'intent': 'data_query',
                'confidence': 0.6
            }
        
        return {
            'sql': 'SELECT "Consulta no procesable" as mensaje',
            'explanation': 'No se pudo generar SQL válido',
            'tables_used': [],
            'intent': 'error',
            'confidence': 0.2
        }

# ============================================================================
# FORMATEADOR DE RESPUESTAS NATURALES
# ============================================================================

class BankingResponseFormatter:
    """Formateador especializado en contexto bancario"""
    
    def __init__(self):
        self.llm_client = iniciar_agente_llm()
    
    async def format_response(self, data: Any, query: str, context: Dict = None) -> str:
        """Convierte datos en respuesta natural con contexto bancario"""
        try:
            if not data:
                return "No se encontraron datos para su consulta. ¿Podría proporcionar más detalles específicos sobre el período o gestor de interés?"
    
            # Preparar contexto de forma segura
            safe_data = data if data is not None else []
            safe_query = str(query) if query else "consulta"
            
            banking_prompt = f"""
            Genera una respuesta profesional para esta consulta de Control de Gestión:

            CONSULTA: "{safe_query}"
            DATOS: {safe_data}

            CONTEXTO BANCARIO:
            - Banca March - Departamento de Control de Gestión
            - Enfoque en rentabilidad y eficiencia operativa
            - Audiencia: Directivos y gestores comerciales
            - Estilo: Profesional, directo, con insights accionables

            FORMATO REQUERIDO:
            - Respuesta directa al inicio
            - Datos estructurados con bullets
            - Insights o recomendaciones al final
            - Números con formato bancario (€, %, separadores de miles)
            
            EJEMPLO:
            "📊 **Análisis de Gestores - Octubre 2025**
            
            Se identificaron 25 gestores activos:
            • **Banca Privada:** 8 gestores (32%)
            • **Banca Personal:** 12 gestores (48%)  
            • **Empresas:** 5 gestores (20%)
            
            💡 **Insights:** La concentración en Banca Personal sugiere oportunidades de crecimiento en segmentos premium."
            """
            
            if IMPORTS_SUCCESSFUL:
                response = self.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": CHAT_NATURAL_RESPONSE_SYSTEM_PROMPT},
                        {"role": "user", "content": banking_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=800
                )
                return response.choices[0].message.content.strip()
            else:
                return self._format_fallback(data, query)
    
        except Exception as e:
            logger.error(f"Error formateando respuesta: {e}")
            return f"Se procesaron los datos para '{query}', pero hubo un error en el formateo de la respuesta."
    
    def _format_fallback(self, data: Any, query: str) -> str:
        """Formateo fallback con contexto bancario"""
        if isinstance(data, list) and len(data) > 0:
            return f"📊 **Resultados para:** {query}\n\nSe encontraron **{len(data)} registros** en el sistema de Control de Gestión."
        elif isinstance(data, dict):
            formatted_items = []
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if 'pct' in key.lower() or 'percent' in key.lower():
                        formatted_items.append(f"• **{key.replace('_', ' ').title()}:** {value:.2f}%")
                    elif 'eur' in key.lower() or 'euro' in key.lower():
                        formatted_items.append(f"• **{key.replace('_', ' ').title()}:** {value:,.2f} €")
                    else:
                        formatted_items.append(f"• **{key.replace('_', ' ').title()}:** {value:,.2f}")
                else:
                    formatted_items.append(f"• **{key.replace('_', ' ').title()}:** {value}")
            return f"📊 **Control de Gestión - {query.title()}**\n\n" + "\n".join(formatted_items)
        else:
            return f"📊 **Resultado:** {str(data)}"

# ============================================================================
# DATACLASSES PARA MENSAJES Y RESPUESTAS
# ============================================================================

@dataclass
class ChatMessage:
    user_id: str
    message: str
    gestor_id: Optional[str] = None
    periodo: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    current_chart_config: Optional[Dict[str, Any]] = None
    include_charts: Optional[bool] = True
    include_recommendations: Optional[bool] = True

@dataclass
class ChatResponse:
    response: str
    response_type: str
    data: Optional[Any] = None
    charts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    confidence_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""

@dataclass
class ChatSession:
    user_id: str
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    chart_configs: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# 🚀 AGENTE DE CHAT PRINCIPAL - VERSION 10.0 COMPLETA
# ============================================================================

class UniversalChatAgentV10:
    """
    🚀 Chat Agent Universal v10.0 - VERSIÓN COMPLETA DEFINITIVA
    
    Flujo perfecto implementado:
    consulta_usuario → ¿Necesita SQL?
        ├── SÍ → ¿Existe query predefinida?
        │    ├── SÍ → Usar query predefinida  
        │    └── NO → Generar SQL dinámicamente
        └── NO → Respuesta LLM con contexto bancario
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.sessions: Dict[str, ChatSession] = {}
        
        # 🎯 COMPONENTES PRINCIPALES V10.0
        self.classifier = IntelligentQueryClassifier()
        self.predefined_executor = PredefinedQueryExecutor()
        self.query_builder = EnhancedQueryBuilder(self.db_path)
        self.formatter = BankingResponseFormatter()
        self.llm_client = iniciar_agente_llm()
        # Integraciones externas
        self.cdg_agent = create_cdg_agent() if IMPORTS_SUCCESSFUL else None
        self.chart_generator = None
        if IMPORTS_SUCCESSFUL:
            try:
                self.chart_generator = QueryIntegratedChartGenerator()
            except:
                logger.warning("Chart generator no disponible")
        
        mode = "PRODUCTION" if IMPORTS_SUCCESSFUL else "FALLBACK"
        print(f"\n{'='*60}")
        print(f"🚀 UNIVERSAL CHAT AGENT v10.0 COMPLETO")
        print(f"   Estado: ✅ LISTO")
        print(f"   Modo: {mode}")
        print(f"   Componentes: {'✅ Todos activos' if IMPORTS_SUCCESSFUL else '⚠️ Modo fallback'}")
        print(f"   CDG Integration: {'✅ Conectado' if self.cdg_agent else '❌ No disponible'}")
        print(f"{'='*60}\n")
        logger.info("🚀 Universal Chat Agent v10.0 COMPLETO inicializado exitosamente")

    
    def get_session(self, user_id: str) -> ChatSession:
        """Obtiene o crea sesión de usuario"""
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession(
                user_id=user_id,
                preferences={
                    "response_style": "professional",
                    "detail_level": "medium",
                    "include_banking_context": True
                }
            )
        return self.sessions[user_id]
    
    async def process_chat_message(self, message: ChatMessage) -> ChatResponse:
        """
        🎯 MÉTODO PRINCIPAL: Implementa el flujo perfecto de clasificación y enrutamiento
        """
        start_time = datetime.now()
        session = self.get_session(message.user_id)
        
        try:
            if not message.message.strip():
                return ChatResponse(
                    response="Por favor, ingrese su consulta sobre control de gestión bancario.",
                    response_type="validation_error",
                    session_id=message.user_id,
                    execution_time=0.0
                )
            
            # 🎯 PASO 1: CLASIFICACIÓN Y ENRUTAMIENTO INTELIGENTE
            routing_result = await self.classifier.classify_and_route(
                message.message, 
                {
                    'history': session.conversation_history[-3:],
                    'charts': session.chart_configs,
                    'preferences': session.preferences,
                    'gestor_id': message.gestor_id,
                    'periodo': message.periodo
                }
            )
            
            flow_type = routing_result['flow_type']
            logger.info(f"🎯 Flujo determinado: {flow_type} (confianza: {routing_result['confidence']})")
            
            # 🎯 PASO 2: EJECUTAR FLUJO CORRESPONDIENTE
            if flow_type == 'PREDEFINED_QUERY':
                return await self._execute_predefined_flow(message, session, routing_result, start_time)
                
            elif flow_type == 'DYNAMIC_SQL':
                return await self._execute_dynamic_sql_flow(message, session, routing_result, start_time)
                
            elif flow_type == 'CDG_AGENT':
                return await self._execute_cdg_agent_flow(message, session, routing_result, start_time)
                
            elif flow_type == 'CONTEXTUAL_RESPONSE':
                return await self._execute_contextual_flow(message, session, routing_result, start_time)
                
            else:
                # Fallback a SQL dinámico
                return await self._execute_dynamic_sql_flow(message, session, routing_result, start_time)
        
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=f"Disculpe, hubo un error procesando su consulta: {str(e)}. Por favor, intente reformularla.",
                response_type="error",
                metadata={"error": str(e)},
                execution_time=execution_time,
                session_id=message.user_id
            )
    
    async def _execute_predefined_flow(self, message: ChatMessage, session: ChatSession, 
                                     routing_result: Dict, start_time: datetime) -> ChatResponse:
        """🎯 FLUJO: Query predefinida encontrada - ejecutarla directamente"""
        try:
            logger.info("🎯 Ejecutando FLUJO PREDEFINIDO")
            
            predefined_match = routing_result['predefined_match']
            
            # Ejecutar query predefinida
            execution_result = await self.predefined_executor.execute_predefined_query(
                predefined_match, 
                message.message,
                {
                    'gestor_id': message.gestor_id,
                    'periodo': message.periodo,
                    'context': message.context
                }
            )
            
            if not execution_result['success']:
                logger.warning(f"Query predefinida falló: {execution_result['error']}")
                # Fallback a SQL dinámico
                return await self._execute_dynamic_sql_flow(message, session, routing_result, start_time)
            
            # Formatear respuesta
            formatted_response = await self.formatter.format_response(
                execution_result['data'],
                message.message,
                {
                    'predefined_query': True,
                    'metadata': execution_result['metadata'],
                    'preferences': session.preferences
                }
            )
            
            # Actualizar historial
            session.conversation_history.append({
                'user_message': message.message,
                'response': formatted_response,
                'flow_type': 'PREDEFINED_QUERY',
                'timestamp': datetime.now().isoformat()
            })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=formatted_response,
                response_type="predefined_query",
                data=execution_result['data'],
                metadata={
                    'flow_type': 'PREDEFINED_QUERY',
                    'predefined_function': f"{predefined_match.get('catalog')}.{predefined_match.get('function_name')}",
                    'execution_metadata': execution_result['metadata'],
                    'routing_confidence': routing_result['confidence']
                },
                execution_time=execution_time,
                confidence_score=routing_result['confidence'],
                session_id=message.user_id
            )
            
        except Exception as e:
            logger.error(f"Error en flujo predefinido: {e}")
            # Fallback a SQL dinámico
            return await self._execute_dynamic_sql_flow(message, session, routing_result, start_time)
    
    async def _execute_dynamic_sql_flow(self, message: ChatMessage, session: ChatSession,
                                      routing_result: Dict, start_time: datetime) -> ChatResponse:
        """🎯 FLUJO: Generar SQL dinámicamente"""
        try:
            logger.info("🎯 Ejecutando FLUJO SQL DINÁMICO")
            
            # Construir SQL dinámicamente
            sql_result = await self.query_builder.build_sql_for_any_query(
                message.message,
                {
                    'classification': routing_result['classification'],
                    'gestor_id': message.gestor_id,
                    'periodo': message.periodo,
                    'context': message.context
                }
            )
            
            if not sql_result['is_safe']:
                logger.warning(f"❌ SQL bloqueado por seguridad: {sql_result.get('sql', '')}")
                return ChatResponse(
                    response="Por seguridad, no puedo ejecutar esa consulta. ¿Podría reformularla de manera más específica?",
                    response_type="security_block",
                    session_id=message.user_id,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Ejecutar SQL
            query_data = self._execute_query_safely(sql_result['sql'])
            
            # Formatear respuesta
            formatted_response = await self.formatter.format_response(
                query_data,
                message.message,
                {
                    'sql_explanation': sql_result['explanation'],
                    'tables_used': sql_result['tables_used'],
                    'preferences': session.preferences
                }
            )
            
            # Actualizar historial
            session.conversation_history.append({
                'user_message': message.message,
                'response': formatted_response,
                'flow_type': 'DYNAMIC_SQL',
                'timestamp': datetime.now().isoformat()
            })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=formatted_response,
                response_type="dynamic_sql",
                data=query_data,
                metadata={
                    'flow_type': 'DYNAMIC_SQL',
                    'sql_executed': sql_result['sql'],
                    'explanation': sql_result['explanation'],
                    'tables_used': sql_result['tables_used'],
                    'routing_confidence': routing_result['confidence']
                },
                execution_time=execution_time,
                confidence_score=routing_result['confidence'],
                session_id=message.user_id
            )
            
        except Exception as e:
            logger.error(f"Error en flujo SQL dinámico: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=f"Hubo un problema ejecutando su consulta SQL: {str(e)}",
                response_type="sql_error",
                execution_time=execution_time,
                session_id=message.user_id
            )
    
    async def _execute_cdg_agent_flow(self, message: ChatMessage, session: ChatSession,
                                    routing_result: Dict, start_time: datetime) -> ChatResponse:
        """🎯 FLUJO: Delegar al CDG Agent para análisis complejo"""
        try:
            logger.info("🎯 Ejecutando FLUJO CDG AGENT")
            
            if not self.cdg_agent:
                # Fallback a SQL dinámico si CDG no disponible
                return await self._execute_dynamic_sql_flow(message, session, routing_result, start_time)
            
            cdg_request = CDGRequest(
                user_message=message.message,
                user_id=message.user_id,
                gestor_id=message.gestor_id,
                periodo=message.periodo,
                context=message.context,
                include_charts=True,
                include_recommendations=True
            )
            
            cdg_response = await self.cdg_agent.process_request(cdg_request)
            
            # Formatear respuesta del CDG Agent
            if hasattr(cdg_response, 'content') and cdg_response.content:
                formatted_response = await self.formatter.format_response(
                    cdg_response.content,
                    message.message,
                    {
                        'cdg_analysis': True,
                        'preferences': session.preferences
                    }
                )
            else:
                formatted_response = "El análisis avanzado ha sido procesado exitosamente por el sistema CDG."
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=formatted_response,
                response_type="cdg_analysis",
                data=getattr(cdg_response, 'content', None),
                charts=getattr(cdg_response, 'charts', []),
                recommendations=getattr(cdg_response, 'recommendations', []),
                metadata={
                    'flow_type': 'CDG_AGENT',
                    'cdg_agent_used': True,
                    'cdg_confidence': getattr(cdg_response, 'confidence_score', 0.8),
                    'routing_confidence': routing_result['confidence']
                },
                execution_time=execution_time,
                confidence_score=getattr(cdg_response, 'confidence_score', 0.8),
                session_id=message.user_id
            )
            
        except Exception as e:
            logger.error(f"Error en flujo CDG Agent: {e}")
            # Fallback a SQL dinámico
            return await self._execute_dynamic_sql_flow(message, session, routing_result, start_time)
    
    async def _execute_contextual_flow(self, message: ChatMessage, session: ChatSession,
                                     routing_result: Dict, start_time: datetime) -> ChatResponse:
        """🎯 FLUJO: Respuesta contextual sin SQL (preguntas generales/conceptuales)"""
        try:
            logger.info("🎯 Ejecutando FLUJO CONTEXTUAL")
            
            # Obtener información dinámica de la BD para contexto
            schema_info = self.query_builder.schema_inspector.get_database_schema()
            available_tables = list(schema_info['tables'].keys())
            total_records = schema_info['metadata']['total_records']
            
            contextual_prompt = f"""
            Responde esta pregunta sobre Control de Gestión bancario con contexto profesional:

            PREGUNTA: "{message.message}"

            CONTEXTO DISPONIBLE:
            - Sistema: Banca March - Control de Gestión 
            - Base de datos: {len(available_tables)} tablas, {total_records:,} registros
            - Alcance: Análisis de rentabilidad, KPIs, gestores comerciales
            - Productos: Fondos, Banca Privada, Empresas, Seguros
            
            TIPO DE RESPUESTA REQUERIDA:
            - Profesional y clara
            - Con ejemplos bancarios específicos
            - Incluir sugerencias de consultas concretas si es apropiado
            - Máximo 400 palabras
            
            Si es una pregunta conceptual (qué es X), explica con ejemplos de control de gestión.
            Si es una pregunta general, orienta hacia consultas específicas disponibles.
            """
            
            if IMPORTS_SUCCESSFUL:
                response = self.formatter.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": CHAT_CONVERSATIONAL_SYSTEM_PROMPT},
                        {"role": "user", "content": contextual_prompt}
                    ],
                    temperature=0.4,
                    max_tokens=600
                )
                contextual_response = response.choices[0].message.content.strip()
            else:
                contextual_response = self._generate_contextual_fallback(message.message, schema_info)
            
            # Generar sugerencias dinámicas
            suggestions = self._generate_contextual_suggestions(message.message, schema_info)
            
            # Actualizar historial
            session.conversation_history.append({
                'user_message': message.message,
                'response': contextual_response,
                'flow_type': 'CONTEXTUAL_RESPONSE',
                'timestamp': datetime.now().isoformat()
            })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=contextual_response,
                response_type="contextual_response",
                recommendations=suggestions,
                metadata={
                    'flow_type': 'CONTEXTUAL_RESPONSE',
                    'database_info': {
                        'tables_available': len(available_tables),
                        'total_records': total_records,
                        'last_updated': schema_info['metadata']['last_updated']
                    },
                    'routing_confidence': routing_result['confidence']
                },
                execution_time=execution_time,
                confidence_score=routing_result['confidence'],
                session_id=message.user_id
            )
            
        except Exception as e:
            logger.error(f"Error en flujo contextual: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=f"Error generando respuesta contextual: {str(e)}",
                response_type="contextual_error",
                execution_time=execution_time,
                session_id=message.user_id
            )
    
    def _execute_query_safely(self, sql: str) -> Any:
        """Ejecuta consulta SQL de forma segura"""
        try:
            if IMPORTS_SUCCESSFUL:
                return query_executor.execute_query(sql)
            else:
                return [{"mock": "data", "message": "Modo fallback activo"}]
                
        except Exception as e:
            logger.error(f"Error ejecutando SQL: {e}")
            return {"error": f"Error en consulta SQL: {str(e)}"}
    
    def _generate_contextual_fallback(self, user_message: str, schema_info: Dict) -> str:
        """Genera respuesta contextual fallback"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['qué es', 'define', 'concepto']):
            return f"""
            📚 **Control de Gestión Bancario - Conceptos Clave**
            
            Su consulta sobre "{user_message}" se refiere a conceptos fundamentales de nuestro sistema de control de gestión.
            
            En Banca March utilizamos métricas clave como:
            • **Margen Neto:** Diferencia entre ingresos y gastos operativos
            • **ROE:** Rentabilidad sobre patrimonio  
            • **Eficiencia Operativa:** Ratio ingresos/gastos
            
            💡 **Consultas específicas que puedo responder:**
            • "¿Cuál es el margen neto del gestor 15?"
            • "Muestra la eficiencia operativa por centro"  
            • "Compara ROE entre segmentos"
            """
        
        return f"""
        👋 **Bienvenido al Sistema de Control de Gestión**
        
        He recibido su consulta: "{user_message}"
        
        📊 **Sistema disponible:**
        • {schema_info['metadata']['total_tables']} tablas especializadas
        • {schema_info['metadata']['total_records']:,} registros actualizados
        • Cobertura completa de gestores, productos y KPIs
        
        💡 **Para mejores resultados, puede consultar:**
        • Performance específico de gestores
        • Análisis comparativos entre períodos  
        • KPIs financieros y operativos
        • Desviaciones de precios y márgenes
        
        ¿En qué aspecto específico le gustaría que le ayude?
        """
    
    def _generate_contextual_suggestions(self, user_message: str, schema_info: Dict) -> List[str]:
        """Genera sugerencias contextuales dinámicas"""
        base_suggestions = [
            "¿Cuántos gestores tenemos activos?",
            "Muestra el ranking de gestores por margen neto",
            "¿Cuál es la distribución de contratos por producto?",
            "Analiza las desviaciones de precio del último período"
        ]
        
        # Añadir sugerencias específicas según tablas disponibles
        if 'MAESTRO_GESTORES' in schema_info['tables']:
            count = schema_info['tables']['MAESTRO_GESTORES']['record_count']
            base_suggestions.append(f"Analizar los {count} gestores disponibles")
        
        if 'PRECIO_POR_PRODUCTO_REAL' in schema_info['tables']:
            base_suggestions.append("Detectar desviaciones críticas de precios")
        
        return base_suggestions[:5]  # Limitar a 5 sugerencias
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Estado completo del agente v10.0"""
        schema_info = self.query_builder.schema_inspector.get_database_schema()
        
        return {
            'status': 'active',
            'version': '10.0 - Integración Completa con Catálogos',
            'capabilities': [
                'Clasificación inteligente de consultas',
                'Búsqueda automática en queries predefinidas (6 catálogos)',
                'Generación SQL dinámica con contexto bancario',
                'Respuestas contextuales sin SQL',
                'Integración completa con CDG Agent',
                'Flujo perfecto de enrutamiento'
            ],
            'query_catalogs': list(self.classifier.query_catalogs.keys()),
            'database_info': {
                'path': self.db_path,
                'tables_available': len(schema_info['tables']),
                'total_records': schema_info['metadata']['total_records'],
                'last_schema_update': schema_info['metadata']['last_updated']
            },
            'sessions_active': len(self.sessions),
            'imports_successful': IMPORTS_SUCCESSFUL
        }

# ============================================================================
# FUNCIONES DE CONVENIENCIA Y EXPORTS
# ============================================================================

def create_universal_chat_agent(db_path: str = None) -> UniversalChatAgentV10:
    """Factory para crear agente v10.0 completo"""
    return UniversalChatAgentV10(db_path)

# Instancia global
_universal_agent = None

def get_universal_chat_agent() -> UniversalChatAgentV10:
    """Obtiene instancia global del agente v10.0"""
    global _universal_agent
    if _universal_agent is None:
        _universal_agent = create_universal_chat_agent()
    return _universal_agent

# Para compatibilidad con código existente
CDGChatAgent = UniversalChatAgentV10

__all__ = [
    'UniversalChatAgentV10',
    'CDGChatAgent', 
    'ChatMessage',
    'ChatResponse',
    'IntelligentQueryClassifier',
    'PredefinedQueryExecutor',
    'BankingResponseFormatter',
    'create_universal_chat_agent',
    'get_universal_chat_agent'
]

if __name__ == "__main__":
    # Demo del agente v10.0 completo
    async def demo():
        print("🚀 Iniciando Universal Chat Agent v10.0 - VERSIÓN COMPLETA...")
        
        agent = create_universal_chat_agent()
        status = agent.get_agent_status()
        
        print(f"Status: {status}")
        
        # Test con consulta
        test_message = ChatMessage(
            user_id="demo_user",
            message="¿Cuántos gestores tenemos en total?"
        )
        
        response = await agent.process_chat_message(test_message)
        print(f"\nRespuesta: {response.response}")
        print(f"Tipo: {response.response_type}")
        print(f"Flujo usado: {response.metadata.get('flow_type', 'unknown')}")
        print(f"Confianza: {response.confidence_score}")
        
    import asyncio
    asyncio.run(demo())
