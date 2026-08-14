"""Valida que el JavaScript embebido en cada plantilla_* de formularios.py
sea sintácticamente válido de verdad.

`ruff` (regla W605) ya atrapa un error real que pasó en esta sesión — un
`\\s` sin escapar en un string de Python que después terminaba adentro de
un <script> — pero eso es una propiedad del *string de Python*, no del
*JavaScript* que contiene. Nada verificaba que el HTML generado tuviera
JS realmente parseable (llaves sin cerrar, coma de más, etc.) hasta este
archivo. Usa Node (ya es una dependencia del proyecto vía los hooks de
.claude/hooks) con `--check`, que solo valida sintaxis sin ejecutar nada.
"""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from encuesta_hogares import formularios

_NODE_DISPONIBLE = subprocess.run(["node", "--version"], capture_output=True).returncode == 0

_LLAMADAS = {
    "plantilla_finalizacion": lambda: formularios.plantilla_finalizacion(True, True),
    "plantilla_arranque": lambda: formularios.plantilla_arranque(),
    "plantilla_bienvenida": lambda: formularios.plantilla_bienvenida("2024"),
    "plantilla_datos": lambda: formularios.plantilla_datos("2024", "https://ejemplo.uy"),
    "plantilla_areas": lambda: formularios.plantilla_areas(True, True, True),
    "plantilla_catalogo": lambda: formularios.plantilla_catalogo(
        incluir_brecha_digital=True, incluir_hogares=True, incluir_territorio=True,
        incluir_vivienda=True, incluir_fies=True, incluir_empleo=True, incluir_seguridad=True,
    ),
    "plantilla_revision": lambda: formularios.plantilla_revision("prop", "problema", "alternativa"),
}


def _extraer_scripts(html: str) -> list[str]:
    return re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)


@pytest.mark.skipif(not _NODE_DISPONIBLE, reason="node no está disponible en esta máquina")
@pytest.mark.parametrize("nombre", sorted(_LLAMADAS))
def test_javascript_embebido_es_sintacticamente_valido(nombre):
    html = _LLAMADAS[nombre]()
    scripts = _extraer_scripts(html)
    assert scripts, f"{nombre} no tiene ningún bloque <script> — revisar el extractor si esto es inesperado"

    for i, js in enumerate(scripts):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
            ruta = f.name
        try:
            resultado = subprocess.run(["node", "--check", ruta], capture_output=True, text=True)
            assert resultado.returncode == 0, (
                f"{nombre}, bloque <script> #{i}: JavaScript inválido según Node:\n{resultado.stderr}"
            )
        finally:
            Path(ruta).unlink(missing_ok=True)
