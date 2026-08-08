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
   clasificar nivel económico.
2. **Análisis preliminar**: cuántos hogares tienen la tecnología principal
   (TV cable) en total.
3. **Distribución por barrio**: % de abonados por barrio, clasificado en
   cuartiles (nivel de suscripción del **barrio**, no del hogar — ver
   sección 4 de este documento).
4. **Composición de los hogares** con y sin la tecnología principal (edad,
   sexo).
5. **Ampliación del análisis**, organizada en "Entornos" temáticos:
   - Entorno 1 — Nivel económico del hogar (brecha digital, acceso por
     tecnología).
   - Entorno 2 — Nivel de pobreza del hogar.
   - Entorno 3 — Otros factores del hogar y el territorio (sustitución
     tecnológica, condiciones de vivienda, composición del hogar, situación
     ocupacional, alcance nacional).
6. **Resumen analítico final**, organizado por los mismos Entornos, con
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
  confiable. Antes de publicar una gráfica nueva, revisar el tamaño de cada
  grupo (`.value_counts()` o `len()` del segmento).
- **Correlación vs. causación**: el lenguaje debe ser siempre observacional
  ("los hogares con X tienen más probabilidad de Y"), nunca causal ("X
  provoca Y"), salvo que el diseño del estudio lo permita (no es el caso
  acá: es una encuesta transversal).
- **Proporciones que no suman 100% entre sí no se apilan.** Si dos barras
  representan porcentajes calculados sobre bases distintas (ej. "% con
  problema estructural dentro de 'con cable'" y "dentro de 'sin cable'"),
  no se pueden combinar en un gráfico de barras apiladas — eso implica una
  relación parte-todo que no existe. Para comparar varias categorías de este
  tipo a la vez, usar una gráfica de **diferencia** (puntos porcentuales
  entre grupos), no un apilado. Ver `condiciones_vivienda_diferencia()` /
  `plot_condiciones_vivienda_diferencia()` como ejemplo ya resuelto.

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
5. Re-ejecutar el notebook completo:
   `jupyter nbconvert --to notebook --execute --inplace <notebook>.ipynb`
6. Verificar que ninguna celda de código haya quedado con `output_type ==
   "error"`.
7. Para cualquier gráfica nueva o modificada, extraer el PNG embebido del
   output de la celda y mirarlo — no asumir que "si no tiró error, se ve
   bien". Revisar que los números y el orden de las barras tengan sentido.
8. Generar el informe HTML sin código (para gente no técnica):
   - Copiar el notebook, filtrar del output los mensajes `stderr` de tipo
     `stream` (son warnings inofensivos de matplotlib, no errores reales).
   - `jupyter nbconvert --to html --no-input <copia>.ipynb`
   - Corregir el `<title>` del HTML generado (por defecto queda con el
     nombre del archivo).
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
   `python -c` o un archivo temporal):
   ```python
   from playwright.sync_api import sync_playwright

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
5. Nombrá el archivo de forma clara, ej. `Informe_ECH_{AÑO}.pdf`.
6. Copiá el PDF a la carpeta de Descargas del usuario, además de dejarlo en
   el proyecto:
   ```python
   from pathlib import Path
   import shutil
   shutil.copy(ruta_pdf_salida, Path.home() / "Downloads" / "Informe_ECH_{AÑO}.pdf")
   ```
   `Path.home() / "Downloads"` funciona igual en Windows y en Mac. Si esa
   carpeta no existe (poco común, pero puede pasar), avisale al usuario en
   vez de fallar en silencio.
7. Abrí el PDF resultante (o al menos revisá la cantidad de páginas y que
   el tamaño de archivo sea razonable) antes de darlo por terminado — no
   asumas que la conversión salió bien solo porque no tiró error.

## 7. Publicación

- Nunca commitear los archivos `.sav` (ya están en `.gitignore`).
- Antes de hacer `git push`, **preguntar explícitamente al usuario si
  quiere publicar los cambios** — no asumir que sí.
- Si el usuario tiene un sitio de portafolio y quiere mostrar el nuevo
  análisis ahí, copiar el informe HTML generado y agregar o actualizar la
  tarjeta del proyecto correspondiente.
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
5. Preguntar si además de reproducir el análisis estándar, el usuario quiere
   explorar preguntas nuevas (ver la guía de "Cómo agregar un análisis
   nuevo" en el archivo del agente).
