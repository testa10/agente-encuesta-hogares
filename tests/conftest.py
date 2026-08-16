"""Configuración común de la suite.

`_bitacora_de_hooks_a_archivo_temporal` es un autouse: se aplica a TODOS
los tests sin que ninguno tenga que acordarse de pedirlo. Nace de un
problema que ya apareció dos veces en este proyecto — los tests escribiendo
en la bitácora real de quien tenga el proyecto en esa carpeta, dejando
entradas indistinguibles de una corrida suya, justo en el archivo que
existe para reconstruir qué le pasó. La primera vez fue del lado de Python
(`bitacora.LOG_PATH`); la segunda, al hacer que los hooks registraran sus
bloqueos, volvió por el lado de Node.

Que sea autouse y no un fixture opcional es a propósito: un test nuevo que
corra un hook no tiene por qué saber que existe este riesgo.
"""

import pytest


@pytest.fixture(autouse=True)
def _bitacora_de_hooks_a_archivo_temporal(tmp_path, monkeypatch):
    monkeypatch.setenv("ENCUESTA_HOGARES_BITACORA", str(tmp_path / "bitacora_hooks.jsonl"))
