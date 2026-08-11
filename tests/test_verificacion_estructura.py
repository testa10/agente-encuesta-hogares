from encuesta_hogares import config, verificacion_estructura as ve


def test_comparar_columnas_detecta_faltantes_y_no_mapeadas():
    esperadas = {"ID": "id_hogar", "nom_dpto": "departamento", "ESTRED13": "estrato_tipo"}
    presentes = {"ID", "nom_dpto", "columna_nueva_que_no_conocemos"}

    faltantes, no_mapeadas = ve.comparar_columnas(esperadas, presentes)

    assert faltantes == ["ESTRED13"]
    assert no_mapeadas == ["columna_nueva_que_no_conocemos"]


def test_comparar_columnas_ok_cuando_todo_esta_presente():
    esperadas = {"ID": "id_hogar"}
    presentes = {"ID", "otra_columna"}

    faltantes, _ = ve.comparar_columnas(esperadas, presentes)

    assert faltantes == []


def test_resultado_comparacion_ok_es_falso_si_hay_faltantes(tmp_path):
    resultado_con_falla = ve.ResultadoComparacion("x", tmp_path, 3, faltantes=["ID"])
    resultado_sin_falla = ve.ResultadoComparacion("x", tmp_path, 3, faltantes=[])

    assert resultado_con_falla.ok is False
    assert resultado_sin_falla.ok is True


def test_verificar_hogares_personas_csv_detecta_columna_faltante(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2030"
    carpeta.mkdir()
    # Simula un cambio de formato futuro: falta "ESTRED13" (uno de los
    # nombres de columna que config.HOGARES_COLUMNS_CSV espera).
    columnas_sin_estrato = [c for c in config.HOGARES_COLUMNS_CSV if c != "ESTRED13"]
    (carpeta / "ECH_2030.csv").write_text(",".join(columnas_sin_estrato) + "\n")

    resultados = ve.verificar_hogares_personas(2030)

    hogares = next(r for r in resultados if r.nombre == "Hogares (CSV combinado)")
    assert "ESTRED13" in hogares.faltantes
    assert hogares.ok is False


def test_verificar_hogares_personas_csv_ok_cuando_estan_todas(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2030"
    carpeta.mkdir()
    todas_las_columnas = set(config.HOGARES_COLUMNS_CSV) | set(config.PERSONAS_COLUMNS_CSV)
    (carpeta / "ECH_2030.csv").write_text(",".join(todas_las_columnas) + "\n")

    resultados = ve.verificar_hogares_personas(2030)

    assert all(r.ok for r in resultados)


def test_verificar_empleo_detecta_mes_con_columnas_distintas(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2030"
    carpeta.mkdir()
    columnas_normales = ",".join(config.EMPLEO_COLUMNS) + "\n"
    columnas_distintas = ",".join(c for c in config.EMPLEO_COLUMNS if c != "SECTOR_F") + "\n"

    for i, path in enumerate(config.empleo_files(2030), start=1):
        path.write_text(columnas_distintas if i == 6 else columnas_normales)

    resultados = ve.verificar_empleo(2030)

    inconsistencias = [r for r in resultados if r.nombre.startswith("Consistencia mensual")]
    assert len(inconsistencias) == 1
    assert "SECTOR_F" in inconsistencias[0].faltantes


def test_verificar_anio_devuelve_vacio_sin_archivos(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    assert ve.verificar_anio(2030) == []
