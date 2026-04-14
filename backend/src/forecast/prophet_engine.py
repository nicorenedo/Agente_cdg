"""
prophet_engine.py — Motor de forecast con Meta Prophet.

growth='logistic' con cap dinámico (max_historico × 1.25).
Entrenado con toda la serie (20 meses) para capturar estacionalidad.
interval_width=0.80 → escenarios al 80% de confianza.
Caché de modelo: no re-entrenar si los datos no cambiaron.
"""

import pandas as pd
import numpy as np
import hashlib
import logging
import warnings
from typing import Dict, Optional

warnings.filterwarnings('ignore', module='prophet')
warnings.filterwarnings('ignore', module='cmdstanpy')
logger = logging.getLogger(__name__)

# Suppress Prophet/Stan verbose output
logging.getLogger('prophet').setLevel(logging.WARNING)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

from prophet import Prophet


MONTH_NAMES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}


class ProphetEngine:

    def __init__(self):
        self._model: Optional[Prophet] = None
        self._cap: float = 0
        self._floor: float = 0
        self._last_data_hash: str = ''
        self._last_forecast: Optional[pd.DataFrame] = None
        self._fit_df: Optional[pd.DataFrame] = None

    def _hash_data(self, df: pd.DataFrame) -> str:
        return hashlib.md5(
            pd.util.hash_pandas_object(df).values.tobytes()
        ).hexdigest()

    def fit(self, df: pd.DataFrame, cap_factor: float = 1.10) -> None:
        """
        Entrena Prophet con growth='logistic'.
        cap = max(y) × cap_factor.
        S86: cap_factor 1.25→1.10, yearly=False, cp=0.005 para proyecciones estables.
        """
        data_hash = self._hash_data(df)
        if data_hash == self._last_data_hash and self._model is not None:
            logger.info("ProphetEngine: usando modelo cacheado")
            return

        self._cap = float(df['y'].max() * cap_factor)
        self._floor = 0.0
        self._fit_df = df.copy()

        df_fit = df.copy()
        df_fit['cap'] = self._cap
        df_fit['floor'] = self._floor

        self._model = Prophet(
            growth='logistic',
            changepoint_prior_scale=0.005,  # S86: very conservative (cap dominates anyway)
            seasonality_prior_scale=0.1,
            yearly_seasonality=False,       # S86: only 20 months — yearly creates spurious waves
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.80,
        )
        self._model.fit(df_fit)
        self._last_data_hash = data_hash
        self._last_forecast = None
        logger.info(f"ProphetEngine: entrenado con {len(df)} puntos, cap={self._cap:,.0f}")

    def predict(self, horizonte_meses: int = 6) -> pd.DataFrame:
        """
        Forecast para N meses. Devuelve solo los periodos futuros.
        Columns: ds, yhat, yhat_lower, yhat_upper.
        """
        if self._model is None:
            raise RuntimeError("Modelo no entrenado. Llama a fit() primero.")

        future = self._model.make_future_dataframe(periods=horizonte_meses, freq='MS')
        future['cap'] = self._cap
        future['floor'] = self._floor

        forecast = self._model.predict(future)
        self._last_forecast = forecast

        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(horizonte_meses).copy()
        # Clip: no negative, no exceeding cap
        result['yhat_lower'] = result['yhat_lower'].clip(lower=0, upper=self._cap)
        result['yhat'] = result['yhat'].clip(lower=0, upper=self._cap)
        result['yhat_upper'] = result['yhat_upper'].clip(lower=0, upper=self._cap)
        return result

    def get_scenarios(self, horizonte_meses: int = 6) -> Dict:
        """
        3 escenarios formateados para frontend.
        """
        pred = self.predict(horizonte_meses)
        ultimo_real = self._fit_df['y'].iloc[-1] if self._fit_df is not None else 0
        periodo_base = self._fit_df['ds'].max().strftime('%Y-%m') if self._fit_df is not None else ''

        base = []
        optimista = []
        pesimista = []
        for _, row in pred.iterrows():
            p = row['ds'].strftime('%Y-%m')
            base.append({'periodo': p, 'valor': round(float(row['yhat']), 0)})
            optimista.append({'periodo': p, 'valor': round(float(row['yhat_upper']), 0)})
            pesimista.append({'periodo': p, 'valor': round(float(row['yhat_lower']), 0)})

        # Growth estimate
        if base:
            crec = round((base[-1]['valor'] - ultimo_real) / max(ultimo_real, 1) * 100, 1)
        else:
            crec = 0

        return {
            'base': base,
            'optimista': optimista,
            'pesimista': pesimista,
            'horizonte_meses': horizonte_meses,
            'periodo_base': periodo_base,
            'cap': round(self._cap, 0),
            'confianza': 0.80,
            'metadata': {
                'crecimiento_esperado_pct': crec,
                'ultimo_valor_real': round(ultimo_real, 0),
            },
        }

    def get_trend_components(self) -> Dict:
        """
        Descomposición de tendencia y estacionalidad.
        """
        if self._last_forecast is None or self._fit_df is None:
            # Run a predict first to populate forecast
            self.predict(horizonte_meses=1)

        fc = self._last_forecast
        if fc is None:
            return {'tendencia': 'sin_datos', 'crecimiento_mensual_medio_pct': 0,
                    'estacionalidad_detectada': False, 'meses_fuertes': [], 'meses_flojos': []}

        # Trend: compare first and last fitted value
        n_hist = len(self._fit_df)
        trend_vals = fc['trend'].iloc[:n_hist]
        if len(trend_vals) > 2:
            monthly_growth = (trend_vals.iloc[-1] - trend_vals.iloc[-6 if len(trend_vals) >= 6 else 0]) / max(abs(trend_vals.iloc[-6 if len(trend_vals) >= 6 else 0]), 1) * 100
            if len(trend_vals) >= 6:
                monthly_growth = monthly_growth / 6
        else:
            monthly_growth = 0

        if monthly_growth > 1:
            tendencia = 'creciente'
        elif monthly_growth < -1:
            tendencia = 'decreciente'
        else:
            tendencia = 'estable'

        # Seasonality: look at yearly component by month
        has_yearly = 'yearly' in fc.columns
        meses_fuertes = []
        meses_flojos = []

        if has_yearly:
            fc_hist = fc.iloc[:n_hist].copy()
            fc_hist['month'] = fc_hist['ds'].dt.month
            seasonal = fc_hist.groupby('month')['yearly'].mean()
            if len(seasonal) >= 6:
                threshold = seasonal.std() * 0.3
                for m, v in seasonal.items():
                    if v > threshold:
                        meses_fuertes.append(MONTH_NAMES_ES.get(m, str(m)))
                    elif v < -threshold:
                        meses_flojos.append(MONTH_NAMES_ES.get(m, str(m)))

        return {
            'tendencia': tendencia,
            'crecimiento_mensual_medio_pct': round(monthly_growth, 1),
            'estacionalidad_detectada': has_yearly and (len(meses_fuertes) > 0 or len(meses_flojos) > 0),
            'meses_fuertes': meses_fuertes,
            'meses_flojos': meses_flojos,
        }
