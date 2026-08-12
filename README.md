# Agente de Análisis: Encuesta Continua de Hogares (ECH, INE Uruguay)

Este proyecto te permite repetir, cada vez que consigas un nuevo año de
datos de la Encuesta Continua de Hogares del INE Uruguay, el mismo análisis
de penetración tecnológica (TV cable, internet, computadora, streaming) en
hogares de Montevideo — sin tener que volver a explicar desde cero cómo se
hace, ni programar vos mismo.

En vez de un análisis fijo, este proyecto incluye un **agente**: un asistente
de inteligencia artificial (Claude) que hace el trabajo — carga los datos,
arma las gráficas, redacta las conclusiones, verifica que todo esté bien —
y te va guiando con **formularios visuales que se abren solos en tu
navegador** (nada de comandos ni pantallas negras): elegís el año, marcás
qué métricas te interesan de un catálogo, y confirmás con un clic. También
podés proponer una métrica propia que no esté en el catálogo, y el agente
te va a avisar si encuentra algún problema estadístico antes de
construirla, ofreciéndote una alternativa.

No hace falta que entiendas el resto de este documento técnicamente — está
escrito para que lo sigas paso a paso, incluso si nunca programaste.

---

## Lo que vas a necesitar (una sola vez)

Estos son programas que se instalan una única vez en tu computadora. Si ya
tenés alguno instalado, saltealo.

| Programa | Para qué sirve | Dónde conseguirlo |
|---|---|---|
| **Git** | Para descargar y actualizar este proyecto | https://git-scm.com/downloads |
| **Anaconda** | Trae Python y las librerías de análisis de datos | https://www.anaconda.com/download |
| **Visual Studio Code** | El editor donde vas a abrir el proyecto | https://code.visualstudio.com/ |
| **Node.js** | Lo necesita Claude Code para funcionar | https://nodejs.org (versión LTS) |
| **Claude Code** | La herramienta que ejecuta al agente | https://claude.com/claude-code (instrucciones de instalación ahí mismo) |
| **7-Zip** | Para abrir el archivo comprimido (.RAR) que baja el INE | https://www.7-zip.org/ |

Instalá cada uno con las opciones por defecto del instalador — no hace
falta configurar nada especial.

---

## Paso 1: Descargar este proyecto a tu computadora

Abrí una terminal (en Windows: buscá "Git Bash" en el menú de inicio, si lo
instalaste junto con Git) y escribí:

```bash
git clone https://github.com/testa10/agente-encuesta-hogares.git
cd agente-encuesta-hogares
```

Esto crea una carpeta `agente-encuesta-hogares` con todo el proyecto adentro.

## Paso 2: Instalar todo lo que falta (Node.js, Claude Code y las
dependencias de Python)

La forma más simple: andá a la carpeta `agente-encuesta-hogares` en el
Explorador de Windows y hacé **doble clic en `instalar.bat`**. Se abre una
ventana negra que revisa qué te falta y lo instala solo. Si te pide
instalar Node.js, va a abrir la página de descarga en el navegador — instalá
ese programa con las opciones por defecto y después volvé a hacer doble
clic en `instalar.bat` para que continúe donde quedó.

Si preferís hacerlo a mano (o el `.bat` no te funciona por algún motivo),
desde una terminal, dentro de la carpeta del proyecto:

```bash
pip install -e ".[dev]"
```

