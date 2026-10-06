"""Logica de negocio del gestor de inventario y ventas de "La Esquina"."""

from datetime import datetime
from typing import NamedTuple, TypedDict

# ---------------------------------------------------------------
# Reglas de negocio
# ---------------------------------------------------------------
TASA_IVA = 0.16

# Descuento por volumen: se aplica sobre el subtotal de la venta
UMBRAL_DESCUENTO_ALTO = 1000
TASA_DESCUENTO_ALTO = 0.10
UMBRAL_DESCUENTO_MEDIO = 500
TASA_DESCUENTO_MEDIO = 0.05

# Descuento extra para clientes cuyo codigo empieza con el prefijo VIP,
# solo si el monto (ya con descuento por volumen) supera el minimo
PREFIJO_CLIENTE_VIP = "VIP"
TASA_DESCUENTO_VIP = 0.02
MONTO_MINIMO_VIP = 200

# Productos con menos unidades que esto se consideran con stock bajo
STOCK_MINIMO = 5

NOMBRE_TIENDA = "TIENDA LA ESQUINA"
SEPARADOR_TICKET = "-" * 28
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"



class Producto(TypedDict):
    """Producto del inventario (asi se guarda tambien en el JSON)."""

    codigo: str
    nombre: str
    precio: float
    stock: int


class Venta(TypedDict):
    """Registro de una venta (asi se guarda tambien en el JSON)."""

    folio: int
    codigo: str
    nombre: str
    cantidad: int
    subtotal: float
    descuento: float
    impuesto: float
    total: float
    cliente: str | None
    fecha: str
    ticket: str


class Importes(NamedTuple):
    """Montos calculados de una compra (sin redondear, salvo el total)."""

    descuento: float
    impuesto: float
    total: float


# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO: dict[str, Producto] = {}
VENTAS: list[Venta] = []
contador_ventas: int = 0
ultimo_error: str = ""


def reiniciar_sistema() -> None:
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contador_ventas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contador_ventas = 0
    ultimo_error = ""


def agregarProducto(
    codigo: str | None, nombre: str, precio: float, stock: int
) -> bool:
    """Da de alta un producto. Regresa False si algun dato es invalido."""
    global ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return False
    if codigo in INVENTARIO:
        ultimo_error = "el producto ya existe"
        return False
    if precio <= 0:
        ultimo_error = "precio invalido"
        return False
    if stock < 0:
        ultimo_error = "stock invalido"
        return False
    INVENTARIO[codigo] = {
        "codigo": codigo,
        "nombre": nombre,
        "precio": precio,
        "stock": stock,
    }
    return True


def eliminar_producto(codigo: str) -> bool:
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo: str, cantidad: int) -> bool:
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    nuevo_stock = INVENTARIO[codigo]["stock"] + cantidad
    if nuevo_stock < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = nuevo_stock
    return True


def buscarProducto(texto: str) -> list[Producto]:
    """Regresa los productos cuyo nombre contiene el texto (ignora mayusculas)."""
    texto_buscado = texto.lower()
    return [
        producto
        for producto in INVENTARIO.values()
        if texto_buscado in producto["nombre"].lower()
    ]


def calcular_descuento_volumen(subtotal: float) -> float:
    """Regresa el descuento por volumen que corresponde a un subtotal."""
    if subtotal >= UMBRAL_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= UMBRAL_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0


def es_cliente_vip(cliente: str | None) -> bool:
    """Indica si el codigo de cliente tiene el prefijo VIP."""
    return cliente is not None and cliente.startswith(PREFIJO_CLIENTE_VIP)


def calcular_importes(subtotal: float, cliente: str | None = None) -> Importes:
    """Calcula descuento, IVA y total de una compra.

    Es la unica fuente de verdad de los precios: la usan tanto
    registrar_venta como cotizar. El extra VIP solo aplica si el monto,
    ya con el descuento por volumen, supera MONTO_MINIMO_VIP.
    """
    descuento = calcular_descuento_volumen(subtotal)
    if es_cliente_vip(cliente) and subtotal - descuento > MONTO_MINIMO_VIP:
        descuento = descuento + subtotal * TASA_DESCUENTO_VIP
    base = subtotal - descuento
    impuesto = base * TASA_IVA
    return Importes(descuento, impuesto, round(base + impuesto, 2))


def _validar_venta(codigo: str | None, cantidad: int | None) -> str | None:
    """Regresa el motivo por el que la venta no procede, o None si es valida."""
    if codigo is None or codigo == "":
        return "codigo vacio"
    if codigo not in INVENTARIO:
        return "producto no existe"
    if cantidad is None or cantidad <= 0:
        return "cantidad invalida"
    if INVENTARIO[codigo]["stock"] < cantidad:
        return "stock insuficiente"
    return None


def _armar_ticket(venta: Venta, hubo_descuento: bool) -> str:
    """Arma el ticket en texto plano de una venta ya registrada."""
    lineas = [
        NOMBRE_TIENDA,
        SEPARADOR_TICKET,
        f"Folio: {venta['folio']}",
        f"{venta['nombre']} x{venta['cantidad']}",
        f"Subtotal: ${venta['subtotal']}",
    ]
    if hubo_descuento:
        lineas.append(f"Descuento: -${venta['descuento']}")
    lineas.append(f"IVA: ${venta['impuesto']}")
    lineas.append(f"TOTAL: ${venta['total']}")
    return "\n".join(lineas) + "\n"


def _siguiente_folio() -> int:
    """Incrementa el contador de ventas y regresa el nuevo folio."""
    global contador_ventas
    contador_ventas = contador_ventas + 1
    return contador_ventas


def registrar_venta(
    codigo: str | None, cantidad: int | None, cliente: str | None = ""
) -> Venta | None:
    """Registra una venta: valida, cobra, descuenta stock y genera el ticket.

    Regresa el diccionario de la venta, o None si no procede (el motivo
    queda en ultimo_error).
    """
    global ultimo_error
    error = _validar_venta(codigo, cantidad)
    if error is not None:
        ultimo_error = error
        return None
    # _validar_venta ya garantizo que ambos tienen valor
    assert codigo is not None and cantidad is not None

    producto = INVENTARIO[codigo]
    subtotal = producto["precio"] * cantidad
    importes = calcular_importes(subtotal, cliente)
    producto["stock"] = producto["stock"] - cantidad

    venta: Venta = {
        "folio": _siguiente_folio(),
        "codigo": codigo,
        "nombre": producto["nombre"],
        "cantidad": cantidad,
        "subtotal": round(subtotal, 2),
        "descuento": round(importes.descuento, 2),
        "impuesto": round(importes.impuesto, 2),
        "total": importes.total,
        "cliente": cliente,
        "fecha": datetime.now().strftime(FORMATO_FECHA),
        "ticket": "",
    }
    venta["ticket"] = _armar_ticket(venta, hubo_descuento=importes.descuento > 0)
    VENTAS.append(venta)
    return venta


def cotizar(codigo: str, cantidad: int | None) -> float | None:
    """Calcula cuanto costaria una compra sin registrar la venta."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    subtotal = INVENTARIO[codigo]["precio"] * cantidad
    return calcular_importes(subtotal).total
