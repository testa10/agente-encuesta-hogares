# Metodología: cómo se construyó (y se debe mantener) este análisis

Este documento resume todo lo aprendido durante la construcción del análisis
original (ECH 2019, Montevideo) para que se pueda reproducir con la misma
calidad en cualquier año futuro. No es teoría abstracta: cada regla acá
existe porque en el proyecto original encontramos un problema concreto,
lo corregimos, y queremos evitar repetirlo.

## 1. Estructura estándar del análisis

El análisis se organiza siempre en las mismas grandes partes (los números de
sección pueden variar si se agregan o quitan preguntas, pero el orden lógico
se mantiene):

1. **Preparación de datos**: cargar Hogares y Personas, filtrar a Montevideo,
   clasificar nivel económico. Es la única parte que se genera siempre —
   toda infraestructura, sin contenido temático propio.
2. **Panorama general de TV cable**, **Distribución por barrio** y
   **Composición de los hogares con y sin cable** — a diferencia del punto
   1, **estas tres NO se generan siempre**: son contenido del bloque
   "Brecha Digital" (ver `.claude/agents/encuesta-hogares.md`, paso 5.2), así
   que solo se arman si el usuario eligió ese bloque en el paso 3.5.
   "Territorio" ya no depende de esto — su índice de desarrollo
   territorial es infraestructura propia. No asumir que a todos les
   interesa la tecnología es la misma razón por la que el catálogo dejó de
   incluir esos bloques por defecto — aplicarla acá y no en el catálogo
   hubiera sido inconsistente.
3. **Bloques elegidos**, cada uno organizado como "Entorno" temático propio
   (Brecha Digital, Hogares, Territorio, Vivienda, y — si corresponde —
   Seguridad Alimentaria, Empleo, Seguridad y Victimización): el usuario
   elige qué bloques quiere (paso 3.5) y qué métricas de cada uno (paso 4).
4. **Resumen analítico final**, organizado por los mismos bloques que
   terminó teniendo el informe (nunca por una lista fija de Entornos), con
   cifras reales (nunca estimadas) y redactado para un lector no técnico.

Cada subsección nueva sigue el mismo patrón: **una pregunta guía en
markdown, antes de la celda de código que la responde.** Nunca al revés.

## 2. Reglas de rigor estadístico (no negociables)

Estas reglas surgieron de una revisión hecha "como si fuéramos un experto en
estadística y censos" sobre el análisis original, que llevó a eliminar
secciones enteras. Antes de agregar una gráfica o sección nueva, revisala
contra esta lista:

- **Falacia ecológica**: no mezclar el nivel de agregación. Si una variable
  describe un barrio (ej. el % de abonados de todo el barrio), no se puede
  usar para sacar conclusiones sobre hogares individuales de ese barrio, ni
  viceversa. Si se cruzan variables de distinto nivel (hogar vs. barrio vs.
  persona), **aclarrarlo explícitamente en el texto y en los títulos de las
  gráficas** (ver el caso de "nivel de suscripción del barrio" en la
  sección 4).
- **Sesgo de mediador/selección**: no estratificar por una variable que es,
  en parte, resultado de la variable que se está explicando. Ejemplo real
  que se eliminó del proyecto original: cruzar "ingreso del hogar" con
  "nivel de suscripción del barrio" mezclaba causa y efecto de forma
  confusa y no aportaba una conclusión clara — se sacó toda la sección.
- **Celdas chicas**: si un grupo tiene muy pocos casos, la comparación no es
  confiable. Antes de publicar una gráfica nueva agrupada por algo, corré
  `analysis.grupos_con_muestra_chica(df, columna_grupo)` sobre el
  dataframe sin agrupar — si devuelve algún grupo, aclará en el texto que
  esa estimación puntual tiene poca base muestral (umbral: n=30).
