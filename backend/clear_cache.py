# Crear archivo: clear_cache.py en backend/
import os
import shutil

def clear_python_cache(start_dir="."):
    """Limpia todo el caché de Python recursivamente"""
    for root, dirs, files in os.walk(start_dir):
        # Eliminar directorios __pycache__
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                print(f"Eliminando {dir_path}")
                shutil.rmtree(dir_path)
        
        # Eliminar archivos .pyc y .pyo
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file)
                print(f"Eliminando {file_path}")
                os.remove(file_path)

if __name__ == "__main__":
    clear_python_cache()
    print("✅ Caché de Python limpiado completamente")
