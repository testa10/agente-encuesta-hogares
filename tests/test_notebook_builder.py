"""Que `notebook_builder` se mantenga sincronizado con el catálogo real.

Nace de una preocupación real planteada al construir este módulo: ahora
hay tres lugares que tienen que coincidir (el catálogo en
`formularios.py`, el manifiesto de `verificacion_catalogo.py`, y las
plantillas de este módulo) y nada avisaba automáticamente si alguno se
desincronizaba de los otros. Este archivo cierra esa parte del problema
para el número de métrica; `tools/validar_con_datos_reales.py` cierra la
otra parte (que el código que generan las plantillas siga corriendo de
verdad contra datos reales, no solo que exista una entrada para cada
número).

Solo cubre el año base — la comparación entre años se decidió dejarla en
código libre (ver el docstring de notebook_builder.py), así que no hay
nada de eso para probar acá.
"""

from encuesta_hogares import notebook_builder as nb
from encuesta_hogares import verificacion_catalogo as vc


def test_generadores_cubre_exactamente_el_catalogo_actual():
    catalogo = set(vc.numeros_del_catalogo())
    generadores = set(nb.GENERADORES)
    faltantes = catalogo - generadores
    sobrantes = generadores - catalogo
    assert not faltantes, (
        f"Hay métricas en el catálogo sin plantilla en notebook_builder.GENERADORES: {sorted(faltantes)} "
        "— agregar un generador _mN, o si la métrica no se presta a mecanizarse, revisar el diseño."
    )
    assert not sobrantes, (
        f"notebook_builder.GENERADORES tiene entradas para métricas que ya no están en el catálogo: "
        f"{sorted(sobrantes)} — se renumeraron o se eliminaron; limpiar la(s) función(es) _mN correspondiente(s)."
    )


def test_todas_las_metricas_generan_markdown_y_codigo():
    for numero in nb.GENERADORES:
        celda = nb.construir_celdas_metrica(numero)
        assert celda.markdown.strip(), numero
        assert celda.codigo.strip(), numero


def test_todas_las_metricas_generan_codigo_python_valido():
    for numero in nb.GENERADORES:
        celda = nb.construir_celdas_metrica(numero)
        compile(celda.codigo, f"<metrica_{numero}>", "exec")


def test_construir_celdas_notebook_arma_preparacion_mas_una_celda_por_metrica():
    celdas = nb.construir_celdas_notebook(
        anio_base=2025,
        metricas=[1, 8, 22],
        incluir_brecha_digital=False,
        incluir_fies=True,
        incluir_empleo=False,
        incluir_seguridad=False,
    )
    # 1 preparación + 3 métricas (sin Brecha Digital, sin Empleo/Seguridad).
    assert len(celdas) == 4


def test_construir_celdas_notebook_agrega_panorama_solo_si_se_eligio_brecha_digital():
    sin_brecha = nb.construir_celdas_notebook(
        anio_base=2025, metricas=[8], incluir_brecha_digital=False,
        incluir_fies=False, incluir_empleo=False, incluir_seguridad=False,
    )
    con_brecha = nb.construir_celdas_notebook(
        anio_base=2025, metricas=[8], incluir_brecha_digital=True,
        incluir_fies=False, incluir_empleo=False, incluir_seguridad=False,
    )
    # Una sola celda de panorama. Eran tres hasta la 0.9.0 ("Panorama
    # general" contando hogares con y sin TV cable, "Distribución por
    # barrio" con el % de abonados, y "Composición de los hogares con y
    # sin cable"): aparecían en todo informe que incluyera el bloque, sin
    # importar las métricas elegidas, y por vivir acá y no en el catálogo
    # sobrevivieron a la limpieza de métricas de cable de la 0.6.0 hasta
    # llegar a un informe real.
    assert len(con_brecha) == len(sin_brecha) + 1


def test_construir_celdas_notebook_agrega_celdas_de_empleo_y_seguridad_solo_si_se_eligieron():
    base = nb.construir_celdas_notebook(
        anio_base=2025, metricas=[8], incluir_brecha_digital=False,
        incluir_fies=False, incluir_empleo=False, incluir_seguridad=False,
    )
    con_empleo_y_seguridad = nb.construir_celdas_notebook(
        anio_base=2025, metricas=[8], incluir_brecha_digital=False,
        incluir_fies=False, incluir_empleo=True, incluir_seguridad=True,
    )
    assert len(con_empleo_y_seguridad) == len(base) + 2
