from encuesta_hogares.formularios import (
    plantilla_areas,
    plantilla_arranque,
    plantilla_bienvenida,
    plantilla_catalogo,
    plantilla_datos,
    plantilla_finalizacion,
    plantilla_revision,
)


def test_plantilla_bienvenida_pide_el_anio():
    html = plantilla_bienvenida()
    assert "<form" in html
    assert 'id="anio"' in html


def test_plantilla_datos_muestra_la_carpeta_y_el_anio():
    html = plantilla_datos("2024", r"C:\ruta\data\2024", "https://ejemplo.ine/ficha")
    assert r"C:\ruta\data\2024" in html
    assert "2024" in html
    assert "https://ejemplo.ine/ficha" in html


def test_plantilla_catalogo_incluye_las_25_metricas():
    html = plantilla_catalogo()
    for numero in range(1, 26):
        assert f'value="{numero}"' in html
    # las 5 categorías
    assert "Nivel económico y brecha digital" in html
    assert "Pobreza" in html
    assert "Territorio" in html
    assert "Hogar y demografía" in html
    assert "Vivienda y tecnología" in html
    # preferencia de PDF presente
    assert 'name="pdf"' in html


def test_plantilla_revision_incluye_las_tres_salidas():
    html = plantilla_revision("mi propuesta", "el problema", "la alternativa")
    assert "mi propuesta" in html
    assert "el problema" in html
    assert "la alternativa" in html
    assert 'value="aceptar"' in html
    assert 'value="nueva"' in html
    assert 'value="descartar"' in html


def test_plantilla_finalizacion_muestra_ambos_links_cuando_hay_pdf_y_html():
    html = plantilla_finalizacion(pdf_disponible=True, html_disponible=True)
    assert 'href="/informe.pdf"' in html
    assert 'href="/informe.html"' in html


def test_plantilla_finalizacion_omite_el_link_del_formato_no_generado():
    html = plantilla_finalizacion(pdf_disponible=False, html_disponible=True)
    assert 'href="/informe.pdf"' not in html
    assert 'href="/informe.html"' in html


def test_plantilla_arranque_ofrece_empezar_y_salir():
    html = plantilla_arranque()
    assert "elegir('empezar')" in html
    assert "elegir('salir')" in html


def test_plantilla_catalogo_no_incluye_fies_por_defecto():
    html = plantilla_catalogo()
    assert "Seguridad alimentaria" not in html
    assert 'value="26"' not in html


def test_plantilla_catalogo_incluye_fies_cuando_se_pide():
    html = plantilla_catalogo(incluir_fies=True)
    assert "Seguridad alimentaria" in html
    for numero in range(26, 33):
        assert f'value="{numero}"' in html


def test_plantilla_catalogo_incluye_empleo_cuando_se_pide():
    html = plantilla_catalogo(incluir_empleo=True)
    assert "7 · Empleo" in html
    for numero in range(33, 41):
        assert f'value="{numero}"' in html


def test_plantilla_catalogo_sin_empleo_por_defecto():
    html = plantilla_catalogo()
    assert 'value="33"' not in html


def test_plantilla_areas_muestra_solo_lo_disponible():
    html_ninguna = plantilla_areas(empleo_disponible=False, seguridad_disponible=False)
    assert 'value="empleo"' not in html_ninguna
    assert 'value="seguridad"' not in html_ninguna

    html_empleo = plantilla_areas(empleo_disponible=True, seguridad_disponible=False)
    assert 'value="empleo"' in html_empleo
    assert 'value="seguridad"' not in html_empleo

    html_ambas = plantilla_areas(empleo_disponible=True, seguridad_disponible=True)
    assert 'value="empleo"' in html_ambas
    assert 'value="seguridad"' in html_ambas


def test_plantilla_catalogo_incluye_seguridad_cuando_se_pide():
    html = plantilla_catalogo(incluir_seguridad=True)
    assert "Seguridad y victimización" in html
    for numero in range(41, 48):
        assert f'value="{numero}"' in html


def test_plantilla_catalogo_sin_seguridad_por_defecto():
    html = plantilla_catalogo()
    assert 'value="41"' not in html
