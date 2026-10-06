"""Pruebas de caracterización (agregadas durante el reto).

Fijan el comportamiento observable ACTUAL del programa antes de refactorizar:
textos exactos del ticket y de los reportes, fronteras de los descuentos,
mensajes de error y la salida del menú. Si una refactorización cambia
cualquiera de estas cosas, aquí se nota. Este archivo es nuevo: los tests
originales no se modificaron.
"""

import json

import pytest

import almacen
import gestor
import main
import reportes

# ---------------------------------------------------------------- ventas


@pytest.mark.parametrize(
    ("precio", "cantidad", "subtotal", "descuento", "impuesto", "total"),
    [
        (10.0, 2, 20.0, 0, 3.2, 23.2),  # sin descuento
        (499.99, 1, 499.99, 0, 80.0, 579.99),  # justo debajo de 500
        (500.0, 1, 500.0, 25.0, 76.0, 551.0),  # frontera exacta 5 %
        (999.99, 1, 999.99, 50.0, 152.0, 1101.99),  # justo debajo de 1000
        (1000.0, 1, 1000.0, 100.0, 144.0, 1044.0),  # frontera exacta 10 %
    ],
)
def test_importes_y_fronteras_de_descuento(
    precio, cantidad, subtotal, descuento, impuesto, total
):
    gestor.agregarProducto("A1", "Prod", precio, 100)
    venta = gestor.registrar_venta("A1", cantidad)
    assert venta["subtotal"] == subtotal
    assert venta["descuento"] == descuento
    assert venta["impuesto"] == impuesto
    assert venta["total"] == total


def test_venta_tiene_todas_las_claves_esperadas():
    gestor.agregarProducto("A1", "Café", 10.0, 10)
    venta = gestor.registrar_venta("A1", 1, "C01")
    assert set(venta) == {
        "folio", "codigo", "nombre", "cantidad", "subtotal", "descuento",
        "impuesto", "total", "cliente", "fecha", "ticket",
    }
    assert venta["cliente"] == "C01"
    assert venta["nombre"] == "Café"


def test_ticket_sin_descuento_texto_exacto():
    gestor.agregarProducto("A1", "Café", 10.0, 10)
    venta = gestor.registrar_venta("A1", 2)
    assert venta["ticket"] == (
        "TIENDA LA ESQUINA\n"
        "----------------------------\n"
        "Folio: 1\n"
        "Café x2\n"
        "Subtotal: $20.0\n"
        "IVA: $3.2\n"
        "TOTAL: $23.2\n"
    )


def test_ticket_con_descuento_vip_texto_exacto():
    gestor.agregarProducto("A1", "Café", 100.0, 50)
    venta = gestor.registrar_venta("A1", 6, "VIP007")
    assert venta["ticket"] == (
        "TIENDA LA ESQUINA\n"
        "----------------------------\n"
        "Folio: 1\n"
        "Café x6\n"
        "Subtotal: $600.0\n"
        "Descuento: -$42.0\n"
        "IVA: $89.28\n"
        "TOTAL: $647.28\n"
    )


@pytest.mark.parametrize(
    ("cliente", "precio", "cantidad", "descuento_esperado"),
    [
        ("VIP1", 100.0, 3, 6.0),  # 300 sin desc. volumen, > 200 -> 2 % VIP
        ("VIP1", 100.0, 2, 0),  # 200 no es > 200 -> sin extra
        ("VIP", 100.0, 3, 6.0),  # exactamente "VIP" cuenta
        ("vip1", 100.0, 3, 0),  # minúsculas no cuentan
        ("XVIP", 100.0, 3, 0),  # VIP debe ir al inicio
        ("VI", 100.0, 3, 0),  # demasiado corto
        (None, 100.0, 3, 0),  # sin cliente
    ],
)
def test_reglas_del_descuento_vip(cliente, precio, cantidad, descuento_esperado):
    gestor.agregarProducto("A1", "Prod", precio, 100)
    venta = gestor.registrar_venta("A1", cantidad, cliente)
    assert venta["descuento"] == descuento_esperado
    assert venta["cliente"] == cliente


def test_vip_se_evalua_sobre_el_monto_ya_con_descuento_de_volumen():
    # 2 x 105 = 210 -> sin desc. volumen -> 210 > 200 -> 2 % VIP = 4.2
    gestor.agregarProducto("A1", "Prod", 105.0, 100)
    assert gestor.registrar_venta("A1", 2, "VIP1")["descuento"] == 4.2


