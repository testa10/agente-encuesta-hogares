# Flujo de trabajo: verificación, entrega del informe y casos operativos

Este documento reúne los procedimientos paso a paso del proyecto —
distinto de [`METODOLOGIA.md`](METODOLOGIA.md), que reúne las reglas y
principios (qué es correcto o incorrecto), este archivo es sobre *cómo
ejecutar* el trabajo una vez que las reglas ya están claras. Se separó de
`METODOLOGIA.md` porque ese documento había crecido mezclando ambos
tipos de contenido y se había vuelto difícil de navegar.

## 1. Flujo de verificación (seguir siempre, sin saltarse pasos)

1. Escribir o editar el código en `src/encuesta_hogares/` (nunca directamente
   en el notebook si la lógica se puede poner en una función reutilizable
   y testeable).
2. Si se agrega una función nueva en `analysis.py`, agregarle un test en
   `tests/`.
3. Correr `pytest -q` y confirmar que todo pasa.
4. Editar el notebook con `nbformat` (no pegar JSON a mano).
5. Re-ejecutar el notebook completo, cronometrando cuánto tarda (para
   poder ver después, con `tools/resumen_sesiones.py`, si el cuello de
   botella real está acá o en otro paso) — en vez de invocar `jupyter
   nbconvert` directo por Bash, envolverlo con `bitacora.medir_comando()`:
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
   extracción, nunca usar un comodín en `rm` (ej. `rm -f celda_*.png`)** —
   la herramienta de Bash rechaza los patrones glob en operaciones de
   escritura/borrado, y esa aprobación interrumpe una corrida que se
   supone que no necesita supervisión. Hacer el borrado con Python
   (`pathlib.Path(carpeta).glob("celda_*.png")` y `.unlink()` en un bucle,
   dentro del mismo script que ya se esté corriendo con `run_python.bat`) —
   mismo criterio que ya se sigue para editar el notebook (nbformat, nunca
   JSON a mano) y para correr comandos largos (`bitacora.medir_comando`,
   nunca `jupyter nbconvert` suelto).
8. Generar el informe HTML sin código (para gente no técnica):
   - Copiar el notebook, filtrar del output los mensajes `stderr` de tipo
     `stream` (son warnings inofensivos de matplotlib, no errores reales).
   - Igual que en el paso 5, envolver la conversión con
     `bitacora.medir_comando("generacion_html", [sys.executable, "-m", "jupyter", "nbconvert", "--to", "html", "--no-input", "<copia>.ipynb"])`
     en vez de invocar `jupyter nbconvert` directo.
   - Corregir el `<title>` del HTML generado (por defecto queda con el
     nombre del archivo).
   - **El HTML final se guarda siempre como exactamente
     `notebooks/Informe_ECH_{AÑO}.html`** — mismo criterio que el nombre
     del notebook (paso 5.2 de `.claude/agents/encuesta-hogares.md`): sin
     sufijos ni variantes, para que dos años nunca choquen y el respaldo
     de abajo se dispare solo cuando de verdad se repite el mismo año.
   - **Antes de guardar el HTML final con ese nombre**, llamar a
     `entrega.respaldar_si_existe(ruta_html_final)` — si ya existía un
     informe de una corrida anterior para ese mismo año (ej. alguien
     corrió el mismo año dos veces), queda como "Informe_ECH_{AÑO}
     (anterior).html" en vez de perderse en silencio.
9. Generar el informe PDF profesional a partir de ese HTML, y copiarlo a la
   carpeta de Descargas del usuario (ver sección 2). Este paso es parte del
   resultado estándar que se le entrega al usuario — no es opcional ni algo
   que solo se hace si lo pide.
10. Publicar (ver sección 3).

## 2. Generación del informe PDF profesional

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

1. Asegurarse de tener Playwright listo (una sola vez por instalación):
   `playwright install chromium`. Si no está, instalarlo con Bash — es la
   descarga de un componente del propio paquete Python que ya está en las
   dependencias del proyecto, no un programa externo nuevo que el usuario
   tenga que gestionar.
