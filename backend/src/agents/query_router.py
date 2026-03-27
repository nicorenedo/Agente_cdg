"""
query_router.py — Router determinista de queries (sin LLM)
===========================================================

Reemplaza los 6 LLM calls secuenciales de _find_predefined_query().
Mapea keywords del mensaje → (catalog, function, params) directamente.

Sesión S40 — Refactorización arquitectura CDG.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DeterministicQueryRouter:
    """
    Busca la función de query adecuada sin llamar al LLM.

    Estructura ROUTE_TABLE:
      - keywords:        strings que deben aparecer en el mensaje (lower)
      - require_personal: True  → necesita gestor_id (query personal)
                          False → no necesita gestor_id (query global)
                          None  → funciona con o sin gestor_id
      - catalog:         nombre del catálogo (gestor / basic / comparative /
                         deviation / period / incentive)
      - function:        nombre exacto del método en el catálogo
      - params_keys:     lista de parámetros a extraer del contexto.
                         Claves reconocidas: 'gestor_id', 'periodo', 'fecha'
                         ('fecha' se rellena con el valor de 'periodo')

    Orden importa: reglas multi-palabra antes que single-keyword.
    """

    ROUTE_TABLE = [
        # ═══════════════════════════════════════════════════════════════
        # BLOQUE 1 — Frases multi-palabra (evaluar antes que keywords simples)
        # ═══════════════════════════════════════════════════════════════

        # Evolución comparativa de gestores sep→oct (CDG, no personal)
        {
            'keywords': [
                'quién mejoró', 'quien mejoró', 'quién empeoró', 'quien empeoró',
                'gestores que retrocedieron', 'gestores que mejoraron',
                'evolución gestores', 'evolucion gestores',
                'retroceso por gestor', 'evolución sep-oct', 'evolucion sep-oct',
                'gestores han empeorado', 'gestores han mejorado',
            ],
            'require_personal': False,
            'catalog': 'comparative',
            'function': 'get_evolucion_gestores_sep_oct',
            'params_keys': [],
        },

        # Ranking / comparativa de gestores por margen (CDG, no personal) — español e inglés
        {
            'keywords': [
                'ranking gestores', 'top gestores', 'mejor gestor', 'peor gestor',
                'comparativa gestores', 'comparar gestores', 'gestores por margen',
                'gestores ordenados', 'lista de gestores',
                # S46: keywords en inglés (substrings que matchean de verdad)
                'top manager', 'best manager', 'worst manager',
                'manager ranking', 'revenue ranking', 'what manager', 'which manager',
                'managers by', 'by revenue',
            ],
            'require_personal': False,
            'catalog': 'comparative',
            'function': 'ranking_gestores_por_margen_enhanced',
            'params_keys': ['periodo'],
        },

        # Desviaciones críticas globales (CDG, no personal)
        {
            'keywords': [
                'desviaciones críticas', 'desviaciones criticas',
                'alertas de precio', 'alertas precio',
                'precio real vs estándar', 'precio real vs std',
                'anomalías de precio', 'anomalias de precio',
            ],
            'require_personal': False,
            'catalog': 'deviation',
            'function': 'detect_precio_desviaciones_criticas_enhanced',
            'params_keys': ['periodo'],
        },

        # KPIs / ROE globales del grupo (CDG, no personal)
        {
            'keywords': [
                'kpis globales', 'kpis consolidado', 'kpi global', 'kpi consolidado',
                'roe del grupo', 'roe grupo',
                'resultados globales', 'resultados del grupo',
                'margen grupo', 'margen global',
                'consolidado del grupo',
            ],
            'require_personal': False,
            'catalog': 'period',
            'function': 'get_periodo_metricas_financieras',
            'params_keys': ['periodo'],
        },

        # Mejores clientes del gestor (personal)
        {
            'keywords': [
                'mejores clientes', 'top clientes', 'clientes por margen',
                'clientes por ingresos', 'ranking clientes', 'mis mejores clientes',
            ],
            'require_personal': True,
            'catalog': 'basic',
            'function': 'get_gestor_clientes_con_metricas',
            'params_keys': ['gestor_id', 'periodo'],
        },

        # ═══════════════════════════════════════════════════════════════
        # BLOQUE 2 — Keywords simples personales (requieren gestor_id)
        # ═══════════════════════════════════════════════════════════════

        # ROE / rentabilidad personal
        {
            'keywords': ['roe', 'rentabilidad', 'return on equity', 'retorno'],
            'require_personal': True,
            'catalog': 'gestor',
            'function': 'calculate_roe_gestor_enhanced',
            'params_keys': ['gestor_id', 'periodo'],
        },

        # Gastos / costes personales → calculate_roe porque incluye
        # desglose directos + redistribuidos + beneficio neto
        {
            'keywords': [
                'gastos', 'gasto', 'costes', 'coste', 'coste operativo',
                'cuánto me cuesta', 'estructura de costes', 'gastos directos',
                'gastos redistribuidos', 'gastos del centro',
            ],
            'require_personal': True,
            'catalog': 'gestor',
            'function': 'calculate_roe_gestor_enhanced',
            'params_keys': ['gestor_id', 'periodo'],
        },

        # Evolución mensual personal (sep→oct)
        {
            'keywords': [
                'evolución', 'evolucion', 'sep vs oct', 'sep/oct',
                'variación mensual', 'variacion mensual',
                'septiembre', 'octubre', 'cambio de mes', 'mes a mes',
            ],
            'require_personal': True,
            'catalog': 'gestor',
            'function': 'compare_gestor_septiembre_octubre',
            'params_keys': ['gestor_id'],
        },

        # Desviaciones precio personal
        {
            'keywords': [
                'desviación', 'desviacion', 'precio real', 'precio estándar',
                'precio std', 'precio standard', 'sobreprecio',
            ],
            'require_personal': True,
            'catalog': 'gestor',
            'function': 'get_desviaciones_precio_gestor_enhanced',
            'params_keys': ['gestor_id', 'periodo'],
        },

        # Clientes del gestor
        {
            'keywords': ['clientes', 'cliente', 'mis clientes'],
            'require_personal': True,
            'catalog': 'basic',
            'function': 'get_gestor_clientes_con_metricas',
            'params_keys': ['gestor_id', 'periodo'],
        },

        # Cartera / contratos personales
        {
            'keywords': ['cartera', 'contratos', 'portafolio', 'mis contratos'],
            'require_personal': True,
            'catalog': 'gestor',
            'function': 'get_cartera_completa_gestor_enhanced',
            'params_keys': ['gestor_id', 'fecha'],  # usa 'fecha' no 'periodo'
        },

        # KPIs / margen / ingresos / performance personal
        {
            'keywords': [
                'margen', 'kpi', 'kpis', 'ingresos', 'resultado', 'resultados',
                'rendimiento', 'performance', 'cómo estoy', 'mis resultados',
                'mis kpis', 'mis ingresos',
            ],
            'require_personal': True,
            'catalog': 'gestor',
            'function': 'get_gestor_performance_enhanced',
            'params_keys': ['gestor_id', 'periodo'],
        },

        # Alertas personales
        {
            'keywords': ['alerta', 'alertas', 'problema', 'problemas', 'riesgo'],
            'require_personal': True,
            'catalog': 'gestor',
            'function': 'get_alertas_criticas_gestor',
            'params_keys': ['gestor_id', 'periodo'],
        },

        # ═══════════════════════════════════════════════════════════════
        # BLOQUE 3 — Keywords que funcionan personal o no personal
        # ═══════════════════════════════════════════════════════════════

        # Incentivos / bonus
        {
            'keywords': [
                'incentivo', 'incentivos', 'bonus', 'comisión', 'comisiones', 'premio',
            ],
            'require_personal': None,
            'catalog': 'incentive',
            'function': 'calculate_incentivo_cumplimiento_objetivos_enhanced',
            'params_keys': ['periodo'],
        },

        # Gastos por período (análisis global, no personal)
        {
            'keywords': ['gastos del período', 'gastos del periodo', 'gastos centrales'],
            'require_personal': False,
            'catalog': 'period',
            'function': 'get_periodo_analisis_gastos',
            'params_keys': ['periodo'],
        },
    ]

    def route(
        self,
        user_message: str,
        context: Optional[Dict] = None,
        is_personal: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Busca la función adecuada sin LLM.

        Args:
            user_message: Texto del usuario.
            context:      Dict con 'gestor_id', 'periodo', 'user_id', etc.
            is_personal:  Hint del clasificador LLM.
                          True  → prioriza rutas personales.
                          False → prioriza rutas no-personales.
                          None  → busca en todas las rutas.

        Returns:
            {found, catalog, function_name, parameters, confidence, reasoning, router}
        """
        msg_lower = (user_message or '').lower()
        context = context or {}
        gestor_id = context.get('gestor_id')
        periodo = context.get('periodo', '2025-10')

        for rule in self.ROUTE_TABLE:
            req = rule['require_personal']

            # Filtrar según is_personal hint
            if is_personal is True and req is False:
                continue   # query personal → omite reglas no-personales
            if is_personal is False and req is True:
                continue   # query no-personal → omite reglas personales

            # Rutas personales necesitan gestor_id disponible
            if req is True and not gestor_id:
                continue

            # Comprobar si algún keyword aparece en el mensaje
            if not any(kw in msg_lower for kw in rule['keywords']):
                continue

            # ── Match encontrado ──────────────────────────────────────
            params = {}
            for key in rule['params_keys']:
                if key == 'gestor_id' and gestor_id:
                    params['gestor_id'] = str(gestor_id)
                elif key in ('periodo', 'fecha'):
                    params[key] = periodo

            matched_kw = next(kw for kw in rule['keywords'] if kw in msg_lower)
            logger.info(
                f"🎯 [ROUTER] '{user_message[:60]}' → "
                f"{rule['catalog']}.{rule['function']} "
                f"(kw='{matched_kw}', params={params})"
            )
            return {
                'found': True,
                'catalog': rule['catalog'],
                'function_name': rule['function'],
                'parameters': params,
                'confidence': 0.95,
                'reasoning': (
                    f"Router determinista: kw='{matched_kw}' → "
                    f"{rule['catalog']}.{rule['function']}"
                ),
                'router': 'deterministic',
            }

        logger.info(
            f"🔍 [ROUTER] Sin match para: '{user_message[:60]}' "
            f"(is_personal={is_personal}, gestor_id={gestor_id})"
        )
        return {'found': False, 'confidence': 0.0, 'router': 'deterministic'}
