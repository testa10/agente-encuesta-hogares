"""Cálculos analíticos sobre las tablas ya preparadas."""

from dataclasses import dataclass

import pandas as pd

from . import config

# Segmentos combinando tipo de abonado y nivel de suscripción del barrio,
# reutilizados tanto para el análisis por edad como por sexo.
FILTROS_SUSCRIPCION = [
    {
        "titulo": "Con Cable - Barrio de Alta/Media-Alta Suscripción",
        "tipo_abonado": "Con cable",
        "niveles": {"4-Alta", "3-Media-Alta"},
    },
    {
        "titulo": "Con Cable - Barrio de Baja/Media-Baja Suscripción",
        "tipo_abonado": "Con cable",
        "niveles": {"1-Baja", "2-Media-Baja"},
    },
    {
        "titulo": "Sin Cable - Barrio de Alta/Media-Alta Suscripción",
        "tipo_abonado": "Sin cable",
        "niveles": {"4-Alta", "3-Media-Alta"},
    },
    {
        "titulo": "Sin Cable - Barrio de Baja/Media-Baja Suscripción",
        "tipo_abonado": "Sin cable",
        "niveles": {"1-Baja", "2-Media-Baja"},
    },
]


@dataclass
class ResumenConectividad:
    total_hogares: int
    hogares_con_cable: int
    hogares_sin_cable: int

    @property
    def pct_con_cable(self) -> float:
        return round(self.hogares_con_cable / self.total_hogares * 100, 2)

    @property
    def pct_sin_cable(self) -> float:
        return round(self.hogares_sin_cable / self.total_hogares * 100, 2)


def resumen_conectividad(hogares_mdeo: pd.DataFrame) -> ResumenConectividad:
    """Totales y porcentajes de hogares con/sin TV cable en Montevideo."""
    total = len(hogares_mdeo)
    con_cable = int((hogares_mdeo["tipo_abonado"] == 1.0).sum())
    return ResumenConectividad(total_hogares=total, hogares_con_cable=con_cable, hogares_sin_cable=total - con_cable)


def filtrar_segmento(df: pd.DataFrame, filtro: dict) -> pd.DataFrame:
    """Filtra el dataframe combinado según un segmento de FILTROS_SUSCRIPCION."""
    return df[(df["tipo_abonado"] == filtro["tipo_abonado"]) & (df["nivel_suscripcion"].isin(filtro["niveles"]))]


def promedio_edad_por_grupo(segmento: pd.DataFrame) -> pd.Series:
    """Edad promedio por tramo etario, dentro de un segmento ya filtrado."""
    return segmento.groupby("edad_grupo", observed=True)["edad"].mean().round(0)


def porcentaje_por_sexo(segmento: pd.DataFrame, total_personas: int) -> pd.Series:
    """% de personas por sexo (sobre el total general), dentro de un segmento ya filtrado."""
    return (segmento.groupby("sexo_grupo", observed=True)["id_persona"].count() / total_personas * 100).round(2)


# ============================================================================
# Ampliación de métricas
# ============================================================================

def proporcion_cruzada(df: pd.DataFrame, fila: str, columna: str) -> pd.DataFrame:
    """% de `columna` dentro de cada categoría de `fila` (cada fila suma 100%)."""
    return (pd.crosstab(df[fila], df[columna], normalize="index") * 100).round(2)


def brecha_digital_por_nivel_economico(df_extendido: pd.DataFrame) -> pd.DataFrame:
    """% de penetración de cada tecnología (cable, internet, PC, streaming), por nivel económico."""
    tecnologias = list(config.TECNOLOGIAS_LABELS.keys())
    resumen = (
        df_extendido.groupby("nivel_economico", observed=True)[tecnologias]
        .mean()
        .mul(100)
        .round(2)
        .reset_index()
        .melt(id_vars="nivel_economico", var_name="tecnologia", value_name="pct_penetracion")
    )
    resumen["tecnologia"] = resumen["tecnologia"].map(config.TECNOLOGIAS_LABELS)
    return resumen


def condiciones_vivienda_por(df_extendido: pd.DataFrame, columna_grupo: str, etiquetas: dict) -> pd.DataFrame:
    """% de hogares con cada problema estructural de vivienda, agrupado por
    una columna booleana cualquiera (ej. `tiene_cable`, `tiene_celular`,
    `tiene_streaming`).

    `etiquetas` mapea {False: "...", True: "..."} a los nombres de columna
    que va a tener el resultado.
    """
    condiciones_cols = list(config.CONDICIONES_VIVIENDA_COLUMNS.values())
    resumen = (
        df_extendido.groupby(columna_grupo)[condiciones_cols]
        .mean()
        .mul(100)
        .round(2)
        .T.rename(columns=etiquetas)
        .rename(index=config.CONDICION_VIVIENDA_LABELS)
        .reset_index()
        .rename(columns={"index": "condicion"})
        .sort_values(etiquetas[True])
    )
    return resumen


def condiciones_vivienda_diferencia(resumen: pd.DataFrame, col_sin: str, col_con: str) -> pd.Series:
    """Diferencia en puntos porcentuales (grupo "con" menos grupo "sin") de
    cada condición estructural de la vivienda, a partir de una tabla ya
    calculada con `condiciones_vivienda_por`. Sirve para comparar varias
    tecnologías en una misma vista de síntesis.
    """
    tabla = resumen.set_index("condicion")
    return (tabla[col_con] - tabla[col_sin]).round(2)


def composicion_hogar_por(df_extendido: pd.DataFrame, columna_grupo: str, etiquetas: dict) -> pd.DataFrame:
    """Tamaño promedio del hogar, y promedio de menores de 14 y de ocupados,
    agrupado por una columna booleana cualquiera (ej. `tiene_cable`,
    `tiene_internet`).
    """
    resumen = (
        df_extendido.groupby(columna_grupo)
        .agg(
            tamano_promedio=("total_personas", "mean"),
            promedio_menores_14=("menores_14", "mean"),
            promedio_ocupados=("ocupados_hogar", "mean"),
        )
        .round(2)
        .rename(index=etiquetas)
        .reset_index()
        .rename(columns={columna_grupo: "grupo"})
    )
    return resumen


def situacion_ocupacional_por(df_combinado: pd.DataFrame, columna_grupo: str) -> pd.DataFrame:
    """% de personas por condición de actividad (Ocupados/Desocupados/Inactivos),
    agrupado por una columna cualquiera (ej. `tipo_abonado`, o una columna de
    acceso a celular/internet ya etiquetada como "Con.../Sin...").

    Excluye a los menores de 14 años (categoría 1 de pobpcoac), que no integran
    la fuerza laboral.
    """
    df = df_combinado[df_combinado["condicion_actividad_cod"] != 1.0].copy()
    df["condicion_actividad"] = df["condicion_actividad_cod"].map(config.POBPCOAC_GRUPOS)
    return proporcion_cruzada(df, columna_grupo, "condicion_actividad")
