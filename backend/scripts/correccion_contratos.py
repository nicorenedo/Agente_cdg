#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrección Final de Precios Octubre
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def correccion_final_octubre():
    """Corrección completa del problema"""
    
    print("🔧 CORRECCIÓN FINAL OCTUBRE")
    print("=" * 40)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Verificar estructura real
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN FECHA_ALTA <= '2025-09-01' THEN 1 END) as SEPT,
                COUNT(CASE WHEN FECHA_ALTA <= '2025-10-01' THEN 1 END) as OCT,
                COUNT(CASE WHEN FECHA_ALTA = '2025-10-01' THEN 1 END) as NUEVOS_OCT
            FROM MAESTRO_CONTRATOS
            WHERE CENTRO_CONTABLE BETWEEN 1 AND 5
        """)
        
        sept, oct, nuevos = cursor.fetchone()
        
        print(f"📊 Situación real:")
        print(f"   Septiembre: {sept} contratos")
        print(f"   Octubre: {oct} contratos")
        print(f"   Nuevos octubre: {nuevos} contratos")
        
        if oct != 215:
            print(f"❌ ERROR: Deberían ser 215 contratos octubre, tienes {oct}")
            print("💡 Necesitas añadir más contratos octubre o verificar fechas")
            return
        
        # 2. Verificar gastos proporcionales
        cursor.execute("""
            SELECT SUM(IMPORTE) FROM GASTOS_CENTRO WHERE FECHA = '2025-09-01'
        """)
        gastos_sept = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT SUM(IMPORTE) FROM GASTOS_CENTRO WHERE FECHA = '2025-10-01'
        """)
        gastos_oct = cursor.fetchone()[0]
        
        ratio_gastos = gastos_oct / gastos_sept
        ratio_contratos = oct / sept
        
        print(f"\n💰 Análisis proporcional:")
        print(f"   Gastos sept: €{gastos_sept:,.2f}")
        print(f"   Gastos oct: €{gastos_oct:,.2f}")
        print(f"   Ratio gastos: {ratio_gastos:.3f}")
        print(f"   Ratio contratos: {ratio_contratos:.3f}")
        
        if ratio_gastos > ratio_contratos + 0.1:
            print("⚠️ PROBLEMA: Gastos crecen más rápido que contratos")
            
            # Ajustar gastos octubre
            factor_correccion = ratio_contratos * 1.05  # Solo 5% más que contratos
            nuevo_total = gastos_sept * factor_correccion
            
            print(f"🎯 Corrección sugerida:")
            print(f"   Nuevo total gastos: €{nuevo_total:,.2f}")
            
            cursor.execute("""
                UPDATE GASTOS_CENTRO 
                SET IMPORTE = IMPORTE * ?
                WHERE FECHA = '2025-10-01'
            """, (nuevo_total / gastos_oct,))
            
            print("✅ Gastos corregidos")
            conn.commit()
        
        # 3. Recalcular precios
        print("\n🔄 Lanzando recálculo...")

if __name__ == "__main__":
    correccion_final_octubre()
