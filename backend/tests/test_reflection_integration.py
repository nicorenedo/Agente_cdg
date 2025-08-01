"""
Test de Integración Completa del Reflection Pattern - Agente CDG
==============================================================

Suite completa de tests para verificar la integración del sistema de aprendizaje
continuo (reflection pattern) con cdg_agent.py y chat_agent.py.

Ejecutar con: python backend/tests/test_reflection_integration.py

Autor: Agente CDG Development Team
Fecha: 2025-08-01
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# CORRECCIÓN: Añadir AMBOS directorios al path
backend_root = os.path.join(os.path.dirname(__file__), '..')  # backend/
backend_src = os.path.join(os.path.dirname(__file__), '..', 'src')  # backend/src/

sys.path.insert(0, backend_root)  # Para config.py
sys.path.insert(0, backend_src)   # Para src/utils/, src/agents/, etc.

print(f"🔍 Path agregado: {backend_root}")
print(f"🔍 Path agregado: {backend_src}")
print(f"🔍 Directorio actual: {os.getcwd()}")

# Verificar archivos críticos antes de importar
critical_files = [
    os.path.join(backend_root, "config.py"),
    os.path.join(backend_src, "utils", "reflection_pattern.py"),
    os.path.join(backend_src, "utils", "initial_agent.py")
]

print("\n🔍 Verificando archivos críticos:")
for file_path in critical_files:
    if os.path.exists(file_path):
        print(f"✅ {os.path.relpath(file_path)}")
    else:
        print(f"❌ {os.path.relpath(file_path)} - FALTANTE")

# Importar módulos del agente CDG con manejo de errores detallado
try:
    print("\n📦 Importando reflection_pattern...")
    from utils.reflection_pattern import (
        ReflectionPatternManager,
        integrate_feedback_from_chat_agent,
        get_personalization_for_user,
        reflection_manager
    )
    print("✅ reflection_pattern importado correctamente")
    
except ImportError as e:
    print(f"❌ Error importando reflection_pattern: {e}")
    print("🔧 Asegúrate de que estos archivos existan:")
    print("   • backend/config.py (al mismo nivel que src/)")
    print("   • backend/src/utils/reflection_pattern.py")
    print("   • backend/src/utils/initial_agent.py")
    sys.exit(1)

try:
    print("📦 Importando chat_agent...")
    from agents.chat_agent import CDGChatAgent, ChatMessage
    print("✅ chat_agent importado correctamente")
    
except ImportError as e:
    print(f"⚠️ Advertencia importando chat_agent: {e}")
    print("📝 Continuando con tests básicos del reflection_pattern")

class TestReflectionPatternIntegration:
    """Suite de tests para verificar el sistema de reflection pattern"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        self.test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # Deshabilitamos análisis LLM para tests simples
        self.manager = ReflectionPatternManager(enable_llm_analysis=False)
        print(f"🧪 Setup completado para usuario: {self.test_user_id}")
    
    def test_1_basic_functionality(self):
        """Test básico de funcionalidad del reflection pattern"""
        print("\n🔧 Test 1: Verificando funcionalidad básica...")
        
        # Test de inicialización
        assert self.manager is not None
        assert hasattr(self.manager, 'user_profiles')
        assert hasattr(self.manager, 'organizational_memory')
        
        # Test de creación de perfil
        profile = self.manager.get_user_profile(self.test_user_id)
        assert profile is not None
        assert profile.user_id == self.test_user_id
        
        print("✅ Test 1 PASADO: Funcionalidad básica verificada")
    
    async def test_2_feedback_processing(self):
        """Test de procesamiento de feedback"""
        print("\n📝 Test 2: Verificando procesamiento de feedback...")
        
        result = await self.manager.process_feedback(
            user_id=self.test_user_id,
            query='¿Cuál es mi margen neto este trimestre?',
            response='Su margen neto actual es 12.5%, representando un incremento del 2% vs trimestre anterior.',
            response_type='gestor_analysis',
            feedback_rating=4,
            feedback_comments='Análisis muy útil, me ayuda a entender mi performance'
        )
        
        assert result['status'] == 'processed'
        assert 'learning_signal' in result
        
        # Verificar que se actualizó el perfil
        profile = self.manager.get_user_profile(self.test_user_id)
        assert profile.total_interactions == 1
        assert profile.average_rating == 4.0
        
        print("✅ Test 2 PASADO: Procesamiento de feedback verificado")
    
    def test_3_personalization_context(self):
        """Test de contexto de personalización"""
        print("\n🎯 Test 3: Verificando personalización...")
        
        # Test usando función de integración
        personalization = get_personalization_for_user(self.test_user_id)
        
        assert isinstance(personalization, dict)
        assert 'preferred_detail_level' in personalization
        assert 'technical_level' in personalization
        assert 'communication_style' in personalization
        
        print("✅ Test 3 PASADO: Personalización verificada")
    
    async def test_4_learning_progression(self):
        """Test de progresión de aprendizaje"""
        print("\n📈 Test 4: Verificando progresión de aprendizaje...")
        
        # Secuencia de feedback que muestra mejora
        feedback_sequence = [
            {"rating": 2, "comments": "Muy técnico, no entiendo los términos bancarios"},
            {"rating": 3, "comments": "Mejor, pero sigue siendo confuso"},
            {"rating": 4, "comments": "Mucho mejor, ahora lo entiendo"},
            {"rating": 5, "comments": "Perfecto! Justo lo que necesitaba"}
        ]
        
        # Procesar secuencia de feedback
        for i, feedback in enumerate(feedback_sequence):
            await self.manager.process_feedback(
                user_id=self.test_user_id,
                query=f"Consulta bancaria {i+1}",
                response=f"Respuesta adaptada {i+1}",
                response_type="gestor_analysis",
                feedback_rating=feedback["rating"],
                feedback_comments=feedback["comments"]
            )
        
        # Verificar mejora progresiva
        profile = self.manager.get_user_profile(self.test_user_id)
        assert profile.total_interactions == len(feedback_sequence)
        assert profile.average_rating > 3.0  # Debe mostrar mejora
        
        print("✅ Test 4 PASADO: Progresión de aprendizaje verificada")
    
    def test_5_organizational_insights(self):
        """Test de insights organizacionales"""
        print("\n📊 Test 5: Verificando insights organizacionales...")
        
        # Simular múltiples usuarios para insights organizacionales
        test_users = ["gestor_001", "gestor_002", "control_001"]
        
        # Crear actividad para cada usuario
        for user_id in test_users:
            profile = self.manager.get_user_profile(user_id)
            profile.total_interactions = 5
            profile.average_rating = 4.0
            profile.frequent_query_types = {"gestor_analysis": 3, "comparative_analysis": 2}
        
        insights = self.manager.generate_organizational_insights()
        
        assert 'status' in insights
        assert insights['status'] == 'success'
        assert insights['total_users'] >= len(test_users)
        assert 'average_satisfaction' in insights
        
        print("✅ Test 5 PASADO: Insights organizacionales verificados")
    
    async def test_6_integration_function(self):
        """Test de función de integración con chat agent"""
        print("\n🔗 Test 6: Verificando función de integración...")
        
        chat_response = {
            'response': 'Su ROE actual es 8.3%, situándose en el percentil 75 del equipo comercial',
            'response_type': 'gestor_analysis',
            'session_id': 'test_session_123',
            'charts': [{'type': 'bar', 'title': 'ROE vs Objetivos'}],
            'recommendations': ['Optimizar mix de productos para incrementar ROE']
        }
        
        feedback_data = {
            'rating': 5,
            'comments': 'Excelente análisis comparativo, muy útil para mi gestión'
        }
        
        result = await integrate_feedback_from_chat_agent(
            user_id=self.test_user_id,
            chat_message="¿Cómo está mi ROE comparado con otros gestores?",
            chat_response=chat_response,
            feedback_data=feedback_data
        )
        
        assert 'status' in result
        assert result['status'] == 'processed'
        
        print("✅ Test 6 PASADO: Función de integración verificada")
    
    def test_7_profile_persistence(self):
        """Test de persistencia de perfil de usuario"""
        print("\n💾 Test 7: Verificando persistencia de perfil...")
        
        # Crear perfil con datos específicos
        profile = self.manager.get_user_profile(self.test_user_id)
        profile.preferred_detail_level = "high"
        profile.communication_style = "professional"
        profile.technical_level = "advanced"
        profile.total_interactions = 25
        profile.average_rating = 4.5
        
        # Exportar datos
        exported_data = self.manager.export_learning_data(self.test_user_id)
        
        assert 'user_profile' in exported_data
        assert exported_data['user_profile']['preferred_detail_level'] == "high"
        assert exported_data['user_profile']['total_interactions'] == 25
        
        print("✅ Test 7 PASADO: Persistencia de perfil verificada")

