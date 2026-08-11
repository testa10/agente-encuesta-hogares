import pandas as pd

from encuesta_hogares.analysis import (
    brecha_por_grupo,
    composicion_hogar_por,
    condiciones_vivienda_diferencia,
    condiciones_vivienda_por,
    diferencia_entre_categorias,
    diferencia_entre_tablas,
    filtrar_segmento,
    ingreso_hogar_mediano_por_departamento,
    inseguridad_alimentaria_por,
    pct_ponderado_por,
    prevalencia_inseguridad_alimentaria,
    proporcion_cruzada,
    resumen_conectividad,
    situacion_ocupacional_por,
    tasa_mensual_promedio_por,
    tasas_actividad_empleo_desempleo,
    tasas_actividad_empleo_desempleo_por,
)


def test_resumen_conectividad():
    hogares = pd.DataFrame({"tipo_abonado": [1.0, 1.0, 2.0, 2.0, 2.0]})
    resumen = resumen_conectividad(hogares)
    assert resumen.total_hogares == 5
    assert resumen.hogares_con_cable == 2
    assert resumen.hogares_sin_cable == 3
    assert resumen.pct_con_cable == 40.0
    assert resumen.pct_sin_cable == 60.0


def test_filtrar_segmento():
    df = pd.DataFrame(
        {
            "tipo_abonado": ["Con cable", "Con cable", "Sin cable"],
            "nivel_suscripcion": ["4-Alta", "1-Baja", "4-Alta"],
        }
    )
    filtro = {"tipo_abonado": "Con cable", "niveles": {"4-Alta", "3-Media-Alta"}}
    resultado = filtrar_segmento(df, filtro)
    assert len(resultado) == 1
    assert resultado.iloc[0]["nivel_suscripcion"] == "4-Alta"


def test_proporcion_cruzada_suma_100_por_fila():
    df = pd.DataFrame(
        {
            "pobreza": ["Pobre", "Pobre", "No pobre", "No pobre", "No pobre"],
            "cable": ["Con cable", "Sin cable", "Con cable", "Con cable", "Sin cable"],
        }
    )
    tabla = proporcion_cruzada(df, "pobreza", "cable")
    assert tabla.loc["Pobre", "Con cable"] == 50.0
    assert tabla.loc["Pobre", "Sin cable"] == 50.0
    assert round(tabla.loc["No pobre", "Con cable"], 2) == 66.67


def test_condiciones_vivienda_por():
    df = pd.DataFrame(
        {
            "tiene_celular": [True, True, False, False],
            "goteras": [True, False, True, True],
        }
    )
    # Solo usamos una condicion para simplificar el test - la funcion espera
    # todas las columnas de config.CONDICIONES_VIVIENDA_COLUMNS, asi que
    # completamos el resto con valores fijos.
    from encuesta_hogares import config
    for col in config.CONDICIONES_VIVIENDA_COLUMNS.values():
        if col not in df.columns:
            df[col] = False

    resumen = condiciones_vivienda_por(df, "tiene_celular", {False: "Sin celular", True: "Con celular"})
    fila_goteras = resumen[resumen["condicion"] == "Goteras en techos"].iloc[0]
    assert fila_goteras["Con celular"] == 50.0
    assert fila_goteras["Sin celular"] == 100.0


def test_condiciones_vivienda_por_tolera_columnas_faltantes():
    # A partir de 2024 solo hay 4 de las 12 columnas de vivienda (ver
    # config.CONDICIONES_VIVIENDA_COLUMNS_CSV) - la función solo debe usar
    # las que están presentes en el dataframe, sin fallar por las demás.
    df = pd.DataFrame(
        {
            "tiene_celular": [True, True, False, False],
            "goteras": [True, False, True, True],
        }
    )
    resumen = condiciones_vivienda_por(df, "tiene_celular", {False: "Sin celular", True: "Con celular"})
    assert resumen["condicion"].tolist() == ["Goteras en techos"]
    fila_goteras = resumen[resumen["condicion"] == "Goteras en techos"].iloc[0]
    assert fila_goteras["Con celular"] == 50.0
    assert fila_goteras["Sin celular"] == 100.0


