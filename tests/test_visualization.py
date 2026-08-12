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


# ============================================================================
# Hogares y Brecha Digital: funciones nuevas, sin ninguna corrida real
# todavía - smoke tests simples (corren sin error, devuelven una figura) en
# vez de los tests de regresión de arriba, que existen para bugs ya vistos.
# ============================================================================

def test_plot_pct_pobres_indigentes_no_falla():
    fig = viz.plot_pct_pobres_indigentes({"pct_pobres": 5.3, "pct_indigentes": 0.2})
    assert fig is not None


def test_plot_tasa_jefatura_femenina_no_falla():
    fig = viz.plot_tasa_jefatura_femenina({"pct_jefatura_femenina": 42.0, "total_hogares": 100})
    assert fig is not None


def test_plot_tipos_hogar_no_falla():
    df = pd.DataFrame({"tipo_hogar": ["Nuclear", "Unipersonal"], "pct_hogares": [60.0, 40.0]})
    fig = viz.plot_tipos_hogar(df)
    assert fig is not None


def test_plot_hacinamiento_por_no_falla():
    df = pd.DataFrame({"nivel_economico": ["1-Bajo", "5-Alto"], "pct_hacinamiento": [15.0, 2.0]})
    fig = viz.plot_hacinamiento_por(df, "nivel económico")
    assert fig is not None


def test_plot_razon_dependencia_por_no_falla():
    df = pd.DataFrame({"departamento": ["MONTEVIDEO", "SALTO"], "razon_dependencia": [45.0, 55.0]})
    fig = viz.plot_razon_dependencia_por(df, "departamento")
    assert fig is not None


def test_plot_pct_unipersonales_mayores_no_falla():
    fig = viz.plot_pct_unipersonales_mayores({"pct_unipersonales_mayores": 60.0, "total_unipersonales": 50})
    assert fig is not None


def test_plot_brecha_digital_por_cohorte_no_falla():
    df = pd.DataFrame(
        {
            "cohorte": ["Millennials (1981-1996)", "Baby boomers (1946-1964)"],
            "tecnologia": ["Internet", "Internet"],
            "pct_penetracion": [90.0, 60.0],
        }
    )
    fig = viz.plot_brecha_digital_por_cohorte(df)
    assert fig is not None


def test_plot_brecha_digital_por_jefatura_no_falla():
    df = pd.DataFrame(
        {
            "jefe_sexo": ["1-Hombre", "2-Mujer"],
            "tecnologia": ["Internet", "Internet"],
            "pct_penetracion": [80.0, 78.0],
        }
    )
    fig = viz.plot_brecha_digital_por_jefatura(df)
    assert fig is not None


def test_plot_calidad_conexion_por_no_falla():
    df = pd.DataFrame(
        {"Sin conexión": [10.0, 2.0], "Solo móvil": [30.0, 8.0], "Banda ancha fija": [60.0, 90.0]},
        index=pd.Index(["1-Bajo", "5-Alto"], name="nivel_economico"),
    )
    fig = viz.plot_calidad_conexion_por(df, "nivel económico")
    assert fig is not None


def test_plot_indice_acceso_digital_por_no_falla():
    df = pd.DataFrame({"nivel_economico": ["1-Bajo", "5-Alto"], "indice_promedio": [1.5, 3.5]})
    fig = viz.plot_indice_acceso_digital_por(df, "nivel económico")
    assert fig is not None


def test_plot_adopcion_tablet_ibirapita_no_falla():
    df = pd.DataFrame({"jefe_es_mayor": [True, False], "pct_con_tablet": [25.0, 1.0]})
    fig = viz.plot_adopcion_tablet_ibirapita(df, "jefe es mayor")
    assert fig is not None


def test_plot_clasificacion_barrios_no_falla():
    df = pd.DataFrame(
        {
            "nivel_suscripcion": ["1-Baja", "2-Media-Baja", "3-Media-Alta", "4-Alta"],
            "cantidad_barrios": [10, 9, 9, 10],
        }
    )
    fig = viz.plot_clasificacion_barrios(df)
    assert fig is not None


def test_plot_dumbbell_no_falla_con_una_sola_categoria():
    fig = viz.plot_dumbbell(
        categorias=["FIES"],
        valores_a=[12.0],
        valores_b=[45.0],
        nombre_a="Quintil 1 (más pobre)",
        nombre_b="Quintil 5 (más rico)",
        titulo="Inseguridad alimentaria: quintil 1 vs. quintil 5",
    )
    assert fig is not None


def test_plot_dumbbell_ancla_el_eje_x_en_cero_con_varias_categorias():
    fig = viz.plot_dumbbell(
        categorias=["Hurto", "Rapiña", "Copamiento"],
        valores_a=[70.0, 55.0, 40.0],
        valores_b=[20.0, 35.0, 30.0],
        nombre_a="Comunicación informal",
        nombre_b="Denuncia formal",
        titulo="Brecha entre comunicación informal y denuncia formal",
    )
    assert fig.layout.xaxis.range[0] == 0
    # una línea + dos series de marcadores
    assert len(fig.data) == 3
