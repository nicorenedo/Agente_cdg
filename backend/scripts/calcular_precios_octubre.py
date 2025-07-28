#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CÁLCULO DEFINITIVO PRECIOS REALES OCTUBRE 2025
=============================================
Calcula precios reales con gastos centrales ya redistribuidos
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def calcular_precios_reales_octubre_definitivo():
    print("🏦 CÁLCULO DEFINITIVO PRECIOS REALES OCTUBRE")
    print("=" * 60)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Verificación de datos base
        cursor.execute("SELECT COUNT(*) FROM MOVIMIENTOS_CONTRATOS WHERE FECHA = '2025-10-01'")
        movimientos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*), SUM(IMPORTE) FROM GASTOS_CENTRO WHERE FECHA = '2025-10-01'")
        registros_gastos, total_gastos_centro = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(DISTINCT CONTRATO_ID) FROM MAESTRO_CONTRATOS 
            WHERE FECHA_ALTA <= '2025-10-31' AND CENTRO_CONTABLE BETWEEN 1 AND 5
        """)
        total_contratos = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT SUM(ABS(IMPORTE)) FROM MOVIMIENTOS_CONTRATOS 
            WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL AND IMPORTE < 0
        """)
        gastos_operativos = cursor.fetchone()[0] or 0
        
        total_gastos_global = total_gastos_centro + gastos_operativos
        coste_unitario_medio = total_gastos_global / total_contratos
        
        print(f"📊 Verificación datos octubre:")
        print(f"   • Movimientos: {movimientos}")
        print(f"   • Gastos centro: €{total_gastos_centro:,.2f}")
        print(f"   • Gastos operativos: €{gastos_operativos:,.2f}")
        print(f"   • TOTAL GASTOS: €{total_gastos_global:,.2f}")
        print(f"   • Contratos: {total_contratos}")
        print(f"   • Coste unitario medio: €{coste_unitario_medio:.2f}")
        
        # 2. Gastos y contratos por centro (solo 1-5)
        cursor.execute("""
            SELECT CENTRO_CONTABLE, SUM(IMPORTE) FROM GASTOS_CENTRO 
            WHERE FECHA = '2025-10-01' AND CENTRO_CONTABLE BETWEEN 1 AND 5
            GROUP BY CENTRO_CONTABLE
        """)
        gastos_por_centro = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT CENTRO_CONTABLE, SUM(ABS(IMPORTE)) FROM MOVIMIENTOS_CONTRATOS 
            WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL AND IMPORTE < 0
              AND CENTRO_CONTABLE BETWEEN 1 AND 5
            GROUP BY CENTRO_CONTABLE
        """)
        gastos_operativos_centro = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT CENTRO_CONTABLE, COUNT(DISTINCT CONTRATO_ID) FROM MAESTRO_CONTRATOS 
            WHERE CENTRO_CONTABLE BETWEEN 1 AND 5 AND FECHA_ALTA <= '2025-10-31'
            GROUP BY CENTRO_CONTABLE
        """)
        contratos_por_centro = dict(cursor.fetchall())
        
        # Combinar gastos por centro
        gastos_totales_centro = {}
        gastos_verificacion = 0
        
        for centro in range(1, 6):
            if centro in contratos_por_centro:
                gasto_centro = gastos_por_centro.get(centro, 0)
                gasto_operativo = gastos_operativos_centro.get(centro, 0)
                total_centro = gasto_centro + gasto_operativo
                gastos_totales_centro[centro] = total_centro
                gastos_verificacion += total_centro
        
        print(f"\n🏢 Distribución por centro (incluye centrales redistribuidos):")
        for centro in sorted(gastos_totales_centro.keys()):
            contratos = contratos_por_centro.get(centro, 0)
            gastos = gastos_totales_centro[centro]
            unitario = gastos / contratos if contratos > 0 else 0
            print(f"   Centro {centro}: {contratos} contratos | €{gastos:,.2f} | €{unitario:.2f}/contrato")
        
        print(f"   TOTAL GASTOS ASIGNADOS: €{gastos_verificacion:,.2f}")
        
        # Verificar que coincide con el gasto global
        diferencia = abs(gastos_verificacion - total_gastos_global)
        if diferencia > 1:
            print(f"⚠️ ADVERTENCIA: Diferencia de €{diferencia:.2f}")
        else:
            print(f"✅ Cuadre perfecto: diferencia €{diferencia:.2f}")
        
        # 3. Distribución por segmento-producto
        cursor.execute("""
            SELECT 
                g.SEGMENTO_ID, c.PRODUCTO_ID, s.DESC_SEGMENTO, p.DESC_PRODUCTO,
                COUNT(DISTINCT c.CONTRATO_ID) as NUM_CONTRATOS,
                SUM(CASE WHEN c.CENTRO_CONTABLE = 1 THEN 1 ELSE 0 END) as C1,
                SUM(CASE WHEN c.CENTRO_CONTABLE = 2 THEN 1 ELSE 0 END) as C2,
                SUM(CASE WHEN c.CENTRO_CONTABLE = 3 THEN 1 ELSE 0 END) as C3,
                SUM(CASE WHEN c.CENTRO_CONTABLE = 4 THEN 1 ELSE 0 END) as C4,
                SUM(CASE WHEN c.CENTRO_CONTABLE = 5 THEN 1 ELSE 0 END) as C5
            FROM MAESTRO_CONTRATOS c
            JOIN MAESTRO_GESTORES g ON c.GESTOR_ID = g.GESTOR_ID
            JOIN MAESTRO_SEGMENTOS s ON g.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS p ON c.PRODUCTO_ID = p.PRODUCTO_ID
            WHERE c.CENTRO_CONTABLE BETWEEN 1 AND 5 AND c.FECHA_ALTA <= '2025-10-31'
            GROUP BY g.SEGMENTO_ID, c.PRODUCTO_ID, s.DESC_SEGMENTO, p.DESC_PRODUCTO
            ORDER BY g.SEGMENTO_ID, c.PRODUCTO_ID
        """)
        
        distribuciones = cursor.fetchall()
        
        print(f"\n📈 Calculando precios por segmento-producto...")
        
        # 4. Cálculo de precios reales
        precios_reales = {}
        gastos_distribuidos_total = 0
        contratos_procesados_total = 0
        
        for row in distribuciones:
            segmento_id, producto_id, desc_seg, desc_prod, num_contratos, c1, c2, c3, c4, c5 = row
            
            gasto_total_producto = 0
            for centro, contratos_centro in [(1, c1), (2, c2), (3, c3), (4, c4), (5, c5)]:
                if contratos_centro > 0 and centro in gastos_totales_centro and centro in contratos_por_centro:
                    gasto_centro_total = gastos_totales_centro[centro]
                    total_contratos_centro = contratos_por_centro[centro]
                    gasto_unitario = gasto_centro_total / total_contratos_centro
                    gasto_asignado = gasto_unitario * contratos_centro
                    gasto_total_producto += gasto_asignado
            
            precios_reales[(segmento_id, producto_id, desc_seg, desc_prod)] = {
                'gastos_totales': gasto_total_producto,
                'contratos_totales': num_contratos
            }
            
            gastos_distribuidos_total += gasto_total_producto
            contratos_procesados_total += num_contratos
        
        # 5. Insertar en base de datos
        print(f"\n💾 Insertando precios reales octubre...")
        
        cursor.execute("DELETE FROM PRECIO_POR_PRODUCTO_REAL WHERE FECHA_CALCULO = '2025-10-01'")
        
        registros_insertados = 0
        for (segmento_id, producto_id, desc_seg, desc_prod), datos in precios_reales.items():
            if datos['contratos_totales'] > 0:
                precio_real = -(datos['gastos_totales'] / datos['contratos_totales'])
                coste_unitario = datos['gastos_totales'] / datos['contratos_totales']
                
                cursor.execute("""
                    INSERT INTO PRECIO_POR_PRODUCTO_REAL 
                    (SEGMENTO_ID, PRODUCTO_ID, PRECIO_MANTENIMIENTO_REAL, FECHA_CALCULO, 
                     NUM_CONTRATOS_BASE, GASTOS_TOTALES_ASIGNADOS, COSTE_UNITARIO_CALCULADO)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (segmento_id, producto_id, round(precio_real, 2), '2025-10-01',
                      datos['contratos_totales'], round(datos['gastos_totales'], 2),
                      round(coste_unitario, 2)))
                
                registros_insertados += 1
                print(f"   ✅ {segmento_id} ({desc_seg}) | {desc_prod}")
                print(f"      Precio: €{precio_real:.2f} | Contratos: {datos['contratos_totales']} | Gastos: €{datos['gastos_totales']:,.2f}")
        
        conn.commit()
        
        print(f"\n✅ PROCESO COMPLETADO:")
        print(f"   • {registros_insertados} precios octubre calculados")
        print(f"   • €{gastos_distribuidos_total:,.2f} gastos distribuidos")
        print(f"   • {contratos_procesados_total} contratos procesados")
        print(f"   • Incluye gastos centrales redistribuidos")
        
        # Verificación final de cuadre
        diferencia_final = abs(gastos_distribuidos_total - total_gastos_global)
        if diferencia_final < 1:
            print(f"   ✅ Cuadre perfecto: diferencia €{diferencia_final:.2f}")
        else:
            print(f"   ⚠️ Diferencia de cuadre: €{diferencia_final:.2f}")
        
        return {
            'registros': registros_insertados,
            'gastos_totales': gastos_distribuidos_total,
            'contratos': contratos_procesados_total
        }

if __name__ == "__main__":
    try:
        resultado = calcular_precios_reales_octubre_definitivo()
        print(f"\n🎉 ¡PRECIOS REALES OCTUBRE CALCULADOS!")
        print(f"🚀 Tu Agente CDG está listo con datos completos")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
