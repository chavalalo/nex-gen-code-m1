"""Reportes de la tienda: inventario, ventas y mas vendidos.

Las funciones de este modulo solo calculan y arman texto; quien las llama
(main.py) decide si lo imprime.
"""

from collections import Counter

import gestor

MARCA_STOCK_BAJO = "  <-- STOCK BAJO"


def formatear_moneda(monto: float) -> str:
    """Da formato de dinero a un numero: 12.5 -> "$12.5"."""
    return "$" + str(round(monto, 2))


def tiene_stock_bajo(producto: gestor.Producto) -> bool:
    """Indica si un producto esta por debajo del stock minimo."""
    return producto["stock"] < gestor.STOCK_MINIMO


def productos_stock_bajo() -> list[gestor.Producto]:
    """Regresa la lista de productos con stock por debajo del minimo."""
    return [p for p in gestor.INVENTARIO.values() if tiene_stock_bajo(p)]


def _linea_de_inventario(producto: gestor.Producto) -> str:
    """Arma la linea del reporte de inventario para un producto."""
    linea = (
        f"{producto['codigo']} | {producto['nombre']} | "
        f"{formatear_moneda(producto['precio'])} | stock: {producto['stock']}"
    )
    if tiene_stock_bajo(producto):
        linea += MARCA_STOCK_BAJO
    return linea


def reporte_inventario() -> str:
    """Regresa el reporte del inventario como texto."""
    productos = gestor.INVENTARIO.values()
    valor_total = sum(p["precio"] * p["stock"] for p in productos)
    lineas = ["===== INVENTARIO ====="]
    lineas.extend(_linea_de_inventario(p) for p in productos)
    lineas.append(f"Valor total del inventario: {formatear_moneda(valor_total)}")
    return "\n".join(lineas) + "\n"


def total_vendido() -> float:
    """Suma el total (con IVA) de todas las ventas registradas."""
    return round(sum(venta["total"] for venta in gestor.VENTAS), 2)


def mas_vendidos(n: int = 3) -> list[tuple[str, int]]:
    """Regresa los n productos mas vendidos como lista de (codigo, unidades).

    En caso de empate se respeta el orden en que se vendieron por primera vez.
    """
    unidades_por_codigo: Counter[str] = Counter()
    for venta in gestor.VENTAS:
        unidades_por_codigo[venta["codigo"]] += venta["cantidad"]
    ranking = sorted(
        unidades_por_codigo.items(), key=lambda par: par[1], reverse=True
    )
    return ranking[:n]


def resumen_ventas() -> str:
    """Regresa el resumen de ventas del dia como texto."""
    lineas = ["===== RESUMEN DE VENTAS ====="]
    lineas.extend(
        f"Folio {venta['folio']}: {venta['nombre']} x{venta['cantidad']}"
        f" = {formatear_moneda(venta['total'])}"
        for venta in gestor.VENTAS
    )
    total_dia = sum(venta["total"] for venta in gestor.VENTAS)
    lineas.append(f"Numero de ventas: {len(gestor.VENTAS)}")
    lineas.append(f"Total del dia: {formatear_moneda(total_dia)}")
    return "\n".join(lineas) + "\n"
