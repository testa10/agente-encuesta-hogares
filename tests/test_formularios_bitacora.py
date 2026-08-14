"""Que la bitácora guarde lo que la persona respondió de verdad, no solo
que respondió algo.

Nace de un caso real: el informe final trajo un bloque que la persona no
pidió (FIES) y le faltó otro que sí había marcado (Vivienda), y no había
forma de confirmar si fue un error al tildar o una lectura equivocada de
la respuesta más adelante en el flujo, porque la bitácora solo registraba
"formulario_respondido" sin el contenido. Este test hace un POST real
contra el servidor que levanta mostrar_formulario()/mostrar_finalizacion()
(no una llamada directa a bitacora.registrar) para probar el camino
completo tal cual lo recorre un navegador de verdad.
"""

import json
import threading
import time
import urllib.request

from encuesta_hogares import bitacora, formularios


def _responder(url: str, payload: dict) -> None:
    datos = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=datos, headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=5).read()


def test_mostrar_formulario_guarda_la_respuesta_real_en_la_bitacora(monkeypatch):
    capturados = []
    monkeypatch.setattr(bitacora, "registrar", lambda tipo, **detalle: capturados.append((tipo, detalle)))

    urls = []
    monkeypatch.setattr(formularios.subprocess, "run", lambda cmd, check=False: urls.append(cmd[-1]))

    salida = {}

    def correr():
        salida["respuesta"] = formularios.mostrar_formulario("<html><title>Test</title></html>", timeout=5)

    hilo = threading.Thread(target=correr)
    hilo.start()
    for _ in range(50):
        if urls:
            break
        time.sleep(0.05)
    assert urls, "el formulario nunca llegó a abrir el navegador (falso)"

    _responder(urls[0], {"anio": 2025, "areas": ["hogares", "vivienda"]})
    hilo.join(timeout=5)

    assert salida["respuesta"] == {"anio": 2025, "areas": ["hogares", "vivienda"]}
    eventos = {tipo: detalle for tipo, detalle in capturados}
    assert eventos["formulario_respondido"]["respuesta"] == {"anio": 2025, "areas": ["hogares", "vivienda"]}


def test_mostrar_finalizacion_guarda_la_respuesta_real_en_la_bitacora(monkeypatch):
    capturados = []
    urls = []
    monkeypatch.setattr(bitacora, "registrar", lambda tipo, **detalle: capturados.append((tipo, detalle)))
    monkeypatch.setattr(formularios.subprocess, "run", lambda cmd, check=False: urls.append(cmd[-1]))

    salida = {}

    def correr():
        salida["respuesta"] = formularios.mostrar_finalizacion(timeout=5)

    hilo = threading.Thread(target=correr)
    hilo.start()
    for _ in range(50):
        if urls:
            break
        time.sleep(0.05)
    assert urls, "la pantalla de finalización nunca llegó a abrir el navegador (falso)"

    _responder(urls[0], {"accion": "nuevo_informe"})
    hilo.join(timeout=5)

    assert salida["respuesta"] == {"accion": "nuevo_informe"}
    eventos = {tipo: detalle for tipo, detalle in capturados}
    assert eventos["finalizacion_respondida"]["respuesta"] == {"accion": "nuevo_informe"}
