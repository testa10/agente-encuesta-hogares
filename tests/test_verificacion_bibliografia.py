from encuesta_hogares import verificacion_bibliografia as vb


def test_autores_citados_en_visualizacion_de_datos_encuentra_varios_autores_conocidos():
    autores = vb.autores_citados_en_visualizacion_de_datos()
    # Autores reales de BIBLIOGRAFIA.md a esta fecha - si esta lista se
    # queda corta después de agregar fuentes nuevas, está bien (el test
    # de citas_sin_conectar es el que de verdad importa mantener en
    # verde); esto solo confirma que el parseo encuentra lo esperado.
    for esperado in ("Cleveland", "Few", "Knaflic", "Tufte", "Wilke"):
        assert esperado in autores, f"no se encontró '{esperado}' — revisar el parseo de BIBLIOGRAFIA.md"


def test_no_quedan_citas_de_visualizacion_sin_conectar_a_convenciones_de_graficas():
    faltantes = vb.citas_sin_conectar()
    detalle = "\n".join(f"  - {autor}: {razon}" for autor, razon in faltantes.items())
    assert not faltantes, (
        "Hay citas en la sección 'Visualización de datos' de "
        "BIBLIOGRAFIA.md que no aparecen en ninguna entrada de "
        "CONVENCIONES_DE_GRAFICAS.md:\n\n" + detalle
    )
