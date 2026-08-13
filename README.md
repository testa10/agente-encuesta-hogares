# Agente de Análisis: Encuesta Continua de Hogares (ECH, INE Uruguay)

Este proyecto permite generar un informe de la Encuesta Continua de
Hogares del INE Uruguay, tanto a usuarios técnicos (con conocimientos
estadísticos) como a usuarios sin experiencia en programación, y
reproducirlo cada vez que se disponga de un nuevo año de datos, sin
necesidad de reconfigurar el análisis desde cero. El catálogo se define
en dos pasos: primero se seleccionan los **bloques temáticos** a incluir
(Brecha Digital, Hogares, Territorio, Vivienda y, cuando el año elegido
cuenta con esos datos, Seguridad Alimentaria, Empleo, y Seguridad y
Victimización — ninguno se incluye por defecto), y luego las métricas
puntuales dentro de cada bloque.

El análisis lo ejecuta un **agente**: un asistente de inteligencia
artificial (Claude) que carga los datos, construye las gráficas, redacta
las conclusiones y verifica la consistencia del resultado, guiando todo
el proceso mediante **formularios visuales que se abren automáticamente
en el navegador** — sin comandos ni ventanas de terminal. El usuario
selecciona el año, marca las métricas de interés en el catálogo y
confirma con un clic. También es posible proponer una métrica propia que
no figure en el catálogo; el agente advierte si detecta un problema
metodológico antes de construirla y ofrece una alternativa válida.

El resto de este documento está pensado para seguirse paso a paso, sin
necesidad de conocimientos técnicos previos.

---

## Requisitos previos (instalación única)

Los siguientes programas se instalan una sola vez. Si ya cuenta con
alguno instalado, puede omitir ese paso.

| Programa | Función | Dónde obtenerlo |
|---|---|---|
| **Git** | Descargar y actualizar este proyecto | https://git-scm.com/downloads |
| **Anaconda** | Incluye Python y las librerías de análisis de datos | https://www.anaconda.com/download |
| **Visual Studio Code** | Editor para abrir el proyecto | https://code.visualstudio.com/ |
| **Node.js** | Requerido por Claude Code | https://nodejs.org (versión LTS) |
| **Claude Code** | Herramienta que ejecuta al agente | https://claude.com/claude-code (instrucciones de instalación incluidas) |
| **7-Zip** | Para descomprimir el archivo `.RAR` que distribuye el INE | https://www.7-zip.org/ |

Instale cada programa con las opciones por defecto del instalador; no se
requiere configuración adicional.

---

## Paso 1: Descargar el proyecto

Abra una terminal (en Windows: busque "Git Bash" en el menú de inicio, si
lo instaló junto con Git) y ejecute:

```bash
git clone https://github.com/testa10/agente-encuesta-hogares.git
cd agente-encuesta-hogares
```

Esto crea una carpeta `agente-encuesta-hogares` con el contenido completo
del proyecto.

## Paso 2: Instalar las dependencias (Node.js, Claude Code y Python)

La forma más simple es hacer **doble clic en `instalar.bat`**, dentro de
la carpeta `agente-encuesta-hogares`. Se abre una ventana que verifica
qué falta e instala automáticamente lo necesario. Si solicita instalar
Node.js, abrirá la página de descarga en el navegador; instálelo con las
opciones por defecto y vuelva a ejecutar `instalar.bat` para continuar
donde quedó.

Alternativamente, desde una terminal, dentro de la carpeta del proyecto:

```bash
pip install -e ".[dev]"
```

