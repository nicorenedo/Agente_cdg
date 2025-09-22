#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROLLBACK ALINEAMIENTO DE GESTORES - RESTAURAR ESTADO ORIGINAL
===========================================================
Script de emergencia para deshacer el alineamiento de gestores
y restaurar MAESTRO_CLIENTES a su estado original
"""

import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

def listar_backups_disponibles():
    """
    Lista todos los backups disponibles de MAESTRO_CLIENTES
    """
    print("🔍 BUSCANDO BACKUPS DISPONIBLES...")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Buscar todas las tablas de backup
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='table' 
              AND name LIKE 'MAESTRO_CLIENTES_BACKUP_%'
            ORDER BY name DESC
        """)
        
        backups = cursor.fetchall()
        
        if not backups:
            print("❌ No se encontraron backups de MAESTRO_CLIENTES")
            return []
        
        print(f"📋 Encontrados {len(backups)} backups:")
        
        backup_info = []
        for i, (tabla_nombre, _) in enumerate(backups):
            # Extraer timestamp del nombre
            try:
                timestamp_parte = tabla_nombre.replace('MAESTRO_CLIENTES_BACKUP_', '')
                if len(timestamp_parte) == 15:  # YYYYMMDD_HHMMSS
                    fecha_str = timestamp_parte[:8]
                    hora_str = timestamp_parte[9:]
                    fecha_legible = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:8]}"
                    hora_legible = f"{hora_str[:2]}:{hora_str[2:4]}:{hora_str[4:6]}"
                    fecha_completa = f"{fecha_legible} {hora_legible}"
                else:
                    fecha_completa = timestamp_parte
            except:
                fecha_completa = "Fecha desconocida"
            
            # Contar registros en el backup
            cursor.execute(f"SELECT COUNT(*) FROM {tabla_nombre}")
            num_registros = cursor.fetchone()[0]
            
            backup_info.append({
                'indice': i + 1,
                'tabla': tabla_nombre,
                'fecha': fecha_completa,
                'registros': num_registros
            })
            
            print(f"   {i+1}. {tabla_nombre}")
            print(f"      📅 Creado: {fecha_completa}")
            print(f"      📊 Registros: {num_registros}")
        
        return backup_info

