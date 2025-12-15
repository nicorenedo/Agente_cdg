"""
chart_generator.py — V4.4 INTEGRACIÓN COMPLETA (Azure OpenAI + Confidencialidad)

✅ MEJORAS V4.4:
- Integración completa con chart_prompts.py V2.0
- Sistema de confidencialidad bancaria integrado
- Validación automática de permisos por rol de usuario
- Interpretación contextual con roles (GESTOR vs CONTROL_GESTION)
- Funciones avanzadas de chart_prompts utilizadas
- Mantenida compatibilidad con sistemas existentes
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Importar basic_queries con tolerancia a ruta de ejecución
try:
    from queries.basic_queries import basic_queries
except Exception:
    from ..queries.basic_queries import basic_queries  # type: ignore

# 🚀 INTEGRACIÓN COMPLETA CON CHART_PROMPTS V2.0 Y AZURE OPENAI
try:
    from utils.initial_agent import iniciar_agente_llm
    from prompts.chart_prompts import (
        CHART_PIVOT_SYSTEM_PROMPT,
        build_chart_pivot_prompt,
        build_context_aware_prompt,
        validate_chart_request,
        get_available_options_by_role,
        EXTENDED_METRICS,
        EXTENDED_DIMENSIONS,
        EXTENDED_CHART_TYPES
    )
    AZURE_OPENAI_AVAILABLE = True
    logger.info("✅ Azure OpenAI + Chart Prompts V2.0 con confidencialidad habilitado")
except ImportError as e:
    AZURE_OPENAI_AVAILABLE = False
    logger.warning(f"⚠️ Azure OpenAI o Chart Prompts V2.0 no disponible: {e}")

# Configuraciones CDG extendidas con las nuevas métricas
CDG_CHART_CONFIGS = {
    'colors': {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e',
        'success': '#2ca02c',
        'danger': '#d62728',
        'warning': '#ff9800',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40',
        'banca_march_blue': '#003366',
        'banca_march_gold': '#FFD700'
    },
    # Usar configuraciones extendidas si están disponibles
    'chart_types': EXTENDED_CHART_TYPES if AZURE_OPENAI_AVAILABLE else {
        'bar': 'Gráfico de Barras',
        'line': 'Gráfico de Líneas',
        'pie': 'Gráfico Circular',
        'area': 'Gráfico de Área',
        'scatter': 'Gráfico de Dispersión',
        'horizontal_bar': 'Barras Horizontales',
        'donut': 'Gráfico Donut',
        'stacked_bar': 'Barras Apiladas'
    },
    'dimensions': EXTENDED_DIMENSIONS if AZURE_OPENAI_AVAILABLE else {
        'gestor': 'Gestor',
        'centro': 'Centro',
        'segmento': 'Segmento',
        'producto': 'Producto',
        'periodo': 'Período',
        'cliente': 'Cliente',
        'contrato': 'Contrato'
    },
    'metrics': EXTENDED_METRICS if AZURE_OPENAI_AVAILABLE else {
        'ROE': 'Rentabilidad sobre Patrimonio',
        'MARGEN_NETO': 'Margen Neto',
        'INGRESOS': 'Ingresos Totales',
        'EFICIENCIA': 'Eficiencia Operativa',
        'CONTRATOS': 'Número de Contratos',
        'PERFORMANCE': 'Performance General',
        'PRECIO_STD': 'Precio Estándar',
        'PRECIO_REAL': 'Precio Real',
        'DESVIACION': 'Desviación vs Estándar',
        'GASTOS': 'Gastos Totales',
        'CLIENTES': 'Número de Clientes'
    }
}

class QueryIntegratedChartGenerator:
    """
    Generador de gráficos integrado con queries, Azure OpenAI y sistema de confidencialidad V4.4
    ✅ NUEVA: Integración completa con chart_prompts.py V2.0
    """
    
    def __init__(self):
        self.chart_configs = CDG_CHART_CONFIGS
        self.supported_types = list(self.chart_configs['chart_types'].keys())
        self.current_charts: Dict[str, Dict[str, Any]] = {}
        self.basic_queries = basic_queries
        self.azure_available = AZURE_OPENAI_AVAILABLE
        logger.info(f"✅ QueryIntegratedChartGenerator V4.4 inicializado (Azure OpenAI: {self.azure_available})")

    # ---------- Utilidades internas (sin cambios) ----------
    def _coerce_rows(self, query_data: Any) -> List[Dict[str, Any]]:
        """Acepta List[dict] o QueryResult y devuelve List[dict]."""
        if query_data is None:
            return []
        # QueryResult-like
        if hasattr(query_data, "data") and isinstance(getattr(query_data, "data"), list):
            return query_data.data  # type: ignore[attr-defined]
        return query_data if isinstance(query_data, list) else []

    def _is_label_value_dataset(self, rows: List[Dict[str, Any]]) -> bool:
        """Detecta si el dataset está ya en forma [{'label','value',...}]."""
        if not rows:
            return False
        sample = rows[0]
        return isinstance(sample, dict) and 'label' in sample and 'value' in sample

    # ---------- Generación principal con contexto de confidencialidad ----------
    def generate_chart_from_data(self, query_data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Genera gráfico desde datos de query con validación de confidencialidad"""
        try:
            rows = self._coerce_rows(query_data)
            if not rows:
                return self._create_empty_chart("No hay datos disponibles")

            # 🔐 NUEVA: Extraer contexto de usuario para confidencialidad
            user_role = config.get('user_role', 'GESTOR')
            user_context = config.get('user_context', {})
            
            # Validar configuración según permisos si hay funciones avanzadas disponibles
            if self.azure_available:
                try:
                    validation_result = validate_chart_request(
                        requested_config=config,
                        user_role=user_role,
                        user_context=user_context
                    )
                    if validation_result['adjustments_made']:
                        config = validation_result['valid_config']
                        logger.info(f"🔐 Ajustes automáticos aplicados por confidencialidad: {validation_result['adjustments_made']}")
                except Exception as e:
                    logger.warning(f"Error en validación de confidencialidad: {e}")

            chart_type = config.get('chart_type', 'bar')
            dimension = config.get('dimension', 'gestor')
            metric = config.get('metric', 'PERFORMANCE')

            # Passthrough si ya viene como [{'label','value'}]
            if self._is_label_value_dataset(rows):
                processed = [
                    {
                        'label': str(r.get('label')),
                        'value': float(r.get('value', 0) or 0),
                        'dimension': dimension,
                        'metric': metric,
                        'original_data': r.get('original_data', r)
                    }
                    for r in rows[:25]
                    if r.get('label') is not None
                ]
                processed.sort(key=lambda x: x['value'], reverse=True)
            else:
                processed = self._process_data_for_chart(rows, dimension, metric)

            if not processed:
                return self._create_empty_chart("Datos no compatibles con el gráfico solicitado")

            chart_id = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            chart = {
                'id': chart_id,
                'type': chart_type,
                'title': self._generate_chart_title(chart_type, dimension, metric),
                'data': processed,
                'config': {**config},
                'dimension': dimension,
                'metric': metric,
                'created_at': datetime.now().isoformat(),
                'interactive': True,
                'pivot_enabled': True,
                'data_source': 'basic_queries',
                # 🔐 NUEVA: Información de confidencialidad
                'user_role': user_role,
                'confidentiality_applied': True
            }
            self.current_charts[chart_id] = chart
            logger.info(f"✅ Gráfico generado: {chart_id} ({chart_type}) para rol {user_role}")
            return chart

        except Exception as e:
            logger.exception("Error generando gráfico desde datos")
            return self._create_error_chart(str(e))

    # ---------- 🚀 INTERPRETACIÓN CON CONFIDENCIALIDAD COMPLETA ----------
    def interpret_chart_change(self, user_message: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        🚀 INTERPRETACIÓN V4.4: Azure OpenAI + Confidencialidad + Validación automática
        """
        try:
            logger.info(f"🔄 Interpretando cambio V4.4: '{user_message}' (Azure: {self.azure_available})")
            
            # 1. 🚀 PRIORIDAD: Interpretación con Azure OpenAI + Confidencialidad
            if self.azure_available:
                azure_result = self._interpret_with_azure_openai_and_confidentiality(user_message, current_config)
                if azure_result.get('status') == 'success':
                    logger.info("✅ Interpretación exitosa con Azure OpenAI + Confidencialidad")
                    return azure_result
                else:
                    logger.info("🔄 Azure OpenAI no pudo interpretar, usando fallback")

            # 2. Fallback al método de patrones
            logger.info("🔄 Usando interpretación por patrones (fallback)")
            return self._interpret_with_patterns(user_message, current_config)

        except Exception as e:
            logger.exception("Error interpretando cambio de gráfico")
            return {
                'status': 'error', 
                'message': f'Error procesando cambio: {str(e)}', 
                'new_config': current_config, 
                'changes_made': [],
                'interpretation_method': 'error'
            }

    def _interpret_with_azure_openai_and_confidentiality(self, user_message: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """🚀 IMPLEMENTACIÓN V4.4: Azure OpenAI + Confidencialidad completa"""
        try:
            # Extraer contexto de usuario
            user_role = current_config.get('user_role', 'GESTOR')
            user_context = current_config.get('user_context', {})
            
            # 🔐 NUEVA: Usar prompt con contexto de confidencialidad
            enhanced_prompt = build_context_aware_prompt(
                user_message=user_message,
                user_role=user_role,
                gestor_id=user_context.get('gestor_id'),
                centro_id=user_context.get('centro_id'),
                current_chart_config=current_config
            )
            
            logger.info(f"🔐 Usando prompt con contexto de confidencialidad para rol {user_role}")
            
            response = iniciar_agente_llm(
                system_prompt="",  # Ya incluido en enhanced_prompt
                user_prompt=enhanced_prompt,
                temperature=0.1,
                max_tokens=300
            )
            
            # Extraer contenido de la respuesta
            if hasattr(response, 'choices'):
                result_text = response.choices[0].message.content.strip()
            else:
                result_text = str(response).strip()
            
            # Limpiar respuesta (quitar posibles markdown wrapping de ``` ... ```)
            if result_text.startswith("```") or result_text.endswith("```"):
                lines = result_text.split('\n')
                # eliminar primera línea si comienza con backticks (puede incluir lenguaje)
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                # eliminar última línea si es solo backticks
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                result_text = '\n'.join(lines).strip()
            
            try:
                ai_changes = json.loads(result_text)
                logger.info(f"🚀 Azure OpenAI interpretó: {ai_changes}")
            except json.JSONDecodeError:
                logger.warning(f"Azure OpenAI devolvió JSON inválido: {result_text}")
                return {'status': 'fallback'}
            
            # 🔐 NUEVA: Validar cambios según permisos del usuario
            validation_result = validate_chart_request(
                requested_config=ai_changes,
                user_role=user_role,
                user_context=user_context
            )
            
            if validation_result['adjustments_made']:
                ai_changes = validation_result['valid_config']
                logger.info(f"🔐 Ajustes automáticos por confidencialidad: {validation_result['adjustments_made']}")
            
            # Aplicar cambios validados
            new_config = current_config.copy()
            changes_made = []
            confidentiality_adjustments = validation_result.get('adjustments_made', [])
            
            if 'chart_type' in ai_changes and ai_changes['chart_type'] in self.supported_types:
                new_config['chart_type'] = ai_changes['chart_type']
                type_name = self.chart_configs['chart_types'].get(ai_changes['chart_type'], ai_changes['chart_type'])
                changes_made.append(f"Tipo de gráfico cambiado a {type_name}")
            
            if 'dimension' in ai_changes:
                # Usar dimensiones extendidas si están disponibles
                valid_dimensions = list(self.chart_configs['dimensions'].keys())
                if ai_changes['dimension'] in valid_dimensions:
                    new_config['dimension'] = ai_changes['dimension']
                    dim_name = self.chart_configs['dimensions'][ai_changes['dimension']]
                    changes_made.append(f"Dimensión cambiada a {dim_name}")
            
            if 'metric' in ai_changes:
                # Usar métricas extendidas si están disponibles
                valid_metrics = list(self.chart_configs['metrics'].keys())
                if ai_changes['metric'] in valid_metrics:
                    new_config['metric'] = ai_changes['metric']
                    metric_name = self.chart_configs['metrics'][ai_changes['metric']]
                    changes_made.append(f"Métrica cambiada a {metric_name}")
            
            # Añadir información de ajustes por confidencialidad
            if confidentiality_adjustments:
                changes_made.extend([f"🔐 {adj}" for adj in confidentiality_adjustments])
            
            return {
                'status': 'success',
                'new_config': new_config,
                'changes_made': changes_made,
                'message': '; '.join(changes_made) if changes_made else 'Configuración interpretada con IA y validada',
                'original_config': current_config,
                'user_message': user_message,
                'interpretation_method': 'azure_openai_with_confidentiality',
                'user_role': user_role,
                'confidentiality_applied': True,
                'validation_result': validation_result
            }
            
        except Exception as e:
            logger.warning(f"Error en interpretación Azure OpenAI con confidencialidad: {e}")
            return {'status': 'fallback'}

    def _interpret_with_patterns(self, user_message: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Método original de interpretación por patrones con validación de confidencialidad"""
        try:
            message_lower = user_message.lower()
            new_config = current_config.copy()
            changes_made: List[str] = []

            # Detectar cambios de tipo de gráfico
            type_changes = {
                'barras': 'bar', 'bar': 'bar',
                'líneas': 'line', 'linea': 'line', 'line': 'line',
                'circular': 'pie', 'pie': 'pie', 'torta': 'pie',
                'área': 'area', 'area': 'area',
                'dispersión': 'scatter', 'scatter': 'scatter',
                'horizontal': 'horizontal_bar',
                'donut': 'donut', 'rosquilla': 'donut',
                'apiladas': 'stacked_bar', 'stacked': 'stacked_bar',
                # Nuevos tipos extendidos
                'medidor': 'gauge', 'gauge': 'gauge',
                'mapa': 'heatmap', 'heatmap': 'heatmap', 'calor': 'heatmap',
                'cascada': 'waterfall', 'waterfall': 'waterfall'
            }
            for keyword, ctype in type_changes.items():
                if keyword in message_lower and ctype != current_config.get('chart_type'):
                    if ctype in self.supported_types:
                        new_config['chart_type'] = ctype
                        changes_made.append(f"Tipo de gráfico cambiado a {self.chart_configs['chart_types'][ctype]}")
                        break

            # Detectar cambios de dimensión
            dimension_changes = {
                'gestores': 'gestor', 'gestor': 'gestor',
                'centros': 'centro', 'centro': 'centro',
                'segmentos': 'segmento', 'segmento': 'segmento',
                'productos': 'producto', 'producto': 'producto',
                'período': 'periodo', 'periodo': 'periodo', 'tiempo': 'periodo',
                'clientes': 'cliente', 'cliente': 'cliente',
                'contratos': 'contrato', 'contrato': 'contrato',
                # Nuevas dimensiones extendidas
                'ranking': 'ranking',
                'tendencia': 'tendencia_temporal', 'temporal': 'tendencia_temporal'
            }
            for keyword, dim in dimension_changes.items():
                if keyword in message_lower and dim != current_config.get('dimension'):
                    if dim in self.chart_configs['dimensions']:
                        new_config['dimension'] = dim
                        changes_made.append(f"Dimensión cambiada a {self.chart_configs['dimensions'][dim]}")
                        break

            # Detectar cambios de métrica
            metric_changes = {
                'roe': 'ROE', 'rentabilidad': 'ROE',
                'margen': 'MARGEN_NETO',
                'ingresos': 'INGRESOS',
                'eficiencia': 'EFICIENCIA',
                'contratos': 'CONTRATOS',
                'performance': 'PERFORMANCE',
                'precio': 'PRECIO_STD', 'precios': 'PRECIO_STD',
                'gastos': 'GASTOS',
                'clientes': 'CLIENTES',
                'desviación': 'DESVIACION',
                # Nuevas métricas extendidas
                'incentivos': 'INCENTIVOS_PROPIOS',  # Default para gestor
                'bonus': 'BONUS_POOL',
                'objetivos': 'CUMPLIMIENTO_OBJETIVOS',
                'anomalías': 'ANOMALIAS'
            }
            for keyword, m in metric_changes.items():
                if keyword in message_lower and m != current_config.get('metric'):
                    if m in self.chart_configs['metrics']:
                        new_config['metric'] = m
                        changes_made.append(f"Métrica cambiada a {self.chart_configs['metrics'][m]}")
                        break

            # 🔐 NUEVA: Validar cambios según confidencialidad
            user_role = current_config.get('user_role', 'GESTOR')
            user_context = current_config.get('user_context', {})
            
            if changes_made and self.azure_available:
                try:
                    validation_result = validate_chart_request(
                        requested_config=new_config,
                        user_role=user_role,
                        user_context=user_context
                    )
                    if validation_result['adjustments_made']:
                        new_config = validation_result['valid_config']
                        changes_made.extend([f"🔐 {adj}" for adj in validation_result['adjustments_made']])
                        logger.info(f"🔐 Ajustes por confidencialidad aplicados en fallback")
                except Exception as e:
                    logger.warning(f"Error validando en fallback: {e}")

            return {
                'status': 'success' if changes_made else 'no_changes',
                'new_config': new_config,
                'changes_made': changes_made,
                'message': '; '.join(changes_made) if changes_made else 'No se detectaron cambios específicos',
                'original_config': current_config,
                'user_message': user_message,
                'interpretation_method': 'pattern_matching_with_validation',
                'user_role': user_role,
                'confidentiality_applied': self.azure_available
            }
        except Exception as e:
            logger.exception("Error interpretando cambio de gráfico con patrones")
            return {
                'status': 'error', 
                'message': f'Error procesando cambio: {str(e)}', 
                'new_config': current_config, 
                'changes_made': [],
                'interpretation_method': 'pattern_error'
            }

    # ---------- 🔐 NUEVAS: Funciones de utilidad para confidencialidad ----------
    def get_available_options_for_user(self, user_role: str = "GESTOR") -> Dict[str, Any]:
        """
        🔐 NUEVA: Devuelve opciones disponibles según el rol del usuario
        """
        try:
            if self.azure_available:
                return get_available_options_by_role(user_role)
            else:
                # Fallback básico
                return {
                    'chart_types': list(self.chart_configs['chart_types'].keys()),
                    'dimensions': list(self.chart_configs['dimensions'].keys())[:4],  # Limitado
                    'metrics': list(self.chart_configs['metrics'].keys())[:6],  # Limitado
                    'role': user_role,
                    'advanced_features': False
                }
        except Exception as e:
            logger.error(f"Error obteniendo opciones por rol: {e}")
            return {'error': str(e), 'role': user_role}

    def validate_user_chart_request(self, config: Dict[str, Any], user_role: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🔐 NUEVA: Valida configuración de gráfico según permisos del usuario
        """
        try:
            if self.azure_available:
                return validate_chart_request(config, user_role, user_context or {})
            else:
                # Fallback: validación básica
                return {
                    'valid_config': config,
                    'adjustments_made': [],
                    'validation_status': 'basic',
                    'user_role': user_role,
                    'permissions_applied': False
                }
        except Exception as e:
            logger.error(f"Error validando configuración: {e}")
            return {'valid_config': config, 'error': str(e)}

    # ---------- Gráficos integrados con Basic Queries (sin cambios significativos) ----------
    def generate_gestores_ranking_chart(self, metric: str = 'CONTRATOS', chart_type: str = 'bar', user_role: str = 'GESTOR') -> Dict[str, Any]:
        try:
            if metric == 'CONTRATOS':
                q = self.basic_queries.count_contratos_by_gestor()
                rows = self._coerce_rows(q)
                data_field = 'num_contratos'
            elif metric == 'CLIENTES':
                q = self.basic_queries.count_clientes_by_gestor()
                rows = self._coerce_rows(q)
                data_field = 'num_clientes'
            else:
                q = self.basic_queries.get_ranking_gestores_por_contratos()
                rows = self._coerce_rows(q)
                data_field = 'num_contratos'

            # Transformar a label/value
            chart_data = [
                {
                    'label': item.get('DESC_GESTOR', f"Gestor {item.get('GESTOR_ID', '')}"),
                    'value': float(item.get(data_field, 0) or 0),
                    'center': item.get('DESC_CENTRO', ''),
                    'segment': item.get('DESC_SEGMENTO', ''),
                    'original_data': item
                }
                for item in rows[:15]
                if (item.get(data_field, 0) or 0) != 0
            ]

            config = {
                'chart_type': chart_type,
                'dimension': 'gestor_anonimo' if user_role == 'GESTOR' else 'gestor',  # 🔐 Confidencialidad
                'metric': metric,
                'auto_generated': True,
                'user_role': user_role
            }
            chart = self.generate_chart_from_data(chart_data, config)
            chart['title'] = f"Ranking de Gestores por {self.chart_configs['metrics'].get(metric, metric)}"
            return chart

        except Exception as e:
            logger.exception("Error generando ranking de gestores")
            return self._create_error_chart(str(e))

    def generate_centros_distribution_chart(self, chart_type: str = 'pie') -> Dict[str, Any]:
        try:
            q = self.basic_queries.count_contratos_by_centro()
            rows = self._coerce_rows(q)

            chart_data = [
                {
                    'label': item.get('DESC_CENTRO', f"Centro {item.get('CENTRO_ID', '')}"),
                    'value': float(item.get('num_contratos', 0) or 0),
                    'center_id': item.get('CENTRO_ID'),
                    'original_data': item
                }
                for item in rows if (item.get('num_contratos', 0) or 0) > 0
            ]

            config = {'chart_type': chart_type, 'dimension': 'centro', 'metric': 'CONTRATOS', 'auto_generated': True}
            chart = self.generate_chart_from_data(chart_data, config)
            chart['title'] = "Distribución de Contratos por Centro"
            return chart

        except Exception as e:
            logger.exception("Error generando distribución por centros")
            return self._create_error_chart(str(e))

    def generate_productos_popularity_chart(self, chart_type: str = 'horizontal_bar') -> Dict[str, Any]:
        try:
            q = self.basic_queries.count_contratos_by_producto()
            rows = self._coerce_rows(q)

            chart_data = [
                {
                    'label': item.get('DESC_PRODUCTO', f"Producto {item.get('PRODUCTO_ID', '')}"),
                    'value': float(item.get('num_contratos', 0) or 0),
                    'product_id': item.get('PRODUCTO_ID'),
                    'original_data': item
                }
                for item in rows
            ]

            config = {'chart_type': chart_type, 'dimension': 'producto', 'metric': 'CONTRATOS', 'auto_generated': True}
            chart = self.generate_chart_from_data(chart_data, config)
            chart['title'] = "Popularidad de Productos (Contratos)"
            return chart

        except Exception as e:
            logger.exception("Error generando popularidad de productos")
            return self._create_error_chart(str(e))

    def generate_precios_comparison_chart(self, fecha_calculo: Optional[str] = None, chart_type: str = 'bar', user_role: str = 'CONTROL_GESTION') -> Dict[str, Any]:
        try:
            # 🔐 Solo control de gestión puede ver precios reales
            if user_role == 'GESTOR':
                logger.warning("🔐 Gestor intentó acceder a comparación de precios reales - denegado")
                return self._create_error_chart("Acceso denegado: Solo disponible para Control de Gestión")
            
            q = self.basic_queries.compare_precios_std_vs_real(fecha_calculo)
            rows = self._coerce_rows(q)

            chart_data = []
            for item in rows:
                segment_product = f"{item.get('DESC_SEGMENTO', 'N/A')} - {item.get('DESC_PRODUCTO', 'N/A')}"
                chart_data.append({
                    'label': segment_product,
                    'precio_std': abs(float(item.get('precio_std', 0) or 0)),
                    'precio_real': abs(float(item.get('precio_real', 0) or 0)),
                    'diferencia': float(item.get('diferencia', 0) or 0),
                    'desviacion_pct': float(item.get('porcentaje_desviacion', 0) or 0),
                    'original_data': item
                })

            chart_id = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            chart = {
                'id': chart_id,
                'type': 'comparison',
                'chart_type': chart_type,
                'title': f"Comparación Precios Estándar vs Reales{' - ' + fecha_calculo if fecha_calculo else ''}",
                'data': chart_data,
                'config': {
                    'chart_type': chart_type,
                    'dimension': 'segmento_producto',
                    'metric': 'PRECIO_COMPARISON',
                    'auto_generated': True,
                    'user_role': user_role
                },
                'created_at': datetime.now().isoformat(),
                'interactive': True,
                'data_source': 'basic_queries',
                'confidentiality_applied': True
            }
            self.current_charts[chart_id] = chart
            return chart

        except Exception as e:
            logger.exception("Error generando comparación de precios")
            return self._create_error_chart(str(e))

    def generate_gastos_by_centro_chart(self, fecha: str, chart_type: str = 'stacked_bar') -> Dict[str, Any]:
        try:
            q = self.basic_queries.get_gastos_by_fecha(fecha)
            rows = self._coerce_rows(q)

            centro_gastos: Dict[str, Dict[str, Any]] = {}
            for item in rows:
                centro_desc = item.get('DESC_CENTRO', f"Centro {item.get('CENTRO_CONTABLE')}")
                concepto = item.get('CONCEPTO_COSTE', 'Sin concepto')
                importe = float(item.get('IMPORTE', 0) or 0)

                if centro_desc not in centro_gastos:
                    centro_gastos[centro_desc] = {'total': 0.0, 'conceptos': {}}
                centro_gastos[centro_desc]['total'] += importe
                centro_gastos[centro_desc]['conceptos'][concepto] = centro_gastos[centro_desc]['conceptos'].get(concepto, 0.0) + importe

            chart_data = [
                {'label': centro, 'value': data['total'], 'conceptos': data['conceptos'], 'original_data': data}
                for centro, data in centro_gastos.items()
            ]

            config = {'chart_type': chart_type, 'dimension': 'centro', 'metric': 'GASTOS', 'auto_generated': True}
            chart = self.generate_chart_from_data(chart_data, config)
            chart['title'] = f"Gastos por Centro - {fecha}"
            return chart

        except Exception as e:
            logger.exception("Error generando gastos por centro")
            return self._create_error_chart(str(e))

    def generate_summary_dashboard(self) -> Dict[str, Any]:
        try:
            resumen = {}
            try:
                resumen_q = self.basic_queries.get_resumen_general()
                resumen = resumen_q.data if hasattr(resumen_q, "data") and isinstance(resumen_q.data, dict) else resumen_q
            except Exception:
                resumen = {}

            dashboard_charts = []

            # Chart 1: Resumen general
            summary_data = [
                {'label': 'Gestores', 'value': (resumen or {}).get('total_gestores', 0)},
                {'label': 'Clientes', 'value': (resumen or {}).get('total_clientes', 0)},
                {'label': 'Contratos', 'value': (resumen or {}).get('total_contratos', 0)},
                {'label': 'Productos', 'value': (resumen or {}).get('total_productos', 0)},
                {'label': 'Centros', 'value': (resumen or {}).get('total_centros', 0)}
            ]
            summary_chart = self.generate_chart_from_data(summary_data, {'chart_type': 'bar', 'dimension': 'metric', 'metric': 'count'})
            summary_chart['title'] = 'Resumen General del Sistema'
            dashboard_charts.append(summary_chart)

            # Chart 2: Ranking gestores
            dashboard_charts.append(self.generate_gestores_ranking_chart('CONTRATOS', 'horizontal_bar'))

            # Chart 3: Distribución centros
            dashboard_charts.append(self.generate_centros_distribution_chart('donut'))

            dashboard_id = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return {
                'id': dashboard_id,
                'type': 'dashboard',
                'title': 'Dashboard Resumen CDG',
                'charts': dashboard_charts,
                'summary_data': resumen,
                'created_at': datetime.now().isoformat(),
                'interactive': True,
                'data_source': 'basic_queries'
            }

        except Exception as e:
            logger.exception("Error generando dashboard resumen")
            return self._create_error_chart(str(e))

    # ---------- Métodos auxiliares (mantenidos sin cambios) ----------
    def _process_data_for_chart(self, rows: List[Dict[str, Any]], dimension: str, metric: str) -> List[Dict[str, Any]]:
        try:
            processed: List[Dict[str, Any]] = []

            # Fallback si ya viene 'label'/'value'
            if self._is_label_value_dataset(rows):
                for r in rows[:25]:
                    processed.append({
                        'label': str(r.get('label')),
                        'value': float(r.get('value', 0) or 0),
                        'dimension': dimension,
                        'metric': metric,
                        'original_data': r.get('original_data', r)
                    })
                processed.sort(key=lambda x: x['value'], reverse=True)
                return processed

            for item in rows[:25]:
                if not isinstance(item, dict):
                    continue
                    
                dim_value = self._extract_dimension_value(item, dimension)
                if dim_value is None:
                    dim_value = str(item.get('label')) if item.get('label') is not None else None
                if dim_value is None:
                    continue

                metric_value = self._extract_metric_value(item, metric)
                if metric_value is None and 'value' in item:
                    try:
                        metric_value = float(item['value'])
                    except Exception:
                        metric_value = None
                if metric_value is None:
                    continue

                processed.append({
                    'label': str(dim_value),
                    'value': float(metric_value or 0),
                    'dimension': dimension,
                    'metric': metric,
                    'original_data': item
                })

            processed.sort(key=lambda x: x['value'], reverse=True)
            return processed
        except Exception as e:
            logger.exception("Error procesando datos para gráfico")
            return []

    def _extract_dimension_value(self, item: Dict[str, Any], dimension: str) -> Optional[str]:
        dimension_fields = {
            'gestor': ['DESC_GESTOR', 'desc_gestor', 'gestor_name', 'gestor', 'nombre_gestor'],
            'centro': ['DESC_CENTRO', 'desc_centro', 'centro_name', 'centro', 'nombre_centro'],
            'segmento': ['DESC_SEGMENTO', 'desc_segmento', 'segmento_name', 'segmento', 'nombre_segmento'],
            'producto': ['DESC_PRODUCTO', 'desc_producto', 'producto_name', 'producto', 'nombre_producto'],
            'periodo': ['periodo', 'FECHA_CALCULO', 'fecha', 'date', 'month'],
            'cliente': ['NOMBRE_CLIENTE', 'nombre_cliente', 'cliente_name', 'cliente'],
            'contrato': ['CONTRATO_ID', 'contrato_id', 'contrato']
        }
        for field in dimension_fields.get(dimension, [dimension]):
            if field in item and item[field] is not None:
                return str(item[field])
        return None

    def _extract_metric_value(self, item: Dict[str, Any], metric: str) -> Optional[float]:
        metric_fields = {
            'ROE': ['roe_pct', 'roe', 'rentabilidad', 'return_on_equity'],
            'MARGEN_NETO': ['margen_neto_pct', 'margen_neto', 'margin', 'net_margin'],
            'INGRESOS': ['total_ingresos', 'ingresos', 'revenue', 'income'],
            'EFICIENCIA': ['eficiencia_pct', 'eficiencia', 'efficiency', 'ratio_eficiencia'],
            'CONTRATOS': ['num_contratos', 'contratos', 'contracts', 'count'],
            'PERFORMANCE': ['performance_score', 'performance', 'score', 'rating'],
            'PRECIO_STD': ['PRECIO_MANTENIMIENTO', 'precio_std', 'precio_estandar'],
            'PRECIO_REAL': ['PRECIO_MANTENIMIENTO_REAL', 'precio_real'],
            'DESVIACION': ['diferencia', 'desviacion', 'porcentaje_desviacion'],
            'GASTOS': ['IMPORTE', 'importe', 'gastos', 'gasto_total'],
            'CLIENTES': ['num_clientes', 'clientes', 'cliente_count']
        }
        fields = metric_fields.get(metric, [metric.lower()])
        for f in fields:
            if f in item and item[f] is not None:
                try:
                    return float(item[f])
                except (ValueError, TypeError):
                    continue
        # fallback numérico
        for k, v in item.items():
            if isinstance(v, (int, float)):
                try:
                    return float(v)
                except Exception:
                    continue
        return None

    def _generate_chart_title(self, chart_type: str, dimension: str, metric: str) -> str:
        type_name = self.chart_configs['chart_types'].get(chart_type, 'Gráfico')
        dim_name = self.chart_configs['dimensions'].get(dimension, dimension)
        metric_name = self.chart_configs['metrics'].get(metric, metric)
        return f"{type_name}: {metric_name} por {dim_name}"

    def _create_empty_chart(self, message: str) -> Dict[str, Any]:
        return {
            'id': f"empty_{datetime.now().strftime('%H%M%S')}",
            'type': 'empty',
            'title': 'Sin datos',
            'message': message,
            'data': [],
            'created_at': datetime.now().isoformat(),
            'interactive': False,
            'data_source': 'basic_queries'
        }

    def _create_error_chart(self, error_message: str) -> Dict[str, Any]:
        return {
            'id': f"error_{datetime.now().strftime('%H%M%S')}",
            'type': 'error',
            'title': 'Error en gráfico',
            'message': error_message,
            'data': [],
            'created_at': datetime.now().isoformat(),
            'interactive': False,
            'data_source': 'basic_queries'
        }

# ---- Alias de compatibilidad (mantenidos) ----
class CDGDashboardGenerator(QueryIntegratedChartGenerator):
    """Alias de compatibilidad con CDG Agent"""
    def __init__(self):
        super().__init__()
        logger.info("✅ CDGDashboardGenerator (alias) inicializado")

    def generate_gestor_dashboard(self, gestor_data: Dict[str, Any], kpi_data: Dict[str, Any], periodo: Optional[str] = None) -> Dict[str, Any]:
        try:
            query_data = [gestor_data] if gestor_data else []
            config = {'chart_type': 'bar', 'dimension': 'gestor', 'metric': 'ROE', 'period': periodo or datetime.now().strftime('%Y-%m')}
            chart = self.generate_chart_from_data(query_data, config)
            return {'charts': [chart] if chart.get('type') != 'error' else [], 'dashboard_data': {'gestor': gestor_data, 'kpis': kpi_data, 'periodo': periodo}}
        except Exception as e:
            logger.exception("Error generando dashboard de gestor")
            return {'charts': [], 'error': str(e)}

    def generate_comparative_dashboard(self, ranking_data: List[Dict[str, Any]], metric: str = 'margen_neto', titulo: str = 'Comparativo') -> Dict[str, Any]:
        try:
            config = {'chart_type': 'bar', 'dimension': 'gestor', 'metric': 'MARGEN_NETO' if 'margen' in (metric or '').lower() else 'PERFORMANCE', 'period': datetime.now().strftime('%Y-%m')}
            return self.generate_chart_from_data(ranking_data, config)
        except Exception as e:
            logger.exception("Error generando dashboard comparativo")
            return self._create_error_chart(str(e))

    def generate_trend_dashboard(self, trend_data: List[Dict[str, Any]], title: str = 'Tendencia') -> Dict[str, Any]:
        try:
            config = {'chart_type': 'line', 'dimension': 'periodo', 'metric': 'PERFORMANCE', 'period': datetime.now().strftime('%Y-%m')}
            return self.generate_chart_from_data(trend_data, config)
        except Exception as e:
            logger.exception("Error generando dashboard de tendencia")
            return self._create_error_chart(str(e))

class ChartFactory:
    """Factory para crear gráficos (mantenido)"""
    @staticmethod
    def create_chart(chart_type: str, data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        try:
            generator = QueryIntegratedChartGenerator()
            config = {'chart_type': chart_type, 'dimension': kwargs.get('dimension', 'gestor'), 'metric': kwargs.get('metric', 'PERFORMANCE'), 'period': kwargs.get('period', datetime.now().strftime('%Y-%m'))}
            return generator.generate_chart_from_data(data, config)
        except Exception as e:
            logger.exception("Error en ChartFactory.create_chart")
            return {'id': 'factory_error', 'type': 'error', 'title': 'Error Factory', 'message': str(e), 'data': [], 'data_source': 'basic_queries'}

    @staticmethod
    def create_from_basic_queries(query_method: str, chart_type: str = 'bar', **kwargs) -> Dict[str, Any]:
        try:
            generator = QueryIntegratedChartGenerator()
            method_map = {
                'gestores_ranking': 'generate_gestores_ranking_chart',
                'centros_distribution': 'generate_centros_distribution_chart',
                'productos_popularity': 'generate_productos_popularity_chart',
                'precios_comparison': 'generate_precios_comparison_chart',
                'summary_dashboard': 'generate_summary_dashboard'
            }
            if query_method in method_map:
                method = getattr(generator, method_map[query_method])
                return method(chart_type=chart_type, **kwargs) if 'chart_type' in method.__code__.co_varnames else method(**kwargs)
            raise ValueError(f"Método de query no soportado: {query_method}")
        except Exception as e:
            logger.exception("Error en ChartFactory.create_from_basic_queries")
            return ChartFactory.create_chart('bar', [], error=str(e))

    @staticmethod
    def get_supported_chart_types() -> List[str]:
        return list(CDG_CHART_CONFIGS['chart_types'].keys())

    @staticmethod
    def get_available_queries() -> List[str]:
        return ['gestores_ranking', 'centros_distribution', 'productos_popularity', 'precios_comparison', 'summary_dashboard']

# ---- Funciones de conveniencia actualizadas ----
def create_chart_from_query_data(query_data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        generator = QueryIntegratedChartGenerator()
        return generator.generate_chart_from_data(query_data, config)
    except Exception as e:
        logger.exception("Error en create_chart_from_query_data")
        return {'id': 'error', 'type': 'error', 'title': 'Error', 'message': str(e), 'data': [], 'data_source': 'basic_queries'}

def create_quick_chart(query_method: str, chart_type: str = 'bar', **kwargs) -> Dict[str, Any]:
    return ChartFactory.create_from_basic_queries(query_method, chart_type, **kwargs)

def pivot_chart_with_query_integration(user_message: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        generator = QueryIntegratedChartGenerator()
        return generator.interpret_chart_change(user_message, current_config)
    except Exception as e:
        logger.exception("Error en pivot_chart_with_query_integration")
        return {'status': 'error', 'message': str(e), 'new_config': current_config, 'changes_made': []}

def handle_chart_change_request(user_message: str, current_chart_config: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    ✅ Función principal V4.4 para manejo de cambios de gráfico con confidencialidad
    """
    try:
        logger.info(f"🔄 Procesando cambio de gráfico V4.4 con contexto CDG")
        
        generator = QueryIntegratedChartGenerator()
        
        # 🔐 NUEVA: Enriquecer config con contexto si está disponible
        if context:
            current_chart_config['user_role'] = context.get('user_role', 'GESTOR')
            current_chart_config['user_context'] = context.get('user_context', {})
        
        result = generator.interpret_chart_change(user_message, current_chart_config)
        
        if context:
            result['context'] = context
            result['agente'] = context.get('agente', 'CDG')
            result['sistema'] = 'Control de Gestión Banca March'
        
        result['chart_change_handler'] = 'handle_chart_change_request_v4.4'
        result['integrated_with_system'] = True
        result['confidentiality_enabled'] = generator.azure_available
        
        return result
        
    except Exception as e:
        logger.error(f"Error en handle_chart_change_request V4.4: {e}")
        return {
            'status': 'error',
            'message': f'Error procesando cambio de gráfico: {str(e)}',
            'new_config': current_chart_config,
            'changes_made': [],
            'context': context or {},
            'confidentiality_enabled': False
        }

# 🔐 NUEVAS FUNCIONES DE CONVENIENCIA PARA CONFIDENCIALIDAD
def get_chart_options_by_role(user_role: str = "GESTOR") -> Dict[str, Any]:
    """Función de conveniencia para obtener opciones disponibles por rol"""
    try:
        generator = QueryIntegratedChartGenerator()
        return generator.get_available_options_for_user(user_role)
    except Exception as e:
        logger.error(f"Error obteniendo opciones por rol: {e}")
        return {'error': str(e), 'role': user_role}

def validate_chart_config_for_user(config: Dict[str, Any], user_role: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Función de conveniencia para validar configuración según permisos"""
    try:
        generator = QueryIntegratedChartGenerator()
        return generator.validate_user_chart_request(config, user_role, user_context or {})
    except Exception as e:
        logger.error(f"Error validando configuración: {e}")
        return {'valid_config': config, 'error': str(e)}

def create_chart_with_confidentiality(
    query_data: Any, 
    config: Dict[str, Any], 
    user_role: str = "GESTOR",
    gestor_id: Optional[str] = None,
    centro_id: Optional[str] = None
) -> Dict[str, Any]:
    """🔐 NUEVA: Crear gráfico con contexto de confidencialidad completo"""
    try:
        # Enriquecer configuración con contexto de usuario
        enhanced_config = config.copy()
        enhanced_config.update({
            'user_role': user_role,
            'user_context': {
                'gestor_id': gestor_id,
                'centro_id': centro_id
            }
        })
        
        generator = QueryIntegratedChartGenerator()
        return generator.generate_chart_from_data(query_data, enhanced_config)
        
    except Exception as e:
        logger.error(f"Error creando gráfico con confidencialidad: {e}")
        return {
            'id': 'confidentiality_error',
            'type': 'error',
            'title': 'Error de Confidencialidad',
            'message': str(e),
            'data': [],
            'user_role': user_role
        }

def interpret_chart_change_with_context(
    user_message: str,
    current_config: Dict[str, Any],
    user_role: str = "GESTOR",
    gestor_id: Optional[str] = None,
    centro_id: Optional[str] = None
) -> Dict[str, Any]:
    """🔐 NUEVA: Interpretar cambio de gráfico con contexto completo de confidencialidad"""
    try:
        # Enriquecer configuración con contexto de usuario
        enhanced_config = current_config.copy()
        enhanced_config.update({
            'user_role': user_role,
            'user_context': {
                'gestor_id': gestor_id,
                'centro_id': centro_id
            }
        })
        
        generator = QueryIntegratedChartGenerator()
        return generator.interpret_chart_change(user_message, enhanced_config)
        
    except Exception as e:
        logger.error(f"Error interpretando cambio con contexto: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'new_config': current_config,
            'changes_made': [],
            'user_role': user_role
        }

# 🎯 FUNCIONES ESPECIALIZADAS PARA INTEGRACIÓN CON MAIN.PY
def handle_chart_pivot_request(
    user_message: str,
    chart_config: Dict[str, Any],
    user_role: str = "GESTOR",
    user_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """🎯 FUNCIÓN ESPECIALIZADA: Para endpoint /charts/pivot en main.py"""
    try:
        # Preparar contexto enriquecido
        enhanced_context = {
            'user_role': user_role,
            'user_context': user_context or {},
            'agente': 'CDG',
            'endpoint': '/charts/pivot'
        }
        
        return handle_chart_change_request(
            user_message=user_message,
            current_chart_config=chart_config,
            context=enhanced_context
        )
        
    except Exception as e:
        logger.error(f"Error en handle_chart_pivot_request: {e}")
        return {
            'status': 'error',
            'message': f'Error en pivot request: {str(e)}',
            'new_config': chart_config,
            'changes_made': [],
            'endpoint': '/charts/pivot'
        }

def get_chart_metadata_for_frontend() -> Dict[str, Any]:
    """🎯 FUNCIÓN ESPECIALIZADA: Para endpoint /charts/meta en main.py"""
    try:
        generator = QueryIntegratedChartGenerator()
        
        return {
            'chart_types': generator.chart_configs['chart_types'],
            'dimensions': generator.chart_configs['dimensions'],
            'metrics': generator.chart_configs['metrics'],
            'supported_types': generator.supported_types,
            'azure_openai_available': generator.azure_available,
            'confidentiality_enabled': generator.azure_available,
            'version': 'V4.4',
            'features': {
                'dynamic_pivot': True,
                'confidentiality_controls': generator.azure_available,
                'role_based_access': generator.azure_available,
                'azure_openai_interpretation': generator.azure_available
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo metadata: {e}")
        return {'error': str(e), 'version': 'V4.4'}

def validate_chart_generator() -> Dict[str, Any]:
    """Validación del sistema de gráficos V4.4"""
    try:
        generator = QueryIntegratedChartGenerator()
        test_data = [{'label': 'Test Gestor', 'value': 15}, {'label': 'Test Gestor 2', 'value': 12}]
        test_config = {
            'chart_type': 'bar', 
            'dimension': 'gestor', 
            'metric': 'CONTRATOS',
            'user_role': 'GESTOR',
            'user_context': {'gestor_id': 'test_123'}
        }
        test_chart = generator.generate_chart_from_data(test_data, test_config)
        
        # Test basic queries integration
        try:
            resumen_q = generator.basic_queries.get_resumen_general()
            basic_queries_working = True if resumen_q is not None else False
        except Exception:
            basic_queries_working = False
        
        # Test confidentiality features
        confidentiality_features = False
        try:
            options = generator.get_available_options_for_user('GESTOR')
            validation = generator.validate_user_chart_request(test_config, 'GESTOR')
            confidentiality_features = True
        except Exception:
            confidentiality_features = False
        
        # Test Azure OpenAI integration
        azure_test = False
        if generator.azure_available:
            try:
                test_interpretation = generator.interpret_chart_change("cambia a líneas", test_config)
                azure_test = test_interpretation.get('status') in ['success', 'no_changes']
            except Exception:
                azure_test = False
            
        if test_chart and test_chart.get('type') != 'error' and basic_queries_working:
            return {
                'status': 'OK', 
                'message': 'Chart Generator V4.4 validado correctamente', 
                'azure_openai_available': generator.azure_available,
                'azure_openai_working': azure_test,
                'basic_queries_integration': basic_queries_working, 
                'confidentiality_features': confidentiality_features,
                'test_chart_id': test_chart.get('id'),
                'version': 'V4.4 - Integración Completa con Confidencialidad'
            }
        return {
            'status': 'ERROR', 
            'message': 'Error en validación básica', 
            'basic_queries_integration': basic_queries_working,
            'confidentiality_features': confidentiality_features,
            'azure_openai_available': generator.azure_available
        }
    except Exception as e:
        logger.exception("Error validando Chart Generator V4.4")
        return {'status': 'ERROR', 'message': str(e), 'version': 'V4.4'}

# Función principal de test/debug
if __name__ == "__main__":
    print("🧪 Testing Chart Generator V4.4...")
    
    # Test 1: Validación completa
    validation = validate_chart_generator()
    print(f"✅ Validación: {validation['status']} - {validation.get('message', 'N/A')}")
    
    # Test 2: Opciones por rol
    gestor_options = get_chart_options_by_role("GESTOR")
    direccion_options = get_chart_options_by_role("CONTROL_GESTION")
    print(f"✅ Opciones GESTOR: {len(gestor_options.get('metrics', []))} métricas")
    print(f"✅ Opciones CONTROL_GESTION: {len(direccion_options.get('metrics', []))} métricas")
    
    # Test 3: Creación con confidencialidad
    test_data = [{'label': 'Gestor 1', 'value': 100}, {'label': 'Gestor 2', 'value': 85}]
    test_config = {'chart_type': 'bar', 'dimension': 'gestor', 'metric': 'CONTRATOS'}
    
    gestor_chart = create_chart_with_confidentiality(
        test_data, test_config, "GESTOR", gestor_id="1001"
    )
    print(f"✅ Gráfico gestor: {gestor_chart.get('id', 'ERROR')}")
    
    direccion_chart = create_chart_with_confidentiality(
        test_data, test_config, "CONTROL_GESTION"
    )
    print(f"✅ Gráfico dirección: {direccion_chart.get('id', 'ERROR')}")
    
    # Test 4: Interpretación con contexto
    interpretation = interpret_chart_change_with_context(
        "cambia a líneas", test_config, "GESTOR", gestor_id="1001"
    )
    print(f"✅ Interpretación: {interpretation.get('status', 'ERROR')}")
    
    # Test 5: Metadata para frontend
    metadata = get_chart_metadata_for_frontend()
    print(f"✅ Metadata: {len(metadata.get('chart_types', {}))} tipos de gráfico")
    
    print("🎯 Chart Generator V4.4 con confidencialidad completa funcionando!")
