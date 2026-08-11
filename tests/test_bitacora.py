from encuesta_hogares import bitacora


def test_registrar_escribe_una_linea_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(bitacora, "LOG_PATH", tmp_path / "logs" / "bitacora.jsonl")

    bitacora.registrar("formulario_mostrado", nombre="Bienvenida")

    eventos = bitacora.leer_eventos()
    assert len(eventos) == 1
    assert eventos[0]["tipo"] == "formulario_mostrado"
    assert eventos[0]["nombre"] == "Bienvenida"
    assert "timestamp" in eventos[0]


def test_registrar_nunca_lanza_excepcion_si_no_puede_escribir(tmp_path, monkeypatch):
    # Un archivo (no una carpeta) en el lugar del padre hace que mkdir falle.
    bloqueador = tmp_path / "logs"
    bloqueador.write_text("no soy una carpeta")
    monkeypatch.setattr(bitacora, "LOG_PATH", bloqueador / "bitacora.jsonl")

    bitacora.registrar("formulario_mostrado", nombre="x")  # no debe lanzar


def test_leer_eventos_ignora_lineas_corruptas(tmp_path, monkeypatch):
    log = tmp_path / "bitacora.jsonl"
    log.write_text('{"tipo": "a", "timestamp": "2026-01-01T00:00:00+00:00"}\n' "esto no es json\n")
    monkeypatch.setattr(bitacora, "LOG_PATH", log)

    eventos = bitacora.leer_eventos()

    assert len(eventos) == 1
    assert eventos[0]["tipo"] == "a"


def test_leer_eventos_devuelve_vacio_si_no_existe_el_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(bitacora, "LOG_PATH", tmp_path / "no_existe.jsonl")
    assert bitacora.leer_eventos() == []


def test_agrupar_en_sesiones_separa_por_gap_de_tiempo():
    eventos = [
        {"tipo": "formulario_mostrado", "timestamp": "2026-01-01T09:00:00+00:00"},
        {"tipo": "formulario_respondido", "timestamp": "2026-01-01T09:05:00+00:00"},
        # gap de 5 horas -> sesión nueva
        {"tipo": "formulario_mostrado", "timestamp": "2026-01-01T14:10:00+00:00"},
    ]

    sesiones = bitacora.agrupar_en_sesiones(eventos, gap_horas=2.0)

    assert len(sesiones) == 2
    assert len(sesiones[0]) == 2
    assert len(sesiones[1]) == 1


def test_resumir_sesion_cuenta_formularios_timeouts_y_errores():
    eventos = [
        {"tipo": "formulario_mostrado", "timestamp": "2026-01-01T09:00:00+00:00", "nombre": "Bienvenida"},
        {"tipo": "formulario_respondido", "timestamp": "2026-01-01T09:01:00+00:00", "nombre": "Bienvenida"},
        {"tipo": "formulario_mostrado", "timestamp": "2026-01-01T09:02:00+00:00", "nombre": "Catálogo"},
        {"tipo": "formulario_timeout", "timestamp": "2026-01-01T09:32:00+00:00", "nombre": "Catálogo"},
        {"tipo": "formulario_error", "timestamp": "2026-01-01T09:33:00+00:00", "mensaje": "boom"},
    ]

    r = bitacora.resumir_sesion(eventos)

    assert r.formularios_mostrados == 2
    assert r.timeouts == 1
    assert len(r.errores) == 1
    assert r.errores[0]["mensaje"] == "boom"
    assert r.inicio == eventos[0]["timestamp"]
    assert r.fin == eventos[-1]["timestamp"]
