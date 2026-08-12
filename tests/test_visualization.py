"""Tests de regresión para bugs de gráficas ya encontrados y corregidos.

No es un test exhaustivo de cada función de `visualization.py` (son
muchas y la mayoría son variaciones directas de `analysis.py`, ya
cubierto). Estos dos casos puntuales sí se testean porque ya fallaron una
vez en un informe real: un `px.scatter` no ancla el eje en cero solo (a
diferencia de un `px.bar`), así que si alguien edita estas funciones sin
saberlo, puede volver a exagerar visualmente las diferencias sin que
nada lo note.
"""

import pandas as pd

from encuesta_hogares import visualization as viz


def test_plot_penetracion_por_barrio_ancla_el_eje_y_en_cero():
    df = pd.DataFrame(
        {
            "barrio": ["1", "2", "3"],
            "pct_abonados": [45.0, 60.0, 30.0],
            "nivel_suscripcion": ["2-Media-Baja", "3-Media-Alta", "1-Baja"],
        }
    )

    fig = viz.plot_penetracion_por_barrio(df)

    assert fig.layout.yaxis.range[0] == 0


def test_plot_penetracion_nacional_ancla_el_eje_x_en_cero():
    df = pd.DataFrame({"departamento": ["MONTEVIDEO", "RIVERA", "SALTO"], "pct_cable": [55.0, 20.0, 35.0]})

    fig = viz.plot_penetracion_nacional(df)

    assert fig.layout.xaxis.range[0] == 0
