# Bitácora de refactorización

**Nombre:** Salvador Razo
**Matrícula:**
**Fecha de inicio:** 2026-10-05
**Herramienta:** Claude (agente de código) con `CLAUDE.md` + `.claude/settings.json`

Cada refactorización se hizo **una a la vez**: prompt → revisión del plan →
cambio → `pytest -q` → `ruff check src` → revisión del `git diff` → commit.

## Resumen

| # | Prompt usado (resumen) | Cambio realizado | Justificación | Tests OK | Ruff |
|---|------------------------|------------------|---------------|----------|------|
| 0 | Configuración + diagnóstico (ver detalle) | `CLAUDE.md`, `.claudeignore`, `.claude/settings.json`, `docs/diagnostico.md` | Dar contexto y reglas al agente antes de tocar código | 20/20 ✅ | 20 errores (línea base) |
| — | Pruebas de caracterización (red de seguridad) | `tests/test_caracterizacion.py` nuevo, 36 pruebas | Detectar cualquier cambio de comportamiento que los 20 tests no ven | 56/56 ✅ | 20 |
| 1 | Eliminar código muerto verificando con grep | −40 líneas: 3 funciones muertas, global e import sin uso, encoding | Menos superficie, cero ambigüedad; git guarda el historial | 56/56 ✅ | 13 |
| 2 | Números mágicos → constantes, sin tocar la estructura | 13 constantes de negocio en `gestor.py`; `reportes` usa `STOCK_MINIMO` | Nombres que explican la regla; una sola fuente de verdad | 56/56 ✅ | 13 |
| 3 | Extraer cálculo de precios duplicado (con CoT para demostrar equivalencia de floats) | `calcular_descuento_volumen`, `calcular_importes` → `Importes`; usadas por venta y cotización | DRY: venta y cotización ya no pueden divergir; lógica de precios aislada y probable | 56/56 ✅ | 11 |
| 4 | Dividir `registrar_venta` + cláusulas de guarda (con lista de lo que NO debe cambiar) | 4 funciones extraídas; complejidad 12 → 2; VIP de 4 `if` a 1 | Responsabilidad única, sin efecto flecha, intención explícita | 56/56 ✅ | 8 |
| 5 | Renombrado descriptivo + PEP 8 con few-shot de ejemplos y lista de nombres intocables | ~35 renombres en 4 archivos; comentarios → docstrings | Código autoexplicativo; estilo consistente | 56/56 ✅ | 6 |
| 6 | Manejo de errores con TDD (prueba en rojo → fix mínimo → iteración UTF-8) | `with`, excepciones específicas, validación antes de mutar, errores como constantes | Carga atómica; ningún error se traga ni deja el sistema a medias | 64/64 ✅ | 2 |
| 7 | Separar E/S de reportes + biblioteca estándar, con verificación diferencial contra el original | Reportes sin `print`; burbuja → `sorted`; `sum`, `Counter`, comprehensions | Responsabilidad única, reutilizable, O(n log n) | 64/64 ✅ + diff idéntico | 2 |
| 8 | Menú → funciones por opción + diccionario de despacho, verificado con el diferencial | `menu()` complejidad 18 → 3; sin duplicación de errores ni de `int(pedir_numero())` | Abierto/cerrado: nueva opción = nueva función + 1 entrada | 64/64 ✅ + diff idéntico | **0** |
| 9 | Type hints completos verificados con `mypy --strict` (pedir explicación antes de aceptar cambios) | `Producto`/`Venta` TypedDict; todas las funciones anotadas; mypy 82 → 0 | Contratos explícitos; esquema del JSON documentado en código | 64/64 ✅ | 0 |
| fix | Bugs B3/B4 con TDD (decisión explícita de cambiar comportamiento) | Ruta absoluta con `pathlib`; aviso si la carga falla | El README funciona tal cual; el menú no miente al usuario | 66/66 ✅ | 0 |

---

## Paso 0 — Línea base y punto de retorno

```bash
git init && git add -A && git commit -m "chore: estado inicial del reto"
pytest -q          # 20 passed in 0.05s
ruff check src     # Found 20 errors. [*] 7 fixable with the --fix option
```

El commit de estado inicial es el punto contra el que se compara todo al
final y el "botón de deshacer" si una refactorización sale mal.

## Paso 1 — Configuración de Claude Code

**Prompt:**

