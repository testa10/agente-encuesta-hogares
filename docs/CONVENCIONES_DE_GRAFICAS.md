# Convenciones de gráficas: justificar el tipo elegido, con fundamento estadístico

Se separó de [`METODOLOGIA.md`](METODOLOGIA.md) por ser un tema propio y
consultado seguido (cada métrica nueva pasa por acá) — mantenerlo aparte
evita que quien solo necesita elegir un tipo de gráfica tenga que leer
todo el resto de las reglas de rigor estadístico para encontrarlo. Las
citas completas de cada fuente mencionada acá están en
[`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md).

**Cada gráfica del informe va acompañada de una justificación con
fundamento, no solo una frase intuitiva.** El público de este informe es
académico y profesional — "no técnico" no significa "sin formación": es
gente que puede leer una cita o una fórmula y que la va a valorar como
señal de que los números tienen sentido, no como ruido innecesario. Por
eso, a diferencia de un criterio anterior de este proyecto (ya
descartado), acá **sí correspondía citar la fuente y, cuando la métrica
lo amerite, mostrar la fórmula o definición exacta** — no ocultarla.

Cada celda de markdown con una métrica lleva, además de la pregunta guía:

1. **Por qué ese tipo de gráfica** — con el principio de visualización que
   lo respalda y, cuando aplique, el autor/fuente (Cleveland & McGill
   sobre comparación visual de formas; Tufte sobre slopegraphs; Knaflic,
   *Storytelling with Data*; Few sobre simplicidad — ver la chuleta más
   abajo con la cita concreta de cada patrón).
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

## Chuleta de referencia, con la fuente de cada patrón

- **Barras horizontales** (en vez de verticales): cuando las categorías
  tienen nombres largos (barrios, condiciones de vivienda) — se leen sin
  inclinar la cabeza. Fundamento: Cleveland & McGill (1984), sobre
  precisión en la percepción de posición vs. longitud en distintas
  orientaciones.
- **Barras agrupadas** (en vez de una sola barra con todo mezclado): para
  comparar el mismo dato entre 2 o más grupos lado a lado. Fundamento:
  principio de comparación directa (Few, *Show Me the Numbers*).
- **Nunca gráfico de torta con más de 3-4 categorías**: el ojo humano
  compara longitudes y posiciones con mayor precisión que ángulos
  (Cleveland & McGill, 1984) — con muchas porciones, un gráfico de torta
  se vuelve difícil de leer con precisión.
- **Heatmap (mapa de calor)**: cuando se cruzan dos variables categóricas
  y lo que importa es la magnitud relativa de la concentración, no el
  valor exacto de cada celda.
- **Gráfico de puntos/dispersión ordenado**: cuando hay muchas categorías
  (ej. 62 barrios) y lo que importa es el orden y la distancia entre
  ellas, no compararlas de a pares.
- **Barras 100% apiladas**: cuando cada categoría se reparte en partes que
  suman exactamente 100% (ej. ocupados/desocupados/inactivos) — deja ver
  la composición completa en una sola barra por grupo.
- **Barras de diferencia** (puntos porcentuales, no barras apiladas):
  cuando se comparan varios grupos que NO suman 100% entre sí — apilarlos
  daría una impresión de proporción que no existe (ver
  `docs/METODOLOGIA.md`, sección 2).
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

Si una gráfica no encaja claramente en ninguno de estos patrones, aplicá
el mismo criterio general: identificá el principio de percepción visual
o de rigor estadístico que está en juego, y citalo — nunca elijas el tipo
de gráfica "porque sí" o "porque se ve bien".