def test_condiciones_vivienda_diferencia():
    resumen = pd.DataFrame(
        {
            "condicion": ["Goteras en techos", "Humedad en cimientos"],
            "Sin celular": [100.0, 40.0],
            "Con celular": [50.0, 30.0],
        }
    )
    diferencia = condiciones_vivienda_diferencia(resumen, "Sin celular", "Con celular")
    assert diferencia["Goteras en techos"] == -50.0
    assert diferencia["Humedad en cimientos"] == -10.0


def test_situacion_ocupacional_excluye_menores():
    df = pd.DataFrame(
        {
            "tipo_abonado": ["Con cable", "Con cable", "Con cable", "Sin cable"],
            "condicion_actividad_cod": [1.0, 2.0, 6.0, 2.0],  # 1 = menor de 14
        }
    )
    tabla = situacion_ocupacional_por(df, "tipo_abonado")
    # Con cable: 1 ocupado + 1 inactivo (el menor de 14 se excluye) -> 50/50
    assert tabla.loc["Con cable", "Ocupados"] == 50.0
    assert tabla.loc["Con cable", "Inactivos"] == 50.0


def test_composicion_hogar_por_agrupa_por_cualquier_columna():
    df = pd.DataFrame(
        {
            "tiene_internet": [True, True, False, False],
            "total_personas": [4.0, 2.0, 3.0, 1.0],
            "menores_14": [2.0, 0.0, 1.0, 0.0],
            "ocupados_hogar": [1.0, 2.0, 1.0, 1.0],
        }
    )
    resumen = composicion_hogar_por(
        df, "tiene_internet", {False: "Sin internet", True: "Con internet"}
    )
    fila_con = resumen[resumen["grupo"] == "Con internet"].iloc[0]
    assert fila_con["tamano_promedio"] == 3.0
    assert fila_con["promedio_menores_14"] == 1.0


def test_ingreso_hogar_mediano_por_departamento():
    hogares = pd.DataFrame(
        {
            "departamento": ["RIVERA", "RIVERA", "RIVERA", "MONTEVIDEO", "MONTEVIDEO", "SALTO"],
            "ingreso_hogar": [10000.0, 20000.0, 30000.0, 50000.0, 70000.0, 999999.0],
        }
    )
    resultado = ingreso_hogar_mediano_por_departamento(hogares, ["RIVERA", "MONTEVIDEO"])
    assert resultado["RIVERA"] == 20000.0
    assert resultado["MONTEVIDEO"] == 60000.0
    assert "SALTO" not in resultado.index


def test_prevalencia_inseguridad_alimentaria_pondera_correctamente():
    df = pd.DataFrame(
        {
            "inseguridad_moderada_o_severa": [True, True, False, False],
            "inseguridad_severa": [True, False, False, False],
            "ponderador_fies": [100.0, 100.0, 100.0, 100.0],
        }
    )
    resultado = prevalencia_inseguridad_alimentaria(df)
    assert resultado["moderada_o_severa"] == 50.0
    assert resultado["severa"] == 25.0


def test_inseguridad_alimentaria_por_pondera_por_grupo_no_solo_cuenta_filas():
    df = pd.DataFrame(
        {
            "quintil_ingreso": [1, 1, 5, 5],
            "inseguridad_moderada_o_severa": [True, False, False, False],
            "ponderador_fies": [300.0, 100.0, 50.0, 50.0],
        }
    )
    resumen = inseguridad_alimentaria_por(df, "quintil_ingreso").set_index("quintil_ingreso")
    # quintil 1: 300 de ponderador "inseguro" sobre 400 totales -> 75%, no 50%
    # (que seria el resultado si se contaran filas en vez de ponderar)
    assert resumen.loc[1, "pct_inseguridad"] == 75.0
    assert resumen.loc[5, "pct_inseguridad"] == 0.0


def test_inseguridad_alimentaria_por_usa_la_columna_de_clasificacion_indicada():
    df = pd.DataFrame(
        {
            "region": ["Montevideo", "Montevideo"],
            "inseguridad_moderada_o_severa": [True, True],
            "inseguridad_severa": [True, False],
            "ponderador_fies": [100.0, 100.0],
        }
    )
    resumen = inseguridad_alimentaria_por(df, "region", columna_clasificacion="inseguridad_severa")
    assert resumen.iloc[0]["pct_inseguridad"] == 50.0


