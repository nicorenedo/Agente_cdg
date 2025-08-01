# backend/src/tools/kpi_calculator.py
"""
kpi_calculator.py

Biblioteca centralizada de cálculos de KPIs financieros para el Agente CDG.
Fórmulas estandarizadas específicas para control de gestión bancario.
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class FinancialKPICalculator:
    """
    Calculadora de KPIs financieros específicos para control de gestión bancario
    
    COBERTURA:
    - Margen neto y rentabilidad
    - ROE y ROA bancarios
    - Ratios de eficiencia operativa
    - Métricas de captación y fidelización
    - Análisis de desviaciones presupuestarias
    """
    
    def __init__(self):
        self.precision = 4  # Precisión decimal para cálculos financieros
    
    # =================================================================
    # 1. CÁLCULOS DE MARGEN Y RENTABILIDAD
    # =================================================================
    
    def calculate_margen_neto(self, ingresos: float, gastos: float) -> Dict[str, Any]:
        """
        Cálculo estandarizado de margen neto bancario
        Fórmula: (Ingresos - Gastos) / Ingresos * 100
        
        Returns:
            Dict con margen_neto_pct, beneficio_neto, clasificacion
        """
        try:
            if not ingresos or ingresos <= 0:
                return {
                    'margen_neto_pct': 0.0,
                    'beneficio_neto': 0.0,
                    'clasificacion': 'SIN_INGRESOS',
                    'formula_aplicada': 'División por cero evitada'
                }
            
            beneficio_neto = ingresos - gastos
            margen_neto_pct = round((beneficio_neto / ingresos) * 100, 2)
            
            # Clasificación según estándares bancarios CDG
            if margen_neto_pct >= 20.0:
                clasificacion = 'EXCELENTE'
            elif margen_neto_pct >= 15.0:
                clasificacion = 'BUENO'
            elif margen_neto_pct >= 8.0:
                clasificacion = 'ACEPTABLE'
            elif margen_neto_pct >= 0.0:
                clasificacion = 'BAJO'
            else:
                clasificacion = 'PERDIDAS'
            
            return {
                'margen_neto_pct': margen_neto_pct,
                'beneficio_neto': round(beneficio_neto, 2),
                'clasificacion': clasificacion,
                'formula_aplicada': f'({ingresos} - {gastos}) / {ingresos} * 100'
            }
            
        except Exception as e:
            logger.error(f"Error calculando margen neto: {e}")
            return {
                'margen_neto_pct': 0.0,
                'beneficio_neto': 0.0,
                'clasificacion': 'ERROR',
                'formula_aplicada': f'Error: {str(e)}'
            }
    
    def calculate_roe(self, beneficio_neto: float, patrimonio: float) -> Dict[str, Any]:
        """
        Cálculo de ROE (Return on Equity) bancario
        Fórmula: Beneficio Neto / Patrimonio * 100
        """
        try:
            if not patrimonio or patrimonio <= 0:
                return {
                    'roe_pct': 0.0,
                    'clasificacion': 'SIN_PATRIMONIO',
                    'benchmark_vs_sector': 'N/A'
                }
            
            roe_pct = round((beneficio_neto / patrimonio) * 100, 4)
            
            # Clasificación según benchmarks bancarios
            if roe_pct >= 15.0:
                clasificacion = 'SOBRESALIENTE'
                benchmark = 'Top quartile sector bancario'
            elif roe_pct >= 10.0:
                clasificacion = 'BUENO'
                benchmark = 'Por encima de media sectorial'
            elif roe_pct >= 5.0:
                clasificacion = 'PROMEDIO'
                benchmark = 'En línea con sector'
            elif roe_pct >= 0.0:
                clasificacion = 'BAJO'
                benchmark = 'Por debajo de media sectorial'
            else:
                clasificacion = 'NEGATIVO'
                benchmark = 'Destrucción de valor'
            
            return {
                'roe_pct': roe_pct,
                'clasificacion': clasificacion,
                'benchmark_vs_sector': benchmark,
                'formula_aplicada': f'{beneficio_neto} / {patrimonio} * 100'
            }
            
        except Exception as e:
            logger.error(f"Error calculando ROE: {e}")
            return {'roe_pct': 0.0, 'clasificacion': 'ERROR'}
    
    # =================================================================
    # 2. RATIOS DE EFICIENCIA OPERATIVA
    # =================================================================
    
    def calculate_ratio_eficiencia(self, ingresos: float, gastos: float) -> Dict[str, Any]:
        """
        Ratio de eficiencia operativa: Ingresos / Gastos
        Valores >1.5 considerados eficientes en banca
        """
        try:
            if not gastos or gastos <= 0:
                return {
                    'ratio_eficiencia': float('inf'),
                    'clasificacion': 'GASTOS_NULOS',
                    'interpretacion': 'Sin gastos operativos'
                }
            
            ratio = round(ingresos / gastos, 2)
            
            if ratio >= 2.0:
                clasificacion = 'MUY_EFICIENTE'
                interpretacion = 'Excelente control de costes'
            elif ratio >= 1.5:
                clasificacion = 'EFICIENTE'
                interpretacion = 'Buena gestión operativa'
            elif ratio >= 1.0:
                clasificacion = 'EQUILIBRADO'
                interpretacion = 'Balance aceptable ingresos/gastos'
            else:
                clasificacion = 'INEFICIENTE'
                interpretacion = 'Gastos exceden ingresos'
            
            return {
                'ratio_eficiencia': ratio,
                'clasificacion': clasificacion,
                'interpretacion': interpretacion,
                'formula_aplicada': f'{ingresos} / {gastos}'
            }
            
        except Exception as e:
            logger.error(f"Error calculando ratio eficiencia: {e}")
            return {'ratio_eficiencia': 0.0, 'clasificacion': 'ERROR'}
    
    # =================================================================
    # 3. MÉTRICAS DE CAPTACIÓN Y FIDELIZACIÓN
    # =================================================================
    
    def calculate_crecimiento_captacion(self, clientes_fin: int, clientes_ini: int, 
                                       periodo_dias: int = 30) -> Dict[str, Any]:
        """
        Cálculo de crecimiento en captación de clientes
        """
        try:
            if clientes_ini <= 0:
                return {
                    'crecimiento_absoluto': clientes_fin,
                    'crecimiento_pct': 100.0 if clientes_fin > 0 else 0.0,
                    'tasa_captacion_diaria': round(clientes_fin / periodo_dias, 2),
                    'clasificacion': 'ARRANQUE'
                }
            
            crecimiento_absoluto = clientes_fin - clientes_ini
            crecimiento_pct = round((crecimiento_absoluto / clientes_ini) * 100, 2)
            tasa_diaria = round(crecimiento_absoluto / periodo_dias, 2)
            
            if crecimiento_pct >= 20.0:
                clasificacion = 'CRECIMIENTO_ALTO'
            elif crecimiento_pct >= 10.0:
                clasificacion = 'CRECIMIENTO_MODERADO'
            elif crecimiento_pct >= 0.0:
                clasificacion = 'CRECIMIENTO_LENTO'
            else:
                clasificacion = 'DECRECIMIENTO'
            
            return {
                'crecimiento_absoluto': crecimiento_absoluto,
                'crecimiento_pct': crecimiento_pct,
                'tasa_captacion_diaria': tasa_diaria,
                'clasificacion': clasificacion
            }
            
        except Exception as e:
            logger.error(f"Error calculando crecimiento captación: {e}")
            return {'crecimiento_pct': 0.0, 'clasificacion': 'ERROR'}
    
    # =================================================================
    # 4. ANÁLISIS DE DESVIACIONES PRESUPUESTARIAS
    # =================================================================
    
    def analyze_desviacion_presupuestaria(self, valor_real: float, valor_presupuestado: float) -> Dict[str, Any]:
        """
        Análisis de desviaciones vs presupuesto con clasificación de severidad
        """
        try:
            if not valor_presupuestado or valor_presupuestado == 0:
                return {
                    'desviacion_absoluta': valor_real,
                    'desviacion_pct': 0.0,
                    'nivel_alerta': 'SIN_PRESUPUESTO',
                    'accion_recomendada': 'Definir presupuesto base'
                }
            
            desviacion_absoluta = valor_real - valor_presupuestado
            desviacion_pct = round((desviacion_absoluta / valor_presupuestado) * 100, 2)
            
            # Clasificación según umbrales CDG
            if abs(desviacion_pct) >= 25.0:
                nivel_alerta = 'CRITICA'
                accion = 'Revisión inmediata requerida'
            elif abs(desviacion_pct) >= 15.0:
                nivel_alerta = 'ALTA'
                accion = 'Análisis detallado necesario'
            elif abs(desviacion_pct) >= 8.0:
                nivel_alerta = 'MEDIA'
                accion = 'Monitoreo cercano recomendado'
            else:
                nivel_alerta = 'NORMAL'
                accion = 'Dentro de parámetros aceptables'
            
            return {
                'desviacion_absoluta': round(desviacion_absoluta, 2),
                'desviacion_pct': desviacion_pct,
                'nivel_alerta': nivel_alerta,
                'accion_recomendada': accion,
                'tipo_desviacion': 'POSITIVA' if desviacion_pct > 0 else 'NEGATIVA'
            }
            
        except Exception as e:
            logger.error(f"Error analizando desviación presupuestaria: {e}")
            return {'desviacion_pct': 0.0, 'nivel_alerta': 'ERROR'}
    
    # =================================================================
    # 5. FUNCIONES HELPER PARA INTEGRACIÓN
    # =================================================================
    
    def calculate_kpis_from_data(self, data_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula múltiples KPIs desde una fila de datos unificada
        Ideal para integrar con results de queries existentes
        """
        try:
            ingresos = data_row.get('ingresos_total', 0) or 0
            gastos = data_row.get('gastos_total', 0) or 0
            patrimonio = data_row.get('patrimonio_total', 0) or 0
            
            # Calcular KPIs principales
            margen_result = self.calculate_margen_neto(ingresos, gastos)
            roe_result = self.calculate_roe(margen_result['beneficio_neto'], patrimonio)
            eficiencia_result = self.calculate_ratio_eficiencia(ingresos, gastos)
            
            return {
                'kpis_calculados': {
                    'margen_neto': margen_result,
                    'roe': roe_result,
                    'eficiencia': eficiencia_result
                },
                'resumen_performance': {
                    'margen_neto_pct': margen_result['margen_neto_pct'],
                    'roe_pct': roe_result['roe_pct'],
                    'ratio_eficiencia': eficiencia_result['ratio_eficiencia'],
                    'clasificacion_global': self._get_clasificacion_global(margen_result, roe_result, eficiencia_result)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculando KPIs desde data: {e}")
            return {'error': str(e)}
    
    def _get_clasificacion_global(self, margen_result: Dict, roe_result: Dict, eficiencia_result: Dict) -> str:
        """Clasificación global basada en todos los KPIs"""
        clasificaciones = [
            margen_result.get('clasificacion', ''),
            roe_result.get('clasificacion', ''),
            eficiencia_result.get('clasificacion', '')
        ]
        
        if 'EXCELENTE' in clasificaciones or 'SOBRESALIENTE' in clasificaciones:
            return 'HIGH_PERFORMER'
        elif 'BUENO' in clasificaciones:
            return 'GOOD_PERFORMER'
        elif 'PROMEDIO' in clasificaciones or 'ACEPTABLE' in clasificaciones:
            return 'AVERAGE_PERFORMER'
        else:
            return 'NEEDS_IMPROVEMENT'

# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# =================================================================

# Instancia global para uso en toda la aplicación
kpi_calculator = FinancialKPICalculator()

# Funciones de conveniencia para importación directa
def calculate_margen_neto(ingresos: float, gastos: float) -> Dict[str, Any]:
    """Función de conveniencia para cálculo de margen neto"""
    return kpi_calculator.calculate_margen_neto(ingresos, gastos)

def calculate_roe(beneficio_neto: float, patrimonio: float) -> Dict[str, Any]:
    """Función de conveniencia para cálculo de ROE"""
    return kpi_calculator.calculate_roe(beneficio_neto, patrimonio)

def get_kpis_from_data(data_row: Dict[str, Any]) -> Dict[str, Any]:
    """Función de conveniencia para calcular KPIs desde datos"""
    return kpi_calculator.calculate_kpis_from_data(data_row)
