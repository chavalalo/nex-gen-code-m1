"""Pruebas de los bugs B3 y B4 del menú (agregadas en el reto, escritas en rojo)."""

from pathlib import Path

import main

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def test_archivo_de_datos_no_depende_del_directorio_actual():
    # B3: el README indica `cd src && python main.py`; el archivo de ejemplo
    # vive en la raíz del proyecto, así que la ruta debe ser absoluta.
    assert Path(main.ARCHIVO) == RAIZ_PROYECTO / "datos_ejemplo.json"


def test_menu_no_dice_datos_cargados_si_el_archivo_esta_corrupto(
    monkeypatch, capsys, tmp_path
):
    # B4: antes imprimía "Datos cargados de ..." aunque la carga fallara.
    ruta = tmp_path / "datos.json"
    ruta.write_text("{corrupto", encoding="utf-8")
    monkeypatch.setattr(main, "ARCHIVO", str(ruta))
    monkeypatch.setattr("builtins.input", lambda _mensaje="": "8")
    monkeypatch.setattr(main.almacen, "guardar_datos", lambda _ruta: True)
    main.menu()
    salida = capsys.readouterr().out
    assert "Datos cargados" not in salida
    assert "No se pudieron cargar los datos: archivo corrupto" in salida
