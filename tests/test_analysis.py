import pandas as pd

from encuesta_hogares.analysis import (
    composicion_hogar_por,
    condiciones_vivienda_diferencia,
    condiciones_vivienda_por,
    filtrar_segmento,
    ingreso_hogar_mediano_por_departamento,
    proporcion_cruzada,
    resumen_conectividad,
    situacion_ocupacional_por,
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
