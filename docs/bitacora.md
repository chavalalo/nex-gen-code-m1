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
