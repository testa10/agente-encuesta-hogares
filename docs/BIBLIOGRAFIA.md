# Bibliografía

Todas las fuentes académicas e institucionales consultadas para diseñar el
catálogo de métricas y elegir el tipo de gráfica de cada una, en un solo
lugar. `.claude/agents/encuesta-hogares.md` sigue siendo la fuente de
verdad sobre *qué* fuente respalda *qué* métrica puntual (buscar el nombre
del autor ahí para ver el contexto exacto); este documento es el índice
único para auditar o reutilizar una cita sin tener que rastrearla.

Organizado por tema. Dentro de cada tema, alfabético por autor/organismo.

## Visualización de datos (aplica a cualquier bloque, ver `docs/CONVENCIONES_DE_GRAFICAS.md`)

- Cleveland, W.S. & McGill, R. (1984). "Graphical Perception: Theory,
  Experimentation, and Application to the Development of Graphical
  Methods". *Journal of the American Statistical Association*. Fundamento
  de por qué el proyecto usa barras horizontales para categorías con
  nombres largos, y por qué evita gráficos de torta con muchas categorías
  — la percepción de posición/longitud es más precisa que la de ángulos.
- Few, S. *Show Me the Numbers*. Fundamento del uso de barras agrupadas
  para comparación directa entre grupos.
- Hofmann, H., Wickham, H. & Kafadar, K. (2017). "Letter-Value Plots:
  Boxplots for Large Data". *Journal of Computational and Graphical
  Statistics*. Referencia para el día que el catálogo incluya una métrica
  de distribución continua con muestra grande — mejora sobre el boxplot
  clásico (`seaborn.boxenplot()`). Todavía no hay ninguna métrica que lo
  necesite.
- Knaflic, C.N. — *storytellingwithdata.com*, "More on slopegraphs"
  (2014). Uno de los tres fundamentos del dumbbell/slope chart
  (`visualization.plot_dumbbell`).
- Nightingale / Data Visualization Society. "Beyond the Bar: Alternative
  Methods for Visualizing Two Points of Change". Segundo fundamento del
  dumbbell chart.
- Tufte, E. (slopegraphs, años 80). Tercer fundamento del dumbbell chart —
  el originador del formato.
- Weissgerber, T.L. et al. (2015). "Beyond Bar and Line Graphs: Time for a
  New Data Presentation Paradigm". *PLOS Biology*. Fundamento de por qué
  el proyecto evita el patrón "dynamite plot" (barra + error, sin mostrar
  la distribución real) para variables continuas — ver la nota en
  `visualization.plot_composicion_edades`.

## Brecha Digital y Hogares (métricas 1-17)

- CEPAL — Observatorio de Desarrollo Digital de América Latina y el Caribe:
  https://desarrollodigital.cepal.org/es/indicadores
- CEPAL — "La brecha digital de género: reflejo de la desigualdad social",
  Nota para la Igualdad N°10:
  https://oig.cepal.org/sites/default/files/notas_para_la_igualdad_ndeg10_-_brecha_digital_de_genero.pdf
- CEPALSTAT (CEPAL/CELADE) — jefatura de hogar, tipos de hogar,
  hacinamiento, razón de dependencia demográfica:
  https://statistics.cepal.org/portal/cepalstat/
- A4AI — estándar "Meaningful Connectivity":
  https://a4ai.org/news/what-is-meaningful-internet-access-conceptualising-a-holistic-ict4d-policy-framework/
- Muñoz, R. — "Brechas de acceso digital: cambio histórico y ciclo vital"
  (aplica el enfoque de cohorte a esta misma encuesta), *Revista de
  Ciencias Sociales*, UdelaR:
  https://rcs.cienciassociales.edu.uy/index.php/rcs/article/view/261
- UIT/ITU — ICT Development Index:
  https://www.itu.int/en/ITU-D/Statistics/Pages/IDI/default.aspx

## Territorio (métricas 18-20)

- CEPAL — "Guía metodológica para el diseño de indicadores compuestos de
  desarrollo sostenible" (2009): https://repositorio.cepal.org/handle/11362/3663
- CEPAL/ILPES — "Panorama del desarrollo territorial de América Latina y
  el Caribe" (Índice de Desarrollo Regional):
  https://www.cepal.org/es/publicaciones/tipos/panorama-desarrollo-territorial-america-latina-caribe
