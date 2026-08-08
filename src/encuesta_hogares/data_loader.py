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
