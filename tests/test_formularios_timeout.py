"""Qué devuelve mostrar_formulario()/mostrar_finalizacion() cuando nadie
responde dentro del timeout (la persona cierra la pestaña, se va, etc.).

Nace de una revisión real de este proyecto: antes de este archivo, ese
caso devolvía `{}` — un diccionario vacío que el chequeo estándar
`respuesta.get("salir_del_flujo")` no distingue de "no pidió salir", así
que el siguiente acceso a un campo esperado (`respuesta["anio"]`, por
ejemplo) tiraba un `KeyError` sin manejar. Se prueba acá con un timeout
muy corto (no los 30 minutos reales) y sin abrir un navegador de verdad
(se reemplaza `subprocess.run` por un no-op). También se redirige la
bitácora a un archivo temporal: sin esto, cada corrida de la suite
completa escribía entradas falsas ("formulario_timeout") en la bitácora
real de quien esté usando el proyecto en esa misma carpeta.
"""

from encuesta_hogares import bitacora, formularios


def test_mostrar_formulario_devuelve_salir_del_flujo_si_nadie_responde(monkeypatch, tmp_path):
    monkeypatch.setattr(formularios.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(bitacora, "LOG_PATH", tmp_path / "bitacora.jsonl")
    respuesta = formularios.mostrar_formulario("<html><title>Test</title></html>", timeout=0.05)
    assert respuesta.get("salir_del_flujo") is True


def test_mostrar_finalizacion_devuelve_terminar_si_nadie_responde(monkeypatch, tmp_path):
    monkeypatch.setattr(formularios.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(bitacora, "LOG_PATH", tmp_path / "bitacora.jsonl")
    respuesta = formularios.mostrar_finalizacion(timeout=0.05)
    assert respuesta.get("accion") == "terminar"
