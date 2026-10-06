"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os

import gestor

ERROR_NO_EXISTE = "el archivo no existe"
ERROR_CORRUPTO = "archivo corrupto"
ERROR_LECTURA = "no se pudo leer el archivo"
ERROR_ESCRITURA = "no se pudo guardar el archivo"


def guardar_datos(ruta):
    """Guarda el inventario, las ventas y el folio actual en un JSON.

    Regresa False (y deja el motivo en gestor.ultimo_error) si no se puede
    escribir el archivo.
    """
    datos = {
        "inventario": gestor.INVENTARIO,
        "ventas": gestor.VENTAS,
        "contador": gestor.contador_ventas,
    }
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=2, ensure_ascii=False)
    except OSError:
        gestor.ultimo_error = ERROR_ESCRITURA
        return False
    return True


def _tiene_estructura_valida(datos):
    """Revisa que el JSON tenga las secciones que el gestor necesita."""
    return (
        isinstance(datos, dict)
        and isinstance(datos.get("inventario"), dict)
        and isinstance(datos.get("ventas"), list)
    )


def cargar_datos(ruta):
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe, no se puede leer o esta corrupto;
    en ese caso el estado actual no se modifica y el motivo queda en
    gestor.ultimo_error.
    """
    if not existe_archivo(ruta):
        gestor.ultimo_error = ERROR_NO_EXISTE
        return False
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        gestor.ultimo_error = ERROR_CORRUPTO
        return False
    except OSError:
        gestor.ultimo_error = ERROR_LECTURA
        return False
    if not _tiene_estructura_valida(datos):
        gestor.ultimo_error = ERROR_CORRUPTO
        return False

    # Solo se toca el estado global cuando ya se sabe que los datos son validos
    gestor.INVENTARIO.clear()
    gestor.INVENTARIO.update(datos["inventario"])
    gestor.VENTAS.clear()
    gestor.VENTAS.extend(datos["ventas"])
    gestor.contador_ventas = datos.get("contador", 0)
    return True


def existe_archivo(ruta):
    """Indica si ya existe el archivo de datos."""
    return os.path.exists(ruta)
