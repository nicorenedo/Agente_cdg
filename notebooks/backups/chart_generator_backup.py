"""
Chart Generator para CDG - Versión 3.2 DEFINITIVA
================================================

🔧 CORRECCIÓN FINAL: Añadido ChartFactory + CDGDashboardGenerator
Generador de gráficos integrado con queries enhanced y pivoteo conversacional

Autor: Agente CDG Development Team
Fecha: 2025-08-29
Versión: 3.2 - DEFINITIVA con todas las clases necesarias
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN DE GRÁFICOS CDG
# ============================================================================

CDG_CHART_CONFIGS = {
    'colors': {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e', 
        'success': '#2ca02c',
        'danger': '#d62728',
        'warning': '#ff9800',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40'
    },
    'chart_types': {
        'bar': 'Gráfico de Barras',
        'line': 'Gráfico de Líneas', 
        'pie': 'Gráfico Circular',
        'area': 'Gráfico de Área',
        'scatter': 'Gráfico de Dispersión',
        'horizontal_bar': 'Barras Horizontales'
    },
    'dimensions': {
        'gestor': 'Gestor',
        'centro': 'Centro',
        'segmento': 'Segmento', 
        'producto': 'Producto',
        'periodo': 'Período'
    },
    'metrics': {
        'ROE': 'Rentabilidad sobre Patrimonio',
        'MARGEN_NETO': 'Margen Neto',
        'INGRESOS': 'Ingresos Totales',
        'EFICIENCIA': 'Eficiencia Operativa',
        'CONTRATOS': 'Número de Contratos',
        'PERFORMANCE': 'Performance General'
    }
}

# ============================================================================
# GENERADOR DE GRÁFICOS INTEGRADO CON QUERIES
# ============================================================================

class QueryIntegratedChartGenerator:
    """
    🚀 Generador de gráficos integrado con sistema de queries enhanced
    
    Capacidades:
    - Generación automática desde query data
    - Pivoteo conversacional de visualizaciones
    - Personalización según preferencias del usuario
    - Integración perfecta con CDG Agent
    """
    
    def __init__(self):
        self.chart_configs = CDG_CHART_CONFIGS
        self.supported_types = list(self.chart_configs['chart_types'].keys())
        self.current_charts = {}
        logger.info("QueryIntegratedChartGenerator inicializado")
    
    def generate_chart_from_data(self, query_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎨 Genera gráfico desde datos de query
        
        Args:
            query_data: Datos del sistema de queries
            config: Configuración del gráfico (tipo, dimensión, métrica)
        
        Returns:
            Dict con el gráfico generado
        """
        try:
            if not query_data:
                return self._create_empty_chart("No hay datos disponibles")
            
            chart_type = config.get('chart_type', 'bar')
            dimension = config.get('dimension', 'gestor')
            metric = config.get('metric', 'performance')
            
            # Procesar datos según el tipo de gráfico
            processed_data = self._process_data_for_chart(query_data, dimension, metric)
            
            if not processed_data:
                return self._create_empty_chart("Datos no compatibles con el gráfico solicitado")
            
            chart_id = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            chart = {
                'id': chart_id,
                'type': chart_type,
                'title': self._generate_chart_title(chart_type, dimension, metric),
                'data': processed_data,
                'config': config.copy(),
                'dimension': dimension,
                'metric': metric,
                'created_at': datetime.now().isoformat(),
                'interactive': True,
                'pivot_enabled': True
            }
            
            # Guardar para futuras interacciones
            self.current_charts[chart_id] = chart
            
            logger.info(f"Gráfico generado: {chart_id} ({chart_type})")
            return chart
            
        except Exception as e:
            logger.error(f"Error generando gráfico desde datos: {e}")
            return self._create_error_chart(str(e))
    
    def interpret_chart_change(self, user_message: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        🧠 Interpreta cambios solicitados por el usuario
        
        Args:
            user_message: Mensaje del usuario sobre cambios
            current_config: Configuración actual del gráfico
        
        Returns:
            Dict con la nueva configuración interpretada
        """
        try:
            message_lower = user_message.lower()
            new_config = current_config.copy()
            changes_made = []
            
            # Detectar cambios de tipo de gráfico
            type_changes = {
                'barras': 'bar',
                'bar': 'bar',
                'líneas': 'line',
                'linea': 'line',
                'line': 'line',
                'circular': 'pie',
                'pie': 'pie',
                'torta': 'pie',
                'área': 'area',
                'area': 'area',
                'dispersión': 'scatter',
                'scatter': 'scatter',
                'horizontal': 'horizontal_bar'
            }
            
            for keyword, chart_type in type_changes.items():
                if keyword in message_lower:
                    if chart_type != current_config.get('chart_type'):
                        new_config['chart_type'] = chart_type
                        changes_made.append(f"Tipo de gráfico cambiado a {self.chart_configs['chart_types'][chart_type]}")
                    break
            
            # Detectar cambios de dimensión
            dimension_changes = {
                'gestor': 'gestor',
                'gestores': 'gestor', 
                'centro': 'centro',
                'centros': 'centro',
                'segmento': 'segmento',
                'segmentos': 'segmento',
                'período': 'periodo',
                'periodo': 'periodo',
                'tiempo': 'periodo'
            }
            
            for keyword, dimension in dimension_changes.items():
                if keyword in message_lower:
                    if dimension != current_config.get('dimension'):
                        new_config['dimension'] = dimension
                        changes_made.append(f"Dimensión cambiada a {self.chart_configs['dimensions'].get(dimension, dimension)}")
                    break
            
            # Detectar cambios de métrica
            metric_changes = {
                'roe': 'ROE',
                'rentabilidad': 'ROE',
                'margen': 'MARGEN_NETO',
                'ingresos': 'INGRESOS',
                'eficiencia': 'EFICIENCIA',
                'contratos': 'CONTRATOS',
                'performance': 'PERFORMANCE'
            }
            
            for keyword, metric in metric_changes.items():
                if keyword in message_lower:
                    if metric != current_config.get('metric'):
                        new_config['metric'] = metric
                        changes_made.append(f"Métrica cambiada a {self.chart_configs['metrics'].get(metric, metric)}")
                    break
            
            result = {
                'status': 'success' if changes_made else 'no_changes',
                'new_config': new_config,
                'changes_made': changes_made,
                'message': '; '.join(changes_made) if changes_made else 'No se detectaron cambios específicos',
                'original_config': current_config,
                'user_message': user_message
            }
            
            logger.info(f"Interpretación de cambio: {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Error interpretando cambio de gráfico: {e}")
            return {
                'status': 'error',
                'message': f'Error procesando cambio: {str(e)}',
                'new_config': current_config,
                'changes_made': []
            }
    
    def _process_data_for_chart(self, query_data: List[Dict[str, Any]], dimension: str, metric: str) -> List[Dict[str, Any]]:
        """Procesa datos de query para formato de gráfico"""
        try:
            processed_data = []
            
            for item in query_data[:20]:  # Limitar a 20 elementos para performance
                if not isinstance(item, dict):
                    continue
                
                # Extraer valor de dimensión
                dim_value = self._extract_dimension_value(item, dimension)
                if dim_value is None:
                    continue
                
                # Extraer valor de métrica
                metric_value = self._extract_metric_value(item, metric)
                if metric_value is None:
                    continue
                
                processed_data.append({
                    'label': str(dim_value),
                    'value': float(metric_value),
                    'dimension': dimension,
                    'metric': metric,
                    'original_data': item
                })
            
            # Ordenar por valor para mejor visualización
            processed_data.sort(key=lambda x: x['value'], reverse=True)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error procesando datos para gráfico: {e}")
            return []
    
    def _extract_dimension_value(self, item: Dict[str, Any], dimension: str) -> Optional[str]:
        """Extrae valor de dimensión del item de datos"""
        dimension_fields = {
            'gestor': ['desc_gestor', 'gestor_name', 'gestor', 'nombre_gestor'],
            'centro': ['desc_centro', 'centro_name', 'centro', 'nombre_centro'],
            'segmento': ['desc_segmento', 'segmento_name', 'segmento', 'nombre_segmento'],
            'producto': ['desc_producto', 'producto_name', 'producto', 'nombre_producto'],
            'periodo': ['periodo', 'fecha', 'date', 'month']
        }
        
        fields = dimension_fields.get(dimension, [dimension])
        
        for field in fields:
            if field in item and item[field] is not None:
                return str(item[field])
        
        return None
    
    def _extract_metric_value(self, item: Dict[str, Any], metric: str) -> Optional[float]:
        """Extrae valor de métrica del item de datos"""
        metric_fields = {
            'ROE': ['roe_pct', 'roe', 'rentabilidad', 'return_on_equity'],
            'MARGEN_NETO': ['margen_neto_pct', 'margen_neto', 'margin', 'net_margin'],
            'INGRESOS': ['total_ingresos', 'ingresos', 'revenue', 'income'],
            'EFICIENCIA': ['eficiencia_pct', 'eficiencia', 'efficiency'],
            'CONTRATOS': ['num_contratos', 'contratos', 'contracts', 'count'],
            'PERFORMANCE': ['performance_score', 'performance', 'score', 'rating']
        }
        
        fields = metric_fields.get(metric, [metric.lower()])
        
        for field in fields:
            if field in item and item[field] is not None:
                try:
                    return float(item[field])
                except (ValueError, TypeError):
                    continue
        
        # Fallback: buscar cualquier campo numérico
        for key, value in item.items():
            if isinstance(value, (int, float)) and value != 0:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _generate_chart_title(self, chart_type: str, dimension: str, metric: str) -> str:
        """Genera título descriptivo para el gráfico"""
        type_name = self.chart_configs['chart_types'].get(chart_type, 'Gráfico')
        dim_name = self.chart_configs['dimensions'].get(dimension, dimension)
        metric_name = self.chart_configs['metrics'].get(metric, metric)
        
        return f"{type_name}: {metric_name} por {dim_name}"
    
    def _create_empty_chart(self, message: str) -> Dict[str, Any]:
        """Crea gráfico vacío con mensaje"""
        return {
            'id': f"empty_{datetime.now().strftime('%H%M%S')}",
            'type': 'empty',
            'title': 'Sin datos',
            'message': message,
            'data': [],
            'created_at': datetime.now().isoformat(),
            'interactive': False
        }
    
    def _create_error_chart(self, error_message: str) -> Dict[str, Any]:
        """Crea gráfico de error"""
        return {
            'id': f"error_{datetime.now().strftime('%H%M%S')}",
            'type': 'error',
            'title': 'Error en gráfico',
            'message': error_message,
            'data': [],
            'created_at': datetime.now().isoformat(),
            'interactive': False
        }

# ============================================================================
# 🔧 ALIAS PARA COMPATIBILIDAD CON INTEGRACIONES EXISTENTES
# ============================================================================

# 🆕 CORRECCIÓN: Crear alias CDGDashboardGenerator para compatibilidad
class CDGDashboardGenerator(QueryIntegratedChartGenerator):
    """
    🔧 Alias de compatibilidad para QueryIntegratedChartGenerator
    
    Mantiene compatibilidad con código existente que espera CDGDashboardGenerator
    """
    
    def __init__(self):
        super().__init__()
        logger.info("CDGDashboardGenerator (alias) inicializado")
    
    def generate_gestor_dashboard(self, gestor_data: Dict[str, Any], kpi_data: Dict[str, Any], periodo: Optional[str] = None) -> Dict[str, Any]:
        """Método de compatibilidad para generar dashboard de gestor"""
        try:
            # Convertir datos de gestor a formato de query_data
            query_data = [gestor_data] if gestor_data else []
            
            config = {
                'chart_type': 'bar',
                'dimension': 'gestor',
                'metric': 'ROE',
                'period': periodo or datetime.now().strftime('%Y-%m')
            }
            
            chart = self.generate_chart_from_data(query_data, config)
            
            return {
                'charts': [chart] if chart.get('type') != 'error' else [],
                'dashboard_data': {
                    'gestor': gestor_data,
                    'kpis': kpi_data,
                    'periodo': periodo
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando dashboard de gestor: {e}")
            return {'charts': [], 'error': str(e)}
    
    def generate_comparative_dashboard(self, ranking_data: List[Dict[str, Any]], metric: str = 'margen_neto', titulo: str = 'Comparativo') -> Dict[str, Any]:
        """Método de compatibilidad para dashboard comparativo"""
        try:
            config = {
                'chart_type': 'bar',
                'dimension': 'gestor',
                'metric': 'MARGEN_NETO' if 'margen' in metric.lower() else 'PERFORMANCE',
                'period': datetime.now().strftime('%Y-%m')
            }
            
            return self.generate_chart_from_data(ranking_data, config)
            
        except Exception as e:
            logger.error(f"Error generando dashboard comparativo: {e}")
            return self._create_error_chart(str(e))
    
    def generate_trend_dashboard(self, trend_data: List[Dict[str, Any]], title: str = 'Tendencia') -> Dict[str, Any]:
        """Método de compatibilidad para dashboard de tendencias"""
        try:
            config = {
                'chart_type': 'line',
                'dimension': 'periodo',
                'metric': 'PERFORMANCE',
                'period': datetime.now().strftime('%Y-%m')
            }
            
            return self.generate_chart_from_data(trend_data, config)
            
        except Exception as e:
            logger.error(f"Error generando dashboard de tendencia: {e}")
            return self._create_error_chart(str(e))

# ============================================================================
# 🆕 NUEVA CLASE: ChartFactory (FALTABA ESTA)
# ============================================================================

class ChartFactory:
    """
    🏭 Factory para creación de gráficos - CLASE FALTANTE
    
    Proporciona métodos estáticos para crear diferentes tipos de gráficos
    de manera uniforme y compatible con el sistema CDG.
    """
    
    @staticmethod
    def create_chart(chart_type: str, data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        🎨 Método factory principal para crear gráficos
        
        Args:
            chart_type: Tipo de gráfico ('bar', 'line', 'pie', etc.)
            data: Datos para el gráfico
            **kwargs: Configuración adicional
        
        Returns:
            Dict con el gráfico creado
        """
        try:
            generator = QueryIntegratedChartGenerator()
            
            config = {
                'chart_type': chart_type,
                'dimension': kwargs.get('dimension', 'gestor'),
                'metric': kwargs.get('metric', 'PERFORMANCE'),
                'period': kwargs.get('period', datetime.now().strftime('%Y-%m'))
            }
            
            return generator.generate_chart_from_data(data, config)
            
        except Exception as e:
            logger.error(f"Error en ChartFactory.create_chart: {e}")
            return {
                'id': 'factory_error',
                'type': 'error',
                'title': 'Error Factory',
                'message': str(e),
                'data': []
            }
    
    @staticmethod
    def create_bar_chart(data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """🔧 Método de conveniencia para gráficos de barras"""
        return ChartFactory.create_chart('bar', data, **kwargs)
    
    @staticmethod
    def create_line_chart(data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """🔧 Método de conveniencia para gráficos de líneas"""
        return ChartFactory.create_chart('line', data, **kwargs)
    
    @staticmethod
    def create_pie_chart(data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """🔧 Método de conveniencia para gráficos circulares"""
        return ChartFactory.create_chart('pie', data, **kwargs)
    
    @staticmethod
    def get_supported_chart_types() -> List[str]:
        """📋 Retorna tipos de gráficos soportados"""
        return list(CDG_CHART_CONFIGS['chart_types'].keys())
    
    @staticmethod
    def validate_chart_config(config: Dict[str, Any]) -> bool:
        """✅ Valida configuración de gráfico"""
        try:
            chart_type = config.get('chart_type')
            if not chart_type or chart_type not in CDG_CHART_CONFIGS['chart_types']:
                return False
            
            dimension = config.get('dimension')
            if dimension and dimension not in CDG_CHART_CONFIGS['dimensions']:
                return False
            
            metric = config.get('metric')
            if metric and metric not in CDG_CHART_CONFIGS['metrics']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando configuración de gráfico: {e}")
            return False

# ============================================================================
# FUNCIONES DE UTILIDAD PARA INTEGRACIÓN EXTERNA
# ============================================================================

def create_chart_from_query_data(query_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    🎨 Función de utilidad para crear gráfico desde query data
    
    Args:
        query_data: Datos del sistema de queries
        config: Configuración del gráfico
    
    Returns:
        Dict con el gráfico generado
    """
    try:
        generator = QueryIntegratedChartGenerator()
        return generator.generate_chart_from_data(query_data, config)
    except Exception as e:
        logger.error(f"Error en create_chart_from_query_data: {e}")
        return {
            'id': 'error',
            'type': 'error',
            'title': 'Error',
            'message': str(e),
            'data': []
        }

def pivot_chart_with_query_integration(user_message: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔄 Función de utilidad para pivoteo conversacional de gráficos
    
    Args:
        user_message: Mensaje del usuario solicitando cambio
        current_config: Configuración actual del gráfico
    
    Returns:
        Dict con resultado del pivoteo
    """
    try:
        generator = QueryIntegratedChartGenerator()
        return generator.interpret_chart_change(user_message, current_config)
    except Exception as e:
        logger.error(f"Error en pivot_chart_with_query_integration: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'new_config': current_config,
            'changes_made': []
        }

def validate_chart_generator() -> Dict[str, Any]:
    """
    ✅ Valida que el Chart Generator esté funcionando correctamente
    
    Returns:
        Dict con resultado de la validación
    """
    try:
        # Test básico de inicialización
        generator = QueryIntegratedChartGenerator()
        
        # Test de generación básica
        test_data = [
            {'desc_gestor': 'Test Gestor', 'roe_pct': 15.5},
            {'desc_gestor': 'Test Gestor 2', 'roe_pct': 12.3}
        ]
        
        test_config = {
            'chart_type': 'bar',
            'dimension': 'gestor',
            'metric': 'ROE'
        }
        
        test_chart = generator.generate_chart_from_data(test_data, test_config)
        
        if test_chart and test_chart.get('type') != 'error':
            return {'status': 'OK', 'message': 'Chart Generator validado correctamente'}
        else:
            return {'status': 'ERROR', 'message': 'Error en test de generación'}
            
    except Exception as e:
        logger.error(f"Error validando Chart Generator: {e}")
        return {'status': 'ERROR', 'message': str(e)}

# ============================================================================
# TESTING Y DEMOSTRACIÓN
# ============================================================================

def demo_chart_generator():
    """🎯 Demostración del Chart Generator"""
    print("🎨 === DEMO CHART GENERATOR COMPLETO ===")
    
    try:
        # Inicializar generador
        generator = QueryIntegratedChartGenerator()
        
        # Datos de prueba
        test_data = [
            {'desc_gestor': 'Juan Pérez', 'roe_pct': 15.5, 'margen_neto_pct': 12.3},
            {'desc_gestor': 'María García', 'roe_pct': 18.2, 'margen_neto_pct': 14.1},
            {'desc_gestor': 'Carlos López', 'roe_pct': 12.7, 'margen_neto_pct': 11.8}
        ]
        
        # Test 1: Generación básica
        print("\n📊 Test 1: Generación básica")
        config1 = {'chart_type': 'bar', 'dimension': 'gestor', 'metric': 'ROE'}
        chart1 = generator.generate_chart_from_data(test_data, config1)
        print(f"✅ Chart ID: {chart1.get('id')}")
        print(f"📈 Título: {chart1.get('title')}")
        print(f"📋 Datos procesados: {len(chart1.get('data', []))}")
        
        # Test 2: Pivoteo conversacional
        print("\n🔄 Test 2: Pivoteo conversacional")
        pivot_result = generator.interpret_chart_change("Cambiar a gráfico circular", config1)
        print(f"✅ Status: {pivot_result['status']}")
        print(f"🔧 Cambios: {pivot_result['changes_made']}")
        
        # Test 3: Compatibilidad CDGDashboardGenerator
        print("\n🔧 Test 3: Compatibilidad CDGDashboardGenerator")
        cdg_generator = CDGDashboardGenerator()
        dashboard = cdg_generator.generate_gestor_dashboard(test_data[0], {'test': True})
        print(f"✅ Dashboard charts: {len(dashboard.get('charts', []))}")
        
        # Test 4: ChartFactory (NUEVO)
        print("\n🏭 Test 4: ChartFactory")
        factory_chart = ChartFactory.create_bar_chart(test_data)
        print(f"✅ Factory chart ID: {factory_chart.get('id')}")
        print(f"📊 Tipos soportados: {ChartFactory.get_supported_chart_types()}")
        
        print("\n🎉 DEMO COMPLETO exitoso!")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")

if __name__ == "__main__":
    demo_chart_generator()
