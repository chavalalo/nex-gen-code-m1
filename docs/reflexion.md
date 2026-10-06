# Reflexión final

## ¿Qué tan útil fue la IA para detectar y corregir problemas?

Me ayudó bastante, sobre todo con problemas que se podían comprobar directamente. Detectó y corrigió rápido los 20 errores de ruff y buena parte de los *code smells*, como código duplicado, condiciones anidadas y nombres poco claros.

Para mí, lo más útil fue poder verificar cada cambio con pruebas, el linter y un `git diff` pequeño. Eso me permitió revisar qué estaba haciendo y decidir si aceptarlo.

También me quedó claro que el resultado dependía mucho de cómo le pedía las cosas. Los prompts que mejor funcionaron fueron los que tenían límites concretos, como conservar el ticket idéntico byte a byte o respetar el orden de validación de `cotizar`. Pedirle simplemente que “mejorara el código” dejaba demasiado espacio para cambiar cosas que debían mantenerse.

## ¿Qué propuso la IA que yo no había notado?

- **Agregar pruebas de caracterización antes de refactorizar.** Los 20 tests originales no cubrían el texto del ticket, los límites de los descuentos ni la salida del menú. Las 36 pruebas adicionales ayudaron a comprobar que esos comportamientos se conservaran.
- **Revisar errores que no eran tan evidentes.** Encontró el `KeyError` al cargar un JSON incompleto (B1). También apareció un problema más delicado: la carga podía dejar el inventario parcialmente vacío antes de fallar (B5). Este último se descubrió al escribir la prueba en rojo; el diagnóstico inicial no lo había detectado.
- **Comparar la ejecución original con la refactorizada.** Se ejecutó el menú con las mismas 41 entradas y se compararon las 206 líneas de salida. Eso dio evidencia adicional de que el comportamiento se mantenía.
- **Usar `mypy --strict`.** Esta revisión adicional llevó a escribir `es_cliente_vip` de una forma más explícita.

## ¿En qué casos tuve que corregir o rechazar sugerencias?

Hubo varias situaciones donde tuve que revisar lo que proponía y poner límites:

- **Una prueba tenía mal calculado el resultado esperado.** La IA puso 1151.99 en lugar de 1101.99. Como la prueba falló contra el código original, se corrigió la prueba. Esto me dejó una lección clara: también hay que verificar las pruebas que genera la IA.
- **La documentación no reflejaba lo que había pasado.** En `CLAUDE.md` se decía que ciertos cambios se habían realizado durante las refactorizaciones 6 y 7, cuando se hicieron juntos al final. Se corrigió para mantener un historial preciso.
- **Quiso unificar las validaciones de `cotizar` y `registrar_venta`.** Parecía razonable, pero cambiaba el mensaje de error cuando el código estaba vacío. Lo rechacé porque ya implicaba modificar el comportamiento.
- **Propuso eliminar el estado global.** Podía ser una mejora de diseño, pero los tests utilizan directamente `gestor.INVENTARIO` y no se podían modificar. Se redujeron los riesgos de su uso, validando antes de modificar el inventario y evitando efectos secundarios en los reportes.
- **Detectó el problema de la ruta de datos (B3).** Se documentó y después decidí corregirlo en un commit `fix:` separado. Separar las correcciones de las refactorizaciones facilitó revisar el historial y entender el propósito de cada cambio.

## ¿Qué técnicas de prompting funcionaron mejor?

| Técnica (Clase 2) | Dónde la utilicé | Qué me aportó |
|---|---|---|
| Contexto persistente en `CLAUDE.md` | Todo el proceso | Evitó repetir las restricciones en cada prompt. El `deny` de `settings.json` reforzó la protección de los tests. |
| Restricciones explícitas | R2, R4 y R7 | Ayudaron a mantener cambios pequeños y dentro del alcance. |
| Solicitar una justificación verificable | R3 | Permitió comprobar que los resultados con floats se conservaran. |
| Few-shot | R5 | Con cuatro ejemplos de renombre, la IA aplicó el mismo criterio al resto. |
| Rol exigente y “no inventes hallazgos” | Diagnóstico | Produjo observaciones concretas, con evidencia y acciones claras. |
| TDD: prueba en rojo primero | R6 y correcciones | Permitió encontrar un bug que no apareció en el diagnóstico inicial. |
| Prompt chaining | Exploración | Dividir el trabajo en mapa, diagnóstico y plan permitió revisar cada etapa antes de avanzar. |

## ¿Qué aprendí sobre refactorizar con apoyo de IA?

1. **Lo que más atención requiere es verificar.** La IA puede generar los cambios rápido, pero la confianza vino de las 66 pruebas, ruff, mypy y la comparación de la salida del menú.
2. **Conviene mantener una idea por commit.** Separar los renombres de los cambios de lógica hizo más fácil revisar y, si era necesario, revertir cada modificación.
3. **La responsabilidad de decidir sigue siendo mía.** La IA propone soluciones, pero me corresponde evaluar si respetan el alcance y si un cambio de comportamiento tiene sentido.
4. **El contexto del proyecto debe actualizarse.** Incorporar en `CLAUDE.md` lo aprendido —validar antes de modificar el estado, comparar ejecuciones y usar mypy— ayudó a mantener criterios consistentes durante el trabajo.

**¿Qué haría distinto?** Agregaría las pruebas de caracterización del menú desde el inicio y automatizaría la comparación entre la versión original y la refactorizada mediante un hook. En este ejercicio la hice manualmente durante las refactorizaciones 7 a 9; tenerla desde antes habría facilitado la revisión.