Y asegurate de tener [Node.js](https://nodejs.org) y Claude Code
instalados (`npm install -g @anthropic-ai/claude-code`) — ver la tabla de
prerrequisitos más arriba.

Esto instala las librerías de Python que el análisis necesita (para leer los
datos, hacer las gráficas, etc.). Puede tardar uno o dos minutos.

## Paso 3: Conseguir los datos del año que querés analizar

En resumen: entrá al catálogo del INE, aceptá sus términos de uso, bajá el
archivo `.RAR` de la base en formato SPSS del año que te interesa,
extraelo, y copiá los dos archivos `.sav` (Hogares y Personas) a la carpeta
`data/` de este proyecto.

La guía completa, paso a paso y con capturas de dónde hacer clic, está en
[`data/README.md`](data/README.md) — seguila de ahí, es más detallada que
este resumen. Si preferís, también le podés pedir directamente al agente
que te guíe mientras lo hacés (ver Paso 5).

> Estos archivos de datos **nunca se suben a GitHub** — son de uso personal
> según las condiciones del INE. El proyecto ya está configurado para
> ignorarlos automáticamente.

## Paso 4: Abrir el proyecto en Claude Code

La forma más simple: hacé doble clic en **`abrir_agente.bat`** (está en esta
misma carpeta). Se abre una terminal ya parada en el proyecto y lanza
Claude Code directo — listo para el Paso 5.

Si preferís hacerlo a mano, o vas a editar algo del proyecto de paso:

1. Abrí Visual Studio Code y abrí la carpeta `agente-encuesta-hogares`
   (`Archivo > Abrir Carpeta...`).
2. Abrí una terminal integrada (`Terminal > Nueva Terminal`, o `` Ctrl+` ``).
3. Escribí `claude` y presioná Enter. Esto abre Claude Code, ya ubicado en
   la carpeta de tu proyecto.

## Paso 5: Pedirle al agente que haga el análisis

En la conversación con Claude Code, escribí simplemente lo que querés,
en tus propias palabras. Por ejemplo:

> Quiero hacer el análisis de la Encuesta de Hogares con los datos de 2024
> que puse en la carpeta data/

Claude va a reconocer que este pedido corresponde al agente de este
proyecto y va a empezar a trabajar con ese método. Si en algún momento no
se activa solo, podés pedirlo de forma explícita:

> Usá el agente encuesta-hogares para analizar los datos de 2024

## Paso 6: Completar los formularios que te va mostrando

A partir de acá, **no hace falta que escribas nada más en la terminal**:
el agente te va a ir abriendo el navegador con una serie de pantallas
(bienvenida, dónde poner los datos, qué querés incluir en el informe,
etc.) — vas completando cada una con clics y algún campo de texto corto,
y apenas confirmás una, sigue con la siguiente. La terminal de Claude Code
queda de fondo, trabajando; no hace falta que la mires.

Una de esas pantallas te deja elegir, de un catálogo, qué métricas querés
que tenga tu informe (organizadas por tema, cada una con una explicación
breve), y también proponer una que no esté en la lista si se te ocurre
algo puntual. Si el agente encuentra un problema con algo que propusiste
(por ejemplo, un cruce que no se puede hacer de forma confiable con los
datos disponibles), te lo va a mostrar en otra pantalla, con una
alternativa que sí funcione — ahí elegís si la aceptás, proponés otra
cosa, o la dejás afuera del informe.

**Después de confirmar el catálogo, esperá — un informe tarda bastante.**
No es un cálculo instantáneo: el agente arma y revisa una por una todas
las gráficas que elegiste. Como referencia real (catálogo completo, las
47 métricas de las cinco categorías): **alrededor de 25 a 30 minutos**.
Eligiendo menos métricas tarda menos, más o menos en proporción a
cuántas elegiste. Esto también consume una porción real de tu uso de
Claude Code (en la corrida de referencia, el equivalente a unos 95
llamados a herramientas) — no es un error ni algo colgado si la terminal
sigue trabajando un buen rato sin que pase nada nuevo en pantalla.

## Paso 7: Revisar los resultados

Vas a encontrar tres archivos nuevos en `notebooks/`, todos con el año
que elegiste en el nombre (ej. `Informe_ECH_2024.ipynb/.html/.pdf` — si
volvés a correr el mismo año, el informe anterior no se pierde, queda
guardado como "(anterior)"):
- El notebook, con todo el análisis y el código incluido — para quien
  quiera ver el detalle.
- Un informe en HTML, sin código, pensado para compartir con cualquier
  persona.
- Un **informe en PDF**, con formato de documento profesional (portada,
  tipografía cuidada, gráficas ajustadas a la hoja) — el agente siempre
  genera los dos formatos, y además copia el PDF automáticamente a tu
  **carpeta de Descargas**: no hace falta que lo busques dentro del
  proyecto, aparece ahí solo, como cualquier archivo que descargarías
  normalmente.

La última pantalla del agente ya trae un botón para abrir cada formato
directamente, además de un botón para **crear un nuevo informe** (otro
año, u otra selección de métricas) sin tener que cerrar la ventana ni
volver a hacer doble clic en `abrir_agente.bat` — vuelve directo al primer
formulario, en la misma conversación.

Con eso el trabajo del agente termina — el análisis queda guardado en tu
propia computadora, nada se sube a ningún lado automáticamente ni el
agente te lo va a ofrecer.

---

## Preguntas frecuentes

**¿Necesito saber programar?**
No. Toda la interacción es a través de formularios en el navegador, en
español — nunca ves código ni comandos. El código existe, pero no
necesitás tocarlo ni entenderlo.

**¿Qué pasa si el INE cambió el formato o los nombres de las preguntas de la
encuesta entre 2019 y el año que estoy usando?**
El agente lo detecta automáticamente al revisar los datos nuevos, y te va a
avisar y pedir confirmación antes de asumir nada — nunca adivina en
silencio.

**¿Puedo correr el análisis de más de un año y compararlos?**
Sí — pedíselo al agente directamente, por ejemplo "quiero comparar el
análisis de 2019 con el de 2024".

**¿Dónde está la lógica de "qué está bien y qué está mal" que sigue el
agente?**
En [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) — es el documento con todas
las reglas de rigor estadístico y claridad que se fueron descubriendo
durante la construcción del análisis original. Si te interesa el detalle
técnico, está todo ahí.

**¿El agente registra lo que hago?**
Sí, un registro mínimo y local: qué pantallas se te mostraron y cuándo, si
alguna tardó demasiado o falló — nada de lo que escribiste ni de tus
datos personales. Queda en el archivo `logs/bitacora.jsonl`, **en tu
propia computadora**, nunca se sube a ningún lado ni se comparte
automáticamente con nadie. Sirve para que, si algo te falla y le avisás a
quien mantiene este proyecto, pueda entender qué pasó mandándole ese
archivo, en vez de tener que describir de memoria lo que viste.

**Los tests, ¿cómo los corro yo si quiero revisar que todo esté bien?**

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
│   └── encuesta_hogares/        # El código de análisis, reutilizable año a año
├── notebooks/                   # Acá se generan los análisis (uno por año)
├── tests/                       # Tests automáticos de la lógica de análisis
├── data/                        # Tus archivos .sav van acá (no se suben a git)
└── pyproject.toml
```

## Fuente de los datos

Instituto Nacional de Estadística (INE) - Encuesta Continua de Hogares (ECH).
https://www4.ine.gub.uy/Anda5/index.php/catalog/Encuestas_a_hogares
