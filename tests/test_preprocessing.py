import pandas as pd

from encuesta_hogares.preprocessing import (
    classify_edad_grupo,
    classify_nivel_economico,
    classify_sexo,
    compute_penetracion_nacional,
    decode_si_no,
    prepare_hogares_extendido,
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
