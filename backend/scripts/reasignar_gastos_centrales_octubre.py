#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REDISTRIBUCIÓN DE GASTOS CENTRALES OCTUBRE 2025
==============================================
Redistribuye automáticamente los gastos de centros 6-8 hacia centros 1-5
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def redistribuir_gastos_centrales():
    print("🔄 REDISTRIBUYENDO GASTOS CENTRALES OCTUBRE")
    print("=" * 60)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Obtener gastos de centros centrales (6-8)
        cursor.execute("""
            SELECT SUM(IMPORTE) FROM GASTOS_CENTRO 
            WHERE FECHA = '2025-10-01' AND CENTRO_CONTABLE BETWEEN 6 AND 8
        """)
        gastos_centrales_centro = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT SUM(ABS(IMPORTE)) FROM MOVIMIENTOS_CONTRATOS 
            WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL 
              AND IMPORTE < 0 AND CENTRO_CONTABLE BETWEEN 6 AND 8
        """)
        gastos_centrales_mov = cursor.fetchone()[0] or 0
        
        total_gastos_centrales = gastos_centrales_centro + gastos_centrales_mov
        
        print(f"💰 Gastos centrales a redistribuir:")
        print(f"   • GASTOS_CENTRO (6-8): €{gastos_centrales_centro:,.2f}")
        print(f"   • Gastos operativos (6-8): €{gastos_centrales_mov:,.2f}")
        print(f"   • TOTAL CENTRALES: €{total_gastos_centrales:,.2f}")
        
        if total_gastos_centrales == 0:
            print("✅ No hay gastos centrales que redistribuir")
            return
        
        # 2. Obtener contratos por centro finalista (1-5)
        cursor.execute("""
            SELECT CENTRO_CONTABLE, COUNT(DISTINCT CONTRATO_ID) 
            FROM MAESTRO_CONTRATOS 
            WHERE CENTRO_CONTABLE BETWEEN 1 AND 5 AND FECHA_ALTA <= '2025-10-31'
            GROUP BY CENTRO_CONTABLE
        """)
        contratos_por_centro = dict(cursor.fetchall())
        total_contratos = sum(contratos_por_centro.values())
        
        print(f"\n📊 Contratos finalistas para reparto:")
        for centro in sorted(contratos_por_centro.keys()):
            contratos = contratos_por_centro[centro]
            porcentaje = (contratos / total_contratos) * 100
            print(f"   Centro {centro}: {contratos} contratos ({porcentaje:.1f}%)")
        print(f"   TOTAL: {total_contratos} contratos")
        
        # 3. Redistribuir proporcionalmente
        print(f"\n🔄 Redistribuyendo gastos centrales...")
        
        for centro, num_contratos in contratos_por_centro.items():
            proporcion = num_contratos / total_contratos
            gasto_asignado = total_gastos_centrales * proporcion
            
            print(f"   Centro {centro}: +€{gasto_asignado:,.2f} ({proporcion*100:.1f}%)")
            
            # Añadir gasto redistribuido a GASTOS_CENTRO
            cursor.execute("""
                INSERT INTO GASTOS_CENTRO (EMPRESA, CENTRO_CONTABLE, CONCEPTO_COSTE, FECHA, IMPORTE)
                VALUES (1, ?, 'Redistribución Centrales', '2025-10-01', ?)
            """, (centro, round(gasto_asignado, 2)))
        
        # 4. Poner a cero gastos centrales originales
        cursor.execute("""
            UPDATE GASTOS_CENTRO SET IMPORTE = 0 
            WHERE FECHA = '2025-10-01' AND CENTRO_CONTABLE BETWEEN 6 AND 8
        """)
        
        cursor.execute("""
            UPDATE MOVIMIENTOS_CONTRATOS SET IMPORTE = 0 
            WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL 
              AND CENTRO_CONTABLE BETWEEN 6 AND 8
        """)
        
        conn.commit()
        
        # 5. Verificación final
        cursor.execute("SELECT SUM(IMPORTE) FROM GASTOS_CENTRO WHERE FECHA = '2025-10-01'")
        total_final_centro = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT SUM(ABS(IMPORTE)) FROM MOVIMIENTOS_CONTRATOS 
            WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL AND IMPORTE < 0
        """)
        total_final_mov = cursor.fetchone()[0] or 0
        
        total_final = total_final_centro + total_final_mov
        
        print(f"\n✅ REDISTRIBUCIÓN COMPLETADA:")
        print(f"   • Gastos redistribuidos: €{total_gastos_centrales:,.2f}")
        print(f"   • Total gastos octubre: €{total_final:,.2f}")
        print(f"   • Todos los gastos están en centros 1-5")
        
        return total_final

if __name__ == "__main__":
    try:
        total = redistribuir_gastos_centrales()
        print(f"\n🚀 SIGUIENTE PASO:")
        print(f"   Ejecutar: python mejora_gastos_octubre.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
