"""Gráficos del análisis de conectividad. Los gráficos interactivos usan
Plotly; los gráficos estadísticos (heatmap, grillas comparativas) usan
matplotlib/seaborn.
"""

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

from .analysis import FILTROS_SUSCRIPCION, ResumenConectividad, filtrar_segmento


# ============================================================================
# Análisis principal: penetración de TV cable por barrio y nivel económico
# ============================================================================

def plot_distribucion_conectividad(resumen: ResumenConectividad):
    data = {
        "Tipo de Hogar": ["Con Cable", "Sin Cable"],
        "Porcentaje": [resumen.pct_con_cable, resumen.pct_sin_cable],
    }
    fig = px.bar(
        data,
        y="Tipo de Hogar",
        x="Porcentaje",
        orientation="h",
        title="Distribución de hogares de Montevideo",
        width=800,
        height=400,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(width=0.5, text=data["Porcentaje"], textposition="auto")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, title_x=0.5, title_y=0.85)
    return fig


def plot_penetracion_por_barrio(penetracion_por_barrio: pd.DataFrame):
    fig = px.scatter(
        penetracion_por_barrio,
        x="barrio",
        y="pct_abonados",
        color="nivel_suscripcion",
        title="Porcentaje de abonados a TV cable por barrio",
    )
    fig.update_layout(
        xaxis_title="Barrio",
        yaxis_title="Porcentaje (%)",
        xaxis={"categoryorder": "total descending", "tickangle": -60, "tickfont": {"size": 9}},
        width=1190,
        height=620,
        margin=dict(b=160),
        title_x=0.5,
        title_y=0.95,
    )

    promedio = penetracion_por_barrio["pct_abonados"].mean()
    fig.add_shape(
        type="line", x0=0.1, x1=1, y0=promedio, y1=promedio, xref="paper", yref="y",
        line=dict(color="gray", dash="dash"),
    )
    fig.add_annotation(
        x=0, y=promedio, xref="paper", yref="y", text=f"Promedio: {promedio:.2f}%",
        showarrow=False, font=dict(color="gray"),
    )
    return fig


def plot_tabla_barrios(penetracion_por_barrio: pd.DataFrame, nivel: str, titulo: str):
    subset = penetracion_por_barrio[penetracion_por_barrio["nivel_suscripcion"] == nivel]
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=["Barrio", "% de Abonados"], fill_color="moccasin", align="left"),
                cells=dict(values=[subset["barrio"], subset["pct_abonados"]], fill_color="lavender", align="left"),
            )
        ]
    )
    fig.update_layout(title=titulo, width=500, height=600, title_x=0.5, title_y=0.90)
    return fig


def plot_heatmap_suscripcion_vs_economico(hogares_abonados: pd.DataFrame):
    df_2dhist = pd.DataFrame(
        {
            nivel: (grupo["nivel_suscripcion"].value_counts(normalize=True) * 100).round(2)
            for nivel, grupo in hogares_abonados.groupby("nivel_economico", observed=True)
        }
    )

    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(df_2dhist, cmap="viridis", annot=True, fmt="g", cbar=True, ax=ax)
    ax.set_xlabel("Nivel económico")
    ax.set_ylabel("Nivel de suscripción")
    ax.set_title(
        "Relación entre el nivel de suscripción\ny el nivel económico de los hogares de Mdeo.",
        fontsize=13, pad=12,
    )
    fig.tight_layout()
    return fig


def _plot_grid_por_filtros(df: pd.DataFrame, get_serie, titulo: str, ylabel: str, value_fmt: str):
    """Grilla 2x2 genérica: un subplot de barras por cada segmento de FILTROS_SUSCRIPCION.

    `get_serie(segmento_df)` debe devolver una pd.Series (índice=categoría, valor=magnitud a graficar).
    """
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle(titulo, fontsize=15, y=0.98)
    axes = axes.flatten()

    for ax, filtro in zip(axes, FILTROS_SUSCRIPCION):
        segmento = filtrar_segmento(df, filtro)
        serie = get_serie(segmento)

        sns.barplot(x=serie.index, y=serie.values, hue=serie.index, palette="viridis", ax=ax, dodge=False, legend=False)
        for i, valor in enumerate(serie.values):
            ax.text(i, valor + serie.max() * 0.02, value_fmt.format(valor), color="black", ha="center", fontsize=9)

        ax.set_title(filtro["titulo"], fontsize=11, pad=10)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_ylim(0, serie.max() * 1.2)
        ax.tick_params(axis="x", labelsize=9, rotation=10)

    fig.subplots_adjust(hspace=0.45, wspace=0.25, top=0.90)
    return fig


