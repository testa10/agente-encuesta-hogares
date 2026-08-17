"""Que la configuración de `.claude/settings.json` y los hooks que
referencia existan de verdad y estén conectados.

Nace del hallazgo de la v0.13.0: un hook puede correr durante meses sin
mirar nada (buscaba un formato de encabezado que ya no se emitía) y nadie
lo nota, porque "no bloquea nada" y "está roto" se ven idénticos desde
afuera. Estos tests no pueden verificar que cada hook mire lo correcto —
eso lo hacen sus propios tests (`test_gate_*.py`) — pero sí cierran la
capa de abajo: que cada hook referenciado exista y compile, que ningún
guardián haya quedado escrito pero sin conectar, y que las reglas de
permisos que protegen a los propios guardianes sigan presentes.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parents[1]
_SETTINGS = _RAIZ / ".claude" / "settings.json"
_HOOKS_DIR = _RAIZ / ".claude" / "hooks"

_NODE_DISPONIBLE = shutil.which("node") is not None


def _configuracion() -> dict:
    return json.loads(_SETTINGS.read_text(encoding="utf-8"))


def _hooks_referenciados() -> set[str]:
    """Nombres de archivo .cjs que settings.json manda a ejecutar."""
    nombres = set()
    for evento in _configuracion().get("hooks", {}).values():
        for grupo in evento:
            for hook in grupo.get("hooks", []):
                comando = hook.get("command", "")
                for parte in comando.split("/"):
                    if parte.rstrip('"').endswith(".cjs"):
                        nombres.add(parte.rstrip('"'))
    return nombres


def test_todo_hook_referenciado_existe():
    faltantes = [n for n in _hooks_referenciados() if not (_HOOKS_DIR / n).exists()]
    assert not faltantes, (
        f"settings.json referencia hooks que no existen: {faltantes}. "
        f"Si Claude Code no encuentra el archivo, el guardián desaparece "
        f"en silencio — la sesión sigue con una advertencia que nadie lee."
    )


@pytest.mark.skipif(not _NODE_DISPONIBLE, reason="node no está disponible en esta máquina")
def test_todo_hook_referenciado_compila():
    rotos = []
    for nombre in sorted(_hooks_referenciados()):
        resultado = subprocess.run(
            ["node", "--check", str(_HOOKS_DIR / nombre)], capture_output=True, text=True
        )
        if resultado.returncode != 0:
            rotos.append(f"{nombre}: {resultado.stderr.strip()[:200]}")
    assert not rotos, "hooks que no compilan:\n" + "\n".join(rotos)


def test_ningun_guardian_quedo_escrito_pero_sin_conectar():
    """Un gate-*.cjs que existe en la carpeta pero que settings.json no
    referencia es un guardián que alguien escribió, probó, y nunca
    conectó — protege exactamente nada. Los _lib_*.cjs son bibliotecas
    compartidas, no hooks, y quedan afuera a propósito."""
    en_disco = {p.name for p in _HOOKS_DIR.glob("gate-*.cjs")}
    sin_conectar = sorted(en_disco - _hooks_referenciados())
    assert not sin_conectar, f"guardianes escritos pero no conectados en settings.json: {sin_conectar}"


def test_los_guardianes_estan_protegidos_de_edicion():
    """Las reglas deny que impiden que el agente edite sus propios
    guardianes (hooks, permisos, instrucciones) y los .bat del lanzador.

    `run_python.bat` en particular: es el ancla de la regla de permisos
    más amplia del proyecto (`Bash(run_python.bat *)`), así que
    reescribirlo equivaldría a ejecutar cualquier cosa bajo un permiso ya
    aprobado. Ver CLAUDE.md, "Qué es y qué no es la lista de permisos" —
    incluida la parte honesta: esto cierra las herramientas Edit/Write,
    no es una frontera de seguridad completa.
    """
    deny = set(_configuracion()["permissions"]["deny"])
    requeridas = {
        "Edit(.claude/**)",
        "Write(.claude/**)",
        "Edit(run_python.bat)",
        "Write(run_python.bat)",
        "Edit(abrir_agente.bat)",
        "Write(abrir_agente.bat)",
        "Edit(instalar.bat)",
        "Write(instalar.bat)",
        "Bash(git *)",
        "Bash(*git *)",
    }
    faltantes = sorted(requeridas - deny)
    assert not faltantes, f"reglas deny que protegen a los guardianes y faltan: {faltantes}"
