"""Cierre de la consola de Claude Code cuando el flujo termina de verdad.

Nace de un problema real, encontrado por el dueño del proyecto probando
el agente como lo usaría cualquier persona: ni terminar el informe y
apretar "Listo", ni apretar "Salir sin terminar el informe", cerraban la
ventana de consola que abre `abrir_agente.bat` — quedaba viva de fondo
indefinidamente. Para alguien sin conocimientos técnicos eso deja en
pantalla una ventana negra que no sabe qué es, si está haciendo algo, ni
si puede cerrarla.

**La causa no es un fallo intermitente, es de diseño:** `abrir_agente.bat`
invoca `claude "..."` en modo interactivo, y una sesión interactiva de
Claude Code no termina nunca por sí sola — confirmado contra la
documentación oficial de la CLI: no existe ninguna forma nativa de que
una sesión interactiva termine al final de un turno (las únicas opciones
documentadas son el modo `-p/--print`, que no es interactivo, o `/exit`
tipeado a mano). Como `claude` nunca retorna, las últimas líneas del
`.bat` no se ejecutan nunca y la ventana no se cierra jamás. Se intentó
`-p` una vez y se revirtió porque rompía el flujo (ver el historial de
`abrir_agente.bat`), así que este módulo toma el camino contrario: **no
depender de que Claude Code termine solo.**

Cuando el flujo termina de verdad, este módulo cierra el proceso de
Claude Code desde adentro. El `.bat` recupera el control en la línea
siguiente a `claude ...` y cierra su propia ventana con normalidad — no
se mata la consola de prepo, se la deja terminar como habría terminado
si `claude` hubiera retornado solo.

**Solo actúa si `abrir_agente.bat` lo pidió explícitamente** (variables
de entorno `ENCUESTA_HOGARES_CONSOLA` y `ENCUESTA_HOGARES_CONSOLA_PID`,
que solo ese archivo define, y recién después del formulario de
arranque). Sin esas variables no hace absolutamente nada: así una sesión
de `claude` abierta a mano (mantenimiento del dueño del proyecto, o el
"uso manual" que documenta el README) y la suite de tests nunca se
cierran solas por accidente.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from . import bitacora

VAR_ACTIVA = "ENCUESTA_HOGARES_CONSOLA"
VAR_PID_CONSOLA = "ENCUESTA_HOGARES_CONSOLA_PID"


def marca_de_cierre(pid_consola: int) -> Path:
    """Archivo que le avisa a `abrir_agente.bat` que el cierre lo pidió
    este proyecto, y no que Claude Code se haya roto.

    Hace falta porque terminar el proceso de Claude Code hace que `claude`
    salga con código de error: sin esta marca, el `.bat` no puede
    distinguir "el flujo terminó bien y pedimos cerrar" de "algo falló de
    verdad", y le mostraría al usuario un mensaje de error (con su
    `pause`, es decir una ventana que hay que cerrar a mano) justo al
    final de una corrida exitosa.
    """
    return Path(tempfile.gettempdir()) / f"encuesta-hogares-cierre-{pid_consola}.marker"

# Sube por la cadena de procesos padre desde este mismo proceso de Python
# hasta encontrar el que es hijo directo de la consola que abrió
# `abrir_agente.bat` — ese es el proceso de Claude Code — y lo termina.
#
# Se lo identifica por parentesco y no por nombre de ejecutable a
# propósito: según cómo se haya instalado Claude Code, el proceso puede
# llamarse "node.exe" (instalación por npm, que es la que hace
# instalar.bat) o "claude.exe" (instalador nativo), y depender de ese
# nombre haría que el cierre dejara de funcionar en cuanto alguien
# instale Claude Code de la otra forma.
#
# Se termina el proceso de Claude Code y NO el árbol entero de la consola
# (`Stop-Process -Id` a secas, sin matar descendientes): este mismo Python
# es descendiente de Claude Code, así que matar el árbol completo sería
# matarnos a nosotros mismos en medio de la operación, con el riesgo de
# que el cierre quede a mitad de camino. Terminando solo a Claude Code, el
# `.bat` sigue su curso normal, este proceso queda huérfano un instante y
# termina solo, y la ventana se cierra sin que nadie la mate.
_PLANTILLA_POWERSHELL = """
$objetivo = {pid_consola}
$actual = {pid_python}
while ($actual -ne 0) {{
  $proc = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $actual) -ErrorAction SilentlyContinue
  if (-not $proc) {{ break }}
  if ($proc.ParentProcessId -eq $objetivo) {{
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    break
  }}
  $actual = $proc.ParentProcessId
}}
"""


def cierre_pedido_por_el_lanzador() -> bool:
    """¿Fue `abrir_agente.bat` quien lanzó esta sesión, y por lo tanto hay
    una consola que cerrar cuando el flujo termine? Falso en cualquier
    otro contexto (tests, `claude` abierto a mano, notebook suelto)."""
    return os.environ.get(VAR_ACTIVA) == "1" and (os.environ.get(VAR_PID_CONSOLA) or "").strip().isdigit()


def cerrar_consola(motivo: str) -> bool:
    """Cierra la sesión de Claude Code que abrió `abrir_agente.bat`, para
    que su ventana se cierre sola. Devuelve True si se intentó el cierre.

    No hace nada (y devuelve False) si esta sesión no la lanzó
    `abrir_agente.bat` — ver el docstring del módulo. Nunca deja escapar
    una excepción: si el cierre falla, el usuario se queda con una consola
    abierta de más (el problema que ya existía), nunca con un error en
    medio de la entrega de su informe.
    """
    if not cierre_pedido_por_el_lanzador():
        return False

    pid_consola = int(os.environ[VAR_PID_CONSOLA].strip())
    script = _PLANTILLA_POWERSHELL.format(pid_consola=pid_consola, pid_python=os.getpid())
    bitacora.registrar("cierre_consola", motivo=motivo, pid_consola=pid_consola)
    try:
        # La marca se deja ANTES de terminar el proceso: después de matar a
        # Claude Code, este mismo Python queda huérfano y no hay ninguna
        # garantía de cuánto sigue vivo.
        marca_de_cierre(pid_consola).write_text(motivo, encoding="utf-8")
    except Exception:
        # Sin la marca, el .bat va a mostrar el mensaje de error al final -
        # feo, pero no vale la pena abortar el cierre por esto.
        pass
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            check=False,
            capture_output=True,
            timeout=20,
        )
    except Exception as e:  # pragma: no cover - depende del sistema operativo
        bitacora.registrar("cierre_consola_error", motivo=motivo, mensaje=str(e))
        return False
    return True
