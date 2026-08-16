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


# ============================================================================
# Estructura fija de toda métrica. Nace de un problema real encontrado por
# el dueño del proyecto leyendo un informe generado: las métricas de Empleo
# explicaban con la fórmula del INE qué es la tasa de actividad/empleo/
# desempleo, y otras métricas no explicaban ningún término. La diferencia
# no era una decisión — esas definiciones las escribía el modelo a mano
# durante la corrida, así que salían o no según se acordara.
# ============================================================================

_PARTES_OBLIGATORIAS = [
    ("¿Qué pregunta responde?", "la pregunta que responde la métrica"),
    ("Qué significa cada término", "la explicación de los términos según el criterio del INE"),
    ("Por qué esta gráfica:", "la justificación del tipo de gráfica elegido"),
]


def test_toda_metrica_del_catalogo_tiene_las_cinco_partes():
    faltantes = []
    for numero in sorted(nb.GENERADORES):
        celda = nb.construir_celdas_metrica(numero)
        if not celda.markdown.startswith(f"### {numero}. "):
            faltantes.append(f"  - {numero}: no arranca con el nombre de la métrica")
        for marca, descripcion in _PARTES_OBLIGATORIAS:
            if marca not in celda.markdown:
                faltantes.append(f"  - {numero}: le falta {descripcion}")
        # La quinta parte es la gráfica, que la aporta la celda de código.
        if "viz.plot_" not in celda.codigo:
            faltantes.append(f"  - {numero}: no genera ninguna gráfica")
    assert not faltantes, (
        "Toda métrica del informe lleva siempre las mismas cinco partes "
        "(nombre, pregunta que responde, términos según el INE, por qué esa "
        "gráfica, y la gráfica):\n\n" + "\n".join(faltantes)
    )


def test_toda_metrica_del_catalogo_explica_sus_terminos():
    """Una métrica nueva no puede quedarse sin entrada en el glosario: si
    se agrega al catálogo y se olvida acá, esto falla en vez de generar un
    informe donde esa métrica es la única sin explicar su jerga."""
    del_catalogo = set(nb.GENERADORES)
    con_terminos = set(nb._TERMINOS_POR_METRICA)
    assert del_catalogo - con_terminos == set(), (
        f"Métricas sin términos declarados: {sorted(del_catalogo - con_terminos)}"
    )
    assert con_terminos - del_catalogo == set(), (
        f"_TERMINOS_POR_METRICA tiene métricas que ya no están en el catálogo: "
        f"{sorted(con_terminos - del_catalogo)}"
    )


def test_todos_los_terminos_declarados_existen_en_el_glosario():
    rotos = {
        numero: [t for t in terminos if t not in nb._GLOSARIO]
        for numero, terminos in nb._TERMINOS_POR_METRICA.items()
    }
    rotos = {n: ts for n, ts in rotos.items() if ts}
    assert not rotos, f"Términos declarados que no están en el glosario: {rotos}"


def test_el_glosario_no_tiene_terminos_que_nadie_use():
    usados = {t for terminos in nb._TERMINOS_POR_METRICA.values() for t in terminos}
    sin_usar = set(nb._GLOSARIO) - usados
    assert not sin_usar, (
        f"El glosario define términos que ninguna métrica usa: {sorted(sin_usar)} "
        f"— borrarlos o conectarlos a la métrica que corresponda."
    )
