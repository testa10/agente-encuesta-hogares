"""Prueba el hook .claude/hooks/gate-primer-paso.cjs invocándolo de verdad
con Node (pipe de stdin, igual que lo hace Claude Code) — no una
reimplementación en Python de su lógica, que podría divergir del archivo
real sin que nadie lo note.

Nace de un bug real encontrado en una corrida real (no en pruebas
sintéticas): la primera versión de este hook buscaba la subcadena
"plantilla_bienvenida" en el TEXTO CRUDO del comando Bash. El patrón real
que usa el agente (paso 5.2 y en general, "usá siempre Write, nunca un
heredoc de Bash") es escribir el código a un archivo `.py` temporal y
correrlo con `run_python.bat archivo.py` — ahí "plantilla_bienvenida" vive
adentro del archivo, no en el texto del comando, así que la búsqueda nunca
coincidía y la llamada que de verdad mostraba el formulario de bienvenida
quedaba denegada para siempre: un bucle sin salida que bloqueaba el flujo
completo desde el primer paso, para cualquier usuario real.
"""

import json
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest

_HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "gate-primer-paso.cjs"
_NODE_DISPONIBLE = subprocess.run(["node", "--version"], capture_output=True).returncode == 0


def _correr_hook(session_id: str, tool_name: str, tool_input: dict) -> dict | None:
    """Corre el hook de verdad con Node. None si lo permitió (salida
    vacía); el dict de la respuesta si lo denegó."""
    entrada = json.dumps({"session_id": session_id, "tool_name": tool_name, "tool_input": tool_input})
    resultado = subprocess.run(
        ["node", str(_HOOK)], input=entrada, capture_output=True, text=True
    )
    salida = resultado.stdout.strip()
    return json.loads(salida) if salida else None


def _limpiar_marker(session_id: str) -> None:
    marker = Path(tempfile.gettempdir()) / f"encuesta-hogares-bienvenida-{session_id}.marker"
    marker.unlink(missing_ok=True)


@pytest.mark.skipif(not _NODE_DISPONIBLE, reason="node no está disponible en esta máquina")
class TestGatePrimerPaso:
    def setup_method(self):
        self.session_id = f"pytest-{uuid.uuid4()}"

    def teardown_method(self):
        _limpiar_marker(self.session_id)

    def test_permite_leer_los_tres_documentos_indicados_antes_del_paso_1(self):
        for doc in ("METODOLOGIA.md", "FLUJO_DE_TRABAJO.md", "CONVENCIONES_DE_GRAFICAS.md"):
            resultado = _correr_hook(self.session_id, "Read", {"file_path": f"C:/proyecto/docs/{doc}"})
            assert resultado is None, f"debería permitir leer {doc} antes del paso 1"

    def test_bloquea_leer_un_archivo_de_codigo_antes_del_paso_1(self):
        resultado = _correr_hook(self.session_id, "Read", {"file_path": "C:/proyecto/src/analysis.py"})
        assert resultado is not None
        assert resultado["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_permite_bash_con_plantilla_bienvenida_literal_en_el_comando(self):
        resultado = _correr_hook(
            self.session_id, "Bash", {"command": 'run_python.bat -c "formularios.plantilla_bienvenida()"'}
        )
        assert resultado is None

    def test_permite_bash_que_corre_un_archivo_py_con_plantilla_bienvenida_adentro(self, tmp_path):
        # Caso real que causó el bug: el código vive en un archivo aparte,
        # no en el texto del comando.
        archivo = tmp_path / "formulario.py"
        archivo.write_text(
            "from encuesta_hogares import formularios\n"
            "html = formularios.plantilla_bienvenida()\n",
            encoding="utf-8",
        )
        resultado = _correr_hook(self.session_id, "Bash", {"command": f'./run_python.bat "{archivo}"'})
        assert resultado is None, "el patrón real (Write + run_python.bat archivo.py) tiene que quedar permitido"

    def test_despues_de_mostrar_la_bienvenida_ya_se_puede_leer_cualquier_cosa(self, tmp_path):
        archivo = tmp_path / "formulario.py"
        archivo.write_text("formularios.plantilla_bienvenida()\n", encoding="utf-8")
        primero = _correr_hook(self.session_id, "Bash", {"command": f'./run_python.bat "{archivo}"'})
        assert primero is None

        segundo = _correr_hook(self.session_id, "Read", {"file_path": "C:/proyecto/src/analysis.py"})
        assert segundo is None, "una vez mostrada la bienvenida, el resto de herramientas ya no debería bloquearse"
