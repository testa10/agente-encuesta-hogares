# Changelog

Registro de cambios relevantes del proyecto, pensado para quien generó un
informe con una versión anterior y quiere saber qué cambió metodológicamente
antes de comparar corridas de años distintos. Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

El proyecto no versionó formalmente sus primeras ~30 revisiones (desde el
análisis original de 2019 hasta la introducción del catálogo por bloques
opt-in) — el historial completo de esos cambios está en `git log`. Este
changelog arranca en la versión donde se formalizó el versionado.

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
