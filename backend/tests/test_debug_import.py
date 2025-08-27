"""
Test de Diagnóstico Avanzado - Identificar problema específico de imports
"""
import sys
import os
from pathlib import Path

# Configurar paths idénticos al test original
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / 'src'
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

print("🔍 DIAGNÓSTICO AVANZADO DE IMPORTS")
print("=" * 60)

# Test 1: Verificar paths y archivos
print(f"\n📂 Paths configurados:")
print(f"   Backend: {backend_dir}")
print(f"   Src: {src_dir}")
print(f"   Tools existe: {(src_dir / 'tools').exists()}")
print(f"   Chart generator existe: {(src_dir / 'tools' / 'chart_generator.py').exists()}")

# Test 2: Intentar imports paso a paso
print(f"\n🔍 Test de imports paso a paso:")

try:
    print("   ➤ Importando tools...")
    import tools
    print("   ✅ tools importado")
except Exception as e:
    print(f"   ❌ Error importando tools: {e}")

try:
    print("   ➤ Importando tools.chart_generator...")
    import tools.chart_generator
    print("   ✅ tools.chart_generator importado")
except Exception as e:
    print(f"   ❌ Error importando tools.chart_generator: {e}")

try:
    print("   ➤ Importando CDGDashboardGenerator...")
    from tools.chart_generator import CDGDashboardGenerator
    print("   ✅ CDGDashboardGenerator importado")
except Exception as e:
    print(f"   ❌ Error importando CDGDashboardGenerator: {e}")

# Test 3: Simular EXACTAMENTE lo que hace cdg_agent.py
print(f"\n🎯 Simulando imports de cdg_agent.py:")

def simulate_cdg_agent_imports():
    """Simula exactamente los imports de cdg_agent.py"""
    try:
        # Paths idénticos a cdg_agent.py
        current_file = Path(__file__).resolve()
        tests_dir = current_file.parent
        backend_dir = tests_dir.parent
        src_dir = backend_dir / 'src'
        
        # Simular path de agents/cdg_agent.py
        agents_dir = src_dir / 'agents'
        
        print(f"   📍 Simulando desde: {agents_dir}")
        print(f"   📂 Src calculado: {src_dir}")
        
        # Configurar sys.path como en cdg_agent.py
        import sys
        sys.path.insert(0, str(src_dir))
        sys.path.insert(0, str(backend_dir))
        
        # Intentar import como en cdg_agent.py
        from tools.chart_generator import CDGDashboardGenerator, validate_chart_generator
        
        print("   ✅ Import simulado exitoso")
        
        # Test validación
        validation = validate_chart_generator()
        print(f"   ✅ Validación: {validation['status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en simulación: {e}")
        print(f"   📍 Tipo: {type(e).__name__}")
        return False

success = simulate_cdg_agent_imports()

# Test 4: Verificar contenido de __init__.py
print(f"\n📄 Verificando archivos __init__.py:")
init_files = [
    src_dir / '__init__.py',
    src_dir / 'tools' / '__init__.py',
    src_dir / 'agents' / '__init__.py'
]

for init_file in init_files:
    if init_file.exists():
        size = init_file.stat().st_size
        print(f"   ✅ {init_file.relative_to(backend_dir)}: {size} bytes")
        
        # Verificar contenido si no está vacío
        if size > 0:
            with open(init_file, 'r') as f:
                content = f.read()[:100]  # Primeros 100 caracteres
                print(f"      Contenido: {repr(content)}")
    else:
        print(f"   ❌ FALTA: {init_file.relative_to(backend_dir)}")

print("\n" + "=" * 60)
print(f"🎯 RESULTADO FINAL: {'✅ ÉXITO' if success else '❌ FALLA'}")
