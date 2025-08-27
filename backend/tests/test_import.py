# test_import.py - Archivo de diagnóstico CORREGIDO
import sys
import os
from pathlib import Path

# ✅ CORRECCIÓN: Subir al directorio backend y luego ir a src
current_dir = Path(__file__).resolve().parent  # tests\
backend_dir = current_dir.parent                # backend\
src_dir = backend_dir / 'src'                  # backend\src\

# Añadir paths correctos
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

print(f"📂 Current dir: {current_dir}")
print(f"📂 Backend dir: {backend_dir}")  
print(f"📂 Src dir: {src_dir}")
print(f"📂 Src exists: {src_dir.exists()}")
print(f"📂 Tools dir exists: {(src_dir / 'tools').exists()}")
print(f"📂 Chart generator exists: {(src_dir / 'tools' / 'chart_generator.py').exists()}")

# Listar contenido de tools para verificar
tools_dir = src_dir / 'tools'
if tools_dir.exists():
    print(f"📋 Contenido de tools/:")
    for file in tools_dir.iterdir():
        print(f"   - {file.name}")

# Test import directo
print(f"\n🔍 Intentando import desde: {src_dir}")
try:
    from tools.chart_generator import CDGDashboardGenerator
    print("✅ Import exitoso!")
    
    generator = CDGDashboardGenerator()
    print("✅ Instanciacion exitosa!")
    
    # Test básico de funcionalidad
    validation = generator.validate_chart_generator()
    print(f"✅ Validación: {validation.get('status', 'UNKNOWN')}")
    
except ImportError as e:
    print(f"❌ Error de import: {e}")
    print(f"📋 Python path actual: {sys.path[:3]}...")
except Exception as e:
    print(f"❌ Error de instanciación: {e}")
    print(f"   Tipo: {type(e).__name__}")