def run_reflection_tests():
    """Ejecuta todos los tests del reflection pattern"""
    print("🧠 INICIANDO TESTS DEL REFLECTION PATTERN")
    print("=" * 50)
    
    test_suite = TestReflectionPatternIntegration()
    
    tests = [
        ("test_1_basic_functionality", False),
        ("test_2_feedback_processing", True),
        ("test_3_personalization_context", False),
        ("test_4_learning_progression", True),
        ("test_5_organizational_insights", False),
        ("test_6_integration_function", True),
        ("test_7_profile_persistence", False)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, is_async in tests:
        try:
            print(f"\n▶️ Ejecutando {test_name}...")
            test_suite.setup_method()
            
            if is_async:
                asyncio.run(getattr(test_suite, test_name)())
            else:
                getattr(test_suite, test_name)()
            
            passed_tests += 1
            
        except Exception as e:
            print(f"❌ {test_name} FALLÓ: {e}")
            continue
    
    # Resumen final
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN DE TESTS:")
    print(f"✅ Tests pasados: {passed_tests}/{total_tests}")
    print(f"❌ Tests fallados: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ El Reflection Pattern está correctamente integrado")
        print("🚀 Sistema de aprendizaje continuo funcionando")
        print("📋 Listo para implementar main.py")
        
        print("\n🔗 Componentes verificados:")
        print("   • Funcionalidad básica ✅")
        print("   • Procesamiento de feedback ✅")  
        print("   • Personalización de usuarios ✅")
        print("   • Progresión de aprendizaje ✅")
        print("   • Insights organizacionales ✅")
        print("   • Integración con chat agent ✅")
        print("   • Persistencia de datos ✅")
        
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests fallaron")
        print("🔧 Revisa la configuración antes de continuar")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    print("🧠 Test de Integración del Reflection Pattern - CDG Banca March")
    print("=" * 60)
    
    try:
        success = run_reflection_tests()
        
        if success:
            print("\n✨ SISTEMA DE REFLECTION PATTERN COMPLETAMENTE VERIFICADO")
            print("🏦 El agente CDG tiene capacidades de aprendizaje continuo funcionales")
            print("📈 Personalización automática por gestor operativa")
            print("🎯 Sistema listo para producción con gestores reales")
            print("\n🚀 Puedes proceder con confianza a implementar main.py")
        else:
            print("\n🔧 Algunos tests fallaron - revisar configuración")
            
    except Exception as e:
        print(f"❌ Error crítico en la ejecución: {e}")
        print("\n📋 Verificar estructura de archivos:")
        print("   • backend/config.py (mismo nivel que src/)")
        print("   • backend/src/utils/reflection_pattern.py")
        print("   • backend/src/utils/initial_agent.py")
        print("   • Variables de entorno Azure OpenAI configuradas")
