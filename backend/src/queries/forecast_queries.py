"""
forecast_queries.py — Series temporales para el módulo de Proyecciones.
Extrae datos históricos de MOVIMIENTOS_CONTRATOS en formato Prophet (ds, y).
"""

import pandas as pd
import sqlite3
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from config import settings
    DB_PATH = settings.DATABASE_PATH
except Exception:
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'BM_CONTABILIDAD_CDG.db')


class ForecastQueries:

    def _conn(self):
        return sqlite3.connect(DB_PATH)

    def get_serie_ingresos(
        self,
        dimension: str = 'entidad',
        filtro_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Serie temporal de ingresos mensuales en formato Prophet (ds, y)."""
        conn = self._conn()

        if dimension == 'entidad':
            query = """
                SELECT strftime('%Y-%m-01', FECHA) as ds,
                       SUM(CASE WHEN CUENTA_ID LIKE '76%' THEN IMPORTE ELSE 0 END) as y
                FROM MOVIMIENTOS_CONTRATOS
                WHERE CONTRATO_ID IS NOT NULL
                GROUP BY strftime('%Y-%m', FECHA)
                HAVING y > 0
                ORDER BY ds
            """
            df = pd.read_sql_query(query, conn)

        elif dimension == 'centro':
            query = """
                SELECT strftime('%Y-%m-01', mov.FECHA) as ds,
                       SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as y
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
                WHERE mc.CENTRO_CONTABLE = ?
                  AND mov.CONTRATO_ID IS NOT NULL
                GROUP BY strftime('%Y-%m', mov.FECHA)
                HAVING y > 0
                ORDER BY ds
            """
            df = pd.read_sql_query(query, conn, params=(filtro_id,))

        elif dimension == 'gestor':
            query = """
                SELECT strftime('%Y-%m-01', mov.FECHA) as ds,
                       SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as y
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
                WHERE mc.GESTOR_ID = ?
                  AND mov.CONTRATO_ID IS NOT NULL
                GROUP BY strftime('%Y-%m', mov.FECHA)
                HAVING y > 0
                ORDER BY ds
            """
            df = pd.read_sql_query(query, conn, params=(filtro_id,))

        elif dimension == 'producto':
            query = """
                SELECT strftime('%Y-%m-01', mov.FECHA) as ds,
                       SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as y
                FROM MOVIMIENTOS_CONTRATOS mov
                JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
                WHERE mc.PRODUCTO_ID = ?
                  AND mov.CONTRATO_ID IS NOT NULL
                GROUP BY strftime('%Y-%m', mov.FECHA)
                HAVING y > 0
                ORDER BY ds
            """
            df = pd.read_sql_query(query, conn, params=(filtro_id,))
        else:
            df = pd.DataFrame(columns=['ds', 'y'])

        conn.close()
        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
        return df

    def get_serie_contratos_nuevos(
        self,
        dimension: str = 'entidad',
        filtro_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Serie temporal de contratos NUEVOS por mes (FECHA_ALTA en ese mes)."""
        conn = self._conn()

        if dimension == 'entidad':
            query = """
                SELECT strftime('%Y-%m-01', FECHA_ALTA) as ds,
                       CAST(COUNT(*) AS REAL) as y
                FROM MAESTRO_CONTRATOS
                GROUP BY strftime('%Y-%m', FECHA_ALTA)
                ORDER BY ds
            """
            df = pd.read_sql_query(query, conn)
        elif dimension == 'centro':
            query = """
                SELECT strftime('%Y-%m-01', FECHA_ALTA) as ds,
                       CAST(COUNT(*) AS REAL) as y
                FROM MAESTRO_CONTRATOS
                WHERE CENTRO_CONTABLE = ?
                GROUP BY strftime('%Y-%m', FECHA_ALTA)
                ORDER BY ds
            """
            df = pd.read_sql_query(query, conn, params=(filtro_id,))
        else:
            df = pd.DataFrame(columns=['ds', 'y'])

        conn.close()
        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
        return df

    def get_serie_margen(
        self,
        dimension: str = 'entidad',
        filtro_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Serie temporal de margen neto % mensual."""
        conn = self._conn()

        query = """
            SELECT strftime('%Y-%m-01', FECHA) as ds,
                   SUM(CASE WHEN CUENTA_ID LIKE '76%' THEN IMPORTE ELSE 0 END) as ingresos,
                   SUM(CASE WHEN SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69')
                            AND CONTRATO_ID IS NOT NULL THEN ABS(IMPORTE) ELSE 0 END) as gastos_dir
            FROM MOVIMIENTOS_CONTRATOS
            WHERE CONTRATO_ID IS NOT NULL
            GROUP BY strftime('%Y-%m', FECHA)
            HAVING ingresos > 0
            ORDER BY ds
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
            df['y'] = ((df['ingresos'] - df['gastos_dir']) / df['ingresos'] * 100).round(2)
            df = df[['ds', 'y']]
        return df

    def get_dimensiones_disponibles(self) -> dict:
        """Dimensiones disponibles para forecast."""
        conn = self._conn()
        conn.row_factory = sqlite3.Row
        centros = [{'id': r['id'], 'nombre': r['nombre']} for r in conn.execute(
            "SELECT CENTRO_ID as id, DESC_CENTRO as nombre FROM MAESTRO_CENTROS WHERE IND_CENTRO_FINALISTA=1 ORDER BY CENTRO_ID"
        ).fetchall()]
        gestores = [{'id': r['id'], 'nombre': r['nombre']} for r in conn.execute(
            "SELECT GESTOR_ID as id, DESC_GESTOR as nombre FROM MAESTRO_GESTORES ORDER BY GESTOR_ID"
        ).fetchall()]
        productos = [r['DESC_PRODUCTO'] for r in conn.execute(
            "SELECT DESC_PRODUCTO FROM MAESTRO_PRODUCTOS ORDER BY PRODUCTO_ID"
        ).fetchall()]
        conn.close()
        return {'centros': centros, 'gestores': gestores, 'productos': productos}

    def get_metadata_serie(self, df: pd.DataFrame) -> dict:
        """Metadatos de una serie para calibrar Prophet."""
        if df.empty:
            return {'n_puntos': 0, 'cap_recomendado': 0, 'tendencia': 'sin_datos'}

        y_max = float(df['y'].max())
        y_min = float(df['y'].min())
        y_mean = float(df['y'].mean())

        # Tendencia: comparar media última mitad vs primera mitad
        mid = len(df) // 2
        media_primera = df['y'].iloc[:mid].mean() if mid > 0 else y_mean
        media_segunda = df['y'].iloc[mid:].mean()
        if media_segunda > media_primera * 1.05:
            tendencia = 'creciente'
        elif media_segunda < media_primera * 0.95:
            tendencia = 'decreciente'
        else:
            tendencia = 'estable'

        return {
            'n_puntos': len(df),
            'fecha_inicio': df['ds'].min().strftime('%Y-%m'),
            'fecha_fin': df['ds'].max().strftime('%Y-%m'),
            'valor_min': round(y_min, 2),
            'valor_max': round(y_max, 2),
            'valor_medio': round(y_mean, 2),
            'cap_recomendado': round(y_max * 1.25, 2),
            'tendencia': tendencia,
        }


# Global instance
forecast_queries = ForecastQueries()
