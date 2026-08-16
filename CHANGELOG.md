# Changelog

Registro de cambios relevantes del proyecto, pensado para quien generó un
informe con una versión anterior y quiere saber qué cambió metodológicamente
antes de comparar corridas de años distintos. Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

El proyecto no versionó formalmente sus primeras ~30 revisiones (desde el
análisis original de 2019 hasta la introducción del catálogo por bloques
opt-in) — el historial completo de esos cambios está en `git log`. Este
changelog arranca en la versión donde se formalizó el versionado.

## [0.9.3] — 2026-08-15

### Cambiado

- **El modelo con el que corre el agente queda fijado a `claude-opus-5`**,
  en el frontmatter del subagente y en `abrir_agente.bat`. Hasta ahora no
  estaba fijado en ninguna parte: el subagente heredaba el modelo de la
  sesión principal, que tomaba el default de la cuenta. Es decir que el
  modelo con el que se generaba un informe podía cambiar sin que nadie
  tocara el proyecto — si cambiaba el default de la cuenta, o si alguien
  usaba `/model` en otra sesión.

  Los 42 cálculos del catálogo **no** dependen del modelo (los hace
  `analysis.py`, con tests y validación contra datos reales). Pero la
  comparación entre años y las métricas a medida del paso 6 se escriben en
  código libre en cada corrida: ahí el criterio del modelo es lo único que
  separa un cálculo correcto de uno inventado, y es justo donde un número
  puede terminar difiriendo de lo publicado por el INE sin justificación.

  Se usa el id completo y no el alias `opus` a propósito: un alias se
  movería solo a la próxima generación, y este proyecto prefiere que ese
  cambio sea una decisión explícita, con una corrida de validación de por
  medio. Dos tests lo sostienen: que el modelo esté fijado con id completo
  (no alias), y que `abrir_agente.bat` use el mismo que el subagente.

## [0.9.2] — 2026-08-15

### Agregado

- **Toda métrica del informe lleva ahora las mismas cinco partes**, en el
  mismo orden: el nombre, la pregunta que responde, **qué significa cada
  término según el criterio del INE**, por qué se eligió esa gráfica, y la
  gráfica.

  Nace de un informe generado real: las métricas de Empleo explicaban con
  la fórmula del INE qué es la tasa de actividad, empleo y desempleo, y
  otras métricas no explicaban ningún término. La diferencia no era una
  decisión — esas definiciones las escribía el modelo a mano durante la
  corrida, así que aparecían o no según se acordara. Es el mismo patrón
  que ya había fallado con los hooks y con el panorama de TV cable: una
  regla que depende de la memoria del modelo no se cumple pareja.

  Ahora hay un glosario fijo (`notebook_builder._GLOSARIO`) con 23
  términos —tasa de actividad/empleo/desempleo, informalidad, subempleo,
  pobreza e indigencia, hacinamiento, tipos de hogar, razón de
  dependencia, carencia estructural, escala FIES, quintil, victimización,
  denuncia formal, índice de acceso digital, índice territorial, etc.— y
  cada métrica declara cuáles usa. Cada definición describe **lo que de
  verdad calcula el proyecto**, verificado contra `analysis.py`, siguiendo
  el criterio del INE; no se transcriben textos oficiales sin verificar.

  Cuatro tests lo hacen cumplir: que toda métrica tenga las cinco partes,
  que ninguna quede sin términos declarados, que todo término declarado
  exista en el glosario, y que el glosario no acumule términos que nadie
  usa.

- Las instrucciones del agente explicitan que **la comparación entre años
  y las métricas a medida del paso 6 —lo único que queda en código libre—
  llevan exactamente la misma estructura de cinco partes**, y que si un
  término ya está en el glosario hay que reusar esa definición palabra por
  palabra en vez de redactar otra. Sin eso, el problema volvía por el
  único camino que quedó abierto.

## [0.9.1] — 2026-08-15

### Corregido