@pytest.mark.parametrize(
    ("codigo", "cantidad", "mensaje"),
    [
        ("", 1, "codigo vacio"),
        (None, 1, "codigo vacio"),
        ("ZZZ", 1, "producto no existe"),
        ("A1", 0, "cantidad invalida"),
        ("A1", None, "cantidad invalida"),
        ("A1", 99, "stock insuficiente"),
    ],
)
def test_mensajes_de_error_de_venta(codigo, cantidad, mensaje):
    gestor.agregarProducto("A1", "Prod", 10.0, 5)
    assert gestor.registrar_venta(codigo, cantidad) is None
    assert gestor.ultimo_error == mensaje
    assert gestor.VENTAS == []


def test_cotizar_errores_y_no_aplica_vip():
    gestor.agregarProducto("A1", "Prod", 100.0, 5)
    assert gestor.cotizar("ZZZ", 1) is None
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.cotizar("A1", 0) is None
    assert gestor.ultimo_error == "cantidad invalida"
    # cotizar no revisa stock ni modifica nada
    assert gestor.cotizar("A1", 50) == 5220.0
    assert gestor.INVENTARIO["A1"]["stock"] == 5
    assert gestor.VENTAS == []


# ---------------------------------------------------------------- productos


def test_mensajes_de_error_de_productos():
    assert gestor.agregarProducto("", "X", 1.0, 1) is False
    assert gestor.ultimo_error == "codigo vacio"
    gestor.agregarProducto("A1", "X", 1.0, 1)
    assert gestor.agregarProducto("A1", "X", 1.0, 1) is False
    assert gestor.ultimo_error == "el producto ya existe"
    assert gestor.agregarProducto("A2", "X", 0, 1) is False
    assert gestor.ultimo_error == "precio invalido"
    assert gestor.agregarProducto("A2", "X", 1.0, -1) is False
    assert gestor.ultimo_error == "stock invalido"
    assert gestor.actualizar_stock("ZZZ", 1) is False
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.actualizar_stock("A1", -2) is False
    assert gestor.ultimo_error == "el stock no puede quedar negativo"
    assert gestor.eliminar_producto("ZZZ") is False
    assert gestor.ultimo_error == "producto no existe"


def test_buscar_producto_sin_coincidencias_y_en_mayusculas():
    gestor.agregarProducto("A1", "Café de grano", 185.0, 10)
    assert gestor.buscarProducto("xyz") == []
    assert len(gestor.buscarProducto("GRANO")) == 1


# ---------------------------------------------------------------- reportes


def test_stock_bajo_frontera_en_cinco():
    gestor.agregarProducto("A1", "Cuatro", 1.0, 4)
    gestor.agregarProducto("A2", "Cinco", 1.0, 5)
    assert [p["codigo"] for p in reportes.productos_stock_bajo()] == ["A1"]


def test_reporte_inventario_texto_exacto():
    gestor.agregarProducto("A1", "Leche", 26.0, 3)
    gestor.agregarProducto("A2", "Azúcar", 32.5, 40)
    assert reportes.reporte_inventario() == (
        "===== INVENTARIO =====\n"
        "A1 | Leche | $26.0 | stock: 3  <-- STOCK BAJO\n"
        "A2 | Azúcar | $32.5 | stock: 40\n"
        "Valor total del inventario: $1378.0\n"
    )


def test_resumen_ventas_texto_exacto():
    gestor.agregarProducto("A1", "Café", 10.0, 100)
    gestor.registrar_venta("A1", 2)
    gestor.registrar_venta("A1", 1)
    assert reportes.resumen_ventas() == (
        "===== RESUMEN DE VENTAS =====\n"
        "Folio 1: Café x2 = $23.2\n"
        "Folio 2: Café x1 = $11.6\n"
        "Numero de ventas: 2\n"
        "Total del dia: $34.8\n"
    )


def test_mas_vendidos_default_tres_y_empates_en_orden_de_aparicion():
    for codigo in ("A1", "B1", "C1", "D1"):
        gestor.agregarProducto(codigo, codigo, 1.0, 100)
    gestor.registrar_venta("B1", 2)
    gestor.registrar_venta("A1", 2)
    gestor.registrar_venta("C1", 5)
    gestor.registrar_venta("D1", 1)
    assert reportes.mas_vendidos() == [("C1", 5), ("B1", 2), ("A1", 2)]
    assert reportes.mas_vendidos(10)[-1] == ("D1", 1)


