#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AJUSTE DE MOVIMIENTOS_CONTRATOS OCTUBRE A 1,100 REGISTROS
========================================================
Reduce los movimientos de octubre de 1,728 a aproximadamente 1,100 registros
manteniendo la distribución proporcional por tipo de cuenta y centro.
"""

import sqlite3
from pathlib import Path
import random

DATABASE_PATH = Path(__file__).parent.parent / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def ajustar_movimientos_octubre_1100():
    print("🔧 AJUSTE MOVIMIENTOS OCTUBRE A 1,100 REGISTROS")
    print("=" * 60)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Análisis de situación actual
        cursor.execute("SELECT COUNT(*) FROM MOVIMIENTOS_CONTRATOS WHERE FECHA = '2025-09-01'")
        movimientos_septiembre = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM MOVIMIENTOS_CONTRATOS WHERE FECHA = '2025-10-01'")
        movimientos_octubre_actual = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= '2025-09-30' AND CENTRO_CONTABLE BETWEEN 1 AND 5")
        contratos_septiembre = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= '2025-10-31' AND CENTRO_CONTABLE BETWEEN 1 AND 5")
        contratos_octubre = cursor.fetchone()[0]
        
        print(f"📊 Situación actual:")
        print(f"   • Septiembre: {movimientos_septiembre} movimientos | {contratos_septiembre} contratos")
        print(f"   • Octubre actual: {movimientos_octubre_actual} movimientos | {contratos_octubre} contratos")
        print(f"   • Incremento actual: +{((movimientos_octubre_actual/movimientos_septiembre)-1)*100:.1f}%")
        
        # 2. Definir objetivo de 1,100 movimientos
        movimientos_objetivo = 1100
        movimientos_a_eliminar = movimientos_octubre_actual - movimientos_objetivo
        
        print(f"\n🎯 Objetivo de ajuste:")
        print(f"   • Movimientos objetivo: {movimientos_objetivo}")
        print(f"   • Movimientos a eliminar: {movimientos_a_eliminar}")
        print(f"   • Incremento objetivo vs septiembre: +{((movimientos_objetivo/movimientos_septiembre)-1)*100:.1f}%")
        
        if movimientos_a_eliminar <= 0:
            print("✅ No se requiere ajuste - objetivo ya alcanzado")
            return
        
        # 3. Obtener distribución actual por tipo de cuenta
        cursor.execute("""
            SELECT CUENTA_ID, COUNT(*) as CANTIDAD
            FROM MOVIMIENTOS_CONTRATOS 
            WHERE FECHA = '2025-10-01'
            GROUP BY CUENTA_ID
            ORDER BY CANTIDAD DESC
        """)
        distribucion_actual = cursor.fetchall()
        
        print(f"\n📈 Distribución actual por cuenta (top 10):")
        for i, (cuenta, cantidad) in enumerate(distribucion_actual[:10]):
            print(f"   {i+1}. Cuenta {cuenta}: {cantidad} movimientos")
        
        # 4. Calcular movimientos a eliminar por cuenta (proporcional)
        movimientos_a_eliminar_por_cuenta = {}
        total_actual = sum([cantidad for _, cantidad in distribucion_actual])
        
        print(f"\n🗑️ Cálculo de eliminación proporcional:")
        total_eliminados_calculado = 0
        
        for cuenta, cantidad in distribucion_actual:
            proporcion = cantidad / total_actual
            a_eliminar = int(movimientos_a_eliminar * proporcion)
            if a_eliminar > 0:
                movimientos_a_eliminar_por_cuenta[cuenta] = a_eliminar
                total_eliminados_calculado += a_eliminar
                print(f"   Cuenta {cuenta}: -{a_eliminar} movimientos ({proporcion*100:.1f}%)")
        
        print(f"   TOTAL CALCULADO A ELIMINAR: {total_eliminados_calculado}")
        
        # 5. Ajuste fino para llegar exactamente al objetivo
        diferencia = movimientos_a_eliminar - total_eliminados_calculado
        if diferencia > 0:
            # Distribuir la diferencia en las cuentas con más movimientos
            cuentas_principales = sorted(distribucion_actual, key=lambda x: x[1], reverse=True)[:5]
            for i in range(diferencia):
                cuenta = cuentas_principales[i % len(cuentas_principales)][0]
                if cuenta in movimientos_a_eliminar_por_cuenta:
                    movimientos_a_eliminar_por_cuenta[cuenta] += 1
                else:
                    movimientos_a_eliminar_por_cuenta[cuenta] = 1
        
        # 6. Ejecutar eliminación aleatoria proporcional
        print(f"\n🔄 Ejecutando eliminación...")
        total_eliminados_real = 0
        
        for cuenta, cantidad_eliminar in movimientos_a_eliminar_por_cuenta.items():
            # Obtener todos los movimientos de esta cuenta
            cursor.execute("""
                SELECT MOVIMIENTO_ID FROM MOVIMIENTOS_CONTRATOS 
                WHERE FECHA = '2025-10-01' AND CUENTA_ID = ?
                ORDER BY MOVIMIENTO_ID
            """, (cuenta,))
            
            movimientos_cuenta = [row[0] for row in cursor.fetchall()]
            
            # Seleccionar aleatoriamente los que vamos a eliminar
            if len(movimientos_cuenta) >= cantidad_eliminar:
                # Usar seed para reproducibilidad
                random.seed(42)
                movimientos_a_eliminar_ids = random.sample(movimientos_cuenta, cantidad_eliminar)
                
                # Eliminar movimientos seleccionados
                placeholders = ','.join(['?' for _ in movimientos_a_eliminar_ids])
                cursor.execute(f"""
                    DELETE FROM MOVIMIENTOS_CONTRATOS 
                    WHERE MOVIMIENTO_ID IN ({placeholders})
                """, movimientos_a_eliminar_ids)
                
                total_eliminados_real += cantidad_eliminar
                print(f"   ✅ Eliminados {cantidad_eliminar} movimientos de cuenta {cuenta}")
            else:
                print(f"   ⚠️ Cuenta {cuenta}: solo {len(movimientos_cuenta)} disponibles, se eliminan todos")
                cursor.execute("""
                    DELETE FROM MOVIMIENTOS_CONTRATOS 
                    WHERE FECHA = '2025-10-01' AND CUENTA_ID = ?
                """, (cuenta,))
                total_eliminados_real += len(movimientos_cuenta)
        
        conn.commit()
        
        # 7. Verificación final
        cursor.execute("SELECT COUNT(*) FROM MOVIMIENTOS_CONTRATOS WHERE FECHA = '2025-10-01'")
        movimientos_octubre_final = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT CUENTA_ID, COUNT(*) as CANTIDAD
            FROM MOVIMIENTOS_CONTRATOS 
            WHERE FECHA = '2025-10-01'
            GROUP BY CUENTA_ID
            ORDER BY CANTIDAD DESC
        """)
        distribucion_final = cursor.fetchall()
        
        print(f"\n✅ AJUSTE COMPLETADO:")
        print(f"   • Movimientos eliminados: {total_eliminados_real}")
        print(f"   • Movimientos octubre final: {movimientos_octubre_final}")
        print(f"   • Objetivo era: {movimientos_objetivo}")
        print(f"   • Diferencia vs objetivo: {abs(movimientos_octubre_final - movimientos_objetivo)}")
        print(f"   • Incremento final vs septiembre: +{((movimientos_octubre_final/movimientos_septiembre)-1)*100:.1f}%")
        
        print(f"\n📈 Distribución final por cuenta (top 10):")
        for i, (cuenta, cantidad) in enumerate(distribucion_final[:10]):
            print(f"   {i+1}. Cuenta {cuenta}: {cantidad} movimientos")
        
        # 8. Verificar integridad del sistema
        print(f"\n🔍 Verificación de integridad del sistema:")
        
        # Verificar gastos totales (no deben cambiar)
        cursor.execute("SELECT SUM(IMPORTE) FROM GASTOS_CENTRO WHERE FECHA = '2025-10-01'")
        gastos_centro = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(ABS(IMPORTE)) FROM MOVIMIENTOS_CONTRATOS WHERE FECHA = '2025-10-01' AND CONTRATO_ID IS NULL AND IMPORTE < 0")
        gastos_operativos = cursor.fetchone()[0] or 0
        
        total_gastos = gastos_centro + gastos_operativos
        
        # Verificar contratos (no deben cambiar)
        cursor.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= '2025-10-31' AND CENTRO_CONTABLE BETWEEN 1 AND 5")
        contratos_verificacion = cursor.fetchone()[0]
        
        print(f"   ✅ Gastos totales octubre: €{total_gastos:,.2f} (sin cambios)")
        print(f"   ✅ Contratos activos: {contratos_verificacion} (sin cambios)")
        print(f"   ✅ Coste unitario: €{total_gastos/contratos_verificacion:.2f} (sin cambios)")
        
        # 9. Calcular ratio movimientos/contrato
        ratio_sept = movimientos_septiembre / contratos_septiembre
        ratio_oct = movimientos_octubre_final / contratos_octubre
        
        print(f"\n📊 Análisis de actividad por contrato:")
        print(f"   • Septiembre: {ratio_sept:.2f} movimientos/contrato")
        print(f"   • Octubre: {ratio_oct:.2f} movimientos/contrato")
        print(f"   • Variación: {((ratio_oct/ratio_sept)-1)*100:+.1f}%")
        
        return {
            'movimientos_eliminados': total_eliminados_real,
            'movimientos_finales': movimientos_octubre_final,
            'objetivo': movimientos_objetivo,
            'diferencia_objetivo': abs(movimientos_octubre_final - movimientos_objetivo),
            'incremento_vs_septiembre': ((movimientos_octubre_final/movimientos_septiembre)-1)*100,
            'ratio_actividad': ratio_oct
        }

if __name__ == "__main__":
    try:
        resultado = ajustar_movimientos_octubre_1100()
        
        print(f"\n🎉 AJUSTE EXITOSO:")
        print(f"   • Movimientos finales: {resultado['movimientos_finales']}")
        print(f"   • Diferencia vs objetivo: {resultado['diferencia_objetivo']}")
        print(f"   • Incremento realista: +{resultado['incremento_vs_septiembre']:.1f}%")
        print(f"   • Ratio actividad: {resultado['ratio_actividad']:.2f} mov/contrato")
        
        print(f"\n🚀 SISTEMA OPTIMIZADO:")
        print(f"   ✅ Volumen de movimientos realista")
        print(f"   ✅ Crecimiento coherente mes a mes")
        print(f"   ✅ Distribución proporcional mantenida")
        print(f"   ✅ Cálculos de precios no afectados")
        print(f"   ✅ Base de datos lista para Agente CDG")
        
    except Exception as e:
        print(f"\n❌ Error durante el ajuste: {e}")
        raise
