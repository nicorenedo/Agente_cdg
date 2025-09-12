"""
Chat Agent Universal v9.0 - Agente Conversacional CDG Sin Limitaciones
=====================================================================

Agente completamente universal que puede manejar CUALQUIER consulta sobre 
control de gestión mediante:
- Query Builder inteligente con esquema dinámico de BD
- Clasificación sin hardcodeo
- Delegación completa al CDG Agent para análisis complejos
- Constructor de queries dinámico basado en inspección real de BD
- Prompts externalizados en archivos dedicados

Versión: 9.0 Universal con Esquema Dinámico
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
    from backend.config import settings
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
        CHAT_SQL_GENERATION_SYSTEM_PROMPT
    )
    from prompts.user_prompts import (
        build_intent_classification_prompt,
        build_natural_response_prompt,
        build_sql_generation_prompt,
        build_financial_explanation_prompt
    )
    
    IMPORTS_SUCCESSFUL = True
    logger = logging.getLogger(__name__)
    logger.info("🚀 Chat Agent v9.0 Universal inicializado exitosamente")
    
except ImportError as e:
    logging.warning(f"Modo fallback activado: {e}")
    IMPORTS_SUCCESSFUL = False
    
    # Fallbacks mínimos
    def iniciar_agente_llm():
        class MockLLM:
            class Chat:
                class Completions:
                    def create(self, **kwargs):
                        return type('Response', (), {
                            'choices': [type('Choice', (), {
                                'message': type('Message', (), {
                                    'content': '{"intent": "general_query", "sql": "SELECT * FROM MAESTRO_GESTORES LIMIT 5", "confidence": 0.8}'
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
                    'to_dict': lambda: {'response': 'Mock CDG response', 'data': {}}
                })()
        return MockCDGAgent()
    
    # Mock query executor
    class MockQueryExecutor:
        def execute_query(self, query, params=None, fetch_type="all"):
            return [{"mock": "data"}]
    
    query_executor = MockQueryExecutor()
    
    # Mock prompts (básicos)
    CHAT_CONVERSATIONAL_SYSTEM_PROMPT = "Eres un asistente financiero especializado en Control de Gestión bancario."
    CHAT_INTENT_CLASSIFICATION_PROMPT = "Clasifica la intención del usuario en formato JSON."
    CHAT_NATURAL_RESPONSE_SYSTEM_PROMPT = "Genera respuestas naturales y profesionales."
    CHAT_SQL_GENERATION_SYSTEM_PROMPT = "Genera consultas SQL seguras para base de datos financiera."
    
    def build_intent_classification_prompt(message, context):
        return f"Clasifica: {message}"
    
    def build_natural_response_prompt(data, query, context):
        return f"Respuesta para: {query} con datos: {data}"
    
    def build_sql_generation_prompt(message, context):
        return f"SQL para: {message}"

logger = logging.getLogger(__name__)

# ============================================================================
# INSPECTOR DINÁMICO DE ESQUEMA DE BASE DE DATOS
# ============================================================================

class DatabaseSchemaInspector:
    """
    🚀 NUEVA FUNCIONALIDAD: Inspector dinámico de esquema
    Obtiene la estructura completa de la BD en tiempo real
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.schema_cache = {}
        self.cache_timestamp = None
        self.cache_duration = 300  # 5 minutos
    
    def get_database_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtiene el esquema completo de la base de datos dinámicamente
        """
        try:
            # Verificar si necesitamos refrescar el cache
            current_time = datetime.now()
            if (not force_refresh and 
                self.schema_cache and 
                self.cache_timestamp and 
                (current_time - self.cache_timestamp).seconds < self.cache_duration):
                return self.schema_cache
            
            logger.info("🔍 Inspeccionando esquema de base de datos...")
            
            schema = {
                'tables': {},
                'relationships': {},
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
                # Fallback para testing
                tables = [
                    {'name': 'MAESTRO_GESTORES'},
                    {'name': 'MAESTRO_CONTRATOS'},
                    {'name': 'PRECIO_POR_PRODUCTO_REAL'},
                    {'name': 'PRECIO_POR_PRODUCTO_STD'}
                ]
            
            total_records = 0
            
            for table_info in tables:
                table_name = table_info['name']
                
                # Obtener esquema de la tabla
                table_schema = self._get_table_schema(table_name)
                
                # Obtener número de registros
                record_count = self._get_table_count(table_name)
                total_records += record_count
                
                # Identificar relaciones
                relationships = self._identify_relationships(table_name, table_schema)
                
                schema['tables'][table_name] = {
                    'columns': table_schema,
                    'record_count': record_count,
                    'relationships': relationships,
                    'description': self._get_table_description(table_name)
                }
            
            schema['metadata']['total_tables'] = len(tables)
            schema['metadata']['total_records'] = total_records
            
            # Actualizar cache
            self.schema_cache = schema
            self.cache_timestamp = current_time
            
            logger.info(f"✅ Esquema cargado: {len(tables)} tablas, {total_records} registros totales")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Error inspeccionando esquema: {e}")
            return self._get_fallback_schema()
    
    def _get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Obtiene el esquema de una tabla específica"""
        try:
            if IMPORTS_SUCCESSFUL:
                return query_executor.get_table_info(table_name)
            else:
                # Schema básico para testing
                return [
                    {'cid': 0, 'name': 'ID', 'type': 'INTEGER', 'notnull': 1, 'dflt_value': None, 'pk': 1},
                    {'cid': 1, 'name': 'DESCRIPCION', 'type': 'TEXT', 'notnull': 1, 'dflt_value': None, 'pk': 0}
                ]
        except Exception as e:
            logger.warning(f"Error obteniendo esquema de {table_name}: {e}")
            return []
    
    def _get_table_count(self, table_name: str) -> int:
        """Obtiene el número de registros en una tabla"""
        try:
            if IMPORTS_SUCCESSFUL:
                return query_executor.get_table_count(table_name)
            else:
                return 100  # Fallback
        except Exception as e:
            logger.warning(f"Error contando registros en {table_name}: {e}")
            return 0
    
    def _identify_relationships(self, table_name: str, schema: List[Dict]) -> List[Dict]:
        """Identifica relaciones entre tablas basándose en nombres de columnas"""
        relationships = []
        
        for column in schema:
            col_name = column.get('name', '').upper()
            
            # Identificar foreign keys por convención de nombres
            if col_name.endswith('_ID') and col_name != f"{table_name.upper()}_ID":
                target_table = col_name.replace('_ID', '')
                if target_table in ['GESTOR', 'CLIENTE', 'PRODUCTO', 'CENTRO', 'SEGMENTO', 'EMPRESA']:
                    relationships.append({
                        'column': col_name,
                        'references': f'MAESTRO_{target_table}S',
                        'type': 'foreign_key'
                    })
            
            # Identificar otras relaciones comunes
            elif col_name in ['CONTRATO_ID']:
                relationships.append({
                    'column': col_name,
                    'references': 'MAESTRO_CONTRATOS',
                    'type': 'foreign_key'
                })
        
        return relationships
    
    def _get_table_description(self, table_name: str) -> str:
        """Genera descripción de la tabla basándose en su nombre y esquema"""
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
        """Schema fallback básico para casos de error"""
        return {
            'tables': {
                'MAESTRO_GESTORES': {
                    'columns': [{'name': 'GESTOR_ID'}, {'name': 'DESC_GESTOR'}],
                    'record_count': 30,
                    'relationships': [],
                    'description': 'Gestores comerciales'
                }
            },
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'total_tables': 1,
                'total_records': 30
            }
        }
    
    def get_table_names(self) -> List[str]:
        """Obtiene lista de nombres de tablas"""
        schema = self.get_database_schema()
        return list(schema['tables'].keys())
    
    def get_columns_for_table(self, table_name: str) -> List[str]:
        """Obtiene lista de columnas para una tabla específica"""
        schema = self.get_database_schema()
        table_info = schema['tables'].get(table_name.upper(), {})
        columns = table_info.get('columns', [])
        return [col.get('name') for col in columns if col.get('name')]

