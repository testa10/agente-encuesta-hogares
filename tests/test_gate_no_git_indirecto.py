"""Prueba el hook .claude/hooks/gate-no-git-indirecto.cjs invocándolo de
verdad con Node (pipe de stdin, igual que lo hace Claude Code) — no una
reimplementación en Python de su lógica, que podría divergir del archivo
real sin que nadie lo note. Mismo enfoque que test_gate_primer_paso.py.

Nace de dos falsos positivos reales encontrados corriendo el hook a mano:
(1) un comando de varias líneas con un `git status` legítimo en la segunda
línea se bloqueaba, porque el `^` del regex de invocación directa solo
ancla al principio del string completo, no de cada línea — un salto de
línea no estaba en la lista de separadores válidos (`&&`, `;`, `|`).
(2) un nombre de archivo que simplemente contiene la palabra "git" (ej.
`git-log-notes.txt`) se bloqueaba, porque `\\bgit\\b` trata el guion como
límite de palabra igual que un espacio real.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "gate-no-git-indirecto.cjs"
_NODE_DISPONIBLE = subprocess.run(["node", "--version"], capture_output=True).returncode == 0


def _correr_hook(command: str) -> dict | None:
    """Corre el hook de verdad con Node. None si lo permitió (salida
    vacía); el dict de la respuesta si lo denegó."""
    entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    resultado = subprocess.run(["node", str(_HOOK)], input=entrada, capture_output=True, text=True)
    salida = resultado.stdout.strip()
    return json.loads(salida) if salida else None


@pytest.mark.skipif(not _NODE_DISPONIBLE, reason="node no está disponible en esta máquina")
class TestGateNoGitIndirecto:
    def test_permite_git_directo_al_principio_del_comando(self):
        assert _correr_hook("git status") is None

    def test_permite_git_directo_encadenado_con_and_and(self):
        assert _correr_hook("cd /repo && git add . && git commit -m x && git push") is None

    def test_permite_git_directo_en_la_segunda_linea_de_un_comando_multilinea(self):
        # Caso real que causó el bug: un salto de línea no estaba en la
        # lista de separadores que cuentan como "posición de comando".
        assert _correr_hook("echo hola\ngit status") is None

    def test_permite_un_nombre_de_archivo_que_contiene_la_palabra_git(self):
        # Caso real que causó el bug: \bgit\b trata el guion como límite de
        # palabra, así que "git-log-notes.txt" parecía contener la palabra
        # "git" suelta aunque no sea una invocación en absoluto.
        assert _correr_hook("cat git-log-notes.txt") is None

    def test_bloquea_git_invocado_desde_subprocess_de_python(self):
        resultado = _correr_hook("python -c \"import subprocess; subprocess.run(['git','status'])\"")
        assert resultado is not None
        assert resultado["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_bloquea_git_invocado_desde_powershell_command(self):
        resultado = _correr_hook('powershell -Command "git status"')
        assert resultado is not None
        assert resultado["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_permite_un_comando_sin_ninguna_mencion_a_git(self):
        assert _correr_hook("run_python.bat tools/validar_con_datos_reales.py") is None


# ============================================================================
# Todo hook que bloquea deja constancia en la bitácora. Nace de un hueco de
# observabilidad real: en una corrida de producción el notebook se ejecutó
# TRES veces (83s + 98s + 83s, contra los ~83s de una sola pasada). La
# explicación más probable era que los hooks de notebook hubieran bloqueado
# y forzado correcciones —justo para lo que existen—, pero no se pudo
# confirmar porque no dejaban ningún rastro. Sin saber si esos 3 minutos son
# calidad bien invertida o retrabajo evitable, no se puede decidir nada.
# ============================================================================

_HOOKS = Path(__file__).resolve().parents[1] / ".claude" / "hooks"


@pytest.mark.skipif(not _NODE_DISPONIBLE, reason="node no está disponible en esta máquina")
def test_todo_hook_que_puede_bloquear_registra_el_bloqueo():
    sin_registrar = []
    for hook in sorted(_HOOKS.glob("gate-*.cjs")):
        texto = hook.read_text(encoding="utf-8")
        puede_bloquear = '"deny"' in texto or '"block"' in texto
        if puede_bloquear and "registrar(" not in texto:
            sin_registrar.append(hook.name)
    assert not sin_registrar, (
        "Estos hooks bloquean sin dejar constancia en la bitácora, así que un "
        "bloqueo suyo es invisible al diagnosticar una corrida: "
        f"{sin_registrar} — usar `registrar()` de _lib_bitacora.cjs."
    )


@pytest.mark.skipif(not _NODE_DISPONIBLE, reason="node no está disponible en esta máquina")
def test_el_bloqueo_queda_escrito_en_la_bitacora(tmp_path):
    """Corre el hook de verdad con Node y comprueba que la línea se escriba.

    Usa ENCUESTA_HOGARES_BITACORA para que el log caiga en un archivo
    temporal: sin esa redirección, correr los hooks en los tests ensucia la
    bitácora real de quien tenga el proyecto en esa carpeta (ver
    tests/conftest.py, que la aplica a toda la suite).
    """
    log = tmp_path / "bitacora_de_prueba.jsonl"
    entrada = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "python -c \"import subprocess; subprocess.run(['git','status'])\""},
    })
    resultado = subprocess.run(
        ["node", str(_HOOK)], input=entrada, capture_output=True, text=True,
        env={**os.environ, "ENCUESTA_HOGARES_BITACORA": str(log)},
    )
    assert "deny" in resultado.stdout, "el hook tenía que bloquear este comando"

    assert log.exists(), "el hook bloqueó pero no escribió nada en la bitácora"
    evento = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert evento["tipo"] == "hook_bloqueo"
    assert evento["hook"] == "no-git-indirecto"
    assert "timestamp" in evento
