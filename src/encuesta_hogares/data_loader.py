"""Carga de las bases de datos de la ECH (INE Uruguay).

Conviven dos familias de loaders porque el INE cambió el formato de
distribución de los microdatos entre 2019 y 2024:

- Años con archivos .sav separados por módulo (H_/P_...): `load_hogares`,
  `load_personas`, etc., vía `pyreadstat`.
- 2024 en adelante, CSV único combinado (`ECH_{año}.csv`, una fila por
  persona con las columnas de hogar repetidas): `load_hogares_personas_csv`.

Decisión consciente: no se abstrajo esto detrás de una interfaz común de
"loader de año". Con un solo cambio de formato real observado, cualquier
interfaz genérica sería una abstracción prematura basada en una muestra de
tamaño 1 - no hay forma de saber qué variará en un tercer formato hasta que
exista. Si el INE cambia el formato de nuevo (o aparece un tercer caso),
ese es el momento de extraer la interfaz común, con dos changes reales
como guía en vez de una imaginada.
"""

from __future__ import annotations

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


def fix_doble_codificacion(value):
    """Corrige texto que quedó doblemente codificado: unos pocos valores del
    CSV combinado (formato usado desde 2024 en adelante, ver
    HOGARES_COLUMNS_CSV en config.py) mezclan caracteres en latin1 (la
    mayoría de las tildes) con algún caracter guardado en UTF-8 dentro del
    mismo archivo — visto en el departamento "Río Negro", donde la í queda
    como dos caracteres sueltos en vez de uno. Se detectó leyendo el CSV
    crudo en bytes y comparando ambas codificaciones (no es un supuesto).

    El archivo ya se lee con `encoding="latin1"` (correcto para el resto de
    los acentos, ej. "Paysandú", "San José", "Tacuarembó"), así que acá solo
    hace falta re-codificar a bytes latin1 y decodificar como UTF-8 — si
    eso falla (el texto ya estaba bien), se devuelve el valor sin tocar.
    """
    if not isinstance(value, str):
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
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


def load_hogares_personas_csv(anio: int | str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga Hogares y Personas desde el CSV combinado (`config.hogares_csv_file`,
    formato usado desde 2024 en adelante — ver la nota en config.py sobre
    HOGARES_COLUMNS_CSV/PERSONAS_COLUMNS_CSV). El archivo trae una fila por
    persona, con las columnas de hogar repetidas para cada persona del mismo
    hogar, así que la vista de Hogares se arma deduplicando por id_hogar.

    A diferencia de `load_hogares()`, acá también se calcula
    "ocupados_hogar" (no viene precalculado en este formato): se cuenta, por
    hogar, cuántas personas tienen condicion_actividad_cod == 2 (Ocupados).
    """
    columnas_hogar = list(config.HOGARES_COLUMNS_CSV)
    columnas_persona = list(config.PERSONAS_COLUMNS_CSV)
    columnas = sorted(set(columnas_hogar) | set(columnas_persona))
    # encoding="latin1": el CSV combinado no viene en UTF-8 (ver
    # fix_doble_codificacion más arriba para el detalle de un caso mixto).
    df = pd.read_csv(config.hogares_csv_file(anio), usecols=columnas, encoding="latin1")

    personas = df.loc[:, columnas_persona].rename(columns=config.PERSONAS_COLUMNS_CSV)

    ocupados_hogar = (df["POBPCOAC"] == 2).groupby(df["ID"]).sum().rename("ocupados_hogar")

    hogares = (
        df.loc[:, columnas_hogar]
        .drop_duplicates("ID")
        .rename(columns=config.HOGARES_COLUMNS_CSV)
        .merge(ocupados_hogar, left_on="id_hogar", right_index=True, how="left")
    )
    hogares["departamento"] = hogares["departamento"].map(fix_doble_codificacion)
    return hogares, personas


def load_empleo(anio: int | str) -> pd.DataFrame:
    """Carga y concatena los 12 archivos mensuales de empleo
    (`config.empleo_files(anio)`) en un único DataFrame, con la columna
    `mes` conservada — necesaria para calcular cada métrica mes a mes y
    recién ahí promediar entre los 12 (ver nota metodológica en config.py).
    Nunca se pierde de qué mes vino cada fila.

    No todos los años tienen las mismas columnas — `INFORMAL`, `SECTOR_F`
    y `SIT_OCUP` desaparecieron de los archivos desde 2025 (verificado
    contra los datos reales que bajó el INE, no una suposición). Se pide
    a cada archivo solo las columnas de `config.EMPLEO_COLUMNS` que de
    verdad estén presentes en ese archivo puntual — mismo criterio que
    `preprocessing.decode_condiciones_vivienda` para Hogares — en vez de
    romper toda la carga por columnas que faltan. Las métricas que
    dependan de una columna ausente para el año elegido van a fallar
    recién ahí, con un error claro sobre qué falta — no antes, y no con
    un dato inventado.
    """
    columnas_originales = list(config.EMPLEO_COLUMNS)
    # encoding="latin1": mismos archivos fuente que el CSV combinado de
    # Hogares/Personas, con el mismo problema de codificación de acentos.
    meses = []
    for archivo in config.empleo_files(anio):
        columnas_presentes = set(pd.read_csv(archivo, nrows=0, encoding="latin1").columns)
        columnas_a_pedir = [c for c in columnas_originales if c in columnas_presentes]
        meses.append(pd.read_csv(archivo, usecols=columnas_a_pedir, encoding="latin1"))
    df = pd.concat(meses, ignore_index=True).rename(columns=config.EMPLEO_COLUMNS)
    df["departamento"] = df["departamento"].map(fix_doble_codificacion)
    return df


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
        pd.concat(
            pd.read_csv(a, usecols=["ID", "nom_dpto"], encoding="latin1") for a in archivos_segundo_semestre
        )
        .drop_duplicates("ID")
        .rename(columns={"ID": "id_hogar", "nom_dpto": "departamento"})
    )
    departamentos["departamento"] = departamentos["departamento"].map(fix_doble_codificacion)
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
