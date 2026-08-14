"""Manifiesto métrica → función: detecta métricas "huérfanas" del catálogo.

`formularios.py` define el catálogo que ve el usuario (número, título,
descripción) pero **nunca dice qué función de `analysis.py`/
`preprocessing.py`/`visualization.py` la implementa** — esa asociación
solo existe en la cabeza de quien construye el notebook (el agente
`encuesta-hogares`, siguiendo el paso 5 de su instrucción: "leé
analysis.py y visualization.py, y llamá a las funciones que ya
identificaste"). Nada verifica automáticamente que esa asociación siga
siendo válida.

Construyendo este manifiesto se encontraron 4 métricas del catálogo
activo (3, 9, 11 y 40) que **no tenían ninguna función de análisis
propia, ponderada y testeada** — el cálculo quedaba librado a que el
agente lo improvisara dentro del notebook en cada corrida, sin test, sin
revisión, y en al menos un caso (métrica 9) directamente sin ponderar.
Se corrigieron agregando las funciones que faltaban (ver
`analysis.composicion_categorica_ponderada_por` y sus tres usos
concretos: `calidad_conexion_por`, `suscripcion_vs_nivel_economico`,
`streaming_vs_cable`) — este módulo existe para que la próxima métrica
en esa misma situación falle un test en vez de esperar a que alguien la
note en una corrida real.

MANIFEST no pretende ser el ÚNICO camino válido para cada métrica —
varias reutilizan un mismo helper genérico (`pct_ponderado_por`,
`tasa_mensual_promedio_por`, etc.) con distintos argumentos, y más de
una función podría servir igual de bien. La garantía que da esta
verificación es más modesta pero igual de útil: cada métrica tiene AL
MENOS UNA función real, existente y llamable que la implementa — no que
el manifiesto documente el único camino verdadero.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import analysis, config, formularios, preprocessing, visualization
from .verificacion_estructura import columnas_csv

_MODULOS = {"analysis": analysis, "preprocessing": preprocessing, "visualization": visualization}

# numero -> {"funciones": [referencias "modulo.nombre" que calculan los
# datos], "visualizacion": referencia "modulo.nombre" que la grafica}.
# Ver la nota en el docstring del módulo sobre por qué "funciones" no
# pretende ser la única lista posible.
MANIFEST: dict[int, dict] = {
    # 1 · Brecha Digital
    1: {"funciones": ["analysis.brecha_digital_por_nivel_economico"], "visualizacion": "visualization.plot_brecha_digital"},
    2: {"funciones": ["analysis.brecha_digital_por_cohorte"], "visualizacion": "visualization.plot_brecha_digital_por_cohorte"},
    3: {"funciones": ["analysis.calidad_conexion_por"], "visualizacion": "visualization.plot_calidad_conexion_por"},
    4: {"funciones": ["analysis.brecha_digital_por_jefatura"], "visualizacion": "visualization.plot_brecha_digital_por_jefatura"},
    5: {"funciones": ["analysis.indice_acceso_digital_por"], "visualizacion": "visualization.plot_indice_acceso_digital_por"},
    6: {"funciones": ["analysis.adopcion_tablet_ibirapita_por"], "visualizacion": "visualization.plot_adopcion_tablet_ibirapita"},
    7: {"funciones": ["preprocessing.compute_penetracion_por_barrio"], "visualizacion": "visualization.plot_penetracion_por_barrio"},
    8: {"funciones": ["analysis.clasificacion_barrios_resumen"], "visualizacion": "visualization.plot_clasificacion_barrios"},
    9: {"funciones": ["analysis.suscripcion_vs_nivel_economico"], "visualizacion": "visualization.plot_heatmap_suscripcion_vs_economico"},
    10: {"funciones": ["preprocessing.compute_penetracion_nacional"], "visualizacion": "visualization.plot_penetracion_nacional"},
    11: {"funciones": ["analysis.streaming_vs_cable"], "visualizacion": "visualization.plot_streaming_vs_cable"},
    # 2 · Hogares
    12: {"funciones": ["analysis.pct_pobres_indigentes"], "visualizacion": "visualization.plot_pct_pobres_indigentes"},
    13: {"funciones": ["analysis.tasa_jefatura_femenina"], "visualizacion": "visualization.plot_tasa_jefatura_femenina"},
    14: {"funciones": ["analysis.pct_hacinamiento_por", "preprocessing.compute_hacinamiento"], "visualizacion": "visualization.plot_hacinamiento_por"},
    15: {"funciones": ["analysis.tipos_hogar_resumen"], "visualizacion": "visualization.plot_tipos_hogar"},
    16: {"funciones": ["analysis.razon_dependencia_por"], "visualizacion": "visualization.plot_razon_dependencia_por"},
    17: {"funciones": ["analysis.pct_unipersonales_mayores"], "visualizacion": "visualization.plot_pct_unipersonales_mayores"},
    # 3 · Territorio
    18: {"funciones": ["analysis.indice_desarrollo_territorial"], "visualizacion": "visualization.plot_indice_desarrollo_territorial"},
    19: {"funciones": ["analysis.indice_desarrollo_territorial"], "visualizacion": "visualization.plot_perfil_territorial"},
    20: {"funciones": ["analysis.diferencia_entre_categorias"], "visualizacion": "visualization.plot_dumbbell"},
    # 4 · Vivienda
    21: {"funciones": ["analysis.precariedad_estructural"], "visualizacion": "visualization.plot_precariedad_estructural"},
    22: {"funciones": ["analysis.precariedad_estructural_por"], "visualizacion": "visualization.plot_precariedad_estructural_por"},
    23: {"funciones": ["analysis.precariedad_estructural_por"], "visualizacion": "visualization.plot_precariedad_estructural_por"},
    24: {"funciones": ["analysis.diferencia_entre_categorias"], "visualizacion": "visualization.plot_dumbbell"},
    25: {"funciones": ["analysis.carencias_estructurales_mas_frecuentes"], "visualizacion": "visualization.plot_carencias_estructurales_mas_frecuentes"},
    # 5 · Seguridad alimentaria (FIES)
    26: {"funciones": ["analysis.prevalencia_inseguridad_alimentaria"], "visualizacion": "visualization.plot_prevalencia_inseguridad_alimentaria"},
    27: {"funciones": ["analysis.inseguridad_alimentaria_por"], "visualizacion": "visualization.plot_inseguridad_alimentaria_por"},
    28: {"funciones": ["analysis.inseguridad_alimentaria_por"], "visualizacion": "visualization.plot_inseguridad_alimentaria_por"},
    29: {"funciones": ["analysis.diferencia_entre_categorias"], "visualizacion": "visualization.plot_dumbbell"},
    30: {"funciones": ["analysis.inseguridad_alimentaria_por"], "visualizacion": "visualization.plot_inseguridad_alimentaria_por"},
    31: {"funciones": ["analysis.inseguridad_alimentaria_por"], "visualizacion": "visualization.plot_inseguridad_alimentaria_por"},
    32: {"funciones": ["analysis.inseguridad_alimentaria_por"], "visualizacion": "visualization.plot_inseguridad_alimentaria_por"},
    # 6 · Empleo
    33: {"funciones": ["analysis.tasas_actividad_empleo_desempleo"], "visualizacion": "visualization.plot_tasas_actividad_empleo_desempleo"},
    34: {"funciones": ["analysis.tasas_actividad_empleo_desempleo_por", "analysis.brecha_por_grupo"], "visualizacion": "visualization.plot_tasas_por_grupo"},
    35: {"funciones": ["analysis.tasa_mensual_promedio_por"], "visualizacion": "visualization.plot_tasa_mensual_promedio_por"},
    36: {"funciones": ["analysis.tasa_mensual_promedio_por"], "visualizacion": "visualization.plot_tasa_mensual_promedio_por"},
    37: {"funciones": ["analysis.tasa_mensual_promedio_por"], "visualizacion": "visualization.plot_tasa_mensual_promedio_por"},
    38: {"funciones": ["analysis.tasa_mensual_promedio_por"], "visualizacion": "visualization.plot_tasa_mensual_promedio_por"},
    39: {"funciones": ["analysis.tasas_actividad_empleo_desempleo_por", "analysis.brecha_por_grupo"], "visualizacion": "visualization.plot_tasas_por_grupo"},
    40: {"funciones": ["analysis.composicion_categorica_por_mes_promedio"], "visualizacion": "visualization.plot_composicion_categorica"},
    # 7 · Seguridad y victimización
    41: {"funciones": ["analysis.pct_ponderado_por"], "visualizacion": "visualization.plot_pct_por"},
    42: {"funciones": ["analysis.pct_ponderado_por"], "visualizacion": "visualization.plot_pct_por"},
    43: {"funciones": ["analysis.pct_ponderado_por"], "visualizacion": "visualization.plot_pct_por"},
    44: {"funciones": ["analysis.pct_ponderado_por"], "visualizacion": "visualization.plot_pct_por"},
    45: {"funciones": ["analysis.pct_ponderado_por"], "visualizacion": "visualization.plot_pct_por"},
    46: {"funciones": ["analysis.diferencia_entre_tablas"], "visualizacion": "visualization.plot_dumbbell"},
    47: {"funciones": ["analysis.pct_ponderado_por"], "visualizacion": "visualization.plot_pct_por"},
}


@dataclass
class ReferenciaRota:
    numero: int
    referencia: str


def numeros_del_catalogo() -> dict[int, str]:
    """Recorre el catálogo real de `formularios.py` (los 4 bloques:
    permanentes + FIES + Empleo + Seguridad) y devuelve {número: título} —
    la fuente de verdad contra la que se valida MANIFEST, para que un
    número agregado/quitado del catálogo se note acá sin duplicar la
    lista a mano.
    """
    numeros: dict[int, str] = {}
    for _clave, (_titulo_bloque, metricas) in formularios._CATEGORIAS_METRICAS.items():
        for numero, titulo, _descripcion in metricas:
            numeros[numero] = titulo
    for bloque in (formularios._CATEGORIA_FIES, formularios._CATEGORIA_EMPLEO, formularios._CATEGORIA_SEGURIDAD):
        _titulo_bloque, metricas = bloque
        for numero, titulo, _descripcion in metricas:
            numeros[numero] = titulo
    return numeros


def _resolver(referencia: str):
    modulo_nombre, _, funcion_nombre = referencia.partition(".")
    modulo = _MODULOS.get(modulo_nombre)
    if modulo is None:
        return None
    return getattr(modulo, funcion_nombre, None)


def metricas_sin_manifiesto(catalogo: dict[int, str]) -> set[int]:
    """Números del catálogo real que no tienen entrada en MANIFEST."""
    return set(catalogo) - set(MANIFEST)


def entradas_manifiesto_obsoletas(catalogo: dict[int, str]) -> set[int]:
    """Números de MANIFEST que ya no existen en el catálogo real (métrica
    renumerada o eliminada, entrada no limpiada)."""
    return set(MANIFEST) - set(catalogo)


_VALIDADOR_DATOS_REALES = Path(__file__).resolve().parents[2] / "tools" / "validar_con_datos_reales.py"


def metricas_sin_funcion_validada_con_datos_reales() -> dict[int, list[str]]:
    """Números de MANIFEST cuya(s) función(es) de "funciones" nunca se
    invocan en `tools/validar_con_datos_reales.py` — la garantía de
    `referencias_rotas()` es solo que la función *existe*, no que alguien
    la haya corrido de verdad contra datos reales del INE.

    Nace de una evaluación de rigor real de este proyecto: 31 de las 47
    métricas del catálogo activo no tenían ninguna de sus funciones
    invocada ahí — esa brecha no la detectaba ni la suite sintética
    (que no usa datos reales) ni "el pipeline no explota" (un test
    sintético puede pasar aunque el cálculo esté mal para un caso real
    que ese sintético no reproduce). Se cerró para las 47 en esa
    evaluación; este chequeo existe para que la próxima métrica que se
    agregue sin ejercitarla ahí falle un test en vez de sumarse en
    silencio a la lista.

    Solo mira coincidencia de nombre de función en el texto del archivo
    (no ejecuta nada) — no reemplaza correr el script de verdad contra
    datos reales, que sigue siendo manual (`./run_python.bat
    tools/validar_con_datos_reales.py`, cuando hay datos en `data/`).
    """
    if not _VALIDADOR_DATOS_REALES.exists():
        return {}
    texto = _VALIDADOR_DATOS_REALES.read_text(encoding="utf-8")
    faltantes: dict[int, list[str]] = {}
    for numero, entrada in MANIFEST.items():
        nombres = [ref.split(".")[-1] for ref in entrada["funciones"]]
        invocada = any(re.search(rf"\b{re.escape(nombre)}\s*\(", texto) for nombre in nombres)
        if not invocada:
            faltantes[numero] = nombres
    return faltantes


def referencias_rotas() -> list[ReferenciaRota]:
    """Toda referencia de MANIFEST (en "funciones" o "visualizacion") que
    apunta a una función que no existe de verdad en su módulo — la señal
    concreta de una métrica huérfana: catalogada, pero sin implementación
    real detrás (o con una que se borró/renombró después)."""
    rotas = []
    for numero, entrada in MANIFEST.items():
        referencias = list(entrada["funciones"]) + [entrada["visualizacion"]]
        for referencia in referencias:
            if _resolver(referencia) is None:
                rotas.append(ReferenciaRota(numero, referencia))
    return rotas


# ============================================================================
# Disponibilidad por año: MANIFEST/referencias_rotas() verifica que el
# CÓDIGO exista — esto verifica que los DATOS del año elegido tengan las
# columnas que ese código necesita. Nace de un caso real: en 2025 el INE
# dejó de publicar INFORMAL/SECTOR_F/SIT_OCUP en los archivos mensuales de
# Empleo, y nada avisaba de eso hasta que la métrica correspondiente
# reventaba a mitad de una corrida — después de que el usuario ya la había
# elegido en el catálogo (paso 4). Este chequeo corre antes, con solo leer
# el encabezado de un archivo (sin cargar los datos completos), para poder
# avisar en el catálogo mismo en vez de con un traceback.
#
# Solo tiene entradas para métricas con un riesgo real y ya observado de
# que su columna de origen varíe entre años — no las 47, para no acumular
# un mapeo enorme que nadie mantiene. Si otro bloque tiene alguna vez el
# mismo problema, sumale su entrada acá cuando pase, no antes.
#
# numero -> lista de "opciones": cada opción es una lista de columnas
# CRUDAS (nombre tal cual viene en el archivo del INE, antes de
# config.EMPLEO_COLUMNS) que alcanzan, todas juntas, para calcular esa
# métrica. Basta con que UNA opción esté completa. Ej. informalidad
# (36/37) tiene dos caminos posibles (INFORMAL directo, o f82 si no está
# — ver preprocessing.prepare_empleo); situación ocupacional (40) por
# ahora solo tiene un camino conocido.
COLUMNAS_REQUERIDAS: dict[int, list[list[str]]] = {
    36: [["INFORMAL"], ["f82"]],
    37: [["INFORMAL"], ["f82"]],
    40: [["SIT_OCUP", "SECTOR_F"]],
}


def metricas_no_disponibles(columnas_presentes: set[str]) -> dict[int, list[str]]:
    """De `COLUMNAS_REQUERIDAS`, qué métricas no se pueden calcular con
    `columnas_presentes` (las columnas crudas que de verdad trae el
    archivo de un año — ver `metricas_empleo_no_disponibles` para
    obtenerlas solas con leer el encabezado). Devuelve
    `{número: columnas que le faltarían a la opción más cercana}` — solo
    para las métricas donde NINGUNA opción está completa.
    """
    resultado = {}
    for numero, opciones in COLUMNAS_REQUERIDAS.items():
        if any(all(c in columnas_presentes for c in opcion) for opcion in opciones):
            continue
        mejor_opcion = min(opciones, key=lambda op: sum(1 for c in op if c not in columnas_presentes))
        resultado[numero] = [c for c in mejor_opcion if c not in columnas_presentes]
    return resultado


def metricas_empleo_no_disponibles(anio: int | str) -> dict[int, list[str]]:
    """Igual que `metricas_no_disponibles`, pero mirando directo los
    archivos mensuales de Empleo de `anio` — solo lee el encabezado del
    primer archivo que exista (los 12 deberían compartir estructura;
    `verificacion_estructura.verificar_empleo` ya audita eso por
    separado). Diccionario vacío si el año no tiene ningún archivo de
    Empleo todavía, o si no falta nada.
    """
    primero = next((a for a in config.empleo_files(anio) if a.exists()), None)
    if primero is None:
        return {}
    return metricas_no_disponibles(columnas_csv(primero))


def aviso_metricas_no_disponibles(anio: int | str) -> list[str]:
    """Mensajes ya redactados, uno por métrica de Empleo no disponible
    para `anio` — para mostrarle al usuario ANTES de que elija el
    catálogo (paso 4 de `.claude/agents/encuesta-hogares.md`), no después
    de que la corrida falle. Lista vacía si no hay nada para avisar.
    """
    catalogo = numeros_del_catalogo()
    avisos = []
    for numero, faltantes in sorted(metricas_empleo_no_disponibles(anio).items()):
        titulo = catalogo.get(numero, "?")
        plural = "n" if len(faltantes) > 1 else ""
        avisos.append(
            f"Métrica {numero} — {titulo}: no disponible para este año, "
            f"falta{plural} {', '.join(faltantes)} en los datos del INE."
        )
    return avisos
