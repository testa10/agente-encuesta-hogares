"""¿El informe está diciendo un disparate?

Nace de una preocupación concreta del dueño del proyecto: que un número
del informe no pueda diferir de la realidad sin que nadie lo note. **La
idea NO es reproducir los cálculos del INE** —nuestra metodología puede
diferir legítimamente de la suya— sino analizar con rigor estadístico y
que un error grueso no llegue nunca a un informe entregado.

Los tests de la suite verifican que un porcentaje esté entre 0 y 100. Eso
deja pasar casi cualquier error real: una tasa de desempleo de 45%, una
pobreza de 0,14% (proporción confundida con porcentaje), o una tasa de
empleo mayor que la de actividad — todos son "porcentajes válidos" y
todos son imposibles.

Este módulo tiene dos capas, y la primera es la más fuerte:

1. **Coherencia interna** (`incoherencias`): identidades que se cumplen
   SIEMPRE, por definición, sin importar el país ni el año. Si una falla,
   hay un bug seguro — no una diferencia metodológica. No dependen de
   ninguna cifra externa.

2. **Plausibilidad** (`fuera_de_rango`): rangos anchos a propósito, para
   atrapar disparates sin marcar variación legítima. No son objetivos a
   cumplir ni cifras del INE a replicar: son los límites de lo que un
   indicador puede valer en Uruguay sin que algo esté roto.

Los rangos se anclan en magnitudes que publica el propio INE (ver
`_FUENTES`), ensanchadas con margen amplio. La regla de diseño es que un
falso positivo acá es peor que el problema: trabaría un informe correcto.
Ante la duda, el rango se ensancha.
"""

from __future__ import annotations

from dataclasses import dataclass

# Anclas oficiales, para que los rangos de abajo no sean una opinión.
# Consultadas en el portal del INE (gub.uy/instituto-nacional-estadistica,
# sección Actividad, Empleo y Desempleo): tasa de actividad en torno a
# 63,9-64,4%, tasa de empleo en torno a 59,5%, tasa de desempleo entre 7,0
# y 7,6%. Informalidad: 22,8% publicado por el INE para 2025 (ver
# CHANGELOG 0.5.x, donde se comparó contra el 21,94% que calcula este
# proyecto desde f82 — diferencia chica y explicable, no un error).
_FUENTES = (
    "INE Uruguay — Actividad, Empleo y Desempleo (ECH), "
    "https://www.gub.uy/instituto-nacional-estadistica/tematica/actividad-empleo-desempleo"
)


@dataclass
class Hallazgo:
    indicador: str
    valor: float
    motivo: str

    def __str__(self) -> str:
        return f"{self.indicador} = {self.valor}: {self.motivo}"


# indicador -> (minimo, maximo, por que ese rango)
#
# Los limites son deliberadamente anchos: incluyen la crisis de 2002
# (desempleo ~17%, pobreza ~40%) por arriba y escenarios mucho mejores que
# el actual por abajo. Lo que tienen que atrapar es un error de calculo,
# no una variacion economica.
RANGOS: dict[str, tuple[float, float, str]] = {
    "tasa_actividad": (45.0, 80.0, "el INE la publica en torno al 64%; fuera de 45-80 hay un error de cálculo, no un cambio del mercado laboral"),
    "tasa_empleo": (35.0, 75.0, "el INE la publica en torno al 59,5%"),
    "tasa_desempleo": (1.0, 30.0, "el INE la publica entre 7% y 8%; ni siquiera la crisis de 2002 (~17%) se acerca a 30"),
    "pct_pobres": (1.0, 50.0, "en torno al 10-15% en los últimos años; el pico de 2002 rondó el 40%"),
    "pct_indigentes": (0.0, 15.0, "históricamente por debajo del 5%"),
    "pct_informalidad": (5.0, 50.0, "el INE publicó 22,8% para 2025"),
    "pct_inseguridad_alimentaria": (0.5, 50.0, "en torno al 12-14% en los años medidos"),
    "pct_hacinamiento": (0.0, 40.0, "afecta a una minoría de los hogares"),
    "pct_con_internet": (20.0, 100.0, "en torno al 89% en Montevideo en 2025"),
}


def fuera_de_rango(indicador: str, valor: float | None) -> Hallazgo | None:
    """¿Este valor es un disparate? None si está bien, o si el indicador no
    tiene rango definido (no se inventa uno: mejor no opinar que opinar mal).
    """
    if valor is None or indicador not in RANGOS:
        return None
    minimo, maximo, razon = RANGOS[indicador]
    if minimo <= valor <= maximo:
        return None
    return Hallazgo(
        indicador=indicador,
        valor=round(float(valor), 4),
        motivo=f"esperado entre {minimo} y {maximo} — {razon}. Fuente de referencia: {_FUENTES}",
    )


def incoherencias(cifras: dict[str, float]) -> list[Hallazgo]:
    """Identidades que se cumplen siempre, por definición. Una violación
    acá es un bug seguro, no una diferencia metodológica.

    `cifras` es un dict con los nombres de RANGOS (los que falten se
    ignoran: cada bloque del informe aporta los suyos).
    """
    hallazgos: list[Hallazgo] = []

    actividad = cifras.get("tasa_actividad")
    empleo = cifras.get("tasa_empleo")
    desempleo = cifras.get("tasa_desempleo")

    if actividad is not None and empleo is not None and empleo > actividad + 0.01:
        hallazgos.append(Hallazgo(
            "tasa_empleo", round(empleo, 4),
            f"no puede superar a la tasa de actividad ({round(actividad, 2)}): "
            "los ocupados son un subconjunto de los activos",
        ))

    # Identidad: desempleo = (activos - ocupados) / activos * 100. Se
    # tolera medio punto por el redondeo de promediar 12 meses por separado.
    if actividad and empleo is not None and desempleo is not None:
        esperado = (actividad - empleo) / actividad * 100
        if abs(esperado - desempleo) > 0.5:
            hallazgos.append(Hallazgo(
                "tasa_desempleo", round(desempleo, 4),
                f"no cierra con actividad ({round(actividad, 2)}) y empleo ({round(empleo, 2)}), "
                f"que implican {round(esperado, 2)} — revisar el denominador",
            ))

    pobres = cifras.get("pct_pobres")
    indigentes = cifras.get("pct_indigentes")
    if pobres is not None and indigentes is not None and indigentes > pobres + 0.01:
        hallazgos.append(Hallazgo(
            "pct_indigentes", round(indigentes, 4),
            f"no puede superar a la pobreza ({round(pobres, 2)}): la indigencia es un subconjunto",
        ))

    severa = cifras.get("pct_inseguridad_severa")
    moderada_o_severa = cifras.get("pct_inseguridad_alimentaria")
    if severa is not None and moderada_o_severa is not None and severa > moderada_o_severa + 0.01:
        hallazgos.append(Hallazgo(
            "pct_inseguridad_severa", round(severa, 4),
            f"no puede superar a la inseguridad moderada o severa ({round(moderada_o_severa, 2)})",
        ))

    return hallazgos


def revisar(cifras: dict[str, float]) -> list[Hallazgo]:
    """Las dos capas juntas: primero las identidades (bug seguro), después
    los rangos (probable disparate)."""
    hallazgos = incoherencias(cifras)
    for indicador, valor in cifras.items():
        hallazgo = fuera_de_rango(indicador, valor)
        if hallazgo is not None:
            hallazgos.append(hallazgo)
    return hallazgos
