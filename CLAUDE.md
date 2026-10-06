# CLAUDE.md — Gestor de inventario y ventas "La Esquina"

App de consola en Python 3.10+ para una tienda pequeña: alta de productos,
ventas con descuentos e IVA, cotizaciones, reportes y persistencia en JSON.
**Objetivo del repo:** refactorizar `src/` SIN cambiar el comportamiento
observable. La suite de `tests/` es de caja negra y es la fuente de verdad.

## Comandos (córrelos SIEMPRE antes de dar una tarea por terminada)

```bash
pytest -q                 # deben pasar TODOS (20 originales + los nuevos)
ruff check src            # meta final: 0 errores
ruff check src --fix      # solo para fixes triviales (imports, encoding)
cd src && mypy --strict . # opcional: verifica los type hints (0 errores)
python docs/evidencia/comparar_menu.py src datos_ejemplo.json  # salida del menú
cd src && python main.py  # prueba manual del menú (opcional)
```

## Mapa del código

| Archivo | Responsabilidad |
|---------|-----------------|
| `src/gestor.py` | Estado global (`INVENTARIO`, `VENTAS`, folio) + reglas de productos y ventas |
| `src/almacen.py` | Guardar / cargar el estado en JSON |
| `src/reportes.py` | Reportes de inventario, ventas y más vendidos |
| `src/main.py` | Menú interactivo (única capa que usa `input`/`print`); una función `opcion_*` por opción + diccionario `ACCIONES` |
| `tests/test_caracterizacion.py`, `tests/test_manejo_errores.py` | Pruebas agregadas en el reto (sí se pueden ampliar) |

## Reglas que NO se negocian

1. **No modifiques archivos existentes de `tests/` ni `pyproject.toml`.**
   Si un test falla, el error está en tu cambio, no en el test. Sí puedes
   AGREGAR archivos de prueba nuevos (`tests/test_*_extra.py`).
2. **API pública congelada** (la usan los tests): `gestor.INVENTARIO`,
   `gestor.VENTAS`, `gestor.reiniciar_sistema`, `gestor.agregarProducto`,
   `gestor.buscarProducto`, `gestor.eliminar_producto`,
   `gestor.actualizar_stock`, `gestor.registrar_venta`, `gestor.cotizar`,
   `almacen.guardar_datos`, `almacen.cargar_datos`,
   `reportes.productos_stock_bajo`, `reportes.total_vendido`,
   `reportes.mas_vendidos`, `reportes.reporte_inventario`.
   `agregarProducto` y `buscarProducto` conservan su camelCase (excepción
   configurada en ruff). No cambies firmas, valores de retorno ni claves de
   los diccionarios (`codigo`, `nombre`, `precio`, `stock`, `folio`,
   `total`, `ticket`, …).
3. **Mismos resultados numéricos:** el orden de las operaciones y los
   `round(..., 2)` de dinero deben producir exactamente los mismos totales.
4. **Una refactorización por vez.** Al terminar cada una: `pytest -q`,
   `ruff check src`, muestra el `git diff` y espera aprobación antes del commit.
5. Si detectas un bug, **repórtalo, no lo corrijas en silencio**: se decide
   aparte y se documenta en `docs/bitacora.md`.

## Convenciones de estilo

- PEP 8, líneas ≤ 88, `snake_case` para funciones/variables,
  `MAYUSCULAS` para constantes, `_prefijo` para helpers privados.
- Nombres descriptivos en español, sin acentos en identificadores.
  ❌ `aux`, `temp2`, `x`, `d`, `t`, `hacer_cosa` → ✅ `subtotal`,
  `resultados`, `producto`, `datos`, `ticket`, `formatear_moneda`.
- Type hints en todas las funciones (`list[dict]`, `str | None`, sintaxis 3.10).
- Docstring breve en español en cada función pública (qué hace y qué regresa).
- Sin números mágicos: reglas de negocio como constantes con nombre.
  ❌ `if subtotal >= 1000: desc = subtotal * 0.10`
  ✅ `if subtotal >= UMBRAL_DESCUENTO_ALTO: descuento = subtotal * TASA_DESCUENTO_ALTO`
- Cláusulas de guarda en lugar de `if` anidados; funciones de complejidad ≤ 10.
- Archivos siempre con `with open(..., encoding="utf-8")`.
- Capturar excepciones concretas (`json.JSONDecodeError`, `OSError`), nunca
  `except Exception` genérico.
- Lógica sin `print`/`input`: solo `main.py` habla con la consola.
- Valida los datos externos (JSON, entrada del usuario) ANTES de modificar el
  estado global: o se aplica todo o no cambia nada.
- Usa los tipos del proyecto: `gestor.Producto`, `gestor.Venta` (TypedDict) e
  `Importes` (NamedTuple) en lugar de `dict` genérico.

## Formato de commits (Conventional Commits, en español)

```
refactor(gestor): extrae el cálculo de descuentos duplicado
test: agrega pruebas de caracterización del ticket
docs: registra la refactorización 3 en la bitácora
```

## Documentación del proceso

- `docs/diagnostico.md`: code smells detectados y plan priorizado (PLAN).
- `docs/bitacora.md`: una entrada por refactorización (prompt, cambio,
  justificación, resultado de tests y ruff).
- `docs/reflexion.md`: aprendizajes finales.

## Historial de este archivo

- v1: versión inicial (comandos, reglas, convenciones).
- v2 (al cerrar la refactorización 9): se incorporaron lecciones del proceso
  para no repetirlas en cada prompt: pruebas NUEVAS para TDD (R6), validar
  antes de mutar el estado (R6), verificación diferencial del menú porque los
  tests no revisan cada salto de línea (R7), `mypy --strict` y los tipos
  `Producto`/`Venta`/`Importes` como vocabulario del proyecto (R9).
