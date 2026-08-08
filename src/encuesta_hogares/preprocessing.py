"""Limpieza, clasificación y combinación de las bases de Hogares y Personas."""

import pandas as pd

from . import config


def classify_nivel_economico(estrato_tipo: pd.Series) -> pd.Series:
    """Clasifica el estrato socioeconómico (1-5) en una etiqueta legible."""
    return (
        estrato_tipo.astype("Int64")
        .map(config.NIVEL_ECONOMICO_LABELS)
        .fillna(config.NIVEL_ECONOMICO_DEFAULT)
    )


def classify_sexo(sexo: pd.Series) -> pd.Series:
    """Clasifica el sexo (1/2) en una etiqueta legible."""
    return sexo.astype("Int64").map(config.SEXO_LABELS).fillna(config.SEXO_DEFAULT)


def classify_edad_grupo(edad: pd.Series) -> pd.Series:
    """Agrupa la edad en tramos: niños/jóvenes, adultos y adultos mayores."""
    return pd.cut(edad, bins=config.EDAD_BINS, labels=config.EDAD_LABELS, right=False)


def prepare_hogares_montevideo(hogares: pd.DataFrame) -> pd.DataFrame:
    """Filtra los hogares de Montevideo y agrega el nivel económico."""
    hogares_mdeo = hogares.loc[hogares["departamento"] == "MONTEVIDEO"].copy()
    hogares_mdeo["nivel_economico"] = classify_nivel_economico(hogares_mdeo["estrato_tipo"])
    return hogares_mdeo


def compute_penetracion_por_barrio(hogares_mdeo: pd.DataFrame) -> pd.DataFrame:
    """Calcula el % de hogares con cable por barrio y su nivel de suscripción (por cuartiles)."""
    resumen = (
        hogares_mdeo.groupby("barrio")
        .agg(total_hogares=("id_hogar", "count"), pct_abonados=("tipo_abonado", lambda s: (s == 1.0).mean() * 100))
        .round(2)
        .reset_index()
        .sort_values("pct_abonados", ascending=False)
    )

    resumen["nivel_suscripcion"] = pd.qcut(
        resumen["pct_abonados"], q=4, labels=config.NIVEL_SUSCRIPCION_LABELS
    )
    return resumen


def merge_penetracion(hogares_mdeo: pd.DataFrame, penetracion_por_barrio: pd.DataFrame) -> pd.DataFrame:
    """Agrega el nivel de suscripción del barrio a cada hogar."""
    return hogares_mdeo.merge(
        penetracion_por_barrio[["barrio", "nivel_suscripcion"]], on="barrio", how="left"
    )


def merge_personas(hogares_resumen: pd.DataFrame, personas: pd.DataFrame) -> pd.DataFrame:
    """Agrega datos de las personas del hogar (edad, sexo, ingresos) a la tabla de hogares."""
    combinado = hogares_resumen.merge(personas, on="id_hogar", how="left").sort_values("id_hogar")
    combinado["tipo_abonado"] = combinado["tipo_abonado"].map(config.TIPO_ABONADO_LABELS)
    combinado["edad_grupo"] = classify_edad_grupo(combinado["edad"])
    combinado["sexo_grupo"] = classify_sexo(combinado["sexo"])
    return combinado


# ============================================================================
# Ampliación: brecha digital, pobreza, vivienda, composición del hogar y
# alcance nacional. Estas funciones no filtran a Montevideo salvo que se les
# pase un dataframe ya filtrado (ver notebook).
# ============================================================================

def decode_si_no(series: pd.Series) -> pd.Series:
    """Convierte una variable 1=Sí/2=No/99=Sin dato en booleano (99 -> NaN)."""
    return series.map(config.SI_NO_MAP)


def prepare_hogares_extendido(hogares_mdeo: pd.DataFrame) -> pd.DataFrame:
    """A partir de hogares ya filtrados (ej. Montevideo), decodifica las variables
    de tecnología, pobreza y condiciones de vivienda.
    """
    df = hogares_mdeo.copy()

    df["tiene_cable"] = df["tipo_abonado"] == 1.0
    for col in ["tiene_internet", "internet_fija", "internet_movil", "tiene_pc", "tiene_streaming"]:
        df[col] = decode_si_no(df[col])

    df["pobre"] = df["pobre"] == 1.0
    df["indigente"] = df["indigente"] == 1.0

    condiciones_cols = list(config.CONDICIONES_VIVIENDA_COLUMNS.values())
    for col in condiciones_cols:
        df[col] = decode_si_no(df[col])

    return df


def compute_tiene_celular_hogar(personas: pd.DataFrame) -> pd.DataFrame:
    """Determina, por hogar, si al menos una persona tiene teléfono celular.

    `tiene_celular_persona` es una variable a nivel de persona, no de hogar
    como `tipo_abonado` o `tiene_streaming` — por eso se agrega con `.any()`
    por `id_hogar` antes de poder cruzarla con datos del hogar.
    """
    personas = personas.copy()
    personas["tiene_celular_persona"] = decode_si_no(personas["tiene_celular_persona"])
    resumen = (
        personas.groupby("id_hogar")["tiene_celular_persona"]
        .any()
        .reset_index()
        .rename(columns={"tiene_celular_persona": "tiene_celular"})
    )
    return resumen


def compute_penetracion_nacional(hogares: pd.DataFrame) -> pd.DataFrame:
    """% de hogares con TV cable por departamento, para todo el país (sin filtrar a Montevideo)."""
    df = hogares.copy()
    df["tiene_cable"] = df["tipo_abonado"] == 1.0
    resumen = (
        df.groupby("departamento")
        .agg(total_hogares=("id_hogar", "count"), pct_cable=("tiene_cable", "mean"))
        .reset_index()
    )
    resumen["pct_cable"] = (resumen["pct_cable"] * 100).round(2)
    return resumen.sort_values("pct_cable", ascending=False)
