# Reflexión final

## ¿Qué tan útil fue la IA para detectar y corregir problemas?

Muy útil para lo mecánico y verificable. Los 20 errores de ruff y la mayoría
de los *code smells* (duplicación, `if` anidados, nombres crípticos) los
detectó y corrigió rápido. Lo más valioso fue que cada cambio llegó
acompañado de su verificación: pruebas, linter y un `git diff` pequeño que se
podía revisar en minutos. Sin embargo, la utilidad dependió casi por completo
de cómo se pidieron las cosas. Los prompts que funcionaron mejor tenían
restricciones explícitas de qué **no** cambiar ("el ticket debe quedar
idéntico byte a byte", "conserva el orden de validación de `cotizar`").

## ¿Qué propuso la IA que yo no había notado?

- **Pruebas de caracterización antes de refactorizar.** Los 20 tests
  originales no revisan el texto del ticket, los límites de los descuentos ni
  la salida del menú. Sin esas 36 pruebas extra, varias refactorizaciones
  (sobre todo la del ticket y la de reportes) se habrían validado "a ciegas".
- **Bugs que no eran evidentes leyendo el código:** el `KeyError` con un JSON
  incompleto (B1), y sobre todo que la carga dejaba el inventario **vacío a
  medias** antes de fallar (B5). Este último apareció al escribir la prueba en
  rojo, no al leer el código: el TDD encontró algo que el diagnóstico no vio.
- **Verificación diferencial:** correr el menú original y el refactorizado con
  las mismas 41 entradas y comparar las 206 líneas de salida. Es más fuerte
  que cualquier prueba individual.
- `mypy --strict` como verificación adicional, que obligó a escribir
  `es_cliente_vip` de forma más explícita.

## ¿En qué casos tuve que corregir o rechazar sugerencias?

- **Un valor esperado mal calculado.** En una prueba de caracterización la IA
  calculó a mano un total (1151.99 en lugar de 1101.99). La prueba falló
  contra el código original y se corrigió la *prueba*, no el código. Lección:
  lo que genera la IA también se verifica, incluidas las expectativas.
- **Documentación imprecisa.** Al actualizar `CLAUDE.md`, el historial decía
  que los cambios se habían hecho en las refactorizaciones 6 y 7, cuando en
  realidad se aplicaron todos juntos al final. Se corrigió para que reflejara
  lo que realmente pasó.
- **Unificar la validación de `cotizar` con la de `registrar_venta`.** Parecía
  una mejora natural, pero cambiaba el mensaje de error con un código vacío.
  Se rechazó: es una decisión de negocio, no una refactorización.
- **Eliminar el estado global.** Era el cambio "ideal", pero los tests acceden
  a `gestor.INVENTARIO` directamente y no se pueden modificar. Se redujo su uso
  (validar antes de mutar, reportes sin efectos secundarios) sin romper la
  interfaz.
- **Corregir el bug de la ruta de datos (B3).** La IA lo detectó y lo
  documentó, pero no lo corrigió hasta que yo lo decidí, y lo hizo en un
  commit `fix:` separado. Mantener separados "refactorizar" y "cambiar
  comportamiento" fue clave para que el historial se pudiera revisar.

## ¿Qué técnicas de prompting funcionaron mejor?

| Técnica (Clase 2) | Dónde | Resultado |
|-------------------|-------|-----------|
| Contexto persistente en `CLAUDE.md` | Todas | No hubo que repetir "no toques los tests" en cada prompt; el `deny` de `settings.json` lo hizo obligatorio |
| Restricciones explícitas (qué NO hacer) | R2, R4, R7 | Diffs pequeños y sin efectos colaterales |
| Chain-of-thought para auditar | R3 | Antes de aceptar, se demostró que los floats eran idénticos |
| Few-shot | R5 | Con 4 ejemplos de renombre, el resto salió con el mismo criterio |
| Rol exigente + "no inventes hallazgos" | Diagnóstico | Tabla accionable con evidencia ejecutada, no elogios |
| TDD (prueba en rojo primero) | R6, fix | Encontró un bug que el diagnóstico no vio |
| Prompt chaining | Exploración | Mapa → diagnóstico → plan; cada paso verificable |

## ¿Qué aprendí sobre refactorizar con apoyo de IA?

1. **Generar ya no es el cuello de botella; verificar sí.** Cada
   refactorización tomó poco tiempo de escribir, pero su valor vino de la red
   de verificación: 66 pruebas, ruff, mypy y la comparación del menú.
2. **Una idea por commit.** Separar "renombrar literales" de "cambiar la
   lógica" (R2 contra R4) hizo que cada diff se pudiera revisar y revertir.
3. **El agente propone; yo decido.** Las decisiones que cambiaban el
   comportamiento (B3, la validación de `cotizar`) se tomaron fuera del flujo
   automático y quedaron documentadas.
4. **`CLAUDE.md` es un documento vivo.** Las lecciones del proceso (validar
   antes de mutar, el diferencial, mypy) se incorporaron para no tener que
   repetirlas.

**Qué haría distinto:** escribiría las pruebas de caracterización del menú
desde el primer minuto y automatizaría el diferencial como un hook, en lugar
de correrlo a mano en las refactorizaciones 7 a 9.
