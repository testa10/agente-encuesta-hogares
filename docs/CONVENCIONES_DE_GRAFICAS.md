# Convenciones de gráficas: justificar el tipo elegido, con fundamento estadístico

Este documento reúne las convenciones para justificar el tipo de gráfica
elegido en cada métrica — distinto de
[`METODOLOGIA.md`](METODOLOGIA.md), que reúne las reglas de rigor
estadístico y terminología. Las citas completas de cada fuente
mencionada acá están en [`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md).

**Cada gráfica del informe va acompañada de una justificación con
fundamento, no solo una frase intuitiva.** El público al que está
orientado este proyecto —académico, profesional, técnico o no técnico—
tiene que poder leer una cita, una fórmula o un gráfico y entender con
claridad qué significan, los números que respaldan el análisis, las
preguntas que lo originan, y la fuente estadística que justifica la
elección.

Cada celda de markdown con una métrica lleva, además de la pregunta guía:

1. **Por qué ese tipo de gráfica** — con el principio de visualización que
   lo respalda y, cuando aplique, el autor/fuente (Cleveland & McGill
   sobre comparación visual de formas; Tufte sobre slopegraphs; Knaflic,
   *Storytelling with Data*; Few sobre simplicidad — ver la guía de
   referencia más abajo con la cita concreta de cada patrón).
2. **La fórmula o definición exacta**, cuando la métrica la tenga (ej. una
   tasa, un índice compuesto, una razón) — no alcanza con describirla en
   palabras si existe una notación estándar. Ejemplo: "Razón de
   dependencia demográfica = (población de 0 a 14 + población de 65 y
   más) / población de 15 a 64 × 100".

**Esto aplica a todas las métricas, sin excepción — no hay métrica
"demasiado simple" como para saltearse la gráfica o la justificación.**
Un solo número o una diferencia entre dos grupos siguen necesitando su
gráfica (ver la entrada de "dumbbell chart" más abajo) y su fundamento,
igual que cualquier otra.

## Guía de referencia, con la fuente de cada patrón

- **Barras horizontales** (en vez de verticales): cuando las categorías
  tienen nombres largos (barrios, condiciones de vivienda) — se leen sin
  inclinar la cabeza. Fundamento: Cleveland & McGill (1984), sobre
  precisión en la percepción de posición vs. longitud en distintas
  orientaciones. El orden de las categorías (`categoryorder: "total
  ascending"`, ya usado en todo el proyecto) aplica además el principio
  Gestalt de continuidad — Ware, *Information Visualization: Perception
  for Design*: una secuencia ordenada se procesa como una sola tendencia,
  no como valores sueltos sin relación entre sí.
- **Barras agrupadas** (en vez de una sola barra con todo mezclado): para
  comparar el mismo dato entre 2 o más grupos lado a lado. Fundamento:
  principio de comparación directa (Few, *Show Me the Numbers*).
- **Líneas con marcadores, eje x numérico real (no categórico)**: para
  comparar la misma métrica entre corridas de distintos años que no son
  necesariamente consecutivos (ej. 2019, 2024, 2025 — ver
  `analysis.tasas_actividad_empleo_desempleo_por_anio` /
  `visualization.plot_tasas_por_anio`). El año tiene que quedar en su
  escala real, no parejo espaciado como una categoría — si no, un salto de
  5 años (2019→2024) se ve visualmente igual de "cerca" que uno de 1 año
  (2024→2025), y la línea sugiere una tendencia continua e interpolada
  entre años sin encuesta propia, que no se midió. Fundamento: mismo
  principio de precisión perceptiva de posición en una escala común de
  Cleveland & McGill (1984), aplicado al eje temporal en vez de solo al de
  categorías. Los marcadores explícitos en cada punto son parte de la
  misma idea: distinguen "acá hay una medición real" de "esto es una
  interpolación visual".
- **Nunca gráfico de torta con más de 3-4 categorías**: el ojo humano
  compara longitudes y posiciones con mayor precisión que ángulos
  (Cleveland & McGill, 1984) — con muchas porciones, un gráfico de torta
  se vuelve difícil de leer con precisión. Fundamento adicional: Cohen et
  al. (2016), sobre el límite de la atención perceptiva — más porciones
  que ese límite no se retienen como categorías distintas, se perciben
  como ruido.
- **Heatmap (mapa de calor)**: cuando se cruzan dos variables categóricas
  y lo que importa es la magnitud relativa de la concentración, no el
  valor exacto de cada celda. Fundamento: principio Gestalt de similitud
  — Ware, *Information Visualization: Perception for Design*: celdas de
  color parecido se agrupan visualmente solas, sin necesidad de leer cada
  valor individual.
- **Gráfico de puntos/dispersión ordenado**: cuando hay muchas categorías
  (ej. 62 barrios) y lo que importa es el orden y la distancia entre
  ellas, no compararlas de a pares.
- **Barras 100% apiladas**: cuando cada categoría se reparte en partes que
  suman exactamente 100% (ej. ocupados/desocupados/inactivos) — deja ver
  la composición completa en una sola barra por grupo. Fundamento: Wilke,
  *Fundamentals of Data Visualization*, capítulo sobre proporciones.
- **Barras de diferencia** (puntos porcentuales, no barras apiladas):
  cuando se comparan varios grupos que NO suman 100% entre sí — apilarlos
  daría una impresión de proporción que no existe (ver
  `docs/METODOLOGIA.md`, sección 2; mismo fundamento de Wilke sobre
  proporciones que la entrada anterior, aplicado al caso donde no
  corresponde apilar).
- **Nunca agregar a una gráfica un elemento que no aporte información**
  (grillas de fondo densas, bordes gruesos, colores decorativos sin
  significado, sombras): cada elemento visual compite por la atención de
  quien lee, así que solo debería estar ahí lo que ayuda a leer el dato.
  Fundamento: Tufte, principio de "data-ink ratio" (*The Visual Display
  of Quantitative Information*, 1983).
- **Dumbbell chart (o "barbell"/slopegraph)** — dos puntos por categoría,
  conectados por una línea, en vez de una barra con la resta ya calculada:
  para cualquier métrica que compare **dos grupos específicos** dentro de
  una variable más amplia (ej. "quintil 1 vs. quintil 5", "comunicación
  informal vs. denuncia formal"). Es la práctica recomendada en la
  literatura de visualización por sobre una barra de diferencia simple,
  porque conserva los dos valores reales además de la brecha entre ellos
  — una barra de diferencia sola oculta si la brecha viene de un valor
  alto contra uno bajo, o de dos valores intermedios cercanos. Fuente:
  Tufte (slopegraphs, años 80); Knaflic, *storytellingwithdata.com*,
  "More on slopegraphs" (2014); Nightingale/Data Visualization Society,
  "Beyond the Bar: Alternative Methods for Visualizing Two Points of
  Change". Implementación: `visualization.plot_dumbbell`.
- **Comparar cualquier métrica del catálogo entre dos años (ej. "2024 vs.
  2025")**: es el mismo caso que el punto anterior — "año" es un grupo
  específico como cualquier otro, no hace falta código nuevo. Es una
  opción de primera clase del catálogo (`formularios.plantilla_catalogo`,
  campo "¿Comparar estas métricas con otro año?"), no algo que la persona
  tenga que pedir escribiéndolo en "otra métrica". Calcular la métrica
  una vez por año con la función que ya exista (la misma que usa el
  informe de un solo año), cruzar las dos tablas con
  `analysis.diferencia_entre_tablas` y graficar con
  `visualization.plot_dumbbell` — confirmado en una corrida real
  (Seguridad y Victimización, 41-47, comparando 2024 con 2025): se
  resolvió entero sin escribir ninguna función nueva. Para 3 años o más,
  o cuando lo que importa es la evolución en el tiempo más que un
  "antes/después" puntual, usar en cambio el patrón de líneas con eje
  numérico real de más arriba (ver
  `analysis.tasas_actividad_empleo_desempleo_por_anio` como ejemplo ya
  resuelto para Empleo).

Si una gráfica no encaja claramente en ninguno de estos patrones, aplicar
el mismo criterio general: identificar el principio de percepción visual
o de rigor estadístico que está en juego, y citarlo — nunca elegir el
tipo de gráfica "porque sí" o "porque se ve bien".
