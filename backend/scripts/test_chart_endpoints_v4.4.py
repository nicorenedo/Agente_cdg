"""
Script de pruebas para Chart Generator V4.4 con sistema de confidencialidad
Ubicación: backend/scripts/test_chart_endpoints_v4.4.py

Prueba todos los endpoints de gráficos dinámicos mejorados
"""

import requests
import json
from datetime import datetime
import time
import sys
import os

# Configuración
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

class ChartEndpointTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def log(self, message: str, test_name: str = ""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        if test_name:
            self.results[test_name] = message

    def test_health_check(self):
        """Verificar que el servidor esté activo"""
        self.log("🏥 Testing health check...", "health")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
            if response.status_code == 200:
                self.log("✅ Servidor activo y funcionando", "health")
                return True
            else:
                self.log(f"❌ Health check falló: {response.status_code}", "health")
                return False
        except Exception as e:
            self.log(f"❌ Error conectando al servidor: {e}", "health")
            return False

    def test_chart_generator_validation(self):
        """Validar que el chart generator V4.4 esté funcionando"""
        self.log("🔧 Testing chart generator validation...", "generator_validation")
        try:
            response = requests.get(f"{self.base_url}/admin/validate-chart-generator", timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json().get('data', {})
                status = data.get('status', 'UNKNOWN')
                version = data.get('version', 'N/A')
                azure_available = data.get('azure_openai_available', False)
                confidentiality = data.get('confidentiality_features', False)
                
                self.log(f"✅ Chart Generator: {status} - {version}", "generator_validation")
                self.log(f"   🚀 Azure OpenAI: {'✅' if azure_available else '❌'}")
                self.log(f"   🔐 Confidencialidad: {'✅' if confidentiality else '❌'}")
                
                self.total_tests += 1
                if status == 'OK':
                    self.passed_tests += 1
                    return True
                return False
            else:
                self.log(f"❌ Error validating chart generator: {response.status_code}", "generator_validation")
                return False
        except Exception as e:
            self.log(f"❌ Error en validación: {e}", "generator_validation")
            return False

    def test_charts_meta_by_role(self):
        """Test endpoint /charts/meta con diferentes roles"""
        self.log("📊 Testing /charts/meta with roles...", "charts_meta")
        
        roles_to_test = ["GESTOR", "CONTROL_GESTION"]
        results = {}
        
        for role in roles_to_test:
            try:
                response = requests.get(f"{self.base_url}/charts/meta?user_role={role}", timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    available_metrics = len(data.get('available_for_role', {}).get('metrics', []))
                    chart_types = len(data.get('chart_types', {}))
                    confidentiality_enabled = data.get('confidentiality_enabled', False)
                    
                    results[role] = {
                        'metrics': available_metrics,
                        'chart_types': chart_types,
                        'confidentiality': confidentiality_enabled
                    }
                    
                    self.log(f"✅ {role}: {available_metrics} métricas, {chart_types} tipos, Confidencialidad: {'✅' if confidentiality_enabled else '❌'}")
                else:
                    self.log(f"❌ Error {role}: {response.status_code}")
                    results[role] = {'error': response.status_code}
                    
            except Exception as e:
                self.log(f"❌ Error testing {role}: {e}")
                results[role] = {'error': str(e)}
        
        self.total_tests += 1
        if all('error' not in result for result in results.values()):
            self.passed_tests += 1
            
        return results

    def test_charts_options_by_role(self):
        """Test nuevos endpoints /charts/options/{role}"""
        self.log("🔐 Testing /charts/options by role...", "charts_options")
        
        roles_to_test = ["GESTOR", "CONTROL_GESTION"]
        results = {}
        
        for role in roles_to_test:
            try:
                response = requests.get(f"{self.base_url}/charts/options/{role}", timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    metrics = len(data.get('metrics', []))
                    dimensions = len(data.get('dimensions', []))
                    chart_types = len(data.get('chart_types', []))
                    
                    results[role] = {
                        'metrics': metrics,
                        'dimensions': dimensions,
                        'chart_types': chart_types,
                        'success': True
                    }
                    
                    self.log(f"✅ {role}: {metrics} métricas, {dimensions} dimensiones, {chart_types} tipos")
                else:
                    self.log(f"❌ Error {role}: {response.status_code}")
                    results[role] = {'error': response.status_code, 'success': False}
                    
            except Exception as e:
                self.log(f"❌ Error testing {role}: {e}")
                results[role] = {'error': str(e), 'success': False}
        
        self.total_tests += 1
        if all(result.get('success', False) for result in results.values()):
            self.passed_tests += 1
            
        return results

    def test_charts_pivot_with_confidentiality(self):
        """Test endpoint /charts/pivot con sistema de confidencialidad"""
        self.log("🔄 Testing /charts/pivot with confidentiality...", "charts_pivot")
        
        test_cases = [
            {
                "name": "GESTOR - Cambio permitido",
                "payload": {
                    "userid": "gestor-1001-test",
                    "message": "cambia a barras horizontales",
                    "current_chart_config": {
                        "chart_type": "bar",
                        "dimension": "periodo",
                        "metric": "CONTRATOS"
                    },
                    "chart_interaction_type": "pivot",
                    "user_role": "GESTOR",
                    "gestor_id": "1001"
                }
            },
            {
                "name": "GESTOR - Intento acceso datos confidenciales",
                "payload": {
                    "userid": "gestor-1001-test",
                    "message": "muestra precios reales por producto",
                    "current_chart_config": {
                        "chart_type": "bar",
                        "dimension": "producto",
                        "metric": "PRECIO_STD"
                    },
                    "chart_interaction_type": "pivot",
                    "user_role": "GESTOR",
                    "gestor_id": "1001"
                }
            },
            {
                "name": "CONTROL_GESTION - Acceso completo",
                "payload": {
                    "userid": "admin-control-test",
                    "message": "cambia a precios reales por gestor",
                    "current_chart_config": {
                        "chart_type": "bar",
                        "dimension": "gestor",
                        "metric": "PRECIO_STD"
                    },
                    "chart_interaction_type": "pivot",
                    "user_role": "CONTROL_GESTION"
                }
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                response = requests.post(f"{self.base_url}/charts/pivot", json=test_case["payload"], timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    status = data.get('status', 'unknown')
                    changes = len(data.get('changes_made', []))
                    confidentiality_applied = data.get('confidentiality_applied', False)
                    
                    results[test_case["name"]] = {
                        'status': status,
                        'changes': changes,
                        'confidentiality': confidentiality_applied,
                        'success': True
                    }
                    
                    self.log(f"✅ {test_case['name']}: {status}, {changes} cambios, Confidencialidad: {'✅' if confidentiality_applied else '❌'}")
                else:
                    self.log(f"❌ {test_case['name']}: HTTP {response.status_code}")
                    results[test_case["name"]] = {'error': response.status_code, 'success': False}
                    
            except Exception as e:
                self.log(f"❌ Error en {test_case['name']}: {e}")
                results[test_case["name"]] = {'error': str(e), 'success': False}
        
        self.total_tests += 1
        if all(result.get('success', False) for result in results.values()):
            self.passed_tests += 1
            
        return results

    def test_charts_validate_config(self):
        """Test endpoint /charts/validate-config"""
        self.log("🔍 Testing /charts/validate-config...", "charts_validate")
        
        test_cases = [
            {
                "name": "GESTOR - Config válida",
                "payload": {
                    "config": {
                        "chart_type": "bar",
                        "dimension": "periodo",
                        "metric": "CONTRATOS"
                    },
                    "user_role": "GESTOR",
                    "user_context": {"gestor_id": "1001"}
                }
            },
            {
                "name": "GESTOR - Config requiere ajuste",
                "payload": {
                    "config": {
                        "chart_type": "bar",
                        "dimension": "gestor",
                        "metric": "PRECIO_REAL"
                    },
                    "user_role": "GESTOR",
                    "user_context": {"gestor_id": "1001"}
                }
            },
            {
                "name": "CONTROL_GESTION - Config completa",
                "payload": {
                    "config": {
                        "chart_type": "bar",
                        "dimension": "gestor",
                        "metric": "PRECIO_REAL"
                    },
                    "user_role": "CONTROL_GESTION"
                }
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                response = requests.post(f"{self.base_url}/charts/validate-config", json=test_case["payload"], timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    adjustments = len(data.get('adjustments_made', []))
                    validation_status = data.get('validation_status', 'unknown')
                    
                    results[test_case["name"]] = {
                        'adjustments': adjustments,
                        'status': validation_status,
                        'success': True
                    }
                    
                    self.log(f"✅ {test_case['name']}: {validation_status}, {adjustments} ajustes")
                else:
                    self.log(f"❌ {test_case['name']}: HTTP {response.status_code}")
                    results[test_case["name"]] = {'error': response.status_code, 'success': False}
                    
            except Exception as e:
                self.log(f"❌ Error en {test_case['name']}: {e}")
                results[test_case["name"]] = {'error': str(e), 'success': False}
        
        self.total_tests += 1
        if all(result.get('success', False) for result in results.values()):
            self.passed_tests += 1
            
        return results

    def test_charts_create_secure(self):
        """Test endpoint /charts/create-secure"""
        self.log("🔐 Testing /charts/create-secure...", "charts_create")
        
        test_cases = [
            {
                "name": "GESTOR - Gráfico personal",
                "payload": {
                    "data": [
                        {"label": "Enero", "value": 100},
                        {"label": "Febrero", "value": 120},
                        {"label": "Marzo", "value": 95}
                    ],
                    "config": {
                        "chart_type": "line",
                        "dimension": "periodo",
                        "metric": "CONTRATOS"
                    },
                    "user_role": "GESTOR",
                    "gestor_id": "1001"
                }
            },
            {
                "name": "CONTROL_GESTION - Gráfico comparativo",
                "payload": {
                    "data": [
                        {"label": "Gestor A", "value": 150},
                        {"label": "Gestor B", "value": 120},
                        {"label": "Gestor C", "value": 180}
                    ],
                    "config": {
                        "chart_type": "bar",
                        "dimension": "gestor",
                        "metric": "MARGEN_NETO"
                    },
                    "user_role": "CONTROL_GESTION"
                }
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                response = requests.post(f"{self.base_url}/charts/create-secure", json=test_case["payload"], timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    chart = data.get('chart', {})
                    chart_id = chart.get('id', 'N/A')
                    chart_type = chart.get('type', 'unknown')
                    confidentiality_applied = chart.get('confidentiality_applied', False)
                    
                    results[test_case["name"]] = {
                        'chart_id': chart_id,
                        'chart_type': chart_type,
                        'confidentiality': confidentiality_applied,
                        'success': chart_type != 'error'
                    }
                    
                    self.log(f"✅ {test_case['name']}: ID={chart_id}, Tipo={chart_type}, Confidencialidad={'✅' if confidentiality_applied else '❌'}")
                else:
                    self.log(f"❌ {test_case['name']}: HTTP {response.status_code}")
                    results[test_case["name"]] = {'error': response.status_code, 'success': False}
                    
            except Exception as e:
                self.log(f"❌ Error en {test_case['name']}: {e}")
                results[test_case["name"]] = {'error': str(e), 'success': False}
        
        self.total_tests += 1
        if all(result.get('success', False) for result in results.values()):
            self.passed_tests += 1
            
        return results

    def test_integration_classify_and_route(self):
        """Test endpoint /integration/classify-and-route"""
        self.log("🔀 Testing /integration/classify-and-route...", "integration")
        
        test_cases = [
            {
                "name": "Consulta con gráficos",
                "payload": {
                    "userid": "gestor-1001-test",
                    "message": "muéstrame mi evolución de ROE en gráfico de líneas",
                    "gestor_id": "1001",
                    "include_charts": True
                }
            },
            {
                "name": "Consulta sin gráficos",
                "payload": {
                    "userid": "admin-test",
                    "message": "¿cuál es el estado general del negocio?",
                    "include_charts": False
                }
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                response = requests.post(f"{self.base_url}/integration/classify-and-route", json=test_case["payload"], timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    classification = data.get('classification', {})
                    has_charts = bool(data.get('charts', []))
                    
                    results[test_case["name"]] = {
                        'classification': classification.get('category', 'unknown'),
                        'has_charts': has_charts,
                        'success': True
                    }
                    
                    self.log(f"✅ {test_case['name']}: {classification.get('category', 'N/A')}, Gráficos: {'✅' if has_charts else '❌'}")
                else:
                    self.log(f"❌ {test_case['name']}: HTTP {response.status_code}")
                    results[test_case["name"]] = {'error': response.status_code, 'success': False}
                    
            except Exception as e:
                self.log(f"❌ Error en {test_case['name']}: {e}")
                results[test_case["name"]] = {'error': str(e), 'success': False}
        
        self.total_tests += 1
        if all(result.get('success', False) for result in results.values()):
            self.passed_tests += 1
            
        return results

    def run_all_tests(self):
        """Ejecutar todos los tests"""
        self.log("🚀 Iniciando tests completos de Chart Endpoints V4.4")
        self.log("=" * 80)
        
        start_time = time.time()
        
        # Tests secuenciales
        if not self.test_health_check():
            self.log("❌ Servidor no disponible - cancelando tests")
            return False
            
        self.test_chart_generator_validation()
        self.test_charts_meta_by_role()
        self.test_charts_options_by_role()
        self.test_charts_pivot_with_confidentiality()
        self.test_charts_validate_config()
        self.test_charts_create_secure()
        self.test_integration_classify_and_route()
        
        # Resumen final
        end_time = time.time()
        duration = end_time - start_time
        
        self.log("=" * 80)
        self.log(f"🎯 RESUMEN DE TESTS:")
        self.log(f"   ✅ Tests ejecutados: {self.total_tests}")
        self.log(f"   ✅ Tests exitosos: {self.passed_tests}")
        self.log(f"   ❌ Tests fallidos: {self.total_tests - self.passed_tests}")
        self.log(f"   ⏱️ Tiempo total: {duration:.2f}s")
        self.log(f"   📊 Tasa de éxito: {(self.passed_tests/max(self.total_tests,1)*100):.1f}%")
        
        if self.passed_tests == self.total_tests:
            self.log("🎉 ¡TODOS LOS TESTS PASARON! Chart Generator V4.4 funcionando correctamente")
            return True
        else:
            self.log("⚠️ Algunos tests fallaron - revisar logs anteriores")
            return False

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    print(f"📊 Chart Endpoints V4.4 Tester")
    print(f"🌐 URL Base: {base_url}")
    print(f"⏰ Timeout: {TIMEOUT}s")
    print()
    
    tester = ChartEndpointTester(base_url)
    success = tester.run_all_tests()
    
    # Guardar resultados
    results_file = f"backend/scripts/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(tester.results, f, indent=2, ensure_ascii=False)
        print(f"📝 Resultados guardados en: {results_file}")
    except Exception as e:
        print(f"⚠️ No se pudieron guardar los resultados: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
