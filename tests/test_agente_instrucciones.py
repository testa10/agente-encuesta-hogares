"""Chequeos estructurales sobre .claude/agents/encuesta-hogares.md.

No valida contenido (eso lo hace un humano leyéndolo) - valida que la
estructura no se rompa por una edición futura, como pasó una vez: el paso
3.5 quedó físicamente después del paso 4 en el archivo, aunque el texto
decía "antes del paso 4". Un test no puede evitar una mala instrucción,
pero sí puede evitar que el orden de los pasos quede contradictorio.
"""

import re
from pathlib import Path

AGENTE_MD = Path(__file__).resolve().parents[1] / ".claude" / "agents" / "encuesta-hogares.md"


def _pasos_en_orden_de_aparicion() -> list[float]:
    texto = AGENTE_MD.read_text(encoding="utf-8")
    numeros = re.findall(r"^### (\d+(?:\.\d+)?)\. ", texto, flags=re.MULTILINE)
    return [float(n) for n in numeros]


def test_el_archivo_del_agente_existe():
    assert AGENTE_MD.exists(), f"No se encontró {AGENTE_MD}"


def test_los_pasos_aparecen_en_orden_numerico_ascendente():
    pasos = _pasos_en_orden_de_aparicion()
    assert pasos, "No se encontró ningún paso con el patrón '### N. ...' en el archivo"
    assert pasos == sorted(pasos), (
        f"Los pasos no están en orden ascendente en el archivo: {pasos}. "
        "Esto es exactamente el bug que hizo que una corrida real se saltara "
        "el formulario de áreas y se fuera a explorar código - revisá el "
        "orden físico de las secciones '### N. Título', no solo el texto."
    )


def test_el_paso_de_bienvenida_es_el_primero():
    pasos = _pasos_en_orden_de_aparicion()
    assert pasos[0] == 1.0, (
        "El paso 1 (bienvenida) tiene que ser la primera sección numerada "
        "del archivo - es la regla innegociable de todo el flujo."
    )


def test_la_curacion_del_catalogo_tiene_compuerta_previa():
    texto = AGENTE_MD.read_text(encoding="utf-8")
    seccion = texto.split("## Curación del catálogo")[-1]
    assert "Compuerta previa" in seccion, (
        "La sección de curación del catálogo perdió su compuerta de "
        "calidad (punto 0: confirmación explícita del dueño del proyecto "
        "sobre revisión metodológica, validación con datos reales y "
        "archivos a tocar, antes de escribir nada permanente). No basta "
        "con el pedido de 'agregá esta métrica' - eso autoriza la "
        "intención, la compuerta es la revisión técnica antes de "
        "ejecutar."
    )


def test_el_nombre_del_notebook_esta_atado_al_anio_sin_variantes():
    texto = AGENTE_MD.read_text(encoding="utf-8")
    assert "notebooks/Informe_ECH_{año}.ipynb" in texto, (
        "La regla de que el notebook se llama siempre "
        "'notebooks/Informe_ECH_{año}.ipynb', sin sufijos ni variantes, "
        "desapareció del archivo. Es lo que evita que dos años choquen "
        "entre sí y que el respaldo automático (entrega.py) se dispare "
        "solo cuando de verdad se repite el mismo año."
    )


def test_la_pantalla_final_ramifica_por_nuevo_informe():
    texto = AGENTE_MD.read_text(encoding="utf-8")
    assert '"nuevo_informe"' in texto, (
        "La instrucción de ramificar según la respuesta de "
        "mostrar_finalizacion() ('terminar' vs 'nuevo_informe', volviendo "
        "al paso 1) desapareció del archivo."
    )
