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
    # Igual que en preprocessing.prepare_hogares_extendido: no todos los años
    # tienen las 12 columnas (ver config.CONDICIONES_VIVIENDA_COLUMNS_CSV),
    # así que solo se usan las que están presentes en este dataframe.
    condiciones_cols = [c for c in config.CONDICIONES_VIVIENDA_COLUMNS.values() if c in df_extendido.columns]
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


def ingreso_hogar_mediano_por_departamento(hogares: pd.DataFrame, departamentos: list) -> pd.Series:
    """Ingreso típico (mediana, más robusta a valores extremos que el
    promedio) del hogar, sin valor locativo, para los departamentos
    indicados. No requiere filtrar a Montevideo — usa la tabla de hogares
    completa.
    """
    subset = hogares[hogares["departamento"].isin(departamentos)]
    return subset.groupby("departamento")["ingreso_hogar"].median().round(0)


def diferencia_entre_categorias(
    resumen: pd.DataFrame, columna_grupo: str, categoria_a, categoria_b, columna_valor: str
) -> float:
    """Diferencia en puntos porcentuales (categoria_a menos categoria_b) para
    dos categorías cualquiera de una misma tabla ya calculada (ej. el
    quintil de ingreso más rico contra el más pobre, en una tabla armada con
    `inseguridad_alimentaria_por`). Mismo patrón que `brecha_por_grupo` y
    `condiciones_vivienda_diferencia`, pero para tablas con una sola columna
    de valor por categoría en vez de una columna por grupo.
    """
    tabla = resumen.set_index(columna_grupo)
    return round(tabla.loc[categoria_a, columna_valor] - tabla.loc[categoria_b, columna_valor], 2)


def prevalencia_inseguridad_alimentaria(fies_clasificado: pd.DataFrame) -> dict:
    """% de hogares (ponderado por `ponderador_fies`, no por el ponderador
    general de la encuesta) en inseguridad alimentaria moderada-o-severa y
    severa, a nivel nacional. FIES cubre una submuestra de hogares, no el
    total del año — este cálculo ya lo tiene en cuenta vía el ponderador.
    """
    total_ponderado = fies_clasificado["ponderador_fies"].sum()
    moderada_o_severa = (
        fies_clasificado.loc[fies_clasificado["inseguridad_moderada_o_severa"], "ponderador_fies"].sum()
        / total_ponderado * 100
    )
    severa = (
        fies_clasificado.loc[fies_clasificado["inseguridad_severa"], "ponderador_fies"].sum()
        / total_ponderado * 100
    )
    return {"moderada_o_severa": round(moderada_o_severa, 2), "severa": round(severa, 2)}


def inseguridad_alimentaria_por(
    fies_clasificado: pd.DataFrame, columna_grupo: str, columna_clasificacion: str = "inseguridad_moderada_o_severa"
) -> pd.DataFrame:
    """% de hogares en inseguridad alimentaria (ponderado por `ponderador_fies`),
    agrupado por una columna cualquiera (ej. quintil de ingreso, región).
    `columna_clasificacion` permite reutilizar la función tanto para
    moderada-o-severa como para severa.
    """
    df = fies_clasificado.copy()
    df["_ponderador_positivo"] = df["ponderador_fies"].where(df[columna_clasificacion], 0.0)
    resumen = df.groupby(columna_grupo).agg(
        total_ponderado=("ponderador_fies", "sum"),
        positivo_ponderado=("_ponderador_positivo", "sum"),
    )
    resumen["pct_inseguridad"] = (resumen["positivo_ponderado"] / resumen["total_ponderado"] * 100).round(2)
    return resumen[["pct_inseguridad"]].reset_index()


def tasas_actividad_empleo_desempleo(empleo: pd.DataFrame) -> dict:
    """Tasas de actividad, empleo y desempleo (definiciones estándar del
    INE), ponderadas por `ponderador_empleo`. Se calculan mes a mes y se
    promedian entre los 12 meses — nunca sobre el pool de los 12 CSV juntos,
    porque cada hogar permanece en el panel 6 meses seguidos y eso pesaría
    de más a quien lleva más tiempo en la muestra (ver nota en config.py).
    Tasa de desempleo = desocupados / (ocupados + desocupados), no sobre el
    total de personas.
    """
    df = empleo.copy()
    df["_ocupado_pond"] = df["ponderador_empleo"].where(df["condicion_actividad"] == "Ocupados", 0.0)
    df["_desocupado_pond"] = df["ponderador_empleo"].where(df["condicion_actividad"] == "Desocupados", 0.0)
    df["_activo_pond"] = df["ponderador_empleo"].where(
        df["condicion_actividad"].isin(["Ocupados", "Desocupados"]), 0.0
    )

    por_mes = df.groupby("mes").agg(
        total=("ponderador_empleo", "sum"),
        ocupados=("_ocupado_pond", "sum"),
        desocupados=("_desocupado_pond", "sum"),
        activos=("_activo_pond", "sum"),
    )
    por_mes["tasa_actividad"] = por_mes["activos"] / por_mes["total"] * 100
    por_mes["tasa_empleo"] = por_mes["ocupados"] / por_mes["total"] * 100
    por_mes["tasa_desempleo"] = por_mes["desocupados"] / por_mes["activos"] * 100

    return {
        "tasa_actividad": round(por_mes["tasa_actividad"].mean(), 2),
        "tasa_empleo": round(por_mes["tasa_empleo"].mean(), 2),
        "tasa_desempleo": round(por_mes["tasa_desempleo"].mean(), 2),
    }


