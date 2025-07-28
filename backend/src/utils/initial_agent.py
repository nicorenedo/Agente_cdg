# backend/src/initial_agent.py (versión actualizada)
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
    system_prompt: str,
    user_prompt: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,  # Cambiado de functions a tools
    temperature: float = 0.0,
    max_tokens: int = 2000
) -> ChatCompletion:
    """
    Invoca a Azure OpenAI ChatCompletion con tu deployment.
    """
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
        return resp
        
    except OpenAIError as e:
        logger.error(f"❌ Error al llamar al LLM: {e}")
        raise RuntimeError(f"Error al llamar al LLM: {e}")
