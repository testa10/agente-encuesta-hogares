# Changelog

Registro de cambios relevantes del proyecto, pensado para quien generó un
informe con una versión anterior y quiere saber qué cambió metodológicamente
antes de comparar corridas de años distintos. Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

El proyecto no versionó formalmente sus primeras ~30 revisiones (desde el
análisis original de 2019 hasta la introducción del catálogo por bloques
opt-in) — el historial completo de esos cambios está en `git log`. Este
changelog arranca en la versión donde se formalizó el versionado.

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
