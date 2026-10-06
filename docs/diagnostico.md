# Diagnóstico y plan de refactorización (PLAN)

> Fase de exploración en **modo plan / chat**: solo lectura, sin modificar
> código. Al terminar, `git status` solo debe mostrar este archivo nuevo.

## Línea base (antes de tocar nada)

| Verificación | Resultado |
|--------------|-----------|
| `pytest -q` | **20 passed** |
| `ruff check src` | **20 errores** (7 corregibles con `--fix`) |

Errores de ruff por regla:

| Regla | # | Qué significa | Dónde |
|-------|---|---------------|-------|
| UP009 | 4 | Declaración `# -*- coding: utf-8 -*-` innecesaria | los 4 archivos |
| SIM102 | 3 | `if` anidados que se pueden unir | `gestor.registrar_venta` (VIP) |
| SIM115 | 3 | `open()` sin `with` | `almacen` ×2, `reportes` ×1 |
| C901 | 2 | Complejidad > 10 | `registrar_venta` (12), `main.menu` (17) |
| N802 | 2 | Función no snake_case | `hayArchivo`, `reporteViejoCSV` |
| SIM108 | 1 | `if/else` que debería ser ternario | descuento en `registrar_venta` |
| N816 | 1 | Global mixedCase | `contadorVentas` |
| SIM103 | 1 | `if cond: return True else: return False` | `hayArchivo` |
| UP015 | 1 | `open(ruta, "r")` modo redundante | `almacen.cargar_datos` |
| I001 | 1 | Imports desordenados | `main.py` |
| F401 | 1 | Import sin usar (`os`) | `reportes.py` |

## Code smells detectados (más allá de ruff)

| # | Smell | Ubicación | Severidad |
|---|-------|-----------|-----------|
| S1 | **Lógica duplicada**: el cálculo de descuento por volumen + IVA está copiado en `registrar_venta` y `cotizar` | `gestor.py` | Alta |
| S2 | **Función gigante** (valida, calcula, descuenta stock, genera folio, arma ticket, guarda) | `gestor.registrar_venta` | Alta |
| S3 | **Pirámide de `if` anidados** para validar (4 niveles) y para el cliente VIP | `gestor.registrar_venta` | Alta |
| S4 | **Números mágicos**: `1000`, `500`, `0.10`, `0.05`, `0.02`, `200`, `0.16`, `"VIP"`, `5` (stock mínimo, repetido 2 veces) | `gestor.py`, `reportes.py` | Alta |
| S5 | **Nombres crípticos**: `x`, `aux`, `temp`, `temp2`, `desc`, `t`, `d`, `f`, `k`, `p`, `s`, `hacer_cosa` | todos | Media |
| S6 | **Estilos de nombrado mezclados**: `contadorVentas`, `hayArchivo`, `reporteViejoCSV` junto a `snake_case` | todos | Media |
| S7 | **Código muerto**: `calcular_descuento_viejo`, `exportar_txt` comentado, `reporteViejoCSV`, `MODO_DEBUG`, `import os` | `gestor.py`, `reportes.py` | Media |
| S8 | **Manejo de errores frágil**: `open` sin `with`, `except Exception` genérico, un JSON válido sin la clave `"inventario"` revienta con `KeyError` en vez de regresar `False` | `almacen.py` | Media |
| S9 | **Mezcla de lógica y E/S**: `reporte_inventario` y `resumen_ventas` imprimen y además regresan el texto | `reportes.py` | Media |
| S10 | **Menú monolítico**: un `if/elif` de 8 ramas con la lógica de cada opción adentro | `main.menu` | Media |
| S11 | **Algoritmo reinventado**: burbuja a mano (con un `TODO`) en lugar de `sorted`; sumas a mano en lugar de `sum` | `reportes.py` | Baja |
| S12 | **Sin type hints** ni docstrings en varias funciones | todos | Baja |
| S13 | **Estado global** mutable compartido entre módulos | `gestor.py` | Media (restringido por los tests) |

## Hallazgos de comportamiento (bugs latentes) — se reportan, no se corrigen en silencio

| # | Hallazgo | Evidencia | Decisión |
|---|----------|-----------|----------|
| B1 | `cargar_datos` con un JSON válido pero sin `"inventario"` lanza `KeyError` | Probado: `{"otra": 1}` → `KeyError: 'inventario'` | Corregir en la refactorización de manejo de errores: regresar `False` y `ultimo_error = "archivo corrupto"` (coherente con el contrato documentado: "Regresa False si el archivo ... esta corrupto"). |
| B2 | `cotizar` no aplica el descuento VIP (no recibe cliente) | `cotizar("A1", 6)` = 661.2; venta VIP = 647.28 | **No se cambia**: el test `test_cotizar_coincide_con_el_total_de_la_venta` fija el contrato sin cliente. Se documenta. |
| B3 | El README indica `cd src && python main.py`, pero `ARCHIVO = "datos_ejemplo.json"` es relativo al directorio actual: desde `src/` no encuentra los datos de ejemplo y al guardar crea un archivo nuevo en `src/` | Probado: no aparece "Datos cargados de…" | Pendiente de decidir (ver plan, paso opcional). |

## Restricciones que condicionan el plan

- Los tests acceden directo a `gestor.INVENTARIO`, `gestor.VENTAS` y
  `gestor.reiniciar_sistema()`, así que **no se puede eliminar el estado
  global** sin modificar los tests (prohibido). Se reduce su uso, pero se
  conserva la interfaz.
- `agregarProducto` y `buscarProducto` conservan su nombre.

## Plan priorizado (una refactorización = un commit)

| Orden | Refactorización | Categoría del reto | Smells | Criterio de aceptación |
|-------|-----------------|--------------------|--------|------------------------|
| 0 | Pruebas de caracterización nuevas (ticket, VIP, redondeos, reportes, errores de carga) en un archivo NUEVO | Red de seguridad | — | Pasan contra el código original |
| 1 | Eliminar código muerto, imports sin usar y declaraciones de encoding | Código muerto | S7 | 20+ tests ok; desaparecen F401, UP009, N802 de `reporteViejoCSV` |
| 2 | Reemplazar números mágicos por constantes de negocio con nombre | Legibilidad | S4 | Ningún literal de negocio en la lógica |
| 3 | Extraer el cálculo de precios duplicado a funciones reutilizables | Extraer funciones | S1 | `cotizar` y `registrar_venta` usan la misma función |
| 4 | Dividir `registrar_venta` y aplanar condicionales con cláusulas de guarda | Simplificar condicionales | S2, S3 | Sin C901, SIM102, SIM108 |
| 5 | Renombrar variables y funciones con nombres descriptivos y PEP 8 | Renombrar | S5, S6 | Sin N802/N816; cero nombres de 1 letra o `aux/temp` |
| 6 | Mejorar el manejo de errores en la persistencia | Manejo de errores | S8, B1 | Sin SIM115/UP015; JSON sin claves → `False` |
| 7 | Separar lógica de E/S en reportes y simplificar con `sorted`/`sum` | Extraer funciones / simplificar | S9, S11 | Reportes no imprimen; `main` imprime |
| 8 | Dividir el menú en funciones por opción (tabla de despacho) | Extraer funciones | S10 | Sin C901 en `main` |
| 9 | Agregar type hints y docstrings (`TypedDict` para producto y venta) | Type hints | S12 | Todas las funciones anotadas |
| Final | `ruff check src` = 0, `pytest` verde, README actualizado, reflexión | Validación | — | 0 errores de ruff |
