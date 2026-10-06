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
