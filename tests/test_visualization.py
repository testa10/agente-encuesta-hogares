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


def test_plot_composicion_categorica_no_falla():
    df = pd.DataFrame(
        {"Empleado": [70.0, 50.0], "Cuentapropista": [30.0, 50.0]},
        index=pd.Index(["Formal", "Informal"], name="sector"),
    )
    fig = viz.plot_composicion_categorica(df, "Situación ocupacional por sector", "Sector")
    assert fig is not None


def test_plot_heatmap_suscripcion_vs_economico_no_falla():
    df = pd.DataFrame(
        {"1-Bajo": [40.0, 60.0], "5-Alto": [10.0, 90.0]},
        index=pd.Index(["1-Baja", "4-Alta"], name="nivel_suscripcion"),
    )
    fig = viz.plot_heatmap_suscripcion_vs_economico(df)
    assert fig is not None


def test_plot_streaming_vs_cable_no_falla():
    df = pd.DataFrame(
        {True: [60.0, 90.0], False: [40.0, 10.0]},
        index=pd.Index([True, False], name="tiene_cable"),
    )
    fig = viz.plot_streaming_vs_cable(df)
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


def test_plot_tasas_por_anio_usa_eje_x_numerico_con_los_anios_reales():
    tabla = pd.DataFrame(
        {
            "anio": [2019, 2024, 2025],
            "tasa_actividad": [62.0, 64.28, 65.0],
            "tasa_empleo": [58.0, 59.02, 60.0],
            "tasa_desempleo": [6.5, 8.18, 7.5],
        }
    )
    fig = viz.plot_tasas_por_anio(tabla)
    # Eje numerico real (no categorico) - 2019->2024 tiene que quedar mas
    # separado visualmente que 2024->2025, no parejo espaciado.
    assert fig.layout.xaxis.type == "linear"
    assert list(fig.layout.xaxis.tickvals) == [2019, 2024, 2025]
    # 3 series (actividad, empleo, desempleo), cada una con marcadores.
    assert len(fig.data) == 3
    assert all(trace.mode == "lines+markers" for trace in fig.data)


def test_plot_serie_por_anio_con_una_sola_serie():
    # Caso simple: una métrica de un solo número por año (ej. pobreza),
    # comparando 3 años no consecutivos.
    tabla = pd.DataFrame({"anio": [2019, 2024, 2025], "valor": [8.14, 12.99, 14.14]})
    fig = viz.plot_serie_por_anio(tabla, titulo="Pobreza por año", ylabel="% (ponderado)")
    assert fig.layout.xaxis.type == "linear"
    assert list(fig.layout.xaxis.tickvals) == [2019, 2024, 2025]
    assert len(fig.data) == 1
    assert fig.data[0].mode == "lines+markers"


def test_plot_serie_por_anio_con_varias_series_y_etiquetas():
    tabla = pd.DataFrame(
        {
            "anio": [2019, 2024],
            "jefatura_hombre": [53.43, 44.14],
            "jefatura_mujer": [46.57, 55.86],
        }
    )
    fig = viz.plot_serie_por_anio(
        tabla,
        etiquetas={"jefatura_hombre": "Hombre", "jefatura_mujer": "Mujer"},
        titulo="Jefatura por sexo",
    )
    assert len(fig.data) == 2
    nombres = {trace.name for trace in fig.data}
    assert nombres == {"Hombre", "Mujer"}


def test_plot_tasa_mensual_promedio_por_no_falla_y_es_horizontal():
    df = pd.DataFrame({"departamento": ["MONTEVIDEO", "TREINTA Y TRES"], "pct_promedio": [7.5, 9.2]})
    fig = viz.plot_tasa_mensual_promedio_por(df, "departamento", "Desempleo por departamento")
    assert fig is not None
    assert fig.data[0].orientation == "h"


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


def test_plot_precariedad_estructural_no_falla():
    fig = viz.plot_precariedad_estructural({"pct_con_carencia": 35.0, "total_hogares": 100, "hogares_con_carencia": 35})
    assert fig is not None


def test_plot_precariedad_estructural_por_es_horizontal():
    df = pd.DataFrame({"departamento": ["MONTEVIDEO", "SALTO"], "pct_precariedad": [20.0, 45.0]})
    fig = viz.plot_precariedad_estructural_por(df, "departamento")
    assert fig.data[0].orientation == "h"


def test_plot_carencias_estructurales_mas_frecuentes_no_falla():
    df = pd.DataFrame({"carencia": ["Goteras en techos", "Se inunda cuando llueve"], "pct_hogares": [40.0, 15.0]})
    fig = viz.plot_carencias_estructurales_mas_frecuentes(df)
    assert fig is not None


def test_plot_indice_desarrollo_territorial_ancla_el_eje_x_en_0_1():
    resultado = pd.DataFrame(
        {"pct_pobreza": [1.0, 0.0], "tasa_empleo": [0.0, 1.0], "indice": [0.5, 0.5]},
        index=pd.Index(["MONTEVIDEO", "SALTO"], name="departamento"),
    )
    fig = viz.plot_indice_desarrollo_territorial(resultado)
    assert fig.layout.xaxis.range[0] == 0


def test_plot_perfil_territorial_no_falla():
    resultado = pd.DataFrame(
        {"pct_pobreza": [1.0, 0.0], "tasa_empleo": [0.0, 1.0], "indice": [0.5, 0.5]},
        index=pd.Index(["MONTEVIDEO", "SALTO"], name="departamento"),
    )
    fig = viz.plot_perfil_territorial(resultado)
    assert fig is not None
