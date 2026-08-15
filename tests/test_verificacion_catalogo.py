from encuesta_hogares import config, verificacion_catalogo as vc


def test_toda_metrica_del_catalogo_tiene_entrada_en_el_manifiesto():
    catalogo = vc.numeros_del_catalogo()
    faltantes = vc.metricas_sin_manifiesto(catalogo)
    detalle = "\n".join(f"  - {n}: {catalogo[n]}" for n in sorted(faltantes))
    assert not faltantes, (
        "Hay métricas en el catálogo (formularios.py) sin entrada en "
        "verificacion_catalogo.MANIFEST — agregales la(s) función(es) que "
        "las implementan:\n\n" + detalle
    )


def test_manifiesto_no_tiene_entradas_obsoletas():
    catalogo = vc.numeros_del_catalogo()
    obsoletas = vc.entradas_manifiesto_obsoletas(catalogo)
    assert not obsoletas, (
        f"MANIFEST tiene entradas para métricas que ya no están en el "
        f"catálogo: {sorted(obsoletas)} — revisar si se renumeraron o se "
        f"eliminaron, y limpiar la entrada."
    )


def test_toda_referencia_del_manifiesto_resuelve_a_una_funcion_real():
    rotas = vc.referencias_rotas()
    detalle = "\n".join(f"  - métrica {r.numero}: {r.referencia}" for r in rotas)
    assert not rotas, (
        "MANIFEST referencia funciones que no existen de verdad — la "
        "métrica quedó huérfana (nunca implementada, o la función se "
        "borró/renombró después):\n\n" + detalle
    )


def test_toda_metrica_del_manifiesto_tiene_su_funcion_validada_con_datos_reales():
    faltantes = vc.metricas_sin_funcion_validada_con_datos_reales()
    detalle = "\n".join(f"  - {n}: {nombres}" for n, nombres in sorted(faltantes.items()))
    assert not faltantes, (
        "Hay métricas cuya función nunca se invoca en "
        "tools/validar_con_datos_reales.py — el pipeline puede pasar la "
        "suite sintética y calcular mal contra datos reales sin que nada "
        "lo note. Agregá una llamada real (con datos de al menos un año) "
        "y un assert de invariante genérico (ej. 0 <= pct <= 100):\n\n" + detalle
    )


def test_numeros_del_catalogo_cubre_los_43_bloques_conocidos():
    catalogo = vc.numeros_del_catalogo()
    assert min(catalogo) == 1
    assert max(catalogo) == 43
    assert len(catalogo) == 43


def test_resolver_devuelve_none_para_una_referencia_inexistente():
    entrada_falsa = {"funciones": ["analysis.esta_funcion_no_existe"], "visualizacion": "visualization.plot_brecha_digital"}
    original = vc.MANIFEST.get(9999)
    vc.MANIFEST[9999] = entrada_falsa
    try:
        rotas = vc.referencias_rotas()
    finally:
        if original is None:
            del vc.MANIFEST[9999]
        else:
            vc.MANIFEST[9999] = original

    assert any(r.numero == 9999 and r.referencia == "analysis.esta_funcion_no_existe" for r in rotas)


def test_metricas_no_disponibles_acepta_cualquier_opcion_completa():
    # Caso real 2025: falta INFORMAL pero esta f82 - la 32/33 tienen que
    # quedar disponibles (segunda opcion completa), no marcadas.
    columnas = {"ID", "nper", "mes", "POBPCOAC", "f82", "SUBEMPLEO", "W"}
    no_disponibles = vc.metricas_no_disponibles(columnas)
    assert 32 not in no_disponibles
    assert 33 not in no_disponibles


def test_metricas_no_disponibles_marca_metrica_sin_ninguna_opcion_completa():
    # Caso real 2025: SIT_OCUP y SECTOR_F no estan, sin ningun camino
    # alternativo conocido para la metrica 36.
    columnas = {"ID", "nper", "mes", "POBPCOAC", "INFORMAL", "SUBEMPLEO", "W"}
    no_disponibles = vc.metricas_no_disponibles(columnas)
    assert 32 not in no_disponibles
    assert set(no_disponibles[36]) == {"SIT_OCUP", "SECTOR_F"}


