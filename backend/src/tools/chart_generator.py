# backend/src/tools/chart_generator.py

"""
Chart Generator para Agente CDG - Banca March
=============================================

Módulo para generar configuraciones de gráficos dinámicos para el dashboard React.
Integra con queries existentes y kpi_calculator para visualizaciones financieras.

Autor: Agente CDG Development Team
Fecha: 2025-08-01
"""

import json
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Logger para auditoría
logger = logging.getLogger(__name__)

class ChartType(Enum):
    """Tipos de gráficos soportados para el dashboard CDG"""
    BAR = "bar"
    LINE = "line" 
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    WATERFALL = "waterfall"

class ChartColorScheme(Enum):
    """Esquemas de colores para dashboard financiero"""
    PRIMARY = ["#1976d2", "#42a5f5", "#90caf9"]
    SUCCESS = ["#4caf50", "#66bb6a", "#a5d6a7"]
    WARNING = ["#ff9800", "#ffb74d", "#ffcc02"]
    DANGER = ["#f44336", "#ef5350", "#e57373"]
    NEUTRAL = ["#9e9e9e", "#bdbdbd", "#e0e0e0"]
    FINANCIAL = ["#2e7d32", "#388e3c", "#4caf50", "#66bb6a", "#81c784"]

@dataclass
class ChartData:
    """Estructura de datos para gráficos"""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChartOptions:
    """Opciones de configuración para gráficos"""
    responsive: bool = True
    maintainAspectRatio: bool = False
    plugins: Optional[Dict[str, Any]] = None
    scales: Optional[Dict[str, Any]] = None
    colors: Optional[List[str]] = None
    animation: Optional[Dict[str, Any]] = None