def tasas_actividad_empleo_desempleo_por(empleo: pd.DataFrame, columna_grupo: str) -> pd.DataFrame:
    """Igual que `tasas_actividad_empleo_desempleo`, pero desagregado por una
    columna cualquiera (`sexo_grupo`, `grupo_edad_laboral`) — sirve tanto
    para la brecha de género como para comparar el desempleo juvenil contra
    el resto. Mismo cálculo mes a mes y promedio entre los 12 meses, ahora
    dentro de cada grupo.
    """
    df = empleo.copy()
    df["_ocupado_pond"] = df["ponderador_empleo"].where(df["condicion_actividad"] == "Ocupados", 0.0)
    df["_desocupado_pond"] = df["ponderador_empleo"].where(df["condicion_actividad"] == "Desocupados", 0.0)
    df["_activo_pond"] = df["ponderador_empleo"].where(
        df["condicion_actividad"].isin(["Ocupados", "Desocupados"]), 0.0
    )

    por_mes_grupo = df.groupby(["mes", columna_grupo]).agg(
        total=("ponderador_empleo", "sum"),
        ocupados=("_ocupado_pond", "sum"),
        desocupados=("_desocupado_pond", "sum"),
        activos=("_activo_pond", "sum"),
    )
    por_mes_grupo["tasa_actividad"] = por_mes_grupo["activos"] / por_mes_grupo["total"] * 100
    por_mes_grupo["tasa_empleo"] = por_mes_grupo["ocupados"] / por_mes_grupo["total"] * 100
    por_mes_grupo["tasa_desempleo"] = por_mes_grupo["desocupados"] / por_mes_grupo["activos"] * 100

    resumen = por_mes_grupo.groupby(columna_grupo)[["tasa_actividad", "tasa_empleo", "tasa_desempleo"]].mean().round(2)
    return resumen.reset_index()


def brecha_por_grupo(resumen_por_grupo: pd.DataFrame, columna_grupo: str, grupo_a: str, grupo_b: str) -> pd.Series:
    """Diferencia en puntos porcentuales (grupo_a menos grupo_b) de cada
    tasa, a partir de una tabla ya calculada con
    `tasas_actividad_empleo_desempleo_por` — mismo patrón que
    `condiciones_vivienda_diferencia`, para el texto de síntesis.
    """
    tabla = resumen_por_grupo.set_index(columna_grupo)
    columnas_tasas = [c for c in tabla.columns if c.startswith("tasa_")]
    return (tabla.loc[grupo_a, columnas_tasas] - tabla.loc[grupo_b, columnas_tasas]).round(2)


def tasa_mensual_promedio_por(
    df: pd.DataFrame, columna_grupo: str, columna_positivo: str, columna_ponderador: str = "ponderador_empleo"
) -> pd.DataFrame:
    """% ponderado de `columna_positivo` (una columna booleana), agrupado
    por `columna_grupo`, calculado mes a mes y promediado entre los 12
    meses — misma lógica que `tasas_actividad_empleo_desempleo`, pero
    genérica para reutilizar en cualquier corte (departamento, nivel
    educativo, sexo). El `df` que se le pasa ya tiene que venir filtrado al
    universo correcto (ej. solo Ocupados, para informalidad o subempleo).
    """
    df = df.copy()
    df["_positivo_pond"] = df[columna_ponderador].where(df[columna_positivo], 0.0)
    por_mes_grupo = df.groupby(["mes", columna_grupo]).agg(
        total=(columna_ponderador, "sum"),
        positivo=("_positivo_pond", "sum"),
    )
    por_mes_grupo["pct"] = por_mes_grupo["positivo"] / por_mes_grupo["total"] * 100
    resumen = por_mes_grupo.groupby(columna_grupo)["pct"].mean().round(2).reset_index()
    return resumen.rename(columns={"pct": "pct_promedio"})