def test_metricas_empleo_no_disponibles_lee_el_primer_archivo_existente(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2025"
    carpeta.mkdir()
    columnas_2025 = [c for c in config.EMPLEO_COLUMNS if c not in ("INFORMAL", "SECTOR_F", "SIT_OCUP")]
    (carpeta / "ECH_01_2025.csv").write_text(",".join(columnas_2025) + "\n")

    no_disponibles = vc.metricas_empleo_no_disponibles("2025")

    assert 32 not in no_disponibles  # f82 esta en columnas_2025
    assert set(no_disponibles[36]) == {"SIT_OCUP", "SECTOR_F"}


def test_metricas_empleo_no_disponibles_vacio_si_no_hay_archivos(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    assert vc.metricas_empleo_no_disponibles("2030") == {}


def test_aviso_metricas_no_disponibles_redacta_mensaje_legible(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2025"
    carpeta.mkdir()
    columnas_2025 = [c for c in config.EMPLEO_COLUMNS if c not in ("INFORMAL", "SECTOR_F", "SIT_OCUP")]
    (carpeta / "ECH_01_2025.csv").write_text(",".join(columnas_2025) + "\n")

    avisos = vc.aviso_metricas_no_disponibles("2025")

    assert len(avisos) == 1
    assert "Métrica 36" in avisos[0]
    assert "SIT_OCUP" in avisos[0] and "SECTOR_F" in avisos[0]


def test_metricas_empleo_no_disponibles_no_marca_metricas_de_vivienda(tmp_path, monkeypatch):
    # Caso real que este test evita repetir: al agregar las entradas de
    # Vivienda (17-21) a COLUMNAS_REQUERIDAS, metricas_empleo_no_disponibles
    # las marcaba igual como "no disponibles" solo porque el archivo de
    # Empleo (obviamente) no tiene columnas de vivienda - metricas_no_disponibles
    # ahora necesita saber que a un archivo de Empleo solo le corresponde
    # responder por las métricas de Empleo.
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2025"
    carpeta.mkdir()
    (carpeta / "ECH_01_2025.csv").write_text(",".join(config.EMPLEO_COLUMNS) + "\n")

    no_disponibles = vc.metricas_empleo_no_disponibles("2025")

    assert not {14, 15, 16, 17, 18, 19, 20, 21} & set(no_disponibles)


def test_metricas_hogares_no_disponibles_detecta_modulo_vivienda_ausente(tmp_path, monkeypatch):
    # Caso real: 2023 no tiene ninguna columna del módulo C5 en el CSV
    # combinado de Hogares/Personas.
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2023"
    carpeta.mkdir()
    columnas_sin_vivienda = [c for c in config.HOGARES_COLUMNS_CSV if c not in config.CONDICIONES_VIVIENDA_COLUMNS_CSV]
    (carpeta / "ECH_2023.csv").write_text(",".join(columnas_sin_vivienda) + "\n")

    no_disponibles = vc.metricas_hogares_no_disponibles("2023")

    assert set(no_disponibles) == {14, 15, 16, 17, 18, 19, 20, 21}
    # metricas de Empleo no deberian aparecer al chequear un archivo de Hogares
    assert 32 not in no_disponibles and 36 not in no_disponibles


def test_metricas_hogares_no_disponibles_ok_si_hay_al_menos_una_columna(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2030"
    carpeta.mkdir()
    (carpeta / "ECH_2030.csv").write_text(",".join(config.HOGARES_COLUMNS_CSV) + "\n")

    assert vc.metricas_hogares_no_disponibles("2030") == {}


def test_aviso_metricas_no_disponibles_incluye_vivienda(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2023"
    carpeta.mkdir()
    columnas_sin_vivienda = [c for c in config.HOGARES_COLUMNS_CSV if c not in config.CONDICIONES_VIVIENDA_COLUMNS_CSV]
    (carpeta / "ECH_2023.csv").write_text(",".join(columnas_sin_vivienda) + "\n")

    avisos = vc.aviso_metricas_no_disponibles("2023")

    numeros_avisados = {int(a.split(" ")[1]) for a in avisos}
    assert {14, 15, 16, 17, 18, 19, 20, 21} <= numeros_avisados
