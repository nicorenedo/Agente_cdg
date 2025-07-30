# backend/test_quick_fix.py
import sys
import os
sys.path.append('.')

from src.database.db_connection import test_database_connection

print("=== Test Conexión BD ===")
result = test_database_connection()
print(f"Status: {result['status']}")
print(f"BD Path: {result['database_path']}")
if result['status'] == 'success':
    print(f"Tablas encontradas: {result['total_tables']}")
    for table, count in result['tables'].items():
        print(f"  - {table}: {count} registros")
else:
    print(f"Error: {result['error']}")
