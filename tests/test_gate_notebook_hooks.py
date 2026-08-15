"""Prueba los tres hooks que gatean sobre `jupyter nbconvert --execute`
(gate-notebook-sin-duplicados.cjs, gate-notebook-metrica-sin-grafica-o-cita.cjs,
gate-notebook-graficas-faltantes.cjs) invocándolos de verdad con Node (pipe
de stdin, igual que lo hace Claude Code) — no una reimplementación en
Python de su lógica. Mismo enfoque que test_gate_primer_paso.py y
test_gate_no_git_indirecto.py.

Nace de un bug real encontrado replicando el patrón que documenta
docs/FLUJO_DE_TRABAJO.md (pasos 5 y 8): `nbconvert --execute` nunca se
invoca suelto por Bash, siempre envuelto en un archivo `.py` con
`bitacora.medir_comando(...)` y corrido con `run_python.bat archivo.py`
(el mismo patrón "Write + run_python.bat" cuyo bug ya arregló
gate-primer-paso.cjs). Los tres hooks buscaban "nbconvert"/"--execute" y
la ruta del notebook solo en el texto CRUDO del comando Bash — con el
patrón real, ese texto es apenas `run_python.bat archivo.py`, así que
ninguno de los tres se disparaba nunca. La detección ahora vive en
.claude/hooks/_lib_notebook_ejecutado.cjs, compartida por los tres, que
también busca dentro de cualquier archivo `.py` que el comando referencie.
"""

import json
import subprocess
from pathlib import Path

import pytest

_HOOKS = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
_NODE_DISPONIBLE = subprocess.run(["node", "--version"], capture_output=True).returncode == 0

_NOTEBOOK_CON_DUPLICADO = {
    "cells": [
        {"cell_type": "code", "source": ["fig = viz.plot_bar(df)\n", "fig"], "outputs": [], "metadata": {}},
    ],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5,
}

_NOTEBOOK_LIMPIO = {
    "cells": [
        {
            "cell_type": "code",
            "source": ["fig2 = viz.plot_bar(df)\n", "fig2.show()"],
            "outputs": [{"output_type": "display_data", "data": {"text/plain": ["<img>"]}, "metadata": {}}],
            "metadata": {},
        },
    ],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5,
}

_NOTEBOOK_SIN_OUTPUT = {
    "cells": [
        {"cell_type": "code", "source": ["fig2 = viz.plot_bar(df)\n", "fig2.show()"], "outputs": [], "metadata": {}},
    ],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5,
}


def _correr_hook(hook_nombre: str, comando: str, cwd: Path) -> dict | None:
    """Corre el hook de verdad con Node, con cwd = carpeta del notebook
    (así resuelve igual que en una sesión real, donde el cwd del proceso
    del hook es la raíz del proyecto y las rutas del comando son relativas
    a ella)."""
    entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}})
    resultado = subprocess.run(
        ["node", str(_HOOKS / hook_nombre)], input=entrada, capture_output=True, text=True, cwd=str(cwd)
    )
    salida = resultado.stdout.strip()
    return json.loads(salida) if salida else None


def _escribir_notebook(tmp_path: Path, nombre: str, contenido: dict) -> None:
    (tmp_path / nombre).write_text(json.dumps(contenido), encoding="utf-8")


def _escribir_script_ejecutor(tmp_path: Path, nombre_script: str, nombre_notebook: str) -> str:
    """Reproduce el patrón real de FLUJO_DE_TRABAJO.md paso 5: nbconvert
    envuelto en bitacora.medir_comando(), en un archivo .py, nunca suelto
    por Bash. Devuelve el comando Bash tal como lo correría la sesión real
    (`run_python.bat archivo.py`)."""
    script = tmp_path / nombre_script
    script.write_text(
        "import sys\n"
        "from encuesta_hogares import bitacora\n"
        "bitacora.medir_comando('ejecucion_notebook', [\n"
        "    sys.executable, '-m', 'jupyter', 'nbconvert',\n"
        "    '--to', 'notebook', '--execute', '--inplace',\n"
        f"    {nombre_notebook!r},\n"
        "])\n",
        encoding="utf-8",
    )
    return f'run_python.bat "{nombre_script}"'


@pytest.mark.skipif(not _NODE_DISPONIBLE, reason="node no está disponible en esta máquina")
class TestDeteccionDeNbconvertOcultoEnPy:
    """El bug: los tres hooks ignoraban nbconvert cuando vivía dentro de un
    .py referenciado por el comando Bash, en vez de en el texto del comando."""

    def test_sin_duplicados_bloquea_via_write_y_run_python_bat(self, tmp_path):
        _escribir_notebook(tmp_path, "nb.ipynb", _NOTEBOOK_CON_DUPLICADO)
        comando = _escribir_script_ejecutor(tmp_path, "ejecutar.py", "nb.ipynb")
        resultado = _correr_hook("gate-notebook-sin-duplicados.cjs", comando, tmp_path)
        assert resultado is not None
        assert resultado["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_sin_duplicados_permite_notebook_limpio_via_write_y_run_python_bat(self, tmp_path):
        _escribir_notebook(tmp_path, "nb.ipynb", _NOTEBOOK_LIMPIO)
        comando = _escribir_script_ejecutor(tmp_path, "ejecutar.py", "nb.ipynb")
        assert _correr_hook("gate-notebook-sin-duplicados.cjs", comando, tmp_path) is None

    def test_graficas_faltantes_bloquea_celda_sin_output_via_write_y_run_python_bat(self, tmp_path):
        _escribir_notebook(tmp_path, "nb.ipynb", _NOTEBOOK_SIN_OUTPUT)
        comando = _escribir_script_ejecutor(tmp_path, "ejecutar.py", "nb.ipynb")
        resultado = _correr_hook("gate-notebook-graficas-faltantes.cjs", comando, tmp_path)
        assert resultado is not None
        assert resultado["decision"] == "block"

    def test_graficas_faltantes_permite_notebook_con_output_via_write_y_run_python_bat(self, tmp_path):
        _escribir_notebook(tmp_path, "nb.ipynb", _NOTEBOOK_LIMPIO)
        comando = _escribir_script_ejecutor(tmp_path, "ejecutar.py", "nb.ipynb")
        assert _correr_hook("gate-notebook-graficas-faltantes.cjs", comando, tmp_path) is None

    def test_metrica_sin_grafica_o_cita_no_revienta_via_write_y_run_python_bat(self, tmp_path):
        # Este notebook de prueba no tiene celdas "#### Métrica N", así que
        # no hay ninguna métrica que revisar - lo que importa acá es que
        # detecte el nbconvert oculto en el .py y no reviente ni bloquee a
        # ciegas por falta de encabezados de métrica.
        _escribir_notebook(tmp_path, "nb.ipynb", _NOTEBOOK_LIMPIO)
        comando = _escribir_script_ejecutor(tmp_path, "ejecutar.py", "nb.ipynb")
        assert _correr_hook("gate-notebook-metrica-sin-grafica-o-cita.cjs", comando, tmp_path) is None

    def test_ningun_hook_se_dispara_sin_mencion_a_nbconvert(self, tmp_path):
        for hook in (
            "gate-notebook-sin-duplicados.cjs",
            "gate-notebook-metrica-sin-grafica-o-cita.cjs",
            "gate-notebook-graficas-faltantes.cjs",
        ):
            assert _correr_hook(hook, "run_python.bat tools/validar_con_datos_reales.py", tmp_path) is None