def pct_ponderado_por(df: pd.DataFrame, columna_grupo: str, columna_positivo: str, columna_ponderador: str) -> pd.DataFrame:
    """% ponderado de `columna_positivo` (booleana), agrupado por
    `columna_grupo` — sin promedio mensual, a diferencia de
    `tasa_mensual_promedio_por`. Sirve para datos que no vienen en panel
    rotativo mensual (Victimización, un corte del semestre).
    """
    df = df.copy()
    df["_positivo_pond"] = df[columna_ponderador].where(df[columna_positivo], 0.0)
    resumen = df.groupby(columna_grupo).agg(
        total=(columna_ponderador, "sum"),
        positivo=("_positivo_pond", "sum"),
    )
    resumen["pct"] = (resumen["positivo"] / resumen["total"] * 100).round(2)
    return resumen[["pct"]].reset_index()


def diferencia_entre_tablas(
    tabla_a: pd.DataFrame, tabla_b: pd.DataFrame, columna_indice: str, columna_valor: str
) -> pd.Series:
    """Diferencia en puntos porcentuales (tabla_a menos tabla_b) para la
    misma columna de valor, cruzando dos tablas por su columna de índice
    (ej. comunicación a la policía vs denuncia formal, ambas por tipo de
    delito) — mismo patrón que `condiciones_vivienda_diferencia` y
    `brecha_por_grupo`.
    """
    a = tabla_a.set_index(columna_indice)[columna_valor]
    b = tabla_b.set_index(columna_indice)[columna_valor]
    return (a - b).round(2)


# ============================================================================
# Hogares (composición, sin tecnología) y Brecha Digital (con marco
# internacional) — ver la nota de fuentes en config.py y el detalle
# metodológico en .claude/agents/encuesta-hogares.md.
# ============================================================================

def pct_pobres_indigentes(hogares_extendido: pd.DataFrame) -> dict:
    """% de hogares pobres y % en indigencia (el grado más severo, un
    subconjunto de los pobres)."""
    return {
        "pct_pobres": round(hogares_extendido["pobre"].mean() * 100, 2),
        "pct_indigentes": round(hogares_extendido["indigente"].mean() * 100, 2),
    }


def tasa_jefatura_femenina(tipo_hogar: pd.DataFrame) -> dict:
    """% de hogares cuyo jefe/a es mujer, sobre el total de hogares con
    jefatura identificada. Indicador estándar CEPAL/CELADE."""
    total = int(tipo_hogar["jefe_sexo"].notna().sum())
    mujeres = int((tipo_hogar["jefe_sexo"] == "2-Mujer").sum())
    return {"pct_jefatura_femenina": round(mujeres / total * 100, 2), "total_hogares": total}


