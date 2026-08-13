from encuesta_hogares import config


def test_datos_disponibles_detecta_hogares_y_fies(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2024"
    carpeta.mkdir()
    (carpeta / "ECH_2024.csv").write_text("ID\n1\n")
    (carpeta / "base_FIES_2024.csv").write_text("ID\n1\n")

    assert config.datos_disponibles(2024) == {"hogares": True, "fies": True, "empleo": False, "seguridad": False}


def test_datos_disponibles_sin_fies():
    carpeta_vacia = config.DATA_DIR / "0000"
    assert not carpeta_vacia.exists()
    assert config.datos_disponibles(0) == {"hogares": False, "fies": False, "empleo": False, "seguridad": False}


def test_datos_disponibles_detecta_seguridad(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2024"
    carpeta.mkdir()
    (carpeta / "ECH_VICTIMIZACION_S2_2024.csv").write_text("ID\n1\n")
    assert config.datos_disponibles(2024)["seguridad"] is True


def test_victimizacion_file_resuelve_por_anio(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2024"
    carpeta.mkdir()
    archivo = carpeta / "ECH_VICTIMIZACION_S2_2024.csv"
    archivo.write_text("ID\n1\n")
    assert config.victimizacion_file(2024) == archivo


def test_datos_disponibles_hogares_via_sav(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2019"
    carpeta.mkdir()
    (carpeta / "H_2019_Terceros.sav").write_bytes(b"")

    disponibles = config.datos_disponibles(2019)
    assert disponibles["hogares"] is True
    assert disponibles["fies"] is False


def test_fies_file_resuelve_por_anio(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2024"
    carpeta.mkdir()
    archivo = carpeta / "base_FIES_2024.csv"
    archivo.write_text("ID\n1\n")

    assert config.fies_file(2024) == archivo


def test_fies_file_sin_archivo_devuelve_ruta_esperada_igual(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    ruta = config.fies_file(2030)
    assert ruta.name == "base_FIES_2030.csv"
    assert not ruta.exists()


def test_empleo_files_devuelve_los_12_meses_en_orden(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    archivos = config.empleo_files(2024)
    assert len(archivos) == 12
    assert archivos[0].name == "ECH_01_24.csv"
    assert archivos[11].name == "ECH_12_24.csv"


def test_meses_labels_cubre_los_12_meses_sin_huecos():
    assert set(config.MESES_LABELS) == set(range(1, 13))
    assert config.MESES_LABELS[1] == "Enero"
    assert config.MESES_LABELS[12] == "Diciembre"


def test_hogares_csv_file_resuelve_por_anio(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2024"
    carpeta.mkdir()
    archivo = carpeta / "ECH_2024.csv"
    archivo.write_text("ID\n1\n")

    assert config.hogares_csv_file(2024) == archivo


def test_hogares_csv_file_sin_archivo_devuelve_ruta_esperada_igual(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    ruta = config.hogares_csv_file(2030)
    assert ruta.name == "ECH_2030.csv"
    assert not ruta.exists()


def test_datos_disponibles_empleo_requiere_los_12_meses_completos(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2024"
    carpeta.mkdir()
    for mes in range(1, 12):  # 11 de 12, a proposito
        (carpeta / f"ECH_{mes:02d}_24.csv").write_text("ID\n1\n")
    assert config.datos_disponibles(2024)["empleo"] is False

    (carpeta / "ECH_12_24.csv").write_text("ID\n1\n")
    assert config.datos_disponibles(2024)["empleo"] is True