```text
Contexto: proyecto Python 3.10 (gestor de inventario "La Esquina") que vamos a
refactorizar sin cambiar su comportamiento. Los tests de tests/ son de caja
negra y no se pueden modificar; tampoco pyproject.toml (config de ruff).

Instrucción: propón un CLAUDE.md corto (< 200 líneas) con:
1. Comandos para correr pruebas, linter y el menú.
2. Mapa de qué hace cada archivo de src/.
3. Reglas no negociables: no tocar tests ni pyproject.toml, API pública
   congelada (lista los nombres que usan los tests), mismos redondeos,
   una refactorización por vez.
4. Convenciones de estilo con ejemplos ❌/✅ (naming, constantes, type hints,
   manejo de errores, sin print en la lógica).
5. Formato de commits.
Además propón .claudeignore y un .claude/settings.json con permissions.deny
(secretos, venv, cachés, y bloquear Edit de los tests existentes) y un hook
PostToolUse que corra pytest después de cada edición.

Formato: muéstrame los tres archivos antes de guardarlos.
```

**Resultado / decisiones:**

- `CLAUDE.md`: comandos, mapa del código, 5 reglas, convenciones con ejemplos,
  formato de commits y una sección "Historial de este archivo" para registrar
  cómo se ajustan las instrucciones durante el reto.
- `.claudeignore`: entornos virtuales, cachés (`__pycache__`, `.pytest_cache`,
  `.ruff_cache`), datos generados por el menú, `.env`, archivos del SO y los
  documentos `.docx/.pdf` del curso (no son código y consumen contexto).
- `.claude/settings.json`: como vimos en la Clase 4, `.claudeignore` **no está
  en la documentación oficial**; lo que el cliente sí obliga son las reglas
  `permissions.deny`. Por eso se agregaron:
  - `deny` de lectura para `.env`, venv y cachés (higiene + seguridad).
  - `deny` de **edición** para los 4 archivos de tests y `pyproject.toml`:
    la regla "no modifiques los tests" deja de ser una sugerencia y pasa a ser
    un candado.
  - Hook `PostToolUse` que ejecuta `pytest -q -x` después de cada
    `Edit/Write`; si falla, regresa código 2 y el agente ve el error de
    inmediato ("CLAUDE.md sugiere; un hook obliga"). No se incluyó `ruff` en
    el hook porque al inicio hay 20 errores y bloquearía cada edición.
- `.gitignore` para no subir cachés al PR.

## Paso 2 — Exploración en modo plan (sin cambiar código)

**Prompt 2a — mapa del proyecto (prompt chaining, paso 1):**

```text
Lee src/ y tests/ y dame un mapa: qué hace cada archivo, qué funciones expone,
qué estado global existe y qué funciones usan los tests directamente. No
cambies nada.
```

**Prompt 2b — diagnóstico (rol exigente + formato accionable + anti-complacencia):**

```text
Actúa como revisor senior de Python enfocado en mantenibilidad.
Analiza src/ y entrega una tabla con: smell, archivo/función, severidad
(alta/media/baja) y refactorización sugerida. Incluye los 20 errores de
`ruff check src` agrupados por regla.
Además, busca comportamientos sospechosos (bugs latentes) y para cada uno
dame la evidencia ejecutando un snippet; NO los corrijas.
Si algo está bien, dilo; no inventes hallazgos. No modifiques ningún archivo.
```

**Prompt 2c — plan con criterios de aceptación (spec ligera):**

```text
Con ese diagnóstico, propón un plan de al menos 5 refactorizaciones
ordenadas de menor a mayor riesgo, una por commit. Para cada una indica la
categoría del reto, qué smells resuelve y un criterio de aceptación
verificable (tests + regla de ruff que debe desaparecer). Considera que los
tests usan gestor.INVENTARIO y gestor.VENTAS directamente. Guárdalo en
docs/diagnostico.md.
```

**Resultado:** `docs/diagnostico.md` con 13 smells, 3 bugs latentes y un plan
de 10 pasos. Hallazgos que valió la pena verificar ejecutando código en vez de
solo leerlo:

- **B1:** un JSON válido sin la clave `"inventario"` hace que `cargar_datos`
  lance `KeyError` en vez de regresar `False`.
- **B2:** `cotizar` no aplica el descuento VIP (los tests fijan ese contrato,
  así que se documenta y no se cambia).
- **B3:** siguiendo el README (`cd src && python main.py`) el menú no
  encuentra `datos_ejemplo.json`, porque la ruta es relativa al directorio
  actual.

`git status` después de explorar: solo archivos nuevos de configuración y
documentación; ningún archivo de `src/` ni `tests/` cambió. ✅

## Paso 3 — Red de seguridad: pruebas de caracterización

**Prompt:**

