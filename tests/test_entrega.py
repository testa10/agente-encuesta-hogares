from encuesta_hogares import entrega


def test_respaldar_si_existe_devuelve_none_si_no_hay_archivo(tmp_path):
    ruta = tmp_path / "Informe_ECH_2024.pdf"
    assert entrega.respaldar_si_existe(ruta) is None


def test_respaldar_si_existe_renombra_el_archivo_previo(tmp_path):
    ruta = tmp_path / "Informe_ECH_2024.pdf"
    ruta.write_bytes(b"version vieja")

    respaldo = entrega.respaldar_si_existe(ruta)

    assert respaldo == tmp_path / "Informe_ECH_2024 (anterior).pdf"
    assert respaldo.read_bytes() == b"version vieja"
    assert not ruta.exists()


def test_respaldar_si_existe_no_acumula_mas_de_una_version_anterior(tmp_path):
    ruta = tmp_path / "Informe_ECH_2024.pdf"
    ruta.write_bytes(b"version 1")
    entrega.respaldar_si_existe(ruta)

    ruta.write_bytes(b"version 2")
    respaldo = entrega.respaldar_si_existe(ruta)

    assert respaldo.read_bytes() == b"version 2"
    assert list(tmp_path.iterdir()) == [respaldo]


def test_respaldar_si_existe_acepta_ruta_como_string(tmp_path):
    ruta = tmp_path / "Informe_ECH_2024.html"
    ruta.write_text("contenido")

    respaldo = entrega.respaldar_si_existe(str(ruta))

    assert respaldo == tmp_path / "Informe_ECH_2024 (anterior).html"
