"""Uso: python tools/verificar_sincronizacion.py

Herramienta para quien mantiene el proyecto (Claude Code corriendo desde
la copia de git de desarrollo) — no es parte del flujo del agente
encuesta-hogares ni de nada que corra un usuario final.

El proyecto vive en dos copias separadas a propósito: una donde se
desarrolla (con git), y la copia de Documents, que tiene que poder
funcionar sola aunque la primera no exista. El agente encuesta-hogares
corre siempre sobre la copia de Documents — nunca sobre la de
desarrollo — y no tiene permiso de usar git (ver .claude/settings.json).

Eso significa que si el agente escribe código nuevo y reutilizable
durante una corrida real (ej. una función nueva en analysis.py para una
métrica propuesta por el usuario), ese código queda solamente en el
disco de Documents, sin commitear ni subir a GitHub, hasta que alguien
lo note. Pasó de verdad en una sesión real: una función completa con su
test quedó así casi dos días antes de que una auditoría manual la
encontrara.

Este script automatiza esa auditoría en vez de depender de que alguien
se acuerde de hacerla a mano: compara el árbol de trabajo actual (tal
cual está en disco, incluyendo archivos sin trackear) contra
`origin/main`, sin modificar ni commitear nada.

Correrlo desde la raíz de CUALQUIERA de las dos copias — sirve en las
dos direcciones: encuentra tanto trabajo real sin publicar (como el caso
de arriba) como una copia que simplemente quedó atrasada.
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
        "que el agente agregó en una corrida), llevalos a la otra copia "
        "del proyecto y publicalos con git commit + git push desde ahí.\n"
        "Si en cambio es solo atraso (esta copia no tiene los últimos "
        "cambios ya publicados), poné esta copia al día sin tocar ningún "
        "archivo con:\n"
        "  git fetch origin && git reset --soft origin/main"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