# ============================================================================
# QUERY BUILDER UNIVERSAL INTELIGENTE
# ============================================================================

class UniversalQueryBuilder:
    """
    Query Builder que CONOCE la base de datos dinámicamente y puede construir 
    consultas para CUALQUIER pregunta sobre control de gestión
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.schema_inspector = DatabaseSchemaInspector(self.db_path)
        self.llm_client = iniciar_agente_llm()
    
    async def build_sql_for_any_query(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """
        Construye SQL para CUALQUIER consulta del usuario usando esquema dinámico
        """
        try:
            # 1. Obtener esquema completo y actualizado
            database_schema = self.schema_inspector.get_database_schema()
            
            # 2. Preparar contexto completo de la BD para el LLM
            schema_context = self._build_comprehensive_schema_context(database_schema)
            
            # 3. Construir prompt usando sistema externalizado
            sql_generation_prompt = build_sql_generation_prompt(user_message, {
                'database_schema': schema_context,
                'context': context or {},
                'available_tables': list(database_schema['tables'].keys()),
                'total_records': database_schema['metadata']['total_records']
            }) if IMPORTS_SUCCESSFUL else f"Genera SQL para: {user_message}"
            
            # 4. Llamar a LLM para generar SQL
            if IMPORTS_SUCCESSFUL:
                response = self.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": CHAT_SQL_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": sql_generation_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                result_text = response.choices[0].message.content.strip()
                logger.debug(f"🔍 LLM raw response: {result_text}")
                
                # Limpiar y parsear JSON
                result = self._parse_llm_sql_response(result_text)
                logger.debug(f"🔍 Parsed SQL: {result.get('sql', '')}")
            else:
                # Fallback básico
                result = self._generate_fallback_sql(user_message, database_schema)
            
            # 5. Validar seguridad
            sql = result.get('sql', '')
            is_safe = is_query_safe(sql) if IMPORTS_SUCCESSFUL else True
            
            # 6. Enriquecer resultado
            result.update({
                'is_safe': is_safe,
                'generated_at': datetime.now().isoformat(),
                'schema_version': database_schema['metadata']['last_updated'],
                'tables_available': len(database_schema['tables'])
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error construyendo SQL: {e}")
            return {
                'sql': 'SELECT "Error en construcción de query - consulta no válida" as message',
                'explanation': f'Error: {str(e)}',
                'tables_used': [],
                'intent': 'error',
                'confidence': 0.0,
                'is_safe': True
            }
    
    def _build_comprehensive_schema_context(self, schema: Dict[str, Any]) -> str:
        """Construye descripción completa y actualizada del esquema para el LLM"""
        context_lines = []
        
        context_lines.append("BASE DE DATOS BM_CONTABILIDAD_CDG - ESQUEMA COMPLETO ACTUALIZADO:")
        context_lines.append(f"Última actualización: {schema['metadata']['last_updated']}")
        context_lines.append(f"Total tablas: {schema['metadata']['total_tables']}")
        context_lines.append(f"Total registros: {schema['metadata']['total_records']}")
        context_lines.append("")
        
        for table_name, table_info in schema['tables'].items():
            columns = table_info.get('columns', [])
            record_count = table_info.get('record_count', 0)
            description = table_info.get('description', '')
            relationships = table_info.get('relationships', [])
            
            context_lines.append(f"TABLA: {table_name}")
            context_lines.append(f"Descripción: {description}")
            context_lines.append(f"Registros: {record_count}")
            
            # Columnas con tipos
            col_info = []
            for col in columns:
                col_name = col.get('name', 'unknown')
                col_type = col.get('type', 'unknown')
                is_pk = " [PK]" if col.get('pk') else ""
                is_notnull = " NOT NULL" if col.get('notnull') else ""
                col_info.append(f"{col_name} ({col_type}){is_pk}{is_notnull}")
            
            context_lines.append(f"Columnas: {', '.join(col_info)}")
            
            # Relaciones
            if relationships:
                rel_info = [f"{r['column']} -> {r['references']}" for r in relationships]
                context_lines.append(f"Relaciones: {', '.join(rel_info)}")
            
            context_lines.append("")
        
        return '\n'.join(context_lines)
    
    def _parse_llm_sql_response(self, llm_response: str) -> Dict[str, Any]:
        """Parsea la respuesta del LLM y extrae el SQL con validaciones robustas"""
        try:
            # Limpiar respuesta
            cleaned_response = llm_response.strip()

            # Detectar respuestas muy cortas o solo palabras clave
            if len(cleaned_response) < 10 or cleaned_response.upper() in ['SELECT', 'WITH', 'FROM', 'WHERE']:
                logger.warning(f"LLM devolvió respuesta incompleta: {cleaned_response}")
                return self._generate_fallback_sql("precio real", {})

            # Buscar JSON válido
            import re
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                sql = result.get('sql', '').strip()

                # Validar que el SQL extraído del JSON esté completo
                if self._is_complete_sql(sql):
                    return {
                        'sql': sql,
                        'explanation': result.get('explanation', ''),
                        'tables_used': result.get('tables_used', []),
                        'intent': result.get('intent', 'data_query'),
                        'confidence': float(result.get('confidence', 0.8))
                    }
                else:
                    logger.warning(f"SQL incompleto en JSON: {sql}")

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error parseando JSON: {e}")

        # Fallback: buscar SQL directamente con validación mejorada
        sql_patterns = [
            r'(SELECT\s+.+?\s+FROM\s+\w+.*?)(?:;|\n|$)',  # Más estricto: requiere FROM
            r'(WITH\s+.+?SELECT\s+.+?\s+FROM\s+\w+.*?)(?:;|\n|$)',  # Para CTEs
        ]

        for pattern in sql_patterns:
            sql_match = re.search(pattern, cleaned_response, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if sql_match:
                sql = sql_match.group(1).strip()
                if self._is_complete_sql(sql):
                    return {
                        'sql': sql,
                        'explanation': 'SQL extraído del texto de respuesta',
                        'tables_used': self._extract_tables_from_sql(sql),
                        'intent': 'data_query',
                        'confidence': 0.6
                    }

        # Último fallback con mensaje más específico
        logger.error(f"No se pudo extraer SQL válido de: {cleaned_response[:100]}...")
        return self._generate_fallback_sql("precio real", {})

    def _is_complete_sql(self, sql: str) -> bool:
        """Valida que el SQL sea completo y ejecutable"""
        if not sql or len(sql.strip()) < 10:
            return False

        sql_upper = sql.upper().strip()

        # Debe empezar con SELECT o WITH
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            return False

        # Para SELECT, debe tener FROM
        if sql_upper.startswith('SELECT') and 'FROM' not in sql_upper:
            return False

        # No debe terminar en palabras clave incompletas
        incomplete_endings = ['WHERE', 'AND', 'OR', 'SELECT', 'FROM', 'JOIN', 'ON', 'GROUP BY', 'ORDER BY']
        for ending in incomplete_endings:
            if sql_upper.strip().endswith(ending):
                return False

        return True

    def _generate_fallback_sql(self, user_message: str, schema: Dict) -> Dict[str, Any]:
        """SQL fallback inteligente mejorado"""
        message_lower = user_message.lower()

        # Identificar tabla objetivo con mayor precisión
        target_table = None
        confidence = 0.3  # Confianza baja para fallbacks

        if any(word in message_lower for word in ['precio', 'coste', 'cost']):
            if 'real' in message_lower or 'actual' in message_lower:
                target_table = 'PRECIO_POR_PRODUCTO_REAL'
                confidence = 0.5
            else:
                target_table = 'PRECIO_POR_PRODUCTO_STD'
                confidence = 0.4
        elif any(word in message_lower for word in ['gestor', 'comercial']):
            target_table = 'MAESTRO_GESTORES'
            confidence = 0.4
        elif any(word in message_lower for word in ['contrato', 'contract']):
            target_table = 'MAESTRO_CONTRATOS'
            confidence = 0.4
        elif any(word in message_lower for word in ['cliente']):
            target_table = 'MAESTRO_CLIENTES'
            confidence = 0.4

        # Si no se identifica tabla específica, usar la primera disponible
        if not target_table:
            available_tables = list(schema.get('tables', {}).keys()) if schema else []
            target_table = available_tables[0] if available_tables else 'MAESTRO_GESTORES'
            confidence = 0.2

        # Construir SQL más seguro
        sql = f"SELECT * FROM {target_table} LIMIT 10"

        return {
            'sql': sql,
            'explanation': f'Consulta fallback generada para la tabla {target_table}. El LLM no pudo generar SQL válido.',
            'tables_used': [target_table],
            'intent': 'data_query',
            'confidence': confidence
        }


    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extrae nombres de tablas mencionadas en el SQL"""
        import re
        sql_upper = sql.upper()
        
        # Buscar patrones FROM y JOIN
        table_patterns = [
            r'FROM\s+([A-Z_][A-Z0-9_]*)',
            r'JOIN\s+([A-Z_][A-Z0-9_]*)',
            r'UPDATE\s+([A-Z_][A-Z0-9_]*)',
            r'INSERT\s+INTO\s+([A-Z_][A-Z0-9_]*)'
        ]
        
        tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, sql_upper)
            tables.update(matches)
        
        return list(tables)

