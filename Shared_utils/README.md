# 📦 Utils

Esta carpeta actúa como una **plantilla de utilidades compartidas** para proyectos de inteligencia artificial generativa (GEN AI) desarrollados dentro de nuestra organización.  

Su objetivo es centralizar funciones comunes y reutilizables que resuelvan problemas repetitivos en diferentes proyectos y equipos.

---

## 🚫 ¿Qué NO es esta carpeta?

- No es un espacio de desarrollo ni de pruebas.
- No contiene lógica de negocio específica de ningún caso de uso.
- No se debe ejecutar ni modificar código directamente aquí.

---

## ✅ ¿Cómo se usa?

1. **Navega a la carpeta [`formulas/`](./formulas/)**.
2. **Copia** el archivo o función que necesites.
3. **Pega** esa función en tu proyecto.
4. Adáptala si es necesario para tu caso de uso.

> ⚠️ Las funciones aquí son de solo lectura y no deben modificarse dentro de esta plantilla.

---

## 📁 Estructura de la carpeta 

```
Utils/
│
├── README.md               ← Este archivo
└── formulas/               ← Funciones reutilizables
    ├── README.md           ← Documentación de cada función
    ├── detectar_ruta.py    ← Manejo de rutas relativas al proyecto
    ├── crear_cliente_azureopenai.py  ← Inicialización de cliente Azure OpenAI
    └── leer_pdf.py         ← Lectura de PDFs y extracción vía LLM
```

---

## 🧩 Funcionalidades incluidas

| Función                         | Descripción                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|
| `detectar_ruta()`              | Permite construir rutas relativas de forma portable.                        |
| `crear_cliente_azureopenai()`  | Inicializa el cliente de Azure OpenAI usando variables de entorno.          |
| `leer_pdf()`                   | Extrae información de documentos PDF mediante Azure OpenAI y prompts.       |

---

## 🧼 Buenas prácticas

- ✅ Usar esta carpeta como fuente de funciones modelo.
- ✅ Copiar código a tus proyectos locales.
- ❌ No desarrollar ni probar código dentro de esta plantilla.

---


## 📬 ¿Tienes una función que podría ser útil?

Si conoces alguna función que creas que puede ser útil para otros equipos y que podría formar parte de esta plantilla, contacta con:

📧 nicolas.renedo@accenture.com
