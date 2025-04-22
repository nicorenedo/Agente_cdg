🚀 Guía sencilla: Primeros pasos en un nuevo repositorio Git
============================================================

## Índice
1. Descripción del repositorio

2. Ejecución del proyecto
   1. Iniciar el frontend (versión final)
   2. Modo desarrollo (usando el notebook)

3. Clonar el repositorio base
   1. Seleccionar la carpeta local
   2. Copiar y clonar el repositorio base
   3. Desvincular el repositorio original
   4. Conectar tu propio repositorio
   5. Sincronizar con el repositorio remoto
   6. Subir tu versión al repositorio

4. Uso de archivo `.env` para gestionar la API Key de Azure

---

## 1. Descripción del repositorio

Este repositorio contiene los componentes principales para la inicialización de una POC:

- **Backend**: Implementa el agente `ReactAgent` que utiliza el planning pattern para procesar consultas de usuarios y archivos opcionales.
- **Frontend**: Proporciona una interfaz de usuario basada en Streamlit para interactuar con el agente, permitiendo enviar consultas y visualizar las respuestas.


---

## 2. Ejecución del proyecto

El funcionamiento de backend <> frontend funciona con simples llamadas desde `app.py` a las funciones del backend del agente. Por eso, para la **versión final**, solo hace falta ejecutar el frontend.

### 2.1 Iniciar el frontend (versión final)
1. Navega a la carpeta del frontend:
   ```bash
   cd frontend/src
   ```

2. Inicia el frontend:
   ```bash
   streamlit run app.py
   ```

   Abre tu navegador en `http://localhost:8501` para interactuar con la aplicación.

---

### 2.2 Modo desarrollo (usando el notebook)

Si estás en modo "developer" y necesitas probar o depurar el comportamiento del agente paso a paso, utiliza el notebook `planning_pattern.ipynb` ubicado en `backend/src`.

1. Navega a la carpeta del backend:
   ```bash
   cd backend/src
   ```

2. Sigue las celdas del notebook para ejecutar y probar cada paso del agente:
   - Inicialización de herramientas.
   - Procesamiento de consultas.
   - Ejecución de herramientas y generación de respuestas.

Este enfoque te permitirá entender y modificar el comportamiento del agente de manera granular.

---

## 3. Clonar el repositorio base

### 3.1 Seleccionar la carpeta local

🗂️ Paso 1: Selecciona la carpeta local donde quieres clonar el repositorio
---------------------------------------------------------------------------

Antes de clonar nada, piensa:  
👉 **¿En qué carpeta de tu equipo quieres guardar el proyecto?**

Por ejemplo, puedes usar:

`C:\Users\tu_usuario\Documents\Proyectos\`

Abre tu terminal (PowerShell, CMD o Git Bash) y navega a esa carpeta:

`cd "C:\Users\tu_usuario\Documents\Proyectos"`

---

### 3.2 Copiar y clonar el repositorio base

🧭 Paso 2: Copia y clona el repositorio base
--------------------------------------------

Vamos a traernos una copia del repositorio _template_ a tu equipo.
Copia la URL del repositorio (desde el botón **"Clone"** en Azure DevOps) y ejecuta:

`git clone https://CFOERiskLabs@dev.azure.com/CFOERiskLabs/CFOEVRiskLabsIBERIA/_git/template_POC`

👉 Esto crea una carpeta llamada `template_POC` con todo el contenido del template.

  
Ahora le vamos a cambiar el nombre para que el nombre del repo en local sea igual al nombre del repo en remoto y así es menos confuso.

`mv template_POC RepoTest` Cambiamos el nombre

Entramos en la carpeta con el nombre modificado
`cd RepoTest`

---

### 3.3 Desvincular el repositorio original

✂️ Paso 3: Desvincula el repositorio original
---------------------------------------------

Ya no queremos seguir conectados al template original, así que lo desvinculamos:

`git remote remove origin`

---

### 3.4 Conectar tu propio repositorio

🔗 Paso 4: Conecta tu propio repositorio
----------------------------------------

Ahora sí, vinculamos el proyecto a **tu propio repositorio** (el que vas a usar realmente).
Reemplaza la URL con la de tu nuevo repositorio, por ejemplo:

`git remote add origin   
https://dev.azure.com/CFOERiskLabs/CFOEVRiskLabsIBERIA/_git/RepoTest`

---

### 3.5 Sincronizar con el repositorio remoto

🔄 Paso 5: Sincroniza con el repositorio remoto
-----------------------------------------------

Por si hay algo en el repositorio remoto (aunque esté vacío, mejor prevenir):

`git pull origin main --rebase`

---

### 3.6 Subir tu versión al repositorio

⬆️ Paso 6: Sube tu versión al repositorio
-----------------------------------------

¡Hora de subir tus archivos! 🚀

`git push origin main`

---

## 4. Uso de archivo `.env` para gestionar la API Key de Azure

### 4.1 Buena práctica en el manejo de credenciales

Para mantener la seguridad y evitar exponer credenciales sensibles en el código fuente, es recomendable almacenar las API Keys en un archivo `.env`. Este archivo debe ubicarse en la misma carpeta donde se encuentra el código y debe contener la API Key de Azure de la siguiente manera:

    AZURE_API_KEY='valor_de_la_api_key'

Es importante **no incluir este archivo en el control de versiones**. Para ello, se debe agregar `.env` al archivo `.gitignore`:

    # Archivo .gitignore
    .env

---

### 4.2 Cargando la API Key en el código

Para acceder a la API Key en el código, utilizaremos la biblioteca `dotenv`, que permite cargar las variables definidas en el archivo `.env`. A continuación, se muestra un ejemplo de cómo realizar la conexión con Azure:

    from dotenv import load_dotenv
    import os
    from azure.openai import AzureOpenAI

    # Cargar variables del archivo .env
    load_dotenv()

    # Obtener la API Key desde las variables de entorno
    AZURE_API_KEY = os.getenv("AZURE_API_KEY")

    def connect_azure():
        client = AzureOpenAI(
            azure_endpoint="https://llmcoeiberia-ada.openai.azure.com/",
            api_key=AZURE_API_KEY,
            api_version="2024-02-01"
        )
        return client

---

### 4.3 Ventajas de este enfoque

- **Seguridad**: Evita exponer credenciales en el código fuente o en repositorios de control de versiones.
- **Portabilidad**: Permite cambiar las claves sin modificar el código.
- **Escalabilidad**: Facilita la gestión de credenciales en distintos entornos (desarrollo, pruebas y producción).

Con este método, la conexión con Azure será segura y flexible, evitando riesgos de seguridad innecesarios.