- **Ponderación por muestreo — no negociable, no es "un detalle técnico".**
  Toda estadística de Hogares/Personas (pobreza, hacinamiento, tipos de
  hogar, jefatura, razón de dependencia, vivienda, territorio, brecha
  digital) se calcula ponderada por `ponderador_hogar` (columna `pesoano`
  en 2019, `W_ANO` desde 2024 — mismo ponderador, verificado idéntico para
  todas las personas de un mismo hogar). Esto se agregó recién en esta
  versión: antes, todo lo que no fuera FIES/Empleo/Victimización (que ya
  traían su propio ponderador de módulo) se calculaba como proporción
  simple sobre la muestra — un sesgo real, no cosmético: con datos de
  2019, la pobreza de Montevideo da 6.71% sin ponderar contra 8.14%
  ponderada correctamente, y a nivel nacional 4.79% contra 5.87% — una
  diferencia de casi 1.1 puntos porcentuales, suficiente para cambiar una
  conclusión. Nunca calcules una proporción/media/mediana de Hogares con
  `.mean()`/`.median()`/`.value_counts()` simple — usá los helpers ya
  armados para esto: `analysis.pct_ponderado`/`pct_ponderado_por` (%),
  `media_ponderada_por` (promedio), `proporcion_ponderada` (value_counts
  ponderado), `mediana_ponderada` (mediana). Si agregás una función nueva
  de Hogares/Personas y no vas a ponderarla, dejá explícito por qué en el
  docstring — no que se te haya olvidado.
- **Límite conocido: sin intervalos de confianza ni test de significancia.**
  Los microdatos públicos del INE no incluyen las variables de diseño
  muestral (conglomerado/estrato) necesarias para calcular un error
  estándar correcto en un diseño muestral complejo — calcularlo asumiendo
  muestreo aleatorio simple (la única opción sin esas variables)
  subestimaría el error real y daría una precisión falsa, peor que no
  mostrar nada. Por eso ningún número de este proyecto lleva margen de
  error ni "diferencia estadísticamente significativa": son estimaciones
  puntuales ponderadas, no inferencia con incertidumbre cuantificada. Si
  alguna vez el INE publica las variables de diseño, esto se puede
  reconsiderar — hasta entonces, no simules una precisión que no se puede
  respaldar.
- **Correlación vs. causación**: el lenguaje debe ser siempre observacional
  ("los hogares con X tienen más probabilidad de Y"), nunca causal ("X
  provoca Y"), salvo que el diseño del estudio lo permita (no es el caso
  acá: es una encuesta transversal).
