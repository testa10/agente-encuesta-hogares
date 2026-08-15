"""Cierre de la consola de Claude Code al terminar el flujo
(`src/encuesta_hogares/cierre.py` y sus dos usos en `formularios.py`).

Nace del único problema que quedaba bloqueando la puesta en producción:
ni terminar el informe ni salir antes cerraban la ventana de consola que
abre `abrir_agente.bat`, porque una sesión interactiva de Claude Code no
termina nunca por sí sola. Lo que se prueba acá es la lógica de CUÁNDO se
cierra, no el cierre en sí (que mata un proceso real del sistema
operativo): en los tests nunca se llega a ejecutar PowerShell, se
reemplaza `subprocess.run` por un espía.

El caso más importante es el último: "crear un nuevo informe" NO tiene
que cerrar nada — ahí el agente reinicia desde el paso 1 en la misma
conversación, y cerrar la consola dejaría a la persona sin agente justo
después de pedir otro informe.
"""

import pytest

from encuesta_hogares import bitacora, cierre, formularios


@pytest.fixture
def espia_cierre(monkeypatch, tmp_path):
    """Deja `cierre.cerrar_consola` operativo pero inofensivo: registra
    las llamadas a PowerShell en vez de ejecutarlas, y manda la marca y la
    bitácora a archivos temporales."""
    llamadas = []
    monkeypatch.setattr(cierre.subprocess, "run", lambda *a, **k: llamadas.append(a))
    monkeypatch.setattr(cierre.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(bitacora, "LOG_PATH", tmp_path / "bitacora.jsonl")
    return llamadas


@pytest.fixture
def lanzado_por_el_bat(monkeypatch):
    """Simula las variables de entorno que define `abrir_agente.bat`."""
    monkeypatch.setenv(cierre.VAR_ACTIVA, "1")
    monkeypatch.setenv(cierre.VAR_PID_CONSOLA, "4242")


class TestCuandoCierra:
    def test_no_hace_nada_sin_las_variables_del_bat(self, espia_cierre, monkeypatch):
        # Caso real que esto protege: la suite de tests, un `claude`
        # abierto a mano por el dueño del proyecto, o un notebook suelto -
        # ninguno debería cerrarse solo.
        monkeypatch.delenv(cierre.VAR_ACTIVA, raising=False)
        monkeypatch.delenv(cierre.VAR_PID_CONSOLA, raising=False)

        assert cierre.cerrar_consola(motivo="test") is False
        assert espia_cierre == []

    def test_no_hace_nada_si_el_pid_no_es_un_numero(self, espia_cierre, monkeypatch):
        monkeypatch.setenv(cierre.VAR_ACTIVA, "1")
        monkeypatch.setenv(cierre.VAR_PID_CONSOLA, "no-es-un-pid")

        assert cierre.cerrar_consola(motivo="test") is False
        assert espia_cierre == []

    def test_cierra_y_deja_la_marca_cuando_lo_pidio_el_bat(self, espia_cierre, lanzado_por_el_bat):
        assert cierre.cerrar_consola(motivo="terminar") is True
        assert len(espia_cierre) == 1

        marca = cierre.marca_de_cierre(4242)
        assert marca.exists(), "sin la marca, abrir_agente.bat muestra un error al final de una corrida exitosa"
        assert marca.read_text(encoding="utf-8") == "terminar"


@pytest.fixture
def motivos_de_cierre(monkeypatch):
    """Espía sobre `cierre.cerrar_consola` — devuelve la lista de motivos
    con los que se lo llamó.

    Se espía la función y no `subprocess.run` a propósito: `formularios` y
    `cierre` importan el MISMO objeto módulo `subprocess`, así que
    parchear `formularios.subprocess.run` (para no abrir un navegador de
    verdad) pisaría también el espía de `cierre.subprocess.run` y los
    tests medirían siempre cero. Acá lo que importa es CUÁNDO se pide el
    cierre; el cierre en sí ya se prueba en TestCuandoCierra.
    """
    motivos = []

    def espia(motivo: str) -> bool:
        motivos.append(motivo)
        return True

    monkeypatch.setattr(formularios.cierre, "cerrar_consola", espia)
    return motivos


class TestDesdeLosFormularios:
    """Los dos puntos donde el flujo termina de verdad, y los que no."""

    def test_finalizacion_con_terminar_cierra_la_consola(self, monkeypatch, motivos_de_cierre):
        resultado = _finalizacion_simulada(monkeypatch, {"accion": "terminar"})
        assert resultado["accion"] == "terminar"
        assert motivos_de_cierre == ["terminar"], "terminar el informe tiene que cerrar la consola"

    def test_finalizacion_con_nuevo_informe_NO_cierra_la_consola(self, monkeypatch, motivos_de_cierre):
        # El caso que no se puede romper: la persona pidió otro informe y
        # el agente sigue en la misma conversación desde el paso 1 -
        # cerrar acá la dejaría sin agente justo después de pedirlo.
        resultado = _finalizacion_simulada(monkeypatch, {"accion": "nuevo_informe"})
        assert resultado["accion"] == "nuevo_informe"
        assert motivos_de_cierre == [], "crear un nuevo informe nunca debe cerrar la consola"

    def test_salir_sin_terminar_cierra_la_consola(self, monkeypatch, motivos_de_cierre):
        resultado = _formulario_simulado(monkeypatch, {"salir_del_flujo": True})
        assert resultado["salir_del_flujo"] is True
        assert motivos_de_cierre == ["salir_del_flujo"]

    def test_una_respuesta_normal_no_cierra_nada(self, monkeypatch, motivos_de_cierre):
        resultado = _formulario_simulado(monkeypatch, {"anio": "2024"})
        assert resultado == {"anio": "2024"}
        assert motivos_de_cierre == [], "contestar un paso intermedio no puede cerrar la consola"

    def test_timeout_de_formulario_cierra_la_consola(self, monkeypatch, motivos_de_cierre):
        # Nadie contestó dentro del timeout: la persona se fue, no tiene
        # sentido dejarle la consola abierta.
        monkeypatch.setattr(formularios.subprocess, "run", lambda *a, **k: None)
        respuesta = formularios.mostrar_formulario("<html><title>T</title></html>", timeout=0.05)
        assert respuesta.get("salir_del_flujo") is True
        assert motivos_de_cierre == ["timeout_formulario"]

    def test_timeout_de_finalizacion_cierra_la_consola(self, monkeypatch, motivos_de_cierre):
        monkeypatch.setattr(formularios.subprocess, "run", lambda *a, **k: None)
        respuesta = formularios.mostrar_finalizacion(timeout=0.05)
        assert respuesta.get("accion") == "terminar"
        assert motivos_de_cierre == ["timeout_finalizacion"]


def _responder_en_cuanto_arranque(monkeypatch, respuesta: dict):
    """Hace que el formulario reciba `respuesta` apenas se abre el
    "navegador", sin servidor ni browser de verdad: `subprocess.run` es lo
    que el código usa para abrir la pestaña, así que sirve de gatillo."""
    import json
    import urllib.request

    def abrir(cmd, *a, **k):
        url = cmd[-1]
        datos = json.dumps(respuesta).encode("utf-8")
        pedido = urllib.request.Request(url, data=datos, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(pedido, timeout=5).read()

    monkeypatch.setattr(formularios.subprocess, "run", abrir)


def _formulario_simulado(monkeypatch, respuesta: dict) -> dict:
    _responder_en_cuanto_arranque(monkeypatch, respuesta)
    return formularios.mostrar_formulario("<html><title>T</title></html>", timeout=10)


def _finalizacion_simulada(monkeypatch, respuesta: dict) -> dict:
    _responder_en_cuanto_arranque(monkeypatch, respuesta)
    return formularios.mostrar_finalizacion(timeout=10)
