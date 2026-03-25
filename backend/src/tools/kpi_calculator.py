# backend/src/tools/kpi_calculator.py
"""
kpi_calculator.py

Biblioteca centralizada de cálculos de KPIs financieros para el Agente CDG.
Fórmulas estandarizadas específicas para control de gestión bancario.
VERSIÓN CORREGIDA - Soluciona inconsistencias en cálculo de ROE y otros KPIs.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class KPICalculator:
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
            Dict con margen_neto_pct, beneficio_neto, formula_aplicada
        """
        try:
            ingresos = float(ingresos) if ingresos is not None else 0.0
            gastos = float(gastos) if gastos is not None else 0.0

            if not ingresos or ingresos <= 0:
                return {
                    'margen_neto_pct': 0.0,
                    'beneficio_neto': 0.0,
                    'formula_aplicada': 'División por cero evitada'
                }

            beneficio_neto = round(ingresos - gastos, 2)
            margen_neto_pct = round((beneficio_neto / ingresos) * 100, 2)

            return {
                'margen_neto_pct': margen_neto_pct,
                'beneficio_neto': beneficio_neto,
                'formula_aplicada': f'({ingresos} - {gastos}) / {ingresos} * 100'
            }
        except Exception as e:
            logger.error(f"Error calculando margen neto: {e}")
            return {
                'margen_neto_pct': 0.0,
                'beneficio_neto': 0.0,
                'formula_aplicada': f'Error: {str(e)}'
            }
    
    def calculate_roe(self, beneficio_neto: float, patrimonio: float) -> Dict[str, Any]:
        """
        Cálculo de ROE (Return on Equity) bancario
        Fórmula: Beneficio Neto / Patrimonio * 100
        CORREGIDO: Maneja correctamente beneficio_neto de gestor_queries
        """
        try:
            beneficio_neto = float(beneficio_neto) if beneficio_neto is not None else 0.0
            patrimonio = float(patrimonio) if patrimonio is not None else 0.0
            
            if not patrimonio or patrimonio <= 0:
                return {
                    'roe_pct': 0.0,
                    'formula_aplicada': f'{beneficio_neto} / {patrimonio} * 100 (patrimonio inválido)'
                }

            roe_pct = round((beneficio_neto / patrimonio) * 100, 4)

            return {
                'roe_pct': roe_pct,
                'formula_aplicada': f'{beneficio_neto} / {patrimonio} * 100'
            }
        except Exception as e:
            logger.error(f"Error calculando ROE: {e}")
            return {
                'roe_pct': 0.0,
                'formula_aplicada': f'Error: {str(e)}'
            }
    
    # =================================================================
    # 2. RATIOS DE EFICIENCIA OPERATIVA
    # =================================================================
    
    def calculate_ratio_eficiencia(self, ingresos: float, gastos: float) -> Dict[str, Any]:
        """
        Ratio de eficiencia operativa: Ingresos / Gastos
        Valores >1.5 considerados eficientes en banca
        """
        try:
            ingresos = float(ingresos) if ingresos is not None else 0.0
            gastos = float(gastos) if gastos is not None else 0.0
            
            if not gastos or gastos <= 0:
                return {
                    'ratio_eficiencia': 999999.99,
                    'formula_aplicada': 'Sin gastos operativos'
                }

            ratio = round(ingresos / gastos, 2)

            return {
                'ratio_eficiencia': ratio,
                'formula_aplicada': f'{ingresos} / {gastos}'
            }
        except Exception as e:
            logger.error(f"Error calculando ratio eficiencia: {e}")
            return {'ratio_eficiencia': 0.0}
    
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
                }

            crecimiento_absoluto = clientes_fin - clientes_ini
            crecimiento_pct = round((crecimiento_absoluto / clientes_ini) * 100, 2)
            tasa_diaria = round(crecimiento_absoluto / periodo_dias, 2)

            return {
                'crecimiento_absoluto': crecimiento_absoluto,
                'crecimiento_pct': crecimiento_pct,
                'tasa_captacion_diaria': tasa_diaria,
            }
        except Exception as e:
            logger.error(f"Error calculando crecimiento captación: {e}")
            return {'crecimiento_pct': 0.0}
    
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
            
            tipo = 'NEUTRA' if desviacion_pct == 0 else ('POSITIVA' if desviacion_pct > 0 else 'NEGATIVA')
            
            return {
                'desviacion_absoluta': round(desviacion_absoluta, 2),
                'desviacion_pct': desviacion_pct,
                'nivel_alerta': nivel_alerta,
                'accion_recomendada': accion,
                'tipo_desviacion': tipo
            }
        except Exception as e:
            logger.error(f"Error analizando desviación presupuestaria: {e}")
            return {'desviacion_pct': 0.0, 'nivel_alerta': 'ERROR'}
    
    # =================================================================
    # 5. FUNCIONES HELPER PARA INTEGRACIÓN - CORREGIDAS
    # =================================================================
    
    def calculate_kpis_from_data(self, data_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula múltiples KPIs desde una fila de datos unificada
        CORREGIDO: Mejor mapeo de campos y manejo de datos de entrada
        """
        try:
            ingresos = (
                data_row.get('total_ingresos') or 
                data_row.get('ingresos_total') or
                data_row.get('total_ingresos_gestor') or
                data_row.get('ingresos') or 0
            )
            gastos = (
                data_row.get('total_gastos') or 
                data_row.get('gastos_total') or
                data_row.get('total_gastos_gestor') or
                data_row.get('gastos') or 0
            )
            patrimonio = (
                data_row.get('patrimonio_total') or 
                data_row.get('patrimonio_gestionado') or
                data_row.get('patrimonio') or 0
            )
            # SOLO campos que realmente representan beneficio neto, no porcentajes
            beneficio_neto_directo = (
                data_row.get('beneficio_neto') or
                data_row.get('net_profit') or
                data_row.get('beneficio') or
                data_row.get('resultado_neto')
            )
            
            logger.info(
                f"KPI Calculator inputs: ingresos={ingresos}, gastos={gastos}, "
                f"patrimonio={patrimonio}, beneficio_directo={beneficio_neto_directo}"
            )
            
            margen_result = self.calculate_margen_neto(ingresos, gastos)
            beneficio_para_roe = beneficio_neto_directo if beneficio_neto_directo is not None else margen_result['beneficio_neto']
            roe_result = self.calculate_roe(beneficio_para_roe, patrimonio)
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
                    'nivel_global': self._get_nivel_global(margen_result, roe_result, eficiencia_result)
                }
            }
        except Exception as e:
            logger.error(f"Error calculando KPIs desde data: {e}")
            logger.error(f"Data row recibida: {data_row}")
            return {'error': str(e)}
    
    def _get_nivel_global(self, margen_result: Dict, roe_result: Dict, eficiencia_result: Dict) -> str:
        """Nivel global basado en umbrales numéricos internos (alto/medio/bajo)"""
        margen_pct = margen_result.get('margen_neto_pct', 0)
        roe_pct = roe_result.get('roe_pct', 0)
        ratio = eficiencia_result.get('ratio_eficiencia', 0)

        puntos_altos = sum([margen_pct >= 20, roe_pct >= 15, ratio >= 2.0])
        puntos_bajos = sum([margen_pct < 8, roe_pct < 5, ratio < 1.0])

        if puntos_altos >= 2:
            return 'alto'
        elif puntos_bajos >= 2:
            return 'bajo'
        return 'medio'

    # =================================================================
    # 6. FUNCIÓN ESPECIAL PARA USAR DATOS DE GESTOR_QUERIES
    # =================================================================
    
    def calculate_kpis_from_gestor_data(self, gestor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula KPIs específicamente desde los datos de gestor_queries
        Esto asegura consistencia con los cálculos del módulo gestor_queries
        """
        try:
            ingresos = gestor_data.get('total_ingresos', 0) or 0
            gastos = gestor_data.get('total_gastos', 0) or 0
            patrimonio = gestor_data.get('patrimonio_total', 0) or 0
            beneficio_neto = gestor_data.get('beneficio_neto', None)
            
            # CORREGIDO: solo recalcular si es None (no si es 0)
            if beneficio_neto is None:
                beneficio_neto = ingresos - gastos
            
            roe_result = self.calculate_roe(beneficio_neto, patrimonio)
            margen_result = self.calculate_margen_neto(ingresos, gastos)
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
                    'nivel_global': self._get_nivel_global(margen_result, roe_result, eficiencia_result)
                }
            }
        except Exception as e:
            logger.error(f"Error calculando KPIs desde gestor_data: {e}")
            return {'error': str(e)}


# =================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# =================================================================

kpi_calculator = KPICalculator()

def calculate_margen_neto(ingresos: float, gastos: float) -> Dict[str, Any]:
    return kpi_calculator.calculate_margen_neto(ingresos, gastos)

def calculate_roe(beneficio_neto: float, patrimonio: float) -> Dict[str, Any]:
    return kpi_calculator.calculate_roe(beneficio_neto, patrimonio)

def get_kpis_from_data(data_row: Dict[str, Any]) -> Dict[str, Any]:
    return kpi_calculator.calculate_kpis_from_data(data_row)

def get_kpis_from_gestor_data(gestor_data: Dict[str, Any]) -> Dict[str, Any]:
    return kpi_calculator.calculate_kpis_from_gestor_data(gestor_data)

FinancialKPICalculator = KPICalculator
__all__ = ['KPICalculator', 'FinancialKPICalculator', 'kpi_calculator']
