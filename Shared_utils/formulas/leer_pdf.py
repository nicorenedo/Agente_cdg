import pdfplumber
import json
import re
from openai import AzureOpenAI

def leer_pdf(ruta_pdf: str, ruta_json: str, client: AzureOpenAI, deployment_id: str, system_prompt: str) -> str:
    """
    Lee el contenido completo de un archivo PDF y lo analiza con Azure OpenAI para extraer información estructurada.

    Parámetros:
        ruta_pdf (str): Ruta al archivo PDF de entrada.
        ruta_json (str): Ruta donde se guardará el JSON de salida.
        client (AzureOpenAI): Cliente autenticado de Azure OpenAI.
        deployment_id (str): ID del modelo desplegado en Azure.
        system_prompt (str): Prompt con instrucciones específicas para el modelo.

    Retorna:
        str: Contenido generado por el modelo, en formato JSON como string.

    ---------------------------------------------------------------------------
    🔍 IMPORTANTE - SOBRE EL SYSTEM PROMPT

    El parámetro `system_prompt` es el núcleo de esta función. Es el mensaje que define el rol, contexto y
    comportamiento del modelo de lenguaje. Debe ser muy específico según tu dominio. 

    ---------------------------------------------------------------------------
    """
    #Cambia el prompt según tu caso de uso
    # 1. Leer texto completo del PDF
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    # 2. Preparar prompt de usuario
    user_prompt = f"""Este es el texto completo del documento:

---
{texto}
---
"""

    # 3. Llamar al LLM
    response = client.chat.completions.create(
        model=deployment_id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    # 4. Interpretar y limpiar la respuesta
    content_raw = response.choices[0].message.content.strip()
    content_clean = re.sub(r"```(?:json)?", "", content_raw).strip()

    print("📥 Respuesta del LLM (limpia):\n", content_clean)

    try:
        datos = json.loads(content_clean)
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        print(f"✅ Datos extraídos y guardados en: {ruta_json}")
    except json.JSONDecodeError as e:
        print("⚠️ Error al interpretar JSON:", e)
        print("🔎 Respuesta cruda recibida:\n", content_raw)

    return content_clean
