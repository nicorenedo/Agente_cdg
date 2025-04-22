# Backend para la POC de Plantilla

Este es el componente backend del template POC. Contiene la implementación del `ReactAgent`, que sigue un patrón de planificación para procesar consultas de usuario y, opcionalmente, archivos subidos. A continuación, se ofrece una guía detallada para ayudar a los nuevos desarrolladores a entender y trabajar con este proyecto.

---

## Tabla de Contenidos
1. [Resumen](#resumen)
2. [Cómo funciona el agente con patrón de planificación](#cómo-funciona-el-agente-con-patrón-de-planificación)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Instrucciones de Configuración](#instrucciones-de-configuración)
5. [Componentes Clave](#componentes-clave)
6. [Guía de Personalización](#guía-de-personalización)
7. [Resolución de Problemas](#resolución-de-problemas)

---

## Resumen

El backend es responsable de:
- Implementar el `ReactAgent`, que procesa las entradas del usuario utilizando un patrón de planificación.
- Definir herramientas que el agente puede usar para realizar tareas específicas (por ejemplo, operaciones matemáticas, procesamiento de archivos).

El backend está diseñado para ser modular, permitiendo a los desarrolladores añadir nuevas herramientas o modificar el comportamiento del agente fácilmente.

---

## Cómo funciona el agente con patrón de planificación

El `ReactAgent` sigue un patrón de planificación, que implica:
1. **Inicialización de Herramientas**:
   - El agente se inicializa con una lista de herramientas, cada una de las cuales realiza una tarea específica.
2. **Procesamiento de Entrada**:
   - El agente recibe una consulta del usuario y, opcionalmente, el contenido de un archivo.
3. **Selección de Herramientas**:
   - Basándose en la entrada, el agente selecciona la(s) herramienta(s) adecuada(s) para procesar la consulta.
4. **Ejecución**:
   - Se ejecutan las herramientas seleccionadas y sus resultados se combinan para generar una respuesta.
5. **Generación de Respuesta**:
   - El agente devuelve la respuesta final al frontend.

---

## Estructura de Archivos

```
backend/
├── src/
│   ├── agentic_patterns_azure/
│   │   ├── planning_pattern/
│   │   │   └── react_agent.py   # Implementación del ReactAgent
│   │   └── ...                  # Otros módulos de patrones agentic
│   ├── defined_tools.py         # Herramientas utilizadas por el ReactAgent
│   ├── planning_pattern.ipynb   # Notebook para personalizar el agente
│   ├── .env                     # Archivo donde introducir tu AZURE_OPENAI_API_KEY
│   └── ...                      # Otros archivos relacionados con el backend
└── README.md                    # Documentación del backend
```

---

## Instrucciones de Configuración

### Requisitos Previos
- Python 3.8 o superior

### Pasos
1. Navega al directorio del backend:
   ```bash
   cd template_POC/backend
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Asegúrate de que el backend esté correctamente referenciado en el frontend:
   - El directorio del backend debe añadirse a la ruta de Python en el archivo `app.py` del frontend.

4. Para realizar pruebas, ejecuta el notebook `planning_pattern.ipynb` y sigue los pasos que se indican en él. Este notebook contiene ejemplos prácticos y guías para validar el funcionamiento del agente y sus herramientas.

---

## Componentes Clave

### `react_agent.py`
- **Propósito**: Implementa la clase `ReactAgent`, que procesa las entradas del usuario utilizando un patrón de planificación.
- **Métodos Clave**:
  - `__init__`: Inicializa el agente con una lista de herramientas.
  - `run`: Procesa la consulta del usuario y, opcionalmente, el contenido de un archivo, seleccionando y ejecutando las herramientas adecuadas.

### `defined_tools.py`
- **Propósito**: Contiene las herramientas utilizadas por el `ReactAgent`.
- **Ejemplos de Herramientas**:
  - `sum_two_elements`: Suma dos números.
  - `multiply_two_elements`: Multiplica dos números.
  - `compute_log`: Calcula el logaritmo de un número.

---

## Guía de Personalización

### Añadir Nuevas Herramientas
1. Define la nueva herramienta en `defined_tools.py`:
   ```python
   def nueva_herramienta(datos_entrada):
       # Lógica de la herramienta aquí
       return resultado
   ```

2. Importa la herramienta en `react_agent.py` o donde se inicialice el agente.

3. Añade la herramienta a la inicialización del agente:
   ```python
   agente = ReactAgent(tools=[herramienta_existente, nueva_herramienta])
   ```


### Soportar Nuevos Tipos de Entrada
- Añade tools para poder leer el tipo de archivo que se necesite.

---

## Resolución de Problemas

### Problemas Comunes
1. **Herramienta No Encontrada**:
   - Asegúrate de que la herramienta esté correctamente definida e importada en `react_agent.py`.

2. **Errores del Agente**:
   - Revisa el método `run` en busca de errores lógicos o herramientas no implementadas.

3. **Problemas con el Procesamiento de Archivos**:
   - Verifica que el contenido del archivo se lea correctamente y se pase al agente.

### Consejos para Depuración
- Añade declaraciones de registro en `react_agent.py` para rastrear el flujo de ejecución del agente.
- Usa pruebas unitarias para validar el comportamiento de herramientas individuales y del agente.

---

## Recursos Adicionales
- [Documentación de Logging en Python](https://docs.python.org/3/library/logging.html)
- [Documentación de Streamlit](https://docs.streamlit.io/)
- [Documentación del Frontend del Proyecto](../frontend/README.md)

---
