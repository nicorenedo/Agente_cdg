# test_integration.py - Script para validar toda la integración

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Prueba todos los endpoints críticos"""
    
    tests = [
        # Health checks
        {"method": "GET", "url": "/health", "name": "Health Check"},
        {"method": "GET", "url": "/database/health", "name": "Database Health"},
        
        # Dashboard crítico
        {"method": "GET", "url": "/api/dashboard/2025-10", "name": "Dashboard Data"},
        {"method": "GET", "url": "/periods/available", "name": "Períodos Disponibles"},
        
        # Gestores
        {"method": "GET", "url": "/gestores", "name": "Lista Gestores"},
        {"method": "GET", "url": "/gestor/1/performance?periodo=2025-10", "name": "Performance Gestor"},
        
        # KPIs
        {"method": "GET", "url": "/kpis/consolidados?periodo=2025-10", "name": "KPIs Consolidados"},
        {"method": "GET", "url": "/analisis-comparativo?periodo=2025-10", "name": "Análisis Comparativo"},
        
        # Chat
        {"method": "POST", "url": "/chat", "name": "Chat Endpoint",
         "data": {
             "user_id": "test_user",
             "message": "¿Cuál es el ROE del período actual?",
             "periodo": "2025-10"
         }},
    ]
    
    results = []
    
    for test in tests:
        try:
            print(f"🧪 Testing: {test['name']}")
            
            if test['method'] == 'GET':
                response = requests.get(f"{BASE_URL}{test['url']}", timeout=10)
            else:
                response = requests.post(
                    f"{BASE_URL}{test['url']}", 
                    json=test['data'], 
                    timeout=10
                )
            
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            results.append(f"{status} - {test['name']}")
            
            if response.status_code != 200:
                print(f"   Error: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            results.append(f"🔌 NO CONNECTION - {test['name']}")
        except Exception as e:
            results.append(f"❌ ERROR - {test['name']}: {str(e)}")
    
    print("\n" + "="*50)
    print("📊 RESULTADOS DEL TEST:")
    print("="*50)
    for result in results:
        print(result)
    
    return results

if __name__ == "__main__":
    print("🚀 Iniciando tests de integración...")
    print(f"⏰ Timestamp: {datetime.now()}")
    print("-" * 50)
    
    test_endpoints()
