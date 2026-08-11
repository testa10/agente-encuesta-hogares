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