```text
Antes de refactorizar, necesito una red de seguridad más fina que los 20 tests
originales. Crea un archivo NUEVO tests/test_caracterizacion.py (no toques los
existentes) con pruebas que fijen el comportamiento ACTUAL, no el que "debería"
ser:
- texto exacto del ticket con y sin descuento;
- fronteras de descuento (499.99, 500, 999.99, 1000) y todas las reglas VIP
  (minúsculas, prefijo, longitud < 3, None, umbral de 200);
- cada mensaje de ultimo_error;
- texto exacto de reporte_inventario y resumen_ventas; empates en mas_vendidos;
- formato del JSON guardado y carga de archivos corruptos/inexistentes;
- el menú completo simulando input() con monkeypatch y capsys.
Usa parametrize. Solo prueba comportamiento observable (nada de detalles
internos como contadorVentas, que vamos a renombrar). Corre la suite contra el
código original: todo debe pasar sin tocar src/.
```

**Resultado:** 36 pruebas nuevas → **56 passed**.

**Intento fallido y corrección:** la primera versión tenía un valor esperado
mal calculado a mano (999.99 → total 1151.99). Al correr contra el código
original falló (`1101.99 != 1151.99`): 999.99 − 50 = 949.99 → +16 % =
1101.99. En una prueba de caracterización **el código original es la fuente
de verdad**, así que se corrigió el valor esperado, no el código. Lección: las
expectativas generadas (por la IA o por mí) también se validan.

**Ajuste de prompt:** en la primera versión se usaba `gestor.contadorVentas`
en las aserciones; se reemplazó por el folio observable para que la prueba no
se rompa con el renombrado de la refactorización 5.

---

## Refactorización 1 — Eliminar código muerto

**Prompt:**

```text
Refactorización 1 de docs/diagnostico.md: elimina el código muerto.
Antes de borrar, demuestra con grep que nadie lo usa (src/ y tests/):
calcular_descuento_viejo, el exportar_txt comentado, reporteViejoCSV,
MODO_DEBUG, el import os sin usar de reportes.py y las declaraciones
"# -*- coding: utf-8 -*-" (innecesarias en Python 3). Quita también el
comentario histórico obsoleto del docstring de gestor.py.
No cambies nada más. Corre pytest y ruff y muéstrame el diff.
```

**Cambio:** −40 líneas en 4 archivos. Se eliminaron 3 funciones/bloques que
nadie llama, una variable global sin uso, un import sin usar y 4 declaraciones
de encoding.

**Justificación:** el código muerto confunde (¿se usa?, ¿hay que mantenerlo?),
aumenta la superficie a leer y aparece en búsquedas. "Por si acaso" ya lo
cubre git: cualquier versión anterior se puede recuperar del historial.

**Validación:** `grep` sin usos → `pytest` **56 passed** → `ruff` 20 → **13 errores**
(desaparecen F401, 4×UP009, N802 de `reporteViejoCSV` y un SIM115).

---

## Refactorización 2 — Reemplazar números mágicos por constantes de negocio

**Prompt:**

```text
Refactorización 2: reemplaza los números mágicos y literales de negocio por
constantes con nombre en MAYÚSCULAS, agrupadas al inicio de gestor.py en una
sección "Reglas de negocio" con un comentario breve por grupo:
IVA (0.16), umbrales y tasas de descuento por volumen (1000/0.10, 500/0.05),
regla VIP ("VIP", 0.02, 200), stock mínimo (5, usado en reportes.py dos
veces), encabezado/separador del ticket y formato de fecha.
Restricciones: NO cambies la estructura de los if ni el orden de las
operaciones (eso es la refactorización 3 y 4); solo sustituye literales, de
modo que los resultados de punto flotante sean idénticos. reportes.py debe
usar la constante de gestor, no redefinirla.
Al final, demuestra con grep que no quedan literales numéricos de negocio
fuera de las definiciones.
```

**Cambio:** 13 constantes nuevas (`TASA_IVA`, `UMBRAL_DESCUENTO_ALTO`,
`TASA_DESCUENTO_MEDIO`, `PREFIJO_CLIENTE_VIP`, `MONTO_MINIMO_VIP`,
`STOCK_MINIMO`, `NOMBRE_TIENDA`, …). `reportes.py` usa `gestor.STOCK_MINIMO`
en sus dos apariciones.

**Justificación:** `0.16` o `5` no dicen *qué* son; `TASA_IVA` y
`STOCK_MINIMO` sí. Además, cada regla vive en un solo lugar: si el IVA o el
umbral de stock bajo cambian, se modifica una línea (antes había que
encontrar 2–3 copias y era fácil olvidar una, como el `5` duplicado entre
`productos_stock_bajo` y `reporte_inventario`).

