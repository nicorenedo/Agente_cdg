import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🔍 Probando import de main.py...")

try:
    from main import app
    print("✅ Import de main exitoso")
    print(f"📊 App type: {type(app)}")
    
    # Verificar rutas disponibles
    routes = [route.path for route in app.routes]
    print(f"🛣️  Rutas encontradas: {len(routes)}")
    for route in routes[:10]:  # Mostrar las primeras 10
        print(f"   - {route}")
        
except Exception as e:
    print(f"❌ Error importando: {e}")
    import traceback
    traceback.print_exc()
