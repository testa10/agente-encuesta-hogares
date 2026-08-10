from encuesta_hogares.formularios import (
    plantilla_bienvenida,
    plantilla_catalogo,
    plantilla_datos,
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