- **Proporciones que no suman 100% entre sí no se apilan.** Si dos barras
  representan porcentajes calculados sobre bases distintas (ej. "% de
  ocupados" dentro de "hombres" y dentro de "mujeres"), no se pueden
  combinar en un gráfico de barras apiladas — eso implica una relación
  parte-todo que no existe. Para comparar varias categorías de este tipo a
  la vez, preferí barras agrupadas (cada valor real, lado a lado) — ver
  `tasas_por_grupo()` / `plot_tasas_por_grupo()` como ejemplo ya
  resuelto — y, para comparar solo dos grupos puntuales, el dumbbell chart
  de la sección 9. En ambos casos se muestran los valores reales, nunca
  solo la resta ya calculada.

## 3. Reglas de terminología y claridad

- **Nunca nombrar una variable de forma que sugiera algo que no mide.**
  Caso real: la variable de estrato de muestreo del INE (`estred13`) se
  llamaba inicialmente "nivel de ingreso" en el código y el notebook, pero
  en realidad es una clasificación geográfica/socioeconómica usada para
  diseñar la muestra, no una medición directa del ingreso del hogar (que sí
  existe como variable aparte, `YSVL`/`ingreso_hogar`). Se renombró a
  "nivel económico" en todo el proyecto, con una aclaración de origen en la
  sección 1 del notebook.
- **Si una variable describe al barrio y no al hogar (o a la persona y no
  al hogar), decilo en el título de la gráfica**, no solo en el texto de
  arriba — quien mira solo la gráfica también tiene que poder entenderla.
- **No amontonar preguntas ni encabezados con dos puntos y texto extra.**
  Un encabezado es un encabezado; la pregunta que responde la sección va en
  el párrafo de abajo, no pegada al título.
- **Cada gráfica necesita una razón de ser.** Si al mirar una gráfica no se
  puede explicar en una frase qué pregunta responde o qué decisión ayuda a
  tomar, no se incluye. (No hace falta *justificar por escrito* el tipo de
  gráfica elegido en el notebook — sí hace falta que la gráfica tenga
  sentido.)
- **No dejar huecos de numeración ni referencias a secciones eliminadas.**
  Cuando se borra o renombra una sección, revisar todo el notebook (y el
  README) buscando menciones cruzadas que hayan quedado colgando.

## 4. Ejemplo real de ambigüedad ya resuelta: "nivel de suscripción"

Puede volver a pasar con otras variables, así que vale la pena documentar el
patrón: `nivel_suscripcion` es una clasificación por **cuartiles del % de
abonados de todo un barrio** (se calcula en la sección de distribución por
barrio), que después se le asigna a **cada hogar de ese barrio**, tenga o
no tenga la tecnología. Cruzarla con `tipo_abonado` (que sí es del hogar)
puede producir combinaciones que a primera vista parecen contradictorias
("Sin cable" + "barrio de Alta suscripción"), pero son válidas: describen un
hogar que es la excepción dentro de su barrio. La solución no es cambiar el
cálculo — es dejar clarísimo en el título y el texto que una variable es del
barrio y la otra del hogar.

## 5. Flujo de verificación (seguir siempre, sin saltarse pasos)

1. Escribir o editar el código en `src/encuesta_hogares/` (nunca directamente
   en el notebook si la lógica se puede poner en una función reutilizable
   y testeable).
2. Si agregás una función nueva en `analysis.py`, agregale un test en
   `tests/`.
3. Correr `pytest -q` y confirmar que todo pasa.
4. Editar el notebook con `nbformat` (no pegar JSON a mano).
5. Re-ejecutar el notebook completo, cronometrando cuánto tarda (para
   poder ver después, con `tools/resumen_sesiones.py`, si el cuello de
   botella real está acá o en otro paso) — en vez de invocar `jupyter
   nbconvert` directo por Bash, envolvelo con `bitacora.medir_comando()`:
   ```python
   import sys
   from encuesta_hogares import bitacora
   bitacora.medir_comando("ejecucion_notebook", [
       sys.executable, "-m", "jupyter", "nbconvert",
       "--to", "notebook", "--execute", "--inplace", "<notebook>.ipynb",
   ])
   ```
6. Verificar que ninguna celda de código haya quedado con `output_type ==
   "error"`.
7. Para cualquier gráfica nueva o modificada, extraer el PNG embebido del
   output de la celda y mirarlo — no asumir que "si no tiró error, se ve
   bien". Revisar que los números y el orden de las barras tengan sentido.
   **Si hay que borrar PNGs viejos del scratchpad antes de una nueva
   extracción, nunca uses un comodín en `rm` (ej. `rm -f celda_*.png`)** —
   la herramienta de Bash rechaza los patrones glob en operaciones de
   escritura/borrado, y esa aprobación interrumpe una corrida que se
   supone que no necesita supervisión. Hacé el borrado con Python
   (`pathlib.Path(carpeta).glob("celda_*.png")` y `.unlink()` en un bucle,
   dentro del mismo script que ya estás corriendo con `run_python.bat`) —
   mismo criterio que ya se sigue para editar el notebook (nbformat, nunca
   JSON a mano) y para correr comandos largos (`bitacora.medir_comando`,
   nunca `jupyter nbconvert` suelto).
8. Generar el informe HTML sin código (para gente no técnica):
   - Copiar el notebook, filtrar del output los mensajes `stderr` de tipo
     `stream` (son warnings inofensivos de matplotlib, no errores reales).
   - Igual que en el paso 5, envolvé la conversión con
     `bitacora.medir_comando("generacion_html", [sys.executable, "-m", "jupyter", "nbconvert", "--to", "html", "--no-input", "<copia>.ipynb"])`
     en vez de invocar `jupyter nbconvert` directo.
   - Corregir el `<title>` del HTML generado (por defecto queda con el
     nombre del archivo).
   - **El HTML final se guarda siempre como exactamente
     `notebooks/Informe_ECH_{AÑO}.html`** — mismo criterio que el nombre
     del notebook (paso 5.2 de `.claude/agents/encuesta-hogares.md`): sin
     sufijos ni variantes, para que dos años nunca choquen y el respaldo
     de abajo se dispare solo cuando de verdad se repite el mismo año.
   - **Antes de guardar el HTML final con ese nombre**, llamá a
     `entrega.respaldar_si_existe(ruta_html_final)` — si ya existía un
     informe de una corrida anterior para ese mismo año (ej. alguien
     corrió el mismo año dos veces), queda como "Informe_ECH_{AÑO}
     (anterior).html" en vez de perderse en silencio.
9. Generar el informe PDF profesional a partir de ese HTML, y copiarlo a la
   carpeta de Descargas del usuario (ver sección 6). Este paso es parte del
   resultado estándar que se le entrega al usuario — no es opcional ni algo
   que solo se hace si lo pide.
10. Publicar (ver sección 7).

## 6. Generación del informe PDF profesional

El objetivo es un PDF con aspecto de informe real (portada, tipografía
cuidada, gráficas que nunca se cortan ni se salen de la hoja), no una
impresión cruda del notebook. Se arma en base al HTML sin código del paso 8,
así no hay que mantener dos fuentes de verdad.

**Por qué no usar `jupyter nbconvert --to pdf`:** ese exportador depende de
una instalación de LaTeX completa, que es pesada, lenta de instalar y
frágil en Windows — mala idea para un usuario no técnico. En su lugar se
usa Chromium sin interfaz (a través de Playwright) para "imprimir" el HTML
a PDF, igual que haría un navegador común.

Pasos:

1. Asegurate de tener Playwright listo (una sola vez por instalación):
   `playwright install chromium`. Si no está, instalalo vos mismo con Bash
   — es la descarga de un componente del propio paquete Python que ya está
   en las dependencias del proyecto, no un programa externo nuevo que el
   usuario tenga que gestionar.
2. Tomá el HTML sin código ya generado (paso 8 de la sección 5) y anteponé
   al `<body>` un bloque de portada:
   ```html
   <div class="portada">
     <h1>Encuesta Continua de Hogares — Informe {AÑO}</h1>
     <div class="subtitulo">Penetración tecnológica en hogares de Montevideo</div>
     <div class="meta">Generado el {fecha de hoy}</div>
   </div>
   ```
3. Inyectá `docs/informe_estilo.css` dentro de un `<style>` en el `<head>`
   del HTML (o enlazalo con `<link>` si vas a mantener el archivo al lado).
   Esa hoja de estilos ya define tamaño A4, márgenes, tipografía, y sobre
   todo `max-width`/`max-height` + `page-break-inside: avoid` en las
   imágenes — es lo que evita que una gráfica quede cortada entre dos
   páginas o se salga del ancho de la hoja. No la reinventes ni la
   simplifiques: cada regla ahí resuelve un problema real de paginación.
4. Convertí ese HTML a PDF con Playwright (script corto, vía Bash con
   `python -c` o un archivo temporal), cronometrando el bloque con
   `bitacora.medir()` y respaldando el PDF anterior si existía:
   ```python
   from playwright.sync_api import sync_playwright
   from encuesta_hogares import bitacora, entrega

   entrega.respaldar_si_existe(ruta_pdf_salida)
   with bitacora.medir("conversion_pdf"):
       with sync_playwright() as p:
           browser = p.chromium.launch()
           page = browser.new_page()
           page.goto(f"file:///{ruta_html_absoluta}")
           page.pdf(
               path=ruta_pdf_salida,
               format="A4",
               print_background=True,
               display_header_footer=True,
               header_template="<span></span>",
               footer_template=(
                   '<div style="font-size:8pt; width:100%; text-align:center; '
                   'color:#8b949e;">Página <span class="pageNumber"></span> '
                   'de <span class="totalPages"></span></div>'
               ),
               margin={"top": "20mm", "bottom": "16mm", "left": "18mm", "right": "18mm"},
           )
           browser.close()
   ```
   Usá `header_template` / `footer_template` (no CSS `@page { @bottom-center }`)
   para la numeración de página: Chromium no soporta las cajas de margen de
   `@page` en su motor de impresión, solo esas plantillas HTML de Playwright.
5. **El nombre del archivo es siempre exactamente `Informe_ECH_{AÑO}.pdf`**
   (el año elegido en el paso 1, sin ningún sufijo ni variante — nada de
   `_personalizado`, `_v2`, una descripción del contenido, etc.). No es
   solo una cuestión de prolijidad: es lo que hace que dos años distintos
   nunca choquen entre sí, y que `entrega.respaldar_si_existe()` (ver
   paso 8 de la sección 5) respalde correctamente solo cuando se repite
   el mismo año.
6. Copiá el PDF a la carpeta de Descargas del usuario, además de dejarlo en
   el proyecto — respaldando ahí también el que hubiera de una corrida
   anterior, por la misma razón del paso 8 de la sección 5:
   ```python
   from pathlib import Path
   import shutil
   from encuesta_hogares import entrega
   ruta_descargas = Path.home() / "Downloads" / "Informe_ECH_{AÑO}.pdf"
   entrega.respaldar_si_existe(ruta_descargas)
   shutil.copy(ruta_pdf_salida, ruta_descargas)
   ```
   `Path.home() / "Downloads"` funciona igual en Windows y en Mac. Si esa
   carpeta no existe (poco común, pero puede pasar), avisale al usuario en
   vez de fallar en silencio.
7. Abrí el PDF resultante (o al menos revisá la cantidad de páginas y que
   el tamaño de archivo sea razonable) antes de darlo por terminado — no
   asumas que la conversión salió bien solo porque no tiró error.

## 7. Publicación (no es parte del flujo del agente)

El agente **nunca** publica nada en GitHub ni se lo ofrece al usuario —
ver el paso 9 de `.claude/agents/encuesta-hogares.md`. La mayoría de
quienes usan el agente no tienen permiso de escritura sobre el
repositorio, y mezclar código puntual de sesiones de usuario con el
repositorio compartido lo llenaría de funciones muy específicas que no le
sirven a nadie más.

Decidir qué código o qué métrica de una sesión vale la pena incorporar al
catálogo permanente es una decisión del dueño del proyecto — pero no una
tarea que tenga que hacer a mano: se lo puede pedir directamente al
agente por chat (nunca a través de un formulario, ver "Curación del
catálogo" en `.claude/agents/encuesta-hogares.md`), y el agente hace el
trabajo de generalizar el código, agregarlo al catálogo y testearlo. Esa
posibilidad no existe para nadie más que esté usando el flujo guiado.

Publicar cambios en GitHub, en cambio, es siempre una acción aparte, con
sus propios cuidados:

- Nunca commitear los archivos `.sav` (ya están en `.gitignore`).
- Nunca hacer `git push` sin confirmarlo explícitamente antes.
- Usar Plotly con `pio.renderers.default = "png"` (requiere el paquete
  `kaleido`) desde la primera celda del notebook — si no, las gráficas
  interactivas no se ven en GitHub ni en el HTML exportado.

## 8. Cómo manejar un año de datos nuevo (lo específico de este proyecto)

1. Confirmar con el usuario qué archivos `.sav` puso en `data/` y de qué
   año son.
2. Inspeccionar los metadatos del archivo nuevo con `pyreadstat` (sin cargar
   todos los datos) para revisar si los códigos de columna que usa
   `config.py` (`HOGARES_COLUMNS`, `PERSONAS_COLUMNS`,
   `CONDICIONES_VIVIENDA_COLUMNS`) siguen existiendo y significan lo mismo
   (comparar contra las etiquetas de variable, `column_labels` de
   pyreadstat).
3. Si algún código cambió de nombre o desapareció, **nunca asumir un
   reemplazo por tu cuenta**: proponerle al usuario la columna candidata
   (por su etiqueta) y esperar su confirmación antes de tocar `config.py`.
4. Una vez validado el mapeo, correr el pipeline estándar (secciones 1 a 6)
   y regenerar los cortes/cuartiles reales para ese año — nunca reusar los
   cortes del año anterior, van a haber cambiado.
5. Presentarle el catálogo de métricas por categoría para que elija qué
   incluir en la Ampliación, y dejar espacio para que proponga una métrica
   propia si ninguna del catálogo le sirve (ver el paso 5 del archivo del
   agente).

## 9. Justificar el tipo de gráfica elegido, con fundamento estadístico

**Cada gráfica del informe va acompañada de una justificación con
fundamento, no solo una frase intuitiva.** El público de este informe es
académico y profesional — "no técnico" no significa "sin formación": es
gente que puede leer una cita o una fórmula y que la va a valorar como
señal de que los números tienen sentido, no como ruido innecesario. Por
eso, a diferencia de un criterio anterior de este documento (ya
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

Chuleta de referencia, con la fuente de cada patrón:

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
  daría una impresión de proporción que no existe (ver sección 2).
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