# ============================================================================
# RESTO DE CLASES (QueryClassifier, NaturalResponseFormatter, etc.)
# ============================================================================

@dataclass
class QueryClassification:
    intent: str
    confidence: float
    entities: Dict[str, Any]
    requires_sql: bool
    requires_chart: bool
    query_complexity: str

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
    user_feedback: Optional[Dict[str, Any]] = None
    chart_interaction_type: Optional[str] = None
    use_basic_queries: Optional[bool] = True
    quick_mode: Optional[bool] = False


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

class UniversalQueryClassifier:
    """Clasificador universal sin hardcodeo"""
    
    def __init__(self):
        self.llm_client = iniciar_agente_llm()
    
    async def classify_intent(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Clasifica CUALQUIER consulta sin limitaciones hardcodeadas"""
        try:
            classification_prompt = build_intent_classification_prompt(user_message, {
                'conversation_history': context.get('history', []) if context else [],
                'current_charts': context.get('charts', []) if context else [],
                'user_preferences': context.get('preferences', {}) if context else {}
            }) if IMPORTS_SUCCESSFUL else f"Clasifica: {user_message}"
            
            if IMPORTS_SUCCESSFUL:
                response = self.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": CHAT_INTENT_CLASSIFICATION_PROMPT},
                        {"role": "user", "content": classification_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=300
                )
                
                result_text = response.choices[0].message.content.strip()
                return self._parse_classification_response(result_text)
            else:
                return self._fallback_classification(user_message)
                
        except Exception as e:
            logger.error(f"Error en clasificación: {e}")
            return self._fallback_classification(user_message)
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea respuesta del LLM para clasificación"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return {
                    'intent': result.get('intent', 'general_query'),
                    'complexity': result.get('complexity', 'medium'),
                    'response_type': result.get('response_type', 'data_query'),
                    'requires_sql': result.get('requires_sql', True),
                    'requires_cdg_agent': result.get('requires_cdg_agent', False),
                    'confidence': float(result.get('confidence', 0.5)),
                    'reasoning': result.get('reasoning', 'Clasificación automática')
                }
        except:
            pass
        
        return self._fallback_classification("")
    
    def _fallback_classification(self, user_message: str) -> Dict[str, Any]:
        """Clasificación fallback básica"""
        message_lower = user_message.lower() if user_message else ""
        
        # Detección básica por palabras clave
        if any(word in message_lower for word in ['gráfico', 'chart', 'cambia', 'modifica']):
            return {
                'intent': 'chart_modification',
                'complexity': 'simple',
                'response_type': 'chart_modification',
                'requires_sql': False,
                'requires_cdg_agent': False,
                'confidence': 0.8,
                'reasoning': 'Palabras clave de modificación de gráfico detectadas'
            }
        
        elif any(word in message_lower for word in ['análisis', 'explica', 'por qué']):
            return {
                'intent': 'analysis_request',
                'complexity': 'complex',
                'response_type': 'analysis',
                'requires_sql': True,
                'requires_cdg_agent': True,
                'confidence': 0.7,
                'reasoning': 'Solicitud de análisis detectada'
            }
        
        else:
            return {
                'intent': 'data_query',
                'complexity': 'medium',
                'response_type': 'data_query',
                'requires_sql': True,
                'requires_cdg_agent': False,
                'confidence': 0.6,
                'reasoning': 'Consulta de datos general'
            }

class NaturalResponseFormatter:
    """Formateador de respuestas naturales usando prompts externalizados"""
    
    def __init__(self):
        self.llm_client = iniciar_agente_llm()
    
    async def format_response(self, data: Any, query: str, context: Dict = None) -> str:
        """Convierte CUALQUIER dato en respuesta natural y profesional"""
        try:
            if not data:
                return "No se encontraron datos relacionados con su consulta. ¿Podría reformular la pregunta con más detalles específicos?"
    
            # Construir prompt de forma segura
            try:
                safe_data = data if data is not None else []
                safe_query = str(query) if query else "consulta"
                safe_context = context if isinstance(context, dict) else {}
                
                # Construir prompt manualmente sin usar build_natural_response_prompt
                prompt_text = f"Por favor genera una respuesta profesional en español para la consulta: '{safe_query}', basándote en estos datos: {safe_data}."
                
            except Exception as e:
                logger.error(f"Error preparando prompt: {e}")
                prompt_text = f"Por favor genera una respuesta profesional para: '{query}'"
    
            if IMPORTS_SUCCESSFUL:
                response = self.llm_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_ID,
                    messages=[
                        {"role": "system", "content": CHAT_NATURAL_RESPONSE_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_text}
                    ],
                    temperature=0.3,
                    max_tokens=800
                )
                return response.choices[0].message.content.strip()
            else:
                return self._format_fallback(data, query)
    
        except Exception as e:
            logger.error(f"Error formateando respuesta: {e}")
            return f"Se procesaron los datos para '{query}', pero hubo un error en el formateo."
    


    
    def _format_fallback(self, data: Any, query: str) -> str:
        """Formateo fallback básico"""
        if isinstance(data, list) and len(data) > 0:
            return f"📊 **Resultados para:** {query}\n\nSe encontraron {len(data)} registros."
        elif isinstance(data, dict):
            formatted_items = []
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    formatted_items.append(f"• **{key.replace('_', ' ').title()}:** {value:,.2f}")
                else:
                    formatted_items.append(f"• **{key.replace('_', ' ').title()}:** {value}")
            return f"📊 **Resultado para:** {query}\n\n" + "\n".join(formatted_items)
        else:
            return f"📊 Resultado para '{query}': {str(data)}"

# ============================================================================
# AGENTE DE CHAT PRINCIPAL UNIVERSAL
# ============================================================================

class UniversalChatAgent:
    """
    🚀 Chat Agent Universal v9.0 - CON ESQUEMA DINÁMICO
    
    Características principales:
    - Esquema de BD obtenido dinámicamente
    - Query Builder inteligente sin hardcodeo
    - Prompts externalizados
    - Clasificación universal
    - Integración completa con CDG Agent
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.sessions: Dict[str, ChatSession] = {}
        
        # Componentes principales con esquema dinámico
        self.query_builder = UniversalQueryBuilder(self.db_path)
        self.classifier = UniversalQueryClassifier()
        self.formatter = NaturalResponseFormatter()
        
        # Integraciones
        self.cdg_agent = create_cdg_agent() if IMPORTS_SUCCESSFUL else None
        self.chart_generator = None
        if IMPORTS_SUCCESSFUL:
            try:
                self.chart_generator = QueryIntegratedChartGenerator()
            except:
                logger.warning("Chart generator no disponible")
        
        logger.info("🚀 Universal Chat Agent v9.0 inicializado - Con esquema dinámico")
    
    def get_session(self, user_id: str) -> ChatSession:
        """Obtiene o crea sesión de usuario"""
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession(
                user_id=user_id,
                preferences={"response_style": "professional", "detail_level": "medium"}
            )
        return self.sessions[user_id]
    
    async def process_chat_message(self, message: ChatMessage) -> ChatResponse:
        """
        🎯 MÉTODO PRINCIPAL: Procesa CUALQUIER mensaje del usuario
        """
        start_time = datetime.now()
        session = self.get_session(message.user_id)
        
        try:
            if not message.message.strip():
                return ChatResponse(
                    response="Por favor, ingrese su consulta sobre control de gestión.",
                    response_type="validation_error",
                    session_id=message.user_id,
                    execution_time=0.0
                )
            
            # 1. Clasificar la consulta SIN limitaciones
            classification = await self.classifier.classify_intent(
                message.message, 
                {
                    'history': session.conversation_history[-3:],
                    'charts': session.chart_configs,
                    'preferences': session.preferences,
                    'gestor_id': message.gestor_id,
                    'periodo': message.periodo
                }
            )
            
            logger.info(f"🎯 Consulta clasificada: {classification['intent']} (confianza: {classification['confidence']})")
            
            # 2. Decidir estrategia de procesamiento
            if classification['response_type'] == 'chart_modification':
                return await self._handle_chart_modification(message, session, start_time)
                
            elif classification['requires_cdg_agent'] or classification['complexity'] == 'complex':
                return await self._delegate_to_cdg_agent(message, session, classification, start_time)
                
            elif classification['requires_sql']:
                return await self._handle_sql_query(message, session, classification, start_time)
                
            else:
                return await self._handle_general_query(message, session, classification, start_time)
        
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

    async def safe_format_response(self, formatter, data, query, context=None):
        import traceback, json
        try:
            print(f"🔍 safe_format_response called with:")
            print(f"  - data type: {type(data)}")
            print(f"  - query type: {type(query)} = '{query}'")
            print(f"  - context type: {type(context)}")
            
            if context is not None and not isinstance(context, dict):
                print(f"  - Converting context to dict from {type(context)}")
                context = dict(context)
    
            if not isinstance(query, str):
                print(f"  - Converting query to string from {type(query)}")
                query = str(query)
    
            result = await formatter.format_response(data, query, context)
            print(f"🔍 safe_format_response success: {result[:200]}...")
            return result
    
        except Exception as e:
            print(f"❌ Exception in safe_format_response: {e}")
            print(f"❌ Traceback:\n{traceback.format_exc()}")
            return f"Error durante el formateo de respuesta: {e}"

    
    async def _handle_sql_query(self, message: ChatMessage, session: ChatSession, classification: Dict, start_time: datetime) -> ChatResponse:
        """Maneja consultas que requieren acceso directo a la BD"""
        import traceback
        import json

        logger.info(f"🔍 INICIO _handle_sql_query - Usuario: {message.user_id}, Mensaje: '{message.message}'")

        try:
            # 1. Construir SQL inteligentemente con esquema dinámico
            sql_result = await self.query_builder.build_sql_for_any_query(
                message.message,
                {
                    'classification': classification,
                    'gestor_id': message.gestor_id,
                    'periodo': message.periodo,
                    'context': message.context
                }
            )

            logger.debug(f"🔍 Generated SQL: {sql_result.get('sql', '')}")
            logger.debug(f"🛡️ SQL safety flag: {sql_result.get('is_safe')}")

            if not sql_result['is_safe']:
                logger.warning(f"❌ BLOCKED SQL: {sql_result.get('sql', '')}")
                return ChatResponse(
                    response="Por seguridad, no puedo ejecutar esa consulta. ¿Podría reformularla?",
                    response_type="security_block",
                    session_id=message.user_id,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # 2. Ejecutar consulta
            query_data = self._execute_query_safely(sql_result['sql'])

            # 🔍 LOG DETALLADO ANTES DE FORMATEAR
            logger.debug(f"🔍 Query data type: {type(query_data)}")
            logger.debug(f"🔍 Query data sample: {str(query_data)[:500]}...")
            logger.debug(f"🔍 Message.message type: {type(message.message)} = '{message.message}'")

            # Preparar contexto para el formatter
            context_for_formatter = {
                'sql_explanation': sql_result['explanation'],
                'tables_used': sql_result['tables_used'],
                'preferences': session.preferences
            }

            logger.debug(f"🔍 Context for formatter type: {type(context_for_formatter)}")
            logger.debug(f"🔍 Context for formatter: {json.dumps(context_for_formatter, default=str)[:500]}...")

            # 3. Formatear respuesta naturalmente - CON MANEJO DE ERRORES DETALLADO
            try:
                logger.debug("🔍 LLAMANDO a format_response...")
                natural_response = await self.safe_format_response(
                    self.formatter,
                    query_data,
                    message.message, 
                    context_for_formatter
                )
                logger.debug(f"🔍 format_response completado exitosamente: {natural_response[:100]}...")

            except Exception as format_error:
                logger.error(f"❌ ERROR EN format_response: {format_error}")
                logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")
                logger.error(f"❌ Parámetros pasados:")
                logger.error(f"   - data type: {type(query_data)}")
                logger.error(f"   - query type: {type(message.message)} = '{message.message}'")
                logger.error(f"   - context type: {type(context_for_formatter)}")

                # Usar fallback en caso de error
                natural_response = f"Se procesaron los datos para '{message.message}', pero hubo un error en el formateo."

            # 4. Actualizar historial
            session.conversation_history.append({
                'user_message': message.message,
                'response': natural_response,
                'intent': classification['intent'],
                'timestamp': datetime.now().isoformat()
            })

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"🔍 FIN _handle_sql_query exitoso en {execution_time:.3f}s")

            return ChatResponse(
                response=natural_response,
                response_type=classification['response_type'],
                data=query_data,
                metadata={
                    'sql_executed': sql_result['sql'],
                    'explanation': sql_result['explanation'],
                    'tables_used': sql_result['tables_used'],
                    'classification': classification,
                    'schema_version': sql_result.get('schema_version')
                },
                execution_time=execution_time,
                confidence_score=classification['confidence'],
                session_id=message.user_id
            )

        except Exception as e:
            logger.error(f"❌ ERROR GENERAL en _handle_sql_query: {e}")
            logger.error(f"❌ TRACEBACK COMPLETO: {traceback.format_exc()}")
            execution_time = (datetime.now() - start_time).total_seconds()

            return ChatResponse(
                response=f"Hubo un problema ejecutando su consulta: {str(e)}",
                response_type="sql_error",
                execution_time=execution_time,
                session_id=message.user_id
            )


    
    async def _delegate_to_cdg_agent(self, message: ChatMessage, session: ChatSession, classification: Dict, start_time: datetime) -> ChatResponse:
        """Delega consultas complejas al CDG Agent"""
        try:
            if not self.cdg_agent:
                return ChatResponse(
                    response="El sistema de análisis avanzado no está disponible en este momento.",
                    response_type="service_unavailable",
                    session_id=message.user_id,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
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
                    {'cdg_analysis': True, 'preferences': session.preferences}
                )
            else:
                formatted_response = "El análisis ha sido procesado exitosamente por el sistema CDG."
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=formatted_response,
                response_type="cdg_analysis",
                data=getattr(cdg_response, 'content', None),
                charts=getattr(cdg_response, 'charts', []),
                recommendations=getattr(cdg_response, 'recommendations', []),
                metadata={
                    'cdg_agent_used': True,
                    'classification': classification,
                    'cdg_confidence': getattr(cdg_response, 'confidence_score', 0.8)
                },
                execution_time=execution_time,
                confidence_score=getattr(cdg_response, 'confidence_score', 0.8),
                session_id=message.user_id
            )
            
        except Exception as e:
            logger.error(f"Error delegando a CDG Agent: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                response=f"Error en el análisis avanzado: {str(e)}",
                response_type="cdg_error",
                execution_time=execution_time,
                session_id=message.user_id
            )
    
    async def _handle_chart_modification(self, message: ChatMessage, session: ChatSession, start_time: datetime) -> ChatResponse:
        """Maneja modificaciones de gráficos"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if not session.chart_configs:
            return ChatResponse(
                response="No hay gráfico previo para modificar. Primero solicite un análisis que genere visualizaciones.",
                response_type="chart_error",
                session_id=message.user_id,
                execution_time=execution_time
            )
        
        return ChatResponse(
            response="Función de modificación de gráficos será implementada próximamente.",
            response_type="feature_coming_soon",
            session_id=message.user_id,
            execution_time=execution_time
        )
    
    async def _handle_general_query(self, message: ChatMessage, session: ChatSession, classification: Dict, start_time: datetime) -> ChatResponse:
        """Maneja consultas generales"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Obtener información dinámica de la BD
        schema_info = self.query_builder.schema_inspector.get_database_schema()
        available_tables = list(schema_info['tables'].keys())
        total_records = schema_info['metadata']['total_records']
        
        general_response = f"""
        He recibido su consulta: "{message.message}"

        Para brindarle la mejor respuesta sobre control de gestión, podría ser más específico indicando:
        
        📊 **Base de datos actualizada disponible:**
        • {len(available_tables)} tablas con {total_records:,} registros totales
        • Información de gestores y su performance
        • Precios reales vs. estándar por producto/segmento  
        • Análisis de contratos y movimientos financieros
        • Comparativas entre centros y períodos
        • KPIs financieros y de rentabilidad
        
        💡 **Ejemplos de consultas que puedo responder:**
        • "¿Cuál es el precio real del segmento banca privada?"
        • "Muéstrame todos los gestores del centro de Madrid"
        • "¿Cuántos contratos tenemos activos?"
        • "Analiza la rentabilidad del último mes"
        
        ¿En qué aspecto específico le gustaría que le ayude?
        """
        
        return ChatResponse(
            response=general_response,
            response_type="general_help",
            recommendations=[
                "Sea específico sobre el tipo de información que necesita",
                "Mencione períodos, gestores, o segmentos concretos",
                "Indique si necesita comparativas o análisis temporal"
            ],
            metadata={
                'classification': classification,
                'database_info': {
                    'tables_available': len(available_tables),
                    'total_records': total_records,
                    'last_updated': schema_info['metadata']['last_updated']
                }
            },
            execution_time=execution_time,
            confidence_score=classification['confidence'],
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
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Estado del agente universal"""
        schema_info = self.query_builder.schema_inspector.get_database_schema()
        
        return {
            'status': 'active',
            'version': '9.0 Universal con Esquema Dinámico',
            'capabilities': [
                'Consultas universales sobre control de gestión',
                'Query Builder con esquema dinámico de BD',
                'Clasificación sin hardcodeo',
                'Prompts externalizados',
                'Integración completa con CDG Agent',
                'Sesiones persistentes con historial'
            ],
            'database_info': {
                'path': self.db_path,
                'tables_available': len(schema_info['tables']),
                'total_records': schema_info['metadata']['total_records'],
                'last_schema_update': schema_info['metadata']['last_updated']
            },
            'sessions_active': len(self.sessions),
            'imports_successful': IMPORTS_SUCCESSFUL
        }
    
    def get_dynamic_suggestions(self, user_id: str) -> List[str]:
        """Genera sugerencias dinámicas basadas en el esquema actual"""
        schema_info = self.query_builder.schema_inspector.get_database_schema()
        
        suggestions = [
            "¿Cuántos gestores tenemos por centro?",
            "Muéstrame los precios reales más recientes",
            "¿Cuál es la distribución de contratos por producto?",
            "Analiza las desviaciones de precios del último período"
        ]
        
        # Añadir sugerencias específicas basadas en las tablas disponibles
        if 'MAESTRO_GESTORES' in schema_info['tables']:
            suggestions.append(f"Tenemos {schema_info['tables']['MAESTRO_GESTORES']['record_count']} gestores - ¿quiere verlos?")
        
        if 'MAESTRO_CONTRATOS' in schema_info['tables']:
            suggestions.append(f"Hay {schema_info['tables']['MAESTRO_CONTRATOS']['record_count']} contratos activos - ¿necesita análisis?")
        
        return suggestions

# ============================================================================
# FUNCIONES DE CONVENIENCIA Y EXPORTS
# ============================================================================

def create_universal_chat_agent(db_path: str = None) -> UniversalChatAgent:
    """Factory para crear agente universal con esquema dinámico"""
    return UniversalChatAgent(db_path)

# Instancia global
_universal_agent = None

def get_universal_chat_agent() -> UniversalChatAgent:
    """Obtiene instancia global del agente universal"""
    global _universal_agent
    if _universal_agent is None:
        _universal_agent = create_universal_chat_agent()
    return _universal_agent

# Para compatibilidad con código existente
CDGChatAgent = UniversalChatAgent

__all__ = [
    'UniversalChatAgent',
    'CDGChatAgent', 
    'ChatMessage',
    'ChatResponse',
    'DatabaseSchemaInspector',
    'create_universal_chat_agent',
    'get_universal_chat_agent'
]

if __name__ == "__main__":
    # Demo del agente universal con esquema dinámico
    async def demo():
        print("🚀 Iniciando Universal Chat Agent v9.0 con esquema dinámico...")
        
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
        print(f"Confianza: {response.confidence_score}")
        
    import asyncio
    asyncio.run(demo())
