#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrección Final - Asignar Contratos Octubre a Centros Finalistas
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def corregir_centros_octubre():
    """Asegura que todos los contratos octubre estén en centros 1-5"""
    
    print("🔧 CORRECCIÓN CONTRATOS OCTUBRE - CENTROS FINALISTAS")
    print("=" * 60)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Verificar contratos octubre por centro
        cursor.execute("""
            SELECT CENTRO_CONTABLE, COUNT(*) as CONTRATOS
            FROM MAESTRO_CONTRATOS 
            WHERE FECHA_ALTA LIKE '2025-10%'
            GROUP BY CENTRO_CONTABLE
            ORDER BY CENTRO_CONTABLE
        """)
        
        print("📊 Contratos octubre por centro:")
        total_octubre = 0
        contratos_fuera = 0
        
        for centro, contratos in cursor.fetchall():
            total_octubre += contratos
            if centro > 5:
                contratos_fuera += contratos
                print(f"   Centro {centro}: {contratos} contratos ❌ (fuera de finalistas)")
            else:
                print(f"   Centro {centro}: {contratos} contratos ✅")
        
        print(f"   TOTAL OCTUBRE: {total_octubre}")
        print(f"   FUERA DE FINALISTAS: {contratos_fuera}")
        
        if contratos_fuera > 0:
            print(f"\n🔄 Moviendo {contratos_fuera} contratos a centros finalistas...")
            
            # Mover contratos de centros 6-8 a centros 1-5
            cursor.execute("""
                UPDATE MAESTRO_CONTRATOS 
                SET CENTRO_CONTABLE = CASE 
                    WHEN CENTRO_CONTABLE = 6 THEN 1
                    WHEN CENTRO_CONTABLE = 7 THEN 2
                    WHEN CENTRO_CONTABLE = 8 THEN 3
                    ELSE CENTRO_CONTABLE
                END
                WHERE FECHA_ALTA LIKE '2025-10%'
                  AND CENTRO_CONTABLE > 5
            """)
            
            conn.commit()
            print("✅ Contratos movidos a centros finalistas")
        
        # 2. Verificar total final
        cursor.execute("""
            SELECT COUNT(*) FROM MAESTRO_CONTRATOS 
            WHERE FECHA_ALTA <= '2025-10-31'
              AND CENTRO_CONTABLE BETWEEN 1 AND 5
        """)
        
        total_final = cursor.fetchone()[0]
        print(f"\n📈 TOTAL FINAL CENTROS FINALISTAS: {total_final}")
        
        if total_final == 215:
            print("🎉 ¡PERFECTO! Ahora tienes 215 contratos en centros finalistas")
            return True
        else:
            print(f"⚠️ Esperaba 215, tienes {total_final}")
            
            # Verificar distribución detallada
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN FECHA_ALTA LIKE '2025-01%' OR FECHA_ALTA LIKE '2025-02%' OR 
                             FECHA_ALTA LIKE '2025-03%' OR FECHA_ALTA LIKE '2025-04%' OR 
                             FECHA_ALTA LIKE '2025-05%' THEN 'SEPTIEMBRE_BASE'
                        WHEN FECHA_ALTA LIKE '2025-10%' THEN 'OCTUBRE_NUEVOS'
                        ELSE 'OTROS'
                    END as PERIODO,
                    COUNT(*) as CONTRATOS
                FROM MAESTRO_CONTRATOS
                WHERE CENTRO_CONTABLE BETWEEN 1 AND 5
                GROUP BY 
                    CASE 
                        WHEN FECHA_ALTA LIKE '2025-01%' OR FECHA_ALTA LIKE '2025-02%' OR 
                             FECHA_ALTA LIKE '2025-03%' OR FECHA_ALTA LIKE '2025-04%' OR 
                             FECHA_ALTA LIKE '2025-05%' THEN 'SEPTIEMBRE_BASE'
                        WHEN FECHA_ALTA LIKE '2025-10%' THEN 'OCTUBRE_NUEVOS'
                        ELSE 'OTROS'
                    END
            """)
            
            print("\n📋 Distribución detallada:")
            for periodo, contratos in cursor.fetchall():
                print(f"   {periodo}: {contratos} contratos")
            
            return False

if __name__ == "__main__":
    if corregir_centros_octubre():
        print("\n🚀 PRÓXIMO PASO:")
        print("python scripts/calcular_precios_octubre.py")
        print("Ahora debería mostrar 215 contratos y precios correctos")
