# Frontend para Template POC

Este es el componente frontend del proyecto Template POC. Está construido utilizando [Streamlit](https://streamlit.io/) para proporcionar una interfaz de usuario que interactúe con un agente de IA (`ReactAgent`). A continuación, se ofrece una guía detallada para ayudar a nuevos desarrolladores a entender y trabajar con este proyecto.

---

## Tabla de Contenidos
1. [Descripción General del Proyecto](#descripción-general-del-proyecto)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Cómo Funciona](#cómo-funciona)
4. [Instrucciones de Configuración](#instrucciones-de-configuración)
5. [Componentes Clave](#componentes-clave)
6. [Guía de Personalización](#guía-de-personalización)
7. [Resolución de Problemas](#resolución-de-problemas)

---

## Descripción General del Proyecto

El frontend permite a los usuarios:
- Introducir una consulta para interactuar con el agente de IA.
- Opcionalmente, subir un archivo (por ejemplo, `.txt`, `.csv`, `.json`) para procesamiento adicional.
- Ver la respuesta del agente directamente en la interfaz de usuario.

La lógica del backend es manejada por el `ReactAgent`, que utiliza herramientas predefinidas para procesar las entradas del usuario.

---

## Estructura de Archivos

```
frontend/
├── src/
│   ├── app.py          # Aplicación principal de Streamlit
│   └── ...             # Otros archivos relacionados con el frontend
└── README.md           # Documentación del frontend
```

---

## Cómo Funciona

1. **Entrada del Usuario**:
   - Los usuarios pueden introducir una consulta en el cuadro de texto.
   - Opcionalmente, los usuarios pueden subir un archivo para su procesamiento.

2. **Interacción con el Agente**:
   - El `ReactAgent` procesa la consulta y/o el contenido del archivo utilizando herramientas predefinidas (`sum_two_elements`, `multiply_two_elements`, `compute_log`).

3. **Visualización de Respuestas**:
   - La respuesta del agente se muestra en la interfaz de Streamlit.

4. **Gestión de Errores**:
   - Los errores durante el procesamiento se capturan y se muestran como mensajes de error.

---

## Instrucciones de Configuración

### Requisitos Previos
- Python 3.8 o superior
- Poetry instalado (sigue las [instrucciones de instalación de Poetry](https://python-poetry.org/docs/#installation))

### Pasos
1. Instalar las dependencias con Poetry desde la raíz del proyecto:
   ```bash
   poetry install
   ```

2. Activar el entorno virtual:
   ```bash
   poetry shell
   ```

3. Ejecutar la aplicación desde frontend/src:
   ```bash
   cd frontend/src
   streamlit run app.py
   ```

4. Abrir la aplicación en el navegador en `http://localhost:8501`.

### Añadir Nuevas Dependencias
Si necesitas añadir nuevas bibliotecas al proyecto:
```bash
# Añadir una librería básica
poetry add pandas

# Añadir una librería con una versión específica 
poetry add numpy==1.22.0
```

---

## Componentes Clave

### `app.py`
- **Propósito**: Punto de entrada principal para la aplicación de Streamlit.
- **Características Clave**:
  - Entrada de consulta del usuario
  - Funcionalidad de subida de archivos
  - Interacción con el `ReactAgent`

### `ReactAgent`
- **Propósito**: Procesa las entradas del usuario utilizando herramientas predefinidas.
- **Herramientas**:
  - `sum_two_elements`: Suma dos números.
  - `multiply_two_elements`: Multiplica dos números.
  - `compute_log`: Calcula el logaritmo de un número.

---

## Guía de Personalización

### Añadir Nuevas Herramientas
1. Define la nueva herramienta en el módulo `defined_tools`.
2. Importa la herramienta en `app.py`.
3. Añade la herramienta a la inicialización de `ReactAgent`:
   ```python
   agent = ReactAgent(tools=[existing_tool, new_tool])
   ```

### Modificar la Interfaz de Usuario
- Actualiza los elementos de la interfaz de Streamlit en `app.py`:
  - Cambia títulos, descripciones o campos de entrada según sea necesario.

### Soportar Tipos de Archivo Adicionales
- Actualiza el parámetro `type` en la función `st.file_uploader`:
  ```python
  uploaded_file = st.file_uploader("Sube un archivo:", type=["txt", "csv", "json", "xml"])
  ```

---

## Resolución de Problemas

### Problemas Comunes
1. **Módulo No Encontrado**:
   - Asegúrate de que el directorio del backend esté correctamente añadido al path de Python en `app.py`.

2. **Errores al Subir Archivos**:
   - Verifica que el archivo subido esté en un formato soportado.

3. **Errores del Agente**:
   - Revisa la implementación del `ReactAgent` y sus herramientas.

### Consejos para Depuración
- Usa `st.write` o declaraciones `print` para depurar problemas en `app.py`.
- Revisa los logs de Streamlit en la terminal para obtener detalles de los errores.

---

## Recursos Adicionales
- [Documentación de Streamlit](https://docs.streamlit.io/)
- [Documentación de Pathlib de Python](https://docs.python.org/3/library/pathlib.html)
- [Documentación del Backend del Proyecto](../backend/README.md) (si está disponible)

---
