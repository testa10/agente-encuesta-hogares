# Datos

Los microdatos de la Encuesta Continua de Hogares (ECH) del INE Uruguay
**no están incluidos** en este repositorio, por restricciones de
redistribución de la fuente. `.gitignore` ya excluye los archivos de datos
para que nunca se suban por accidente.

## Cómo conseguirlos (paso a paso)

1. Andá a **https://www4.ine.gub.uy/Anda5/index.php/catalog/Encuestas_a_hogares**
   — ahí está el listado de todas las ediciones de la ECH, año por año.
2. Buscá en la lista (o usá el filtro de año a la izquierda) **"Encuesta
   Continua de Hogares, Año AAAA"**, con el año que te interese, y hacé
   clic para entrar a esa ficha.
3. Dentro de la ficha del año, hacé clic en la pestaña **"OBTENER
   MICRODATOS"**.
4. Vas a ver un texto largo de **Términos y condiciones** del INE. Leelo, y
   si estás de acuerdo, hacé clic en el botón **"Aceptar"** al final. Esto
   lo tenés que hacer vos personalmente — es un acuerdo legal con el INE,
   nadie lo puede aceptar en tu nombre.
5. Se va a abrir una lista de "Archivos de datos". Buscá la opción llamada
   algo como **"Bases ECH AAAA .SAV"** y hacé clic en su enlace de
   **Descargar**. Es un archivo comprimido (`.RAR`) de unos 15-20 MB.
6. **Extraé el archivo .RAR** — Windows no lo abre solo, necesitás un
   programa como [7-Zip](https://www.7-zip.org/) (gratis) o WinRAR. Click
   derecho sobre el archivo descargado → "Extraer aquí" (o similar, según
   el programa que instales).
7. Adentro vas a encontrar varios archivos `.sav` — entre ellos, la base de
   **Hogares** y la base de **Personas** (los nombres exactos pueden variar
   de un año a otro; suelen empezar con `H` para Hogares y `P` para
   Personas).
8. Copiá esos dos archivos `.sav` a la subcarpeta de ese año dentro de
   `data/` — por ejemplo, `data/2024/`. Si le pediste el análisis al
   agente, él ya te va a haber creado esa carpeta y abierto en el
   Explorador antes de este paso, así que solo tenés que soltar los
   archivos ahí.

Si no estás seguro de cuál archivo es cuál, no pasa nada — contale al
agente qué archivos extrajiste y él te va a ayudar a identificarlos y
renombrarlos si hace falta (el código busca automáticamente, dentro de
cada subcarpeta de año, cualquier archivo que empiece con `H_` o `P_` y
termine en `.sav`).

## Carpeta `2019/`

Es el año con el que se construyó y validó todo el análisis original —
sirve como referencia para comparar la estructura de cualquier año nuevo.
**No la borres ni la muevas**, aunque estés analizando otro año.

## Cita requerida

Instituto Nacional de Estadística (INE) - Encuesta Continua de Hogares (ECH).
https://www4.ine.gub.uy/Anda5/index.php/catalog/Encuestas_a_hogares

> Los datos utilizados son un extracto con fines de análisis personal, no
> una muestra representativa completa ni un estudio oficial del INE.
