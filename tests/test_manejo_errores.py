"""Pruebas del manejo de errores de la persistencia (agregadas en el reto).

Se escribieron ANTES de corregir el código (TDD): las de JSON incompleto,
directorio y ruta de guardado inválida fallaban con el código original
porque lanzaban excepciones en lugar de regresar False.
"""

import pytest

import almacen
import gestor


@pytest.mark.parametrize(
    "contenido",
    [
        '{"otra": 1}',  # JSON válido sin las claves esperadas
        '{"inventario": {}}',  # falta "ventas"
        "[]",  # JSON válido pero no es un objeto
        '{"inventario": [], "ventas": []}',  # tipo incorrecto
    ],
)
def test_cargar_json_con_estructura_invalida_regresa_false(tmp_path, contenido):
    ruta = tmp_path / "d.json"
    ruta.write_text(contenido, encoding="utf-8")
    gestor.agregarProducto("A1", "Café", 10.0, 5)
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
    assert "A1" in gestor.INVENTARIO  # el estado anterior se conserva


def test_cargar_un_directorio_regresa_false(tmp_path):
    assert almacen.cargar_datos(str(tmp_path)) is False
    assert gestor.ultimo_error == "no se pudo leer el archivo"


def test_guardar_en_ruta_invalida_regresa_false(tmp_path):
    ruta = tmp_path / "no_existe" / "d.json"
    assert almacen.guardar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "no se pudo guardar el archivo"


def test_menu_avisa_si_no_pudo_guardar(monkeypatch, capsys, tmp_path):
    import main

    monkeypatch.setattr(main, "ARCHIVO", str(tmp_path / "no_existe" / "d.json"))
    monkeypatch.setattr("builtins.input", lambda _mensaje="": "8")
    main.menu()
    salida = capsys.readouterr().out
    assert "Error: no se pudo guardar el archivo" in salida
    assert "Datos guardados" not in salida


def test_cargar_archivo_que_no_es_utf8_regresa_false(tmp_path):
    ruta = tmp_path / "d.json"
    ruta.write_bytes(b'{"inventario": {"\xff": 1}}')
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
