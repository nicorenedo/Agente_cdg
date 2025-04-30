# 📁 Carpeta: `formulas/`

Esta carpeta contiene funciones reutilizables diseñadas para ser **copiadas directamente** a los proyectos de los equipos.  
No se deben modificar ni probar dentro de esta plantilla.

---

## 1. Función destacada: `detectar_ruta`

### 🧩 Problema que resuelve

En proyectos colaborativos, cada miembro del equipo puede tener el repositorio clonado en una ubicación diferente de su equipo local.

Por ejemplo:

```
C:\Users\maria.gomez\Documents\GEN AI\BancaMarch_Agente_Contabilizador  
C:\Users\nicolas.renedo\Documents\GEN AI\BancaMarch_Agente_Contabilizador
```

Si se utiliza una ruta codificada de forma absoluta como esta:

```python
ruta = r"C:\Users\nicolas.renedo\Documents\GEN AI\BancaMarch_Agente_Contabilizador\data\raw\Contrato_Bono.pdf"
```

El código **solo funcionará** en el equipo de Nicolás.  
El resto del equipo obtendrá un error porque esa ruta no existe en sus sistemas.

---

### ✅ Solución: uso de rutas relativas al proyecto

La función `detectar_ruta()` permite **detectar automáticamente la raíz del proyecto**, sin importar su ubicación local.

Con esto se pueden construir rutas relativas y garantizar que el código funcione en todos los equipos, sin necesidad de ajustes manuales.

---

### 🧪 Ejemplo de uso

```python
from detectar_ruta import detectar_ruta

nombre_proyecto = "BancaMarch_Agente_Contabilizador"
ROOT_DIR = detectar_ruta(nombre_proyecto)
ruta_pdf = ROOT_DIR / "data" / "raw" / "Contrato_Bono.pdf"
```

---

## 2. Función destacada: `crear_cliente_azureopenai`

Esta función permite conectar fácilmente con Azure OpenAI utilizando variables de entorno.

Está pensada para facilitar la autenticación y reutilización del cliente `AzureOpenAI` en todos los proyectos de manera segura y consistente.

---

### 🔐 Variables requeridas en el entorno

Estas variables deben estar definidas en un archivo `.env` en tu proyecto, o en tu entorno del sistema:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_ID`
- `AZURE_OPENAI_API_VERSION`

---

### 🧪 Ejemplo de uso

```python
from crear_cliente_azureopenai import crear_cliente_azureopenai

client = crear_cliente_azureopenai()
response = client.chat.completions.create(
    model="AZURE_OPENAI_DEPLOYMENT_ID",
    messages=[{"role": "user", "content": "Hola, ¿qué puedes hacer?"}]
)
```

---

## 3. Función destacada: `leer_pdf`

Esta función permite leer el contenido completo de un archivo PDF y enviarlo a un modelo de lenguaje de Azure OpenAI para que extraiga información estructurada en formato JSON.

Es muy útil para procesar contratos, informes o cualquier documento PDF utilizando un `system_prompt` adaptado al caso de uso.

---

### 🧠 Ejemplo de `system_prompt`

```python
system_prompt = (
    "Eres un experto contable bancario. A partir del texto completo de un contrato de bono, "
    "extrae esta información en un JSON válido con los siguientes campos:\n\n"
    "- Nominal\n- TipoInteres\n- PrecioAdquisicion\n- PeriodicidadCupon\n"
    "- FechaEmision\n- FechaVencimiento\n- TipoInstrumento\n\n"
    "Ejemplo:\n"
    "{ \"Nominal\": 500000, \"TipoInteres\": 5, ... }\n\n"
    "Ahora analiza el texto siguiente y responde únicamente con un JSON válido."
)
```

---

### 🧪 Ejemplo de uso

```python
from leer_pdf import leer_pdf

leer_pdf(
    ruta_pdf="data/raw/Contrato_Bono.pdf",
    ruta_json="outputs/datos_extraidos.json",
    client=client,
    deployment_id="AZURE_OPENAI_DEPLOYMENT_ID",
    system_prompt=system_prompt
)
```

