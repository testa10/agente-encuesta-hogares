"""Comparación de la estructura de un año de datos contra lo que config.py espera.

Nace del incidente real del cambio de formato entre 2019 (.sav por módulo)
y 2024 (CSV combinado): ese cambio se descubrió en vivo, a los tumbos,
durante una sesión de más de media hora, porque nada comparaba
automáticamente las columnas reales del archivo nuevo contra lo que el
resto del código asumía que existía. Esta verificación no reemplaza la
revisión humana contra el diccionario oficial del INE (el significado de
una columna puede cambiar aunque el nombre no cambie), pero sí adelanta
en segundos la señal más barata y más costosa de perderse: "esta columna
que el código necesita ya no está en el archivo".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import config


@dataclass
class ResultadoComparacion:
    nombre: str
    archivo: Path
    columnas_esperadas: int
    faltantes: list[str] = field(default_factory=list)
    no_mapeadas: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.faltantes


def comparar_columnas(esperadas: dict[str, str], presentes: set[str]) -> tuple[list[str], list[str]]:
    """Compara las columnas que `config.py` espera (`esperadas`, un dict
    columna_origen -> nombre_legible) contra las que de verdad están en el
    archivo (`presentes`).

    Devuelve (faltantes, no_mapeadas):
    - faltantes: columnas que el código necesita y no están - esto rompe
      algo, es la señal que importa.
    - no_mapeadas: columnas del archivo que config.py todavía no usa - no
      es un error, es solo informativo (puede ser una variable nueva que
      vale la pena incorporar más adelante).
    """
    faltantes = sorted(c for c in esperadas if c not in presentes)
    no_mapeadas = sorted(presentes - set(esperadas))
    return faltantes, no_mapeadas


def _columnas_csv(path: Path) -> set[str]:
    return set(pd.read_csv(path, nrows=0, encoding="latin1").columns)


def _columnas_sav(path: Path) -> set[str]:
    import pyreadstat

    _, meta = pyreadstat.read_sav(str(path), metadataonly=True)
    return set(meta.column_names)


def verificar_hogares_personas(anio: int | str) -> list[ResultadoComparacion]:
    carpeta = config.DATA_DIR / str(anio)
    csv_path = config.hogares_csv_file(anio)
    if csv_path.exists():
        presentes = _columnas_csv(csv_path)
        faltantes, no_mapeadas = comparar_columnas(config.HOGARES_COLUMNS_CSV, presentes)
        resultados = [
            ResultadoComparacion(
                "Hogares (CSV combinado)", csv_path, len(config.HOGARES_COLUMNS_CSV), faltantes, no_mapeadas
            )
        ]
        faltantes_p, no_mapeadas_p = comparar_columnas(config.PERSONAS_COLUMNS_CSV, presentes)
        resultados.append(
            ResultadoComparacion(
                "Personas (dentro del CSV combinado)",
                csv_path,
                len(config.PERSONAS_COLUMNS_CSV),
                faltantes_p,
                no_mapeadas_p,
            )
        )
        return resultados

    resultados = []
    h_candidatos = sorted(carpeta.glob("H_*.sav"))
    if h_candidatos:
        presentes_h = _columnas_sav(h_candidatos[0])
        faltantes, no_mapeadas = comparar_columnas(config.HOGARES_COLUMNS, presentes_h)
        resultados.append(
            ResultadoComparacion("Hogares (.sav)", h_candidatos[0], len(config.HOGARES_COLUMNS), faltantes, no_mapeadas)
        )
    p_candidatos = sorted(carpeta.glob("P_*.sav"))
    if p_candidatos:
        presentes_p = _columnas_sav(p_candidatos[0])
        faltantes, no_mapeadas = comparar_columnas(config.PERSONAS_COLUMNS, presentes_p)
        resultados.append(
            ResultadoComparacion("Personas (.sav)", p_candidatos[0], len(config.PERSONAS_COLUMNS), faltantes, no_mapeadas)
        )
    return resultados


def verificar_fies(anio: int | str) -> ResultadoComparacion | None:
    path = config.fies_file(anio)
    if not path.exists():
        return None
    presentes = _columnas_csv(path)
    faltantes, no_mapeadas = comparar_columnas(config.FIES_COLUMNS, presentes)
    return ResultadoComparacion("FIES (seguridad alimentaria)", path, len(config.FIES_COLUMNS), faltantes, no_mapeadas)


def verificar_empleo(anio: int | str) -> list[ResultadoComparacion]:
    resultados: list[ResultadoComparacion] = []
    columnas_por_mes: dict[str, set[str]] = {}
    for path in config.empleo_files(anio):
        if not path.exists():
            continue
        presentes = _columnas_csv(path)
        columnas_por_mes[path.name] = presentes
        faltantes, no_mapeadas = comparar_columnas(config.EMPLEO_COLUMNS, presentes)
        resultados.append(
            ResultadoComparacion(f"Empleo ({path.name})", path, len(config.EMPLEO_COLUMNS), faltantes, no_mapeadas)
        )

    # El panel mensual debería tener la misma estructura los 12 meses - si un
    # mes difiere de los demás, promediar el año mezclaría cosas distintas
    # sin que nadie lo note (ver la regla de promediar mes a mes en
    # .claude/agents/encuesta-hogares.md).
    if len(columnas_por_mes) > 1:
        primer_nombre, primeras_cols = next(iter(columnas_por_mes.items()))
        for nombre, cols in columnas_por_mes.items():
            if cols != primeras_cols:
                diferencia = sorted(primeras_cols.symmetric_difference(cols))
                resultados.append(
                    ResultadoComparacion(
                        f"Consistencia mensual: {nombre} difiere de {primer_nombre}",
                        config.DATA_DIR / str(anio) / nombre,
                        0,
                        diferencia,
                        [],
                    )
                )
    return resultados


def verificar_victimizacion(anio: int | str) -> ResultadoComparacion | None:
    path = config.victimizacion_file(anio)
    if not path.exists():
        return None
    presentes = _columnas_csv(path)
    faltantes, no_mapeadas = comparar_columnas(config.VICTIMIZACION_COLUMNS, presentes)
    return ResultadoComparacion(
        "Seguridad y Victimización", path, len(config.VICTIMIZACION_COLUMNS), faltantes, no_mapeadas
    )


def verificar_anio(anio: int | str) -> list[ResultadoComparacion]:
    """Punto de entrada único: corre todas las verificaciones disponibles
    para un año (solo las de los archivos que de verdad existen en
    `data/{año}/`) y devuelve la lista completa de resultados."""
    resultados = list(verificar_hogares_personas(anio))
    fies = verificar_fies(anio)
    if fies is not None:
        resultados.append(fies)
    resultados.extend(verificar_empleo(anio))
    victimizacion = verificar_victimizacion(anio)
    if victimizacion is not None:
        resultados.append(victimizacion)
    return resultados
