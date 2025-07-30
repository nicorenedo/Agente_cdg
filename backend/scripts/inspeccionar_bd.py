# script_inspeccionar_bd.py
import sqlite3
import os

# Ruta a tu BD
db_path = r"C:\Users\nicolas.renedo\Documents\GEN AI\BancaMarch_CdG\backend\src\database\BM_CONTABILIDAD_CDG.db"

def inspeccionar_base_datos():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("="*50)
        print("📊 INSPECCIÓN COMPLETA DE LA BASE DE DATOS")
        print("="*50)
        
        # 1. Listar todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        print(f"\n🏷️  TABLAS ENCONTRADAS ({len(tablas)}):")
        print("-" * 30)
        for tabla in tablas:
            print(f"  • {tabla[0]}")
        
        # 2. Para cada tabla, mostrar esquema
        for tabla in tablas:
            nombre_tabla = tabla[0]
            print(f"\n📋 ESQUEMA DE: {nombre_tabla}")
            print("-" * (len(nombre_tabla) + 15))
            
            cursor.execute(f"PRAGMA table_info({nombre_tabla});")
            columnas = cursor.fetchall()
            
            for col in columnas:
                col_id, nombre, tipo, no_null, default, pk = col
                pk_marker = " [PK]" if pk else ""
                null_marker = " NOT NULL" if no_null else ""
                default_marker = f" DEFAULT {default}" if default else ""
                print(f"  {nombre:<25} {tipo:<15}{pk_marker}{null_marker}{default_marker}")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
            count = cursor.fetchone()[0]
            print(f"  📊 Registros: {count}")
        
        print("\n" + "="*50)
        print("✅ Inspección completada")
        
    except Exception as e:
        print(f"❌ Error inspeccionando BD: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    inspeccionar_base_datos()
