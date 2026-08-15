"""El servidor local de formularios solo acepta respuestas de su propia
página, no de cualquier sitio abierto en el navegador.

Nace de una revisión de seguridad de este proyecto: `do_POST` aceptaba
cualquier POST sin mirar de dónde venía, y encima respondía con
`Access-Control-Allow-Origin: *`. El servidor escucha en 127.0.0.1 con un
puerto al azar, pero eso solo no alcanza — cualquier página web abierta
en el navegador de la persona puede barrer los puertos de localhost desde
JavaScript (el rango efímero es chico, son segundos) y responder el
formulario en su nombre: elegir el año, marcar métricas, o directamente
cerrarle el flujo con `salir_del_flujo`.

Los tests levantan el servidor de verdad y le mandan pedidos HTTP reales,
en vez de llamar a las funciones internas de validación — así se prueba
el comportamiento que de verdad ve un navegador.
"""

import json
import threading
import urllib.error
import urllib.request

import pytest

from encuesta_hogares import bitacora, formularios


@pytest.fixture
def servidor(monkeypatch, tmp_path):
    """Levanta un formulario de verdad en un hilo y devuelve su URL.

    `subprocess.run` (lo que abre el navegador) se reemplaza por un no-op:
    no queremos que se abra una pestaña real en la máquina de quien corra
    los tests. La bitácora va a un archivo temporal para no ensuciar la
    real (mismo motivo que en test_formularios_timeout.py).
    """
    monkeypatch.setattr(bitacora, "LOG_PATH", tmp_path / "bitacora.jsonl")

    urls: list[str] = []

    def capturar_url_en_vez_de_abrir_el_navegador(cmd, *a, **k):
        urls.append(cmd[-1])

    monkeypatch.setattr(formularios.subprocess, "run", capturar_url_en_vez_de_abrir_el_navegador)

    resultado: dict = {}

    def correr():
        resultado.update(formularios.mostrar_formulario("<html><title>T</title></html>", timeout=120))

    # timeout=120 y no 10: los tests contestan al instante, pero con la
    # suite completa corriendo en paralelo el hilo puede tardar en llegar
    # a responder y un timeout corto hacía fallar el test de forma
    # intermitente (el formulario se daba por vencido antes del POST).
    hilo = threading.Thread(target=correr, daemon=True)
    hilo.start()
    for _ in range(200):
        if urls:
            break
        threading.Event().wait(0.05)
    assert urls, "el formulario nunca llegó a levantar el servidor"
    yield urls[0], resultado, hilo


def _postear(url: str, cuerpo: dict, origen: str | None = None, content_length: str | None = None):
    datos = json.dumps(cuerpo).encode("utf-8")
    cabeceras = {"Content-Type": "application/json"}
    if origen is not None:
        cabeceras["Origin"] = origen
    if content_length is not None:
        cabeceras["Content-Length"] = content_length
    pedido = urllib.request.Request(url, data=datos, headers=cabeceras)
    return urllib.request.urlopen(pedido, timeout=5)


def test_rechaza_una_respuesta_que_viene_de_otro_sitio(servidor):
    url, resultado, hilo = servidor

    with pytest.raises(urllib.error.HTTPError) as error:
        _postear(url, {"anio": "1999"}, origen="http://sitio-malicioso.example")

    assert error.value.code == 403
    assert resultado == {}, "una página ajena no puede contestar el formulario por la persona"

    # El formulario sigue esperando: el rechazo no lo dio por respondido.
    _postear(url, {"anio": "2024"}, origen=url.rstrip("/"))
    hilo.join(timeout=5)
    assert resultado["anio"] == "2024"


def test_acepta_la_respuesta_de_su_propia_pagina(servidor):
    url, resultado, hilo = servidor
    respuesta = _postear(url, {"anio": "2024"}, origen=url.rstrip("/"))
    assert respuesta.status == 200
    hilo.join(timeout=5)
    assert resultado["anio"] == "2024"


def test_acepta_un_cliente_sin_cabecera_Origin(servidor):
    # Un cliente que no es un navegador (los propios tests, por ejemplo)
    # no manda Origin. El riesgo que se cierra es el de una página de otro
    # sitio, que siempre la manda.
    url, resultado, hilo = servidor
    respuesta = _postear(url, {"anio": "2024"})
    assert respuesta.status == 200
    hilo.join(timeout=5)
    assert resultado["anio"] == "2024"


def test_un_content_length_invalido_no_tira_el_servidor(servidor):
    # Antes, un Content-Length que no fuera un número tiraba un ValueError
    # sin manejar dentro del hilo del servidor.
    url, resultado, hilo = servidor

    with pytest.raises(urllib.error.HTTPError) as error:
        _postear(url, {"anio": "1999"}, content_length="no-es-un-numero")
    assert error.value.code == 400
    assert resultado == {}

    # Y el formulario sigue vivo y usable.
    _postear(url, {"anio": "2024"})
    hilo.join(timeout=5)
    assert resultado["anio"] == "2024"
