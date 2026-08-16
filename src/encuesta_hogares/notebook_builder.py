"""Arma mecánicamente las celdas de markdown+código del notebook para las
43 métricas fijas del catálogo, para el año base elegido — reemplaza,
para esas métricas, la parte de paso 5 donde el modelo escribía ese
código a mano en cada corrida.

Nace de una medición real: de los ~10 minutos que tardaba el paso 5 en
una corrida con 13 métricas y comparación de 3 años, 7m11s eran el modelo
generando el texto del script — no cómputo. Ese texto es, para las 43
métricas del catálogo, siempre la misma llamada a la misma función ya
testeada (ver `verificacion_catalogo.MANIFEST`) con el mismo criterio de
agrupación: no hay nada que "pensar" ahí que valga la pena volver a
escribir cada vez.

**Qué NO cubre este módulo — a propósito:**

- Las métricas a medida que la persona propone en el paso 6 (campo libre
  del catálogo, o una pregunta nueva a mitad de conversación). Esas no
  tienen entrada en MANIFEST ni texto fijo acá; siguen escribiéndose con
  el mismo criterio de rigor de siempre, en código Python libre.
- **La comparación entre años.** Se probó mecanizarla acá (con dos
  helpers genéricos para el patrón dumbbell/serie), y en una corrida
  completa contra datos reales encontró dos bugs de verdad — variables de
  un año pisando las de otro, y "departamento" escrito distinto entre
  años haciendo que un cruce diera cero filas en vez de un error claro.
  Los dos ya están corregidos, pero decidido en conjunto con el dueño del
  proyecto: cruzar datos de años distintos es justo el tipo de tarea
  donde conviene que seguir teniendo a alguien (o algo) que note que un
  resultado no cierra y lo investigue, no una plantilla fija — así que la
  comparación entre años se sigue escribiendo en código libre, con el
  mismo criterio ya documentado en `docs/CONVENCIONES_DE_GRAFICAS.md`
  (2 años → `diferencia_entre_tablas` + `plot_dumbbell`; 3+ →
  `combinar_por_anio` + `plot_serie_por_anio`) y las reglas de
  `preprocessing.normalizar_departamento`/`analysis.tabla_a_dict` que
  quedaron de esa prueba — ambas funciones reales, con test, para que el
  camino libre tampoco tenga que reinventarlas.

Mezclar plantillas fijas y código libre en el mismo notebook es
intencional: cada celda de este módulo es indistinguible, en el `.ipynb`
final, de una escrita a mano — el criterio de calidad (pregunta guía en
markdown antes del código, gráfica con eje anclado en cero, sin prints
crudos) es el mismo para las dos.

Cada llamada a `analysis.py`/`preprocessing.py`/`visualization.py` de
acá está tomada, sin modificar el criterio, de
`tools/validar_con_datos_reales.py` (ya validada contra datos reales de
verdad) — nunca inventada para este módulo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from . import entrega, formularios


@dataclass
class Celda:
    markdown: str
    codigo: str


# ============================================================================
# Preparación de datos: siempre las mismas variables, para el año base
# elegido — nada de comparación entre años acá (ver docstring del módulo).
# ============================================================================

_TEXTO_PONDERADO = '''"""La palabra 'ponderado' aparece en casi todos los porcentajes de este informe.
La Encuesta Continua de Hogares no encuesta a todos los hogares del país en la
misma proporción en que existen en la realidad — un departamento chico, por
ejemplo, puede terminar levemente sub o sobrerrepresentado en la muestra real
respecto a su peso real en la población. Para corregir eso, el INE le asigna a
cada hogar encuestado un 'ponderador': un factor que ajusta cuánto pesa ese
hogar al calcular un promedio o porcentaje, para que el resultado final
represente a toda la población, no solo a quienes quedaron en la muestra tal
cual. Es el mismo criterio que usa el propio INE en sus publicaciones
oficiales, no una decisión de este informe."""'''


def celda_preparacion_datos(anio_base: int, incluir_fies: bool) -> Celda:
    """La única celda que siempre se genera — infraestructura, no un bloque
    temático (ver docs/METODOLOGIA.md, sección 1). Envuelve la carga con
    `bitacora.medir("carga_de_datos")`, como indica el paso 5 del agente.
    """
    markdown = "## Preparación de datos\n\n" + _TEXTO_PONDERADO.strip('"')
    fies_extra = ""
    if incluir_fies:
        fies_extra = '''
    if config.datos_disponibles(ANIO).get("fies"):
        fies_clasificado = preprocessing.prepare_fies(data_loader.load_fies(config.fies_file(ANIO)))
        fies_clasificado["quintil_ingreso"] = (
            fies_clasificado["quintil_ingreso"].astype("Int64").map(lambda q: f"Quintil {q}")
        )
    else:
        fies_clasificado = None'''

    codigo = f'''ANIO = {anio_base}

with bitacora.medir("carga_de_datos"):
    # Detección de formato general (no solo "es 2019 o no") - el mismo
    # patrón que ya usa tools/validar_con_datos_reales.py: hasta 2023 es
    # .sav (uno por año, sin nombre de archivo fijo), desde 2024 es el CSV
    # combinado.
    if config.hogares_csv_file(ANIO).exists():
        hogares, personas = data_loader.load_hogares_personas_csv(ANIO)
    else:
        carpeta = config.DATA_DIR / str(ANIO)
        hogares = data_loader.load_hogares(sorted(carpeta.glob("H_*.sav"))[0])
        personas = data_loader.load_personas(sorted(carpeta.glob("P_*.sav"))[0])
    hogares = preprocessing.normalizar_departamento(hogares)
    hogares_mdeo = preprocessing.prepare_hogares_montevideo(hogares)
    hogares_cond = preprocessing.decode_condiciones_vivienda(hogares)
    hogares_cond["pobre"] = hogares_cond["pobre"] == 1.0
    hogares_cond["nivel_economico"] = preprocessing.classify_nivel_economico(hogares_cond["estrato_tipo"])
    hogares_ext = preprocessing.prepare_hogares_extendido(hogares_mdeo)
    hogares_ext["calidad_conexion"] = preprocessing.clasificar_calidad_conexion(hogares_ext)
    tipo_hogar = preprocessing.clasificar_tipo_hogar(personas, hogares)
    hogares_ext_con_jefe = hogares_ext.merge(
        tipo_hogar[["id_hogar", "jefe_sexo", "jefe_edad"]], on="id_hogar", how="left"
    )
    hogares_ext_con_jefe["cohorte"] = preprocessing.compute_cohorte_generacional(hogares_ext_con_jefe, ANIO)
    hogares_ext_con_jefe["indice_acceso_digital"] = preprocessing.compute_indice_acceso_digital(hogares_ext_con_jefe)
    hogares_mdeo_hacinamiento = preprocessing.compute_hacinamiento(hogares_mdeo)
    personas_con_depto = preprocessing.merge_personas(hogares, personas){fies_extra}

print(f"Hogares en todo el país: {{len(hogares):,}}")
print(f"Hogares de Montevideo: {{len(hogares_mdeo):,}}")'''
    return Celda(markdown=markdown, codigo=codigo)


def celda_preparacion_empleo(anio_base: int) -> Celda:
    """Solo se genera si se eligió el bloque Empleo — procesar los 12
    meses es bastante más pesado que el resto (ver paso 3.5 del agente),
    por eso queda en su propia celda, separada de Preparación de datos."""
    codigo = '''with bitacora.medir("carga_de_datos_empleo"):
    empleo_prep = preprocessing.prepare_empleo(data_loader.load_empleo(ANIO))
    ocupados = empleo_prep[empleo_prep["condicion_actividad"] == "Ocupados"].copy()
    activos = empleo_prep[empleo_prep["condicion_actividad"].isin(["Ocupados", "Desocupados"])].copy()
    activos["es_desocupado"] = activos["condicion_actividad"] == "Desocupados"

meses_cubiertos = sorted(int(m) for m in empleo_prep["mes"].unique())
print(f"Meses de Empleo cubiertos: {len(meses_cubiertos)}")'''
    return Celda(markdown="## Empleo: preparación específica de este bloque", codigo=codigo)


def celda_preparacion_seguridad(anio_base: int) -> Celda:
    """Solo se genera si se eligió el bloque Seguridad y Victimización."""
    codigo = '''with bitacora.medir("carga_de_datos_seguridad"):
    victimizacion_prep = preprocessing.prepare_victimizacion(data_loader.load_victimizacion(ANIO))
    victimizacion_largo = preprocessing.melt_delitos(victimizacion_prep)
    victimizados = victimizacion_largo[victimizacion_largo["victimizado"]]

print(f"Personas x tipo de delito: {len(victimizacion_largo):,}")'''
    return Celda(markdown="## Seguridad y Victimización: preparación específica de este bloque", codigo=codigo)


# ============================================================================
# Texto fijo por métrica: reusa, sin reescribirlo, el título y la
# explicación que ya redactó `formularios.py` para el catálogo — la
# persona ya los vio al elegir la métrica, así que el informe usa las
# mismas palabras en vez de una segunda redacción que podría no coincidir.
# A propósito NO varía entre corridas ni entre personas: dos informes con
# la misma métrica elegida tienen que traer el mismo texto — confirmado
# explícitamente como lo deseado (si alguien quiere algo distinto, está
# el campo de propuesta libre del paso 4, que sigue yendo por el camino
# de redacción libre del paso 6).
# ============================================================================

def _texto_catalogo() -> dict[int, tuple[str, str]]:
    resultado: dict[int, tuple[str, str]] = {}
    for _clave, (_titulo_bloque, _nota, metricas) in formularios._CATEGORIAS_METRICAS.items():
        for numero, titulo, descripcion in metricas:
            resultado[numero] = (titulo, descripcion)
    for _titulo_bloque, _nota, metricas in (
        formularios._CATEGORIA_FIES,
        formularios._CATEGORIA_EMPLEO,
        formularios._CATEGORIA_SEGURIDAD,
    ):
        for numero, titulo, descripcion in metricas:
            resultado[numero] = (titulo, descripcion)
    return resultado


_TEXTO_CATALOGO = _texto_catalogo()

# Justificación fija del tipo de gráfica, por familia — no por métrica
# (la misma familia de gráfica se justifica siempre igual, ver
# docs/CONVENCIONES_DE_GRAFICAS.md). Ninguna de estas frases es nueva:
# son las mismas razones ya documentadas ahí, solo que ahora quedan
# escritas una vez acá en vez de que el modelo las redacte de nuevo en
# cada corrida.
_JUSTIFICACION_POR_FAMILIA = {
    "barras": "Barras, para comparar magnitudes entre categorías (Cleveland & McGill, 1984).",
    "barras_h": (
        "Barras horizontales, para que las categorías se lean sin inclinar "
        "la cabeza (Cleveland & McGill, 1984)."
    ),
    "barras_100": "Barras 100% apiladas, para mostrar cómo se reparte el total entre categorías.",
    "dumbbell": (
        "Gráfico de dos puntos conectados (dumbbell), para comparar dos grupos "
        "conservando el valor real de cada uno, no solo la diferencia entre "
        "ambos (Tufte; Knaflic, storytellingwithdata.com)."
    ),
    "heatmap": "Heatmap, para cruzar dos variables categóricas a la vez en una sola gráfica.",
}


# ============================================================================
# Glosario de terminos, para que toda metrica explique su jerga.
#
# Nace de un problema real encontrado por el dueno del proyecto leyendo un
# informe generado: las metricas de Empleo traian la formula del INE de
# "tasa de actividad/empleo/desempleo" y otras metricas no explicaban nada.
# La diferencia no era una decision: esas definiciones las escribia el
# modelo a mano durante la corrida, asi que aparecian o no segun se
# acordara. Igual que con los hooks y con el panorama de TV cable, una
# regla que depende de que el modelo se acuerde no se cumple pareja - por
# eso ahora el glosario es fijo y se arma solo.
#
# Cada definicion describe **lo que de verdad calcula este proyecto**
# (verificable contra analysis.py/preprocessing.py), siguiendo el criterio
# del INE. No se transcriben textos oficiales que no esten verificados.
# ============================================================================

_GLOSARIO = {
    "condicion_actividad": (
        "**Condición de actividad**: el INE clasifica a cada persona de 14 años o más como "
        "*ocupada* (trabajó en el período de referencia), *desocupada* (no trabajó, buscó "
        "trabajo y estaba disponible) o *inactiva* (ni trabaja ni busca). Los menores de 14 "
        "años quedan fuera de todo este bloque."
    ),
    "tasa_actividad": (
        "**Tasa de actividad** = (ocupados + desocupados) ÷ población de 14 años o más × 100. "
        "Qué parte de la población en edad de trabajar está en el mercado laboral, sea "
        "trabajando o buscando."
    ),
    "tasa_empleo": (
        "**Tasa de empleo** = ocupados ÷ población de 14 años o más × 100."
    ),
    "tasa_desempleo": (
        "**Tasa de desempleo** = desocupados ÷ (ocupados + desocupados) × 100. El denominador "
        "es la población *activa*, no la población total: por eso un 8% de desempleo **no** "
        "significa que el 8% de la gente no tenga trabajo, sino el 8% de quienes están "
        "trabajando o buscando."
    ),
    "informalidad": (
        "**Informalidad**: se considera informal a la persona ocupada que no aporta a la "
        "seguridad social por ese trabajo. Es el criterio estándar en la región y el mismo que "
        "usa el paquete oficial de R del INE para la ECH."
    ),
    "subempleo": (
        "**Subempleo**: personas ocupadas que trabajan menos horas de las que querrían y están "
        "disponibles para trabajar más."
    ),
    "pobreza": (
        "**Pobreza e indigencia**: clasificación que ya viene calculada por el INE, no estimada "
        "acá. Un hogar es *pobre* si su ingreso no alcanza la línea de pobreza (el costo de una "
        "canasta básica alimentaria y no alimentaria) para su composición, e *indigente* si no "
        "alcanza siquiera la canasta alimentaria."
    ),
    "nivel_economico": (
        "**Nivel económico**: agrupación del estrato socioeconómico que asigna el INE a cada "
        "hogar, de 1 (más bajo) a 5 (más alto)."
    ),
    "hacinamiento": (
        "**Hacinamiento**: hogares con más de 2 personas por habitación."
    ),
    "jefe_hogar": (
        "**Jefe/a de hogar**: la persona que los propios integrantes del hogar reconocen como "
        "tal al responder la encuesta — no la determina el INE por ingreso ni por edad."
    ),
    "tipos_hogar": (
        "**Tipos de hogar** (taxonomía CELADE/CEPAL): *unipersonal* (una sola persona), "
        "*nuclear* (pareja y/o hijos), *extendido* (núcleo más otros parientes), *compuesto* "
        "(incluye personas sin parentesco) y *sin núcleo* (parientes sin pareja ni hijos)."
    ),
    "razon_dependencia": (
        "**Razón de dependencia demográfica** = personas menores de 15 más mayores de 65, "
        "dividido por las de 15 a 64, × 100. Cuántas personas en edades potencialmente "
        "dependientes hay por cada 100 en edad activa."
    ),
    "carencia_estructural": (
        "**Carencia estructural de la vivienda**: la vivienda tiene al menos uno de los "
        "problemas que releva el INE (humedad, goteras, grietas, riesgo de derrumbe, etc.). "
        "Basta una para contarla como deficitaria — el mismo criterio de conteo de carencias "
        "que usa el INE para NBI-vivienda. Qué problemas se relevan cambia según el año."
    ),
    "tecnologias": (
        "**Tecnologías del hogar**: tener conexión a internet, computadora y servicios de "
        "streaming. Son variables del hogar, no de cada persona."
    ),
    "calidad_conexion": (
        "**Calidad de la conexión**: no solo tener o no tener internet, sino cómo. *Banda ancha "
        "fija* (conexión del hogar), *solo móvil* (únicamente por datos de celular) o *sin "
        "conexión*. Si el hogar tiene las dos, cuenta como banda ancha fija."
    ),
    "indice_acceso_digital": (
        "**Índice de acceso digital**: puntaje de 0 a 3 según cuántas de las tres tecnologías "
        "tiene el hogar (internet, computadora, streaming). Es un conteo simple, inspirado en "
        "el enfoque de canasta digital básica de CEPAL."
    ),
    "cohorte": (
        "**Cohorte generacional**: agrupa a los hogares según el año de nacimiento del jefe/a "
        "(baby boomers, generación X, millennials, etc.), calculado sobre el año de la encuesta."
    ),
    "indice_territorial": (
        "**Índice de desarrollo territorial**: combina pobreza, empleo, precariedad de vivienda "
        "y nivel económico en un puntaje de 0 a 1 por departamento, normalizando cada componente "
        "e invirtiendo los negativos para que más alto siempre signifique mejor. Es una medida "
        "del departamento, nunca de un hogar puntual."
    ),
    "fies": (
        "**Inseguridad alimentaria (escala FIES de FAO)**: se construye con preguntas sobre "
        "haber tenido que saltear comidas o reducirlas por falta de dinero. *Moderada* implica "
        "haber comprometido la calidad o la cantidad de la comida; *severa*, haber pasado hambre."
    ),
    "quintil": (
        "**Quintil de ingreso**: los hogares ordenados por ingreso y partidos en cinco grupos "
        "iguales. El quintil 1 es el 20% de menor ingreso y el 5 el 20% de mayor."
    ),
    "victimizacion": (
        "**Victimización**: haber sufrido un delito en el mes anterior a la entrevista. Es una "
        "cifra mensual, no anual."
    ),
    "comunicacion_policia": (
        "**Comunicación a la policía**: haber avisado a la policía de cualquier modo, sin que "
        "eso implique una denuncia formal."
    ),
    "denuncia_formal": (
        "**Denuncia formal**: haber hecho la denuncia presencial en la comisaría. Es un "
        "subconjunto de quienes se comunicaron con la policía."
    ),
}

# numero de metrica -> terminos que usa. Toda metrica del catalogo tiene
# entrada; `test_toda_metrica_del_catalogo_explica_sus_terminos` lo hace
# cumplir, asi que una metrica nueva no puede quedarse sin glosario.
_TERMINOS_POR_METRICA = {
    1: ("tecnologias", "nivel_economico"),
    2: ("tecnologias", "cohorte"),
    3: ("calidad_conexion", "nivel_economico"),
    4: ("tecnologias", "jefe_hogar"),
    5: ("indice_acceso_digital", "nivel_economico"),
    6: ("jefe_hogar",),
    7: ("pobreza",),
    8: ("jefe_hogar", "pobreza"),
    9: ("hacinamiento", "nivel_economico"),
    10: ("tipos_hogar",),
    11: ("razon_dependencia",),
    12: ("tipos_hogar",),
    13: ("indice_territorial",),
    14: ("indice_territorial",),
    15: ("indice_territorial",),
    16: ("carencia_estructural",),
    17: ("carencia_estructural", "nivel_economico"),
    18: ("carencia_estructural",),
    19: ("carencia_estructural", "nivel_economico"),
    20: ("carencia_estructural",),
    21: ("fies",),
    22: ("fies", "quintil"),
    23: ("fies",),
    24: ("fies", "quintil"),
    25: ("fies", "quintil"),
    26: ("fies",),
    27: ("fies",),
    28: ("condicion_actividad", "tasa_actividad", "tasa_empleo", "tasa_desempleo"),
    29: ("tasa_actividad", "tasa_empleo", "tasa_desempleo"),
    30: ("tasa_desempleo",),
    31: ("informalidad",),
    32: ("informalidad",),
    33: ("subempleo",),
    34: ("condicion_actividad", "tasa_desempleo"),
    35: ("informalidad",),
    36: ("victimizacion",),
    37: ("victimizacion",),
    38: ("victimizacion",),
    39: ("victimizacion", "comunicacion_policia"),
    40: ("victimizacion", "denuncia_formal"),
    41: ("comunicacion_policia", "denuncia_formal"),
    42: ("victimizacion",),
}


def _markdown(numero: int, familia_grafica: str) -> str:
    """Las cinco partes que lleva SIEMPRE toda metrica del informe, en el
    mismo orden: nombre, la pregunta que responde, que significa cada
    termino segun el criterio del INE, por que esa grafica, y la grafica
    (que la aporta la celda de codigo que acompana a esta).

    Antes solo estaban el nombre, la descripcion y la justificacion de la
    grafica: los terminos quedaban librados a que el modelo los explicara
    en cada corrida, y por eso aparecian en Empleo pero no en el resto.
    """
    titulo, descripcion = _TEXTO_CATALOGO[numero]
    justificacion = _JUSTIFICACION_POR_FAMILIA[familia_grafica]
    terminos = "\n".join(f"- {_GLOSARIO[t]}" for t in _TERMINOS_POR_METRICA[numero])
    return (
        f"### {numero}. {titulo}\n\n"
        f"**¿Qué pregunta responde?** {descripcion}\n\n"
        f"**Qué significa cada término (criterio del INE):**\n{terminos}\n\n"
        f"*Por qué esta gráfica: {justificacion}*"
    )


# ============================================================================
# Generadores por métrica (1-43), año base únicamente. El número de cada
# función es el número del catálogo — ver `verificacion_catalogo.MANIFEST`
# para qué función de analysis.py/visualization.py implementa cada una
# (la fuente de verdad de esa asociación es esa, no este módulo).
# ============================================================================

def _m1() -> Celda:
    codigo = (
        "brecha_nivel_economico = analysis.brecha_digital_por_nivel_economico(hogares_ext)\n"
        "fig = viz.plot_brecha_digital(brecha_nivel_economico)\nfig.show()"
    )
    return Celda(_markdown(1, "barras"), codigo)


def _m2() -> Celda:
    codigo = (
        "brecha_cohorte = analysis.brecha_digital_por_cohorte(hogares_ext_con_jefe)\n"
        "fig = viz.plot_brecha_digital_por_cohorte(brecha_cohorte)\nfig.show()"
    )
    return Celda(_markdown(2, "barras"), codigo)


def _m3() -> Celda:
    codigo = (
        'calidad_nivel_economico = analysis.calidad_conexion_por(hogares_ext, "nivel_economico")\n'
        'fig = viz.plot_calidad_conexion_por(calidad_nivel_economico, "nivel económico")\nfig.show()'
    )
    return Celda(_markdown(3, "barras_100"), codigo)


def _m4() -> Celda:
    codigo = (
        "brecha_jefatura = analysis.brecha_digital_por_jefatura(hogares_ext_con_jefe)\n"
        "fig = viz.plot_brecha_digital_por_jefatura(brecha_jefatura)\nfig.show()"
    )
    return Celda(_markdown(4, "barras"), codigo)


def _m5() -> Celda:
    codigo = (
        'indice_acceso_nivel = analysis.indice_acceso_digital_por(hogares_ext_con_jefe, "nivel_economico")\n'
        'fig = viz.plot_indice_acceso_digital_por(indice_acceso_nivel, "nivel económico")\nfig.show()'
    )
    return Celda(_markdown(5, "barras"), codigo)


def _m6() -> Celda:
    codigo = (
        'adopcion_tablet_nivel = analysis.adopcion_tablet_ibirapita_por(hogares_ext_con_jefe, "nivel_economico")\n'
        'fig = viz.plot_adopcion_tablet_ibirapita(adopcion_tablet_nivel, "nivel económico")\nfig.show()'
    )
    return Celda(_markdown(6, "barras"), codigo)


def _m7() -> Celda:
    codigo = (
        "pobreza = analysis.pct_pobres_indigentes(hogares_ext)\n"
        "fig = viz.plot_pct_pobres_indigentes(pobreza)\nfig.show()"
    )
    return Celda(_markdown(7, "barras_h"), codigo)


def _m8() -> Celda:
    codigo = (
        "jefatura = analysis.tasa_jefatura_femenina(tipo_hogar)\n"
        "fig = viz.plot_tasa_jefatura_femenina(jefatura)\nfig.show()"
    )
    return Celda(_markdown(8, "barras_h"), codigo)


def _m9() -> Celda:
    codigo = (
        'chicos_hacinamiento_nivel = analysis.grupos_con_muestra_chica(hogares_mdeo_hacinamiento, "nivel_economico")\n'
        "if len(chicos_hacinamiento_nivel):\n"
        '    print("Niveles económicos con menos de 30 casos en la muestra (estimación poco confiable):")\n'
        "    for nivel, n in chicos_hacinamiento_nivel.items():\n"
        '        print(f"  {nivel}: {n} casos")\n\n'
        'hacinamiento_nivel = analysis.pct_hacinamiento_por(hogares_mdeo_hacinamiento, "nivel_economico")\n'
        'fig = viz.plot_hacinamiento_por(hacinamiento_nivel, "nivel económico")\nfig.show()'
    )
    return Celda(_markdown(9, "barras"), codigo)


def _m10() -> Celda:
    codigo = (
        "tipos_hogar_resumen = analysis.tipos_hogar_resumen(tipo_hogar)\n"
        "fig = viz.plot_tipos_hogar(tipos_hogar_resumen)\nfig.show()"
    )
    return Celda(_markdown(10, "barras_h"), codigo)


def _m11() -> Celda:
    codigo = (
        'chicos_depto_dependencia = analysis.grupos_con_muestra_chica(personas_con_depto, "departamento")\n'
        "if len(chicos_depto_dependencia):\n"
        '    print("Departamentos con menos de 30 casos en la muestra (estimación poco confiable):")\n'
        "    for depto, n in chicos_depto_dependencia.items():\n"
        '        print(f"  {depto}: {n} casos")\n\n'
        'dependencia_depto = analysis.razon_dependencia_por(personas_con_depto, "departamento")\n'
        'fig = viz.plot_razon_dependencia_por(dependencia_depto, "departamento")\nfig.show()'
    )
    return Celda(_markdown(11, "barras_h"), codigo)


def _m12() -> Celda:
    codigo = (
        "unipersonales_mayores = analysis.pct_unipersonales_mayores(tipo_hogar)\n"
        "fig = viz.plot_pct_unipersonales_mayores(unipersonales_mayores)\nfig.show()"
    )
    return Celda(_markdown(12, "barras_h"), codigo)


_COMPONENTES_TERRITORIO = (
    'pobreza_depto = analysis.pct_pobres_por(hogares_cond, "departamento").set_index("departamento")\n'
    'estrato_depto = analysis.estrato_promedio_por(hogares, "departamento").set_index("departamento")\n'
    'precariedad_depto = analysis.precariedad_estructural_por(hogares_cond, "departamento").set_index("departamento")\n'
    "componentes_territorio = pd.DataFrame({\n"
    '    "pct_pobreza": pobreza_depto["pct_pobres"],\n'
    '    "pct_precariedad": precariedad_depto["pct_precariedad"],\n'
    '    "estrato_promedio": estrato_depto["estrato_promedio"],\n'
    "}).dropna()\n"
    'indice_territorial = analysis.indice_desarrollo_territorial(componentes_territorio, invertir=["pct_pobreza", "pct_precariedad"])'
)


def _m13() -> Celda:
    codigo = _COMPONENTES_TERRITORIO + "\nfig = viz.plot_indice_desarrollo_territorial(indice_territorial)\nfig.show()"
    return Celda(_markdown(13, "barras_h"), codigo)


def _m14() -> Celda:
    codigo = _COMPONENTES_TERRITORIO + "\nfig = viz.plot_perfil_territorial(indice_territorial)"
    return Celda(_markdown(14, "heatmap"), codigo)


def _m15() -> Celda:
    codigo = (
        _COMPONENTES_TERRITORIO + "\n"
        'mejor_depto = indice_territorial.index[0]\n'
        'peor_depto = indice_territorial.index[-1]\n'
        'brecha_territorial = indice_territorial.loc[mejor_depto, "indice"] - indice_territorial.loc[peor_depto, "indice"]\n'
        'print(f"Brecha territorial: {mejor_depto} ({indice_territorial.loc[mejor_depto, \'indice\']:.2f}) vs. '
        '{peor_depto} ({indice_territorial.loc[peor_depto, \'indice\']:.2f}) — diferencia de {brecha_territorial:.2f}")\n\n'
        "fig = viz.plot_dumbbell(\n"
        '    categorias=["Índice de desarrollo territorial"],\n'
        '    valores_a=[indice_territorial.loc[mejor_depto, "indice"]],\n'
        '    valores_b=[indice_territorial.loc[peor_depto, "indice"]],\n'
        "    nombre_a=mejor_depto, nombre_b=peor_depto,\n"
        '    titulo="Brecha territorial: mejor vs. peor departamento", xlabel="Índice (0 a 1)",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(15, "dumbbell"), codigo)


def _m16() -> Celda:
    codigo = (
        "precariedad = analysis.precariedad_estructural(hogares_cond)\n"
        "fig = viz.plot_precariedad_estructural(precariedad)\nfig.show()"
    )
    return Celda(_markdown(16, "barras_h"), codigo)


def _m17() -> Celda:
    codigo = (
        'precariedad_nivel = analysis.precariedad_estructural_por(hogares_cond, "nivel_economico")\n'
        'fig = viz.plot_precariedad_estructural_por(precariedad_nivel, "nivel económico")\nfig.show()'
    )
    return Celda(_markdown(17, "barras_h"), codigo)


def _m18() -> Celda:
    codigo = (
        'precariedad_depto = analysis.precariedad_estructural_por(hogares_cond, "departamento")\n'
        'fig = viz.plot_precariedad_estructural_por(precariedad_depto, "departamento")\nfig.show()'
    )
    return Celda(_markdown(18, "barras_h"), codigo)


def _m19() -> Celda:
    codigo = (
        'precariedad_nivel = analysis.precariedad_estructural_por(hogares_cond, "nivel_economico")\n'
        'brecha_precariedad = analysis.diferencia_entre_categorias(\n'
        '    precariedad_nivel, "nivel_economico", "1-Bajo", "5-Alto", "pct_precariedad"\n'
        ")\n"
        'print(f"Diferencia 1-Bajo menos 5-Alto: {brecha_precariedad:.2f} puntos porcentuales")\n\n'
        'fila_bajo = precariedad_nivel.set_index("nivel_economico").loc["1-Bajo", "pct_precariedad"]\n'
        'fila_alto = precariedad_nivel.set_index("nivel_economico").loc["5-Alto", "pct_precariedad"]\n'
        "fig = viz.plot_dumbbell(\n"
        '    categorias=["Precariedad estructural"],\n'
        "    valores_a=[fila_bajo], valores_b=[fila_alto],\n"
        '    nombre_a="1-Bajo", nombre_b="5-Alto",\n'
        '    titulo="Precariedad estructural: nivel económico bajo vs. alto", xlabel="% de hogares con carencia",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(19, "dumbbell"), codigo)


def _m20() -> Celda:
    codigo = (
        "carencias_frecuentes = analysis.carencias_estructurales_mas_frecuentes(hogares_cond)\n"
        "fig = viz.plot_carencias_estructurales_mas_frecuentes(carencias_frecuentes)\nfig.show()"
    )
    return Celda(_markdown(20, "barras_h"), codigo)


def _m21() -> Celda:
    codigo = (
        "prevalencia_fies = analysis.prevalencia_inseguridad_alimentaria(fies_clasificado)\n"
        "fig = viz.plot_prevalencia_inseguridad_alimentaria(prevalencia_fies)\nfig.show()"
    )
    return Celda(_markdown(21, "barras"), codigo)


def _m22() -> Celda:
    codigo = (
        'chicos_quintil = analysis.grupos_con_muestra_chica(fies_clasificado, "quintil_ingreso")\n'
        "if len(chicos_quintil):\n"
        '    print("Quintiles con menos de 30 casos en la muestra (estimación poco confiable):")\n'
        "    for quintil, n in chicos_quintil.items():\n"
        '        print(f"  {quintil}: {n} casos")\n\n'
        'inseguridad_quintil = analysis.inseguridad_alimentaria_por(fies_clasificado, "quintil_ingreso")\n'
        "fig = viz.plot_inseguridad_alimentaria_por(\n"
        '    inseguridad_quintil, "quintil_ingreso",\n'
        '    titulo="Inseguridad alimentaria moderada o severa por quintil de ingreso", xlabel="Quintil de ingreso",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(22, "barras"), codigo)


def _m23() -> Celda:
    codigo = (
        'inseguridad_region = analysis.inseguridad_alimentaria_por(fies_clasificado, "region")\n'
        "fig = viz.plot_inseguridad_alimentaria_por(\n"
        '    inseguridad_region, "region",\n'
        '    titulo="Inseguridad alimentaria moderada o severa por región", xlabel="Región",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(23, "barras"), codigo)


def _m24() -> Celda:
    codigo = (
        'inseguridad_quintil = analysis.inseguridad_alimentaria_por(fies_clasificado, "quintil_ingreso")\n'
        "diferencia_quintiles = analysis.diferencia_entre_categorias(\n"
        '    inseguridad_quintil, "quintil_ingreso", "Quintil 1", "Quintil 5", "pct_inseguridad"\n'
        ")\n"
        'print(f"Diferencia Quintil 1 menos Quintil 5: {diferencia_quintiles:.2f} puntos porcentuales")\n\n'
        'fila_q1 = inseguridad_quintil.set_index("quintil_ingreso").loc["Quintil 1", "pct_inseguridad"]\n'
        'fila_q5 = inseguridad_quintil.set_index("quintil_ingreso").loc["Quintil 5", "pct_inseguridad"]\n'
        "fig = viz.plot_dumbbell(\n"
        '    categorias=["Inseguridad alimentaria"],\n'
        "    valores_a=[fila_q1], valores_b=[fila_q5],\n"
        '    nombre_a="Quintil 1", nombre_b="Quintil 5",\n'
        '    titulo="Inseguridad alimentaria: quintil más pobre vs. más rico", xlabel="% de hogares (ponderado)",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(24, "dumbbell"), codigo)


def _m25() -> Celda:
    codigo = (
        "inseguridad_severa_quintil = analysis.inseguridad_alimentaria_por(\n"
        '    fies_clasificado, "quintil_ingreso", columna_clasificacion="inseguridad_severa"\n'
        ")\n"
        "fig = viz.plot_inseguridad_alimentaria_por(\n"
        '    inseguridad_severa_quintil, "quintil_ingreso",\n'
        '    titulo="Inseguridad alimentaria severa por quintil de ingreso", xlabel="Quintil de ingreso",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(25, "barras"), codigo)


def _m26() -> Celda:
    codigo = (
        "fies_con_menores18 = fies_clasificado.assign(\n"
        '    tiene_menores_18=fies_clasificado["tiene_menores_18"].map(\n'
        '        {True: "Con menores de 18", False: "Sin menores de 18"}\n'
        "    )\n"
        ")\n"
        'inseguridad_menores18 = analysis.inseguridad_alimentaria_por(fies_con_menores18, "tiene_menores_18")\n'
        "fig = viz.plot_inseguridad_alimentaria_por(\n"
        '    inseguridad_menores18, "tiene_menores_18",\n'
        '    titulo="Inseguridad alimentaria en hogares con y sin menores de 18 años", xlabel="",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(26, "barras"), codigo)


def _m27() -> Celda:
    codigo = (
        "fies_con_menores6 = fies_clasificado.assign(\n"
        '    tiene_menores_6=fies_clasificado["tiene_menores_6"].map(\n'
        '        {True: "Con niños de 0 a 5", False: "Sin niños de 0 a 5"}\n'
        "    )\n"
        ")\n"
        'inseguridad_menores6 = analysis.inseguridad_alimentaria_por(fies_con_menores6, "tiene_menores_6")\n'
        "fig = viz.plot_inseguridad_alimentaria_por(\n"
        '    inseguridad_menores6, "tiene_menores_6",\n'
        '    titulo="Inseguridad alimentaria en hogares con y sin niños de 0 a 5 años", xlabel="",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(27, "barras"), codigo)


def _m28() -> Celda:
    codigo = (
        "tasas_nacionales = analysis.tasas_actividad_empleo_desempleo(empleo_prep)\n"
        "fig = viz.plot_tasas_actividad_empleo_desempleo(tasas_nacionales)\nfig.show()"
    )
    return Celda(_markdown(28, "barras"), codigo)


def _m29() -> Celda:
    codigo = (
        'tasas_sexo = analysis.tasas_actividad_empleo_desempleo_por(empleo_prep, "sexo_grupo")\n'
        'brecha_genero = analysis.brecha_por_grupo(tasas_sexo, "sexo_grupo", "1-Hombre", "2-Mujer")\n'
        'print(f"Brecha de género (hombre menos mujer):\\n{brecha_genero}")\n\n'
        'fig = viz.plot_tasas_por_grupo(tasas_sexo, "sexo_grupo", "Tasas de actividad, empleo y desempleo por sexo")\n'
        "fig.show()"
    )
    return Celda(_markdown(29, "barras"), codigo)


def _m30() -> Celda:
    codigo = (
        'desempleo_depto = analysis.tasa_mensual_promedio_por(activos, "departamento", "es_desocupado")\n'
        'fig = viz.plot_tasa_mensual_promedio_por(desempleo_depto, "departamento", "Tasa de desempleo por departamento")\n'
        "fig.show()"
    )
    return Celda(_markdown(30, "barras_h"), codigo)


def _m31() -> Celda:
    codigo = (
        'informalidad_sexo = analysis.tasa_mensual_promedio_por(ocupados, "sexo_grupo", "es_informal")\n'
        'fig = viz.plot_tasa_mensual_promedio_por(informalidad_sexo, "sexo_grupo", "Informalidad laboral por sexo")\n'
        "fig.show()"
    )
    return Celda(_markdown(31, "barras_h"), codigo)


def _m32() -> Celda:
    codigo = (
        'informalidad_educacion = analysis.tasa_mensual_promedio_por(ocupados, "nivel_educativo", "es_informal")\n'
        'fig = viz.plot_tasa_mensual_promedio_por(informalidad_educacion, "nivel_educativo", "Informalidad laboral por nivel educativo")\n'
        "fig.show()"
    )
    return Celda(_markdown(32, "barras_h"), codigo)


def _m33() -> Celda:
    codigo = (
        'subempleo_sexo = analysis.tasa_mensual_promedio_por(ocupados, "sexo_grupo", "es_subempleo")\n'
        'fig = viz.plot_tasa_mensual_promedio_por(subempleo_sexo, "sexo_grupo", "Subempleo por sexo")\n'
        "fig.show()"
    )
    return Celda(_markdown(33, "barras_h"), codigo)


def _m34() -> Celda:
    codigo = (
        'tasas_edad_laboral = analysis.tasas_actividad_empleo_desempleo_por(empleo_prep, "grupo_edad_laboral")\n'
        'brecha_edad = analysis.brecha_por_grupo(tasas_edad_laboral, "grupo_edad_laboral", "Joven (14-24)", "Resto")\n'
        'print(f"Brecha juvenil vs. resto:\\n{brecha_edad}")\n\n'
        'fig = viz.plot_tasas_por_grupo(\n'
        '    tasas_edad_laboral, "grupo_edad_laboral",\n'
        '    "Tasas de actividad, empleo y desempleo: jóvenes vs. resto",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(34, "barras"), codigo)


def _m35() -> Celda:
    codigo = (
        'situacion_por_sector = analysis.composicion_categorica_por_mes_promedio(\n'
        '    ocupados, "sector_formalidad", "situacion_ocupacional"\n'
        ")\n"
        "fig = viz.plot_composicion_categorica(\n"
        "    situacion_por_sector,\n"
        '    titulo="Situación ocupacional dentro de cada sector (formal / informal)", xlabel="Sector",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(35, "barras_100"), codigo)


def _m36() -> Celda:
    codigo = (
        'prevalencia_delito = analysis.pct_ponderado_por(\n'
        '    victimizacion_largo, "tipo_delito", "victimizado", "ponderador_victimizacion"\n'
        ")\n"
        "fig = viz.plot_pct_por(\n"
        '    prevalencia_delito, "tipo_delito",\n'
        '    titulo="Prevalencia de victimización por tipo de delito", xlabel="Tipo de delito",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(36, "barras"), codigo)


def _m37() -> Celda:
    codigo = (
        'victimizacion_sexo = analysis.pct_ponderado_por(\n'
        '    victimizacion_prep, "sexo_grupo", "victimizado_algun_delito", "ponderador_victimizacion"\n'
        ")\n"
        "fig = viz.plot_pct_por(\n"
        '    victimizacion_sexo, "sexo_grupo",\n'
        '    titulo="Victimización general por sexo", xlabel="Sexo",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(37, "barras"), codigo)


def _m38() -> Celda:
    codigo = (
        'victimizacion_depto = analysis.pct_ponderado_por(\n'
        '    victimizacion_prep, "departamento", "victimizado_algun_delito", "ponderador_victimizacion"\n'
        ")\n"
        "fig = viz.plot_pct_por(\n"
        '    victimizacion_depto, "departamento",\n'
        '    titulo="Victimización general por departamento", xlabel="Departamento",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(38, "barras"), codigo)


def _m39() -> Celda:
    codigo = (
        'comunicacion_delito = analysis.pct_ponderado_por(\n'
        '    victimizados, "tipo_delito", "comunicacion_policia", "ponderador_victimizacion"\n'
        ")\n"
        "fig = viz.plot_pct_por(\n"
        '    comunicacion_delito, "tipo_delito",\n'
        '    titulo="Tasa de comunicación a la policía por tipo de delito", xlabel="Tipo de delito",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(39, "barras"), codigo)


def _m40() -> Celda:
    codigo = (
        'denuncia_delito = analysis.pct_ponderado_por(\n'
        '    victimizados, "tipo_delito", "denuncia_formal", "ponderador_victimizacion"\n'
        ")\n"
        "fig = viz.plot_pct_por(\n"
        '    denuncia_delito, "tipo_delito",\n'
        '    titulo="Tasa de denuncia formal por tipo de delito", xlabel="Tipo de delito",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(40, "barras"), codigo)


def _m41() -> Celda:
    codigo = (
        'comunicacion_delito = analysis.pct_ponderado_por(\n'
        '    victimizados, "tipo_delito", "comunicacion_policia", "ponderador_victimizacion"\n'
        ")\n"
        'denuncia_delito = analysis.pct_ponderado_por(\n'
        '    victimizados, "tipo_delito", "denuncia_formal", "ponderador_victimizacion"\n'
        ")\n"
        "brecha_comunicacion_denuncia = analysis.diferencia_entre_tablas(\n"
        '    comunicacion_delito, denuncia_delito, "tipo_delito", "pct"\n'
        ")\n"
        'print(f"Comunicación informal menos denuncia formal, por tipo de delito:\\n{brecha_comunicacion_denuncia}")\n\n'
        "fig = viz.plot_dumbbell(\n"
        '    categorias=comunicacion_delito["tipo_delito"].tolist(),\n'
        '    valores_a=comunicacion_delito["pct"].tolist(),\n'
        '    valores_b=denuncia_delito.set_index("tipo_delito").loc[comunicacion_delito["tipo_delito"], "pct"].tolist(),\n'
        '    nombre_a="Comunicación a la policía", nombre_b="Denuncia formal",\n'
        '    titulo="Comunicación informal vs. denuncia formal, por tipo de delito", xlabel="% de víctimas (ponderado)",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(41, "dumbbell"), codigo)


def _m42() -> Celda:
    codigo = (
        "tipos_con_violencia = [info[\"nombre\"] for info in config.TIPOS_DELITO.values() if info[\"violencia\"]]\n"
        'victimizados_violencia = victimizados[victimizados["tipo_delito"].isin(tipos_con_violencia)]\n'
        "violencia_delito = analysis.pct_ponderado_por(\n"
        '    victimizados_violencia, "tipo_delito", "violencia", "ponderador_victimizacion"\n'
        ")\n"
        "fig = viz.plot_pct_por(\n"
        '    violencia_delito, "tipo_delito",\n'
        '    titulo="Casos con violencia por tipo de delito", xlabel="Tipo de delito",\n'
        ")\nfig.show()"
    )
    return Celda(_markdown(42, "barras"), codigo)


# ============================================================================
# Registro y orquestación
# ============================================================================

GENERADORES: dict[int, Callable[[], Celda]] = {n: globals()[f"_m{n}"] for n in range(1, 43)}


def construir_celdas_metrica(numero: int) -> Celda:
    """Punto de entrada para una métrica del catálogo (1-42), año base
    únicamente. Si la persona pidió comparar esta métrica entre años, eso
    se resuelve en código libre (paso 5, criterio ya documentado en
    docs/CONVENCIONES_DE_GRAFICAS.md), no acá."""
    return GENERADORES[numero]()


# ============================================================================
# Panorama general de Brecha Digital: siempre se muestra si se eligió ese
# bloque, sin importar qué métricas puntuales del 1 al 6 se hayan marcado
# — ver paso 5 en .claude/agents/encuesta-hogares.md. No tiene número de
# catálogo propio.
# ============================================================================

def celdas_intro_brecha_digital() -> list[Celda]:
    """Apertura del bloque de Brecha Digital: una sola celda con el
    panorama de conectividad.

    Hasta la 0.9.0 esto traía tres secciones heredadas del análisis
    original de 2019 —"Panorama general" contando hogares con y sin TV
    cable, "Distribución por barrio" con el % de abonados al cable, y
    "Composición de los hogares con y sin cable"— que aparecían en TODO
    informe que incluyera el bloque, sin importar qué métricas hubiera
    elegido la persona. Por vivir acá y no en el catálogo, sobrevivieron a
    la limpieza de métricas de cable de la 0.6.0 y llegaron a un informe
    real. Se eliminaron junto con la dimensión barrio completa (decisión
    del dueño del proyecto), y el panorama que queda mide internet, que es
    lo que la sección siempre dijo medir.
    """
    panorama = Celda(
        markdown="## Panorama general de conectividad en Montevideo",
        codigo=(
            "resumen_conectividad_mdeo = analysis.resumen_conectividad(hogares_ext)\n"
            'print(f"Hogares con internet: {resumen_conectividad_mdeo.hogares_con_internet:,} '
            '({resumen_conectividad_mdeo.pct_con_internet}%)")\n'
            'print(f"Hogares sin internet: {resumen_conectividad_mdeo.hogares_sin_internet:,} '
            '({resumen_conectividad_mdeo.pct_sin_internet}%)")\n\n'
            "fig = viz.plot_distribucion_conectividad(resumen_conectividad_mdeo)\nfig.show()"
        ),
    )
    return [panorama]


# ============================================================================
# Orquestación: arma el notebook completo y lo escribe a disco. Es lo
# único de este módulo que el agente invoca directamente en el paso 5,
# para las métricas del catálogo fijo sin comparación entre años — las
# métricas a medida del paso 6 y cualquier comparación entre años se
# siguen agregando aparte, con `nbformat.v4.new_markdown_cell`/
# `new_code_cell` escritos a mano, antes de `nbformat.write`.
# ============================================================================

_CABECERA = '''%matplotlib inline
import warnings

import pandas as pd
import plotly.io as pio

from encuesta_hogares import analysis, bitacora, config, data_loader, entrega, preprocessing
from encuesta_hogares import visualization as viz

pio.renderers.default = "png"
warnings.filterwarnings("ignore")'''


def construir_celdas_notebook(
    anio_base: int,
    metricas: list[int],
    incluir_brecha_digital: bool,
    incluir_fies: bool,
    incluir_empleo: bool,
    incluir_seguridad: bool,
) -> list[Celda]:
    """Arma, en orden, todas las celdas de las métricas fijas del catálogo
    para `anio_base` (preparación de datos + panorama de Brecha Digital si
    corresponde + una celda de markdown/código por métrica elegida) — sin
    escribir nada a disco todavía. Si alguna métrica de `metricas` fue
    pedida con comparación entre años, el agente la agrega aparte, en
    código libre, después de llamar a esta función."""
    celdas = [celda_preparacion_datos(anio_base, incluir_fies)]
    if incluir_empleo:
        celdas.append(celda_preparacion_empleo(anio_base))
    if incluir_seguridad:
        celdas.append(celda_preparacion_seguridad(anio_base))
    if incluir_brecha_digital:
        celdas.extend(celdas_intro_brecha_digital())

    for numero in metricas:
        celdas.append(construir_celdas_metrica(numero))

    return celdas


def escribir_notebook(celdas: list[Celda], ruta: Path | str) -> Path:
    """Convierte las celdas ya armadas a un notebook real y lo escribe a
    disco, respaldando el de la misma ruta si ya existía (mismo criterio
    que el resto del flujo — ver `entrega.respaldar_si_existe`)."""
    ruta = Path(ruta)
    nb = new_notebook()
    nb["cells"].append(new_code_cell(_CABECERA))
    for celda in celdas:
        nb["cells"].append(new_markdown_cell(celda.markdown))
        nb["cells"].append(new_code_cell(celda.codigo))
    entrega.respaldar_si_existe(ruta)
    nbformat.write(nb, str(ruta))
    return ruta
