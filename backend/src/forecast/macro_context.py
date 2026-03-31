"""
macro_context.py — Contexto macroeconómico real para el módulo de Proyecciones.

Fuentes:
- BCE MIR: tipos de interés hipotecarios eurozona
- INE IPC: inflación España
- Euribor: valor estático configurable (BCE Euribor endpoint roto en S66)

Caché TTL 24h. Si APIs fallan, usa fallback razonables. Nunca bloquea.
"""

import json
import logging
import time
import urllib.request
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MacroContextService:
    _cache: Dict = {}
    _cache_timestamp: float = 0
    _CACHE_TTL: int = 86400  # 24h

    FALLBACK = {
        'euribor_12m': 2.5,
        'tipos_hipotecas': 3.4,
        'ipc_spain': 2.8,
    }

    def get_context(self) -> Dict:
        now = time.time()
        if self._cache and (now - self._cache_timestamp) < self._CACHE_TTL:
            return self._cache

        tipos = self._fetch_bce_mir()
        ipc = self._fetch_ine_ipc()

        tipos_val = tipos['valor'] if tipos else self.FALLBACK['tipos_hipotecas']
        tipos_hist = tipos['historico'] if tipos else []
        ipc_val = ipc['valor'] if ipc else self.FALLBACK['ipc_spain']
        ipc_hist = ipc['historico'] if ipc else []

        tipos_tend = self._calculate_tendencia(tipos_hist) if len(tipos_hist) >= 2 else 'sin_datos'
        ipc_tend = self._calculate_tendencia(ipc_hist) if len(ipc_hist) >= 2 else 'sin_datos'

        impacto = self._interpret_impacto(tipos_val, ipc_val)
        narrativas = self._generate_narrative(tipos_val, tipos_tend, ipc_val, ipc_tend, impacto)

        alertas = []
        if tipos_val > 4.0:
            alertas.append('Tipos por encima del 4%: riesgo de caida en captacion hipotecaria')
        if ipc_val > 4.0:
            alertas.append('IPC elevado: erosion poder adquisitivo clientes, menor captacion depositos')

        ctx = {
            'tipos_hipotecas_pct': round(tipos_val, 2),
            'tipos_hipotecas_tendencia': tipos_tend,
            'ipc_spain_pct': round(ipc_val, 2),
            'ipc_tendencia': ipc_tend,
            'euribor_12m_pct': self.FALLBACK['euribor_12m'],
            'fecha_actualizacion': time.strftime('%Y-%m'),
            'fuente_tipos': 'BCE MIR' if tipos else 'fallback',
            'fuente_ipc': 'INE' if ipc else 'fallback',
            'impacto_hipotecario': impacto['hipotecario'],
            'impacto_depositos': impacto['depositos'],
            'impacto_frv': impacto['frv'],
            'narrativa_corta': narrativas['corta'],
            'narrativa_completa': narrativas['completa'],
            'alertas': alertas,
        }

        self._cache = ctx
        self._cache_timestamp = now
        return ctx

    def _fetch_bce_mir(self) -> Optional[Dict]:
        """BCE MIR — tipos hipotecarios nuevas operaciones eurozona."""
        try:
            url = 'https://data-api.ecb.europa.eu/service/data/MIR/M.U2.B.A2A.A.R.A.2240.EUR.N?lastNObservations=4'
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                series = data['dataSets'][0]['series']
                for _, v in series.items():
                    obs = v['observations']
                    valores = [float(ov[0]) for _, ov in sorted(obs.items(), key=lambda x: int(x[0]))]
                    return {'valor': valores[-1], 'historico': valores}
        except Exception as e:
            logger.warning(f'BCE MIR fetch failed: {e}')
        return None

    def _fetch_ine_ipc(self) -> Optional[Dict]:
        """INE IPC interanual España."""
        try:
            url = 'https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC206449?nult=4'
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
                items = data.get('Data', [])
                if items:
                    valores = [float(it['Valor']) for it in items]
                    return {'valor': valores[-1], 'historico': valores}
        except Exception as e:
            logger.warning(f'INE IPC fetch failed: {e}')
        return None

    def _calculate_tendencia(self, valores: List[float]) -> str:
        if len(valores) < 2:
            return 'sin_datos'
        media = sum(valores) / len(valores)
        ultimos = valores[-2:]
        media_ultimos = sum(ultimos) / len(ultimos)
        diff = media_ultimos - media
        if diff > 0.1:
            return 'alcista'
        elif diff < -0.1:
            return 'bajista'
        return 'estable'

    def _interpret_impacto(self, tipos: float, ipc: float) -> Dict:
        # Hipotecario
        if tipos < 3.0:
            hip = 'POSITIVO'
        elif tipos < 4.0:
            hip = 'MODERADO_POSITIVO'
        else:
            hip = 'NEGATIVO'

        # Depositos
        if 2.0 <= tipos <= 4.0:
            dep = 'NEUTRAL'
        elif tipos > 4.0:
            dep = 'NEGATIVO'
        else:
            dep = 'POSITIVO'

        # FRV
        if ipc < 3.5:
            frv = 'POSITIVO'
        elif ipc < 5.0:
            frv = 'NEUTRAL'
        else:
            frv = 'NEGATIVO'

        return {'hipotecario': hip, 'depositos': dep, 'frv': frv}

    def _generate_narrative(self, tipos, tipos_tend, ipc, ipc_tend, impacto) -> Dict:
        tend_map = {'alcista': 'al alza', 'bajista': 'a la baja', 'estable': 'estables', 'sin_datos': ''}

        corta = (
            f"Tipos hipotecarios en {tipos:.1f}% ({tend_map.get(tipos_tend, '')}), "
            f"IPC en {ipc:.1f}%. "
        )
        if impacto['hipotecario'] in ('POSITIVO', 'MODERADO_POSITIVO'):
            corta += "Entorno favorable para captacion hipotecaria."
        elif impacto['hipotecario'] == 'NEGATIVO':
            corta += "Presion en captacion hipotecaria por tipos elevados."
        else:
            corta += "Entorno macro neutro para la actividad bancaria."

        completa = (
            f"Los tipos hipotecarios se situan en el {tipos:.1f}% con tendencia {tend_map.get(tipos_tend, 'sin datos claros')}, "
            f"mientras que la inflacion en Espana (IPC) se mantiene en el {ipc:.1f}% ({tend_map.get(ipc_tend, '')}). "
            f"Para el negocio hipotecario, el impacto es {impacto['hipotecario'].lower().replace('_', ' ')}: "
        )
        if tipos < 4.0:
            completa += "los tipos moderados favorecen la demanda de nuevas hipotecas. "
        else:
            completa += "los tipos elevados presionan la demanda de nuevas hipotecas. "

        completa += (
            f"Para depositos, el entorno es {impacto['depositos'].lower()}: "
            f"el banco debe equilibrar el coste de captacion con la necesidad de liquidez. "
            f"Los fondos de inversion se benefician de un entorno de inflacion controlada ({impacto['frv'].lower()}). "
            f"Dado que el banco esta en fase de crecimiento acelerado, "
            f"el principal driver sigue siendo la captacion comercial (nuevos contratos), "
            f"no las condiciones macro."
        )

        return {'corta': corta, 'completa': completa}
