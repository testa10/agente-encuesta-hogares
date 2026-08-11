"""Carga de las bases de datos .sav (ECH - INE Uruguay)."""

from pathlib import Path

import pandas as pd
import pyreadstat

from . import config


def fix_mojibake(value):
    """Corrige caracteres mal codificados (ver config.MOJIBAKE_FIX)."""
    if not isinstance(value, str):
        return value
    for bad, good in config.MOJIBAKE_FIX.items():
        value = value.replace(bad, good)
    return value


def load_hogares(path: Path = config.HOGARES_FILE) -> pd.DataFrame:
    """Carga la base de Hogares y devuelve solo las columnas necesarias, renombradas."""
    df, _meta = pyreadstat.read_sav(str(path))
    df = df.loc[:, list(config.HOGARES_COLUMNS)].rename(columns=config.HOGARES_COLUMNS)
    df["barrio"] = df["barrio"].map(fix_mojibake)
    return df


def load_personas(path: Path = config.PERSONAS_FILE) -> pd.DataFrame:
    """Carga la base de Personas y devuelve solo las columnas necesarias, renombradas."""
    df, _meta = pyreadstat.read_sav(str(path))
    df = df.loc[:, list(config.PERSONAS_COLUMNS)].rename(columns=config.PERSONAS_COLUMNS)
    return df


def load_empleo(anio: int | str) -> pd.DataFrame:
    """Carga y concatena los 12 archivos mensuales de empleo
    (`config.empleo_files(anio)`) en un único DataFrame, con la columna
    `mes` conservada — necesaria para calcular cada métrica mes a mes y
    recién ahí promediar entre los 12 (ver nota metodológica en config.py).
    Nunca se pierde de qué mes vino cada fila.
    """
    columnas_originales = list(config.EMPLEO_COLUMNS)
    meses = [pd.read_csv(archivo, usecols=columnas_originales) for archivo in config.empleo_files(anio)]
    df = pd.concat(meses, ignore_index=True)
    return df.rename(columns=config.EMPLEO_COLUMNS)


def load_victimizacion(anio: int | str) -> pd.DataFrame:
    """Carga el archivo de victimización de un año y le agrega el
    departamento, cruzado por ID contra los archivos mensuales de julio a
    diciembre (segundo semestre — mismo período que releva este módulo). El
    archivo de victimización no trae departamento propio.
    """
    columnas_originales = list(config.VICTIMIZACION_COLUMNS)
    df = pd.read_csv(config.victimizacion_file(anio), usecols=columnas_originales)
    df = df.rename(columns=config.VICTIMIZACION_COLUMNS)

    archivos_segundo_semestre = config.empleo_files(anio)[6:]
    departamentos = (
        pd.concat(pd.read_csv(a, usecols=["ID", "nom_dpto"]) for a in archivos_segundo_semestre)
        .drop_duplicates("ID")
        .rename(columns={"ID": "id_hogar", "nom_dpto": "departamento"})
    )
    return df.merge(departamentos, on="id_hogar", how="left")


def load_fies(path: Path) -> pd.DataFrame:
    """Carga la base de seguridad alimentaria (FIES) y devuelve solo las
    columnas necesarias, renombradas. Es un CSV, no un .sav — y a diferencia
    de Hogares/Personas, `path` no tiene valor por defecto a propósito: FIES
    no existe para todos los años, así que el año siempre se pasa explícito
    (usar `config.fies_file(anio)` para resolver la ruta).
    """
    df = pd.read_csv(path)
    return df.loc[:, list(config.FIES_COLUMNS)].rename(columns=config.FIES_COLUMNS)
