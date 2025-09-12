# tests/test_main_simple.py
import pytest
import sys
import os

# Añadir el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_main():
    """Test para verificar que main.py se puede importar"""
    try:
        import main
        print(f"✅ main.py importado exitosamente")
        print(f"📊 IMPORTS_SUCCESSFUL: {main.IMPORTS_SUCCESSFUL}")
        
        # Verificar que la app existe
        assert hasattr(main, 'app'), "No se encontró la aplicación FastAPI"
        print(f"✅ FastAPI app encontrada")
        
        # Ver endpoints registrados
        routes = [route.path for route in main.app.routes]
        print(f"📍 Rutas registradas: {routes[:10]}...")  # Primeras 10
        
        assert len(routes) > 0, "No hay rutas registradas"
        assert "/" in routes, "Ruta raíz no encontrada"
        
    except Exception as e:
        pytest.fail(f"Error importando main.py: {e}")

def test_basic_fastapi():
    """Test básico de FastAPI"""
    from fastapi.testclient import TestClient
    
    try:
        import main
        client = TestClient(main.app)
        
        # Test endpoint raíz
        response = client.get("/")
        print(f"📡 Status code endpoint raíz: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Respuesta: {response.text}")
            # Intentar obtener información del error
            print(f"📋 Headers: {response.headers}")
        
        assert response.status_code == 200, f"Endpoint raíz falló: {response.text}"
        
    except Exception as e:
        pytest.fail(f"Error en test básico FastAPI: {e}")

if __name__ == "__main__":
    test_import_main()
    test_basic_fastapi()