**Decisión de alcance:** se pidió explícitamente no reestructurar los `if`
en este paso. Mezclar "renombrar literales" con "cambiar la lógica" en un
mismo commit hace el diff difícil de revisar y, si un test falla, no sabes
cuál de los dos cambios lo rompió.

**Validación:** `grep` → solo quedan literales en las definiciones;
`pytest` **56 passed**; `ruff` **13** (sin cambio esperado: este paso no
atacaba reglas de ruff).

---

## Refactorización 3 — Extraer el cálculo de precios duplicado

**Prompt (con chain-of-thought para auditar la equivalencia):**

```text
Refactorización 3: registrar_venta y cotizar tienen copiado el cálculo de
descuento por volumen + IVA. Extráelo a funciones reutilizables en gestor.py:
- calcular_descuento_volumen(subtotal) -> descuento
- calcular_importes(subtotal, cliente=None) -> NamedTuple Importes(descuento,
  impuesto, total) que incluya la regla VIP.
Ambas funciones públicas deben usar calcular_importes.

Antes de escribir el código, razona paso a paso y muéstrame:
1. Las expresiones exactas que calculan el total en cada función hoy.
2. Por qué la versión extraída produce bit a bit el mismo float
   (ojo: cotizar hace base + base*IVA y registrar_venta round(base+impuesto)).
3. Qué pasa con cotizar y la regla VIP (no recibe cliente).
Restricciones: el descuento sin volumen debe seguir siendo el entero 0 (se
guarda en el JSON); no toques todavía la validación ni el ticket (paso 4);
conserva temporalmente los if anidados de la regla VIP (se aplanan en el
paso 4) para que el diff sea solo "mover código".
```

**Razonamiento verificado antes de aceptar:**

1. `cotizar`: `round(base + base * 0.16, 2)`; `registrar_venta`:
   `impuesto = base * 0.16; round(base + impuesto, 2)` → misma expresión,
   mismo float.
2. `cotizar` llama `calcular_importes(subtotal)` con `cliente=None` → la regla
   VIP no aplica, igual que antes (el hallazgo B2 se conserva a propósito).
3. `calcular_descuento_volumen` regresa `0` (entero) cuando no hay
   descuento, igual que el original; así el JSON guardado no cambia de `0` a
   `0.0`.

**Cambio:** nuevas `Importes` (NamedTuple), `calcular_descuento_volumen` y
`calcular_importes`. `cotizar` pasó de 10 líneas de cálculo a 2.
`registrar_venta` delega todo el cálculo en una línea.

**Justificación:** DRY. Antes, cambiar una tasa de descuento requería editar
dos funciones, y si se olvidaba una, la cotización y la venta darían montos
distintos (justo lo que vigila `test_cotizar_coincide_con_el_total_de_la_venta`).
Ahora es imposible que diverjan. Además, el cálculo de precios ya se puede
probar de forma aislada, sin inventario ni estado global.

**Efecto colateral positivo:** al extraer el bloque, `registrar_venta` bajó
de complejidad 12 a < 10 y desaparecieron **C901** y **SIM108** sin
atacarlas directamente.

**Validación:** `pytest` **56 passed**; `ruff` 13 → **11**.

---

## Refactorización 4 — Dividir `registrar_venta` y aplanar condicionales

**Prompt (restricciones explícitas de qué NO tocar):**

```text
Refactorización 4: registrar_venta sigue haciendo 5 cosas (validar, cobrar,
descontar stock, generar folio, armar ticket) y tiene dos pirámides de if
anidados (validación de 4 niveles y regla VIP de 4 niveles).
1. Extrae _validar_venta(codigo, cantidad) que regrese el mensaje de error o
   None, usando cláusulas de guarda en el MISMO orden de evaluación actual
   (codigo vacío → producto no existe → cantidad inválida → stock insuficiente).
2. Extrae es_cliente_vip(cliente) y reduce la regla VIP a un solo if.
3. Extrae _armar_ticket(venta, hubo_descuento) y _siguiente_folio().
4. Construye el dict de la venta con un literal en vez de 11 asignaciones.
Restricciones: el texto del ticket debe ser idéntico byte a byte (la
condición de la línea "Descuento" usa el descuento SIN redondear); el
diccionario de la venta conserva las mismas claves en el mismo orden;
cotizar conserva su propio orden de validación (no la unifiques: con
codigo "" hoy responde "producto no existe", no "codigo vacio").
Corre pytest y ruff; reporta la complejidad ciclomática antes/después.
```

**Cambio:**

