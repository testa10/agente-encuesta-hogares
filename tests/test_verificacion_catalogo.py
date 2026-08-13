from encuesta_hogares import verificacion_catalogo as vc


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
