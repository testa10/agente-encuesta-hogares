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


def test_plantilla_catalogo_no_incluye_nada_por_defecto():
    # Ningún bloque se incluye por defecto - ni siquiera Brecha Digital o
    # Hogares, que antes venían siempre. Cada uno es opt-in.
    html = plantilla_catalogo()
    assert "Brecha Digital" not in html
    assert "Hogares" not in html
    assert "Territorio" not in html
    assert "Vivienda" not in html
    assert 'value="1"' not in html


def test_plantilla_catalogo_incluye_las_47_metricas_con_todos_los_bloques():
    html = plantilla_catalogo(
        incluir_brecha_digital=True,
        incluir_hogares=True,
        incluir_territorio=True,
        incluir_vivienda=True,
        incluir_fies=True,
        incluir_empleo=True,
        incluir_seguridad=True,
    )
    for numero in range(1, 48):
        assert f'value="{numero}"' in html
    # los 7 bloques
    assert "Brecha Digital" in html
    assert "Hogares" in html
    assert "Territorio" in html
    assert "Vivienda" in html
    assert "Seguridad alimentaria" in html
    assert "6 · Empleo" in html
    assert "Seguridad y victimización" in html
    # el informe siempre se entrega en PDF y HTML - no se pregunta acá
    assert 'name="pdf"' not in html


def test_plantilla_catalogo_cada_bloque_base_es_independiente():
    html_solo_hogares = plantilla_catalogo(incluir_hogares=True)
    assert "Hogares" in html_solo_hogares
    assert "Brecha Digital" not in html_solo_hogares
    assert "Territorio" not in html_solo_hogares
    assert "Vivienda" not in html_solo_hogares
    for numero in range(12, 18):
        assert f'value="{numero}"' in html_solo_hogares
    for numero in [1, 11, 18]:
        assert f'value="{numero}"' not in html_solo_hogares


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


def test_plantilla_finalizacion_ofrece_crear_un_nuevo_informe():
    html = plantilla_finalizacion(pdf_disponible=True, html_disponible=True)
    assert 'value="nuevo_informe"' in html
    assert 'value="terminar"' in html
    # no debe prometer que la pestana se puede cerrar en la rama de "nuevo
    # informe" (va a abrir una pestana nueva, igual que las pantallas de
    # procesamiento) - solo en la rama que de verdad termina el flujo.
    assert "e.submitter" in html


def test_pantallas_de_procesamiento_no_prometen_que_se_puede_cerrar():
    # A diferencia de plantilla_finalizacion (que sí es el cierre real del
    # flujo) y del mensaje de despedida al salir a mitad de camino, la
    # pantalla de "procesando" (mostrarListo) siempre va seguida de una
    # pestaña nueva - prometer que se puede cerrar mientras se dice
    # "estamos procesando" es contradictorio para alguien sin conocimientos
    # técnicos (ver feedback real de usuario). Se busca puntualmente dentro
    # de mostrarListo(), no en todo el HTML - el botón de "salir sin
    # terminar" sí usa esa misma frase, correctamente, en su propio mensaje
    # de despedida (ese es un cierre real del flujo).
    pantallas = [
        plantilla_bienvenida(),
        plantilla_datos("2024", r"C:\ruta\data\2024"),
        plantilla_areas(True, True, True),
        plantilla_catalogo(),
        plantilla_revision("propuesta", "problema", "alternativa"),
    ]
    for html in pantallas:
        inicio = html.index("function mostrarListo()")
        fin = html.index("function salirDelFlujo()")
        cuerpo_mostrar_listo = html[inicio:fin]
        assert "podés cerrar esta pestaña" not in cuerpo_mostrar_listo.lower()


def test_todas_las_pantallas_del_flujo_guiado_ofrecen_salir():
    # Sin este botón, alguien que quiere dejar de usar el agente a mitad de
    # camino tiene que cerrar la pestaña y dejar al agente esperando hasta
    # el timeout de 30 minutos (ver bug real reportado por el usuario).
    pantallas = [
        plantilla_bienvenida(),
        plantilla_datos("2024", r"C:\ruta\data\2024"),
        plantilla_areas(True, True, True),
        plantilla_catalogo(),
        plantilla_revision("propuesta", "problema", "alternativa"),
    ]
    for html in pantallas:
        assert "salirDelFlujo()" in html
        assert "salir_del_flujo" in html


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
    assert "6 · Empleo" in html
    for numero in range(33, 41):
        assert f'value="{numero}"' in html


def test_plantilla_catalogo_sin_empleo_por_defecto():
    html = plantilla_catalogo()
    assert 'value="33"' not in html


def test_plantilla_areas_siempre_ofrece_los_cuatro_bloques_base():
    # Brecha Digital, Hogares, Territorio y Vivienda no dependen de FIES/
    # Empleo/Seguridad - se ofrecen siempre, ninguno tildado de antemano.
    html = plantilla_areas(fies_disponible=False, empleo_disponible=False, seguridad_disponible=False)
    assert 'value="brecha_digital"' in html
    assert 'value="hogares"' in html
    assert 'value="territorio"' in html
    assert 'value="vivienda"' in html
    assert 'value="fies"' not in html
    assert 'value="empleo"' not in html
    assert 'value="seguridad"' not in html


def test_plantilla_areas_muestra_solo_lo_disponible():
    html_ninguna = plantilla_areas(fies_disponible=False, empleo_disponible=False, seguridad_disponible=False)
    assert 'value="fies"' not in html_ninguna
    assert 'value="empleo"' not in html_ninguna
    assert 'value="seguridad"' not in html_ninguna

    html_empleo = plantilla_areas(fies_disponible=False, empleo_disponible=True, seguridad_disponible=False)
    assert 'value="empleo"' in html_empleo
    assert 'value="seguridad"' not in html_empleo

    html_todas = plantilla_areas(fies_disponible=True, empleo_disponible=True, seguridad_disponible=True)
    assert 'value="fies"' in html_todas
    assert 'value="empleo"' in html_todas
    assert 'value="seguridad"' in html_todas


def test_plantilla_catalogo_incluye_seguridad_cuando_se_pide():
    html = plantilla_catalogo(incluir_seguridad=True)
    assert "Seguridad y victimización" in html
    for numero in range(41, 48):
        assert f'value="{numero}"' in html


def test_plantilla_catalogo_sin_seguridad_por_defecto():
    html = plantilla_catalogo()
    assert 'value="41"' not in html
