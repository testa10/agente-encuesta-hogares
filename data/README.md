# Datos

Los microdatos de la Encuesta Continua de Hogares (ECH) del INE Uruguay
**no están incluidos** en este repositorio, por restricciones de
redistribución de la fuente. `.gitignore` ya excluye los archivos de datos
para que nunca se suban por accidente.

## Cómo conseguirlos (paso a paso)

> **El formato de archivo cambia según el año**: hasta 2023, el INE
> distribuye la base de Hogares y la de Personas como dos archivos `.sav`
> separados; desde 2024, las junta en un único CSV combinado. El proyecto
> soporta los dos formatos automáticamente — solo cambia qué archivo vas
> a encontrar en el paso 5 de abajo.

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
5. Se va a abrir una lista de "Archivos de datos". Qué buscar depende del
   año:
   - **2023 o anterior**: la opción llamada algo como **"Bases ECH AAAA
     .SAV"**. Es un archivo comprimido (`.RAR`) de unos 15-20 MB.
   - **2024 en adelante**: la opción con el CSV combinado (suele llamarse
     algo como **"Base ECH AAAA .CSV"**), o puede venir igual dentro de
     un `.RAR`.

   Hacé clic en el enlace de **Descargar** de la opción que corresponda.
6. **Si descargaste un `.RAR`**, extraelo — Windows no lo abre solo,
   necesitás un programa como [7-Zip](https://www.7-zip.org/) (gratis) o
   WinRAR. Click derecho sobre el archivo descargado → "Extraer aquí" (o
   similar, según el programa que instales). Si ya es un `.csv` suelto, no
   hace falta extraer nada.
7. Fijate qué encontraste:
   - **Dos archivos `.sav`**: la base de **Hogares** y la de **Personas**
     (los nombres exactos pueden variar de un año a otro; suelen empezar
     con `H` para Hogares y `P` para Personas).
   - **Un solo archivo `ECH_AAAA.csv`**: es la base combinada — una fila
     por persona, con los datos del hogar repetidos para cada integrante.
8. Copiá esos archivos (los dos `.sav`, o el `ECH_AAAA.csv`, según lo que
   corresponda) a la subcarpeta de ese año dentro de `data/` — por
   ejemplo, `data/2024/`. Si le pediste el análisis al agente, él ya te
   va a haber creado esa carpeta y abierto en el Explorador antes de este
   paso, así que solo tenés que soltar los archivos ahí.

Si no estás seguro de cuál archivo es cuál, no pasa nada — contale al
agente qué archivos extrajiste y él te va a ayudar a identificarlos y
renombrarlos si hace falta (el código busca automáticamente, dentro de
cada subcarpeta de año, archivos `H_*.sav`/`P_*.sav` o `ECH_AAAA.csv`).

## Datos opcionales: seguridad alimentaria, empleo y seguridad/victimización

Además de Hogares y Personas, el catálogo de métricas del agente puede
incluir tres áreas más — pero **son descargas aparte, y no existen para
todos los años**:

- **Seguridad alimentaria (FIES)**: archivo `base_FIES_AAAA.csv`.
- **Empleo**: los 12 archivos mensuales `ECH_MM_AA.csv` (uno por mes,
  enero a diciembre) del módulo de seguimiento — hacen falta los 12
  juntos, no sirve con menos.
- **Seguridad y victimización**: archivo `ECH_VICTIMIZACION_S2_AAAA.csv`.

Los tres se buscan y se aceptan de la misma forma que la base principal
(pasos 1 a 4 de arriba), dentro de la misma ficha del año en el catálogo
del INE, y se copian a la misma subcarpeta `data/AAAA/`. Si no conseguís
alguno (o el año que elegiste no lo tiene), no pasa nada: el agente
detecta automáticamente qué datos existen y solo te ofrece las
categorías del catálogo que puede construir con lo que sí tenés.

## Carpeta `2019/`

Es el año con el que se construyó y validó todo el análisis original —
sirve como referencia para comparar la estructura de cualquier año nuevo.
**No la borres ni la muevas**, aunque estés analizando otro año.

## Cita requerida

Instituto Nacional de Estadística (INE) - Encuesta Continua de Hogares (ECH).
https://www4.ine.gub.uy/Anda5/index.php/catalog/Encuestas_a_hogares

> Los datos utilizados son un extracto con fines de análisis personal, no
> una muestra representativa completa ni un estudio oficial del INE.