def verificar_estado_actual():
    """
    Verifica el estado actual de inconsistencias
    """
    print("\n📊 VERIFICANDO ESTADO ACTUAL...")
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Estado actual
        cursor.execute("""
            SELECT 
                COUNT(*) as total_contratos,
                COUNT(CASE WHEN mc.GESTOR_ID != mcl.GESTOR_ID THEN 1 END) as contratos_inconsistentes,
                ROUND(COUNT(CASE WHEN mc.GESTOR_ID != mcl.GESTOR_ID THEN 1 END) * 100.0 / COUNT(*), 2) as porcentaje_inconsistente
            FROM MAESTRO_CONTRATOS mc
            JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
        """)
        
        stats = cursor.fetchone()
        total, inconsistentes, porcentaje = stats
        
        print(f"   • Total contratos: {total}")
        print(f"   • Contratos inconsistentes: {inconsistentes}")
        print(f"   • Porcentaje inconsistente: {porcentaje}%")
        
        # Algunos casos específicos
        cursor.execute("""
            SELECT COUNT(DISTINCT mcl.CLIENTE_ID) 
            FROM MAESTRO_CLIENTES mcl
            WHERE mcl.GESTOR_ID = '21'
        """)
        clientes_21 = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT mcl.GESTOR_ID
            FROM MAESTRO_CLIENTES mcl
            WHERE mcl.CLIENTE_ID = '68'
        """)
        gestor_68 = cursor.fetchone()
        gestor_68 = gestor_68[0] if gestor_68 else "No encontrado"
        
        print(f"   • Gestor 21 tiene {clientes_21} clientes")
        print(f"   • Cliente 68 tiene gestor {gestor_68}")
        
        return {
            'total_contratos': total,
            'inconsistentes': inconsistentes,
            'porcentaje': porcentaje,
            'clientes_21': clientes_21,
            'gestor_68': gestor_68
        }

def restaurar_desde_backup(tabla_backup):
    """
    Restaura MAESTRO_CLIENTES desde una tabla de backup específica
    """
    print(f"\n🔄 RESTAURANDO DESDE {tabla_backup}...")
    print("=" * 60)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Verificar que existe el backup
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (tabla_backup,))
        
        if not cursor.fetchone():
            print(f"❌ Error: No existe la tabla {tabla_backup}")
            return False
        
        # Crear backup del estado actual (por si acaso)
        timestamp_rollback = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_actual = f"MAESTRO_CLIENTES_ANTES_ROLLBACK_{timestamp_rollback}"
        
        cursor.execute(f"CREATE TABLE {backup_actual} AS SELECT * FROM MAESTRO_CLIENTES")
        print(f"   💾 Backup del estado actual: {backup_actual}")
        
        # Contar registros originales
        cursor.execute("SELECT COUNT(*) FROM MAESTRO_CLIENTES")
        registros_actuales = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {tabla_backup}")
        registros_backup = cursor.fetchone()[0]
        
        print(f"   📊 Registros actuales: {registros_actuales}")
        print(f"   📊 Registros en backup: {registros_backup}")
        
        # Restaurar datos
        print(f"   🗑️ Eliminando datos actuales...")
        cursor.execute("DELETE FROM MAESTRO_CLIENTES")
        
        print(f"   📥 Restaurando desde backup...")
        cursor.execute(f"INSERT INTO MAESTRO_CLIENTES SELECT * FROM {tabla_backup}")
        
        filas_restauradas = cursor.rowcount
        
        # Verificar que se restauró correctamente
        cursor.execute("SELECT COUNT(*) FROM MAESTRO_CLIENTES")
        registros_finales = cursor.fetchone()[0]
        
        if registros_finales != registros_backup:
            print(f"⚠️ ADVERTENCIA: Registros no coinciden!")
            print(f"   Esperados: {registros_backup} | Obtenidos: {registros_finales}")
            
            # Rollback del rollback
            cursor.execute("ROLLBACK")
            return False
        
        # Confirmar cambios
        conn.commit()
        
        print(f"   ✅ Restauración completada: {filas_restauradas} registros")
        
        return True

def verificar_restauracion():
    """
    Verifica que la restauración fue exitosa
    """
    print(f"\n✅ VERIFICANDO RESTAURACIÓN...")
    
    estado_final = verificar_estado_actual()
    
    print(f"\n📊 RESULTADO DE LA RESTAURACIÓN:")
    print(f"   • Estado restaurado correctamente")
    print(f"   • Inconsistencias actuales: {estado_final['inconsistentes']}")
    print(f"   • Porcentaje inconsistente: {estado_final['porcentaje']}%")
    
    return estado_final

def rollback_completo():
    """
    Función principal de rollback
    """
    print("🚨 ROLLBACK - RESTAURAR ESTADO ORIGINAL")
    print("=" * 50)
    print("Este script restaurará MAESTRO_CLIENTES a su estado anterior")
    print("al alineamiento de gestores.\n")
    
    # 1. Verificar estado actual
    estado_actual = verificar_estado_actual()
    
    if estado_actual['inconsistentes'] > 1000:  # Si hay muchas inconsistencias, probablemente ya está en estado original
        print(f"\n⚠️ ATENCIÓN: Ya hay {estado_actual['inconsistentes']} inconsistencias")
        print("Posiblemente la base de datos ya está en su estado original.")
        continuar = input("¿Continuar con el rollback? (s/N): ").strip().lower()
        if continuar not in ['s', 'si', 'sí', 'yes']:
            print("❌ Rollback cancelado")
            return False
    
    # 2. Listar backups disponibles
    backups = listar_backups_disponibles()
    
    if not backups:
        print("❌ No hay backups disponibles para restaurar")
        return False
    
    # 3. Seleccionar backup
    print(f"\n🎯 SELECCIONAR BACKUP PARA RESTAURAR:")
    try:
        seleccion = input(f"Ingresa el número del backup (1-{len(backups)}) o ENTER para el más reciente: ").strip()
        
        if seleccion == "":
            backup_elegido = backups[0]  # Más reciente
        else:
            indice = int(seleccion) - 1
            if 0 <= indice < len(backups):
                backup_elegido = backups[indice]
            else:
                print("❌ Selección inválida")
                return False
    except ValueError:
        print("❌ Entrada inválida")
        return False
    
    print(f"\n📋 Backup seleccionado:")
    print(f"   • Tabla: {backup_elegido['tabla']}")
    print(f"   • Fecha: {backup_elegido['fecha']}")
    print(f"   • Registros: {backup_elegido['registros']}")
    
    # 4. Confirmación final
    print(f"\n⚠️ CONFIRMACIÓN FINAL:")
    print(f"Se restaurará MAESTRO_CLIENTES desde {backup_elegido['tabla']}")
    print(f"Los datos actuales se perderán (se creará backup de seguridad)")
    
    confirmacion = input("¿Confirmar rollback? (escriba 'CONFIRMAR'): ").strip()
    
    if confirmacion != "CONFIRMAR":
        print("❌ Rollback cancelado - se requiere escribir 'CONFIRMAR'")
        return False
    
    # 5. Ejecutar restauración
    exito = restaurar_desde_backup(backup_elegido['tabla'])
    
    if not exito:
        print("❌ Error durante la restauración")
        return False
    
    # 6. Verificar resultado
    verificar_restauracion()
    
    print(f"\n🎉 ¡ROLLBACK COMPLETADO!")
    print(f"📊 MAESTRO_CLIENTES restaurado al estado del {backup_elegido['fecha']}")
    print(f"🔧 El sistema CDG debe funcionar como antes del alineamiento")
    
    return True

if __name__ == "__main__":
    try:
        print("🚀 Iniciando proceso de rollback...")
        
        exito = rollback_completo()
        
        if exito:
            print(f"\n✅ ¡ROLLBACK EXITOSO!")
            print(f"Tu base de datos está restaurada al estado original")
        else:
            print(f"\n❌ Rollback no completado")
            
    except Exception as e:
        print(f"\n❌ Error durante el rollback: {e}")
        print("💾 Revisa los backups manualmente si es necesario")
        raise
