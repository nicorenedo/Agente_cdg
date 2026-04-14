"""
whatif_simulator.py — Simulador de escenarios what-if.

Traduce shocks paramétricos en escenarios completos.
Orquesta ProphetEngine + MacroContextService + ScenarioBuilder.
"""

import logging
from typing import Dict, List, Optional

from forecast.prophet_engine import ProphetEngine
from forecast.macro_context import MacroContextService
from forecast.scenario_builder import ScenarioBuilder

logger = logging.getLogger(__name__)


SHOCKS_CONFIG = {
    'tipos_interes': {
        'nombre': 'Tipos de interes',
        'descripcion': 'Variacion del Euribor/tipos en puntos basicos',
        'unidad': 'pb',
        'rango_min': -100,
        'rango_max': +200,
        'ejemplo': '+50 = subida de 0.5%',
    },
    'captacion_clientes': {
        'nombre': 'Captacion de clientes',
        'descripcion': 'Variacion % en ritmo de nuevos contratos',
        'unidad': '%',
        'rango_min': -50,
        'rango_max': +50,
        'ejemplo': '-10 = 10% menos contratos nuevos',
    },
    'reduccion_gastos': {
        'nombre': 'Reduccion de gastos',
        'descripcion': 'Reduccion % en gastos operativos directos',
        'unidad': '%',
        'rango_min': 0,
        'rango_max': 30,
        'ejemplo': '15 = reduccion del 15% en gastos',
    },
    'mix_productos': {
        'nombre': 'Mix de productos',
        'descripcion': 'Sesgo hacia FRV (+pp) o Hip (-pp)',
        'unidad': 'pp',
        'rango_min': -20,
        'rango_max': +20,
        'ejemplo': '+10 = 10pp mas peso en FRV',
    },
}


class WhatIfSimulator:

    def __init__(self):
        self.forecast_queries = None  # Injected externally
        self.prophet_engine = ProphetEngine()
        self.macro_service = MacroContextService()
        self.scenario_builder = ScenarioBuilder()

    def simulate(
        self,
        shocks: Dict,
        horizonte_meses: int = 6,
        dimension: str = 'entidad',
        filtro_id: Optional[str] = None
    ) -> Dict:
        """Ejecuta simulacion what-if completa."""
        # Lazy import to avoid circular
        if self.forecast_queries is None:
            from queries.forecast_queries import ForecastQueries
            self.forecast_queries = ForecastQueries()

        df = self.forecast_queries.get_serie_ingresos(dimension=dimension, filtro_id=filtro_id)
        if df.empty:
            return {'error': 'Sin datos historicos para la dimension seleccionada'}

        self.prophet_engine.fit(df)
        forecast = self.prophet_engine.get_scenarios(horizonte_meses=horizonte_meses)
        macro = self.macro_service.get_context()

        escenarios = self.scenario_builder.build(forecast, macro, shocks=shocks)

        # Compute impact analysis
        escenarios_sin_shock = self.scenario_builder.build(forecast, macro, shocks=None)
        base_sin = escenarios_sin_shock['escenario_base']['ingresos_acumulados']
        base_con = escenarios['escenario_base']['ingresos_acumulados']
        impacto_total = round((base_con - base_sin) / max(base_sin, 1) * 100, 1) if base_sin else 0

        impacto_por_shock = {}
        for shock_name, shock_val in shocks.items():
            solo_este = {shock_name: shock_val}
            esc_solo = self.scenario_builder.build(forecast, macro, shocks=solo_este)
            solo_acum = esc_solo['escenario_base']['ingresos_acumulados']
            pct = round((solo_acum - base_sin) / max(base_sin, 1) * 100, 1)
            impacto_por_shock[f'{shock_name}_{shock_val}'] = {'ingresos_pct': pct}

        recomendaciones = self._generate_recommendations(shocks, impacto_total, macro)

        escenarios['analisis_impacto'] = {
            'shocks_aplicados': shocks,
            'impacto_total_pct': impacto_total,
            'impacto_por_shock': impacto_por_shock,
            'recomendaciones': recomendaciones,
            'nota_contexto_banco': (
                'Dado el estadio de crecimiento del banco (operando desde sep-2024), '
                'el principal lever de ingresos es la captacion comercial (nuevos contratos). '
                'Los cambios macro (tipos, IPC) tienen impacto real pero secundario '
                'frente al ritmo de expansion de la cartera.'
            ),
        }

        return escenarios

    def get_shocks_disponibles(self) -> List[Dict]:
        return [
            {**v, 'id': k}
            for k, v in SHOCKS_CONFIG.items()
        ]

    def _generate_recommendations(self, shocks: Dict, impacto_pct: float, macro: Dict) -> List[str]:
        recs = []

        if shocks.get('tipos_interes', 0) > 30:
            recs.append('Priorizar captacion FRV (margen directo 97%) para compensar presion en hipotecario')
        if shocks.get('tipos_interes', 0) < -30:
            recs.append('Aprovechar bajada de tipos para campana agresiva de hipotecas')
        if shocks.get('captacion_clientes', 0) < -5:
            recs.append('Intensificar actividad comercial en centros con menor penetracion')
        if shocks.get('captacion_clientes', 0) > 5:
            recs.append('Asegurar capacidad operativa para absorber crecimiento de cartera')
        if shocks.get('reduccion_gastos', 0) > 10:
            recs.append('Digitalizar procesos para sostener la reduccion de gastos sin impactar servicio')

        if impacto_pct < -5:
            recs.append('Escenario requiere plan de contingencia: revisar objetivos comerciales Q3')
        elif impacto_pct > 10:
            recs.append('Escenario favorable: considerar acelerar inversion en expansion geografica')

        if not recs:
            recs.append('Mantener ritmo de captacion actual y monitorizar entorno macro')

        return recs[:3]