- Rodríguez Miranda, A.; Vial Cossani, C.; Centurión, I.; Pérez Fernández,
  M. (2024). "Índice de Desarrollo Regional Uruguay 2006-2022
  (IDERE-UY)". IECON-FCEA/UdelaR, financiado por ANII (Fondo María
  Viñas): https://ideas.repec.org/p/ulr/wpaper/dt-01-24.html

## Vivienda (métricas 21-25)

- Arriagada, C. (2003). "Perfil de déficit y políticas de vivienda de
  interés social". CEPAL: https://repositorio.cepal.org/handle/11362/5711
- Bramati, M. et al. (2021). "Introducing the Adequate Housing Index
  (AHI)". World Bank Policy Research Working Paper 9830:
  https://documents.worldbank.org/en/publication/documents-reports/documentdetail/936291631846076967
- CELADE/CEPAL (1996). Metodología de déficit habitacional cualitativo vs.
  cuantitativo (sin URL directa — ver Arriagada 2003 arriba, que la
  retoma).
- INE Uruguay, FCS-UdelaR, IECON, MIDES (coord. Calvo, J.J.) (2013).
  "Atlas Sociodemográfico y de la Desigualdad del Uruguay", Fascículo 1
  (NBI): https://www.ine.gub.uy/atlas-sociodemografico-y-de-la-desigualdad-del-uruguay
- UN-Habitat/UNSD (2020). Metadatos del indicador SDG 11.1.1 ("durability
  of housing"):
  https://unhabitat.org/sites/default/files/2020/06/metadata_on_sdg_indicator_11.1.1.pdf

## Seguridad alimentaria (FIES, métricas 26-32)

- FAO — metodología FIES (Food Insecurity Experience Scale): umbral
  estándar de probabilidad (modelo Rasch) usado para clasificar
  inseguridad alimentaria moderada-o-severa y severa (ver
  `config.UMBRAL_FIES`; sin URL directa registrada — buscar "FIES
  methodology FAO" para la documentación oficial vigente).

## Empleo (métricas 33-40)

- OIT/ILO — Indicadores Clave del Mercado de Trabajo (KILM):
  https://www.ilo.org/resource/key-indicators-labour-market-kilm
- "Se profundizó la brecha de género en el mercado laboral" — Ámbito:
  https://www.ambito.com/uruguay/se-profundizo-la-brecha-genero-el-mercado-laboral-n6096977
- "El desempleo entre los más jóvenes cerró cerca del 25% en 2024" — Ámbito:
  https://www.ambito.com/uruguay/el-desempleo-los-mas-jovenes-cerro-cerca-del-25-2024-n6108458
- "Subempleo e informalidad afectan a casi 3 de cada 10 ocupados en
  Uruguay" — La Mañana:
  https://www.xn--lamaana-7za.uy/actualidad/trabajo-subempleo-e-informalidad-afectan-a-casi-3-de-cada-10-ocupados-en-uruguay/

## Seguridad y Victimización (métricas 41-47)

- Manual para Encuestas de Victimización — UNODC/UNECE:
  https://www.unodc.org/documents/data-and-analysis/Crime-statistics/Manual_Victimization_surveys_2009_spanish.pdf
- "Qué porcentaje de delitos son denunciados a la Policía, según informe
  del INE" — Montevideo Portal:
  https://www.montevideo.com.uy/Noticias/Que-porcentaje-de-delitos-son-denunciados-a-la-Policia-segun-informe-del-INE-uc914924

## Fuente de los datos

Instituto Nacional de Estadística (INE) — Encuesta Continua de Hogares (ECH):
https://www4.ine.gub.uy/Anda5/index.php/catalog/Encuestas_a_hogares

---

**Cómo usar esto al agregar una métrica nueva:** si la fuente consultada
ya está acá, no hace falta volver a buscarla. Si es nueva, agregarla en
la sección del bloque que corresponda (o crear una nueva si no encaja en
ninguna) y también en la nota de ese bloque en
`.claude/agents/encuesta-hogares.md`, que es donde el agente arma la
sección "Fuentes de consulta para alineación de métricas" de cada informe
— este archivo es el índice, no reemplaza esas notas.