| Antes | Después |
|-------|---------|
| `registrar_venta`: 1 función de ~70 líneas, complejidad 12 | `registrar_venta` (complejidad **2**) + `_validar_venta`, `es_cliente_vip`, `_armar_ticket`, `_siguiente_folio` |
| `if` anidados 4 niveles (validación) | 4 cláusulas de guarda planas |
| `if cliente != "" and ...: if len(...) >= 3: if cliente[0:3] == "VIP": if ...` | `if es_cliente_vip(cliente) and subtotal - descuento > MONTO_MINIMO_VIP:` |
| Ticket con 9 concatenaciones `t = t + ...` | Lista de líneas + f-strings + `"\n".join` |

**Justificación:** cada función tiene ahora una sola responsabilidad y un
nombre que la describe; `registrar_venta` se lee como un resumen del proceso.
Las cláusulas de guarda eliminan el "efecto flecha": el camino feliz queda al
final sin sangría y cada error se ve junto a su condición. `es_cliente_vip`
reemplaza 3 `if` y un slicing manual por `str.startswith`, que expresa la
intención directamente.

**Puntos de equivalencia revisados:**

- `cliente.startswith("VIP")` ≡ `len(cliente) >= 3 and cliente[0:3] == "VIP"`;
  `bool(cliente)` cubre `None` y `""`. Cubierto por los 7 casos VIP
  parametrizados (minúsculas, `XVIP`, `VI`, `None`, …).
- `f"{x}"` produce lo mismo que `str(x)` para floats → el ticket no cambia
  (lo verifican las pruebas de texto exacto).
- Se decidió **no** unificar la validación de `cotizar` con `_validar_venta`:
  cambiaría el mensaje de error para un código vacío. Queda como posible
  mejora futura que requiere decisión de negocio.

**Validación:** `pytest` **56 passed**; `ruff` 11 → **8** (desaparecen los
3 SIM102).

---

## Refactorización 5 — Nombres descriptivos y estilo PEP 8 consistente

**Prompt (few-shot con la tabla de renombres como ejemplo del estilo esperado):**

```text
Refactorización 5: renombra variables y funciones crípticas siguiendo las
convenciones de CLAUDE.md. Ejemplos del estilo que quiero:
  x       -> producto        (dict de un producto)
  temp2   -> coincidencias   (lista resultado de una búsqueda)
  aux     -> nuevo_stock     (según lo que realmente guarda)
  hacer_cosa -> formatear_moneda
Aplica el mismo criterio a TODO src/: contadorVentas, hayArchivo, d, f, k,
v, t, s, p, c, n, cant, cli, op, temp, par.
Restricciones: NO renombres agregarProducto ni buscarProducto (los usan los
tests) ni ninguna otra función pública de la lista de CLAUDE.md; no cambies
textos impresos, claves de diccionarios ni la lógica (salvo iterar con
.values() en vez de indexar por clave, que es el mismo recorrido). Busca y
actualiza todos los llamadores de cada nombre que cambies. Al final, haz un
grep de nombres de 1–2 letras para comprobar que no quedó ninguno.
```

**Cambio (tabla de renombres):**

| Antes | Después | Archivo |
|-------|---------|---------|
| `contadorVentas` | `contador_ventas` | gestor, almacen |
| `hayArchivo` | `existe_archivo` | almacen, main |
| `hacer_cosa` | `formatear_moneda` | reportes |
| `x` | literal `{...}` en `INVENTARIO[codigo]` | gestor |
| `aux` | `nuevo_stock`, `valor_total`, `unidades_por_codigo` | gestor, reportes |
| `temp2`, `temp` | `coincidencias`, `productos_bajos`, `ranking`, `respuesta` | gestor, reportes, main |
| `d`, `f`, `k`, `v` | `datos`, `archivo`, `codigo`, `venta` | almacen, reportes |
| `s`, `t` | `reporte`, `resumen`, `total`, `total_dia` | reportes |
| `c`, `n`, `p`, `s`, `cant`, `cli`, `op` | `codigo`, `nombre`, `precio`, `stock`, `cantidad`, `cliente`, `opcion` | main |
| `par[0]`, `par[1]` | desempaquetado `codigo, unidades` | main |
| comentarios `# hace X` | docstrings | todos |

**Justificación:** un nombre descriptivo elimina la necesidad de leer el
cuerpo para entender qué guarda una variable (`aux` guardaba 3 cosas
distintas en 3 funciones). PEP 8 exige `snake_case` para funciones y
variables; mezclar `contadorVentas` y `ultimo_error` en el mismo módulo obliga
a recordar cuál es cuál. Los comentarios de "qué hace" se volvieron
docstrings, que sí aparecen en `help()` y en el IDE.

