# Scripts de generación de datos sintéticos

Generaron los 20 meses de datos bancarios sintéticos (sep-2024 a abr-2026)
que alimentan `BM_CONTABILIDAD_CDG.db`.

## Archivos

- `generate_2024_months.py` — genera meses iniciales (sep-2024 a ago-2025)
- `generate_months.py` — genera meses de expansión (sep-2025 a abr-2026)

## Contexto

Los datos simulan una red bancaria con:
- 5 centros finalistas: Madrid, Palma, Barcelona, Málaga, Bilbao
- 30 gestores comerciales con nombres regionales coherentes
- 142 clientes, 351 contratos activos
- 3 productos: Hipotecario, Depósito a Plazo, Fondo Renta Variable (FRV)
- ~19.000 movimientos contables

## Calibraciones aplicadas (S80-S84)

- Depósito recalibrado a margen ~36% (S81)
- Fondeo (660001) imputado solo a Hipotecas (S83)
- Semáforo corregido (S81), redistribución period-aware (S81)
- Todos los gestores con al menos 1 contrato FRV (S84)