def test_tasas_actividad_empleo_desempleo_promedia_por_mes():
    df = pd.DataFrame(
        {
            "mes": [1, 1, 1, 2, 2, 2],
            "condicion_actividad": ["Ocupados", "Desocupados", "Inactivos"] * 2,
            "ponderador_empleo": [80.0, 20.0, 100.0, 80.0, 20.0, 100.0],
        }
    )
    tasas = tasas_actividad_empleo_desempleo(df)
    # cada mes: total=200, activos=100 (ocupados 80 + desocupados 20)
    assert tasas["tasa_actividad"] == 50.0
    assert tasas["tasa_empleo"] == 40.0
    assert tasas["tasa_desempleo"] == 20.0


def test_tasa_mensual_promedio_por_promedia_meses_en_vez_de_hacer_pool():
    df = pd.DataFrame(
        {
            "mes": [1, 1, 1, 1, 2, 2],
            "departamento": ["A", "A", "A", "A", "A", "A"],
            "positivo": [True, False, False, False, True, False],
            "ponderador_empleo": [10.0, 10.0, 10.0, 10.0, 100.0, 100.0],
        }
    )
    resumen = tasa_mensual_promedio_por(df, "departamento", "positivo")
    # mes 1: 10/40=25%, mes 2: 100/200=50% -> promedio 37.5%
    # el pool directo daria 110/240=45.83%, un numero distinto
    assert resumen.iloc[0]["pct_promedio"] == 37.5


def test_tasas_actividad_empleo_desempleo_por_desagrega_por_grupo():
    df = pd.DataFrame(
        {
            "mes": [1, 1, 1, 1, 1, 1],
            "sexo_grupo": ["1-Hombre", "1-Hombre", "1-Hombre", "2-Mujer", "2-Mujer", "2-Mujer"],
            "condicion_actividad": ["Ocupados", "Desocupados", "Inactivos"] * 2,
            "ponderador_empleo": [70.0, 30.0, 100.0, 50.0, 50.0, 100.0],
        }
    )
    resumen = tasas_actividad_empleo_desempleo_por(df, "sexo_grupo").set_index("sexo_grupo")
    assert resumen.loc["1-Hombre", "tasa_desempleo"] == 30.0
    assert resumen.loc["2-Mujer", "tasa_desempleo"] == 50.0


def test_brecha_por_grupo_calcula_diferencia_en_puntos():
    resumen = pd.DataFrame(
        {
            "sexo_grupo": ["1-Hombre", "2-Mujer"],
            "tasa_actividad": [73.0, 56.8],
            "tasa_empleo": [68.7, 51.6],
            "tasa_desempleo": [5.9, 9.3],
        }
    )
    brecha = brecha_por_grupo(resumen, "sexo_grupo", "1-Hombre", "2-Mujer")
    assert brecha["tasa_actividad"] == 16.2
    assert round(brecha["tasa_desempleo"], 1) == -3.4


def test_diferencia_entre_categorias_calcula_diferencia_en_puntos():
    resumen = pd.DataFrame(
        {
            "quintil_ingreso": [1, 2, 3, 4, 5],
            "pct_inseguridad": [45.0, 30.0, 20.0, 10.0, 5.0],
        }
    )
    diferencia = diferencia_entre_categorias(resumen, "quintil_ingreso", 1, 5, "pct_inseguridad")
    assert diferencia == 40.0


def test_pct_ponderado_por_calcula_porcentaje_ponderado_no_conteo_de_filas():
    df = pd.DataFrame(
        {
            "grupo": ["A", "A", "B", "B"],
            "positivo": [True, False, True, True],
            "peso": [10.0, 10.0, 5.0, 15.0],
        }
    )
    resumen = pct_ponderado_por(df, "grupo", "positivo", "peso").set_index("grupo")
    assert resumen.loc["A", "pct"] == 50.0
    assert resumen.loc["B", "pct"] == 100.0


def test_diferencia_entre_tablas_cruza_por_indice():
    tabla_a = pd.DataFrame({"tipo": ["X", "Y"], "pct": [80.0, 60.0]})
    tabla_b = pd.DataFrame({"tipo": ["X", "Y"], "pct": [50.0, 60.0]})
    diferencia = diferencia_entre_tablas(tabla_a, tabla_b, "tipo", "pct")
    assert diferencia["X"] == 30.0
    assert diferencia["Y"] == 0.0