- **Ninguna explicación del catálogo depende ya de otra métrica.** La
  métrica "Inseguridad alimentaria severa por quintil de ingreso" decía
  *"la misma comparación del punto 23"*: obligaba a ir a buscar otra
  métrica para entenderla y, peor, tras la renumeración de la 0.9.0 ese
  "23" quedó apuntando a una métrica **distinta** (pasó a ser
  "Inseguridad alimentaria por región") sin que nada lo detectara. Se
  reescribieron las 7 explicaciones que dependían de otra ("la misma
  comparación", "lo mismo", "el índice anterior", "esos dos grupos") para
  que cada una se entienda sola.

  `test_ninguna_explicacion_del_catalogo_depende_de_otra_metrica` hace
  cumplir la regla de ahora en más: falla si una explicación referencia
  otra métrica por número o con una frase relativa. Verificado que atrapa
  los siete textos viejos sin marcar ninguno legítimo.

### Agregado

- **Los bloques con datos mensuales explican qué significa eso**, en una
  nota al principio del bloque (no repetida en cada métrica):
  - **Empleo**: cada número es el promedio de los 12 meses del año — se
    calcula el valor de cada mes por separado y después se promedian, así
    ningún mes pesa más que otro. No es una foto de un mes suelto.
  - **Seguridad y victimización**: todo se refiere al **mes anterior** a
    la entrevista, no al año entero. Si un número dice 5%, es el 5% que
    sufrió ese delito en un solo mes — no se puede leer como cifra anual
    ni comparar con estadísticas anuales de otras fuentes.
  - **FIES**: se calcula sobre una submuestra de hogares.

## [0.12.0] — 2026-08-16

### Agregado

- **Un informe ya no puede publicar un disparate sin que nada lo note**
  (`verificacion_plausibilidad.py`). Hasta ahora los chequeos verificaban
  que un porcentaje estuviera entre 0 y 100, y eso deja pasar casi
  cualquier error real: una tasa de desempleo de 45%, una pobreza de
  0,14% (una proporción confundida con porcentaje) o una tasa de empleo
  mayor que la de actividad son todas "porcentajes válidos" y todas
  imposibles.

  **No se trata de reproducir los cálculos del INE** —la metodología de
  este proyecto puede diferir legítimamente de la suya— sino de que un
  error grueso nunca llegue a un informe entregado. Son dos capas:

  1. **Identidades estadísticas**: relaciones que se cumplen siempre, por
     definición, sin depender de ninguna cifra externa. La tasa de empleo
     no puede superar a la de actividad; las tres tasas tienen que cerrar
     entre sí (`desempleo = (actividad − empleo) / actividad`); la
     indigencia no puede superar a la pobreza; la inseguridad severa no
     puede superar a la moderada o severa. Una violación acá es un bug
     seguro, no una diferencia de criterio.
  2. **Rangos de plausibilidad**: anchos a propósito, para atrapar
     disparates sin marcar variación legítima. Incluyen la crisis de 2002
     por arriba y escenarios mucho mejores que el actual por abajo — no
     son objetivos a cumplir, son los límites de lo posible.

  Los rangos se anclan en magnitudes que publica el propio INE (actividad
  ~64%, empleo ~59,5%, desempleo 7,0-7,6%, informalidad 22,8%), y cada uno
  lleva escrito de dónde sale: un test falla si alguno queda sin
  justificación, porque un rango sin motivo es una opinión disfrazada de
  verificación.

  De paso quedó confirmado que las cifras de este proyecto están en el
  orden correcto: desempleo 7,45% (2025) y 8,18% (2024) contra el 7,0-7,6%
  que publica el INE — diferencia chica y compatible con promediar los 12
  meses por separado.

## [0.11.0] — 2026-08-16

### Agregado

- **El formulario de áreas ya no ofrece bloques que quedarían vacíos.**
  Hasta ahora Brecha Digital, Hogares, Territorio y Vivienda se ofrecían
  siempre, "porque dependen únicamente de los datos de Hogares" — una
  suposición falsa. Se llevó puesta una corrida real: se eligió 2023 y se
  marcó solo Territorio, que ese año está **completamente vacío** (el INE
  no relevó el módulo C5); el catálogo quedaba sin ninguna métrica y el
  flujo volvía al mismo formulario sin explicar nada, como si fuera un
  error del programa.

  Peor era el caso silencioso: eligiendo Territorio **junto con** otro
  bloque, el informe salía sin ninguna métrica territorial y sin ningún
  aviso, porque el filtro recién actuaba al armar el catálogo.

  Ahora los **siete** bloques se filtran por disponibilidad real, y los
  que quedan afuera se listan con su motivo ("falta `c5_2` en los datos
  del INE", "necesita datos de Empleo"). Lo resuelve
  `verificacion_catalogo.bloques_disponibles(anio)`, que devuelve los
  argumentos de `plantilla_areas` ya calculados — el agente no computa
  nada a mano.

- **Los hooks dejan constancia en la bitácora cuando bloquean.** En una
  corrida real el notebook se ejecutó tres veces (83 s + 98 s + 83 s,
  contra los ~83 s de una sola pasada) y no había forma de saber si eso
  fue el trabajo legítimo de los hooks o retrabajo evitable, porque no
  dejaban ningún rastro. Ahora cada bloqueo queda en la misma línea de
  tiempo que los formularios y los tiempos de cada paso.

- **Ninguna cifra del "Resumen analítico final" puede estar inventada.**
  Nuevo hook (`gate-resumen-cifras-inventadas.cjs`) que verifica que cada
  número citado en el resumen exista de verdad en la salida ejecutada del
  notebook. Es el único lugar del informe donde el modelo transcribe
  números a prosa —todo el resto calcula con pandas y muestra el
  resultado— y es la parte que más gente lee.

  Diseñado para no dar falsos positivos, que ahí serían peores que el
  problema: acepta redondeos legítimos ("cerca del 14%" cuando el dato es
  14,14%), coma o punto decimal, no confunde años con estadísticas, no
  mira el cuerpo del informe y no bloquea un notebook sin ejecutar.

### Corregido

- **Los tests volvían a ensuciar la bitácora real**, ahora por el lado de
  Node: al hacer que los hooks registraran sus bloqueos, cualquier test
  que corriera un hook escribía en la bitácora de quien tuviera el
  proyecto en esa carpeta. Es la segunda vez que aparece el mismo
  problema (la primera fue por Python). Se cerró con un `conftest.py`
  *autouse* que redirige el log de los hooks para toda la suite, más la
  variable `ENCUESTA_HOGARES_BITACORA` — así un test nuevo no tiene que
  saber que ese riesgo existe.

## [0.10.0] — 2026-08-16

### Cambiado

- **El índice de desarrollo territorial ahora sí calcula los cuatro
  componentes que dice calcular.** El catálogo y el glosario decían que
  combinaba "pobreza, empleo, precariedad de vivienda y nivel económico",
  pero el cálculo usaba solo tres: **empleo nunca estuvo**. Lo encontró el
  dueño del proyecto mirando el heatmap del perfil territorial, que
  mostraba tres columnas donde el texto prometía cuatro.

  Se agregó el componente que faltaba en vez de corregir el texto, porque
  la definición con empleo es la que se quiere (y es la que usa el
  IDERE-UY, el antecedente para Uruguay que este proyecto cita). Se usa la
  **tasa de empleo** y no la de desempleo: es el indicador en positivo
  (más alto = mejor), así no hay que invertirlo.

  **Los valores del índice cambian** — no son comparables con los de un
  informe generado antes de esta versión.

  Nada lo había detectado porque los tests verificaban que el índice
  estuviera entre 0 y 1, no que su descripción coincidiera con sus
  componentes reales. Ahora hay tests que comparan una cosa con la otra.

- **Las columnas del heatmap dejan de mostrar nombres de variable.** Decían
  `pct_pobreza`, `pct_precariedad`, `estrato_promedio` — identificadores
  del código, ilegibles para el público del informe. Ahora dicen
  "Pobreza", "Precariedad de vivienda", "Empleo" y "Nivel económico".

- **Las métricas de Territorio (13-15) quedan no disponibles en los años
  sin datos de Empleo** (2019), porque el índice ahora lo necesita.

### Corregido

- **`normalizar_departamento` sobre los datos de Empleo, sin lo cual el
  índice quedaba vacío en silencio.** Los archivos de Empleo traen el
  departamento como "Artigas" y los de Hogares como "ARTIGAS":
  verificado contra los datos reales de 2025, de 19 departamentos
  coincidían **0**, y el `.dropna()` habría dejado el índice sin ninguna
  fila sin lanzar ningún error. Es exactamente el modo de falla que ya
  documentaba `preprocessing.normalizar_departamento`. Se agregó además
  un `assert` como red de seguridad por si el cruce vuelve a fallar.

- **Los números de métrica de las instrucciones del agente**, que habían
  quedado con la numeración vieja tras renumerar el catálogo de 43 a 42
  en la 0.9.0: citaban "métricas 37-43" cuando el catálogo llega a 42, y
  "métrica 36" para lo que pasó a ser la 35. Nueve referencias corregidas,
  con un test que ahora falla si alguna cita un número que no existe.

## [0.9.0] — 2026-08-15

### Eliminado

- **TV cable sale del proyecto por completo.** Era el eje del análisis
  original de 2019 y quedó como herencia cuando el foco pasó a ser la
  brecha digital: tener o no TV cable no dice nada sobre si un hogar está
  conectado. Decisión del dueño del proyecto, encontrada en una corrida
  real donde el informe entregado seguía abriendo con "Hogares con TV
  cable: 3.686 (40,13%)".

  **Por qué sobrevivió a la limpieza de la 0.6.0:** esa versión sacó
  cuatro métricas de cable **del catálogo** —la lista que elige el
  usuario—, pero las secciones que seguían apareciendo no eran métricas
  del catálogo sino *infraestructura fija* del informe
  (`notebook_builder.celdas_intro_brecha_digital`), que se agregaba
  automáticamente cada vez que se elegía el bloque "Brecha Digital", sin
  importar qué métricas se marcaran. Vivían en otra capa, así que limpiar
  el catálogo nunca las tocó.

  Se eliminan las tres secciones fijas ("Panorama general" con hogares con
  y sin cable, "Distribución por barrio" con el % de abonados, y
  "Composición de los hogares con y sin cable") y, con ellas, **la
  dimensión barrio completa**: los barrios se clasificaban en cuatro
  niveles según su % de cable, así que sin cable esa clasificación no
  tenía sobre qué construirse. Se van `resumen_conectividad` (en su forma
  vieja), `compute_penetracion_por_barrio`, `merge_penetracion`,
  `clasificacion_barrios_resumen`, `FILTROS_SUSCRIPCION`,
  `filtrar_segmento`, `promedio_edad_por_grupo`, `porcentaje_por_sexo`,
  sus cuatro gráficas, y las columnas `tipo_abonado`/`tiene_cable` de
  `config.py`.

- **Métrica 7 del catálogo** ("Clasificación de barrios por nivel de
  suscripción"). El catálogo pasa de 43 a **42 métricas, renumeradas del 1
  al 42 sin huecos** — misma convención que la 0.6.0. Si comparás con un
  informe generado antes de este cambio, los números de métrica de 7 en
  adelante están corridos en uno.

### Cambiado

- **El "Panorama general de conectividad" ahora mide internet**, que es lo
  que la sección siempre dijo medir: hogares con y sin conexión, en vez de
  con y sin TV cable.
- **La métrica 1** (brecha digital por nivel económico) compara ahora
  internet, computadora y streaming — tres tecnologías en vez de cuatro.
- **El índice de acceso digital pasa de 0-4 a 0-3.** Sus valores **no son
  comparables** con los de un informe anterior: antes sumaba TV cable como
  una de las cuatro tecnologías.

## [0.8.2] — 2026-08-15

### Cambiado

- **`tools/validar_con_datos_reales.py` ahora reporta todas las fallas de
  una corrida, no solo la primera.** Usaba `assert` sueltos, así que la
  primera falla abortaba todo: al cargar un año nuevo eso obligaba a un
  ciclo de corregir → volver a correr → descubrir la siguiente, un
  problema por corrida y varios minutos cada una. Con los datos de 2023
  hicieron falta cuatro corridas completas para descubrir cuatro
  problemas que ya estaban todos ahí desde la primera. Los `assert`
  siguen igual; lo que cambia es que cada bloque corre dentro de un
  `Recolector` que anota la falla y sigue. Al final imprime la lista
  completa y sale con código 1 si hubo alguna.

  Los bloques que dependen de otro que falló se marcan como OMITIDOS y no
  como fallas, para que el informe no se llene de consecuencias de un
  mismo problema. FIES, Empleo y Seguridad se revisan siempre, incluso si
  todo lo demás falló — es justo donde más suele cambiar el formato del
  INE de un año a otro.

- `jupyter` pasa de dependencia de desarrollo a dependencia normal: el
  paso 5 ejecuta el notebook con `jupyter nbconvert --execute`, así que
  hace falta para cualquier corrida. Funcionaba de casualidad porque
  `instalar.bat` instala `.[dev]`; quien instalara solo el paquete base
  quedaba sin poder generar un informe.

- `instalar.bat` ya no termina diciendo que abras una terminal y escribas
  `claude` —contrario a todo el diseño del proyecto, y a lo que dice el
  README— sino que manda a hacer doble clic en `abrir_agente.bat`.

### Documentación

- `CLAUDE.md` explica ahora qué es y qué no es `.claude/settings.json`:
  una lista de conveniencia para que no aparezcan prompts de aprobación,
  **no** una frontera de seguridad. `Bash(run_python.bat *)` más `Write`
  sin restricción de ruta equivalen a ejecución de código arbitrario ya
  aprobada — y es a propósito, porque el paso 5 consiste exactamente en
  escribir un `.py` y correrlo. Queda escrito también por qué restringir
  `Write` a rutas del proyecto rompería el flujo (los archivos de scratch
  van al scratchpad de Claude Code, fuera del repositorio) y qué es lo
  que de verdad acota el riesgo.

### Corregido

- **El servidor local de formularios ahora solo acepta respuestas de su
  propia página.** `do_POST` aceptaba cualquier POST sin mirar de dónde
  venía y respondía con `Access-Control-Allow-Origin: *`: cualquier
  página abierta en el navegador podía barrer los puertos de localhost
  desde JavaScript y contestar el formulario en nombre de la persona
  (elegir el año, marcar métricas, o cerrarle el flujo). Ahora se valida
  el `Origin` y se sacó el permiso de CORS, que nunca hizo falta.
- Un `Content-Length` inválido en un pedido al servidor de formularios
  tiraba un `ValueError` sin manejar dentro del hilo del servidor; ahora
  responde 400 y sigue atendiendo. Se agregó además un tope de tamaño al
  cuerpo del pedido.
- `instalar.bat` no verificaba si fallaba la descarga de Chromium: decía
  "Listo, ya está todo instalado" igual, y el problema recién aparecía al
  generar el PDF en medio de una corrida real.
- `.claude/settings.local.json` se ignoraba solo por el gitignore global
  del dueño del proyecto, no por el del repositorio: en cualquier otra
  computadora, o en un clone limpio, no estaba ignorado y se podía
  commitear sin querer.
- La bitácora crecía sin límite. Ahora rota al llegar a 2 MB y conserva
  una tanda anterior.
- Los marcadores del hook `gate-primer-paso` quedaban en la carpeta
  temporal para siempre, uno por sesión; ahora se limpian los de más de
  un día.

## [0.8.1] — 2026-08-15

### Corregido

- **La ventana de consola ahora se cierra sola al terminar.** Ni terminar
  el informe y apretar "Listo, gracias", ni apretar "Salir sin terminar
  el informe", cerraban la consola que abre `abrir_agente.bat`: quedaba
  viva de fondo indefinidamente. No era un fallo intermitente sino de
  diseño — `abrir_agente.bat` invocaba `claude "..."` en modo
  interactivo, y una sesión interactiva de Claude Code **no termina nunca
  por sí sola** (confirmado contra la documentación oficial de la CLI: no
  existe ninguna forma nativa de que termine al final de un turno). Como
  `claude` nunca retornaba, las últimas líneas del `.bat` no se
  ejecutaban jamás.

  Ya se había intentado resolver con `claude -p` y se revirtió porque
  rompía el flujo. La solución ahora no depende de que Claude Code
  termine solo: `src/encuesta_hogares/cierre.py` cierra la sesión desde
  adentro cuando el flujo termina de verdad, y el `.bat` retoma el
  control y cierra su ventana con normalidad. Solo actúa si fue
  `abrir_agente.bat` quien lanzó la sesión, así que una sesión de
  `claude` abierta a mano (mantenimiento, o el "uso manual" del README) y
  la suite de tests nunca se cierran solas por accidente.

  "Crear un nuevo informe" **no** cierra nada — ahí el agente reinicia
  desde el paso 1 en la misma conversación (hay un test dedicado a que
  eso no se rompa).

## [0.8.0] — 2026-08-15

### Agregado

- **Comparar entre años, métrica por métrica, no todo el catálogo de
  una vez.** Antes, un solo checkbox global aplicaba la comparación a
  *todas* las métricas elegidas del catálogo; ahora cada métrica tiene su
  propia casilla "comparar esta métrica entre años". Nace de una
  pregunta real: elegir 3 métricas y querer comparar solo una de ellas no
  era posible. `formularios.plantilla_catalogo()` agrega
  `metricas_comparadas` a la respuesta (subconjunto de `metricas`, ya
  filtrado a números que también estén ahí); `comparar_anios` sigue
  siendo un único conjunto de años, compartido por las métricas que se
  comparen.
- El formulario del catálogo ya no deja confirmar la selección con
  `metricas` vacía y sin ninguna propuesta libre — antes, esa
  combinación (posible sobre todo si se tildaba "comparar" sin elegir
  ninguna métrica) quedaba librada a que el agente la interpretara bien.

## [0.7.0] — 2026-08-15

### Agregado

- **`notebook_builder.py`: arma mecánicamente las celdas de las 43
  métricas fijas del catálogo, para el año base.** Nace de una medición
  real — de los ~10 minutos que tardaba el paso 5 en una corrida con
  comparación entre años, 7m11s eran el modelo escribiendo texto que,
  para el catálogo fijo, siempre es la misma llamada a la misma función
  ya testeada. Se probó a fondo contra datos reales (2019/2024/2025, las
  43 métricas, con un kernel de Jupyter de verdad) y quedó limpio.
- `preprocessing.normalizar_departamento`: deja "departamento" en
  mayúsculas consistentes entre años (se escribe distinto según el año
  de origen). Sin esto, cruzar tablas de años distintos por departamento
  cruza cero filas en vez de fallar con un error claro — encontrado
  probando el módulo nuevo, corregido para que el camino libre también
  lo use.
- `analysis.tabla_a_dict`: convierte una tabla de una categoría por fila
  en el dict que `combinar_por_anio` espera — antes se reescribía a mano
  en cada notebook que comparaba 3+ años.
- La detección de qué formato de archivo (.sav vs. CSV combinado) usa un
  año dado ahora sigue el mismo criterio general que ya usaba
  `tools/validar_con_datos_reales.py`, en vez de asumir que solo 2019 usa
  `.sav`.

### Decisión de diseño

- **La comparación entre años queda en código libre, no mecanizada.** Se
  probó mecanizarla también, y corriéndola contra datos reales aparecieron
  dos bugs reales (variables de un año pisando las de otro; el problema de
  "departamento" de arriba). Cruzar datos de años distintos es justo el
  tipo de tarea donde conviene que alguien note que un resultado no
  cierra y lo investigue, no una plantilla fija — decisión tomada en
  conjunto con el dueño del proyecto. Las métricas a medida del paso 6
  tampoco se mecanizan, por el mismo motivo de siempre (no tienen función
  ya validada a la que apuntar).

## [0.6.0] — 2026-08-14

### Eliminado

- **Cuatro métricas del bloque Brecha Digital, sacadas del catálogo por
  completo**: "Suscripción a TV cable por barrio", "Relación entre el
  barrio y el nivel económico", "Montevideo frente al resto del país" y
  "¿El streaming reemplaza a la TV cable?" (antes 7, 9, 10 y 11). El
  catálogo pasa de 47 a 43 métricas, renumeradas del 1 al 43 sin huecos
  (ver el mapeo completo en el historial de `formularios.py` si hace
  falta comparar con un informe generado antes de este cambio). Las
  funciones que quedaron sin ningún uso real se borraron con ellas:
  `analysis.streaming_vs_cable`, `analysis.suscripcion_vs_nivel_economico`,
  `preprocessing.compute_penetracion_nacional`,
  `preprocessing.merge_penetracion`,
  `visualization.plot_streaming_vs_cable` y
  `visualization.plot_heatmap_suscripcion_vs_economico`. La tabla de
  penetración por barrio (`preprocessing.compute_penetracion_por_barrio`)
  se mantiene — la sigue usando la métrica 7 actual ("Clasificación de
  barrios por nivel de suscripción") y la sección "Distribución por
  barrio" que se muestra siempre que se elige el bloque Brecha Digital.

## [0.5.0] — 2026-08-14

### Agregado

- **Nueva opción en el catálogo de métricas (paso 4): comparar todo lo
  elegido con otros años, cualquier cantidad.** Antes había que pedirlo
  escribiéndolo a mano en "otra métrica" cada vez; nace de una sugerencia
  real registrada en la bitácora del agente, después de resolver el caso
  de 2 años dos veces a mano (Empleo, luego Seguridad) sin necesitar
  ninguna función nueva en `src/`. `formularios.plantilla_catalogo()`
  ahora devuelve también `comparar_anios` (lista de enteros, vacía si no
  se pidió). Para exactamente 2 años en total reusa el patrón ya
  documentado en `docs/CONVENCIONES_DE_GRAFICAS.md`
  (`analysis.diferencia_entre_tablas` + `visualization.plot_dumbbell`);
  para 3 o más, generaliza a cualquier métrica el patrón que antes solo
  existía para las tasas de Empleo, con dos funciones nuevas y genéricas:
  `analysis.combinar_por_anio` + `visualization.plot_serie_por_anio` —
  ambas genéricas para toda métrica del catálogo (reciben el resultado ya
  calculado por año, no vuelven a calcular nada), sin un motor de
  comparación automática por separado para cada una de las 47 métricas.

## [0.4.0] — 2026-08-13

### Cambiado (cambia el número de pobreza/indigencia de 2024 — impacta la comparación con informes generados antes de esta versión)

- **Pobreza e indigencia de 2024 ahora usan la metodología de canasta 2017
  (antes: canasta 2006).** El INE publica las dos versiones a la vez en el
  archivo de 2024 (año de transición) — se decidió (confirmado con el
  usuario) preferir la metodología vigente para 2024 también, no solo
  para 2025 en adelante, porque da comparabilidad real entre esos dos
  años. Efecto real, verificado con los datos: la pobreza ponderada de
  2024 pasa de 6.9% (canasta 2006) a 12.99% (canasta 2017) — un cambio
  grande, esperado dado que es un cambio de vara de medición, no un error.
  2019 queda como el único año con la metodología vieja sin alternativa
  (no hay dato de canasta 2017 para ese año) — diferencia metodológica
  documentada, mismo criterio que ya se usa para Vivienda (12 vs. 4
  carencias entre años).

### Agregado (soporte para datos de 2025)

Encontrado y corregido durante la primera corrida real con datos de 2025
— cada punto verificado contra los archivos reales, no supuesto:

- El INE cambió varios nombres/formatos de archivo para 2025: los 12
  mensuales de Empleo pasan de `ECH_MM_AA.csv` a `ECH_MM_AAAA.csv`, y el
  combinado de Hogares/Personas pasa de `ECH_{año}.csv` a
  `ECH_{año}_implantacion.csv`. `config.empleo_files`/`hogares_csv_file`
  ahora reconocen ambos patrones.
- Empleo 2025 dejó de traer `INFORMAL`/`SECTOR_F`/`SIT_OCUP`
  precalculadas. Informalidad se recalcula desde `f82` (aporte a fondo de
  pensión) con el mismo criterio que usa el paquete oficial de R del INE
  para la ECH (`employment_restrictions()`,
  github.com/calcita/ech/R/employment.R) — verificado contra la cifra que
  publicó el propio INE para 2025 (21.94% calculado vs. 22.8% publicado).
  Situación ocupacional por sector (métrica 40) sigue sin variable de
  reemplazo identificada — no se le inventó ninguna.
- `verificacion_catalogo.aviso_metricas_no_disponibles(año)`: nuevo
  chequeo por métrica (no solo por bloque) que avisa antes de que el
  usuario elija en el catálogo una métrica que no se puede calcular ese
  año, en vez de que la corrida falle recién a mitad de camino.
- `config.MESES_LABELS` y una regla nueva contra `print()` de estructuras
  crudas de Python/pandas/numpy en una celda del informe (ver
  `docs/METODOLOGIA.md`, sección 3) — encontrado en el informe real: una
  lista de meses se imprimió como `[np.int64(1), ...]` y varias métricas
  de Empleo mostraban el dict/DataFrame crudo debajo de su propia gráfica.
- `analysis.tasas_actividad_empleo_desempleo_por_anio` +
  `visualization.plot_tasas_por_anio`: comparación de una métrica entre
  corridas de años no necesariamente consecutivos, con el eje temporal en
  su escala real (no categórica) — para no sugerir visualmente una
  tendencia continua entre años sin encuesta propia.
- `formularios.plantilla_datos` ya no recibe la carpeta de destino como
  parámetro de texto libre — la calcula ella misma con `config.DATA_DIR`.
  Encontrado en una corrida real: la pantalla mostró `data/2025` (ruta
  relativa) en vez de la ruta real de Windows. Tampoco promete ya un
  formato de archivo fijo (antes decía "dos archivos .sav", ya falso
  desde 2024).
- `data_loader.fix_entidad_html_rota`: un tercer patrón de corrupción de
  acentos en los CSV del INE (distinto a los dos ya conocidos) —
  caracteres que llegan como `<e9>` en vez de "é", como una entidad HTML
  numérica a la que se le cayó el `&#x`/`;`. Encontrado en departamentos
  reales ("San Jos<e9>", "Paysand<fa>", "Tacuaremb<f3>").

## [0.3.2] — 2026-08-13

### Corregido (métricas 3, 9 y 11 — Brecha Digital: no tenían función de análisis propia)

- **Calidad de conexión por nivel económico (3), relación entre barrio y
  nivel económico (9), y streaming vs. TV cable (11) no tenían ninguna
  función en `analysis.py` que las calculara** — quedaban libradas a que
  el agente improvisara el cálculo dentro del notebook en cada corrida,
  sin test que lo cubriera. En la métrica 9 ese cálculo improvisado
  (`plot_heatmap_suscripcion_vs_economico`) además vivía sin ponderar,
  directamente adentro de la función de gráfica — un tercer lugar donde
  se había colado el mismo problema de la 0.3.0/0.3.1, esta vez en
  `visualization.py`, un módulo que ninguna revisión anterior había
  mirado para esto.
- Se construyó, a partir de esto, un manifiesto explícito
  métrica→función (`verificacion_catalogo.py`) que se revisa en cada
  `pytest`: cada una de las 47 métricas del catálogo tiene que tener al
  menos una función real y llamable que la implemente, o el test falla.

### Agregado

- `analysis.composicion_categorica_ponderada_por`: % ponderado de una
  variable categórica de más de dos valores, agrupado por otra columna
  — la versión sin panel mensual de `composicion_categorica_por_mes_promedio`,
  para datos de Hogares. Tres usos concretos nuevos:
  `calidad_conexion_por` (métrica 3), `suscripcion_vs_nivel_economico`
  (métrica 9), `streaming_vs_cable` (métrica 11).
- `visualization.plot_composicion_categorica`: wrapper público y
  parametrizado de barras 100% apiladas, para reutilizar en cualquier
  métrica categórica ponderada sin necesidad de un wrapper con título
  hardcodeado (usado ahora en la métrica 40, situación ocupacional).
- `encuesta_hogares.verificacion_catalogo`: el manifiesto y su chequeo
  automático — ver "Corregido" arriba.
- `verificacion_ponderacion` ahora también escanea `visualization.py`
  (antes solo `analysis.py`/`preprocessing.py`), con dos excepciones
  documentadas en `ALLOWLIST` para promedios de referencia sobre
  columnas ya ponderadas.

### Eliminado

- `analysis.proporcion_cruzada`: crosstab sin ponderar, no usada por
  ninguna métrica real del catálogo (código muerto que además invitaba
  a reintroducir el mismo descuido) — reemplazada por
  `composicion_categorica_ponderada_por`.

## [0.3.1] — 2026-08-13

### Corregido (cambia los números de las métricas 7, 8, 9 y 10 — Brecha Digital)

- **Suscripción a TV cable por barrio y por departamento (métricas 7-10)
  se calculaban sin ponderar**, un descuido que el retrofit de la 0.3.0 no
  había alcanzado a cubrir porque vivía en `preprocessing.py`
  (`compute_penetracion_por_barrio`, `compute_penetracion_nacional`), no
  en `analysis.py`. Verificado con datos reales de 2019: a nivel de todo
  Montevideo el efecto es chico (60.9% sin ponderar → 60.85% ponderado,
  la muestra grande ya compensaba bastante), pero a nivel de barrio —
  donde la muestra por barrio es mucho más chica — la diferencia llega
  hasta 2.87 puntos porcentuales (barrio Manga), suficiente para mover a
  un barrio de un nivel de suscripción a otro en la clasificación por
  cuartiles (métrica 8).

### Agregado

- `encuesta_hogares.verificacion_ponderacion`: chequeo automático (corre
  en cada `pytest`) que recorre `analysis.py` y `preprocessing.py`
  buscando cálculos estadísticos "crudos" (`.mean()`, `.median()`,
  `.value_counts()` fuera de los helpers ya ponderados) que no estén
  documentados como excepción legítima en su `ALLOWLIST`. Encontrar el
  bug de arriba mientras se armaba esta verificación fue la prueba de que
  hacía falta: una revisión manual completa ya se había hecho una vez
  (0.3.0) y aun así no lo detectó.

## [0.3.0] — 2026-08-13

### Cambiado (cambia los números de casi todas las métricas de Hogares — impacta la comparación con informes generados antes de esta versión)

- **Toda estadística de Hogares/Personas ahora se pondera por el
  ponderador de muestreo del INE** (`pesoano` en 2019, `W_ANO` desde
  2024). Antes, solo FIES/Empleo/Victimización ponderaban (cada uno con
  su propio ponderador de módulo) — pobreza, hacinamiento, tipos de
  hogar, jefatura, razón de dependencia, vivienda, territorio y brecha
  digital se calculaban como proporción simple sobre la muestra, sin
  corregir por el diseño muestral. Encontrado en una revisión real:
  hallazgo verificado con datos de 2019, pobreza nacional 4.79% sin
  ponderar contra 5.87% ponderada — casi 1.1 puntos porcentuales de
  diferencia, suficiente para cambiar una conclusión.
- Nuevos helpers genéricos de ponderación en `analysis.py`:
  `pct_ponderado`/`pct_ponderado_por` (ya existía, ahora reutilizado
  también para Hogares), `media_ponderada_por`, `proporcion_ponderada`,
  `mediana_ponderada`.
- `preprocessing.clasificar_tipo_hogar` ahora requiere un segundo
  parámetro `hogares` (antes solo `personas`), para poder traer el
  ponderador al resultado — cualquier llamada existente con un solo
  argumento hay que actualizarla.
- `ResumenConectividad` (dataclass) cambió `pct_con_cable`/`pct_sin_cable`
  de propiedades calculadas a campos precalculados y ponderados — el uso
  externo (`resumen.pct_con_cable`) no cambia, pero ahora refleja la
  población, no la muestra.

### Agregado

- `analysis.grupos_con_muestra_chica`: detecta grupos con menos de 30
  observaciones (umbral clásico de institutos de estadística) antes de
  publicar una métrica agrupada — operacionaliza la regla de "celdas
  chicas" que ya estaba escrita en `docs/METODOLOGIA.md` pero nunca tuvo
  una implementación concreta.
- Nueva sección en `docs/METODOLOGIA.md` documentando por qué el proyecto
  **no** calcula intervalos de confianza ni tests de significancia (los
  microdatos públicos no traen las variables de diseño muestral
  necesarias — calcularlo igual daría una precisión falsa).

## [0.2.0] — 2026-08-12

### Cambiado (impacta la comparación entre informes de distintos años/corridas)

- **El catálogo pasó de 44 a 47 métricas, con renumeración completa.** Un
  informe generado antes de esta versión tiene números de métrica distintos
  a uno generado después — no asumir que "métrica 22" significa lo mismo en
  ambos.
- **Vivienda ya no depende de tenencia de tecnología.** Antes comparaba
  condiciones estructurales "según acceso a celular/streaming/internet"; ahora
  mide precariedad estructural real (índice de conteo de carencias, con
  fundamento en UN-Habitat, el Adequate Housing Index del Banco Mundial, y el
  NBI-vivienda del INE Uruguay).
- **Territorio ya no es suscripción a TV cable por barrio/departamento.**
  Ahora es un índice sintético de desarrollo territorial (pobreza + empleo +
  precariedad de vivienda + estrato, normalizado), siguiendo el IDERE-UY
  (IECON-UdelaR) y el Índice de Desarrollo Regional de CEPAL/ILPES. Las
  métricas viejas de tecnología por barrio se reubicaron en Brecha Digital
  (ahí es donde corresponde la tecnología, no se perdieron).
- **Toda métrica lleva gráfica, sin excepción** — incluidas las que resumen
  un solo valor o una diferencia entre dos grupos (usan dumbbell chart,
  método nuevo en el proyecto).
- **Las justificaciones de gráfica ahora exigen cita académica y, cuando
  aplica, la fórmula exacta** — antes se evitaba la cita a propósito, por
  considerarla ruido para un público no técnico; se revirtió ese criterio.
- Se eliminó la métrica de "detalle de barrios" (dos tablas presentadas como
  si fueran gráficas).

### Agregado

- Hook estructural que bloquea la ejecución del notebook si alguna métrica
  no tiene gráfica o su justificación no cita una fuente.
- Función genérica de dumbbell chart (`visualization.plot_dumbbell`).
- Botón "crear un nuevo informe" y "salir sin terminar" en todas las
  pantallas del flujo guiado.
- Recomendación de correr el informe por bloques (2 a 5 min cada uno) en vez
  de las 47 métricas de una sola corrida, para no agotar el límite de uso del
  plan de Claude a mitad de camino.
- Lint (`ruff`) y cobertura de tests (`pytest-cov`) al CI.
- Test permanente de integridad del catálogo (numeración sin huecos ni
  duplicados).
- `tools/verificar_sincronizacion.py`: detecta diferencias entre esta copia
  y `origin/main` (para quien mantiene el proyecto, no parte del flujo del
  agente).

### Corregido

- Bug real de compatibilidad con Python 3.9 (sintaxis de anotaciones que
  requería 3.10+, sin que el CI lo detectara).
- `instalar.bat` ya no le pregunta al usuario cómo prefiere ejecutarse — el
  agente lo corre solo, sin interrumpir la corrida con una pregunta que un
  usuario sin conocimientos técnicos no podría responder.
- Barras verticales sin rotar en comparaciones de 19 departamentos (nombres
  largos, ilegibles) pasaron a horizontales.
- Variable muerta en `plantilla_bienvenida`, import sin uso, y comparaciones
  `== True/False` en tests (encontrados por `ruff`).

## Antes de 0.2.0

Sin versionar formalmente. Ver `git log` para el historial completo, desde
el análisis original de 2019 hasta la introducción del catálogo de métricas
por bloques.
