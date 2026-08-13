"""Uso: python tools/verificar_sincronizacion.py

Herramienta para quien mantiene el proyecto — no es parte del flujo del
agente encuesta-hogares ni de nada que corra un usuario final.

El agente encuesta-hogares no tiene permiso de usar git (ver
.claude/settings.json). Eso significa que si escribe código nuevo y
reutilizable durante una corrida real (ej. una función nueva en
analysis.py para una métrica propuesta por el usuario), ese código queda
en el disco pero sin commitear ni subir a GitHub, hasta que alguien lo
note. Pasó de verdad en una sesión real: una función completa con su
test quedó así casi dos días antes de que una auditoría manual la
encontrara (en ese momento el proyecto todavía vivía en dos copias
separadas — ya no; esta herramienta sigue siendo útil igual, porque el
problema de fondo, el agente sin permiso de git, no cambió).

Este script automatiza esa auditoría en vez de depender de que alguien
se acuerde de hacerla a mano: compara el árbol de trabajo actual (tal
cual está en disco, incluyendo archivos sin trackear) contra
`origin/main`, sin modificar ni commitear nada.
"""

import subprocess
import sys


def _run(comando: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        comando, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def main() -> int:
    fetch = _run("git fetch origin")
    if fetch.returncode != 0:
        print("No se pudo hacer git fetch — ¿esta carpeta es un repo git con remoto 'origin'?")
        print(fetch.stderr)
        return 2

    _run("git add -A")
    try:
        diff = _run("git diff --cached origin/main --stat")
        salida = "\n".join(
            linea for linea in diff.stdout.splitlines() if not linea.startswith("warning:")
        ).strip()
    finally:
        # Deja todo exactamente como estaba - nunca commitea nada.
        _run("git reset")

    if not salida:
        print("OK: esta copia coincide exactamente con origin/main.")
        print("Nada para publicar ni para traer.")
        return 0

    print("DIFERENCIAS encontradas contra origin/main:\n")
    print(salida)
    print(
        "\nSi son cambios reales que nunca se publicaron (ej. una función "
        "que el agente agregó en una corrida), revisalos y publicalos con "
        "git commit + git push.\n"
        "Si en cambio es solo atraso (esta copia no tiene los últimos "
        "cambios ya publicados), poné esta copia al día sin tocar ningún "
        "archivo con:\n"
        "  git fetch origin && git reset --soft origin/main"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
