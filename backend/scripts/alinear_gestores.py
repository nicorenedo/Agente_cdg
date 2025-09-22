#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALINEAMIENTO DE GESTORES - CORREGIR MAESTRO_CONTRATOS
===================================================
Actualiza MAESTRO_CONTRATOS para que todos los contratos de un cliente
tengan el mismo gestor asignado al cliente en MAESTRO_CLIENTES
"""

import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def corregir_gestores_contratos():
    """
    Corrige MAESTRO_CONTRATOS.GESTOR_ID para que coincida con 
    MAESTRO_CLIENTES.GESTOR_ID (un cliente = un gestor para todos sus contratos)
    """
    print("🔧 CORRECCIÓN DE GESTORES - CONTRATOS → CLIENTES")
    print("=" * 60)
    print("Lógica: Todos los contratos de un cliente deben tener el mismo gestor del cliente")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. ANÁLISIS INICIAL DE INCONSISTENCIAS
        print("\n📊 Análisis inicial de inconsistencias...")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_contratos,
                COUNT(CASE WHEN mc.GESTOR_ID != mcl.GESTOR_ID THEN 1 END) as contratos_inconsistentes,
                ROUND(COUNT(CASE WHEN mc.GESTOR_ID != mcl.GESTOR_ID THEN 1 END) * 100.0 / COUNT(*), 2) as porcentaje_inconsistente
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
        """)
        
        stats_inicial = cursor.fetchone()
        total_contratos, contratos_inconsistentes, porcentaje = stats_inicial
        
        print(f"   • Total contratos: {total_contratos}")
        print(f"   • Contratos inconsistentes: {contratos_inconsistentes}")
        print(f"   • Porcentaje inconsistente: {porcentaje}%")
        
        if contratos_inconsistentes == 0:
            print("✅ ¡No hay inconsistencias! Base de datos ya está alineada.")
            return
        
        # 2. MOSTRAR EJEMPLOS DE INCONSISTENCIAS
        print("\n📋 Ejemplos de inconsistencias a corregir:")
        cursor.execute("""
            SELECT 
                mc.CONTRATO_ID,
                mc.CLIENTE_ID,
                mcl.NOMBRE_CLIENTE,
                mc.GESTOR_ID as gestor_contrato_actual,
                mcl.GESTOR_ID as gestor_cliente_correcto
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
            WHERE mc.GESTOR_ID != mcl.GESTOR_ID
            ORDER BY mc.CLIENTE_ID, mc.CONTRATO_ID
            LIMIT 10
        """)
        
        ejemplos = cursor.fetchall()
        for contrato_id, cliente_id, nombre, gestor_actual, gestor_correcto in ejemplos:
            print(f"   • Contrato {contrato_id} (Cliente {cliente_id}-{nombre}): {gestor_actual} → {gestor_correcto}")
        
        if len(ejemplos) == 10:
            print("   ... y más")
        
        # 3. CREAR BACKUP ANTES DE PROCEDER
        print(f"\n💾 Creando backup de seguridad...")
        
        backup_table = f"MAESTRO_CONTRATOS_BACKUP_{timestamp}"
        cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM MAESTRO_CONTRATOS")
        
        cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
        backup_count = cursor.fetchone()[0]
        print(f"   ✅ Backup creado: {backup_table} ({backup_count} registros)")
        
        # 4. EJECUTAR LA CORRECCIÓN
        print("\n🔄 Ejecutando corrección de gestores en contratos...")
        print("   Actualizando MAESTRO_CONTRATOS.GESTOR_ID = MAESTRO_CLIENTES.GESTOR_ID")
        
        cursor.execute("""
            UPDATE MAESTRO_CONTRATOS 
            SET GESTOR_ID = (
                SELECT mcl.GESTOR_ID 
                FROM MAESTRO_CLIENTES mcl 
                WHERE mcl.CLIENTE_ID = MAESTRO_CONTRATOS.CLIENTE_ID
            )
            WHERE EXISTS (
                SELECT 1 FROM MAESTRO_CLIENTES mcl 
                WHERE mcl.CLIENTE_ID = MAESTRO_CONTRATOS.CLIENTE_ID
            )
        """)
        
        contratos_actualizados = cursor.rowcount
        print(f"   ✅ {contratos_actualizados} contratos actualizados correctamente")
        
        # 5. VERIFICACIÓN POST-CORRECCIÓN
        print("\n📊 Verificación post-corrección...")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_contratos,
                COUNT(CASE WHEN mc.GESTOR_ID != mcl.GESTOR_ID THEN 1 END) as contratos_inconsistentes,
                ROUND(COUNT(CASE WHEN mc.GESTOR_ID != mcl.GESTOR_ID THEN 1 END) * 100.0 / COUNT(*), 2) as porcentaje_inconsistente
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
        """)
        
        stats_final = cursor.fetchone()
        total_final, inconsistentes_final, porcentaje_final = stats_final
        
        print(f"   • Total contratos: {total_final}")
        print(f"   • Contratos inconsistentes: {inconsistentes_final}")
        print(f"   • Porcentaje inconsistente: {porcentaje_final}%")
        
        # 6. VERIFICAR CASOS ESPECÍFICOS
        print("\n🔍 Verificación de casos específicos...")
        
        # Verificar que cada cliente ahora tiene un solo gestor en todos sus contratos
        cursor.execute("""
            SELECT 
                mcl.CLIENTE_ID,
                mcl.NOMBRE_CLIENTE,
                mcl.GESTOR_ID as gestor_cliente,
                COUNT(DISTINCT mc.GESTOR_ID) as gestores_diferentes_en_contratos,
                COUNT(mc.CONTRATO_ID) as total_contratos_cliente
            FROM MAESTRO_CLIENTES mcl
            JOIN MAESTRO_CONTRATOS mc ON mcl.CLIENTE_ID = mc.CLIENTE_ID
            GROUP BY mcl.CLIENTE_ID, mcl.NOMBRE_CLIENTE, mcl.GESTOR_ID
            HAVING gestores_diferentes_en_contratos > 1
        """)
        
        casos_problema = cursor.fetchall()
        
        if casos_problema:
            print(f"   ⚠️ AÚN HAY {len(casos_problema)} CLIENTES CON MÚLTIPLES GESTORES:")
            for cliente_id, nombre, gestor_cliente, gestores_dif, total_contratos in casos_problema[:5]:
                print(f"   • Cliente {cliente_id} ({nombre}): {gestores_dif} gestores diferentes en {total_contratos} contratos")
        else:
            print("   ✅ PERFECTO: Cada cliente tiene un único gestor en todos sus contratos")
        
        # Caso específico Cliente 68
        cursor.execute("""
            SELECT 
                mc.CONTRATO_ID,
                mc.GESTOR_ID,
                mcl.GESTOR_ID as gestor_cliente
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
            WHERE mc.CLIENTE_ID = '68'
        """)
        
        contratos_68 = cursor.fetchall()
        if contratos_68:
            gestores_unicos = set(c[1] for c in contratos_68)
            gestor_cliente = contratos_68[0][2]
            print(f"   • Cliente 68: {len(contratos_68)} contratos, gestor cliente {gestor_cliente}, gestores en contratos: {gestores_unicos}")
        
        # 7. RESUMEN FINAL
        mejora = porcentaje - porcentaje_final
        
        print(f"\n✅ CORRECCIÓN COMPLETADA:")
        print(f"   • Inconsistencias eliminadas: {contratos_inconsistentes - inconsistentes_final}")
        print(f"   • Mejora: {mejora:.2f} puntos porcentuales")
        print(f"   • Contratos actualizados: {contratos_actualizados}")
        print(f"   • Backup disponible: {backup_table}")
        
        if inconsistentes_final == 0:
            print(f"   🎉 ¡ÉXITO TOTAL! Base de datos 100% consistente")
        else:
            print(f"   ❌ ERROR: Aún hay {inconsistentes_final} inconsistencias")
        
        # 8. CONFIRMAR CAMBIOS
        conn.commit()
        
        return {
            'contratos_actualizados': contratos_actualizados,
            'inconsistencias_eliminadas': contratos_inconsistentes - inconsistentes_final,
            'porcentaje_mejora': mejora,
            'backup_table': backup_table,
            'estado_final': 'PERFECTO' if inconsistentes_final == 0 else 'CON_ERRORES'
        }

if __name__ == "__main__":
    try:
        print("🚀 Iniciando corrección de gestores en contratos...")
        print("\n⚠️ IMPORTANTE: Este script actualiza MAESTRO_CONTRATOS, no MAESTRO_CLIENTES")
        print("   Lógica: Contrato.gestor = Cliente.gestor (un cliente = un gestor)")
        
        # Confirmar antes de proceder
        respuesta = input("\n¿Proceder con la corrección? (S/n): ").strip().lower()
        
        if respuesta in ['s', 'si', 'sí', 'yes', '']:
            resultado = corregir_gestores_contratos()
            
            print(f"\n🎉 ¡PROCESO COMPLETADO!")
            print(f"🚀 Todos los contratos ahora tienen el gestor correcto del cliente")
            print(f"📊 Estado: {resultado['estado_final']}")
            
        else:
            print("❌ Proceso cancelado por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error durante la corrección: {e}")
        print("💾 Los datos originales están respaldados")
        raise
