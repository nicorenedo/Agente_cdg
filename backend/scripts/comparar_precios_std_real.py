#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BANCAMARCH_AGENTECDG - Comparador de Precios STD vs REAL
======================================================
Analiza desviaciones entre precios estándar y reales por segmento-producto
Ubicación: backend/scripts/comparar_precios_std_real.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import csv

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "src" / "database" / "BM_CONTABILIDAD_CDG.db"
REPORTS_DIR = PROJECT_ROOT / "reports"

class ComparadorPrecios:
    def __init__(self):
        self.db_path = DATABASE_PATH
        REPORTS_DIR.mkdir(exist_ok=True)
    
    def conectar_db(self):
        return sqlite3.connect(self.db_path)
    
    def obtener_comparacion(self, fecha_calculo='2025-09-01'):
        """Obtiene comparación completa STD vs REAL"""
        
        with self.conectar_db() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                s.DESC_SEGMENTO,
                p.DESC_PRODUCTO,
                pps.PRECIO_MANTENIMIENTO as PRECIO_STD,
                ppr.PRECIO_MANTENIMIENTO_REAL as PRECIO_REAL,
                (ppr.PRECIO_MANTENIMIENTO_REAL - pps.PRECIO_MANTENIMIENTO) as DESVIACION_ABSOLUTA,
                ROUND(
                    ((ppr.PRECIO_MANTENIMIENTO_REAL - pps.PRECIO_MANTENIMIENTO) / ABS(pps.PRECIO_MANTENIMIENTO)) * 100, 
                    2
                ) as DESVIACION_PORCENTUAL,
                CASE 
                    WHEN ppr.PRECIO_MANTENIMIENTO_REAL > pps.PRECIO_MANTENIMIENTO THEN 'EFICIENTE'
                    WHEN ppr.PRECIO_MANTENIMIENTO_REAL < pps.PRECIO_MANTENIMIENTO THEN 'INEFICIENTE'
                    ELSE 'IGUAL'
                END as PERFORMANCE,
                ppr.NUM_CONTRATOS_BASE,
                ppr.GASTOS_TOTALES_ASIGNADOS,
                ppr.COSTE_UNITARIO_CALCULADO,
                s.SEGMENTO_ID,
                p.PRODUCTO_ID
            FROM PRECIO_POR_PRODUCTO_STD pps
            JOIN PRECIO_POR_PRODUCTO_REAL ppr ON pps.SEGMENTO_ID = ppr.SEGMENTO_ID 
                                              AND pps.PRODUCTO_ID = ppr.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS s ON pps.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS p ON pps.PRODUCTO_ID = p.PRODUCTO_ID
            WHERE ppr.FECHA_CALCULO = ?
            ORDER BY ABS(DESVIACION_PORCENTUAL) DESC
            """
            
            cursor.execute(query, (fecha_calculo,))
            return cursor.fetchall()
    
    def generar_reporte_completo(self, fecha_calculo='2025-09-01'):
        """Genera reporte completo de comparación"""
        
        print(f"🏦 COMPARACIÓN PRECIOS STD vs REAL - {fecha_calculo}")
        print("=" * 100)
        
        datos = self.obtener_comparacion(fecha_calculo)
        
        if not datos:
            print("❌ No se encontraron datos para la fecha especificada")
            return
        
        # Análisis por performance
        eficientes = [d for d in datos if d[6] == 'EFICIENTE']
        ineficientes = [d for d in datos if d[6] == 'INEFICIENTE']
        
        print(f"📊 RESUMEN GENERAL:")
        print(f"   • Total combinaciones: {len(datos)}")
        print(f"   • Eficientes: {len(eficientes)} ({len(eficientes)/len(datos)*100:.1f}%)")
        print(f"   • Ineficientes: {len(ineficientes)} ({len(ineficientes)/len(datos)*100:.1f}%)")
        
        # Calcular estadísticas
        desviaciones = [abs(d[5]) for d in datos]  # Desviación porcentual
        
        print(f"\n📈 ESTADÍSTICAS DE DESVIACIÓN:")
        print(f"   • Desviación promedio: {sum(desviaciones)/len(desviaciones):.2f}%")
        print(f"   • Desviación máxima: {max(desviaciones):.2f}%")
        print(f"   • Desviación mínima: {min(desviaciones):.2f}%")
        
        print(f"\n📋 DETALLE POR SEGMENTO-PRODUCTO:")
        print("-" * 100)
        
        for row in datos:
            segmento, producto, std, real, desv_abs, desv_pct, performance, contratos, gastos, coste, seg_id, prod_id = row
            
            status_icon = "🟢" if performance == "EFICIENTE" else "🔴"
            
            print(f"{segmento:<20} | {producto[:30]:<30}")
            print(f"   Std: €{std:>8.2f} | Real: €{real:>8.2f} | Desv: €{desv_abs:>+8.2f} ({desv_pct:>+6.2f}%) | {status_icon} {performance}")
            print(f"   Contratos: {contratos:>3} | Gastos: €{gastos:>10,.2f} | Coste Unit: €{coste:>8.2f}")
            print("-" * 100)
        
        return datos
    
    def analisis_por_segmento(self, fecha_calculo='2025-09-01'):
        """Análisis agregado por segmento"""
        
        print(f"\n📊 ANÁLISIS POR SEGMENTO:")
        print("=" * 80)
        
        with self.conectar_db() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                s.DESC_SEGMENTO,
                COUNT(*) as NUM_PRODUCTOS,
                ROUND(AVG(ABS((ppr.PRECIO_MANTENIMIENTO_REAL - pps.PRECIO_MANTENIMIENTO) / ABS(pps.PRECIO_MANTENIMIENTO)) * 100), 2) as DESVIACION_PROM,
                SUM(CASE WHEN ppr.PRECIO_MANTENIMIENTO_REAL > pps.PRECIO_MANTENIMIENTO THEN 1 ELSE 0 END) as EFICIENTES,
                SUM(CASE WHEN ppr.PRECIO_MANTENIMIENTO_REAL < pps.PRECIO_MANTENIMIENTO THEN 1 ELSE 0 END) as INEFICIENTES,
                SUM(ppr.NUM_CONTRATOS_BASE) as TOTAL_CONTRATOS,
                ROUND(SUM(ppr.GASTOS_TOTALES_ASIGNADOS), 2) as TOTAL_GASTOS
            FROM PRECIO_POR_PRODUCTO_STD pps
            JOIN PRECIO_POR_PRODUCTO_REAL ppr ON pps.SEGMENTO_ID = ppr.SEGMENTO_ID 
                                              AND pps.PRODUCTO_ID = ppr.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS s ON pps.SEGMENTO_ID = s.SEGMENTO_ID
            WHERE ppr.FECHA_CALCULO = ?
            GROUP BY s.SEGMENTO_ID, s.DESC_SEGMENTO
            ORDER BY DESVIACION_PROM DESC
            """
            
            cursor.execute(query, (fecha_calculo,))
            
            for row in cursor.fetchall():
                segmento, productos, desv_prom, eficientes, ineficientes, contratos, gastos = row
                
                eficiencia_pct = (eficientes / productos) * 100 if productos > 0 else 0
                status = "🟢 BUENO" if eficiencia_pct >= 50 else "🔴 MALO"
                
                print(f"{segmento:<20} | {productos} productos | Desv.Prom: {desv_prom:>6.2f}%")
                print(f"   Eficientes: {eficientes}/{productos} ({eficiencia_pct:.1f}%) | Contratos: {contratos:>3} | Gastos: €{gastos:>10,.2f} | {status}")
                print("-" * 80)
    
    def analisis_por_producto(self, fecha_calculo='2025-09-01'):
        """Análisis agregado por producto"""
        
        print(f"\n🏭 ANÁLISIS POR PRODUCTO:")
        print("=" * 80)
        
        with self.conectar_db() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                p.DESC_PRODUCTO,
                COUNT(*) as NUM_SEGMENTOS,
                ROUND(AVG(ABS((ppr.PRECIO_MANTENIMIENTO_REAL - pps.PRECIO_MANTENIMIENTO) / ABS(pps.PRECIO_MANTENIMIENTO)) * 100), 2) as DESVIACION_PROM,
                ROUND(AVG(pps.PRECIO_MANTENIMIENTO), 2) as PRECIO_STD_PROM,
                ROUND(AVG(ppr.PRECIO_MANTENIMIENTO_REAL), 2) as PRECIO_REAL_PROM,
                SUM(ppr.NUM_CONTRATOS_BASE) as TOTAL_CONTRATOS,
                ROUND(SUM(ppr.GASTOS_TOTALES_ASIGNADOS), 2) as TOTAL_GASTOS
            FROM PRECIO_POR_PRODUCTO_STD pps
            JOIN PRECIO_POR_PRODUCTO_REAL ppr ON pps.SEGMENTO_ID = ppr.SEGMENTO_ID 
                                              AND pps.PRODUCTO_ID = ppr.PRODUCTO_ID
            JOIN MAESTRO_PRODUCTOS p ON pps.PRODUCTO_ID = p.PRODUCTO_ID
            WHERE ppr.FECHA_CALCULO = ?
            GROUP BY p.PRODUCTO_ID, p.DESC_PRODUCTO
            ORDER BY DESVIACION_PROM DESC
            """
            
            cursor.execute(query, (fecha_calculo,))
            
            for row in cursor.fetchall():
                producto, segmentos, desv_prom, std_prom, real_prom, contratos, gastos = row
                
                print(f"{producto[:30]:<30} | {segmentos} segmentos | Desv.Prom: {desv_prom:>6.2f}%")
                print(f"   Std.Prom: €{std_prom:>8.2f} | Real.Prom: €{real_prom:>8.2f} | Contratos: {contratos:>3} | Gastos: €{gastos:>10,.2f}")
                print("-" * 80)
    
    def generar_alertas(self, fecha_calculo='2025-09-01', umbral_desviacion=15.0):
        """Genera alertas para desviaciones significativas"""
        
        print(f"\n🚨 ALERTAS DE DESVIACIONES > {umbral_desviacion}%:")
        print("=" * 100)
        
        datos = self.obtener_comparacion(fecha_calculo)
        alertas = [d for d in datos if abs(d[5]) > umbral_desviacion]  # Desviación > umbral
        
        if not alertas:
            print(f"✅ No hay desviaciones superiores al {umbral_desviacion}%")
            return
        
        # Clasificar alertas por tipo
        alertas_criticas = [a for a in alertas if abs(a[5]) > 25.0]  # > 25%
        alertas_altas = [a for a in alertas if 15.0 < abs(a[5]) <= 25.0]  # 15-25%
        
        print(f"📊 RESUMEN DE ALERTAS:")
        print(f"   • Críticas (>25%): {len(alertas_criticas)}")
        print(f"   • Altas (15-25%): {len(alertas_altas)}")
        print(f"   • Total alertas: {len(alertas)}")
        
        print(f"\n🔴 ALERTAS CRÍTICAS (>25%):")
        for alerta in alertas_criticas:
            segmento, producto, std, real, desv_abs, desv_pct, performance, contratos, gastos, coste, seg_id, prod_id = alerta
            print(f"   {segmento} | {producto[:25]}: {desv_pct:+.2f}% (€{desv_abs:+.2f})")
        
        print(f"\n🟡 ALERTAS ALTAS (15-25%):")
        for alerta in alertas_altas:
            segmento, producto, std, real, desv_abs, desv_pct, performance, contratos, gastos, coste, seg_id, prod_id = alerta
            print(f"   {segmento} | {producto[:25]}: {desv_pct:+.2f}% (€{desv_abs:+.2f})")
        
        return alertas
    
    def exportar_csv(self, fecha_calculo='2025-09-01'):
        """Exporta comparación a CSV"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = REPORTS_DIR / f"comparacion_precios_{fecha_calculo.replace('-', '')}_{timestamp}.csv"
        
        datos = self.obtener_comparacion(fecha_calculo)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Cabecera
            writer.writerow([
                'SEGMENTO', 'PRODUCTO', 'PRECIO_STD', 'PRECIO_REAL', 
                'DESVIACION_ABSOLUTA', 'DESVIACION_PORCENTUAL', 'PERFORMANCE',
                'CONTRATOS', 'GASTOS_ASIGNADOS', 'COSTE_UNITARIO'
            ])
            
            # Datos
            for row in datos:
                writer.writerow([
                    row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}",
                    f"{row[4]:.2f}", f"{row[5]:.2f}", row[6],
                    row[7], f"{row[8]:.2f}", f"{row[9]:.2f}"
                ])
        
        print(f"\n💾 Datos exportados a: {filename}")
        return filename
    
    def comparacion_temporal(self, fecha1='2025-09-01', fecha2='2025-10-01'):
        """Compara precios reales entre dos fechas"""
        
        print(f"\n📅 COMPARACIÓN TEMPORAL: {fecha1} vs {fecha2}")
        print("=" * 100)
        
        with self.conectar_db() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                s.DESC_SEGMENTO,
                p.DESC_PRODUCTO,
                pr1.PRECIO_MANTENIMIENTO_REAL as PRECIO_MES1,
                pr2.PRECIO_MANTENIMIENTO_REAL as PRECIO_MES2,
                (pr2.PRECIO_MANTENIMIENTO_REAL - pr1.PRECIO_MANTENIMIENTO_REAL) as VARIACION,
                ROUND(((pr2.PRECIO_MANTENIMIENTO_REAL - pr1.PRECIO_MANTENIMIENTO_REAL) / ABS(pr1.PRECIO_MANTENIMIENTO_REAL)) * 100, 2) as VARIACION_PCT
            FROM PRECIO_POR_PRODUCTO_REAL pr1
            JOIN PRECIO_POR_PRODUCTO_REAL pr2 ON pr1.SEGMENTO_ID = pr2.SEGMENTO_ID 
                                             AND pr1.PRODUCTO_ID = pr2.PRODUCTO_ID
            JOIN MAESTRO_SEGMENTOS s ON pr1.SEGMENTO_ID = s.SEGMENTO_ID
            JOIN MAESTRO_PRODUCTOS p ON pr1.PRODUCTO_ID = p.PRODUCTO_ID
            WHERE pr1.FECHA_CALCULO = ? AND pr2.FECHA_CALCULO = ?
            ORDER BY ABS(VARIACION_PCT) DESC
            """
            
            cursor.execute(query, (fecha1, fecha2))
            resultados = cursor.fetchall()
            
            if not resultados:
                print("❌ No se encontraron datos para ambas fechas")
                return
            
            mejoras = [r for r in resultados if r[4] > 0]  # Precio más alto (mejor)
            empeoramientos = [r for r in resultados if r[4] < 0]  # Precio más bajo (peor)
            
            print(f"📊 RESUMEN TEMPORAL:")
            print(f"   • Mejoras: {len(mejoras)} ({len(mejoras)/len(resultados)*100:.1f}%)")
            print(f"   • Empeoramientos: {len(empeoramientos)} ({len(empeoramientos)/len(resultados)*100:.1f}%)")
            
            print(f"\n📈 MAYORES VARIACIONES:")
            print("-" * 100)
            
            for row in resultados[:10]:  # Top 10 variaciones
                segmento, producto, mes1, mes2, variacion, var_pct = row
                
                tendencia = "📈 MEJORA" if variacion > 0 else "📉 EMPEORA" if variacion < 0 else "➡️ SIN CAMBIO"
                
                print(f"{segmento:<20} | {producto[:25]:<25}")
                print(f"   {fecha1}: €{mes1:>8.2f} | {fecha2}: €{mes2:>8.2f} | Var: €{variacion:>+8.2f} ({var_pct:>+6.2f}%) | {tendencia}")
                print("-" * 100)

def main():
    """Función principal"""
    comparador = ComparadorPrecios()
    
    # Análisis completo
    datos = comparador.generar_reporte_completo()
    
    if datos:
        comparador.analisis_por_segmento()
        comparador.analisis_por_producto()
        comparador.generar_alertas(umbral_desviacion=10.0)  # Alertas > 10%
        
        # Exportar a CSV
        csv_file = comparador.exportar_csv()
        
        print(f"\n🎯 RESUMEN FINAL:")
        print(f"   ✅ Análisis completado para {len(datos)} combinaciones")
        print(f"   ✅ Reporte exportado: {csv_file}")
        print(f"   ✅ Dashboard disponible para Business Reviews")
        
        # Si hay datos de octubre, hacer comparación temporal
        try:
            comparador.comparacion_temporal('2025-09-01', '2025-10-01')
        except:
            print(f"\n💡 Para comparación temporal, ejecuta primero los precios de octubre")

if __name__ == "__main__":
    main()
