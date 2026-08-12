import pandas as pd

from encuesta_hogares.analysis import (
    adopcion_tablet_ibirapita_por,
    brecha_digital_por_cohorte,
    brecha_digital_por_jefatura,
    brecha_por_grupo,
    composicion_hogar_por,
    condiciones_vivienda_diferencia,
    condiciones_vivienda_por,
    diferencia_entre_categorias,
    diferencia_entre_tablas,
    filtrar_segmento,
    indice_acceso_digital_por,
    ingreso_hogar_mediano_por_departamento,
    inseguridad_alimentaria_por,
    pct_hacinamiento_por,
    pct_pobres_indigentes,
    pct_ponderado_por,
    pct_unipersonales_mayores,
    prevalencia_inseguridad_alimentaria,
    proporcion_cruzada,
    razon_dependencia_demografica,
    razon_dependencia_por,
    resumen_conectividad,
    situacion_ocupacional_por,
    tasa_mensual_promedio_por,
    tasas_actividad_empleo_desempleo,
    tasas_actividad_empleo_desempleo_por,
    tasa_jefatura_femenina,
    tipos_hogar_resumen,
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


# ============================================================================
# Hogares y Brecha Digital
# ============================================================================

def test_pct_pobres_indigentes():
    df = pd.DataFrame({"pobre": [True, True, False, False], "indigente": [True, False, False, False]})
    resultado = pct_pobres_indigentes(df)
    assert resultado == {"pct_pobres": 50.0, "pct_indigentes": 25.0}


def test_tasa_jefatura_femenina():
    df = pd.DataFrame({"jefe_sexo": ["1-Hombre", "2-Mujer", "2-Mujer", "1-Hombre", None]})
    resultado = tasa_jefatura_femenina(df)
    assert resultado == {"pct_jefatura_femenina": 50.0, "total_hogares": 4}


def test_tipos_hogar_resumen_ordena_de_mayor_a_menor():
    df = pd.DataFrame({"tipo_hogar": ["Nuclear", "Nuclear", "Nuclear", "Unipersonal", "Extendido"]})
    resumen = tipos_hogar_resumen(df)
    assert resumen.iloc[0]["tipo_hogar"] == "Nuclear"
    assert resumen.iloc[0]["pct_hogares"] == 60.0


def test_pct_hacinamiento_por():
    df = pd.DataFrame({"nivel_economico": ["1-Bajo", "1-Bajo", "5-Alto"], "hacinado": [True, False, False]})
    resumen = pct_hacinamiento_por(df, "nivel_economico").set_index("nivel_economico")
    assert resumen.loc["1-Bajo", "pct_hacinamiento"] == 50.0
    assert resumen.loc["5-Alto", "pct_hacinamiento"] == 0.0


def test_razon_dependencia_demografica():
    # 2 menores de 15, 1 mayor de 65, 3 en edad activa (15-64) -> 3/3*100 = 100.0
    personas = pd.DataFrame({"edad": [5, 10, 70, 20, 40, 60]})
    assert razon_dependencia_demografica(personas) == 100.0


def test_razon_dependencia_por():
    personas = pd.DataFrame(
        {
            "departamento": ["MONTEVIDEO", "MONTEVIDEO", "MONTEVIDEO", "SALTO", "SALTO"],
            "edad": [5, 30, 40, 30, 40],
        }
    )
    resumen = razon_dependencia_por(personas, "departamento").set_index("departamento")
    assert resumen.loc["MONTEVIDEO", "razon_dependencia"] == 50.0
    assert resumen.loc["SALTO", "razon_dependencia"] == 0.0


def test_pct_unipersonales_mayores():
    df = pd.DataFrame(
        {
            "tipo_hogar": ["Unipersonal", "Unipersonal", "Unipersonal", "Nuclear"],
            "jefe_edad": [70, 30, 68, 40],
        }
    )
    resultado = pct_unipersonales_mayores(df)
    assert resultado == {"pct_unipersonales_mayores": round(2 / 3 * 100, 2), "total_unipersonales": 3}


def test_pct_unipersonales_mayores_sin_unipersonales():
    df = pd.DataFrame({"tipo_hogar": ["Nuclear"], "jefe_edad": [40]})
    resultado = pct_unipersonales_mayores(df)
    assert resultado == {"pct_unipersonales_mayores": 0.0, "total_unipersonales": 0}


def test_brecha_digital_por_cohorte():
    df = pd.DataFrame(
        {
            "cohorte": ["Millennials (1981-1996)", "Millennials (1981-1996)", "Baby boomers (1946-1964)"],
            "tiene_cable": [True, False, True],
            "tiene_internet": [True, True, False],
            "tiene_pc": [True, True, False],
            "tiene_streaming": [True, False, False],
        }
    )
    resumen = brecha_digital_por_cohorte(df)
    fila = resumen[(resumen["cohorte"] == "Millennials (1981-1996)") & (resumen["tecnologia"] == "TV Cable")]
    assert fila["pct_penetracion"].iloc[0] == 50.0


def test_brecha_digital_por_jefatura():
    df = pd.DataFrame(
        {
            "jefe_sexo": ["1-Hombre", "1-Hombre", "2-Mujer"],
            "tiene_cable": [True, False, True],
            "tiene_internet": [True, True, True],
            "tiene_pc": [True, True, True],
            "tiene_streaming": [False, False, True],
        }
    )
    resumen = brecha_digital_por_jefatura(df)
    fila = resumen[(resumen["jefe_sexo"] == "1-Hombre") & (resumen["tecnologia"] == "TV Cable")]
    assert fila["pct_penetracion"].iloc[0] == 50.0


def test_indice_acceso_digital_por():
    df = pd.DataFrame({"nivel_economico": ["1-Bajo", "1-Bajo", "5-Alto"], "indice_acceso_digital": [1, 3, 4]})
    resumen = indice_acceso_digital_por(df, "nivel_economico").set_index("nivel_economico")
    assert resumen.loc["1-Bajo", "indice_promedio"] == 2.0
    assert resumen.loc["5-Alto", "indice_promedio"] == 4.0


def test_adopcion_tablet_ibirapita_por():
    df = pd.DataFrame({"jefe_es_mayor": [True, True, False], "tiene_tablet_ibirapita": [True, False, False]})
    resumen = adopcion_tablet_ibirapita_por(df, "jefe_es_mayor").set_index("jefe_es_mayor")
    assert resumen.loc[True, "pct_con_tablet"] == 50.0
    assert resumen.loc[False, "pct_con_tablet"] == 0.0