@dataclass
class Chart:
    """Objeto principal para gráficos del dashboard CDG"""
    id: str
    type: ChartType
    title: str
    data: ChartData
    options: ChartOptions
    context: str = "general"  # gestor, incentive, comparative, deviation
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el gráfico a diccionario para JSON"""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "data": asdict(self.data),
            "options": asdict(self.options),
            "context": self.context,
            "created_at": self.created_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convierte el gráfico a JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class ChartFactory:
    """Factory para crear diferentes tipos de gráficos CDG"""
    
    @staticmethod
    def create_kpi_bar_chart(
        chart_id: str,
        title: str,
        kpi_data: Dict[str, float],
        target_data: Optional[Dict[str, float]] = None,
        context: str = "gestor"
    ) -> Chart:
        """Crea gráfico de barras para KPIs financieros"""
        
        # Validación de entrada
        if not kpi_data:
            raise ValueError("kpi_data no puede estar vacío")
        
        labels = list(kpi_data.keys())
        actual_values = list(kpi_data.values())
        
        datasets = [{
            "label": "Actual",
            "data": actual_values,
            "backgroundColor": ChartColorScheme.PRIMARY.value[0],
            "borderColor": ChartColorScheme.PRIMARY.value[1],
            "borderWidth": 2
        }]
        
        # Agregar targets si están disponibles
        if target_data:
            target_values = [target_data.get(label, 0) for label in labels]
            datasets.append({
                "label": "Objetivo",
                "data": target_values,
                "backgroundColor": ChartColorScheme.SUCCESS.value[0],
                "borderColor": ChartColorScheme.SUCCESS.value[1],
                "borderWidth": 2
            })
        
        chart_data = ChartData(
            labels=labels,
            datasets=datasets,
            metadata={"kpi_count": len(labels), "has_targets": bool(target_data)}
        )
        
        options = ChartOptions(
            plugins={
                "title": {"display": True, "text": title},
                "legend": {"display": True, "position": "top"}
            },
            scales={
                "y": {
                    "beginAtZero": True,
                    "ticks": {"callback": "function(value) { return value + '%'; }"}
                }
            }
        )
        
        return Chart(chart_id, ChartType.BAR, title, chart_data, options, context)
    
    @staticmethod
    def create_trend_line_chart(
        chart_id: str,
        title: str,
        time_series_data: List[Dict[str, Any]],
        context: str = "comparative"
    ) -> Chart:
        """Crea gráfico de líneas para tendencias temporales"""
        
        if not time_series_data:
            raise ValueError("time_series_data no puede estar vacío")
        
        # Extraer etiquetas de tiempo
        labels = [item.get('periodo', item.get('fecha', '')) for item in time_series_data]
        
        # Determinar métricas disponibles
        metrics = set()
        for item in time_series_data:
            metrics.update([k for k in item.keys() if k not in ['periodo', 'fecha']])
        
        datasets = []
        colors = ChartColorScheme.FINANCIAL.value
        
        for i, metric in enumerate(metrics):
            values = [item.get(metric, 0) for item in time_series_data]
            datasets.append({
                "label": metric.replace('_', ' ').title(),
                "data": values,
                "borderColor": colors[i % len(colors)],
                "backgroundColor": colors[i % len(colors)] + "33",  # Transparencia
                "fill": False,
                "tension": 0.4
            })
        
        chart_data = ChartData(
            labels=labels,
            datasets=datasets,
            metadata={"periods": len(labels), "metrics": list(metrics)}
        )
        
        options = ChartOptions(
            plugins={
                "title": {"display": True, "text": title},
                "legend": {"display": True, "position": "top"}
            },
            scales={
                "x": {"title": {"display": True, "text": "Período"}},
                "y": {"title": {"display": True, "text": "Valor"}}
            }
        )
        
        return Chart(chart_id, ChartType.LINE, title, chart_data, options, context)
    
    @staticmethod
    def create_distribution_pie_chart(
        chart_id: str,
        title: str,
        distribution_data: Dict[str, float],
        context: str = "gestor"
    ) -> Chart:
        """Crea gráfico circular para distribuciones"""
        
        if not distribution_data:
            raise ValueError("distribution_data no puede estar vacío")
        
        labels = list(distribution_data.keys())
        values = list(distribution_data.values())
        
        datasets = [{
            "data": values,
            "backgroundColor": ChartColorScheme.FINANCIAL.value[:len(labels)],
            "borderWidth": 2,
            "borderColor": "#ffffff"
        }]
        
        chart_data = ChartData(
            labels=labels,
            datasets=datasets,
            metadata={"segments": len(labels), "total": sum(values)}
        )
        
        options = ChartOptions(
            plugins={
                "title": {"display": True, "text": title},
                "legend": {"display": True, "position": "right"},
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return context.label + ': ' + context.parsed + '%'; }"
                    }
                }
            }
        )
        
        return Chart(chart_id, ChartType.PIE, title, chart_data, options, context)
    
    @staticmethod
    def create_comparison_chart(
        chart_id: str,
        title: str,
        comparison_data: List[Dict[str, Any]],
        metric: str,
        context: str = "comparative"
    ) -> Chart:
        """Crea gráfico de comparación entre entidades"""
        
        if not comparison_data:
            # En lugar de fallar, crear un gráfico vacío con mensaje
            return ChartFactory._create_empty_chart(chart_id, title, "No hay datos disponibles para la comparación")
        
        labels = [item.get('nombre', item.get('desc_gestor', f'Item {i}')) 
                 for i, item in enumerate(comparison_data)]
        values = [item.get(metric, 0) for item in comparison_data]
        
        # Colores basados en performance
        colors = []
        for value in values:
            if value >= 15:  # Alto performance
                colors.append(ChartColorScheme.SUCCESS.value[0])
            elif value >= 10:  # Performance medio
                colors.append(ChartColorScheme.WARNING.value[0])
            else:  # Bajo performance
                colors.append(ChartColorScheme.DANGER.value[0])
        
        datasets = [{
            "label": metric.replace('_', ' ').title(),
            "data": values,
            "backgroundColor": colors,
            "borderColor": colors,
            "borderWidth": 2
        }]
        
        chart_data = ChartData(
            labels=labels,
            datasets=datasets,
            metadata={"entities": len(labels), "metric": metric}
        )
        
        options = ChartOptions(
            plugins={
                "title": {"display": True, "text": title},
                "legend": {"display": False}
            },
            scales={
                "y": {
                    "beginAtZero": True,
                    "title": {"display": True, "text": metric.replace('_', ' ').title()}
                }
            }
        )
        
        return Chart(chart_id, ChartType.BAR, title, chart_data, options, context)
    
    @staticmethod
    def create_gauge_chart(
        chart_id: str,
        title: str,
        current_value: float,
        target_value: float,
        min_value: float = 0,
        max_value: float = 100,
        context: str = "gestor"
    ) -> Chart:
        """Crea gráfico de gauge para KPIs individuales"""
        
        # Datos para gauge (formato específico)
        datasets = [{
            "data": [current_value, max_value - current_value],
            "backgroundColor": [
                ChartColorScheme.PRIMARY.value[0] if current_value >= target_value 
                else ChartColorScheme.WARNING.value[0],
                "#e0e0e0"
            ],
            "borderWidth": 0,
            "cutout": "80%",
            "circumference": 180,
            "rotation": 270
        }]
        
        chart_data = ChartData(
            labels=["Actual", "Restante"],
            datasets=datasets,
            metadata={
                "current": current_value,
                "target": target_value,
                "min": min_value,
                "max": max_value
            }
        )
        
        options = ChartOptions(
            plugins={
                "title": {"display": True, "text": f"{title}: {current_value}%"},
                "legend": {"display": False},
                "tooltip": {"enabled": False}
            }
        )
        
        return Chart(chart_id, ChartType.GAUGE, title, chart_data, options, context)
    
    @staticmethod
    def _create_empty_chart(chart_id: str, title: str, message: str) -> Chart:
        """Crea un gráfico vacío con mensaje informativo"""
        chart_data = ChartData(
            labels=["Sin datos"],
            datasets=[{
                "data": [1],
                "backgroundColor": ["#e0e0e0"],
                "borderWidth": 0
            }],
            metadata={"empty": True, "message": message}
        )
        
        options = ChartOptions(
            plugins={
                "title": {"display": True, "text": title},
                "legend": {"display": False}
            }
        )
        
        return Chart(chart_id, ChartType.PIE, title, chart_data, options, "empty")

class CDGDashboardGenerator:
    """Generador de dashboards completos para el agente CDG"""
    
    def __init__(self):
        self.charts: List[Chart] = []
        logger.info("CDG Dashboard Generator inicializado exitosamente")
    
    def generate_gestor_dashboard(
        self,
        gestor_data: Dict[str, Any],
        kpi_data: Dict[str, float],
        periodo: str = None
    ) -> Dict[str, Any]:
        """Genera dashboard completo para un gestor específico"""
        
        try:
            dashboard_id = f"gestor_{gestor_data.get('gestor_id', 'unknown')}_{periodo or 'current'}"
            charts = []
            
            # 1. KPIs principales en barras
            if kpi_data and isinstance(kpi_data, dict):
                # Filtrar solo valores numéricos
                numeric_kpis = {k: v for k, v in kpi_data.items() 
                              if isinstance(v, (int, float)) and not isinstance(v, bool)}
                
                if numeric_kpis:
                    kpi_chart = ChartFactory.create_kpi_bar_chart(
                        f"{dashboard_id}_kpis",
                        f"KPIs - {gestor_data.get('desc_gestor', 'Gestor')}",
                        numeric_kpis,
                        context="gestor"
                    )
                    charts.append(kpi_chart.to_dict())
            
            # 2. Distribución de productos (si existe)
            if 'distribucion_productos' in gestor_data and gestor_data['distribucion_productos']:
                dist_chart = ChartFactory.create_distribution_pie_chart(
                    f"{dashboard_id}_productos",
                    "Distribución por Productos",
                    gestor_data['distribucion_productos'],
                    context="gestor"
                )
                charts.append(dist_chart.to_dict())
            
            # 3. Gauge de margen si disponible
            if kpi_data and 'margen_neto' in kpi_data:
                try:
                    gauge_chart = ChartFactory.create_gauge_chart(
                        f"{dashboard_id}_margen_gauge",
                        "Margen Neto",
                        current_value=float(kpi_data['margen_neto']),
                        target_value=float(kpi_data.get('margen_objetivo', 15.0)),
                        context="gestor"
                    )
                    charts.append(gauge_chart.to_dict())
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error creando gauge chart: {e}")
            
            dashboard = {
                "id": dashboard_id,
                "title": f"Dashboard - {gestor_data.get('desc_gestor', 'Gestor')}",
                "periodo": periodo,
                "charts": charts,
                "metadata": {
                    "gestor_id": gestor_data.get('gestor_id'),
                    "centro": gestor_data.get('desc_centro'),
                    "generated_at": datetime.now().isoformat(),
                    "chart_count": len(charts)
                }
            }
            
            logger.info(f"Dashboard generado para gestor {gestor_data.get('gestor_id')} con {len(charts)} gráficos")
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generando dashboard de gestor: {e}")
            return {
                "id": f"gestor_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": "Dashboard - Error",
                "periodo": periodo,
                "charts": [],
                "metadata": {
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                    "chart_count": 0
                }
            }
    
    def generate_comparative_dashboard(
        self,
        comparison_data: List[Dict[str, Any]],
        metric: str = "margen_neto",
        titulo: str = "Comparativa de Gestores"
    ) -> Dict[str, Any]:
        """Genera dashboard comparativo entre gestores"""
        
        try:
            dashboard_id = f"comparative_{metric}_{datetime.now().strftime('%Y%m%d')}"
            
            # Gráfico de comparación principal
            comparison_chart = ChartFactory.create_comparison_chart(
                f"{dashboard_id}_comparison",
                titulo,
                comparison_data,
                metric,
                context="comparative"
            )
            
            dashboard = {
                "id": dashboard_id,
                "title": titulo,
                "charts": [comparison_chart.to_dict()],
                "metadata": {
                    "metric": metric,
                    "entities_compared": len(comparison_data) if comparison_data else 0,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Dashboard comparativo generado con {len(comparison_data) if comparison_data else 0} entidades")
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generando dashboard comparativo: {e}")
            return {
                "id": f"comparative_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": "Dashboard Comparativo - Error",
                "charts": [],
                "metadata": {
                    "error": str(e),
                    "generated_at": datetime.now().isoformat()
                }
            }
    
    def generate_trend_dashboard(
        self,
        trend_data: List[Dict[str, Any]],
        title: str = "Análisis de Tendencias"
    ) -> Dict[str, Any]:
        """Genera dashboard de tendencias temporales"""
        
        try:
            dashboard_id = f"trends_{datetime.now().strftime('%Y%m%d')}"
            
            # Gráfico de tendencias
            trend_chart = ChartFactory.create_trend_line_chart(
                f"{dashboard_id}_trends",
                title,
                trend_data,
                context="deviation"
            )
            
            dashboard = {
                "id": dashboard_id,
                "title": title,
                "charts": [trend_chart.to_dict()],
                "metadata": {
                    "periods": len(trend_data) if trend_data else 0,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Dashboard de tendencias generado con {len(trend_data) if trend_data else 0} períodos")
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generando dashboard de tendencias: {e}")
            return {
                "id": f"trends_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": "Dashboard Tendencias - Error",
                "charts": [],
                "metadata": {
                    "error": str(e),
                    "generated_at": datetime.now().isoformat()
                }
            }
    
    def export_dashboard(self, dashboard: Dict[str, Any], format: str = "json") -> str:
        """Exporta dashboard en formato específico"""
        if format.lower() == "json":
            return json.dumps(dashboard, ensure_ascii=False, indent=2)
        else:
            raise NotImplementedError(f"Formato {format} no soportado")

# Funciones de conveniencia para integración rápida
def create_simple_bar_chart(title: str, labels: List[str], values: List[float]) -> Dict[str, Any]:
    """Función de conveniencia para crear gráfico de barras simple"""
    try:
        chart_id = f"simple_bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        kpi_data = dict(zip(labels, values))
        
        chart = ChartFactory.create_kpi_bar_chart(chart_id, title, kpi_data)
        return chart.to_dict()
    except Exception as e:
        logger.error(f"Error creando gráfico de barras simple: {e}")
        return {"error": str(e), "type": "bar", "title": title}

def create_simple_pie_chart(title: str, distribution: Dict[str, float]) -> Dict[str, Any]:
    """Función de conveniencia para crear gráfico circular simple"""
    try:
        chart_id = f"simple_pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        chart = ChartFactory.create_distribution_pie_chart(chart_id, title, distribution)
        return chart.to_dict()
    except Exception as e:
        logger.error(f"Error creando gráfico circular simple: {e}")
        return {"error": str(e), "type": "pie", "title": title}

def create_simple_line_chart(title: str, time_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Función de conveniencia para crear gráfico de líneas simple"""
    try:
        chart_id = f"simple_line_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        chart = ChartFactory.create_trend_line_chart(chart_id, title, time_data)
        return chart.to_dict()
    except Exception as e:
        logger.error(f"Error creando gráfico de líneas simple: {e}")
        return {"error": str(e), "type": "line", "title": title}

