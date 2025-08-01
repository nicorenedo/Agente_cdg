# backend/src/utils/initial_agent.py
import logging
from openai import AzureOpenAI, OpenAIError
from openai.types.chat.chat_completion import ChatCompletion
from typing import Any, List, Dict, Optional

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    client = AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )
    deployment_id = settings.AZURE_OPENAI_DEPLOYMENT_ID
    logger.info(f"🔄 AzureOpenAI client inicializado. deployment_id={deployment_id}")
except Exception as e:
    logger.error(f"❌ Error al inicializar AzureOpenAI client: {e}")
    raise

def iniciar_agente_llm(
    system_prompt: Optional[str] = None,  # ✅ CORRECCIÓN: Hacer opcional con default
    user_prompt: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.0,
    max_tokens: int = 2000
) -> Any:  # ✅ CORRECCIÓN: Cambiar tipo de retorno para flexibilidad
    """
    Invoca a Azure OpenAI ChatCompletion con tu deployment.
    
    Args:
        system_prompt: Prompt del sistema (opcional, con default)
        user_prompt: Prompt del usuario (opcional)
        tools: Herramientas disponibles (opcional)
        temperature: Temperatura para la generación
        max_tokens: Máximo número de tokens
        
    Returns:
        ChatCompletion response o AzureOpenAI client según parámetros
    """
    
    # ✅ NUEVA FUNCIONALIDAD: Si no se proporciona system_prompt, retornar client
    if system_prompt is None and user_prompt is None:
        logger.info("🔄 Retornando AzureOpenAI client para uso directo")
        return client
    
    # ✅ DEFAULT SYSTEM PROMPT si no se proporciona
    if system_prompt is None:
        system_prompt = "Eres un asistente especializado en análisis financiero bancario para Banca March."
        logger.info("🔄 Usando system prompt por defecto")
    
    messages = [{"role": "system", "content": system_prompt}]
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    try:
        # Parámetros básicos
        params = {
            "model": deployment_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Agregar tools solo si se proporcionan
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        resp = client.chat.completions.create(**params)
        logger.info(f"✅ Llamada exitosa a Azure OpenAI con {len(messages)} mensajes")
        return resp
        
    except OpenAIError as e:
        logger.error(f"❌ Error al llamar al LLM: {e}")
        raise RuntimeError(f"Error al llamar al LLM: {e}")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        raise RuntimeError(f"Error inesperado en iniciar_agente_llm: {e}")

# ✅ NUEVA FUNCIÓN: Para casos donde se necesita solo el client
def get_azure_openai_client() -> AzureOpenAI:
    """
    Retorna el cliente AzureOpenAI configurado
    
    Returns:
        AzureOpenAI client configurado
    """
    return client

# ✅ NUEVA FUNCIÓN: Para compatibilidad con llamadas rápidas
def quick_llm_call(user_message: str, system_context: str = None) -> str:
    """
    Función de conveniencia para llamadas rápidas al LLM
    
    Args:
        user_message: Mensaje del usuario
        system_context: Contexto del sistema (opcional)
        
    Returns:
        Respuesta del LLM como string
    """
    try:
        default_system = system_context or "Eres un asistente especializado en análisis financiero bancario."
        
        response = iniciar_agente_llm(
            system_prompt=default_system,
            user_prompt=user_message,
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"❌ Error en quick_llm_call: {e}")
        return f"Error procesando solicitud: {str(e)}"

# ✅ NUEVA FUNCIÓN: Para validar configuración
def validate_azure_config() -> Dict[str, Any]:
    """
    Valida la configuración de Azure OpenAI
    
    Returns:
        Dict con estado de la configuración
    """
    try:
        # Test simple de conectividad
        test_response = client.chat.completions.create(
            model=deployment_id,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=10
        )
        
        return {
            "status": "connected",
            "deployment_id": deployment_id,
            "endpoint": settings.AZURE_OPENAI_ENDPOINT,
            "api_version": settings.AZURE_OPENAI_API_VERSION,
            "test_successful": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "deployment_id": deployment_id,
            "test_successful": False
        }

if __name__ == "__main__":
    # Test de funcionalidad
    print("🧪 Testing initial_agent.py...")
    
    # Test 1: Validar configuración
    config_status = validate_azure_config()
    print(f"✅ Configuración Azure OpenAI: {config_status['status']}")
    
    # Test 2: Llamada con system_prompt
    try:
        response = iniciar_agente_llm(
            system_prompt="Eres un asistente financiero",
            user_prompt="¿Qué es el ROE?"
        )
        print("✅ Llamada con system_prompt: OK")
    except Exception as e:
        print(f"❌ Error con system_prompt: {e}")
    
    # Test 3: Llamada sin parámetros (retorna client)
    try:
        client_instance = iniciar_agente_llm()
        print("✅ Llamada sin parámetros: OK")
    except Exception as e:
        print(f"❌ Error sin parámetros: {e}")
    
    # Test 4: Quick call
    try:
        quick_response = quick_llm_call("Test message")
        print("✅ Quick call: OK")
    except Exception as e:
        print(f"❌ Error quick call: {e}")
    
    print("🎯 Testing completed!")