def tipos_hogar_resumen(tipo_hogar: pd.DataFrame) -> pd.DataFrame:
    """% de hogares de cada tipo (Unipersonal/Nuclear/Extendido/Compuesto/
    Sin núcleo — ver preprocessing.clasificar_tipo_hogar), de mayor a menor."""
    resumen = (
        tipo_hogar["tipo_hogar"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
        .rename("pct_hogares")
        .rename_axis("tipo_hogar")
        .reset_index()
    )
    return resumen.sort_values("pct_hogares", ascending=False).reset_index(drop=True)


def pct_hacinamiento_por(hogares_hacinamiento: pd.DataFrame, columna_grupo: str) -> pd.DataFrame:
    """% de hogares en situación de hacinamiento (ver
    preprocessing.compute_hacinamiento), agrupado por una columna cualquiera."""
    resumen = (
        hogares_hacinamiento.groupby(columna_grupo, observed=True)["hacinado"]
        .mean()
        .mul(100)
        .round(2)
        .reset_index()
        .rename(columns={"hacinado": "pct_hacinamiento"})
    )
    return resumen


def razon_dependencia_demografica(personas: pd.DataFrame) -> float:
    """(menores de 15 + mayores de 65) / población en edad activa (15-64) x 100.
    Indicador demográfico estándar CEPAL/CELADE — es una relación
    *potencial* (por edad), no mide actividad económica real."""
    menores = (personas["edad"] < 15).sum()
    mayores = (personas["edad"] >= 65).sum()
    activos = personas["edad"].between(15, 64).sum()
    return round((menores + mayores) / activos * 100, 2)


def razon_dependencia_por(personas_con_grupo: pd.DataFrame, columna_grupo: str) -> pd.DataFrame:
    """Razón de dependencia demográfica (ver `razon_dependencia_demografica`),
    agrupada por una columna cualquiera (ej. departamento)."""
    filas = []
    for grupo, sub in personas_con_grupo.groupby(columna_grupo):
        menores = (sub["edad"] < 15).sum()
        mayores = (sub["edad"] >= 65).sum()
        activos = sub["edad"].between(15, 64).sum()
        razon = round((menores + mayores) / activos * 100, 2) if activos else None
        filas.append({columna_grupo: grupo, "razon_dependencia": razon})
    return pd.DataFrame(filas)


def pct_unipersonales_mayores(tipo_hogar: pd.DataFrame) -> dict:
    """De los hogares unipersonales, qué % tiene 65 años o más (su único
    integrante es, por definición, el jefe/a). CEPAL: en América Latina esto
    puede señalar vulnerabilidad, a diferencia de países desarrollados donde
    suele leerse como autonomía — ver nota en
    .claude/agents/encuesta-hogares.md."""
    unipersonales = tipo_hogar[tipo_hogar["tipo_hogar"] == "Unipersonal"]
    total = len(unipersonales)
    mayores = int((unipersonales["jefe_edad"] >= 65).sum())
    return {
        "pct_unipersonales_mayores": round(mayores / total * 100, 2) if total else 0.0,
        "total_unipersonales": total,
    }


def brecha_digital_por_cohorte(df_extendido_con_cohorte: pd.DataFrame) -> pd.DataFrame:
    """% de penetración de cada tecnología, por cohorte generacional del
    jefe/a de hogar (ver preprocessing.compute_cohorte_generacional). Mismo
    cálculo que `brecha_digital_por_nivel_economico`, agrupado por cohorte."""
    tecnologias = list(config.TECNOLOGIAS_LABELS.keys())
    resumen = (
        df_extendido_con_cohorte.groupby("cohorte", observed=True)[tecnologias]
        .mean()
        .mul(100)
        .round(2)
        .reset_index()
        .melt(id_vars="cohorte", var_name="tecnologia", value_name="pct_penetracion")
    )
    resumen["tecnologia"] = resumen["tecnologia"].map(config.TECNOLOGIAS_LABELS)
    return resumen


def brecha_digital_por_jefatura(df_extendido_con_jefatura: pd.DataFrame) -> pd.DataFrame:
    """% de penetración de cada tecnología, según si el hogar tiene jefe o
    jefa mujer. CEPAL documenta que en la región la brecha de género ya casi
    no está en la tenencia del hogar sino en el uso individual — no
    encontrar diferencia acá es un resultado consistente con esa literatura,
    no un resultado vacío (ver .claude/agents/encuesta-hogares.md)."""
    tecnologias = list(config.TECNOLOGIAS_LABELS.keys())
    resumen = (
        df_extendido_con_jefatura.groupby("jefe_sexo", observed=True)[tecnologias]
        .mean()
        .mul(100)
        .round(2)
        .reset_index()
        .melt(id_vars="jefe_sexo", var_name="tecnologia", value_name="pct_penetracion")
    )
    resumen["tecnologia"] = resumen["tecnologia"].map(config.TECNOLOGIAS_LABELS)
    return resumen


def indice_acceso_digital_por(df_con_indice: pd.DataFrame, columna_grupo: str) -> pd.DataFrame:
    """Promedio del índice de acceso digital (0-4, ver
    preprocessing.compute_indice_acceso_digital), agrupado por una columna
    cualquiera."""
    return (
        df_con_indice.groupby(columna_grupo, observed=True)["indice_acceso_digital"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={"indice_acceso_digital": "indice_promedio"})
    )


def adopcion_tablet_ibirapita_por(hogares_extendido: pd.DataFrame, columna_grupo: str) -> pd.DataFrame:
    """% de hogares con tablet del Plan Ibirapitá (programa estatal de
    inclusión digital para personas mayores), agrupado por una columna
    cualquiera (ej. si el jefe/a de hogar es adulto mayor).

    `tiene_tablet_ibirapita` sale de `decode_si_no` en dtype `object`
    (True/False/NaN) — `.astype("boolean")` la pasa al tipo nullable de
    pandas antes de promediar, si no `.mean()`/`.round()` pueden fallar o
    dar un resultado no numérico cuando hay algún "sin dato" (ver
    preprocessing.compute_indice_acceso_digital, mismo motivo)."""
    return (
        hogares_extendido.assign(tiene_tablet_ibirapita=hogares_extendido["tiene_tablet_ibirapita"].astype("boolean"))
        .groupby(columna_grupo, observed=True)["tiene_tablet_ibirapita"]
        .mean()
        .astype("float64")
        .mul(100)
        .round(2)
        .reset_index()
        .rename(columns={"tiene_tablet_ibirapita": "pct_con_tablet"})
    )