2. Tomar el HTML sin código ya generado (paso 8 de la sección 1) y
   anteponer al `<body>` un bloque de portada:
   ```html
   <div class="portada">
     <h1>Encuesta Continua de Hogares — Informe {AÑO}</h1>
     <div class="subtitulo">Penetración tecnológica en hogares de Montevideo</div>
     <div class="meta">Generado el {fecha de hoy}</div>
   </div>
   ```
3. Inyectar `docs/informe_estilo.css` dentro de un `<style>` en el `<head>`
   del HTML (o enlazarlo con `<link>` si se va a mantener el archivo al
   lado). Esa hoja de estilos ya define tamaño A4, márgenes, tipografía, y
   sobre todo `max-width`/`max-height` + `page-break-inside: avoid` en las
   imágenes — es lo que evita que una gráfica quede cortada entre dos
   páginas o se salga del ancho de la hoja. No reinventarla ni
   simplificarla: cada regla ahí resuelve un problema real de paginación.
4. Convertir ese HTML a PDF con Playwright (script corto, vía Bash con
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
   Usar `header_template` / `footer_template` (no CSS `@page { @bottom-center }`)
   para la numeración de página: Chromium no soporta las cajas de margen de
   `@page` en su motor de impresión, solo esas plantillas HTML de Playwright.
5. **El nombre del archivo es siempre exactamente `Informe_ECH_{AÑO}.pdf`**
   (el año elegido en el paso 1, sin ningún sufijo ni variante — nada de
   `_personalizado`, `_v2`, una descripción del contenido, etc.). No es
   solo una cuestión de prolijidad: es lo que hace que dos años distintos
   nunca choquen entre sí, y que `entrega.respaldar_si_existe()` (ver
   paso 8 de la sección 1) respalde correctamente solo cuando se repite
   el mismo año.
6. Copiar el PDF a la carpeta de Descargas del usuario, además de dejarlo
   en el proyecto — respaldando ahí también el que hubiera de una corrida
   anterior, por la misma razón del paso 8 de la sección 1:
   ```python
   from pathlib import Path
   import shutil
   from encuesta_hogares import entrega
   ruta_descargas = Path.home() / "Downloads" / "Informe_ECH_{AÑO}.pdf"
   entrega.respaldar_si_existe(ruta_descargas)
   shutil.copy(ruta_pdf_salida, ruta_descargas)
   ```
   `Path.home() / "Downloads"` funciona igual en Windows y en Mac. Si esa
   carpeta no existe (poco común, pero puede pasar), avisarle al usuario en
   vez de fallar en silencio.
7. Abrir el PDF resultante (o al menos revisar la cantidad de páginas y
   que el tamaño de archivo sea razonable) antes de darlo por terminado —
   no asumir que la conversión salió bien solo porque no tiró error.

## 3. Publicación (no es parte del flujo del agente)

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

## 4. Cómo manejar un año de datos nuevo (lo específico de este proyecto)

1. Confirmar con el usuario qué archivos `.sav` puso en `data/` y de qué
   año son.
2. Inspeccionar los metadatos del archivo nuevo con `pyreadstat` (sin cargar
   todos los datos) para revisar si los códigos de columna que usa
   `config.py` (`HOGARES_COLUMNS`, `PERSONAS_COLUMNS`,
   `CONDICIONES_VIVIENDA_COLUMNS`) siguen existiendo y significan lo mismo
   (comparar contra las etiquetas de variable, `column_labels` de
   pyreadstat).
3. Si algún código cambió de nombre o desapareció, **nunca asumir un
   reemplazo por cuenta propia**: proponerle al usuario la columna
   candidata (por su etiqueta) y esperar su confirmación antes de tocar
   `config.py`.
4. Una vez validado el mapeo, correr el pipeline estándar completo (armar
   el notebook, verificarlo, generar HTML y PDF — secciones 1 y 2 de este
   documento) y regenerar los cortes/cuartiles reales para ese año — nunca
   reusar los cortes del año anterior, seguramente hayan cambiado.
5. Presentarle el catálogo de métricas por categoría para que elija qué
   incluir en la Ampliación, y dejar espacio para que proponga una métrica
   propia si ninguna del catálogo le sirve (ver el paso 5 del archivo del
   agente).
