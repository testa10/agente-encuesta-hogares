import pandas as pd

from encuesta_hogares.preprocessing import (
    classify_edad_grupo,
    classify_nivel_economico,
    classify_sexo,
    compute_penetracion_nacional,
    decode_si_no,
    melt_delitos,
    prepare_empleo,
    prepare_fies,
    prepare_hogares_extendido,
    prepare_victimizacion,
)


def test_classify_nivel_economico():
    result = classify_nivel_economico(pd.Series([1, 3, 5, 9]))
    assert list(result) == ["1-Bajo", "3-Medio", "5-Alto", "6-No Definido"]


def test_classify_sexo():
    result = classify_sexo(pd.Series([1, 2, 9]))
    assert list(result) == ["1-Hombre", "2-Mujer", "3-Otro"]


def test_classify_edad_grupo():
    result = classify_edad_grupo(pd.Series([5, 14, 15, 64, 65, 90]))
    assert list(result.astype(str)) == [
        "1-Niños-Jovenes",
        "1-Niños-Jovenes",
        "2-Adultos",
        "2-Adultos",
        "3-Adultos_mayores",
        "3-Adultos_mayores",
    ]


def test_decode_si_no():
    result = decode_si_no(pd.Series([1.0, 2.0, 99.0]))
    assert result.tolist()[:2] == [True, False]
    assert pd.isna(result.iloc[2])


def _hogares_extendido_ejemplo():
    return pd.DataFrame(
        {
            "id_hogar": [1, 2, 3, 4],
            "departamento": ["MONTEVIDEO"] * 4,
            "tipo_abonado": [1.0, 1.0, 2.0, 2.0],
            "estrato_tipo": [5.0, 1.0, 5.0, 1.0],
            "nivel_economico": ["5-Alto", "1-Bajo", "5-Alto", "1-Bajo"],
            "total_personas": [2.0, 4.0, 3.0, 5.0],
            "menores_14": [0.0, 2.0, 1.0, 2.0],
            "ocupados_hogar": [1.0, 1.0, 2.0, 1.0],
            "pobre": [2.0, 1.0, 2.0, 1.0],
            "indigente": [2.0, 2.0, 2.0, 2.0],
            "ingreso_hogar": [80000.0, 20000.0, 60000.0, 15000.0],
            "tiene_internet": [1.0, 2.0, 1.0, 2.0],
            "internet_fija": [1.0, 2.0, 1.0, 2.0],
            "internet_movil": [2.0, 2.0, 2.0, 1.0],
            "tiene_pc": [1.0, 2.0, 1.0, 1.0],
            "tiene_streaming": [1.0, 2.0, 2.0, 2.0],
            **{col: [1.0, 2.0, 1.0, 2.0] for col in [
                "humedad_techos", "goteras", "muros_agrietados", "puertas_ventanas_deterioradas",
                "grietas_pisos", "caida_revoque", "cielorraso_desprendido", "poca_luz_solar",
                "escasa_ventilacion", "se_inunda", "peligro_derrumbe", "humedad_cimientos",
            ]},
        }
    )


def test_prepare_hogares_extendido_decodes_booleanos():
    df = prepare_hogares_extendido(_hogares_extendido_ejemplo())
    assert df["tiene_cable"].tolist() == [True, True, False, False]
    assert df["pobre"].tolist() == [False, True, False, True]
    assert df["tiene_internet"].tolist() == [True, False, True, False]
    assert df["goteras"].tolist() == [True, False, True, False]


def test_compute_penetracion_nacional():
    hogares = pd.DataFrame(
        {
            "id_hogar": [1, 2, 3, 4],
            "departamento": ["MONTEVIDEO", "MONTEVIDEO", "SALTO", "SALTO"],
            "tipo_abonado": [1.0, 2.0, 1.0, 1.0],
        }
    )
    resumen = compute_penetracion_nacional(hogares)
    salto = resumen[resumen["departamento"] == "SALTO"].iloc[0]
    mdeo = resumen[resumen["departamento"] == "MONTEVIDEO"].iloc[0]
    assert salto["pct_cable"] == 100.0
    assert mdeo["pct_cable"] == 50.0


