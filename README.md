# Gestor de inventario y ventas — Tienda "La Esquina"

Aplicación de consola en Python para administrar el inventario y las ventas de
una tienda pequeña: alta de productos, ventas con descuentos por volumen,
descuento VIP e IVA, cotizaciones, alertas de stock bajo, reporte de más
vendidos y persistencia en JSON.

Este repositorio es la entrega del **Reto M1: Refactorización Asistida por
IA**. El código original funcionaba pero tenía muchos *code smells*; se
refactorizó con un agente de IA **sin cambiar su comportamiento observable**.

| Verificación | Antes | Después |
|--------------|-------|---------|
| `pytest` | 20 passed | **66 passed** (20 originales sin modificar + 46 nuevas) |
| `ruff check src` | 20 errores | **0** |
| `mypy --strict` (extra) | 82 errores | **0** |

## Requisitos previos

- Python **3.10 o superior**
- `pip` y `git`
- Dependencias (en `requirements.txt`): `pytest>=8.0`, `ruff>=0.6`
- Opcional: `mypy` para verificar los type hints

## Instalación

```bash
git clone https://github.com/chavalalo/nex-gen-code-m1.git
cd nex-gen-code-m1

python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar las pruebas

```bash
pytest            # o pytest -v para ver cada prueba
```

## Ejecutar el linter

```bash
ruff check src    # resultado esperado: All checks passed!
```

Verificación de tipos (opcional):

```bash
pip install mypy
cd src && mypy --strict .
```

## Usar la aplicación

```bash
cd src && python main.py      # también funciona: python src/main.py
```

Carga `datos_ejemplo.json` de la raíz del proyecto y lo sobrescribe al elegir
"Guardar y salir". Para restaurar los datos de ejemplo:
`git restore datos_ejemplo.json`.

## Estructura del proyecto

```
.
├── CLAUDE.md                 # Instrucciones y convenciones para el agente de IA
├── .claudeignore             # Archivos que el agente no debe leer
├── .claude/settings.json     # Permisos (deny) y hook que corre pytest tras cada edición
├── src/
│   ├── gestor.py             # Reglas de negocio, tipos Producto/Venta, productos y ventas
│   ├── almacen.py            # Guardar / cargar el estado en JSON
│   ├── reportes.py           # Reportes (solo arman texto, no imprimen)
│   └── main.py               # Menú de consola (única capa con input/print)
├── tests/
│   ├── test_gestor.py, test_almacen.py, test_reportes.py, conftest.py   # originales, sin cambios
│   ├── test_caracterizacion.py   # NUEVO: fija el comportamiento previo a refactorizar
│   ├── test_manejo_errores.py    # NUEVO: TDD de la refactorización 6
│   └── test_ruta_datos.py        # NUEVO: TDD de los fixes B3/B4
├── docs/
│   ├── diagnostico.md        # Code smells, bugs encontrados y plan priorizado
│   ├── bitacora.md           # Prompt, cambio, justificación y resultado de cada paso
│   ├── reflexion.md          # Aprendizajes
│   └── evidencia/            # Logs de pytest, ruff, mypy y script de comparación del menú
├── datos_ejemplo.json
├── pyproject.toml            # Configuración de ruff y pytest (sin cambios)
└── requirements.txt
```

## Refactorizaciones aplicadas

Cada una en su propio commit, con `pytest` y `ruff` después de cada cambio.
El detalle (prompts, justificación, resultados) está en
[`docs/bitacora.md`](docs/bitacora.md).

1. **Eliminar código muerto**: funciones sin uso, global e import sobrantes.
2. **Números mágicos → constantes** de negocio (`TASA_IVA`, `STOCK_MINIMO`, …).
3. **Extraer el cálculo de precios duplicado** (`calcular_importes`).
4. **Dividir `registrar_venta`** y aplanar condicionales con cláusulas de guarda.
5. **Renombrar** con nombres descriptivos en `snake_case`.
6. **Mejorar el manejo de errores** de la persistencia (`with`, excepciones concretas, carga atómica).
7. **Separar lógica de E/S** en reportes y simplificar con `sorted`, `sum`, `Counter`.
8. **Dividir el menú** en funciones por opción con tabla de despacho.
9. **Type hints** completos con `TypedDict` (`Producto`, `Venta`).

Además, en un commit `fix` aparte: ruta absoluta del archivo de datos y aviso
cuando la carga falla (bugs B3/B4 del diagnóstico).

## Reglas del reto que se respetaron

- No se modificaron los tests originales ni `pyproject.toml` (solo se
  **agregaron** archivos de prueba nuevos).
- `agregarProducto` y `buscarProducto` conservan su nombre (los usan los tests).
- El comportamiento observable se mantiene; se verificó además comparando la
  salida completa del menú contra la versión original
  (`docs/evidencia/comparar_menu.py`).