**Problema encontrado y resuelto:** al renombrar en `mas_vendidos`, la línea
`unidades_por_codigo[codigo] = unidades_por_codigo[codigo] + venta["cantidad"]`
excedió 88 caracteres (**E501**, una regla que antes no fallaba). Se
resolvió con `+=`, que es equivalente. Lección: los nombres largos tienen un
costo y el linter lo detecta de inmediato; por eso se corre después de CADA
cambio.

**Validación:** `grep` de nombres cortos → solo falsos positivos
(f-strings, `\n`); `pytest` **56 passed**; `ruff` 8 → **6** (desaparecen
N802 y N816).

---

## Refactorización 6 — Manejo de errores en la persistencia (con TDD)

**Prompt 6a — prueba en rojo primero:**

```text
Refactorización 6 (almacen.py). Antes de cambiar código, escribe en un
archivo NUEVO tests/test_manejo_errores.py pruebas que reproduzcan estos
problemas y córrelas para confirmar que FALLAN con el código actual:
- JSON válido pero sin "inventario"/"ventas", o con tipos incorrectos
  (lista en lugar de objeto) -> debe regresar False, ultimo_error
  "archivo corrupto" y NO modificar el estado actual;
- cargar una ruta que es un directorio -> False, "no se pudo leer el archivo";
- guardar en una carpeta que no existe -> False, "no se pudo guardar el archivo";
- el menú debe avisar si no pudo guardar en vez de decir "Datos guardados".
Muéstrame el error real de cada prueba fallida.
```

**Resultado en rojo** (`docs/evidencia/r6_tdd_rojo.log`): 7 fallas, cada una
con una excepción no controlada (`KeyError`, `TypeError`,
`IsADirectoryError`, `FileNotFoundError`).

**Hallazgo nuevo gracias al TDD:** con `{"inventario": {}}` (falta
`"ventas"`) el código original **ya había vaciado `INVENTARIO`** cuando
lanzó el `KeyError` → dejaba el sistema a medio cargar. Y con
`{"inventario": [], "ventas": []}` regresaba `True` aceptando datos con un
tipo incorrecto. Ninguno de los dos estaba en el diagnóstico inicial: se
descubrieron al escribir la prueba.

**Prompt 6b — corrección:**

```text
Ahora corrige almacen.py con el cambio mínimo para que las pruebas pasen:
- usa `with open(...)` en guardar y cargar (sin el modo "r" redundante);
- captura excepciones concretas, nunca `except Exception`:
  json.JSONDecodeError -> "archivo corrupto"; OSError -> los mensajes nuevos;
- valida la estructura (dict con "inventario" dict y "ventas" list) ANTES de
  tocar el estado global;
- los mensajes de error como constantes del módulo;
- hayArchivo/existe_archivo: regresa la condición directamente;
- en main, imprime "Error: <motivo>" si guardar_datos regresa False.
Conserva los mensajes existentes ("el archivo no existe", "archivo corrupto").
```

**Iteración:** después de la primera corrección pregunté por casos que se
escaparan de las dos excepciones capturadas. Un archivo que no está en UTF-8
lanza `UnicodeDecodeError` (subclase de `ValueError`, no de `OSError`).
Se agregó la prueba (falló en rojo) y se capturó junto con `JSONDecodeError`.

**Cambio:** `almacen.py` reescrito: `with` en los dos `open`, excepciones
específicas, `_tiene_estructura_valida`, el estado global solo se modifica
cuando los datos ya son válidos, `update`/`extend` en lugar de copiar con
ciclos, `existe_archivo` en una línea. `main` reporta el error de guardado.

**Justificación:** `open` sin `with` deja el archivo abierto si ocurre una
excepción entre `open` y `close`. `except Exception` oculta errores de
programación y mezcla "archivo corrupto" con "disco lleno". Validar antes de
mutar hace la carga **atómica**: o se carga todo o no cambia nada.