def test_prepare_fies_clasifica_por_umbral_y_etiqueta_region():
    df = pd.DataFrame(
        {
            "prob_inseguridad_moderada": [0.6, 0.4, 0.5],
            "prob_inseguridad_severa": [0.6, 0.1, 0.2],
            "region_cod": [1, 2, 1],
            "tiene_menores_18": [1, 0, 1],
            "tiene_menores_6": [0, 0, 1],
        }
    )
    resultado = prepare_fies(df)
    assert resultado["inseguridad_moderada_o_severa"].tolist() == [True, False, True]
    assert resultado["inseguridad_severa"].tolist() == [True, False, False]
    assert resultado["region"].tolist() == ["Montevideo", "Interior", "Montevideo"]
    assert resultado["tiene_menores_18"].tolist() == [True, False, True]
    assert resultado["tiene_menores_6"].tolist() == [False, False, True]


def test_prepare_empleo_mapea_actividad_sexo_y_edad():
    df = pd.DataFrame(
        {
            "condicion_actividad_cod": [2.0, 3.0, 6.0],
            "es_informal": [1, 0, 0],
            "es_subempleo": [0, 0, 0],
            "sexo": [1, 2, 1],
            "edad": [20, 40, 24],
        }
    )
    resultado = prepare_empleo(df)
    assert resultado["condicion_actividad"].tolist() == ["Ocupados", "Desocupados", "Inactivos"]
    assert resultado["es_informal"].tolist() == [True, False, False]
    assert resultado["es_subempleo"].tolist() == [False, False, False]
    assert resultado["sexo_grupo"].tolist() == ["1-Hombre", "2-Mujer", "1-Hombre"]
    assert resultado["grupo_edad_laboral"].tolist() == ["Joven (14-24)", "Resto", "Joven (14-24)"]


def test_prepare_victimizacion_marca_victimizado_algun_delito():
    df = pd.DataFrame(
        {
            "sexo": [1, 2],
            "v3": [0, 0], "v4": [0, 1], "v5": [0, 0], "v6": [0, 0], "v7": [0, 0],
        }
    )
    resultado = prepare_victimizacion(df)
    assert resultado["sexo_grupo"].tolist() == ["1-Hombre", "2-Mujer"]
    assert resultado["victimizado_algun_delito"].tolist() == [False, True]


def test_melt_delitos_arma_formato_largo_con_subpreguntas_correctas():
    df = pd.DataFrame(
        {
            "id_persona": [1],
            "sexo_grupo": ["1-Hombre"],
            "departamento": ["MONTEVIDEO"],
            "ponderador_victimizacion": [100.0],
            "v3": [1], "v3_4": [1], "v3_6": [1], "v3_8": [2],
            "v4": [0], "v4_4": [0], "v4_6": [0], "v4_8": [0],
            "v5": [0], "v5_4": [0], "v5_6": [0], "v5_8": [0],
            "v6": [0], "v6_2": [0], "v6_4": [0],
            "v7": [0], "v7_4": [0], "v7_6": [0],
        }
    )
    largo = melt_delitos(df)

    fila_v3 = largo[largo["tipo_delito"] == "Robo total de vehículo"].iloc[0]
    assert fila_v3["victimizado"] == True
    assert fila_v3["comunicacion_policia"] == True
    assert fila_v3["denuncia_formal"] == False
    assert fila_v3["violencia"] == True

    fila_v6 = largo[largo["tipo_delito"] == "Estafa"].iloc[0]
    # v6 (estafa) no tiene sub-pregunta de violencia en el cuestionario
    assert fila_v6["violencia"] == False
