#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de PRECIO_POR_PRODUCTO_REAL basado en GASTOS_CENTRO
Ubicación: backend/scripts/genera_precios_reales.py
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def generar_precios_reales(fecha_calculo='2025-10-01'):
    """Genera precios reales basados en GASTOS_CENTRO"""
    
    print(f"🏦 GENERANDO PRECIOS REALES PARA {fecha_calculo}")
    print("=" * 60)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Obtener gastos por centro desde GASTOS_CENTRO
        cursor.execute("""
            SELECT CENTRO_CONTABLE, SUM(IMPORTE) as GASTOS_TOTALES
            FROM GASTOS_CENTRO 
            WHERE FECHA = ?
            GROUP BY CENTRO_CONTABLE
        """, (fecha_calculo,))
        
        gastos_centro = dict(cursor.fetchall())
        
        print("💰 Gastos por centro (GASTOS_CENTRO):")
        total_gastos = sum(gastos_centro.values())
        for centro, gastos in sorted(gastos_centro.items()):
            print(f"   Centro {centro}: €{gastos:,.2f}")
        print(f"   TOTAL: €{total_gastos:,.2f}")
        
        # 2. Obtener distribución de contratos por segmento-producto
        cursor.execute("""
            SELECT 
                c.CENTRO_CONTABLE,
                g.SEGMENTO_ID,
                c.PRODUCTO_ID,
                COUNT(DISTINCT c.CONTRATO_ID) as NUM_CONTRATOS
            FROM MAESTRO_CONTRATOS c
            JOIN MAESTRO_GESTORES g ON c.GESTOR_ID = g.GESTOR_ID
            WHERE c.CENTRO_CONTABLE BETWEEN 1 AND 5
            GROUP BY c.CENTRO_CONTABLE, g.SEGMENTO_ID, c.PRODUCTO_ID
        """)
        
        distribuciones = cursor.fetchall()
        
        # 3. Calcular total de contratos por centro
        cursor.execute("""
            SELECT c.CENTRO_CONTABLE, COUNT(DISTINCT c.CONTRATO_ID) as TOTAL
            FROM MAESTRO_CONTRATOS c
            WHERE c.CENTRO_CONTABLE BETWEEN 1 AND 5
            GROUP BY c.CENTRO_CONTABLE
        """)
        
        contratos_por_centro = dict(cursor.fetchall())
        
        print("\n📊 Distribución de contratos:")
        for centro, total in sorted(contratos_por_centro.items()):
            gastos = gastos_centro.get(centro, 0)
            coste_unitario = gastos / total if total > 0 else 0
            print(f"   Centro {centro}: {total} contratos | €{coste_unitario:.2f}/contrato")
        
        # 4. Calcular precios por segmento-producto
        precios_reales = {}
        
        for centro, segmento, producto, num_contratos in distribuciones:
            if centro in gastos_centro and centro in contratos_por_centro:
                # Gasto unitario del centro
                gasto_unitario = gastos_centro[centro] / contratos_por_centro[centro]
                gasto_asignado = gasto_unitario * num_contratos
                
                # Acumular por segmento-producto
                key = (segmento, producto)
                if key not in precios_reales:
                    precios_reales[key] = {'gastos': 0.0, 'contratos': 0}
                
                precios_reales[key]['gastos'] += gasto_asignado
                precios_reales[key]['contratos'] += num_contratos
        
        # 5. Limpiar tabla e insertar precios calculados
        cursor.execute("DELETE FROM PRECIO_POR_PRODUCTO_REAL WHERE FECHA_CALCULO = ?", 
                      (fecha_calculo,))
        
        print(f"\n💾 Insertando precios calculados:")
        registros = 0
        
        for (segmento_id, producto_id), datos in precios_reales.items():
            precio_real = -(datos['gastos'] / datos['contratos'])  # Negativo = coste
            coste_unitario = datos['gastos'] / datos['contratos']
            
            cursor.execute("""
                INSERT INTO PRECIO_POR_PRODUCTO_REAL 
                (SEGMENTO_ID, PRODUCTO_ID, PRECIO_MANTENIMIENTO_REAL, FECHA_CALCULO, 
                 NUM_CONTRATOS_BASE, GASTOS_TOTALES_ASIGNADOS, COSTE_UNITARIO_CALCULADO)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                segmento_id, producto_id, round(precio_real, 2), fecha_calculo,
                datos['contratos'], round(datos['gastos'], 2), round(coste_unitario, 2)
            ))
            
            # Obtener nombres para mostrar
            cursor.execute("""
                SELECT s.DESC_SEGMENTO, p.DESC_PRODUCTO
                FROM MAESTRO_SEGMENTOS s, MAESTRO_PRODUCTOS p
                WHERE s.SEGMENTO_ID = ? AND p.PRODUCTO_ID = ?
            """, (segmento_id, producto_id))
            
            desc_seg, desc_prod = cursor.fetchone()
            
            print(f"   ✅ {desc_seg} | {desc_prod}: €{precio_real:.2f}")
            print(f"      ({datos['contratos']} contratos, €{datos['gastos']:,.2f} gastos)")
            
            registros += 1
        
        conn.commit()
        
        print(f"\n✅ {registros} precios reales insertados")
        
        # 6. Mostrar comparación con STD
        print("\n📊 COMPARACIÓN STD vs REAL:")
        print("-" * 80)
        
        cursor.execute("""
            SELECT 
                s.DESC_SEGMENTO,
                p.DESC_PRODUCTO,
                ppr.PRECIO_MANTENIMIENTO_REAL,
                pps.PRECIO_MANTENIMIENTO as PRECIO_STD,
                CASE 
                    WHEN pps.PRECIO_MANTENIMIENTO IS NOT NULL 
                    THEN ppr.PRECIO_MANTENIMIENTO_REAL - pps.PRECIO_MANTENIMIENTO 
                    ELSE NULL 
                END as DESVIACION
            FROM PRECIO_POR_PRODUCTO_REAL ppr
            LEFT JOIN PRECIO_POR_PRODUCTO_STD pps ON ppr.SEGMENTO_ID = pps.SEGMENTO_ID 
                                                  AND ppr.PRODUCTO_ID = pps.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS s ON ppr.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS p ON ppr.PRODUCTO_ID = p.PRODUCTO_ID
            WHERE ppr.FECHA_CALCULO = ?
        """, (fecha_calculo,))
        
        for row in cursor.fetchall():
            segmento, producto, real, std, desv = row
            if std is not None:
                status = "🟢 EFICIENTE" if real > std else "🔴 INEFICIENTE"
                print(f"{segmento:<20} | {producto[:25]:<25}")
                print(f"   Real: €{real:>7.2f} | Std: €{std:>7.2f} | Desv: €{desv:>+7.2f} | {status}")
            else:
                print(f"{segmento:<20} | {producto[:25]:<25}")
                print(f"   Real: €{real:>7.2f} | Std: NO DEFINIDO")
            print("-" * 80)

if __name__ == "__main__":
    generar_precios_reales()