def test_reportes_vacios():
    assert reportes.mas_vendidos() == []
    assert reportes.productos_stock_bajo() == []
    assert reportes.reporte_inventario().endswith(
        "Valor total del inventario: $0\n"
    )


# ---------------------------------------------------------------- almacén


def test_guardar_produce_el_formato_json_esperado(tmp_path):
    ruta = tmp_path / "d.json"
    gestor.agregarProducto("A1", "Café", 10.0, 5)
    gestor.registrar_venta("A1", 1)
    almacen.guardar_datos(str(ruta))
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert set(datos) == {"inventario", "ventas", "contador"}
    assert datos["contador"] == 1
    assert datos["inventario"]["A1"]["stock"] == 4
    assert "Café" in ruta.read_text(encoding="utf-8")  # ensure_ascii=False


def test_cargar_archivo_corrupto(tmp_path):
    ruta = tmp_path / "malo.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    gestor.agregarProducto("A1", "Café", 10.0, 5)
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
    assert "A1" in gestor.INVENTARIO  # el estado no se toca si falla


def test_cargar_archivo_inexistente_deja_mensaje(tmp_path):
    assert almacen.cargar_datos(str(tmp_path / "nada.json")) is False
    assert gestor.ultimo_error == "el archivo no existe"


def test_cargar_sin_contador_usa_cero(tmp_path):
    ruta = tmp_path / "d.json"
    ruta.write_text(
        '{"inventario": {"A1": {"codigo": "A1", "nombre": "X", "precio": 1.0, '
        '"stock": 9}}, "ventas": []}',
        encoding="utf-8",
    )
    assert almacen.cargar_datos(str(ruta)) is True
    assert gestor.registrar_venta("A1", 1)["folio"] == 1


# ---------------------------------------------------------------- menú


def _correr_menu(monkeypatch, capsys, tmp_path, entradas):
    ruta = tmp_path / "datos.json"
    monkeypatch.setattr(main, "ARCHIVO", str(ruta))
    respuestas = iter(entradas)
    monkeypatch.setattr("builtins.input", lambda _mensaje="": next(respuestas))
    main.menu()
    return capsys.readouterr().out, ruta


def test_menu_flujo_completo(monkeypatch, capsys, tmp_path):
    salida, ruta = _correr_menu(
        monkeypatch,
        capsys,
        tmp_path,
        [
            "1", "A1", "Café", "abc", "10", "4",  # alta (con un número inválido)
            "1", "A1", "Otro", "1", "1",  # alta duplicada
            "2", "A1", "2", "",  # venta
            "2", "ZZ", "1", "",  # venta con error
            "3", "A1", "1",  # cotizar
            "3", "ZZ", "1",  # cotizar con error
            "4", "5", "6", "7",  # reportes
            "9",  # opción inválida
            "8",  # guardar y salir
        ],
    )
    assert "Bienvenido al gestor de la tienda La Esquina" in salida
    assert "Eso no es un numero, intenta de nuevo." in salida
    assert "Producto agregado." in salida
    assert "Error: el producto ya existe" in salida
    assert "TOTAL: $23.2" in salida
    assert "Error: producto no existe" in salida
    assert "Total estimado (con IVA): $11.6" in salida
    assert "===== INVENTARIO =====" in salida
    assert "===== RESUMEN DE VENTAS =====" in salida
    assert "A1 -> 2 unidades" in salida
    assert "OJO: Café solo tiene 2 unidades" in salida
    assert "Opcion no valida." in salida
    assert "Datos guardados. Hasta luego." in salida
    assert ruta.exists()


def test_menu_carga_datos_existentes_y_sin_stock_bajo(monkeypatch, capsys, tmp_path):
    gestor.agregarProducto("A1", "Café", 10.0, 50)
    almacen.guardar_datos(str(tmp_path / "datos.json"))
    gestor.reiniciar_sistema()
    salida, _ = _correr_menu(monkeypatch, capsys, tmp_path, ["7", "8"])
    assert "Datos cargados de" in salida
    assert "No hay productos con stock bajo." in salida
