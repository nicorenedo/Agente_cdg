from pathlib import Path

def detectar_ruta(nombre_proyecto: str) -> Path:
    """
    Sube niveles desde el directorio actual hasta encontrar una carpeta cuyo nombre
    coincida con el nombre del proyecto proporcionado.

    Esta función permite trabajar con rutas relativas al proyecto desde cualquier subdirectorio,
    evitando el uso de rutas absolutas que dependen de la ubicación del usuario.

    Parámetros:
        nombre_proyecto (str): Nombre del directorio raíz del proyecto.

    Retorna:
        Path: Ruta absoluta al directorio raíz encontrado.

    Lanza:
        RuntimeError: Si no se encuentra el directorio dentro de 10 niveles.
    """
    carpeta_actual = Path().resolve()
    for _ in range(10):  # Limitar a 10 niveles para evitar ciclos infinitos
        if carpeta_actual.name == nombre_proyecto:
            return carpeta_actual
        carpeta_actual = carpeta_actual.parent
    raise RuntimeError(f"❌ No se encontró una carpeta llamada '{nombre_proyecto}' en la jerarquía.")

# ------------------------------------------------------------------------------------
# Ejemplo de uso real de esta función (puedes copiar a tu notebook o script)
# ------------------------------------------------------------------------------------

# Nombre del directorio raíz de tu proyecto (ajústalo según tu caso real)
nombre_raiz_proyecto = "PathUtils"  # Cambia esto al nombre de tu repo

# Detectar automáticamente la raíz del proyecto
ROOT_DIR = detectar_ruta(nombre_raiz_proyecto)

# Confirmación de que la raíz se ha detectado correctamente
print(f"📁 ROOT_DIR correctamente detectado en: {ROOT_DIR}")

# Construcción de una ruta relativa a partir de la raíz
ruta_pdf = ROOT_DIR / "data" / "raw" / "EjemploPaths.pdf"
