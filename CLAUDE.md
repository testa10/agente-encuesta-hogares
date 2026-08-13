# Instrucciones para la sesión principal de Claude Code

Este proyecto tiene un único agente especializado: `encuesta-hogares` (ver
`.claude/agents/encuesta-hogares.md`). Cualquier pedido relacionado con
analizar la Encuesta Continua de Hogares (ECH) del INE Uruguay — sin
importar cuánto detalle traiga el pedido original ("hacé el análisis
2024", "análisis estándar", "agregá una pregunta sobre X" — se delega
entero a ese agente.

**Al delegarle la tarea, pasale el pedido del usuario tal cual lo
escribió, palabra por palabra, sin resumir, sin completar el año, sin
interpretar qué quiso decir con "estándar", y sin agregar contexto
adicional de tu parte.** No armes un resumen de alcance ni una lista de
lo que entendiste — eso es exactamente lo que el agente tiene que volver
a preguntar él mismo, a través de su propio formulario, y un resumen ya
armado de tu parte compite con esa regla en vez de ayudarla.

No respondas vos ninguna pregunta de alcance (año, métricas, formato de
salida) antes de delegar — todas esas preguntas las hace el agente con
sus propios formularios visuales.

## Mantenimiento del proyecto (para vos, sesión principal — no para el agente)

**Una sola copia** (esta, en Documents) — hasta la versión 0.3.0 existía
también una copia aparte para desarrollo, se eliminó porque generaba
riesgo real de perder trabajo sin publicar (pasó de verdad: una función
nueva en `analysis.py` quedó casi dos días sin subir a GitHub). Ahora se
desarrolla, se prueba y corre el agente todo en el mismo lugar — commiteá
y publicá directo desde acá.

El agente `encuesta-hogares` sigue sin permiso de usar git (ver
`.claude/settings.json`). Si escribe código nuevo y reutilizable durante
una corrida real (ej. una función para una métrica propuesta por el
usuario), ese código queda en el disco pero sin commitear — **antes de
dar por cerrada una sesión de trabajo** (sobre todo si el usuario
mencionó haber corrido el agente), corré:

```bash
./run_python.bat tools/verificar_sincronizacion.py
```

Si encuentra diferencias contra `origin/main`, revisalas — puede ser
trabajo real del agente sin publicar (commiteálo y hacé `git push`) o
simplemente que esta copia está atrasada respecto a lo último subido.

**Antes de publicar un cambio en `analysis.py`/`preprocessing.py` que
toque cómo se leen o combinan los datos**, corré también:

```bash
./run_python.bat tools/validar_con_datos_reales.py
```

Ejercita el pipeline completo contra los datos reales que haya en `data/`
(si hay alguno) — atajó bugs reales esta sesión que los tests con datos
sintéticos no detectaban (columnas de vivienda que cambian de 12 a 4 según
el año, formato .sav vs .csv, base nacional vs. filtrada a Montevideo).
