# test_chart_specific.py - Diagnóstico específico de chart_generator
import sys
from pathlib import Path

# Configurar path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
src_dir = backend_dir / 'src'
sys.path.insert(0, str(src_dir))

print("🔍 DIAGNÓSTICO ESPECÍFICO DE CHART_GENERATOR")
print("=" * 50)

# Test 1: Import del módulo completo
try:
    print("\n📦 Test 1: Import del módulo chart_generator...")
    import tools.chart_generator as chart_module
    print("✅ Módulo importado exitosamente")
    
    # Listar atributos del módulo
    attrs = [attr for attr in dir(chart_module) if not attr.startswith('_')]
    print(f"📋 Atributos disponibles: {attrs}")
    
except Exception as e:
    print(f"❌ Error importando módulo: {e}")
    exit(1)

# Test 2: Import específico de la clase
try:
    print("\n🏗️ Test 2: Import específico de CDGDashboardGenerator...")
    from tools.chart_generator import CDGDashboardGenerator
    print("✅ Clase importada exitosamente")
    
    # Verificar métodos de la clase
    methods = [method for method in dir(CDGDashboardGenerator) if not method.startswith('_')]
    print(f"📋 Métodos de la clase: {methods}")
    
except Exception as e:
    print(f"❌ Error importando clase: {e}")
    exit(1)

# Test 3: Instanciación de la clase
try:
    print("\n🔧 Test 3: Instanciación de CDGDashboardGenerator...")
    generator = CDGDashboardGenerator()
    print("✅ Instanciación exitosa")
    
    # Test método específico
    print("\n📊 Test 4: Probando método generate_gestor_dashboard...")
    test_gestor = {"gestor_id": 1, "desc_gestor": "Test"}
    test_kpis = {"margen_neto": 12.5, "roe": 8.3}
    
    result = generator.generate_gestor_dashboard(test_gestor, test_kpis)
    print(f"✅ Método ejecutado: {len(result.get('charts', []))} charts generados")
    
except Exception as e:
    print(f"❌ Error en instanciación o métodos: {e}")
    print(f"   Tipo de error: {type(e).__name__}")
    import traceback
    print(f"   Stack trace: {traceback.format_exc()}")

# Test 5: Función independiente validate_chart_generator
try:
    print("\n🔍 Test 5: Función validate_chart_generator...")
    from tools.chart_generator import validate_chart_generator
    validation = validate_chart_generator()
    print(f"✅ Validación: {validation}")
    
except Exception as e:
    print(f"❌ Error en función de validación: {e}")

print("\n" + "=" * 50)
print("🎯 DIAGNÓSTICO COMPLETADO")
