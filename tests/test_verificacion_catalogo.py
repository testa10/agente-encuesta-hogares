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


def test_numeros_del_catalogo_cubre_los_47_bloques_conocidos():
    catalogo = vc.numeros_del_catalogo()
    assert min(catalogo) == 1
    assert max(catalogo) == 47
    assert len(catalogo) == 47


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
    # Caso real 2025: falta INFORMAL pero esta f82 - la 36/37 tienen que
    # quedar disponibles (segunda opcion completa), no marcadas.
    columnas = {"ID", "nper", "mes", "POBPCOAC", "f82", "SUBEMPLEO", "W"}
    no_disponibles = vc.metricas_no_disponibles(columnas)
    assert 36 not in no_disponibles
    assert 37 not in no_disponibles


def test_metricas_no_disponibles_marca_metrica_sin_ninguna_opcion_completa():
    # Caso real 2025: SIT_OCUP y SECTOR_F no estan, sin ningun camino
    # alternativo conocido para la metrica 40.
    columnas = {"ID", "nper", "mes", "POBPCOAC", "INFORMAL", "SUBEMPLEO", "W"}
    no_disponibles = vc.metricas_no_disponibles(columnas)
    assert 36 not in no_disponibles
    assert set(no_disponibles[40]) == {"SIT_OCUP", "SECTOR_F"}


def test_metricas_empleo_no_disponibles_lee_el_primer_archivo_existente(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2025"
    carpeta.mkdir()
    columnas_2025 = [c for c in config.EMPLEO_COLUMNS if c not in ("INFORMAL", "SECTOR_F", "SIT_OCUP")]
    (carpeta / "ECH_01_2025.csv").write_text(",".join(columnas_2025) + "\n")

    no_disponibles = vc.metricas_empleo_no_disponibles("2025")

    assert 36 not in no_disponibles  # f82 esta en columnas_2025
    assert set(no_disponibles[40]) == {"SIT_OCUP", "SECTOR_F"}


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
    assert "Métrica 40" in avisos[0]
    assert "SIT_OCUP" in avisos[0] and "SECTOR_F" in avisos[0]
