import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

# Ajusta este valor según el coste unitario realista que quieras para octubre (por ejemplo, 1,350€)
COSTE_UNITARIO_OBJETIVO = 1350  

with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM MAESTRO_CONTRATOS
        WHERE CENTRO_CONTABLE BETWEEN 1 AND 5
          AND FECHA_ALTA <= '2025-10-31'
    """)
    total_contratos = cursor.fetchone()[0]

    gasto_objetivo = total_contratos * COSTE_UNITARIO_OBJETIVO

    cursor.execute("SELECT SUM(IMPORTE) FROM GASTOS_CENTRO WHERE FECHA = '2025-10-01'")
    gastos_centro = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(ABS(IMPORTE)) FROM MOVIMIENTOS_CONTRATOS WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL AND IMPORTE < 0")
    gastos_operativos = cursor.fetchone()[0] or 0
    gastos_actuales = gastos_centro + gastos_operativos

    if gastos_actuales == 0:
        print("Error: gastos actuales de octubre son 0, ajuste abortado.")
        exit(1)

    factor = gasto_objetivo / gastos_actuales
    print(f"Coste unitario objetivo: €{COSTE_UNITARIO_OBJETIVO:.2f}")
    print(f"Total contratos: {total_contratos}")
    print(f"Gasto objetivo octubre: €{gasto_objetivo:,.2f}")
    print(f"Factor de ajuste aplicado: {factor:.4f}")

    cursor.execute("UPDATE GASTOS_CENTRO SET IMPORTE = ROUND(IMPORTE * ?, 2) WHERE FECHA = '2025-10-01'", (factor,))
    cursor.execute("UPDATE MOVIMIENTOS_CONTRATOS SET IMPORTE = ROUND(IMPORTE * ?, 2) WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL AND IMPORTE < 0", (factor,))
    conn.commit()
    print("Ajuste realizado correctamente.")
    print("Ejecuta ahora python calcular_precios_octubre.py")