def plot_composicion_edades(df: pd.DataFrame, promedio_edad_por_grupo):
    return _plot_grid_por_filtros(
        df,
        get_serie=promedio_edad_por_grupo,
        titulo="Composición de los hogares con y sin cable por promedio de edades",
        ylabel="Promedio edades",
        value_fmt="{:.1f}",
    )


def plot_composicion_sexo(df: pd.DataFrame, porcentaje_por_sexo, total_personas: int):
    return _plot_grid_por_filtros(
        df,
        get_serie=lambda segmento: porcentaje_por_sexo(segmento, total_personas),
        titulo="Composición de los hogares con y sin cable según sexo",
        ylabel="Promedio personas (%)",
        value_fmt="{:.2f}%",
    )


# ============================================================================
# Ampliación de métricas
# ============================================================================

def plot_brecha_digital(brecha_df: pd.DataFrame):
    """Barras agrupadas: penetración de cada tecnología por nivel económico."""
    fig = px.bar(
        brecha_df, x="nivel_economico", y="pct_penetracion", color="tecnologia",
        barmode="group", title="Brecha digital por nivel económico",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(
        xaxis_title="Nivel económico", yaxis_title="Penetración (%)",
        legend_title="Tecnología", width=900, height=500, title_x=0.5,
    )
    return fig


def _plot_barras_100_apiladas(tabla_pct: pd.DataFrame, titulo: str, xlabel: str):
    """Barras 100% apiladas: proporción de una variable dentro de categorías de otra."""
    fig, ax = plt.subplots(figsize=(8, 5))
    tabla_pct.plot(kind="bar", stacked=True, ax=ax, colormap="viridis", width=0.6)
    ax.set_title(titulo, fontsize=14)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("% dentro de cada grupo")
    ax.set_ylim(0, 100)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    ax.tick_params(axis="x", rotation=0)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def plot_acceso_por_nivel_economico(tabla_pct: pd.DataFrame, tecnologia: str):
    """Barras 100% apiladas: acceso a una tecnología según el nivel económico del hogar."""
    return _plot_barras_100_apiladas(
        tabla_pct,
        titulo=f"Acceso a {tecnologia} según nivel económico del hogar",
        xlabel="Nivel económico",
    )


def plot_acceso_por_pobreza(tabla_pct: pd.DataFrame, tecnologia: str):
    """Barras 100% apiladas: acceso a una tecnología según la condición de pobreza del hogar."""
    return _plot_barras_100_apiladas(
        tabla_pct,
        titulo=f"Acceso a {tecnologia} según condición de pobreza del hogar",
        xlabel="Condición de pobreza",
    )


def plot_situacion_ocupacional(tabla_ocupacion: pd.DataFrame, criterio: str):
    """Barras 100% apiladas: condición de actividad de las personas según un
    criterio de conectividad cualquiera (tipo de abonado, acceso a celular,
    acceso a internet, etc.).
    """
    return _plot_barras_100_apiladas(
        tabla_ocupacion,
        titulo=f"Condición de actividad de las personas según {criterio}",
        xlabel=criterio.capitalize(),
    )


def _plot_heatmap_cruzado(tabla_pct: pd.DataFrame, titulo: str, xlabel: str, ylabel: str):
    """Heatmap de una tabla cruzada de proporciones entre dos variables categóricas."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.heatmap(tabla_pct, annot=True, fmt=".1f", cmap="viridis", cbar_kws={"label": "%"}, ax=ax)
    ax.set_title(titulo, fontsize=13)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    return fig


def plot_streaming_vs_cable(tabla_streaming: pd.DataFrame):
    return _plot_heatmap_cruzado(
        tabla_streaming,
        titulo="¿Sustituye el streaming a la TV cable?",
        xlabel="Tiene streaming",
        ylabel="Tiene TV cable",
    )


def plot_internet_vs_cable(tabla_internet: pd.DataFrame):
    return _plot_heatmap_cruzado(
        tabla_internet,
        titulo="TV cable según tipo de conexión a internet",
        xlabel="Tipo de conexión a internet",
        ylabel="Tiene TV cable",
    )


def plot_ingreso_hogar_barras(df_extendido: pd.DataFrame):
    """Barras simples con el ingreso típico (el de la mitad de los hogares) del
    hogar, según conectividad a TV cable — más fácil de leer que un boxplot
    para alguien sin formación en estadística: solo hay que comparar el alto
    de las dos barras.
    """
    ingreso_sin = df_extendido.loc[~df_extendido["tiene_cable"], "ingreso_hogar"].dropna().median()
    ingreso_con = df_extendido.loc[df_extendido["tiene_cable"], "ingreso_hogar"].dropna().median()

    fig = px.bar(
        x=["Sin cable", "Con cable"], y=[ingreso_sin, ingreso_con],
        title="Ingreso típico del hogar según conectividad a TV cable",
        color=["Sin cable", "Con cable"],
        color_discrete_map={"Sin cable": "#d1495b", "Con cable": "#66a182"},
        text=[f"{ingreso_sin:,.0f}", f"{ingreso_con:,.0f}"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="", yaxis_title="Ingreso típico del hogar (UYU, sin valor locativo)",
        showlegend=False, width=650, height=500, title_x=0.5,
    )
    return fig


def plot_condiciones_vivienda(resumen_condiciones: pd.DataFrame, columnas: list, titulo: str, color_map: dict):
    """Barras horizontales agrupadas y ordenadas: condiciones estructurales de la vivienda según un grupo cualquiera."""
    df_plot = resumen_condiciones.melt(
        id_vars="condicion", value_vars=columnas,
        var_name="grupo", value_name="pct_hogares",
    )
    fig = px.bar(
        df_plot, y="condicion", x="pct_hogares", color="grupo",
        orientation="h", barmode="group",
        title=titulo,
        color_discrete_map=color_map,
    )
    fig.update_layout(
        yaxis_title="", xaxis_title="% de hogares con el problema",
        legend_title="", width=900, height=500, title_x=0.5,
        yaxis={"categoryorder": "total ascending"},
    )
    return fig


def plot_condiciones_vivienda_diferencia(diferencias: pd.DataFrame):
    """Barras horizontales agrupadas: diferencia en puntos porcentuales (con
    tecnología menos sin tecnología) de cada condición estructural de la
    vivienda, para varias tecnologías a la vez. Vista de síntesis de las
    gráficas de condiciones de vivienda por tecnología.
    """
    columnas = [c for c in diferencias.columns if c != "condicion"]
    df_plot = diferencias.melt(
        id_vars="condicion", value_vars=columnas, var_name="tecnologia", value_name="diferencia_pp"
    )
    orden = diferencias.set_index("condicion")[columnas].mean(axis=1).sort_values(ascending=False).index.tolist()

    fig = px.bar(
        df_plot, y="condicion", x="diferencia_pp", color="tecnologia",
        orientation="h", barmode="group",
        title="Diferencia en condiciones de vivienda según acceso a cada tecnología",
        category_orders={"condicion": orden},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(
        yaxis_title="", xaxis_title="Diferencia en puntos porcentuales (con - sin)",
        legend_title="", width=900, height=550, title_x=0.5,
    )
    fig.add_vline(x=0, line_color="gray")
    return fig


def plot_composicion_hogar(resumen_composicion: pd.DataFrame):
    """Barras agrupadas: composición promedio del hogar según conectividad."""
    df_plot = resumen_composicion.melt(
        id_vars="tipo_abonado",
        value_vars=["tamano_promedio", "promedio_menores_14", "promedio_ocupados"],
        var_name="metrica", value_name="promedio",
    )
    etiquetas = {
        "tamano_promedio": "Tamaño del hogar",
        "promedio_menores_14": "Menores de 14 años",
        "promedio_ocupados": "Personas ocupadas",
    }
    df_plot["metrica"] = df_plot["metrica"].map(etiquetas)
    fig = px.bar(
        df_plot, x="metrica", y="promedio", color="tipo_abonado", barmode="group",
        title="Composición promedio del hogar según conectividad a TV cable",
        color_discrete_map={"Sin cable": "#d1495b", "Con cable": "#66a182"},
    )
    fig.update_layout(xaxis_title="", yaxis_title="Promedio por hogar", legend_title="",
                       width=800, height=450, title_x=0.5)
    return fig


def plot_penetracion_nacional(resumen_departamentos: pd.DataFrame, resaltar: str = "MONTEVIDEO"):
    """Gráfico de puntos ordenado: penetración de TV cable por departamento, con uno resaltado."""
    df_plot = resumen_departamentos.copy()
    df_plot["resaltado"] = df_plot["departamento"] == resaltar

    fig = px.scatter(
        df_plot, x="pct_cable", y="departamento", color="resaltado",
        title="Penetración de TV cable por departamento (Uruguay)",
        color_discrete_map={True: "#d1495b", False: "#8d99ae"},
    )
    fig.update_traces(marker=dict(size=12))
    fig.update_layout(
        xaxis_title="% de hogares con TV cable", yaxis_title="",
        yaxis={"categoryorder": "total ascending"},
        showlegend=False, width=800, height=550, title_x=0.5,
    )
    promedio = df_plot["pct_cable"].mean()
    fig.add_vline(x=promedio, line_dash="dash", line_color="gray")
    fig.add_annotation(x=promedio, y=1.04, yref="paper", text=f"Promedio nacional: {promedio:.1f}%",
                        showarrow=False, font=dict(color="gray"))
    return fig
