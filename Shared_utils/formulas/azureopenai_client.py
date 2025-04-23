import os
from dotenv import load_dotenv
from openai import AzureOpenAI

def crear_cliente_azureopenai() -> AzureOpenAI:
    """
    Crea un cliente Azure OpenAI utilizando variables de entorno.

    Variables requeridas en el entorno (.env o sistema):
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT
        - AZURE_OPENAI_DEPLOYMENT_ID
        - AZURE_OPENAI_API_VERSION

    Retorna:
        AzureOpenAI: Cliente autenticado y configurado para usar OpenAI sobre Azure.
    """
    # Cargar variables de entorno desde .env 
    load_dotenv()

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    # Validar que todas las variables estén presentes
    if not all([api_key, api_base, deployment_id, api_version]):
        raise EnvironmentError("❌ Faltan variables de entorno para configurar Azure OpenAI")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=api_base
    )

    print("✅ Conexión a Azure OpenAI configurada correctamente")
    print(f"📌 Deployment en uso: {deployment_id}")
    return client