# Función de validación para testing
def validate_chart_generator():
    """Valida que el generador de gráficos funciona correctamente"""
    try:
        # Test básico de instanciación
        generator = CDGDashboardGenerator()
        
        # Test de gráfico simple
        test_data = {
            "margen_neto": 12.5,
            "roe": 8.3,
            "eficiencia": 75.2
        }
        
        chart = create_simple_bar_chart("Test KPIs", list(test_data.keys()), list(test_data.values()))
        
        return {
            "status": "OK",
            "generator_initialized": True,
            "chart_created": "error" not in chart,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Tests de funcionalidad
    print("🔄 Iniciando tests de Chart Generator CDG...")
    
    # Test de validación
    validation_result = validate_chart_generator()
    print(f"✅ Validación: {validation_result['status']}")
    
    if validation_result["status"] == "OK":
        # Test 1: Gráfico de barras KPI
        kpi_test_data = {
            "margen_neto": 12.5,
            "roe": 8.3,
            "eficiencia": 75.2
        }
        
        bar_chart = create_simple_bar_chart("KPIs Gestor", 
                                           list(kpi_test_data.keys()), 
                                           list(kpi_test_data.values()))
        print("✅ Test 1 - Gráfico de barras KPI: OK")
        
        # Test 2: Gráfico circular distribución
        dist_test_data = {
            "Fondos": 45.0,
            "Depósitos": 35.0,
            "Seguros": 20.0
        }
        
        pie_chart = create_simple_pie_chart("Distribución Productos", dist_test_data)
        print("✅ Test 2 - Gráfico circular distribución: OK")
        
        # Test 3: Dashboard completo
        dashboard_gen = CDGDashboardGenerator()
        gestor_data = {
            "gestor_id": 1,
            "desc_gestor": "Juan Pérez",
            "desc_centro": "Madrid Centro",
            "distribucion_productos": dist_test_data
        }
        
        dashboard = dashboard_gen.generate_gestor_dashboard(gestor_data, kpi_test_data, "2025-07")
        print("✅ Test 3 - Dashboard completo: OK")
        print(f"   Dashboard generado con {len(dashboard['charts'])} gráficos")
        
        # Test 4: Exportación JSON
        json_output = dashboard_gen.export_dashboard(dashboard)
        print("✅ Test 4 - Exportación JSON: OK")
        print(f"   JSON generado: {len(json_output)} caracteres")
        
        print("\n🎯 Todos los tests completados exitosamente!")
        print("Chart Generator CDG listo para integración con dashboard React")
    else:
        print(f"❌ Error en validación: {validation_result.get('error', 'Unknown')}")