Y verifique tener instalados [Node.js](https://nodejs.org) y Claude Code
(`npm install -g @anthropic-ai/claude-code`) — ver la tabla de
requisitos previos.

Este paso instala las librerías de Python necesarias para el análisis
(lectura de datos, generación de gráficas, etc.). Puede demorar uno o dos
minutos.

## Paso 3: Obtener los datos del año a analizar

En resumen: acceda al catálogo del INE, acepte sus términos de uso,
descargue la base del año de interés, y copie los archivos a la carpeta
`data/` del proyecto. El formato exacto varía según el año (hasta 2023,
dos archivos `.sav`; desde 2024, un único CSV combinado); el proyecto
admite ambos formatos automáticamente.

La guía completa, con el detalle de cada paso, está en
[`data/README.md`](data/README.md) — se recomienda seguirla, ya que
amplía este resumen. También es posible pedirle al agente que guíe este
proceso directamente (ver Paso 5).

> Estos archivos de datos **nunca se suben a GitHub**: su uso es personal,
> conforme a las condiciones del INE. El proyecto ya está configurado
> para excluirlos automáticamente.

## Paso 4: Abrir el proyecto en Claude Code

La forma más simple es hacer doble clic en **`abrir_agente.bat`**, en la
raíz del proyecto. Se abre una terminal ya ubicada en la carpeta
correspondiente y lanza Claude Code directamente — listo para continuar
con el Paso 5.

Alternativamente, para hacerlo manualmente o si se va a editar el
proyecto:

1. Abra Visual Studio Code y abra la carpeta `agente-encuesta-hogares`
   (`Archivo > Abrir Carpeta...`).
2. Abra una terminal integrada (`Terminal > Nueva Terminal`, o `` Ctrl+` ``).
3. Escriba `claude` y presione Enter. Esto abre Claude Code, ya ubicado en
   la carpeta del proyecto.

## Paso 5: Solicitar el análisis al agente

En la conversación con Claude Code, describa lo que necesita con sus
propias palabras. Por ejemplo:

> Quiero hacer el análisis de la Encuesta de Hogares con los datos de 2024
> que puse en la carpeta data/

Claude reconocerá que la solicitud corresponde al agente de este
proyecto y comenzará a trabajar. Si en algún momento no se activa
automáticamente, puede solicitarlo de forma explícita:

> Usá el agente encuesta-hogares para analizar los datos de 2024

## Paso 6: Completar los formularios

A partir de este punto, **no es necesario escribir nada más en la
terminal**: el agente abrirá en el navegador una serie de pantallas
(bienvenida, ubicación de los datos, contenido del informe, etc.), que se
completan con clics y algún campo de texto breve; al confirmar cada una,
continúa automáticamente con la siguiente. La terminal de Claude Code
permanece en segundo plano; no requiere supervisión. Cada pantalla
incluye, además, un enlace para **salir sin terminar el informe**, por si
se decide no continuar.

La primera pantalla permite elegir qué **bloques temáticos** incluir en
el informe — Brecha Digital, Hogares, Territorio, Vivienda y, si hay
datos disponibles para el año elegido, Seguridad Alimentaria, Empleo, y
Seguridad y Victimización. Ninguno viene preseleccionado, ni siquiera
Brecha Digital: se elige uno, varios, o todos.

A continuación, otra pantalla presenta el catálogo de métricas puntuales
disponibles dentro de los bloques elegidos (organizadas por tema, cada
una con una breve explicación), y permite proponer una métrica adicional
que no figure en la lista. Si el agente detecta un problema con algo
propuesto (por ejemplo, un cruce que no puede calcularse de forma
confiable con los datos disponibles), lo indicará en otra pantalla junto
con una alternativa válida, para aceptarla, proponer otra, o descartar
esa métrica del informe.

**Tras confirmar el catálogo, el proceso demora un tiempo considerable.**
No es un cálculo instantáneo: el agente construye y revisa cada gráfica
seleccionada, una por una. Como referencia (catálogo completo, las 47
métricas de los siete bloques): **entre 25 y 30 minutos**. Seleccionar
menos bloques o menos métricas reduce el tiempo proporcionalmente. Este
proceso también consume una parte del uso disponible de Claude Code (en
la corrida de referencia, el equivalente a unos 95 llamados a
herramientas); que la terminal permanezca sin novedades visibles durante
un rato prolongado es esperable, no indica un error.

**Si te preocupa llegar al límite de uso de tu plan a mitad de una
corrida larga, conviene no elegir los siete bloques de una sola vez.**
Cada bloque temático (Brecha Digital, Hogares, Territorio, Vivienda,
Seguridad Alimentaria, Empleo, Seguridad y Victimización) demora, por sí
solo, entre 2 y 5 minutos. Es preferible generar el informe en varias
corridas más chicas — uno o dos bloques por vez, encadenándolas con el
botón "crear un nuevo informe" del Paso 7 — en vez de arriesgarse a que
una corrida completa de 25 a 30 minutos se corte a mitad de camino por
falta de uso disponible. Cada corrida produce su propio informe
(notebook, HTML y PDF); si elegís bloques distintos en cada una, vas a
terminar con varios informes parciales para el mismo año, no uno solo
combinado.

## Paso 7: Revisar los resultados

Se generan tres archivos nuevos en `notebooks/`, todos identificados con
el año elegido (por ejemplo, `Informe_ECH_2024.ipynb/.html/.pdf`; si se
repite la corrida para el mismo año, el informe anterior no se pierde,
queda guardado con el sufijo "(anterior)"):

- El notebook, con el análisis completo y el código incluido, para quien
  desee revisar el detalle técnico.
- Un informe en HTML, sin código, pensado para compartir con cualquier
  persona.
- Un **informe en PDF**, con formato de documento profesional (portada,
  tipografía cuidada, gráficas ajustadas a la página). El agente genera
  siempre ambos formatos, y copia el PDF automáticamente a la **carpeta
  de Descargas** — no es necesario buscarlo dentro del proyecto.

La pantalla final incluye un botón para abrir cada formato directamente,
además de un botón para **crear un nuevo informe** (otro año, u otra
selección de métricas) sin cerrar la ventana ni volver a ejecutar
`abrir_agente.bat` — retoma directamente el primer formulario, dentro de
la misma conversación.

Con esto concluye el trabajo del agente: el análisis queda guardado
localmente; nada se publica automáticamente ni el agente ofrecerá
hacerlo.

---

## Preguntas frecuentes

**¿Es necesario saber programar?**
No. Toda la interacción ocurre mediante formularios en el navegador, en
español, sin exposición a código ni comandos. El código existe, pero no
es necesario modificarlo ni comprenderlo para usar el agente.

**¿Qué ocurre si el INE modificó el formato o los nombres de las
preguntas de la encuesta entre 2019 y el año utilizado?**
El agente lo detecta automáticamente al validar los datos nuevos, y
solicita confirmación antes de asumir cualquier cambio — nunca infiere en
silencio.

**¿Es posible analizar más de un año y compararlos?**
Sí — puede solicitarse directamente al agente, por ejemplo: "quiero
comparar el análisis de 2019 con el de 2024".

**¿Dónde se documentan los criterios de rigor que sigue el agente?**
En [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md), que reúne las reglas de
rigor estadístico y claridad definidas durante la construcción del
análisis original.

**¿El agente registra la actividad del usuario?**
Sí, un registro mínimo y local: qué pantallas se mostraron, cuándo, y si
alguna demoró en exceso o falló — nunca el contenido escrito ni datos
personales. Se guarda en `logs/bitacora.jsonl`, **en la propia
computadora**, sin subirse ni compartirse automáticamente. Su propósito
es permitir que, ante un problema reportado, quien mantiene el proyecto
pueda diagnosticarlo a partir de ese archivo, en lugar de depender de una
descripción de memoria.

**¿Cómo se ejecutan los tests automáticos?**

Desde la terminal, en la carpeta del proyecto:

```bash
python -m pytest -q
```

O desde Visual Studio Code, en el panel de Testing (ícono de matraz en la
barra lateral).

---

## Estructura del proyecto

```
agente-encuesta-hogares/
├── .claude/
│   └── agents/
│       └── encuesta-hogares.md  # El agente: sus instrucciones de trabajo
├── docs/
│   └── METODOLOGIA.md           # Reglas de rigor estadístico y claridad
├── src/
│   └── encuesta_hogares/        # Código de análisis, reutilizable año a año
├── notebooks/                   # Informes generados (uno por año)
├── tests/                       # Tests automáticos de la lógica de análisis
├── data/                        # Archivos de datos del usuario (no se suben a git)
└── pyproject.toml
```

## Fuente de los datos

Instituto Nacional de Estadística (INE) — Encuesta Continua de Hogares (ECH).
https://www4.ine.gub.uy/Anda5/index.php/catalog/Encuestas_a_hogares

## Licencia

Este proyecto se distribuye bajo [PolyForm Noncommercial 1.0.0](LICENSE):
permite usar, copiar, modificar y compartir el código libremente para
fines académicos, educativos, de investigación, y cualquier otro uso no
comercial. Ver el archivo [`LICENSE`](LICENSE) para el texto completo.
