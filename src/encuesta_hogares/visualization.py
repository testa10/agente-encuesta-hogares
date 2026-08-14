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


def plot_dumbbell(categorias: list, valores_a: list, valores_b: list, nombre_a: str, nombre_b: str, titulo: str, xlabel: str = "%"):
    """Dumbbell chart (dos puntos por categoría, conectados por una línea):
    compara dos series de valores a través de una o más categorías —
    ej. "quintil 1" vs. "quintil 5", o "comunicación informal" vs.
    "denuncia formal" para varios tipos de delito a la vez.

    Es la práctica recomendada por la literatura de visualización de
    datos (Tufte; Knaflic, storytellingwithdata.com; Nightingale/Data
    Visualization Society) para comparar dos grupos específicos, en vez
    de una barra con la diferencia ya calculada — conserva los dos
    valores reales además de la brecha entre ellos, algo que una sola
    barra de "diferencia" no muestra (ver docs/CONVENCIONES_DE_GRAFICAS.md).

    Plotly no trae este tipo de gráfica nativo (ni Plotly Express ni
    ninguna librería especializada mejor mantenida vale la pena sumar
    como dependencia nueva solo para esto) — se arma a mano con
    `go.Scatter`: una traza de líneas (los segmentos que conectan cada
    par) y dos trazas de marcadores (una por serie).
    """
    line_x, line_y = [], []
    for categoria, valor_a, valor_b in zip(categorias, valores_a, valores_b):
        line_x += [valor_a, valor_b, None]
        line_y += [categoria, categoria, None]

    fig = go.Figure(
        data=[
            go.Scatter(x=line_x, y=line_y, mode="lines", line=dict(color="#8b949e", width=2), showlegend=False, hoverinfo="skip"),
            go.Scatter(x=valores_a, y=categorias, mode="markers", name=nombre_a, marker=dict(color="#d1495b", size=14)),
            go.Scatter(x=valores_b, y=categorias, mode="markers", name=nombre_b, marker=dict(color="#66a182", size=14)),
        ]
    )
    altura = max(300, 80 * len(categorias) + 150)
    fig.update_layout(
        title=titulo,
        title_x=0.5,
        xaxis_title=xlabel,
        yaxis_title="",
        # Mismo motivo que en plot_penetracion_por_barrio: un scatter no
        # arranca en cero solo, hay que fijarlo a mano.
        xaxis_range=[0, max(max(valores_a), max(valores_b)) * 1.15],
        width=850,
        height=altura,
    )
    return fig


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
    # "barrio" puede venir como código numérico (años sin nombre de barrio,
    # ver HOGARES_COLUMNS_CSV en config.py) o como texto (2019). Si se deja
    # numérico, Plotly arma un eje continuo y "categoryorder" no hace nada
    # -- pasándolo a texto, el eje queda categórico y el orden por
    # suscripción sí se aplica, aunque el barrio se identifique por número.
    df_plot = penetracion_por_barrio.copy()
    df_plot["barrio"] = df_plot["barrio"].astype(str)

    fig = px.scatter(
        df_plot,
        x="barrio",
        y="pct_abonados",
        color="nivel_suscripcion",
        title="Porcentaje de abonados a TV cable por barrio",
    )
    fig.update_layout(
        xaxis_title="Barrio",
        yaxis_title="Porcentaje (%)",
        xaxis={"categoryorder": "total descending", "tickangle": -60, "tickfont": {"size": 9}},
        # El eje de un valor (acá, %) siempre tiene que arrancar en cero y no
        # recortarse -- a diferencia de las barras, que Plotly ya ancla en
        # cero solas, un scatter autoescala al rango de los datos y exagera
        # visualmente las diferencias si no se fija el rango a mano.
        yaxis_range=[0, penetracion_por_barrio["pct_abonados"].max() * 1.1],
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


def plot_clasificacion_barrios(resumen: pd.DataFrame):
    """Barras: cantidad de barrios en cada nivel de suscripción. Es un
    conteo de categorías (no una distribución continua), por eso barras y
    no boxplot/violin — ver docs/CONVENCIONES_DE_GRAFICAS.md.
    """
    fig = px.bar(
        resumen, x="nivel_suscripcion", y="cantidad_barrios",
        title="Clasificación de barrios por nivel de suscripción",
        text="cantidad_barrios",
        color_discrete_sequence=["#5a7fa6"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="Nivel de suscripción", yaxis_title="Cantidad de barrios",
        width=700, height=450, title_x=0.5, showlegend=False,
    )
    return fig


def plot_heatmap_suscripcion_vs_economico(tabla_pct: pd.DataFrame):
    """Heatmap: % PONDERADO de hogares en cada nivel de suscripción del
    barrio, dentro de cada nivel económico (ver
    `analysis.suscripcion_vs_nivel_economico`, que arma `tabla_pct` con
    índice=nivel_suscripcion, columnas=nivel_economico).
    """
    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(tabla_pct, cmap="viridis", annot=True, fmt=".1f", cbar=True, ax=ax)
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
    """Grilla de barras: edad promedio por tramo etario, dentro de cada
    segmento de suscripción/abonado (ver FILTROS_SUSCRIPCION).

    Un promedio graficado como barra, sin mostrar la dispersión alrededor,
    es en general el patrón de "dynamite plot" que Weissgerber et al.
    (2015, PLOS Biology) desaconsejan para datos continuos — puede ocultar
    que dos grupos con la misma barra tienen formas de distribución muy
    distintas. Acá el riesgo es bajo porque `edad_grupo` ya es un tramo
    etario angosto (ver config.py): el promedio dentro de un tramo ya
    acotado no puede variar mucho más que el ancho del tramo mismo, así
    que la barra no está ocultando una dispersión relevante.
    """
    return _plot_grid_por_filtros(
        df,
        get_serie=promedio_edad_por_grupo,
        titulo="Composición de los hogares con y sin cable por promedio de edades",
        ylabel="Promedio edades",
        value_fmt="{:.1f}",
    )


def plot_composicion_sexo(df: pd.DataFrame, porcentaje_por_sexo, total_personas: int):
    """Grilla de barras: % de personas por sexo, dentro de cada segmento de
    suscripción/abonado (ver FILTROS_SUSCRIPCION). Es una proporción, no
    un promedio de una variable continua — a diferencia de
    `plot_composicion_edades`, no aplica la reserva de Weissgerber et al.
    sobre "dynamite plots", porque no hay una distribución subyacente que
    la barra esté ocultando.
    """
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


def plot_ingreso_hogar_departamento(serie: pd.Series):
    """Barras horizontales: ingreso típico del hogar por departamento (19
    categorías, algunas con nombres largos) — horizontales para que se
    lean sin inclinar la cabeza (Cleveland & McGill, 1984), mismo criterio
    que `plot_razon_dependencia_por` para el mismo tipo de comparación.
    """
    fig = px.bar(
        y=serie.index, x=serie.values, orientation="h",
        title="Ingreso típico del hogar por departamento",
        color=serie.index,
        color_discrete_sequence=px.colors.qualitative.Safe,
        text=[f"{v:,.0f}" for v in serie.values],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_title="", xaxis_title="Ingreso típico del hogar (UYU, sin valor locativo)",
        yaxis={"categoryorder": "total ascending"},
        showlegend=False, width=800, height=550, title_x=0.5,
    )
    return fig


def plot_precariedad_estructural(resultado: dict):
    """Barras horizontales: % de hogares con y sin al menos una carencia
    estructural (índice de conteo de carencias — ver
    docs/CONVENCIONES_DE_GRAFICAS.md, o analysis.precariedad_estructural).
    """
    data = {
        "Condición": ["Con carencia estructural", "Sin carencia estructural"],
        "Porcentaje": [resultado["pct_con_carencia"], round(100 - resultado["pct_con_carencia"], 2)],
    }
    fig = px.bar(
        data, y="Condición", x="Porcentaje", orientation="h",
        title="Precariedad estructural de la vivienda",
        width=800, height=350, color_discrete_sequence=["#d1495b"],
    )
    fig.update_traces(width=0.5, text=data["Porcentaje"], textposition="auto")
    fig.update_layout(xaxis_title="% de hogares", yaxis_title="", title_x=0.5)
    return fig


def plot_precariedad_estructural_por(resumen: pd.DataFrame, criterio: str):
    """Barras horizontales: % de hogares con al menos una carencia
    estructural, según un criterio cualquiera (nivel económico,
    departamento). Horizontales para que se lean sin inclinar la cabeza
    cuando el criterio es departamento (19 categorías, algunas con
    nombres largos — Cleveland & McGill, 1984).
    """
    columna_y = resumen.columns[0]
    fig = px.bar(
        resumen, y=columna_y, x="pct_precariedad", orientation="h",
        title=f"Precariedad estructural de la vivienda según {criterio}", text="pct_precariedad",
        color_discrete_sequence=["#d1495b"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        yaxis_title="", xaxis_title="% de hogares con carencia",
        yaxis={"categoryorder": "total ascending"},
        width=850, height=550, title_x=0.5, showlegend=False,
    )
    return fig


def plot_carencias_estructurales_mas_frecuentes(resumen: pd.DataFrame):
    """Barras horizontales ordenadas: % de hogares con cada carencia
    estructural puntual, de mayor a menor prevalencia.
    """
    fig = px.bar(
        resumen, y="carencia", x="pct_hogares", orientation="h",
        title="Carencias estructurales más frecuentes", text="pct_hogares",
        color_discrete_sequence=["#8d6ab8"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        yaxis_title="", xaxis_title="% de hogares",
        yaxis={"categoryorder": "total ascending"},
        width=850, height=500, title_x=0.5, showlegend=False,
    )
    return fig


# ============================================================================
# Hogares (composición, sin tecnología) y Brecha Digital (con marco
# internacional) — ver la nota de fuentes en config.py.
# ============================================================================

def plot_pct_pobres_indigentes(resultado: dict):
    """Barras horizontales: % de hogares pobres y % en indigencia."""
    data = {"Condición": ["Pobres", "Indigentes"], "Porcentaje": [resultado["pct_pobres"], resultado["pct_indigentes"]]}
    fig = px.bar(
        data, y="Condición", x="Porcentaje", orientation="h",
        title="Hogares en situación de pobreza e indigencia",
        width=800, height=350, color_discrete_sequence=["#d1495b"],
    )
    fig.update_traces(width=0.5, text=data["Porcentaje"], textposition="auto")
    fig.update_layout(xaxis_title="% de hogares", yaxis_title="", title_x=0.5)
    return fig


def plot_tasa_jefatura_femenina(resultado: dict):
    """Barras horizontales: % de hogares con jefe hombre vs. jefa mujer."""
    pct_mujer = resultado["pct_jefatura_femenina"]
    data = {"Jefatura": ["Jefe hombre", "Jefa mujer"], "Porcentaje": [round(100 - pct_mujer, 2), pct_mujer]}
    fig = px.bar(
        data, y="Jefatura", x="Porcentaje", orientation="h",
        title="Jefatura de hogar por sexo",
        width=800, height=350, color_discrete_sequence=["#5a7fa6"],
    )
    fig.update_traces(width=0.5, text=data["Porcentaje"], textposition="auto")
    fig.update_layout(xaxis_title="% de hogares", yaxis_title="", title_x=0.5)
    return fig


def plot_tipos_hogar(resumen: pd.DataFrame):
    """Barras horizontales: % de hogares de cada tipo (taxonomía CELADE), de mayor a menor."""
    fig = px.bar(
        resumen, x="pct_hogares", y="tipo_hogar", orientation="h",
        title="Tipos de hogar", text="pct_hogares",
        color_discrete_sequence=["#66a182"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        xaxis_title="% de hogares", yaxis_title="", yaxis={"categoryorder": "total ascending"},
        width=800, height=450, title_x=0.5, showlegend=False,
    )
    return fig


def plot_hacinamiento_por(resumen: pd.DataFrame, criterio: str):
    """Barras: % de hogares en situación de hacinamiento, según un criterio cualquiera."""
    columna_x = resumen.columns[0]
    fig = px.bar(
        resumen, x=columna_x, y="pct_hacinamiento",
        title=f"Hacinamiento según {criterio}", text="pct_hacinamiento",
        color_discrete_sequence=["#d1495b"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        xaxis_title=criterio.capitalize(), yaxis_title="% de hogares hacinados",
        yaxis_range=[0, max(resumen["pct_hacinamiento"].max() * 1.3, 5)],
        width=800, height=500, title_x=0.5, showlegend=False,
    )
    return fig


def plot_razon_dependencia_por(resumen: pd.DataFrame, criterio: str):
    """Barras horizontales: razón de dependencia demográfica, según un
    criterio cualquiera (en la práctica, siempre departamento — 19
    categorías, algunas con nombres largos como "TREINTA Y TRES"). Barras
    horizontales, no verticales, por el mismo motivo que
    `plot_condiciones_vivienda`: se leen sin inclinar la cabeza (Cleveland
    & McGill, 1984).
    """
    columna_y = resumen.columns[0]
    fig = px.bar(
        resumen, y=columna_y, x="razon_dependencia", orientation="h",
        title=f"Razón de dependencia demográfica según {criterio}", text="razon_dependencia",
        color_discrete_sequence=["#5a7fa6"],
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        yaxis_title="", xaxis_title="Razón de dependencia (%)",
        yaxis={"categoryorder": "total ascending"},
        width=850, height=550, title_x=0.5, showlegend=False,
    )
    return fig


def plot_indice_desarrollo_territorial(resultado: pd.DataFrame):
    """Barras horizontales ordenadas: ranking del índice sintético de
    desarrollo territorial por departamento (ver
    analysis.indice_desarrollo_territorial).
    """
    df_plot = resultado.reset_index().rename(columns={resultado.index.name or "index": "departamento"})
    fig = px.bar(
        df_plot, y="departamento", x="indice", orientation="h",
        title="Índice de desarrollo territorial por departamento", text="indice",
        color_discrete_sequence=["#5a7fa6"],
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        yaxis_title="", xaxis_title="Índice (0 a 1, más alto = mejor)",
        yaxis={"categoryorder": "total ascending"},
        xaxis_range=[0, 1.1],
        width=850, height=550, title_x=0.5, showlegend=False,
    )
    return fig


def plot_perfil_territorial(resultado: pd.DataFrame):
    """Heatmap: perfil normalizado (0-1) de cada dimensión del índice de
    desarrollo territorial, por departamento — el detalle que explica por
    qué un departamento queda arriba o abajo en el ranking (ver
    plot_indice_desarrollo_territorial), no solo el promedio final.
    """
    columnas_dimensiones = [c for c in resultado.columns if c != "indice"]
    tabla = resultado[columnas_dimensiones].sort_values(columnas_dimensiones[0])
    fig, ax = plt.subplots(figsize=(7, 8))
    sns.heatmap(tabla, annot=True, fmt=".2f", cmap="viridis", cbar_kws={"label": "0 a 1 (más alto = mejor)"}, ax=ax)
    ax.set_title("Perfil territorial por departamento", fontsize=13)
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    return fig


def plot_pct_unipersonales_mayores(resultado: dict):
    """Barras horizontales: de los hogares unipersonales, % con jefe/a de 65+ vs. menor."""
    pct_mayores = resultado["pct_unipersonales_mayores"]
    data = {
        "Edad del integrante": ["65 años o más", "Menos de 65"],
        "Porcentaje": [pct_mayores, round(100 - pct_mayores, 2)],
    }
    fig = px.bar(
        data, y="Edad del integrante", x="Porcentaje", orientation="h",
        title="Hogares unipersonales según edad de su integrante",
        width=800, height=350, color_discrete_sequence=["#8d6ab8"],
    )
    fig.update_traces(width=0.5, text=data["Porcentaje"], textposition="auto")
    fig.update_layout(xaxis_title="% de hogares unipersonales", yaxis_title="", title_x=0.5)
    return fig


def plot_brecha_digital_por_cohorte(brecha_df: pd.DataFrame):
    """Barras agrupadas: penetración de cada tecnología por cohorte generacional del jefe/a de hogar."""
    fig = px.bar(
        brecha_df, x="cohorte", y="pct_penetracion", color="tecnologia",
        barmode="group", title="Brecha digital por cohorte generacional",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(
        xaxis_title="Cohorte generacional (según edad del jefe/a de hogar)", yaxis_title="Penetración (%)",
        legend_title="Tecnología", width=950, height=500, title_x=0.5,
    )
    return fig


def plot_brecha_digital_por_jefatura(brecha_df: pd.DataFrame):
    """Barras agrupadas: penetración de cada tecnología según el sexo del jefe/a de hogar."""
    fig = px.bar(
        brecha_df, x="jefe_sexo", y="pct_penetracion", color="tecnologia",
        barmode="group", title="Brecha digital según sexo del jefe/a de hogar",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(
        xaxis_title="Sexo del jefe/a de hogar", yaxis_title="Penetración (%)",
        legend_title="Tecnología", width=800, height=500, title_x=0.5,
    )
    return fig


def plot_calidad_conexion_por(tabla_pct: pd.DataFrame, criterio: str):
    """Barras 100% apiladas: calidad de conexión (sin conexión / solo móvil
    / banda ancha fija) según un criterio cualquiera (ej. nivel económico).
    """
    return _plot_barras_100_apiladas(
        tabla_pct,
        titulo=f"Calidad de la conexión a internet según {criterio}",
        xlabel=criterio.capitalize(),
    )


def plot_composicion_categorica(tabla_pct: pd.DataFrame, titulo: str, xlabel: str):
    """Barras 100% apiladas, genérica: para cualquier composición categórica
    ponderada (ver `analysis.composicion_categorica_ponderada_por`) que no
    tenga ya un wrapper específico como `plot_calidad_conexion_por` (ej.
    situación ocupacional por sector formal/informal).
    """
    return _plot_barras_100_apiladas(tabla_pct, titulo=titulo, xlabel=xlabel)


def plot_indice_acceso_digital_por(resumen: pd.DataFrame, criterio: str):
    """Barras: promedio del índice de acceso digital (0 a 4), según un criterio cualquiera."""
    columna_x = resumen.columns[0]
    fig = px.bar(
        resumen, x=columna_x, y="indice_promedio",
        title=f"Índice de acceso digital según {criterio}", text="indice_promedio",
        color_discrete_sequence=["#66a182"],
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        xaxis_title=criterio.capitalize(), yaxis_title="Índice promedio (0 a 4)",
        yaxis_range=[0, 4.5],
        width=800, height=500, title_x=0.5, showlegend=False,
    )
    return fig


def plot_adopcion_tablet_ibirapita(resumen: pd.DataFrame, criterio: str):
    """Barras: % de hogares con tablet del Plan Ibirapitá, según un criterio cualquiera."""
    columna_x = resumen.columns[0]
    fig = px.bar(
        resumen, x=columna_x, y="pct_con_tablet",
        title="Adopción de tablets del Plan Ibirapitá", text="pct_con_tablet",
        color_discrete_sequence=["#8d6ab8"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        xaxis_title=criterio.capitalize(), yaxis_title="% de hogares con tablet",
        yaxis_range=[0, max(resumen["pct_con_tablet"].max() * 1.3, 5)],
        width=800, height=500, title_x=0.5, showlegend=False,
    )
    return fig


def plot_prevalencia_inseguridad_alimentaria(prevalencia: dict):
    """Barras simples: % de hogares (ponderado) en inseguridad alimentaria
    moderada-o-severa y severa, a nivel nacional."""
    categorias = ["Moderada o severa", "Severa"]
    valores = [prevalencia["moderada_o_severa"], prevalencia["severa"]]
    fig = px.bar(
        x=categorias, y=valores,
        title="Prevalencia de inseguridad alimentaria en los hogares",
        color=categorias,
        color_discrete_map={"Moderada o severa": "#eeb95c", "Severa": "#d1495b"},
        text=[f"{v:.1f}%" for v in valores],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="", yaxis_title="% de hogares (ponderado)",
        showlegend=False, width=650, height=500, title_x=0.5,
    )
    return fig


def plot_inseguridad_alimentaria_por(resumen: pd.DataFrame, columna_grupo: str, titulo: str, xlabel: str):
    """Barras simples: % de hogares en inseguridad alimentaria (ponderado), por grupo."""
    fig = px.bar(
        resumen, x=columna_grupo, y="pct_inseguridad",
        title=titulo,
        color=columna_grupo,
        color_discrete_sequence=px.colors.qualitative.Safe,
        text=[f"{v:.1f}%" for v in resumen["pct_inseguridad"]],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title=xlabel, yaxis_title="% de hogares en inseguridad alimentaria (ponderado)",
        showlegend=False, width=650, height=500, title_x=0.5,
    )
    return fig


def plot_tasas_actividad_empleo_desempleo(tasas: dict):
    """Barras simples: tasas de actividad, empleo y desempleo a nivel nacional."""
    etiquetas = {"tasa_actividad": "Actividad", "tasa_empleo": "Empleo", "tasa_desempleo": "Desempleo"}
    categorias = [etiquetas[k] for k in ["tasa_actividad", "tasa_empleo", "tasa_desempleo"]]
    valores = [tasas["tasa_actividad"], tasas["tasa_empleo"], tasas["tasa_desempleo"]]
    fig = px.bar(
        x=categorias, y=valores,
        title="Tasas de actividad, empleo y desempleo (promedio de los 12 meses)",
        color=categorias,
        color_discrete_sequence=px.colors.qualitative.Safe,
        text=[f"{v:.1f}%" for v in valores],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="", yaxis_title="% (ponderado, promedio mensual)",
        showlegend=False, width=650, height=500, title_x=0.5,
    )
    return fig


def plot_tasas_por_grupo(resumen: pd.DataFrame, columna_grupo: str, titulo: str):
    """Barras agrupadas: tasas de actividad, empleo y desempleo comparando
    grupos (sexo, edad) — para la brecha de género y el desempleo juvenil."""
    df_plot = resumen.melt(
        id_vars=columna_grupo, value_vars=["tasa_actividad", "tasa_empleo", "tasa_desempleo"],
        var_name="tasa", value_name="valor",
    )
    etiquetas = {"tasa_actividad": "Actividad", "tasa_empleo": "Empleo", "tasa_desempleo": "Desempleo"}
    df_plot["tasa"] = df_plot["tasa"].map(etiquetas)
    fig = px.bar(
        df_plot, x="tasa", y="valor", color=columna_grupo, barmode="group",
        title=titulo,
        color_discrete_sequence=px.colors.qualitative.Safe,
        text=[f"{v:.1f}%" for v in df_plot["valor"]],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="", yaxis_title="% (ponderado, promedio mensual)",
        width=700, height=500, title_x=0.5, legend_title="",
    )
    return fig


def plot_tasas_por_anio(tabla: pd.DataFrame):
    """Líneas con marcadores: evolución de las tasas de actividad, empleo y
    desempleo entre años no necesariamente consecutivos (ver
    `analysis.tasas_actividad_empleo_desempleo_por_anio`).

    El eje x usa los años en su escala numérica real, no una categoría
    pareja — Plotly ya hace esto solo si `tabla["anio"]` llega como `int`
    (que es como lo entrega esa función): la distancia visual entre 2019 y
    2024 queda 5 veces más ancha que entre 2024 y 2025, en vez de verse
    igual de "cerca" como pasaría con un eje categórico. Fundamento: mismo
    principio de precisión perceptiva de posición en una escala común de
    Cleveland & McGill (1984) que respalda el resto de los gráficos de
    este proyecto — acá aplicado al eje temporal, no solo al de categorías.
    Los marcadores explícitos en cada punto son a propósito: la línea entre
    ellos no representa datos interpolados, solo conecta visualmente años
    con encuesta propia.
    """
    df_plot = tabla.melt(
        id_vars="anio", value_vars=["tasa_actividad", "tasa_empleo", "tasa_desempleo"],
        var_name="tasa", value_name="valor",
    )
    etiquetas = {"tasa_actividad": "Actividad", "tasa_empleo": "Empleo", "tasa_desempleo": "Desempleo"}
    df_plot["tasa"] = df_plot["tasa"].map(etiquetas)
    fig = px.line(
        df_plot, x="anio", y="valor", color="tasa", markers=True,
        title="Tasas de actividad, empleo y desempleo por año",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_traces(marker=dict(size=10))
    fig.update_xaxes(type="linear", tickmode="array", tickvals=sorted(tabla["anio"].unique()))
    fig.update_layout(
        xaxis_title="Año", yaxis_title="% (ponderado, promedio mensual)",
        legend_title="", width=800, height=500, title_x=0.5,
    )
    return fig


def plot_tasa_mensual_promedio_por(resumen: pd.DataFrame, columna_grupo: str, titulo: str):
    """Barras horizontales: % ponderado (promedio mensual) por grupo —
    informalidad, subempleo, desempleo, lo que corresponda según el
    título. Horizontales para leerse sin inclinar la cabeza cuando el
    grupo es departamento (19 categorías, algunas con nombres largos —
    Cleveland & McGill, 1984); no perjudica los casos con pocas
    categorías (sexo, nivel educativo), que se leen igual de bien así.
    """
    fig = px.bar(
        resumen, y=columna_grupo, x="pct_promedio", orientation="h",
        title=titulo,
        color=columna_grupo,
        color_discrete_sequence=px.colors.qualitative.Safe,
        text=[f"{v:.1f}%" for v in resumen["pct_promedio"]],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_title="", xaxis_title="% (ponderado, promedio mensual)",
        yaxis={"categoryorder": "total ascending"},
        # Margen a la derecha de la barra más larga para que su etiqueta de
        # porcentaje no quede cortada por el borde del gráfico (mismo motivo
        # que plot_pct_por) — encontrado en una corrida real: sin este
        # margen, "Tasa de desempleo por departamento" (Treinta y Tres,
        # 14.9%, la barra más larga) recortaba el "%" final.
        xaxis_range=[0, resumen["pct_promedio"].max() * 1.15],
        showlegend=False, width=750, height=500, title_x=0.5,
    )
    return fig


def plot_pct_por(resumen: pd.DataFrame, columna_grupo: str, titulo: str, xlabel: str, columna_valor: str = "pct"):
    """Barras simples: % ponderado por grupo — genérica para prevalencia de
    victimización, tasas de comunicación/denuncia/violencia por tipo de
    delito, o cualquier corte similar sin promedio mensual."""
    fig = px.bar(
        resumen, x=columna_grupo, y=columna_valor,
        title=titulo,
        color=columna_grupo,
        color_discrete_sequence=px.colors.qualitative.Safe,
        text=[f"{v:.1f}%" for v in resumen[columna_valor]],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title=xlabel, yaxis_title="% (ponderado)",
        showlegend=False, width=700, height=500, title_x=0.5,
        # Un poco de margen arriba de la barra más alta, para que la
        # etiqueta de porcentaje no quede cortada por el borde del gráfico
        # cuando el valor está cerca del máximo (ej. 86%).
        yaxis_range=[0, resumen[columna_valor].max() * 1.15],
    )
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
        # Mismo motivo que en plot_penetracion_por_barrio: un scatter no
        # arranca en cero solo, hay que fijarlo a mano.
        xaxis_range=[0, df_plot["pct_cable"].max() * 1.1],
        showlegend=False, width=800, height=550, title_x=0.5,
    )
    promedio = df_plot["pct_cable"].mean()
    fig.add_vline(x=promedio, line_dash="dash", line_color="gray")
    fig.add_annotation(x=promedio, y=1.04, yref="paper", text=f"Promedio nacional: {promedio:.1f}%",
                        showarrow=False, font=dict(color="gray"))
    return fig
