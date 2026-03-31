"""
scenario_builder.py — Generador de escenarios pesimista/base/optimista.

Combina forecast Prophet + contexto macro + shocks opcionales.
Genera escenarios con narrativa interpretativa en español bancario.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ScenarioBuilder:

    def build(
        self,
        forecast_scenarios: Dict,
        macro_context: Dict,
        shocks: Dict = None,
        contexto_banco: Dict = None
    ) -> Dict:
        """Construye 3 escenarios enriquecidos con macro y shocks."""

        base_vals = [v['valor'] for v in forecast_scenarios['base']]
        pes_vals = [v['valor'] for v in forecast_scenarios['pesimista']]
        opt_vals = [v['valor'] for v in forecast_scenarios['optimista']]
        periodos = [v['periodo'] for v in forecast_scenarios['base']]
        horizonte = forecast_scenarios.get('horizonte_meses', len(periodos))
        ultimo_real = forecast_scenarios.get('metadata', {}).get('ultimo_valor_real', base_vals[0] if base_vals else 0)

        # Apply macro adjustment
        base_vals = self._apply_macro_adjustment(base_vals, macro_context)
        pes_vals = self._apply_macro_adjustment(pes_vals, macro_context, bias=-0.02)
        opt_vals = self._apply_macro_adjustment(opt_vals, macro_context, bias=+0.01)

        # Apply shocks if provided
        if shocks:
            base_vals = self._apply_shock(base_vals, shocks)
            pes_vals = self._apply_shock(pes_vals, shocks, factor=1.5)
            opt_vals = self._apply_shock(opt_vals, shocks, factor=0.5)

        def _build_scenario(vals, periodos_list):
            return [{'periodo': p, 'valor': round(max(v, 0), 0)} for p, v in zip(periodos_list, vals)]

        base_acum = round(sum(base_vals))
        pes_acum = round(sum(pes_vals))
        opt_acum = round(sum(opt_vals))

        var_base = round((base_vals[-1] - ultimo_real) / max(ultimo_real, 1) * 100, 1) if base_vals and ultimo_real else 0
        var_pes = round((pes_vals[-1] - ultimo_real) / max(ultimo_real, 1) * 100, 1) if pes_vals and ultimo_real else 0
        var_opt = round((opt_vals[-1] - ultimo_real) / max(ultimo_real, 1) * 100, 1) if opt_vals and ultimo_real else 0

        tipos = macro_context.get('tipos_hipotecas_pct', 3.4)

        return {
            'escenario_pesimista': {
                'valores': _build_scenario(pes_vals, periodos),
                'probabilidad': 0.20,
                'narrativa': self._generate_narrativa('pesimista', pes_vals, macro_context, shocks),
                'drivers_riesgo': self._get_drivers_riesgo(macro_context, shocks),
                'ingresos_acumulados': pes_acum,
                'variacion_vs_actual_pct': var_pes,
            },
            'escenario_base': {
                'valores': _build_scenario(base_vals, periodos),
                'probabilidad': 0.60,
                'narrativa': self._generate_narrativa('base', base_vals, macro_context, shocks),
                'supuestos': self._get_supuestos_base(macro_context),
                'ingresos_acumulados': base_acum,
                'variacion_vs_actual_pct': var_base,
            },
            'escenario_optimista': {
                'valores': _build_scenario(opt_vals, periodos),
                'probabilidad': 0.20,
                'narrativa': self._generate_narrativa('optimista', opt_vals, macro_context, shocks),
                'acciones_requeridas': self._get_acciones_optimista(macro_context),
                'ingresos_acumulados': opt_acum,
                'variacion_vs_actual_pct': var_opt,
            },
            'horizonte_meses': horizonte,
            'periodo_base': forecast_scenarios.get('periodo_base', ''),
            'ingresos_actual': round(ultimo_real),
            'contexto_macro_aplicado': True,
            'shocks_aplicados': shocks or {},
            'nota_metodologica': (
                f"Proyecciones basadas en 20 meses de historico (sep-2024 a abr-2026) "
                f"con modelo Prophet (crecimiento logistico, cap dinamico). "
                f"El banco inicio operaciones en sep-2024; el historico corto limita la "
                f"precision de la estacionalidad detectada. Las variaciones interanuales "
                f"reflejan el crecimiento acelerado de la fase de lanzamiento. "
                f"Contexto macro: tipos hipotecarios {tipos:.1f}%, "
                f"impacto {macro_context.get('impacto_hipotecario', 'N/A')} en hipotecas."
            ),
        }

    def compare(self, escenarios: Dict) -> Dict:
        """Tabla comparativa de los 3 escenarios."""
        pes = escenarios['escenario_pesimista']['valores']
        base = escenarios['escenario_base']['valores']
        opt = escenarios['escenario_optimista']['valores']

        tabla = []
        spreads = []
        for i in range(len(base)):
            p_val = pes[i]['valor'] if i < len(pes) else 0
            b_val = base[i]['valor']
            o_val = opt[i]['valor'] if i < len(opt) else 0
            spread = o_val - p_val
            spreads.append(spread)
            tabla.append({
                'periodo': base[i]['periodo'],
                'pesimista': p_val,
                'base': b_val,
                'optimista': o_val,
                'spread': spread,
            })

        mejor_base = max(base, key=lambda x: x['valor']) if base else {}
        spread_promedio = round(sum(spreads) / len(spreads)) if spreads else 0

        return {
            'tabla': tabla,
            'resumen': {
                'mejor_mes_base': mejor_base,
                'spread_promedio': spread_promedio,
                'ingresos_acum_base': escenarios['escenario_base']['ingresos_acumulados'],
                'ingresos_acum_pesimista': escenarios['escenario_pesimista']['ingresos_acumulados'],
                'ingresos_acum_optimista': escenarios['escenario_optimista']['ingresos_acumulados'],
            }
        }

    def _apply_macro_adjustment(self, valores: List[float], macro: Dict, bias: float = 0) -> List[float]:
        """Ajuste conservador por contexto macro. Max ±5%."""
        tipos = macro.get('tipos_hipotecas_pct', 3.4)
        # tipos > 4% → reduce -3%, < 3% → +2%
        if tipos > 4.0:
            adj = -0.03
        elif tipos < 3.0:
            adj = +0.02
        else:
            adj = 0.0

        ipc = macro.get('ipc_spain_pct', 2.5)
        if ipc > 4.0:
            adj -= 0.02

        adj += bias
        adj = max(-0.05, min(0.05, adj))  # Clamp ±5%

        return [round(v * (1 + adj), 2) for v in valores]

    def _apply_shock(self, valores: List[float], shocks: Dict, factor: float = 1.0) -> List[float]:
        """Aplica shocks paramétricos. factor amplifica/atenúa para pes/opt."""
        result = list(valores)
        tipos_pb = shocks.get('tipos_interes', 0)
        capt_pct = shocks.get('captacion_clientes', 0)
        gastos_pct = shocks.get('reduccion_gastos', 0)
        mix_pp = shocks.get('mix_productos', 0)

        for i in range(len(result)):
            adj = 0.0
            # Tipos: +10pb → +0.3% ingresos existentes, -1.5% captación
            if tipos_pb:
                adj += (tipos_pb / 10) * 0.003 * factor  # ingresos existentes
                adj += (tipos_pb / 10) * (-0.015) * min(1.0, (i + 1) / 3) * factor  # captación gradual

            # Captación: efecto gradual
            if capt_pct:
                gradual = min(1.0, (i + 1) / 4)  # 25% mes 1, 100% mes 4
                adj += (capt_pct / 100) * gradual * factor

            # Mix productos: FRV tiene mayor margen, shift positivo = más FRV
            if mix_pp:
                adj += (mix_pp / 100) * 0.008 * factor

            # Reducción gastos no afecta ingresos brutos (se aplica a margen en otro layer)

            result[i] = round(result[i] * (1 + adj), 2)

        return result

    def _generate_narrativa(self, tipo: str, valores: List[float], macro: Dict, shocks: Dict = None) -> str:
        tipos = macro.get('tipos_hipotecas_pct', 3.4)
        impacto_hip = macro.get('impacto_hipotecario', 'NEUTRAL')
        media = round(sum(valores) / len(valores)) if valores else 0

        if tipo == 'pesimista':
            narr = (
                f"En este escenario, los ingresos medios mensuales se situarian en ~{media:,.0f} euros. "
                f"Se materializaria ante una combinacion de menor captacion comercial, "
                f"presion competitiva en pricing o deterioro del entorno macro"
            )
            if shocks:
                narr += f" (shocks aplicados: {shocks})"
            narr += (
                f". Con tipos hipotecarios en {tipos:.1f}% ({impacto_hip.lower().replace('_', ' ')}), "
                f"el principal riesgo es la desaceleracion de la captacion de nuevos contratos."
            )
        elif tipo == 'optimista':
            narr = (
                f"Para alcanzar ingresos medios de ~{media:,.0f} euros/mes seria necesario "
                f"intensificar la actividad comercial: campanas de captacion FRV (mayor margen), "
                f"refuerzo en los centros con mayor potencial de crecimiento, "
                f"y aprovechamiento del entorno de tipos ({tipos:.1f}%) para hipotecas"
            )
            if shocks:
                narr += f" (shocks favorables: {shocks})"
            narr += "."
        else:  # base
            narr = (
                f"Continuando la tendencia actual, los ingresos se estabilizarian en ~{media:,.0f} euros/mes. "
                f"Este escenario asume ritmo de captacion estable, "
                f"contexto macro sin cambios significativos (tipos {tipos:.1f}%), "
                f"y mix de productos similar al actual."
            )

        return narr

    def _get_drivers_riesgo(self, macro: Dict, shocks: Dict = None) -> List[str]:
        drivers = []
        if macro.get('tipos_hipotecas_pct', 0) > 3.5:
            drivers.append('Tipos hipotecarios elevados presionan captacion')
        if macro.get('ipc_spain_pct', 0) > 3.5:
            drivers.append('Inflacion alta erosiona poder adquisitivo')
        drivers.append('Menor ritmo de captacion comercial')
        if shocks and shocks.get('tipos_interes', 0) > 0:
            drivers.append(f'Shock tipos: +{shocks["tipos_interes"]}pb')
        return drivers[:3]

    def _get_supuestos_base(self, macro: Dict) -> List[str]:
        return [
            'Ritmo de captacion comercial estable (~20 contratos/mes)',
            f'Tipos hipotecarios estables en {macro.get("tipos_hipotecas_pct", 3.4):.1f}%',
            'Mix de productos similar al actual (Hip/Dep/FRV)',
        ]

    def _get_acciones_optimista(self, macro: Dict) -> List[str]:
        acciones = ['Campana comercial FRV Q3 (mayor margen: 98%)']
        if macro.get('impacto_hipotecario', '') in ('POSITIVO', 'MODERADO_POSITIVO'):
            acciones.append('Aprovechar entorno favorable para captacion hipotecaria')
        acciones.append('Refuerzo de captacion en centros con menor penetracion (Malaga, Barcelona)')
        return acciones[:3]
