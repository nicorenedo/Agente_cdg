#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico del Problema de Contratos Octubre
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def diagnosticar_contratos():
    """Diagnostica por qué no se cuentan los 215 contratos"""
    
    print("🔍 DIAGNÓSTICO DE CONTRATOS OCTUBRE")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Contar contratos por mes de alta
        cursor.execute("""
            SELECT 
                DATE(FECHA_ALTA) as MES,
                COUNT(*) as CONTRATOS
            FROM MAESTRO_CONTRATOS
            GROUP BY DATE(FECHA_ALTA)
            ORDER BY FECHA_ALTA
        """)
        
        print("📊 Contratos por fecha de alta:")
        for mes, contratos in cursor.fetchall():
            print(f"   {mes}: {contratos} contratos")
        
        # 2. Total contratos hasta octubre
        cursor.execute("""
            SELECT COUNT(*) FROM MAESTRO_CONTRATOS 
            WHERE FECHA_ALTA <= '2025-10-01'
        """)
        total_octubre = cursor.fetchone()[0]
        
        # 3. Solo contratos septiembre
        cursor.execute("""
            SELECT COUNT(*) FROM MAESTRO_CONTRATOS 
            WHERE FECHA_ALTA <= '2025-09-01'
        """)
        total_septiembre = cursor.fetchone()[0]
        
        print(f"\n📈 Totales acumulados:")
        print(f"   Hasta septiembre: {total_septiembre}")
        print(f"   Hasta octubre: {total_octubre}")
        print(f"   Nuevos octubre: {total_octubre - total_septiembre}")
        
        # 4. Contratos en centros finalistas (1-5)
        cursor.execute("""
            SELECT CENTRO_CONTABLE, COUNT(*) as CONTRATOS
            FROM MAESTRO_CONTRATOS 
            WHERE FECHA_ALTA <= '2025-10-01'
              AND CENTRO_CONTABLE BETWEEN 1 AND 5
            GROUP BY CENTRO_CONTABLE
            ORDER BY CENTRO_CONTABLE
        """)
        
        print(f"\n🏢 Contratos en centros finalistas (hasta octubre):")
        total_finalistas = 0
        for centro, contratos in cursor.fetchall():
            total_finalistas += contratos
            print(f"   Centro {centro}: {contratos} contratos")
        
        print(f"   TOTAL FINALISTAS: {total_finalistas}")
        
        # 5. Verificar si hay contratos en centros 6-8
        cursor.execute("""
            SELECT CENTRO_CONTABLE, COUNT(*) as CONTRATOS
            FROM MAESTRO_CONTRATOS 
            WHERE FECHA_ALTA <= '2025-10-01'
              AND CENTRO_CONTABLE > 5
            GROUP BY CENTRO_CONTABLE
            ORDER BY CENTRO_CONTABLE
        """)
        
        otros_centros = cursor.fetchall()
        if otros_centros:
            print(f"\n⚠️ Contratos en centros de servicios:")
            for centro, contratos in otros_centros:
                print(f"   Centro {centro}: {contratos} contratos")

if __name__ == "__main__":
    diagnosticar_contratos()
