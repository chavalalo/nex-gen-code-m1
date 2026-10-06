"""Punto de entrada del gestor de tienda (menu interactivo en consola).

Este es el unico modulo que lee del teclado e imprime en pantalla; la logica
vive en gestor.py, almacen.py y reportes.py.
"""

from collections.abc import Callable
from pathlib import Path

import almacen
import gestor
import reportes

# Ruta absoluta: funciona igual si se ejecuta desde src/ o desde la raiz
ARCHIVO = str(Path(__file__).resolve().parent.parent / "datos_ejemplo.json")

OPCIONES_MENU = (
    "1) Agregar producto",
    "2) Registrar venta",
    "3) Cotizar",
    "4) Reporte de inventario",
    "5) Resumen de ventas",
    "6) Mas vendidos",
    "7) Alertas de stock bajo",
    "8) Guardar y salir",
)


def pedir_numero(mensaje: str) -> float:
    """Pide un numero al usuario hasta que escriba algo valido."""
    while True:
        respuesta = input(mensaje)
        try:
            return float(respuesta)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def pedir_entero(mensaje: str) -> int:
    """Pide un numero y lo trunca a entero (cantidades y stock)."""
    return int(pedir_numero(mensaje))


def mostrar_error() -> None:
    """Imprime el ultimo error registrado por la logica de negocio."""
    print("Error:", gestor.ultimo_error)


def opcion_agregar_producto() -> None:
    """Opcion 1: da de alta un producto con los datos del usuario."""
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = pedir_entero("Stock inicial: ")
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        mostrar_error()


def opcion_registrar_venta() -> None:
    """Opcion 2: registra una venta e imprime su ticket."""
    codigo = input("Codigo del producto: ")
    cantidad = pedir_entero("Cantidad: ")
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is not None:
        print(venta["ticket"])
    else:
        mostrar_error()


def opcion_cotizar() -> None:
    """Opcion 3: muestra el total estimado de una compra."""
    codigo = input("Codigo del producto: ")
    cantidad = pedir_entero("Cantidad: ")
    total = gestor.cotizar(codigo, cantidad)
    if total is not None:
        print("Total estimado (con IVA): $" + str(total))
    else:
        mostrar_error()


def opcion_reporte_inventario() -> None:
    """Opcion 4."""
    print(reportes.reporte_inventario())


def opcion_resumen_ventas() -> None:
    """Opcion 5."""
    print(reportes.resumen_ventas())


def opcion_mas_vendidos() -> None:
    """Opcion 6."""
    for codigo, unidades in reportes.mas_vendidos():
        print(codigo, "->", unidades, "unidades")


def opcion_alertas_stock() -> None:
    """Opcion 7: lista los productos con stock bajo."""
    productos_bajos = reportes.productos_stock_bajo()
    if not productos_bajos:
        print("No hay productos con stock bajo.")
        return
    for producto in productos_bajos:
        print("OJO:", producto["nombre"], "solo tiene", producto["stock"], "unidades")


def guardar_y_salir() -> None:
    """Opcion 8: guarda los datos y avisa si hubo un problema."""
    if almacen.guardar_datos(ARCHIVO):
        print("Datos guardados. Hasta luego.")
    else:
        mostrar_error()


ACCIONES: dict[str, Callable[[], None]] = {
    "1": opcion_agregar_producto,
    "2": opcion_registrar_venta,
    "3": opcion_cotizar,
    "4": opcion_reporte_inventario,
    "5": opcion_resumen_ventas,
    "6": opcion_mas_vendidos,
    "7": opcion_alertas_stock,
}
OPCION_SALIR = "8"


def cargar_datos_iniciales() -> None:
    """Carga el archivo de datos si existe y avisa si no se pudo."""
    if not almacen.existe_archivo(ARCHIVO):
        return
    if almacen.cargar_datos(ARCHIVO):
        print("Datos cargados de", ARCHIVO)
    else:
        print("No se pudieron cargar los datos:", gestor.ultimo_error)


def imprimir_menu() -> None:
    """Muestra las opciones disponibles."""
    print("")
    for opcion in OPCIONES_MENU:
        print(opcion)


def menu() -> None:
    """Ciclo principal: muestra el menu y ejecuta la opcion elegida."""
    print("Bienvenido al gestor de la tienda La Esquina")
    cargar_datos_iniciales()
    while True:
        imprimir_menu()
        opcion = input("Opcion: ")
        if opcion == OPCION_SALIR:
            guardar_y_salir()
            break
        accion = ACCIONES.get(opcion)
        if accion is None:
            print("Opcion no valida.")
        else:
            accion()


if __name__ == "__main__":
    menu()