**Cambio de comportamiento deliberado (documentado):** casos que antes
lanzaban una excepción ahora regresan `False` con un mensaje, como ya
prometía el docstring original ("Regresa False si el archivo no existe o
esta corrupto"). Ningún caso que antes funcionaba cambió.

**Validación:** 8 pruebas nuevas en verde → `pytest` **64 passed**
(`docs/evidencia/r6_tdd_verde.log`); `ruff` 6 → **2** (desaparecen 2×SIM115,
UP015, SIM103). Quedan I001 y C901 de `main.py` (refactorización 8).

---

## Refactorización 7 — Separar lógica de E/S en reportes y simplificar

**Prompt:**

```text
Refactorización 7 (reportes.py): las funciones reporte_inventario y
resumen_ventas imprimen Y regresan el texto. Haz que solo regresen el texto y
que main.py sea quien imprima (print(reportes.reporte_inventario())), de modo
que la salida en consola sea idéntica.
Aprovecha para simplificar con la biblioteca estándar:
- burbuja manual (tiene un TODO) -> sorted(..., reverse=True); conserva el
  orden de los empates (explica por qué sorted lo garantiza);
- acumuladores manuales -> sum() y Counter;
- concatenación s = s + ... -> lista de líneas + "\n".join;
- extrae tiene_stock_bajo(producto) porque la condición se repite 2 veces;
- buscarProducto en gestor.py -> list comprehension.
Restricción: el texto de los reportes debe ser idéntico byte a byte (incluido
"$0" con el inventario vacío). No toques el menú más allá de los 2 print.
```

**Verificación adicional (diferencial):** como las pruebas revisan el
contenido pero no cada salto de línea del menú, escribí
`docs/evidencia/comparar_menu.py`: corre el menú de la versión original
(`git worktree` del commit inicial) y de la refactorizada con la **misma
secuencia de 41 entradas** (ventas VIP, errores, cotización, número
inválido, todos los reportes, guardar) y compara las salidas.
Resultado: **206 líneas idénticas** (`docs/evidencia/r7_diff_menu.log`).

**Cambio:**

- `reporte_inventario` / `resumen_ventas`: ya no llaman `print`; `main`
  imprime el resultado.
- `mas_vendidos`: burbuja de 2 ciclos anidados → `Counter` + `sorted`.
  `sorted` es estable (también con `reverse=True`), así que los empates
  conservan el orden de primera venta, igual que la burbuja (que solo
  intercambiaba con `<` estricto). Cubierto por
  `test_mas_vendidos_default_tres_y_empates_en_orden_de_aparicion`.
- `total_vendido`, valor del inventario, total del día → `sum()`.
- Nuevos `tiene_stock_bajo` y `_linea_de_inventario`; `MARCA_STOCK_BAJO`
  como constante.
- `buscarProducto` → list comprehension.

**Justificación:** una función que imprime no se puede reutilizar para
escribir un archivo, enviarlo por correo o probarlo sin capturar stdout:
separar cálculo de presentación sigue el principio de responsabilidad única.
La biblioteca estándar (`sorted`, `sum`, `Counter`) está probada, es más
rápida (O(n log n) contra O(n²) de la burbuja) y dice la intención en una
línea.

**Validación:** `pytest` **64 passed**; diferencial del menú idéntico;
`ruff` **2** (sin cambio: solo quedan los de `main.py`).

---

## Refactorización 8 — Dividir el menú en funciones (tabla de despacho)

**Prompt:**

```text
Refactorización 8 (main.py): menu() tiene complejidad 18 por un if/elif de
8 ramas con la lógica de cada opción adentro.
- Extrae una función por opción (opcion_agregar_producto, opcion_cotizar...).
- Reemplaza el if/elif por un diccionario ACCIONES {"1": funcion, ...};
  la opción 8 (salir) se maneja aparte porque rompe el ciclo.
- Elimina la duplicación: el print("Error:", gestor.ultimo_error) aparece 3
  veces y int(pedir_numero(...)) otras 3.
- Las 8 líneas del menú como una tupla de constantes.
Restricción: la salida en consola debe ser idéntica byte a byte; verifícalo
con docs/evidencia/comparar_menu.py contra el commit inicial. Ordena los
imports (I001).
```

**Cambio:** `menu()` pasó de ~60 líneas y complejidad 18 a 12 líneas y
complejidad 3. Nuevas funciones `opcion_*` (una por opción),
`pedir_entero`, `mostrar_error`, `cargar_datos_iniciales`,
`imprimir_menu`, `guardar_y_salir`; constantes `OPCIONES_MENU`, `ACCIONES`,
`OPCION_SALIR`. Imports en orden alfabético.

**Justificación:** agregar una opción nueva ahora significa escribir una
función y añadir una entrada al diccionario, sin tocar el ciclo (principio
abierto/cerrado). Cada opción se puede leer y probar por separado. La tabla
de despacho es el patrón idiomático de Python para reemplazar un
`switch` largo.

**Validación:** `pytest` **64 passed**; diferencial del menú: **idéntico**;
`ruff check src` → **All checks passed! (0 errores)** 🎉
(`docs/evidencia/r8_ruff.log`).

---

## Refactorización 9 — Type hints en todas las funciones

**Prompt:**

```text
Refactorización 9: agrega type hints a TODAS las funciones de src/ con la
sintaxis de Python 3.10 (str | None, list[...], dict[...]).
- Define en gestor.py TypedDict Producto y Venta con las claves exactas que
  hoy se guardan en el JSON, y anota INVENTARIO, VENTAS y los globales.
- Los parámetros que hoy aceptan None (codigo, cantidad, cliente) deben
  reflejarlo en el tipo; no cambies las validaciones.
- Verifica con `mypy --strict --python-version 3.10` (corre primero para tener
  la línea base de errores). Si mypy pide cambiar código, propón la versión
  equivalente y explícame por qué es equivalente antes de aplicarla.
Restricción: cero cambios de comportamiento; las claves del dict de la venta
en el mismo orden.
```

**Cambio:** tipos `Producto` y `Venta` (TypedDict); todas las funciones de
los 4 módulos anotadas; `ACCIONES: dict[str, Callable[[], None]]`.
`mypy --strict`: **82 → 0 errores** (`docs/evidencia/r9_mypy.log`).

**Ajustes que pidió el verificador de tipos (y por qué son equivalentes):**

1. `es_cliente_vip`: `bool(cliente) and cliente.startswith("VIP")` →
   `cliente is not None and cliente.startswith("VIP")`. mypy no deduce de
   `bool()` que no es `None`. Para `""` la nueva versión evalúa
   `"".startswith("VIP")` → `False`, igual que antes.
2. El dict de la venta ahora se crea con `"ticket": ""` y después se llena,
   para cumplir con el `TypedDict` completo; la clave queda en la misma
   posición (última), así que el JSON guardado no cambia.
3. `assert codigo is not None and cantidad is not None` después de
   `_validar_venta`, solo para que el verificador sepa lo que la validación ya
   garantizó (nunca se dispara).

**Justificación:** los tipos documentan el contrato de cada función
(`registrar_venta` puede regresar `None`; `cotizar` regresa `float | None`) y
permiten que el IDE y mypy detecten errores antes de ejecutar. `Producto` y
`Venta` hacen explícito el esquema del JSON, que antes solo existía
implícitamente repartido en el código.

**Actualización de `CLAUDE.md` (v2):** se agregaron `mypy`, el
diferencial del menú, la regla de "validar antes de mutar" y los tipos del
proyecto, para que las siguientes sesiones los usen sin tener que repetirlo
en cada prompt.

**Validación:** `pytest` **64 passed**; `ruff` **0**; `mypy --strict` **0**;
diferencial del menú **idéntico**.

---

## Corrección de bugs B3 y B4 (commit `fix`, separado de las refactorizaciones)

> Esto **no** es una refactorización: cambia el comportamiento a propósito.
> Por eso va en un commit `fix:` aparte, con decisión explícita del autor
> ("sí lo corregimos") y con pruebas en rojo primero.

**Prompt:**

```text
Bug B3 del diagnóstico: el README dice `cd src && python main.py`, pero
ARCHIVO = "datos_ejemplo.json" es relativo al directorio actual, así que
desde src/ no encuentra los datos de ejemplo y al guardar crea otro archivo
en src/. Además revisa qué imprime el menú si el archivo existe pero está
corrupto.
1. Escribe primero pruebas en un archivo nuevo tests/test_ruta_datos.py y
   confirma que fallan.
2. Corrige con el cambio mínimo: ruta absoluta construida con pathlib a partir
   de __file__, y un mensaje de error si la carga falla.
3. Corre pytest, ruff y mypy, y prueba manualmente `cd src && python main.py`.
```

**Hallazgo B4 (nuevo, encontrado con el prompt anterior):**
`cargar_datos_iniciales` imprimía `"Datos cargados de ..."` aunque
`cargar_datos` regresara `False` (archivo corrupto).

**Rojo** (`docs/evidencia/fix_b3_b4_rojo.log`): 2 fallas
(`PosixPath('datos_ejemplo.json') != <raíz>/datos_ejemplo.json` y
"Datos cargados" presente con un archivo corrupto).

**Cambio:**

- `ARCHIVO = str(Path(__file__).resolve().parent.parent / "datos_ejemplo.json")`.
- Si la carga falla: `No se pudieron cargar los datos: <motivo>`.

**Prueba manual:** `cd src && python main.py` → `Datos cargados de
.../datos_ejemplo.json` ✅.
**Nota:** al elegir "Guardar y salir" el menú sobrescribe `datos_ejemplo.json`
de la raíz (era la intención original al ejecutarlo desde la raíz). Para no
modificar los datos de ejemplo del repo durante pruebas manuales, conviene
restaurarlos con `git restore datos_ejemplo.json`.

**Validación:** `pytest` **66 passed**; `ruff` **0**; `mypy --strict` **0**.
