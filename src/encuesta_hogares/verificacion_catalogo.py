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

from dataclasses import dataclass

from . import analysis, formularios, preprocessing, visualization

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
