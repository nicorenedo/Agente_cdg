"""
main_simple.py - Versión corregida sin dependencias problemáticas
"""

import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Función de conexión simple
def get_db_connection():
    db_path = 'src/database/BM_CONTABILIDAD_CDG.db'
    return sqlite3.connect(db_path)

# Verificar base de datos al inicio
try:
    print("🔍 Verificando estructura de base de datos...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    
    table_names = [table[0] for table in tables]
    print(f"✅ Tablas encontradas ({len(tables)}): {table_names}")
    
    # Verificar si existe MAESTROGESTORES
    if 'MAESTROGESTORES' in table_names:
        print("✅ MAESTROGESTORES encontrada")
    else:
        print("❌ MAESTROGESTORES NO encontrada")
        print("📋 Tablas disponibles para usar:", table_names[:5])
    
except Exception as e:
    print(f"❌ Error verificando BD: {e}")

# Crear app FastAPI
app = FastAPI(title="CDG API Diagnóstico")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "CDG API funcionando"}

@app.get("/test")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Probar con una tabla que sí existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        first_table = cursor.fetchone()
        
        if first_table:
            table_name = first_table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            
            conn.close()
            return {
                "status": "success",
                "database_connected": True,
                "test_table": table_name,
                "record_count": count
            }
        else:
            conn.close()
            return {
                "status": "error", 
                "message": "No tables found in database"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/test-detailed")
def test_detailed():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener información detallada de todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_info = {}
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                table_info[table_name] = count
            except:
                table_info[table_name] = "error"
        
        conn.close()
        
        return {
            "status": "success",
            "total_tables": len(tables),
            "table_details": table_info,
            "maestrogestores_exists": "MAESTROGESTORES" in [t[0] for t in tables]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando CDG API con diagnóstico completo...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
